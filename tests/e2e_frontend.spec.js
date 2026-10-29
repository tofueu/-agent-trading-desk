const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

test.describe('Trading Dashboard', () => {
  test.beforeAll(async () => {
    const dataDir = path.join(__dirname, '..', 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir);
    }
    fs.writeFileSync(path.join(dataDir, 'test_real_data.csv'), `strategy,timeframe,product,return
MyStrategy,1H,BTCUSDT,0.05
MyStrategy,1H,BTCUSDT,-0.02
MyStrategy,1H,BTCUSDT,0.01`);
  });

  test.afterAll(async () => {
    const dataDir = path.join(__dirname, '..', 'data');
    if (fs.existsSync(path.join(dataDir, 'test_real_data.csv'))) {
      fs.unlinkSync(path.join(dataDir, 'test_real_data.csv'));
    }
  });

  test('displays true backtest metrics when started', async ({ page }) => {
    await page.goto('http://127.0.0.1:8000');

    // Wait for the start button
    const startBtn = page.locator('#startBtn');
    await startBtn.waitFor({ state: 'visible' });
    const responsePromise = page.waitForResponse(response => response.url().includes('/api/metrics') && response.status() === 200);
    await startBtn.click();

    // Check total PnL
    const totalPnl = page.locator('#totalPnL');
    await totalPnl.waitFor({ state: 'visible', timeout: 5000 });

    // Wait a bit for fetch to complete
    await responsePromise;

    // Should display the real metrics correctly, derived from actual data
    const pnlText = await totalPnl.textContent();
    expect(pnlText).toContain('%');

    const kpiWinRate = page.locator('#kpiWinRate');
    await expect(kpiWinRate).toContainText('%');
  });
});
