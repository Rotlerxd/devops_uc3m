import { test, expect } from '@playwright/test';

test.describe('Auth flow', () => {
  test('login page has form fields', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByLabel('Correo electrónico')).toBeVisible();
    await expect(page.getByLabel('Contraseña')).toBeVisible();
    await expect(page.getByRole('button', { name: /entrar/i })).toBeVisible();
  });

  test('register page has form fields', async ({ page }) => {
    await page.goto('/register');

    await expect(page.getByLabel('Nombre completo')).toBeVisible();
    await expect(page.getByLabel('Correo electrónico')).toBeVisible();
    await expect(page.getByLabel('Contraseña')).toBeVisible();
    await expect(page.getByRole('button', { name: /registrarse/i })).toBeVisible();
  });

  test('navigation between login and register', async ({ page }) => {
    await page.goto('/login');
    await page.click('text=Regístrate aquí');
    await expect(page).toHaveURL(/.*register/);

    await page.click('text=Inicia sesión aquí');
    await expect(page).toHaveURL(/.*login/);
  });

  test('unauthenticated access redirects to login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/.*login/);
  });
});
