import { test, expect } from '@playwright/test';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

test('VTT Lab abre em 415x915', async ({ page }) => {
  const file = path.resolve('current/index.html');
  await page.goto(pathToFileURL(file).href);

  await expect(page.getByTestId('vtt-lab-ready')).toBeVisible();
  expect(await page.viewportSize()).toEqual({ width: 415, height: 915 });
});
