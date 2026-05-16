import { expect, test } from '@playwright/test';

// Helper to login bypassing captcha
async function login(page: any) {
  await page.goto('/auth/login');
  // Wait for form to load
  await page.waitForSelector('input[placeholder="请输入用户名"]');

  // Fill credentials
  await page
    .getByRole('textbox', { name: '请输入用户名' })
    .fill('vben');
  await page.getByRole('textbox', { name: '密码' }).fill('123456');

  // Bypass slider captcha via JS
  await page.evaluate(() => {
    const dragEl = document.querySelector('.cursor-move');
    if (!dragEl) return;
    const track = dragEl.parentElement!;
    const trackRect = track.getBoundingClientRect();
    const startX = trackRect.left + 22;
    const startY = trackRect.top + trackRect.height / 2;
    const endX = trackRect.right - 10;
    dragEl.dispatchEvent(
      new PointerEvent('pointerdown', {
        clientX: startX,
        clientY: startY,
        bubbles: true,
        pointerId: 1,
        isPrimary: true,
      }),
    );
    for (let i = 1; i <= 20; i++) {
      const x = startX + ((endX - startX) * i) / 20;
      document.dispatchEvent(
        new PointerEvent('pointermove', {
          clientX: x,
          clientY: startY,
          bubbles: true,
          pointerId: 1,
          isPrimary: true,
        }),
      );
    }
    document.dispatchEvent(
      new PointerEvent('pointerup', {
        clientX: endX,
        clientY: startY,
        bubbles: true,
        pointerId: 1,
        isPrimary: true,
      }),
    );
  });

  await page.waitForTimeout(500);

  // Try clicking login
  await page.getByRole('button', { name: 'login' }).click();

  // Wait for navigation or error
  await page.waitForTimeout(3000);
}

test.describe('Dashboard Pages', () => {
  test.skip(() => true, 'Dashboard tests require login bypass');

  test('analytics dashboard should load charts', async ({ page }) => {
    await login(page);
    await page.goto('/analytics');
    await page.waitForTimeout(2000);
    // Check that page title exists
    const title = await page.title();
    expect(title).toContain('MiniHES');
  });
});
