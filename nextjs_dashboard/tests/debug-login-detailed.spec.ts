import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

test.describe('Debug Login Detalhado', () => {
  test('Debug - Login completo com logs', async ({ page }) => {
    // Interceptar todas as requisições
    page.on('request', request => {
      console.log('REQUEST:', request.method(), request.url());
    });
    
    page.on('response', response => {
      console.log('RESPONSE:', response.status(), response.url());
    });
    
    // Interceptar console.log do navegador
    page.on('console', msg => {
      console.log('BROWSER LOG:', msg.text());
    });
    
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Página de login carregada');
    
    // Preencher campos
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    
    console.log('✅ Campos preenchidos');
    
    // Aguardar e clicar no botão
    await page.click('button[type="submit"]');
    
    console.log('✅ Botão clicado');
    
    // Aguardar todas as requisições terminarem
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Requisições finalizadas');
    
    // Verificar URL atual
    const currentUrl = page.url();
    console.log('URL atual após login:', currentUrl);
    
    // Verificar se há erros no console
    const logs = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });
    
    // Aguardar um pouco mais para capturar erros
    await page.waitForTimeout(2000);
    
    if (logs.length > 0) {
      console.log('ERROS no console:', logs);
    }
    
    // Verificar se o token foi salvo
    const token = await page.evaluate(() => {
      return document.cookie.includes('auth-token');
    });
    
    console.log('Token salvo no cookie:', token);
    
    // Verificar se há dados no localStorage
    const userData = await page.evaluate(() => {
      return localStorage.getItem('user');
    });
    
    console.log('Dados do usuário no localStorage:', userData);
    
    // Se ainda estiver na página de login, verificar se há mensagem de erro
    if (currentUrl.includes('/login')) {
      const errorElement = await page.locator('[class*="error"], [class*="Error"], .text-red-500').first();
      if (await errorElement.isVisible()) {
        const errorText = await errorElement.textContent();
        console.log('Mensagem de erro encontrada:', errorText);
      }
    }
  });
});
