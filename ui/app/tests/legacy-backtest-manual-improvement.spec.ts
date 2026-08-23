import { expect, test, type Page } from '@playwright/test'
import axe from 'axe-core'
import { mkdir, writeFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'

const evidenceRoot = resolve(process.cwd(), '../../tests/evidence/phase5R/RUN-P5R-MANUAL-20260816-001/manual-capture')

async function openBacktest(page: Page) {
  if ((page.viewportSize()?.width ?? 0) < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  await page.getByTestId('nav-SCREEN-08').click()
  await page.getByRole('button', { name: '旧Backtest履歴表示を開く' }).click()
  await expect(page.getByTestId('screen-SCREEN-08')).toHaveAttribute('data-legacy-backtest-real-api', 'true')
}

test('P5R-MANUAL-16: capture Sweep cancellation after DOM assertions', async ({ page }, testInfo) => {
  test.setTimeout(90_000)
  const externalRequests: string[] = []
  page.on('request', (request) => {
    const url = request.url()
    if (!url.startsWith('http://127.0.0.1:4173') && !url.startsWith('http://127.0.0.1:8765') && !url.startsWith('data:') && !url.startsWith('blob:') && !url.startsWith('about:')) externalRequests.push(url)
  })

  const reset = await page.request.post('http://127.0.0.1:8765/api/backtest/reset', { data: {} })
  expect(reset.ok()).toBeTruthy()
  await page.goto('/')
  await openBacktest(page)
  await page.getByTestId('legacy-backtest-tab-sweep').click()
  await expect(page.getByRole('button', { name: 'Sweep開始' })).toBeVisible()
  await page.getByRole('button', { name: 'Sweep開始' }).click()
  await expect(page.getByRole('button', { name: 'Sweep取消' })).toBeVisible({ timeout: 10_000 })
  await page.getByRole('button', { name: 'Sweep取消' }).click()

  await expect(page.getByText(/状態: CANCELLED/)).toBeVisible({ timeout: 20_000 })
  await expect(page.getByText(/候補ごとの進捗/)).toBeVisible()
  await expect(page.getByText(/子Run/)).toBeVisible()

  await page.addScriptTag({ content: axe.source })
  const axeResults = await page.evaluate(async () => (window as unknown as { axe: typeof axe }).axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } }))
  const blocking = axeResults.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
  expect(blocking, 'legacy Backtest manual improvement critical/serious axe violations').toEqual([])
  expect(externalRequests).toEqual([])

  const projectRoot = join(evidenceRoot, testInfo.project.name)
  await mkdir(projectRoot, { recursive: true })
  const fileName = 'BT-MAN-16.png'
  const absolutePath = join(projectRoot, fileName)
  await page.screenshot({ path: absolutePath, fullPage: true })
  await writeFile(join(projectRoot, 'capture-registry.json'), JSON.stringify({
    run_id: 'RUN-P5R-MANUAL-20260816-001',
    project: testInfo.project.name,
    test: 'legacy-backtest-backtest-manual-improvement.spec.ts',
    manual_id: 'BT-MAN-16',
    description: 'Sweepを途中で取消し、親Jobと子Runの状態を確認する',
    screenshot: `tests/evidence/phase5R/RUN-P5R-MANUAL-20260816-001/manual-capture/${testInfo.project.name}/${fileName}`,
    viewport: page.viewportSize(),
    assertion_before_screenshot: 'Playwright DOM assertions passed',
    external_requests: externalRequests,
    axe_blocking_violations: blocking,
  }, null, 2), 'utf-8')
})
