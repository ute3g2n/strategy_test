import { expect, test, type Page } from '@playwright/test'
import axe from 'axe-core'
import { mkdir, writeFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'

test.describe.configure({ mode: 'serial' })

const evidenceRoot = resolve(process.cwd(), '../../tests/evidence/phase5R/RUN-P5R-09-20260816-001/manual-capture')
const captureIds = [
  'BT-MAN-01', 'BT-MAN-02', 'BT-MAN-03', 'BT-MAN-04', 'BT-MAN-05',
  'BT-MAN-06', 'BT-MAN-07', 'BT-MAN-08', 'BT-MAN-09', 'BT-MAN-10',
  'BT-MAN-11', 'BT-MAN-12', 'BT-MAN-13', 'BT-MAN-14', 'BT-MAN-15',
]

async function openBacktest(page: Page) {
  if ((page.viewportSize()?.width ?? 0) < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  await page.getByTestId('nav-SCREEN-08').click()
  await page.getByRole('button', { name: 'P5R旧履歴表示を開く' }).click()
  await expect(page.getByTestId('screen-SCREEN-08')).toHaveAttribute('data-p5r-real-api', 'true')
}

async function capture(page: Page, testInfo: { project: { name: string }; }, id: string, description: string, captures: Array<Record<string, unknown>>) {
  const projectRoot = join(evidenceRoot, testInfo.project.name)
  await mkdir(projectRoot, { recursive: true })
  const fileName = `${id}.png`
  const absolutePath = join(projectRoot, fileName)
  await page.screenshot({ path: absolutePath, fullPage: true })
  captures.push({
    manual_id: id,
    description,
    project: testInfo.project.name,
    screenshot: `tests/evidence/phase5R/RUN-P5R-09-20260816-001/manual-capture/${testInfo.project.name}/${fileName}`,
    viewport: page.viewportSize(),
    assertion_before_screenshot: 'Playwright DOM assertions passed',
  })
}

test('P5R-09: real Backtest UI journey captures every manual procedure', async ({ page }, testInfo) => {
  test.setTimeout(180_000)
  const captures: Array<Record<string, unknown>> = []
  const externalRequests: string[] = []
  page.on('request', (request) => {
    const url = request.url()
    if (!url.startsWith('http://127.0.0.1:4173') && !url.startsWith('http://127.0.0.1:8765') && !url.startsWith('data:') && !url.startsWith('blob:') && !url.startsWith('about:')) externalRequests.push(url)
  })

  const reset = await page.request.post('http://127.0.0.1:8765/api/backtest/reset', { data: {} })
  expect(reset.ok()).toBeTruthy()
  await page.goto('/')
  await openBacktest(page)
  await expect(page.getByText('P5R実行範囲')).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-01', 'P5R範囲とBacktest条件画面を開く', captures)

  await page.getByRole('button', { name: 'Preflight実行' }).click()
  await expect(page.getByTestId('p5r-preflight-result')).toContainText('TYPE_AND_UNIT')
  await expect(page.getByText('Preflight PASS。実Runを開始できます。')).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-02', '入力・Data範囲・UTC・品質・先読みのPreflight PASS', captures)

  await page.getByLabel('開始（UTC）').fill('2025-02-24T00:00:00')
  await page.getByRole('button', { name: 'Preflight実行' }).click()
  await expect(page.getByText('Preflight STOPPED。停止理由を直してから再実行してください。')).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-03', 'UTC表記がない入力を停止する', captures)

  await page.getByLabel('開始（UTC）').fill('2025-02-24T00:00:00Z')
  await page.getByRole('button', { name: 'Preflight実行' }).click()
  await expect(page.getByText('Preflight PASS。実Runを開始できます。')).toBeVisible()
  await page.getByRole('button', { name: 'Single Run開始' }).click()
  await expect(page.getByTestId('p5r-run-status')).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-04', 'Single Runを開始し、実Run IDと進捗を確認する', captures)
  await expect(page.getByTestId('p5r-run-status')).toContainText('SUCCEEDED', { timeout: 120_000 })
  await expect(page.getByTestId('p5r-five-metrics')).toBeVisible()
  await expect(page.getByTestId('p5r-five-metrics')).toContainText('総損益')
  await capture(page, testInfo, 'BT-MAN-05', '5指標と費用想定を確認する', captures)
  await page.getByRole('button', { name: '結果・詳細を表示' }).click()
  await expect(page.getByTestId('p5r-ledger-table')).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-06', 'Signal・Virtual Fill・残高LedgerとData由来を確認する', captures)

  await page.getByLabel('終了（UTC）').fill('2025-02-28T00:00:00Z')
  await page.getByRole('button', { name: 'Preflight実行' }).click()
  await expect(page.getByText('Preflight PASS。実Runを開始できます。')).toBeVisible()
  await page.getByRole('button', { name: 'Single Run開始' }).click()
  const cancelButton = page.getByRole('button', { name: '取消', exact: true })
  await expect(cancelButton).toBeVisible({ timeout: 10_000 })
  await cancelButton.click()
  await expect(page.getByTestId('p5r-run-status')).toContainText('CANCELLED', { timeout: 10_000 })
  await capture(page, testInfo, 'BT-MAN-07', '実行中の取消とチェックポイント保存を確認する', captures)
  await page.getByRole('button', { name: 'チェックポイントから再開' }).click()
  await expect(page.getByTestId('p5r-run-status')).toContainText('SUCCEEDED', { timeout: 120_000 })
  await capture(page, testInfo, 'BT-MAN-08', 'チェックポイントから再開し、完了結果へ戻る', captures)

  await page.getByLabel('終了（UTC）').fill('2025-02-24T02:30:00Z')
  await page.getByRole('button', { name: 'Preflight実行' }).click()
  await expect(page.getByText('Preflight PASS。実Runを開始できます。')).toBeVisible()
  await page.getByTestId('p5r-tab-sweep').click()
  await page.getByLabel('2番目の候補を意図的に失敗させる').check()
  await page.getByRole('button', { name: 'Sweep開始' }).click()
  await expect(page.getByText('PARTIAL_FAILED')).toBeVisible({ timeout: 120_000 })
  await expect(page.getByText('CANDIDATE_FORCED_FAILURE')).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-09', 'Sweepの親Job・子Run・部分失敗を確認する', captures)

  await page.getByTestId('p5r-tab-single').click()
  await page.getByLabel('Backtest Strategy').selectOption('TURTLE_SYS2')
  await page.getByRole('button', { name: 'Preflight実行' }).click()
  await expect(page.getByText('Preflight PASS。実Runを開始できます。')).toBeVisible()
  await page.getByRole('button', { name: 'Single Run開始' }).click()
  await expect(page.getByTestId('p5r-run-status')).toContainText('SUCCEEDED', { timeout: 120_000 })
  await page.getByTestId('p5r-tab-history').click()
  await expect(page.getByText('このApplication APIで作成したRunの履歴')).toBeVisible()
  await expect(page.getByRole('radio').first()).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-10', 'Run履歴と状態を確認する', captures)

  const comparableRows = page.getByRole('row').filter({ hasText: 'TURTLE_SYS1' }).filter({ hasText: '2025-02-24T00:00:00Z〜2025-02-24T02:30:00Z' }).filter({ hasText: '100%' })
  // Open one completed TURTLE_SYS1 Run, then select another completed
  // TURTLE_SYS1 Run so the compatible comparison path is exercised.
  await expect(comparableRows.nth(1)).toBeVisible()
  await comparableRows.nth(0).getByRole('button', { name: '結果を開く' }).click()
  await expect(page.getByTestId('p5r-five-metrics')).toBeVisible()
  await comparableRows.nth(1).getByRole('radio').click()
  await page.getByRole('button', { name: '選択Runと比較' }).click()
  await expect(page.getByText(/比較結果: comparable=true/)).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-11', '条件の異なる2つのRunを比較する', captures)
  // The same journey also checks that an incompatible strategy is not treated
  // as comparable; the failed comparison remains visible with its reason.
  const incompatibleRow = page.getByRole('row').filter({ hasText: 'TURTLE_SYS2' }).first()
  await incompatibleRow.getByRole('radio').click()
  await page.getByRole('button', { name: '選択Runと比較' }).click()
  await expect(page.getByText(/比較結果: comparable=false/)).toBeVisible()
  await page.getByRole('button', { name: 'CSV生成' }).click()
  await expect(page.getByText(/CSV Job: SUCCEEDED/)).toBeVisible({ timeout: 30_000 })
  await expect(page.getByRole('link', { name: 'CSVダウンロード' })).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-12', '結果LedgerをCSV Jobにしてダウンロード可能にする', captures)

  await page.getByTestId('p5r-tab-evaluation').click()
  await page.getByRole('button', { name: '確定前を試す' }).click()
  await expect(page.getByText(/EARLY_HOLDOUT_ACCESS/)).toBeVisible()
  await capture(page, testInfo, 'BT-MAN-13', '確定前Holdoutを停止する', captures)
  await page.getByRole('button', { name: '確定後に評価' }).click()
  await expect(page.getByText(/SUCCEEDED \/\s+\d+ rows/)).toBeVisible({ timeout: 30_000 })
  await capture(page, testInfo, 'BT-MAN-14', '確定後Holdoutを一度だけ評価する', captures)
  await page.getByRole('button', { name: 'Walk-forward実行' }).click()
  await expect(page.getByText(/SUCCEEDED \/ 窓 3/)).toBeVisible({ timeout: 30_000 })
  await capture(page, testInfo, 'BT-MAN-15', '3窓のWalk-forwardと未来参照なしを確認する', captures)

  await page.addScriptTag({ content: axe.source })
  const axeResults = await page.evaluate(async () => (window as unknown as { axe: typeof axe }).axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } }))
  const blocking = axeResults.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
  expect(blocking, 'P5R Backtest UI critical/serious axe violations').toEqual([])
  expect(externalRequests).toEqual([])
  expect(captures.map((capture) => capture.manual_id)).toEqual(captureIds)

  await mkdir(evidenceRoot, { recursive: true })
  await writeFile(join(evidenceRoot, `capture-registry-${testInfo.project.name}.json`), JSON.stringify({ run_id: 'RUN-P5R-09-20260816-001', project: testInfo.project.name, test: 'p5r-backtest.spec.ts', external_requests: externalRequests, axe_blocking_violations: blocking, captures }, null, 2), 'utf-8')
})
