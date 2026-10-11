import { expect, test } from '@playwright/test';

test('lobby shows healthy backend and connected WebSocket states', async ({ page }) => {
  await page.goto('/lobby');
  await expect(page.getByRole('heading', { name: 'Kvartalno Kare' })).toBeVisible();
  await expect(page.getByTestId('health-state')).toHaveText('healthy');
  await expect(page.getByTestId('ws-state')).toHaveText('connected');
});

test('table route presents the complete private table state', async ({ page }) => {
  await page.goto('/table');
  await expect(page.getByLabel("Texas Hold'em table")).toBeVisible();
  await expect(page.locator('[data-seat-number]')).toHaveCount(8);
  await expect(page.locator('[data-seat-status="occupied"]')).toHaveCount(5);
  await expect(page.locator('[data-seat-status="available"]')).toHaveCount(3);
  await expect(page.getByTestId('hero-position').locator('[data-seat-number="8"]')).toBeVisible();
  await expect(page.getByLabel('Ace of spades')).toBeVisible();
  await expect(page.getByLabel('Queen of hearts')).toBeVisible();
  await expect(page.getByLabel('Face-down card')).toHaveCount(6);
  await expect(page.locator('[title="Dealer"]')).toBeVisible();
  await expect(page.locator('[title="Small blind"]')).toBeVisible();
  await expect(page.locator('[title="Big blind"]')).toBeVisible();
  await expect(page.getByText('180 chips')).toBeVisible();
  await expect(page.getByLabel('Community cards')).toBeVisible();
  await expect(page.getByText('Your turn')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Fold' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Call 20' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Raise to 80' })).toBeVisible();
  expect(await page.locator('body').textContent()).not.toContain('King');
});

for (const viewport of [{ name: 'desktop', width: 1440, height: 900 }, { name: 'mobile', width: 390, height: 844 }]) {
  test(`${viewport.name} table has no horizontal overflow or clipped controls`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto('/table');
    const measurements = await page.evaluate(() => ({
      bodyWidth: document.body.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      buttons: [...document.querySelectorAll('button')].map((button) => button.getBoundingClientRect().toJSON()),
    }));
    expect(measurements.bodyWidth).toBeLessThanOrEqual(measurements.viewportWidth);
    for (const button of measurements.buttons) {
      expect(button.left).toBeGreaterThanOrEqual(0);
      expect(button.right).toBeLessThanOrEqual(viewport.width);
      expect(button.bottom).toBeLessThanOrEqual(viewport.height);
      expect(button.height).toBeGreaterThanOrEqual(44);
    }
  });
}

test('an unknown route redirects to the lobby', async ({ page }) => {
  await page.goto('/not-a-route');
  await expect(page).toHaveURL(/\/lobby$/);
  await expect(page.getByRole('heading', { name: 'Kvartalno Kare' })).toBeVisible();
});
