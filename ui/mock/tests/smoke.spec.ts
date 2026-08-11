import { expect, test } from '@playwright/test'

test('pilot page loads and opens a dialog', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByTestId('pilot-screen')).toBeVisible()
  await expect(page.getByRole('heading', { name: '自動トレードUI基盤 Smoke' })).toBeVisible()
  await page.getByRole('button', { name: 'Base UI Dialogを開く' }).click()
  await expect(page.getByRole('dialog', { name: 'Base UIの確認' })).toBeVisible()
  await page.screenshot({ path: `test-results/pilot-smoke-${test.info().project.name}.png`, fullPage: true })
})
