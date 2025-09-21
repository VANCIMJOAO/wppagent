import { test, expect, Page } from '@playwright/test';

const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

async function login(page: Page) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  
  await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
  await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
  await page.click('button[type="submit"]');
  
  // Aguardar redirecionamento para dashboard
  await page.waitForURL('/dashboard');
  await page.waitForLoadState('networkidle');
}

test.describe('Debug Navegação - Investigar Redirecionamentos', () => {
  test('Debug navegação direta para agendamentos', async ({ page }) => {
    // Interceptar todas as requisições
    page.on('request', request => {
      console.log('🔍 Request:', request.method(), request.url());
    });

    page.on('response', response => {
      if (response.status() !== 200) {
        console.log('❌ Response Error:', response.status(), response.url());
      }
    });

    // Interceptar console logs
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Console Error:', msg.text());
      }
    });

    // Interceptar erros de página
    page.on('pageerror', error => {
      console.log('❌ Page Error:', error.message);
    });

    // Fazer login primeiro
    await login(page);
    console.log('✅ Login realizado, URL atual:', page.url());
    
    // Aguardar um pouco para estabilizar
    await page.waitForTimeout(2000);
    
    // Tentar navegar para agendamentos
    console.log('🌐 Navegando para /agendamentos...');
    await page.goto('/agendamentos');
    
    // Aguardar um pouco para ver o que acontece
    await page.waitForTimeout(3000);
    
    console.log('🌐 URL final:', page.url());
    
    // Verificar se conseguiu acessar agendamentos
    const currentUrl = page.url();
    console.log('📊 URL atual:', currentUrl);
    
    if (currentUrl.includes('/agendamentos')) {
      console.log('✅ Sucesso! Conseguiu acessar agendamentos');
    } else if (currentUrl.includes('/dashboard')) {
      console.log('❌ Redirecionado para dashboard');
    } else if (currentUrl.includes('/login')) {
      console.log('❌ Redirecionado para login');
    } else {
      console.log('❓ Redirecionado para:', currentUrl);
    }
    
    // O teste passa se pelo menos não redirecionou para login
    expect(currentUrl).not.toContain('/login');
  });

  test('Debug navegação via sidebar', async ({ page }) => {
    await login(page);
    console.log('✅ Login realizado');
    
    // Aguardar sidebar carregar
    await page.waitForTimeout(2000);
    
    // Tentar clicar no botão de agendamentos no sidebar
    console.log('🔍 Procurando botão de agendamentos no sidebar...');
    
    // Procurar por botões que contenham "Agendamentos"
    const agendamentosButton = page.locator('button:has-text("Agendamentos")').first();
    
    if (await agendamentosButton.isVisible()) {
      console.log('✅ Botão de agendamentos encontrado');
      await agendamentosButton.click();
      
      // Aguardar navegação
      await page.waitForURL('/agendamentos');
      await page.waitForLoadState('networkidle');
      
      console.log('🌐 URL após clique:', page.url());
      
      const currentUrl = page.url();
      if (currentUrl.includes('/agendamentos')) {
        console.log('✅ Sucesso! Navegação via sidebar funcionou');
      } else {
        console.log('❌ Falha na navegação via sidebar. URL:', currentUrl);
      }
      
      expect(currentUrl).toContain('/agendamentos');
    } else {
      console.log('❌ Botão de agendamentos não encontrado no sidebar');
      // Listar todos os botões disponíveis
      const allButtons = await page.locator('button').all();
      console.log('📋 Botões disponíveis:');
      for (const button of allButtons.slice(0, 10)) { // Primeiros 10
        const text = await button.textContent();
        console.log(`  - ${text?.trim()}`);
      }
      
      // O teste falha se não encontrar o botão
      expect(agendamentosButton).toBeVisible();
    }
  });
});
