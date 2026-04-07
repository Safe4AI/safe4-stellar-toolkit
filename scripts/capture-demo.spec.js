const { test, expect } = require('@playwright/test');
const path = require('node:path');
const fs = require('node:fs');

const outputDir = path.join(process.cwd(), 'docs', 'assets');

test('capture demo screenshots', async ({ page }) => {
  fs.mkdirSync(outputDir, { recursive: true });

  await page.goto('http://127.0.0.1:8080/demo', { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: 'Safe4 Stellar Toolkit' })).toBeVisible();
  await page.screenshot({ path: path.join(outputDir, 'demo-home.png'), fullPage: true });

  await page.getByRole('button', { name: 'Start demo flow' }).click();
  await page.waitForTimeout(500);
  await expect(page.getByText('"status": "payment_required"')).toBeVisible();
  await page.screenshot({ path: path.join(outputDir, 'demo-payment-required.png'), fullPage: true });

  await page.getByRole('button', { name: 'Create mock proof' }).click();
  await page.waitForTimeout(500);
  await page.getByRole('button', { name: 'Retry paid call' }).click();
  await page.waitForTimeout(750);
  await expect(page.getByText('"status": "AUTHORIZED"')).toBeVisible();
  await page.screenshot({ path: path.join(outputDir, 'demo-authorized.png'), fullPage: true });
});
