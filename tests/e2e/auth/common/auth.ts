import type { Page } from '@playwright/test';

export async function login(
  page: Page,
  username: string = 'admin',
  password: string = '123456',
) {
  await page.goto('/auth/login');
  await page.locator('input[name="username"]').fill(username);
  await page.locator('input[type="password"]').fill(password);

  const slider = page.locator('[name="captcha-action"]');
  const box = await slider.boundingBox();
  if (box) {
    await slider.hover();
    await page.mouse.down();
    await page.mouse.move(box.x + box.width + 20, box.y, { steps: 10 });
    await page.mouse.up();
  }

  await page
    .getByRole('button', { name: /登录|sign|submit/i })
    .first()
    .click();
}
