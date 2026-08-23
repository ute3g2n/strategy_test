import { expect, test, type Page } from '@playwright/test'
import axe from 'axe-core'
import { mkdir, writeFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'

const evidenceRoot = resolve(process.cwd(), '../../tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/ui')

async function openP5R2Condition(page: Page): Promise<void> {
  if ((page.viewportSize()?.width ?? 0) < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  await page.getByTestId('nav-SCREEN-08').click()
  await expect(page.getByTestId('screen-SCREEN-08')).toHaveAttribute('data-p5r2-real-api', 'true')
  await expect(page.getByText('P5R2 Web Product / 実Application API')).toBeVisible()
}

async function runAxe(page: Page): Promise<axe.AxeResults> {
  await page.addScriptTag({ content: axe.source })
  return page.evaluate(async () => (window as unknown as { axe: typeof axe }).axe.run(document, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] },
  }))
}

test('P5R2-19: local Web Product journey remains bounded and fail-closed', async ({ page }, testInfo) => {
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
  await openP5R2Condition(page)

  const timeframeOptions = await page.getByLabel('戦略時間足').locator('option').allTextContents()
  expect(timeframeOptions).toEqual(['15m', '30m', '1h', '4h', '1d'])
  expect(timeframeOptions).not.toContain('1m')
  const conditionStart = page.getByLabel('開始日時（UTC）')
  const conditionEnd = page.getByLabel('終了日時（UTC）')
  await expect(conditionStart).toHaveAttribute('type', 'datetime-local')
  await expect(conditionEnd).toHaveAttribute('type', 'datetime-local')
  await expect(conditionStart).toHaveAttribute('step', '60')
  await conditionStart.focus()
  await expect(conditionStart).toBeFocused()
  await page.getByLabel('戦略時間足').focus()
  await expect(page.getByLabel('戦略時間足')).toBeFocused()
  await expect(page.getByText('1mは生成元Dataの説明です。戦略時間足としては選択できません。')).toBeVisible()
  await expect(page.getByText('現在使用可能なヒストリカルDataはありません')).toBeVisible()
  await expect(page.getByRole('button', { name: /ヒストリカルDataをダウンロード/ })).toBeDisabled()
  await expect(page.getByText('HOST_LEVEL_ISOLATION_NOT_VERIFIED。download APIは呼び出していません。')).toBeVisible()

  const conditionAxe = await runAxe(page)
  axeResults.push({
    screen: 'SCREEN-08',
    blocking: conditionAxe.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious'),
  })
  expect(axeResults.at(-1)?.blocking).toEqual([])
  const conditionShot = join(evidenceRoot, testInfo.project.name, 'P5R2-19-SCREEN-08-condition.png')
  await mkdir(join(evidenceRoot, testInfo.project.name), { recursive: true })
  await page.screenshot({ path: conditionShot, fullPage: true })
  screenshots.push(`tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/ui/${testInfo.project.name}/P5R2-19-SCREEN-08-condition.png`)

  await page.getByRole('button', { name: '事前確認' }).click()
  const missingDataDialog = page.getByRole('dialog', { name: '指定期間の時間足Dataが不足しています' })
  await expect(missingDataDialog).toBeVisible()
  await expect(missingDataDialog).toContainText('BTCUSDT / 30m')
  await missingDataDialog.getByRole('button', { name: '時間足を生成する' }).click()
  const generationForm = page.getByTestId('p5r2-generation-form')
  await expect(generationForm).toBeVisible()
  await expect(generationForm.getByText('現在利用可能な1m sourceがないため、全期間の既定値は設定せず、生成要求も送信しません。')).toBeVisible()
  await expect(generationForm.getByRole('button', { name: '時間足を生成する' })).toBeDisabled()

  if ((page.viewportSize()?.width ?? 0) < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  await page.getByTestId('nav-SCREEN-09').click()
  await expect(page.getByTestId('screen-SCREEN-09')).toHaveAttribute('data-p5r2-real-api', 'true')
  await expect(page.getByText('P5R2のBacktest Runはありません')).toBeVisible()
  const runAxeResults = await runAxe(page)
  axeResults.push({
    screen: 'SCREEN-09',
    blocking: runAxeResults.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious'),
  })
  expect(axeResults.at(-1)?.blocking).toEqual([])
  const runShot = join(evidenceRoot, testInfo.project.name, 'P5R2-19-SCREEN-09-runs.png')
  await page.screenshot({ path: runShot, fullPage: true })
  screenshots.push(`tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/ui/${testInfo.project.name}/P5R2-19-SCREEN-09-runs.png`)

  if ((page.viewportSize()?.width ?? 0) < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  await page.getByTestId('nav-SCREEN-10').click()
  await expect(page.getByTestId('screen-SCREEN-10')).toHaveAttribute('data-p5r2-real-api', 'true')
  await expect(page.getByText('表示できるP5R2結果はありません')).toBeVisible()
  await expect(page.getByText('結果表示の削除は承認済み範囲で実行できます')).toBeVisible()
  await expect(page.getByText(/削除対象のRunカードで確認ダイアログ/)).toBeVisible()
  const resultAxe = await runAxe(page)
  axeResults.push({
    screen: 'SCREEN-10',
    blocking: resultAxe.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious'),
  })
  expect(axeResults.at(-1)?.blocking).toEqual([])
  const resultShot = join(evidenceRoot, testInfo.project.name, 'P5R2-19-SCREEN-10-results.png')
  await page.screenshot({ path: resultShot, fullPage: true })
  screenshots.push(`tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/ui/${testInfo.project.name}/P5R2-19-SCREEN-10-results.png`)

  expect(externalRequests).toEqual([])
  await writeFile(join(evidenceRoot, testInfo.project.name, 'p5r2-ui-capture.json'), JSON.stringify({
    schema_version: 'P5R2-19-ui-capture-v1',
    run_id: 'RUN-P5R2-19-LOCAL-001',
    project: testInfo.project.name,
    viewport: page.viewportSize(),
    external_requests: externalRequests,
    axe: axeResults,
    screenshots,
    boundaries: {
      source_timeframe: '1m (説明だけ、選択不可)',
      strategy_timeframes: ['15m', '30m', '1h', '4h', '1d'],
      external_download: 'HOST_LEVEL_ISOLATION_NOT_VERIFIED',
      delete: 'DELETE-G1_APPROVED_BOUNDED_P5R2_21_FIXTURE_ONLY',
      p6: 'NOT_STARTED',
    },
  }, null, 2), 'utf-8')
})
