import { expect, test, type Page, type TestInfo } from '@playwright/test'
import axe from 'axe-core'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve, join } from 'node:path'
import { pathToFileURL } from 'node:url'

const screenIds = Array.from({ length: 21 }, (_, index) => `SCREEN-${String(index + 1).padStart(2, '0')}`)
const stateIds = ['NORMAL', 'LOADING', 'EMPTY', 'REQUIRED', 'WARNING', 'STOPPED', 'FAILED', 'RECOVERY', 'HUMAN-GATE', 'UNAPPROVED']
const criticalScreenIds = ['SCREEN-01', 'SCREEN-08', 'SCREEN-09', 'SCREEN-13', 'SCREEN-14', 'SCREEN-18', 'SCREEN-19']
const evidenceRoot = resolve(process.cwd(), '../../tests/evidence/requirements_ui/RQU-UI-11-20260811-1325')
const staticMock = resolve(process.cwd(), '../../doc/ui_mock/01_自動トレードシステム_UIモック.html')
const axeSource = axe.source

type BrowserEvents = {
  console: string[]
  failedRequests: string[]
  externalRequests: string[]
}

const browserEvents = new Map<Page, BrowserEvents>()

function isAllowedRequest(url: string) {
  return url.startsWith('http://127.0.0.1:4173') || url.startsWith('http://127.0.0.1:8765') || url.startsWith('file:') || url.startsWith('data:') || url.startsWith('blob:') || url.startsWith('about:')
}

function watchBrowser(page: Page) {
  const events: BrowserEvents = { console: [], failedRequests: [], externalRequests: [] }
  browserEvents.set(page, events)
  page.on('console', (message) => events.console.push(`${message.type()}: ${message.text()}`))
  page.on('requestfailed', (request) => events.failedRequests.push(`${request.method()} ${request.url()} / ${request.failure()?.errorText ?? 'unknown'}`))
  page.on('request', (request) => {
    if (!isAllowedRequest(request.url())) events.externalRequests.push(`${request.method()} ${request.url()}`)
  })
  return events
}

async function saveJson(fileName: string, value: unknown) {
  await mkdir(evidenceRoot, { recursive: true })
  await writeFile(join(evidenceRoot, fileName), `${JSON.stringify(value, null, 2)}\n`, 'utf8')
}

async function openReactScreen(page: Page, screenId: string) {
  if (page.viewportSize()?.width && page.viewportSize()!.width < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  if (screenId === 'SCREEN-09' || screenId === 'SCREEN-10') {
    await page.getByTestId('nav-SCREEN-08').click()
    const legacyEntry = page.getByRole('button', { name: 'P5R旧履歴表示を開く' })
    if (await legacyEntry.isVisible()) await legacyEntry.click()
    if ((page.viewportSize()?.width ?? 0) < 820) {
      const menu = page.getByRole('button', { name: 'メニューを開く' })
      if (await menu.isVisible()) await menu.click()
    }
  }
  await page.getByTestId(`nav-${screenId}`).click()
  if (screenId === 'SCREEN-08') {
    const legacyEntry = page.getByRole('button', { name: 'P5R旧履歴表示を開く' })
    if (await legacyEntry.isVisible()) await legacyEntry.click()
  }
  await expect(page.getByTestId(`screen-${screenId}`)).toBeVisible()
  await waitForDrawerSettled(page)
}

async function openStaticScreen(page: Page, screenId: string) {
  if (page.viewportSize()?.width && page.viewportSize()!.width < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  await page.getByTestId(`nav-${screenId}`).click()
  await expect(page.getByTestId(`screen-${screenId}`)).toBeVisible()
  await waitForDrawerSettled(page)
}

async function waitForDrawerSettled(page: Page) {
  if ((page.viewportSize()?.width ?? 0) >= 820) return
  if (await page.locator('.app-sidebar').count()) {
    await expect(page.locator('.app-sidebar')).not.toHaveClass(/mobile-open/)
    await expect(page.locator('.mobile-scrim')).toHaveCount(0)
  } else {
    await expect(page.locator('.sidebar')).not.toHaveClass(/open/)
    await expect(page.locator('#scrim')).toBeHidden()
  }
  await page.waitForTimeout(260)
  await expect.poll(() => page.evaluate(() => window.scrollX)).toBe(0)
}

async function runAxe(page: Page) {
  const alreadyLoaded = await page.evaluate(() => Boolean((window as unknown as { axe?: unknown }).axe))
  if (!alreadyLoaded) await page.addScriptTag({ content: axeSource })
  return page.evaluate(async () => {
    const axe = (window as unknown as { axe: { run: (context: Document, options: unknown) => Promise<unknown> } }).axe
    return axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } })
  }) as Promise<{ violations: Array<{ id: string; impact: string | null; description: string; nodes: Array<{ target: string[] }> }> }>
}

