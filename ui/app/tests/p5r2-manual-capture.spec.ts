import { expect, test, type Page } from '@playwright/test'
import axe from 'axe-core'
import { mkdir, writeFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'

const evidenceRoot = resolve(process.cwd(), '../../tests/evidence/phase5R2/RUN-P5R2-22-MANUAL-LOCAL-001/P5R2-22_manual/ui')

async function runAxe(page: Page): Promise<axe.AxeResults> {
  await page.addScriptTag({ content: axe.source })
  return page.evaluate(async () => (window as unknown as { axe: typeof axe }).axe.run(document, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] },
  }))
}

async function openScreen(page: Page, screenId: 'SCREEN-08' | 'SCREEN-09' | 'SCREEN-10'): Promise<void> {
  if ((page.viewportSize()?.width ?? 0) < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  await page.getByTestId(`nav-${screenId}`).click()
  await expect(page.getByTestId(`screen-${screenId}`)).toHaveAttribute('data-p5r2-real-api', 'true')
}

test('P5R2-22: current manual journey is assert-first and bounded', async ({ page }, testInfo) => {
  test.setTimeout(120_000)
  const externalRequests: string[] = []
  const axeResults: Array<{ screen: string; blocking: unknown[] }> = []
  const screenshots: string[] = []
  page.on('request', (request) => {
    const url = request.url()
    if (!url.startsWith('http://127.0.0.1:4173')
      && !url.startsWith('http://127.0.0.1:8765')
      && !url.startsWith('data:')
      && !url.startsWith('blob:')
      && !url.startsWith('about:')) {
      externalRequests.push(url)
    }
  })

  await page.goto('/')
  await openScreen(page, 'SCREEN-08')
  const timeframeOptions = await page.getByLabel('戦略時間足').locator('option').allTextContents()
  expect(timeframeOptions).toEqual(['15m', '30m', '1h', '4h', '1d'])
  expect(timeframeOptions).not.toContain('1m')
  await expect(page.getByText('1mは生成元Dataの説明です。戦略時間足としては選択できません。')).toBeVisible()
  await expect(page.getByRole('button', { name: /ヒストリカルDataをダウンロード/ })).toBeDisabled()
  await expect(page.getByText('HOST_LEVEL_ISOLATION_NOT_VERIFIED。download APIは呼び出していません。')).toBeVisible()
  await expect(page.getByTestId('p5r2-catalog-table')).toBeVisible()
  await expect(page.getByTestId('p5r2-catalog-table')).toContainText('JOB-TIMEFRAME_GENERATION-p5r2-19-fixture-source-job')

  const conditionAxe = await runAxe(page)
  axeResults.push({ screen: 'SCREEN-08-condition', blocking: conditionAxe.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious') })
  expect(axeResults.at(-1)?.blocking).toEqual([])

  await page.getByRole('button', { name: '事前確認' }).click()
  const missingDataDialog = page.getByRole('dialog', { name: '指定期間の時間足Dataが不足しています' })
  await expect(missingDataDialog).toBeVisible()
  await expect(missingDataDialog).toContainText('BTCUSDT / 30m')
  await missingDataDialog.getByRole('button', { name: '時間足を生成する' }).click()
  const generationForm = page.getByTestId('p5r2-generation-form')
  await expect(generationForm).toBeVisible()
  const generationStart = generationForm.locator('#p5r2-generation-start')
  const generationEnd = generationForm.locator('#p5r2-generation-end')
  await expect(generationStart).toHaveAttribute('type', 'datetime-local')
  await expect(generationEnd).toHaveAttribute('type', 'datetime-local')
  await expect(generationStart).toHaveAttribute('step', '60')
  await expect(generationStart).toHaveValue('2025-02-24T00:00')
  await expect(generationEnd).toHaveValue('2025-02-24T03:00')
  await generationStart.focus()
  await expect(generationStart).toBeFocused()
  await expect(generationEnd).toHaveAttribute('aria-describedby', /p5r2-generation-end-description/)
  await expect(generationForm.getByRole('button', { name: '時間足を生成する' })).toBeEnabled()
  await generationForm.getByRole('button', { name: '時間足を生成する' }).click()
  await expect(generationForm.getByText(/生成Job/)).toBeVisible()
  await expect(generationForm).toContainText('STAGED')
  const generationAxe = await runAxe(page)
  axeResults.push({ screen: 'SCREEN-08-generation', blocking: generationAxe.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious') })
  expect(axeResults.at(-1)?.blocking).toEqual([])

  const projectRoot = join(evidenceRoot, testInfo.project.name)
  await mkdir(projectRoot, { recursive: true })
  const generationShot = join(projectRoot, 'P5R2-22-SCREEN-08-generation.png')
  await page.screenshot({ path: generationShot, fullPage: true })
  screenshots.push(`tests/evidence/phase5R2/RUN-P5R2-22-MANUAL-LOCAL-001/P5R2-22_manual/ui/${testInfo.project.name}/P5R2-22-SCREEN-08-generation.png`)

  await openScreen(page, 'SCREEN-09')
  await expect(page.getByText('P5R2のBacktest Runはありません')).toBeVisible()
  const runAxeResult = await runAxe(page)
  axeResults.push({ screen: 'SCREEN-09', blocking: runAxeResult.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious') })
  expect(axeResults.at(-1)?.blocking).toEqual([])
  const runShot = join(projectRoot, 'P5R2-22-SCREEN-09-runs.png')
  await page.screenshot({ path: runShot, fullPage: true })
  screenshots.push(`tests/evidence/phase5R2/RUN-P5R2-22-MANUAL-LOCAL-001/P5R2-22_manual/ui/${testInfo.project.name}/P5R2-22-SCREEN-09-runs.png`)

  await openScreen(page, 'SCREEN-10')
  await expect(page.getByText('表示できるP5R2結果はありません')).toBeVisible()
  await expect(page.getByText('結果表示の削除は承認済み範囲で実行できます')).toBeVisible()
  const resultAxe = await runAxe(page)
  axeResults.push({ screen: 'SCREEN-10', blocking: resultAxe.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious') })
  expect(axeResults.at(-1)?.blocking).toEqual([])
  const resultShot = join(projectRoot, 'P5R2-22-SCREEN-10-results.png')
  await page.screenshot({ path: resultShot, fullPage: true })
  screenshots.push(`tests/evidence/phase5R2/RUN-P5R2-22-MANUAL-LOCAL-001/P5R2-22_manual/ui/${testInfo.project.name}/P5R2-22-SCREEN-10-results.png`)

  expect(externalRequests).toEqual([])
  await writeFile(join(projectRoot, 'p5r2-manual-capture.json'), JSON.stringify({
    schema_version: 'P5R2-22-manual-ui-capture-v1',
    run_id: 'RUN-P5R2-22-MANUAL-LOCAL-001',
    project: testInfo.project.name,
    viewport: page.viewportSize(),
    external_requests: externalRequests,
    axe: axeResults,
    screenshots,
    assertions: {
      strategy_timeframes: ['15m', '30m', '1h', '4h', '1d'],
      source_timeframe: '1m',
      missing_data_dialog: true,
      default_range_without_source: 'NOT_SET',
      external_download: 'DISABLED_HOST_LEVEL_ISOLATION_NOT_VERIFIED',
    },
    boundaries: { p5r2: 'LOCAL_ONLY', provider: 'NOT_CALLED', p6: 'NOT_STARTED' },
  }, null, 2), 'utf-8')
})
