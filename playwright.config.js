const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests',
  use: {
    headless: true,
  },
  webServer: {
    command: 'python3 backend/app.py & python3 -m http.server 8000',
    port: 8000,
    reuseExistingServer: true,
  },
});