async function capture(page: Page, testInfo: TestInfo, name: string) {
  const project = testInfo.project.name
  await mkdir(join(evidenceRoot, 'screenshots'), { recursive: true })
  await page.screenshot({ path: join(evidenceRoot, 'screenshots', `${project}-${name}.png`), fullPage: true })
  await expect(page).toHaveScreenshot(`${name}-${project}.png`, { fullPage: true, animations: 'disabled', maxDiffPixels: 100 })
}

test.beforeEach(async ({ page }) => {
  watchBrowser(page)
})

test.afterEach(async ({ page }, testInfo) => {
  const events = browserEvents.get(page)
  if (!events) return
  const safeId = testInfo.testId.replace(/[^a-zA-Z0-9_-]/g, '_')
  await saveJson(`browser-events-${safeId}.json`, events)
  browserEvents.delete(page)
})

test('RQU-UI-11 React PC/mobile critical journeys and safety boundaries', async ({ page }, testInfo) => {
  test.setTimeout(120_000)
  await page.goto('/')
  await openReactScreen(page, 'SCREEN-08')
  const backtest = page.getByTestId('screen-SCREEN-08')
  await backtest.getByRole('tab').nth(1).click()
  await expect(backtest.getByText('Risk', { exact: true })).toBeVisible()
  await expect(backtest.locator('button.primary-button')).toBeDisabled()
  await backtest.locator('input[type="number"]').fill('1.0')
  await expect(backtest.locator('button.primary-button')).toBeEnabled()
  await backtest.locator('button.primary-button').click()
  await expect(page.getByTestId('screen-SCREEN-09')).toBeVisible()

  await openReactScreen(page, 'SCREEN-10')
  const result = page.getByTestId('screen-SCREEN-10')
  await expect(result.locator('.five-metrics')).toBeVisible()
  await result.locator('button.primary-button').click()
  await expect(page.getByTestId('screen-SCREEN-11')).toBeVisible()
  await openReactScreen(page, 'SCREEN-12')
  await expect(page.getByTestId('screen-SCREEN-12').locator('table')).toBeVisible()

  await openReactScreen(page, 'SCREEN-14')
  const paperLive = page.getByTestId('screen-SCREEN-14')
  await expect(paperLive.locator('button:disabled')).toHaveCount(1)
  await paperLive.getByRole('button', { name: /移行確認/ }).click()
  await expect(page.getByTestId('screen-SCREEN-18')).toBeVisible()
  const gate = page.getByTestId('screen-SCREEN-18')
  await expect(gate.locator('button.primary-button')).toBeDisabled()
  await gate.locator('input[type="number"]').fill('1.0')
  await expect(gate.locator('button.primary-button')).toBeEnabled()
  await gate.locator('button.primary-button').click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByRole('dialog').getByRole('button', { name: '確認して記録' }).click()
  await expect(gate.locator('.inline-notice')).toBeVisible()

  await openReactScreen(page, 'SCREEN-17')
  const warning = page.getByTestId('screen-SCREEN-17')
  await warning.getByRole('button', { name: '対応済み' }).first().click()
  await expect(warning.getByText('WARN-002')).toBeVisible()
  await warning.getByRole('button', { name: '対応済み' }).first().click()
  await expect(warning.getByText('未対応の警告はありません')).toBeVisible()
  await capture(page, testInfo, 'react-safety')
})

