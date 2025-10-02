import { test, expect } from '@playwright/test';

test.describe('Teste Simples', () => {
  test('deve carregar a página de login', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/WhatsApp Agent Dashboard/);
    
    // Verificar se os campos de login existem
    await expect(page.locator('input[id="username"]')).toBeVisible();
    await expect(page.locator('input[id="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('deve mostrar erro ao tentar login sem credenciais', async ({ page }) => {
    await page.goto('/login');
    
    // Tentar fazer login sem preencher campos
    await page.click('button[type="submit"]');
    
    // Verificar se os campos são obrigatórios
    await expect(page.locator('input[id="username"]')).toHaveAttribute('required');
    await expect(page.locator('input[id="password"]')).toHaveAttribute('required');
  });
});



