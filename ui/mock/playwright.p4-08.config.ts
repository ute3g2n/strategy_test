import { defineConfig, devices } from '@playwright/test'
import { resolve } from 'node:path'

const evidenceRoot = resolve(process.cwd(), '../../tests/evidence/phase4/RUN-P4-04D-001/p4-08-playwright')

export default defineConfig({
  testDir: './tests',
  testMatch: '**/p4-08.spec.ts',
  fullyParallel: false,
  reporter: [['html', { outputFolder: resolve(evidenceRoot, 'playwright-report'), open: 'never' }], ['json', { outputFile: resolve(evidenceRoot, 'results.json') }], ['list']],
  outputDir: resolve(evidenceRoot, 'test-results'),
  use: { baseURL: 'http://127.0.0.1:4173', trace: 'retain-on-failure', screenshot: 'only-on-failure', video: 'retain-on-failure' },
  webServer: { command: 'npm run preview -- --host 127.0.0.1', url: 'http://127.0.0.1:4173', reuseExistingServer: false, timeout: 120_000 },
  projects: [
    { name: 'chromium-desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 900 } } },
    { name: 'chromium-mobile', use: { ...devices['Pixel 5'], browserName: 'chromium', viewport: { width: 390, height: 844 } } },
  ],
})
