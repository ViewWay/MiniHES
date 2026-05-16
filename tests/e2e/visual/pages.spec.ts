import { expect, test } from '@playwright/test';

import { login } from '../auth/common/auth';

const pages = [
  { name: '仪表盘', path: '/dashboard/workspace' },
  { name: '样机列表', path: '/meter/list' },
  { name: '任务列表', path: '/task/list' },
  { name: '数据分析', path: '/analysis/daily' },
  { name: '系统用户', path: '/system/user' },
];

for (const { name, path } of pages) {
  test(`${name} 视觉回归`, async ({ page }) => {
    await login(page);
    await page.goto(path);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    await expect(page).toHaveScreenshot(`${name}.png`, {
      maxDiffPixelRatio: 0.01,
      fullPage: true,
    });
  });
}
