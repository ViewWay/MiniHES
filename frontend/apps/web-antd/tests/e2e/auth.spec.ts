import { expect, test } from '@playwright/test';

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
  });

  test('should display MiniHES branding', async ({ page }) => {
    const title = await page.title();
    expect(title).toContain('MiniHES');

    // Check description text
    await expect(page.getByText('云端智能电表抄表管理系统')).toBeVisible();
    await expect(
      page.getByText('DLMS/COSEM协议 · 多通信方式适配 · 实时数据采集'),
    ).toBeVisible();
  });

  test('should show copyright with MiniHES', async ({ page }) => {
    await expect(page.getByText('Copyright © 2025')).toBeVisible();
    await expect(page.getByRole('link', { name: 'MiniHES' })).toBeVisible();
  });

  test('should have login form elements', async ({ page }) => {
    await expect(
      page.getByRole('textbox', { name: '请输入用户名' }),
    ).toBeVisible();
    await expect(page.getByRole('textbox', { name: '密码' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'login' })).toBeVisible();
  });

  test('should fill username and password on account select', async ({
    page,
  }) => {
    // Default selection fills credentials
    const usernameInput = page.getByRole('textbox', { name: '请输入用户名' });
    const passwordInput = page.getByRole('textbox', { name: '密码' });

    await expect(usernameInput).toHaveValue('vben');
    await expect(passwordInput).toHaveValue('123456');
  });
});
