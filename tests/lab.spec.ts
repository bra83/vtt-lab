import { test, expect } from '@playwright/test';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

test('WWN piloto interativo funciona em 415x915', async ({ page }) => {
  const file = path.resolve('current/index.html');
  await page.goto(pathToFileURL(file).href);

  const map = page.getByTestId('hex-map');
  const party = page.getByTestId('party-marker');
  await expect(page.getByTestId('vtt-lab-ready')).toBeVisible();
  expect(await page.viewportSize()).toEqual({ width: 415, height: 915 });
  await expect(page.getByText('1 hex = 6 milhas')).toBeVisible();
  await expect(map).toHaveAttribute('data-centered', 'true');
  await expect(party).toHaveAttribute('data-current', 'Colinas das Brumas');

  await page.screenshot({ path: 'screenshots/wwn-piloto-inicial-415x915.png' });

  const scale0 = Number(await map.getAttribute('data-scale'));
  await page.getByTestId('zoom-in').click();
  const scale1 = Number(await map.getAttribute('data-scale'));
  expect(scale1).toBeGreaterThan(scale0);

  const beforePan = await map.getAttribute('data-pan-x');
  const box = await map.boundingBox();
  if (!box) throw new Error('Mapa sem bounding box');
  await page.mouse.move(box.x + 310, box.y + 310);
  await page.mouse.down();
  await page.mouse.move(box.x + 260, box.y + 275, { steps: 6 });
  await page.mouse.up();
  await expect(map).toHaveAttribute('data-centered', 'false');
  expect(await map.getAttribute('data-pan-x')).not.toBe(beforePan);

  await page.getByTestId('center-map').click();
  await expect(map).toHaveAttribute('data-centered', 'true');

  await page.getByTestId('fog-zone-left').click();
  await expect(page.getByRole('heading', { name: 'COLINAS DAS BRUMAS' })).toBeVisible();

  const beforePinch = Number(await map.getAttribute('data-scale'));
  await map.dispatchEvent('pointerdown', { pointerId: 11, pointerType: 'touch', clientX: 150, clientY: 260, buttons: 1 });
  await map.dispatchEvent('pointerdown', { pointerId: 12, pointerType: 'touch', clientX: 250, clientY: 260, buttons: 1 });
  await page.locator('body').dispatchEvent('pointermove', { pointerId: 12, pointerType: 'touch', clientX: 300, clientY: 260, buttons: 1 });
  await page.locator('body').dispatchEvent('pointerup', { pointerId: 11, pointerType: 'touch', clientX: 150, clientY: 260 });
  await page.locator('body').dispatchEvent('pointerup', { pointerId: 12, pointerType: 'touch', clientX: 300, clientY: 260 });
  expect(Number(await map.getAttribute('data-scale'))).toBeGreaterThan(beforePinch);

  await page.getByRole('button', { name: 'Ruínas da Vigília' }).click();
  await expect(page.getByRole('heading', { name: 'RUÍNAS DA VIGÍLIA' })).toBeVisible();
  await expect(page.getByTestId('travel-button')).toBeEnabled();

  await page.getByTestId('travel-button').click();
  await expect(party).toHaveAttribute('data-current', 'Ruínas da Vigília');
  await expect(page.getByTestId('travel-button')).toContainText('GRUPO MOVIDO');
  await expect(page.getByText('Q 18 · R 21', { exact: true }).first()).toBeVisible();

  await page.screenshot({ path: 'screenshots/wwn-piloto-interacao-415x915.png' });
});
