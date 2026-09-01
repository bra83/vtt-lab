import { test, expect } from '@playwright/test';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

test('WWN atlas gigante funciona em 415x915 com escala real', async ({ page }) => {
  const file = path.resolve('current/index.html');
  await page.goto(pathToFileURL(file).href);

  const map = page.getByTestId('hex-map');
  const party = page.getByTestId('party-marker');
  const atlas = page.getByTestId('atlas-image');

  await expect(page.getByTestId('vtt-lab-ready')).toBeVisible();
  expect(await page.viewportSize()).toEqual({ width: 415, height: 915 });
  await expect(page.getByTestId('scale-label')).toHaveText('1 hex = 6 milhas');
  await expect(map).toHaveAttribute('data-miles-per-hex', '6');
  await expect(map).toHaveAttribute('data-visible-hexes', '5');
  await expect(map).toHaveAttribute('data-centered', 'true');
  await expect(party).toHaveAttribute('data-current', 'Colinas dos Antigos');
  await expect(atlas).toBeVisible();
  expect(await atlas.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBeTruthy();

  await page.screenshot({ path: 'screenshots/wwn-piloto-inicial-415x915.png' });

  const scale0 = Number(await map.getAttribute('data-scale'));
  await page.getByTestId('zoom-in').click();
  expect(Number(await map.getAttribute('data-scale'))).toBeGreaterThan(scale0);

  const beforePan = await map.getAttribute('data-pan-x');
  const box = await map.boundingBox();
  if (!box) throw new Error('Mapa sem bounding box');
  await page.mouse.move(box.x + 300, box.y + 300);
  await page.mouse.down();
  await page.mouse.move(box.x + 250, box.y + 270, { steps: 6 });
  await page.mouse.up();
  await expect(map).toHaveAttribute('data-centered', 'false');
  expect(await map.getAttribute('data-pan-x')).not.toBe(beforePan);

  await page.getByTestId('center-map').click();
  await expect(map).toHaveAttribute('data-centered', 'true');

  await page.getByRole('button', { name: 'Ruínas de Varn' }).click();
  await expect(page.getByRole('heading', { name: 'RUÍNAS DE VARN' })).toBeVisible();
  await expect(page.getByText('As ruínas são um marco dentro do hex, não o próprio hex.')).toBeVisible();
  await expect(page.getByTestId('travel-button')).toBeEnabled();

  await page.getByTestId('travel-button').click();
  await expect(party).toHaveAttribute('data-current', 'Ruínas de Varn');
  await expect(page.getByTestId('travel-button')).toContainText('GRUPO MOVIDO');
  await expect(page.getByText('Q 18 · R 21', { exact: true }).first()).toBeVisible();

  await page.screenshot({ path: 'screenshots/wwn-piloto-interacao-415x915.png' });
});
