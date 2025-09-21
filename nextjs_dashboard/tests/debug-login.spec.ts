import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

test.describe('Debug Login', () => {
  test('Debug - Verificar página de login', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Verificar se a página carregou
    await expect(page).toHaveTitle(/WhatsApp Agent Dashboard/);
    
    // Verificar se os campos existem
    const usernameField = page.locator('input[id="username"]');
    const passwordField = page.locator('input[id="password"]');
    const submitButton = page.locator('button[type="submit"]');
    
    await expect(usernameField).toBeVisible();
    await expect(passwordField).toBeVisible();
    await expect(submitButton).toBeVisible();
    
    console.log('✅ Campos de login encontrados');
  });

  test('Debug - Tentar login manual', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Preencher campos
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    
    console.log('✅ Campos preenchidos');
    
    // Clicar no botão de submit
    await page.click('button[type="submit"]');
    
    console.log('✅ Botão clicado');
    
    // Aguardar um pouco para ver o que acontece
    await page.waitForTimeout(5000);
    
    // Verificar se houve redirecionamento ou erro
    const currentUrl = page.url();
    console.log('URL atual:', currentUrl);
    
    // Verificar se há mensagens de erro
    const errorMessages = await page.locator('[class*="error"], [class*="Error"]').allTextContents();
    if (errorMessages.length > 0) {
      console.log('Mensagens de erro encontradas:', errorMessages);
    }
    
    // Verificar se há mensagens de sucesso
    const successMessages = await page.locator('[class*="success"], [class*="Success"]').allTextContents();
    if (successMessages.length > 0) {
      console.log('Mensagens de sucesso encontradas:', successMessages);
    }
  });

  test('Debug - Verificar resposta da API', async ({ page }) => {
    // Interceptar requisições de API
    page.on('response', response => {
      if (response.url().includes('/api/proxy/admin/login')) {
        console.log('Resposta da API de login:', response.status(), response.url());
      }
    });
    
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Preencher e submeter
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    
    // Aguardar resposta da API
    await page.waitForTimeout(3000);
  });
});
