import { expect, test, type Page } from '@playwright/test'
import axe from 'axe-core'
import { mkdir, writeFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'

const evidenceRoot = resolve(process.cwd(), '../../tests/evidence/phase5R2/RUN-P5R2-21-DELETE-LOCAL-001/P5R2-21_delete/ui')

async function runAxe(page: Page): Promise<axe.AxeResults> {
  await page.addScriptTag({ content: axe.source })
  return page.evaluate(async () => (window as unknown as { axe: typeof axe }).axe.run(document, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] },
  }))
}

async function openResultScreen(page: Page): Promise<void> {
  if ((page.viewportSize()?.width ?? 0) < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  await page.getByTestId('nav-SCREEN-10').click()
  await expect(page.getByTestId('screen-SCREEN-10')).toHaveAttribute('data-p5r2-real-api', 'true')
}

test('P5R2-21: completed result can be confirmed and physically deleted without cascading', async ({ page }, testInfo) => {
  test.setTimeout(120_000)
  const externalRequests: string[] = []
  let deletePayload: Record<string, unknown> | null = null
  page.on('request', (request) => {
    const url = request.url()
    if (!url.startsWith('http://127.0.0.1:4173')
      && !url.startsWith('http://127.0.0.1:8765')
      && !url.startsWith('data:')
      && !url.startsWith('blob:')
      && !url.startsWith('about:')) {
      externalRequests.push(url)
    }
    if (url.endsWith('/api/p5r2/result-artifacts/delete')) {
      deletePayload = request.postDataJSON() as Record<string, unknown>
    }
  })

  await page.goto('/')
  const findSeeded = async () => {
    const response = await page.request.get('http://127.0.0.1:8765/api/backtest/runs')
    const payload = await response.json() as { items: Array<{ run_id: string; status: string; result_deleted?: boolean }> }
    return payload.items.find((run) => run.status === 'SUCCEEDED' && run.result_deleted !== true)
  }
  await expect.poll(findSeeded, { timeout: 60_000 }).toBeTruthy()
  const created = await findSeeded()
  if (!created) throw new Error('P5R2-21 seeded ResultArtifact was not found')
  expect(created.run_id).toMatch(/^RUN-P5R2-21-UI-SEED-/)

  await openResultScreen(page)
  const runCard = page.getByTestId(`p5r2-run-${created.run_id}`)
  await expect(runCard).toBeVisible()
  await expect(runCard.getByRole('button', { name: '結果表示を削除' })).toBeEnabled()
  await runCard.getByRole('button', { name: '結果表示を削除' }).click()
  const dialog = page.getByRole('dialog', { name: `${created.run_id}の表示を削除しますか？` })
  await expect(dialog).toBeVisible()
  await expect(dialog).toContainText('先にCSVをExportしてください')
  await expect(dialog.getByRole('button', { name: '結果表示を削除する' })).toBeVisible()
  await dialog.getByRole('button', { name: '結果表示を削除する' }).click()

  await expect(page.getByText(new RegExp(`${created.run_id}の結果表示を削除しました`))).toBeVisible()
  await expect(runCard.getByRole('button', { name: '結果表示は削除済み' })).toBeDisabled()
  expect(deletePayload).toMatchObject({
    logical_artifact_id: `RESULT-OWNER-${created.run_id}`,
    artifact_kind: 'RESULT',
    confirmation: true,
  })
  expect(deletePayload).not.toHaveProperty('path')
  expect(deletePayload).not.toHaveProperty('absolute_path')

  const axeResults = await runAxe(page)
  expect(axeResults.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')).toEqual([])
  expect(externalRequests).toEqual([])

  const projectRoot = join(evidenceRoot, testInfo.project.name)
  await mkdir(projectRoot, { recursive: true })
  const screenshot = join(projectRoot, 'P5R2-21-SCREEN-10-result-deleted.png')
  await page.screenshot({ path: screenshot, fullPage: true })
  await writeFile(join(projectRoot, 'p5r2-delete-ui-capture.json'), JSON.stringify({
    schema_version: 'P5R2-21-delete-ui-capture-v1',
    run_id: 'RUN-P5R2-21-DELETE-LOCAL-001',
    created_run_id: created.run_id,
    project: testInfo.project.name,
    viewport: page.viewportSize(),
    external_requests: externalRequests,
    delete_request: deletePayload,
    axe_serious_or_critical: [],
    screenshot: `tests/evidence/phase5R2/RUN-P5R2-21-DELETE-LOCAL-001/P5R2-21_delete/ui/${testInfo.project.name}/P5R2-21-SCREEN-10-result-deleted.png`,
    boundaries: {
      artifact: 'terminal ResultArtifact only',
      protected: ['CSV', 'Historical Data', 'Run', 'Audit', 'Evidence'],
      restore_api: false,
      external_io: false,
      p6: 'NOT_STARTED',
    },
  }, null, 2), 'utf-8')
})
