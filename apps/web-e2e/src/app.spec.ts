import { expect, test } from '@playwright/test';

test('lobby shows healthy backend and connected WebSocket states', async ({ page }) => {
  await page.goto('/lobby');
  await expect(page.getByRole('heading', { name: 'Kvartalno Kare' })).toBeVisible();
  await expect(page.getByTestId('health-state')).toHaveText('healthy');
  await expect(page.getByTestId('ws-state')).toHaveText('connected');
});

test('table route presents the complete private table state', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/table');
  await expect(page.getByLabel("Texas Hold'em table")).toBeVisible();
  await expect(page.locator('[data-seat-number]')).toHaveCount(8);
  await expect(page.locator('[data-seat-status="occupied"]')).toHaveCount(5);
  await expect(page.locator('[data-seat-status="available"]')).toHaveCount(3);
  await expect(page.getByTestId('hero-position').locator('[data-seat-number="8"]')).toBeVisible();
  await expect(page.getByRole('img', { name: 'Ace of spades' })).toBeVisible();
  await expect(page.getByRole('img', { name: 'Queen of hearts' })).toBeVisible();
  await expect(page.getByRole('img', { name: 'Face-down card' })).toHaveCount(6);
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

  const geometry = await page.evaluate(() => {
    const stage = document.querySelector<HTMLElement>('.table-stage')?.getBoundingClientRect();
    const hero = document.querySelector<HTMLElement>('.seat-position[data-position="bottom-center"]')?.getBoundingClientRect();
    const others = [...document.querySelectorAll<HTMLElement>('.seat-position:not([data-position="bottom-center"])')]
      .map((seat) => seat.getBoundingClientRect());
    if (!stage || !hero) throw new Error('Expected table and hero geometry.');
    return {
      tableCenterX: stage.left + stage.width / 2,
      heroCenterX: hero.left + hero.width / 2,
      heroCenterY: hero.top + hero.height / 2,
      highestOtherBottomCentre: Math.max(...others.map((seat) => seat.top + seat.height / 2)),
    };
  });
  expect(Math.abs(geometry.heroCenterX - geometry.tableCenterX)).toBeLessThan(20);
  expect(geometry.heroCenterY).toBeGreaterThan(geometry.highestOtherBottomCentre + 20);
});

for (const viewport of [{ name: 'desktop', width: 1440, height: 900 }, { name: 'mobile', width: 390, height: 844 }]) {
  test(`${viewport.name} table has no horizontal overflow or clipped controls`, async ({ page }, testInfo) => {
    await page.setViewportSize(viewport);
    await page.goto('/table');
    const measurements = await page.evaluate(() => ({
      bodyWidth: document.body.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      buttons: [...document.querySelectorAll('button')].map((button) => button.getBoundingClientRect().toJSON()),
      seats: [...document.querySelectorAll<HTMLElement>('.seat-panel')].map((seat) => seat.getBoundingClientRect().toJSON()),
      constrainedContent: [...document.querySelectorAll<HTMLElement>('.identity-details, .contribution')].map((element) => {
        const content = element.getBoundingClientRect();
        const seat = element.closest<HTMLElement>('.seat-panel')?.getBoundingClientRect();
        return { left: content.left, right: content.right, seatLeft: seat?.left, seatRight: seat?.right, overflowX: getComputedStyle(element).overflowX };
      }),
    }));
    expect(measurements.bodyWidth).toBeLessThanOrEqual(measurements.viewportWidth);
    for (const button of measurements.buttons) {
      expect(button.left).toBeGreaterThanOrEqual(0);
      expect(button.right).toBeLessThanOrEqual(viewport.width);
      expect(button.bottom).toBeLessThanOrEqual(viewport.height);
      expect(button.height).toBeGreaterThanOrEqual(44);
    }
    for (const content of measurements.constrainedContent) {
      expect(content.left).toBeGreaterThanOrEqual((content.seatLeft ?? content.left) - 1);
      expect(content.right).toBeLessThanOrEqual((content.seatRight ?? content.right) + 1);
      expect(content.overflowX).toBe('hidden');
    }
    for (let first = 0; first < measurements.seats.length; first++) {
      for (let second = first + 1; second < measurements.seats.length; second++) {
        const a = measurements.seats[first];
        const b = measurements.seats[second];
        const overlapWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const overlapHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        expect(overlapWidth > 1 && overlapHeight > 1).toBe(false);
      }
    }
    await page.screenshot({ path: testInfo.outputPath(`${viewport.name}-table.png`), fullPage: true });
  });
}

test('reduced motion disables table animations while preserving turn information', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/table');

  const motion = await page.evaluate(() => {
    const stylesFor = (selector: string) => {
      const element = document.querySelector<HTMLElement>(selector);
      if (!element) throw new Error(`Missing ${selector}`);
      const styles = getComputedStyle(element);
      return { animationName: styles.animationName, transitionDuration: styles.transitionDuration };
    };
    return {
      activeSeat: stylesFor('.current-turn'),
      actionPanel: stylesFor('.action-panel'),
      actionButton: stylesFor('.action-panel button'),
    };
  });

  expect(motion.activeSeat.animationName).toBe('none');
  expect(motion.actionPanel.animationName).toBe('none');
  expect(motion.actionPanel.transitionDuration).toBe('0s');
  expect(motion.actionButton.transitionDuration).toBe('0s');
  await expect(page.getByText('Your turn')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Call 20' })).toBeVisible();
});

test('an unknown route redirects to the lobby', async ({ page }) => {
  await page.goto('/not-a-route');
  await expect(page).toHaveURL(/\/lobby$/);
  await expect(page.getByRole('heading', { name: 'Kvartalno Kare' })).toBeVisible();
});
