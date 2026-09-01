import { test, expect } from '@playwright/test';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

test('WWN piloto abre e funciona em 415x915', async ({ page }) => {
  const file = path.resolve('current/index.html');
  await page.goto(pathToFileURL(file).href);

  await expect(page.getByTestId('vtt-lab-ready')).toBeVisible();
  expect(await page.viewportSize()).toEqual({ width: 415, height: 915 });
  await expect(page.getByTestId('hex-map')).toBeVisible();
  await expect(page.getByText('1 hex = 6 milhas')).toBeVisible();

  await page.locator('button.hex[data-name="Ruínas da Vigília"]').click();
  await expect(page.getByText('RUÍNAS DA VIGÍLIA')).toBeVisible();

  await page.getByTestId('travel-button').click();
  await expect(page.getByTestId('travel-button')).toContainText('ROTA DEFINIDA');

  await page.screenshot({ path: 'playwright-report/wwn-piloto-415x915.png' });
});
