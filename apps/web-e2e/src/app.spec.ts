import { expect, test } from '@playwright/test';

test('lobby shows healthy backend and connected WebSocket states', async ({ page }) => {
  await page.goto('/lobby');
  await expect(page.getByRole('heading', { name: 'Kvartalno Kare' })).toBeVisible();
  await expect(page.getByTestId('health-state')).toHaveText('healthy');
  await expect(page.getByTestId('ws-state')).toHaveText('connected');
});

test('table route shows the gameplay placeholder', async ({ page }) => {
  await page.goto('/table');
  await expect(page.getByRole('heading', { name: 'Gameplay is not implemented' })).toBeVisible();
  await expect(page.getByRole('link', { name: /Back to lobby/ })).toBeVisible();
});

test('an unknown route redirects to the lobby', async ({ page }) => {
  await page.goto('/not-a-route');
  await expect(page).toHaveURL(/\/lobby$/);
  await expect(page.getByRole('heading', { name: 'Kvartalno Kare' })).toBeVisible();
});
