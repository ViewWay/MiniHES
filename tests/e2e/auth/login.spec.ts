import { expect, test } from '@playwright/test';

import { login } from './common/auth';

test.describe('登录页', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/auth/login');
  });

  test('页面正常加载，包含登录表单', async ({ page }) => {
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('[name="captcha-action"]')).toBeVisible();
  });

  test('空表单提交显示校验提示', async ({ page }) => {
    await page
      .getByRole('button', { name: /登录|sign|submit/i })
      .first()
      .click();
    await expect(page.getByText(/请输入|required/i).first()).toBeVisible();
  });

  test('错误凭据显示错误提示', async ({ page }) => {
    await login(page, 'wrong', 'wrong');
    await expect(
      page.getByText(/用户名或密码|incorrect/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('admin 账号登录成功', async ({ page }) => {
    await login(page, 'admin', '123456');
    await expect(page).toHaveURL(/\/(dashboard|analytics|workspace)/, {
      timeout: 10_000,
    });
  });

  test('engineer 账号登录成功', async ({ page }) => {
    await login(page, 'engineer', '123456');
    await expect(page).toHaveURL(/\/analytics/, { timeout: 10_000 });
  });

  test('tester 账号登录成功', async ({ page }) => {
    await login(page, 'tester', '123456');
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  });
});