test('RQU-UI-11 React exposes all ten common states with readable operation guidance', async ({ page }, testInfo) => {
  await page.goto('/')
  await openReactScreen(page, 'SCREEN-03')
  const screen = page.getByTestId('screen-SCREEN-03')
  for (const state of stateIds) {
    await screen.getByRole('button', { name: state, exact: true }).click()
    await expect(screen.getByTestId(`state-${state}`).first()).toBeVisible()
  }
  await capture(page, testInfo, 'react-states')
})

test('RQU-UI-13 React covers every common state on all 21 screens', async ({ page }, testInfo) => {
  test.setTimeout(180_000)
  await page.goto('/')
  let checked = 0
  for (const screenId of screenIds) {
    await openReactScreen(page, screenId)
    const screen = page.getByTestId(`screen-${screenId}`)
    for (const state of stateIds) {
      await screen.getByRole('button', { name: state, exact: true }).click()
      await expect(screen.getByTestId(`state-${state}`).first()).toBeVisible()
      checked += 1
    }
  }
  await saveJson(`state-matrix-react-${testInfo.project.name}.json`, { screenCount: screenIds.length, stateCount: stateIds.length, checked, scope: 'Reactインタラクティブ状態操作' })
  expect(checked).toBe(screenIds.length * stateIds.length)
})

