import { test, expect, Page } from '@playwright/test';

const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

test.describe('Debug Login JS Errors', () => {
  test('Capturar erros JavaScript durante login', async ({ page }) => {
    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];

    // Capturar erros do console
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log(`❌ Console Error: ${msg.text()}`);
      }
    });

    // Capturar erros de página
    page.on('pageerror', error => {
      pageErrors.push(error.message);
      console.log(`❌ Page Error: ${error.message}`);
    });

    // Capturar requisições e respostas
    page.on('request', request => {
      if (request.url().includes('/api/proxy/admin/login')) {
        console.log('🔍 Login Request:', request.method(), request.url());
        console.log('📦 Request Body:', request.postData());
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/proxy/admin/login')) {
        console.log('🔍 Login Response:', response.status(), response.url());
        try {
          const body = await response.json();
          console.log('📦 Response Body:', JSON.stringify(body, null, 2));
        } catch (e) {
          console.log('❌ Could not parse response body');
        }
      }
    });

    // Ir para página de login
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Página de login carregada');
    
    // Preencher campos
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    
    console.log('✅ Campos preenchidos');
    
    // Clicar no botão de login
    await page.click('button[type="submit"]');
    
    console.log('✅ Botão clicado');
    
    // Aguardar um pouco para capturar erros
    await page.waitForTimeout(3000);
    
    // Verificar se houve erros
    console.log('📊 Total de erros do console:', consoleErrors.length);
    console.log('📊 Total de erros de página:', pageErrors.length);
    
    if (consoleErrors.length > 0) {
      console.log('❌ Erros do console encontrados:');
      consoleErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
    }
    
    if (pageErrors.length > 0) {
      console.log('❌ Erros de página encontrados:');
      pageErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error}`);
      });
    }
    
    // Verificar URL atual
    const currentUrl = page.url();
    console.log('🌐 URL atual:', currentUrl);
    
    // Verificar localStorage
    const userData = await page.evaluate(() => localStorage.getItem('user'));
    console.log('💾 Dados do usuário no localStorage:', userData);
    
    // Verificar cookies
    const cookies = await page.context().cookies();
    const authTokenCookie = cookies.find(cookie => cookie.name === 'auth-token');
    console.log('🍪 Cookie auth-token:', authTokenCookie ? 'Presente' : 'Ausente');
    if (authTokenCookie) {
      console.log('🍪 Valor do cookie:', authTokenCookie.value.substring(0, 50) + '...');
    }
    
    // O teste passa se não há erros críticos
    expect(consoleErrors.length).toBeLessThan(5); // Permitir alguns warnings
    expect(pageErrors.length).toBe(0); // Não deve haver erros de página
  });
});