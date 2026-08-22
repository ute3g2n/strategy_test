import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  outputDir: 'test-results/p5r2-manual-artifacts',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command: 'py -3 scripts/phase5r/p5r2_web_product_api_server.py --port 8765',
      url: 'http://127.0.0.1:8765/health',
      cwd: '../..',
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: 'npm run preview -- --host 127.0.0.1',
      url: 'http://127.0.0.1:4173',
      cwd: '.',
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
  projects: [
    { name: 'chromium-desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 900 } } },
    { name: 'chromium-mobile', use: { ...devices['Pixel 5'], browserName: 'chromium', viewport: { width: 390, height: 844 } } },
  ],
})
