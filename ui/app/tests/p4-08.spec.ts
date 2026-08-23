import { expect, test, type Page } from '@playwright/test'
import axe from 'axe-core'
import { mkdir } from 'node:fs/promises'
import { join, resolve } from 'node:path'
import { p4ScreenContracts } from '../src/p4Contract'
import type { ScreenId } from '../src/ui'

const screenIds = Array.from({ length: 21 }, (_, index) => `SCREEN-${String(index + 1).padStart(2, '0')}`)
const stateIds = ['NORMAL', 'LOADING', 'EMPTY', 'REQUIRED', 'WARNING', 'STOPPED', 'FAILED', 'RECOVERY', 'HUMAN-GATE', 'UNAPPROVED'] as const
const evidenceRoot = resolve(process.cwd(), '../../tests/evidence/phase4/RUN-P4-04D-001/p4-08-playwright/screenshots')

async function openScreen(page: Page, screenId: string) {
  if ((page.viewportSize()?.width ?? 0) < 820) {
    const menu = page.getByRole('button', { name: 'メニューを開く' })
    if (await menu.isVisible()) await menu.click()
  }
  if (screenId === 'SCREEN-09' || screenId === 'SCREEN-10') {
    await page.getByTestId('nav-SCREEN-08').click()
    const legacyEntry = page.getByRole('button', { name: '旧Backtest履歴表示を開く' })
    if (await legacyEntry.isVisible()) await legacyEntry.click()
    if ((page.viewportSize()?.width ?? 0) < 820) {
      const menu = page.getByRole('button', { name: 'メニューを開く' })
      if (await menu.isVisible()) await menu.click()
    }
  }
  await page.getByTestId(`nav-${screenId}`).click()
  if (screenId === 'SCREEN-08') {
    const legacyEntry = page.getByRole('button', { name: '旧Backtest履歴表示を開く' })
    if (await legacyEntry.isVisible()) await legacyEntry.click()
  }
  await expect(page.getByTestId(`screen-${screenId}`)).toBeVisible()
}

test('P4-08: 21 screens bind fixed API contracts and preserve the boundary', async ({ page }, testInfo) => {
  const externalRequests: string[] = []
  page.on('request', (request) => {
    const url = request.url()
    if (!url.startsWith('http://127.0.0.1:4173') && !url.startsWith('http://127.0.0.1:8765') && !url.startsWith('data:') && !url.startsWith('blob:') && !url.startsWith('about:')) externalRequests.push(url)
  })
  await page.goto('/')
  await mkdir(join(evidenceRoot, testInfo.project.name), { recursive: true })
  for (const screenId of screenIds) {
    await openScreen(page, screenId)
    const typedScreenId = screenId as ScreenId
    const expected = p4ScreenContracts[typedScreenId]
    const contract = page.getByTestId(`p4-contract-${screenId}`)
    await expect(contract).toHaveAttribute('data-p4-scope', expected.scope)
    await expect(contract).toHaveAttribute('data-api-p4-ids', expected.apiIds.join(','))
    await expect(contract).toHaveAttribute('data-reason-id', expected.reasonId)
    const screen = page.getByTestId(`screen-${screenId}`)
    if (expected.scope === 'BOUNDARY_ONLY') {
      await expect(page.getByTestId(`screen-${screenId}`)).toHaveAttribute('data-reason-id', 'P4_OUT_OF_SCOPE')
      await expect(page.getByText('P4では実行できません')).toBeVisible()
    } else {
      if (expected.scope === 'P4_BOUNDARY_TARGET') await expect(screen).toHaveAttribute('data-reason-id', expected.reasonId)
      for (const stateId of stateIds) await expect(screen.getByRole('button', { name: stateId, exact: true })).toBeVisible()
    }
    await page.screenshot({ path: join(evidenceRoot, testInfo.project.name, `${screenId}.png`), fullPage: true })
  }
  expect(externalRequests).toEqual([])
})

test('P4-08: target and boundary screens exercise the ten common states', async ({ page }) => {
  test.setTimeout(120_000)
  await page.goto('/')
  let exercised = 0
  for (const screenId of screenIds) {
    await openScreen(page, screenId)
    const screen = page.getByTestId(`screen-${screenId}`)
    const expected = p4ScreenContracts[screenId as ScreenId]
    if (expected.scope === 'BOUNDARY_ONLY') {
      await expect(screen.getByTestId('state-UNAPPROVED').first()).toBeVisible()
      continue
    }
    for (const stateId of stateIds) {
      await screen.getByRole('button', { name: stateId, exact: true }).click()
      await expect(screen.getByTestId(`state-${stateId}`).first()).toBeVisible()
      exercised += 1
    }
  }
  expect(exercised).toBe(13 * stateIds.length)
})

test('P4-08: axe has no critical or serious violations in the 21 fixed states', async ({ page }) => {
  await page.goto('/')
  await page.addScriptTag({ content: axe.source })
  for (const screenId of screenIds) {
    await openScreen(page, screenId)
    const results = await page.evaluate(async () => (window as unknown as { axe: typeof axe }).axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] } }))
    const blocking = results.violations.filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
    expect(blocking, `${screenId} critical/serious axe violations`).toEqual([])
  }
})
