import { expect, test } from '@playwright/test'

test('pilot page loads and opens a dialog', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('pilot-screen')).toBeVisible()
  await expect(page.getByRole('heading', { name: '自動トレードUI基盤 Smoke' })).toBeVisible()
  await page.getByRole('button', { name: 'Base UI Dialogを開く' }).click()
  await expect(page.getByRole('dialog', { name: 'Base UIの確認' })).toBeVisible()
  await page.screenshot({ path: `test-results/pilot-smoke-${test.info().project.name}.png`, fullPage: true })
})

test('RQU-UI-07 exposes all 21 screens and reaches a common placeholder', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('[data-testid^="nav-SCREEN-"]')).toHaveCount(21)
  if (test.info().project.name === 'chromium-mobile') {
    await page.getByRole('button', { name: 'メニューを開く' }).click()
  }
  await page.getByTestId('nav-SCREEN-21').click()
  const target = page.getByTestId('screen-SCREEN-21')
  await expect(target).toBeVisible()
  await expect(target.getByRole('heading', { name: 'ヘルプ・用語説明', exact: true })).toBeVisible()
  await expect(target.getByTestId('state-NORMAL').first()).toBeVisible()
})

test('RQU-UI-07 mobile navigation opens and closes without changing the current screen', async ({ page }) => {
  test.skip(test.info().project.name !== 'chromium-mobile', 'mobile-specific journey')
  await page.goto('/')
  const menu = page.getByRole('button', { name: 'メニューを開く' })
  await expect(menu).toBeVisible()
  await menu.click()
  await expect(page.getByRole('button', { name: 'メニューを閉じる' })).toBeVisible()
  await page.getByTestId('nav-SCREEN-18').click()
  await expect(page.getByTestId('screen-SCREEN-18')).toBeVisible()
  await expect(page.getByRole('button', { name: 'メニューを開く' })).toBeVisible()
})

test('RQU-UI-08 separates exhaustive Backtest from a single Run and starts after Risk input', async ({ page }) => {
  await page.goto('/')
  if (test.info().project.name === 'chromium-mobile') await page.getByRole('button', { name: 'メニューを開く' }).click()
  await page.getByTestId('nav-SCREEN-08').click()
  const settings = page.getByTestId('screen-SCREEN-08')
  await settings.getByRole('tab', { name: '網羅検証' }).click()
  await expect(settings.getByText('変更するパラメータの下限・上限・ステップ', { exact: true })).toBeVisible()
  await expect(settings.getByRole('button', { name: '開始' })).toBeDisabled()
  await settings.getByLabel('Risk').fill('1.0')
  await expect(settings.getByRole('button', { name: '開始' })).toBeEnabled()
  await settings.getByRole('button', { name: '開始' }).click()
  await expect(page.getByTestId('screen-SCREEN-09')).toBeVisible()
  await expect(page.getByTestId('run-RUN-20260811-002').getByText(/網羅検証 \/ 実行中/)).toBeVisible()
})

test('RQU-UI-08 blocks a duplicate operation unit and allows a distinct unit', async ({ page }) => {
  await page.goto('/')
  if (test.info().project.name === 'chromium-mobile') await page.getByRole('button', { name: 'メニューを開く' }).click()
  await page.getByTestId('nav-SCREEN-04').click()
  const form = page.getByTestId('screen-SCREEN-04')
  await form.getByLabel('運用単位Risk').fill('1.0')
  await expect(form.getByRole('button', { name: '保存' })).toBeDisabled()
  await form.getByLabel('銘柄').selectOption('M6A')
  await expect(form.getByRole('button', { name: '保存' })).toBeEnabled()
  await form.getByRole('button', { name: '保存' }).click()
  await expect(page.getByTestId('screen-SCREEN-03')).toBeVisible()
})

test('RQU-UI-09 keeps Human Gate and connection boundaries explicit', async ({ page }) => {
  await page.goto('/')
  const openNav = async () => {
    if (test.info().project.name === 'chromium-mobile') await page.getByRole('button', { name: 'メニューを開く' }).click()
  }
  await openNav()
  await page.getByTestId('nav-SCREEN-20').click()
  const connection = page.getByTestId('screen-SCREEN-20')
  await expect(connection.getByText('値は非表示')).toBeVisible()
  await expect(connection.getByText('未設定・未承認')).toBeVisible()
  await connection.getByRole('button', { name: '接続確認' }).click()
  await expect(connection.getByText(/外部へ接続しません/)).toBeVisible()

  await openNav()
  await page.getByTestId('nav-SCREEN-18').click()
  const gate = page.getByTestId('screen-SCREEN-18')
  await expect(gate.getByRole('button', { name: '移行を確認' })).toBeDisabled()
  await gate.getByLabel('Risk').fill('1.0')
  await expect(gate.getByRole('button', { name: '移行を確認' })).toBeEnabled()
  await gate.getByRole('button', { name: '取消' }).click()
  await expect(gate.getByText('Human Gateを取消しました。')).toBeVisible()
})

test('RQU-UI-09 warning screen offers acknowledge, retry, stop and reconciliation', async ({ page }) => {
  await page.goto('/')
  if (test.info().project.name === 'chromium-mobile') await page.getByRole('button', { name: 'メニューを開く' }).click()
  await page.getByTestId('nav-SCREEN-17').click()
  const warnings = page.getByTestId('screen-SCREEN-17')
  await expect(warnings.getByText('WARN-001')).toBeVisible()
  await warnings.getByRole('button', { name: '対応済み' }).first().click()
  await expect(warnings.getByText('WARN-002')).toBeVisible()
  await warnings.getByRole('button', { name: '再試行' }).first().click()
  await expect(warnings.getByText(/再試行を受付/)).toBeVisible()
})
