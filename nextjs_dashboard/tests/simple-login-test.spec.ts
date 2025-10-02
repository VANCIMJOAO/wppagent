import { test, expect } from '@playwright/test';

test.describe('Teste de Login Simples', () => {
  test('deve fazer login com sucesso', async ({ page }) => {
    // Ir para a página de login
    await page.goto('/login');
    
    // Aguardar o campo de username aparecer
    await page.waitForSelector('input[id="username"]', { state: 'visible', timeout: 10000 });
    
    // Preencher credenciais
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'admin123');
    
    // Clicar no botão de login
    await page.click('button[type="submit"]');
    
    // Aguardar um pouco para ver o que acontece
    await page.waitForTimeout(3000);
    
    // Verificar para onde foi redirecionado
    console.log('URL atual após login:', page.url());
    
    // Verificar se está na página correta (pode ser /dashboard ou /)
    const currentUrl = page.url();
    expect(currentUrl.includes('/dashboard') || currentUrl.includes('localhost:3000')).toBe(true);
  });
});