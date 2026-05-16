import { expect, test } from '@playwright/test';

import { login } from '../auth/common/auth';

test.describe('样机列表', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
    await page.goto('/meter/list');
    await page.waitForLoadState('networkidle');
  });

  test('页面正确加载', async ({ page }) => {
    await expect(page.locator('table')).toBeVisible();
  });

  test('搜索样机', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="序列号"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill('DLMS');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('networkidle');
      await expect(page.locator('table')).toBeVisible();
    }
  });
});
