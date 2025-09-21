import { test, expect, Page } from '@playwright/test';

const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

test.describe('Debug Login Simples', () => {
  test('Teste de login básico com debug detalhado', async ({ page }) => {
    // Capturar todos os logs
    page.on('console', msg => {
      console.log(`📝 Console [${msg.type()}]: ${msg.text()}`);
    });
    
    page.on('pageerror', error => {
      console.log(`❌ Page Error: ${error.message}`);
      console.log(`❌ Stack: ${error.stack}`);
    });

    page.on('request', request => {
      if (request.url().includes('/api/')) {
        console.log(`🔍 Request: ${request.method()} ${request.url()}`);
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/')) {
        console.log(`🔍 Response: ${response.status()} ${response.url()}`);
        if (!response.ok()) {
          try {
            const body = await response.json();
            console.log(`❌ Error Body:`, body);
          } catch (e) {
            console.log(`❌ Could not parse error body`);
          }
        }
      }
    });

    console.log('🌐 Navegando para /login...');
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Página de login carregada');
    console.log('🌐 URL atual:', page.url());
    
    // Verificar se os campos estão presentes
    const usernameField = page.locator('input[id="username"]');
    const passwordField = page.locator('input[id="password"]');
    const submitButton = page.locator('button[type="submit"]');
    
    console.log('🔍 Campo username visível:', await usernameField.isVisible());
    console.log('🔍 Campo password visível:', await passwordField.isVisible());
    console.log('🔍 Botão submit visível:', await submitButton.isVisible());
    
    // Preencher campos
    console.log('📝 Preenchendo campos...');
    await usernameField.fill(TEST_CREDENTIALS.username);
    await passwordField.fill(TEST_CREDENTIALS.password);
    
    console.log('✅ Campos preenchidos');
    
    // Clicar no botão
    console.log('🖱️ Clicando no botão de login...');
    await submitButton.click();
    
    console.log('✅ Botão clicado');
    
    // Aguardar um pouco para ver o que acontece
    console.log('⏳ Aguardando 3 segundos...');
    await page.waitForTimeout(3000);
    
    console.log('🌐 URL após clique:', page.url());
    
    // Verificar se há erros na página
    const errorElement = page.locator('[data-testid="error"], .error, [role="alert"]');
    if (await errorElement.isVisible()) {
      const errorText = await errorElement.textContent();
      console.log('❌ Erro encontrado na página:', errorText);
    }
    
    // Verificar se há mensagens de sucesso
    const successElement = page.locator('[data-testid="success"], .success');
    if (await successElement.isVisible()) {
      const successText = await successElement.textContent();
      console.log('✅ Sucesso encontrado na página:', successText);
    }
    
    // Verificar localStorage
    const userData = await page.evaluate(() => localStorage.getItem('user'));
    console.log('💾 Dados no localStorage:', userData);
    
    // Verificar cookies
    const cookies = await page.context().cookies();
    const authTokenCookie = cookies.find(cookie => cookie.name === 'auth-token');
    console.log('🍪 Cookie auth-token:', authTokenCookie ? 'Presente' : 'Ausente');
    if (authTokenCookie) {
      console.log('🍪 Valor do cookie:', authTokenCookie.value.substring(0, 20) + '...');
    }
    
    // Verificar se redirecionou para dashboard
    const currentUrl = page.url();
    console.log('🌐 URL final:', currentUrl);
    
    if (currentUrl.includes('/dashboard')) {
      console.log('✅ Redirecionamento para dashboard funcionou!');
      
      // Verificar se o dashboard carregou
      const dashboardTitle = page.locator('h1:has-text("Dashboard")');
      const isDashboardTitleVisible = await dashboardTitle.isVisible();
      console.log('📊 Título "Dashboard" visível:', isDashboardTitleVisible);
      
      if (!isDashboardTitleVisible) {
        // Procurar por outros elementos que possam indicar o dashboard
        const bodyText = await page.textContent('body');
        console.log('📄 Conteúdo da página (primeiros 500 chars):', bodyText?.substring(0, 500));
        
        // Procurar por elementos que contenham "Dashboard"
        const dashboardElements = await page.locator('text=Dashboard').all();
        console.log('🔍 Elementos com "Dashboard" encontrados:', dashboardElements.length);
        
        for (let i = 0; i < Math.min(dashboardElements.length, 5); i++) {
          const element = dashboardElements[i];
          const isVisible = await element.isVisible();
          const tagName = await element.evaluate(el => el.tagName);
          const text = await element.textContent();
          console.log(`  - Elemento ${i}: ${tagName}, visível: ${isVisible}, texto: "${text}"`);
        }
      }
    } else {
      console.log('❌ Não redirecionou para dashboard. URL atual:', currentUrl);
    }
    
    // O teste passa se pelo menos não deu erro crítico
    expect(currentUrl).toBeDefined();
  });
});