test('RQU-UI-13 safety controls require editable inputs and confirmation records', async ({ page }) => {
  test.setTimeout(120_000)
  await page.goto('/')

  await openReactScreen(page, 'SCREEN-08')
  const backtest = page.getByTestId('screen-SCREEN-08')
  await backtest.getByRole('tab', { name: '網羅検証' }).click()
  await backtest.getByLabel('Entry期間 上限').fill('80')
  await expect(backtest.getByLabel('Entry期間 上限')).toHaveValue('80')
  await backtest.getByLabel('設定JSONを選択').setInputFiles({ name: 'rqu-ui-13.json', mimeType: 'application/json', buffer: Buffer.from('{"entryUpper":80}') })
  await expect(backtest.getByText('rqu-ui-13.json', { exact: true })).toBeVisible()

  await openReactScreen(page, 'SCREEN-04')
  const unitForm = page.getByTestId('screen-SCREEN-04')
  await unitForm.getByLabel('運用単位Risk').fill('1.0')
  await unitForm.getByLabel('銘柄').selectOption('M6A')
  await unitForm.getByLabel('時間足').selectOption('H4')
  await expect(unitForm.getByRole('button', { name: '保存' })).toBeDisabled()

  await openReactScreen(page, 'SCREEN-09')
  const run = page.getByTestId('run-RUN-20260811-002')
  await run.getByRole('button', { name: '取消' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByRole('dialog').getByRole('button', { name: '取消を記録' }).click()
  await expect(run.getByRole('status')).toBeVisible()

  await openReactScreen(page, 'SCREEN-06')
  const strategies = page.getByTestId('screen-SCREEN-06')
  await strategies.getByLabel(/操作理由/).fill('安全確認のため一時停止')
  await strategies.getByRole('button', { name: '無効化' }).first().click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByRole('dialog').getByRole('button', { name: '確認して記録' }).click()
  await expect(strategies.getByTestId('state-STOPPED')).toBeVisible()

  await openReactScreen(page, 'SCREEN-07')
  const strategyForm = page.getByTestId('screen-SCREEN-07')
  await strategyForm.getByLabel(/操作理由/).fill('パラメータの検証結果を保存')
  await strategyForm.getByRole('button', { name: '保存して新版' }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByRole('dialog').getByRole('button', { name: '確認して記録' }).click()
  await expect(strategyForm.getByText('設定版保存を操作記録へ残しました。', { exact: true })).toBeVisible()

  await openReactScreen(page, 'SCREEN-14')
  const paperLive = page.getByTestId('screen-SCREEN-14')
  await paperLive.getByLabel('Live自動承認モード').check()
  await paperLive.getByRole('button', { name: '移行確認' }).click()
  const gate = page.getByTestId('screen-SCREEN-18')
  await expect(gate.getByRole('radio', { name: 'スキップ（自動承認）' })).toBeChecked()
  await gate.getByLabel('Risk').fill('1.0')
  await gate.getByRole('button', { name: '移行を確認' }).click()
  await page.getByRole('dialog').getByRole('button', { name: '確認して記録' }).click()
  await expect(gate.getByText('Human Gate（スキップ（自動承認））の確認結果を操作記録へ残しました。Live実行は未接続です。', { exact: true })).toBeVisible()

  await openReactScreen(page, 'SCREEN-11')
  const detail = page.getByTestId('screen-SCREEN-11')
  await expect(detail.getByLabel('時間足')).toContainText('H1')
  await expect(detail.getByLabel('時間足')).toContainText('M30')
})

test('RQU-UI-11 React PC/mobile visual baselines and keyboard/Dialog boundaries', async ({ page }, testInfo) => {
  await page.goto('/')
  await expect(page.getByTestId('pilot-screen')).toBeVisible()
  await page.getByRole('button', { name: 'Base UI Dialogを開く' }).click()
  const dialog = page.getByRole('dialog').first()
  await expect(dialog).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()
  await openReactScreen(page, 'SCREEN-02')
  await page.getByTestId('nav-SCREEN-20').focus()
  await expect(page.getByTestId('nav-SCREEN-20')).toBeFocused()
  await capture(page, testInfo, 'react-home')
})

test('RQU-UI-11 React all 21 screen routes are reachable on the configured viewport', async ({ page }, testInfo) => {
  await page.goto('/')
  for (const screenId of screenIds) {
    await openReactScreen(page, screenId)
    await expect(page.getByTestId(`screen-${screenId}`)).toHaveAttribute('data-testid', `screen-${screenId}`)
  }
  await saveJson(`react-route-summary-${testInfo.project.name}.json`, { screenIds, count: screenIds.length, seed: '20260811' })
})

test('RQU-UI-11 React active screens pass critical/serious axe checks', async ({ page }, testInfo) => {
  test.setTimeout(180_000)
  await page.goto('/')
  const results: Array<{ screenId: string; violations: unknown[]; criticalOrSerious: unknown[] }> = []
  for (const screenId of screenIds) {
    await openReactScreen(page, screenId)
    const axe = await runAxe(page)
    const criticalOrSerious = axe.violations.filter((item) => item.impact === 'critical' || item.impact === 'serious')
    results.push({ screenId, violations: axe.violations, criticalOrSerious })
    expect(criticalOrSerious, `${screenId} has critical/serious axe violations`).toEqual([])
  }
  await saveJson(`a11y-react-${testInfo.project.name}.json`, { screenCount: screenIds.length, results })
})

test('RQU-UI-11 static HTML reaches all 21 screens with no external requests', async ({ page }, testInfo) => {
  await page.goto(pathToFileURL(staticMock).href)
  await expect(page.getByTestId('ui-mock-document')).toBeVisible()
  for (const screenId of screenIds) {
    await openStaticScreen(page, screenId)
    if (criticalScreenIds.includes(screenId)) await capture(page, testInfo, `static-${screenId}`)
  }
  const events = browserEvents.get(page)
  expect(events?.externalRequests ?? [], 'static UI must stay offline').toEqual([])
  await capture(page, testInfo, 'static-all-routes')
  await saveJson(`static-route-summary-${testInfo.project.name}.json`, { screenIds, count: screenIds.length, externalRequests: events?.externalRequests ?? [] })
})

test('RQU-UI-11 static HTML active screens pass critical/serious axe checks', async ({ page }, testInfo) => {
  test.setTimeout(180_000)
  await page.goto(pathToFileURL(staticMock).href)
  const results: Array<{ screenId: string; violations: unknown[]; criticalOrSerious: unknown[] }> = []
  for (const screenId of screenIds) {
    await openStaticScreen(page, screenId)
    const axe = await runAxe(page)
    const criticalOrSerious = axe.violations.filter((item) => item.impact === 'critical' || item.impact === 'serious')
    results.push({ screenId, violations: axe.violations, criticalOrSerious })
    expect(criticalOrSerious, `${screenId} has critical/serious axe violations`).toEqual([])
  }
  await saveJson(`a11y-static-${testInfo.project.name}.json`, { screenCount: screenIds.length, results })
})
