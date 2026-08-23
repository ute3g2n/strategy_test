import { expect, test, type Page } from '@playwright/test'
import { spawn, type ChildProcess } from 'node:child_process'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

const recoveryApiPort = 8766
const repositoryRoot = process.cwd().replace(/\\ui\\app$/, '')

async function waitForHealth(): Promise<void> {
  const deadline = Date.now() + 30_000
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${recoveryApiPort}/health`)
      if (response.ok) return
    } catch {
      // The child process may still be binding its loopback port.
    }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error('RECOVERY_API_HEALTH_TIMEOUT')
}

function startApi(): ChildProcess {
  return spawn('py', ['-3', 'scripts/application_server/application_api_server.py', '--port', String(recoveryApiPort)], {
    cwd: repositoryRoot,
    stdio: 'ignore',
    windowsHide: true,
  })
}

async function stopApi(child: ChildProcess): Promise<void> {
  if (child.exitCode !== null) return
  child.kill()
  await new Promise<void>((resolve) => {
    const timer = setTimeout(resolve, 5_000)
    child.once('exit', () => {
      clearTimeout(timer)
      resolve()
    })
  })
}

async function openBacktest(page: Page): Promise<void> {
  await page.getByTestId('nav-SCREEN-08').click()
  await page.getByRole('button', { name: 'P5R旧履歴表示を開く' }).click()
  await expect(page.getByTestId('screen-SCREEN-08')).toHaveAttribute('data-p5r-real-api', 'true')
}

test('completed Backtest history survives a controlled API process restart', async ({ page }) => {
  test.setTimeout(120_000)
  const apiRequests: string[] = []
  page.on('request', (request) => {
    const url = request.url()
    if (!url.startsWith('http://127.0.0.1:4173') && !url.startsWith('http://127.0.0.1:8765') && !url.startsWith(`http://127.0.0.1:${recoveryApiPort}`) && !url.startsWith('data:') && !url.startsWith('blob:') && !url.startsWith('about:')) apiRequests.push(url)
  })
  await page.route('http://127.0.0.1:8765/**', (route) => route.continue({ url: route.request().url().replace(':8765', `:${recoveryApiPort}`) }))

  let api = startApi()
  try {
    await waitForHealth()
    const reset = await page.request.post(`http://127.0.0.1:${recoveryApiPort}/api/backtest/reset`, { data: {} })
    expect(reset.ok()).toBeTruthy()
    await page.goto('/')
    await openBacktest(page)
    await page.getByRole('button', { name: 'Preflight実行' }).click()
    await expect(page.getByText('Preflight PASS。実Runを開始できます。')).toBeVisible()
    await page.getByRole('button', { name: 'Single Run開始' }).click()
    await expect(page.getByTestId('p5r-run-status')).toContainText('SUCCEEDED', { timeout: 60_000 })
    const runId = await page.getByTestId('p5r-run-status').locator('h3').innerText()

    const beforeRestart = await page.request.get(`http://127.0.0.1:${recoveryApiPort}/api/backtest/runs/${encodeURIComponent(runId)}`)
    expect(beforeRestart.ok()).toBeTruthy()
    const beforePayload = await beforeRestart.json() as { metrics: Record<string, unknown>; provenance: Record<string, unknown> }
    const beforeRowsResponse = await page.request.get(`http://127.0.0.1:${recoveryApiPort}/api/backtest/runs/${encodeURIComponent(runId)}/rows`)
    expect(beforeRowsResponse.ok()).toBeTruthy()
    const beforeRowsPayload = await beforeRowsResponse.json() as { items: unknown[] }
    await expect(page.getByTestId('p5r-run-status')).toContainText(runId)

    await stopApi(api)
    api = startApi()
    await waitForHealth()
    await page.reload()
    await openBacktest(page)
    const afterRestart = await page.request.get(`http://127.0.0.1:${recoveryApiPort}/api/backtest/runs/${encodeURIComponent(runId)}`)
    expect(afterRestart.ok()).toBeTruthy()
    const afterPayload = await afterRestart.json() as { metrics: Record<string, unknown>; provenance: Record<string, unknown> }
    const afterRowsResponse = await page.request.get(`http://127.0.0.1:${recoveryApiPort}/api/backtest/runs/${encodeURIComponent(runId)}/rows`)
    expect(afterRowsResponse.ok()).toBeTruthy()
    const afterRowsPayload = await afterRowsResponse.json() as { items: unknown[] }
    expect(afterPayload.metrics).toEqual(beforePayload.metrics)
    expect(afterPayload.provenance).toEqual(beforePayload.provenance)
    expect(afterRowsPayload.items).toEqual(beforeRowsPayload.items)
    await page.getByTestId('p5r-tab-history').click()
    await expect(page.getByText('保存済み履歴を読み込みました')).toBeVisible({ timeout: 15_000 })
    const restoredRow = page.getByRole('row').filter({ hasText: runId })
    await expect(restoredRow).toBeVisible()
    await restoredRow.getByRole('button', { name: '結果を開く' }).click()
    await expect(page.getByTestId('p5r-ledger-table')).toBeVisible()
    await expect(page.getByTestId('p5r-five-metrics')).toContainText('最終残高')
    const evidenceDirectory = resolve(process.cwd(), '../../tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001')
    await mkdir(evidenceDirectory, { recursive: true })
    await page.screenshot({ path: resolve(evidenceDirectory, 'backtest-history-after-api-restart.png'), fullPage: true })
    expect(apiRequests).toEqual([])
  } finally {
    await stopApi(api)
  }
})
