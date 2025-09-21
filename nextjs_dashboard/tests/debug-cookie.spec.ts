import { test, expect, Page } from '@playwright/test';

const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

test.describe('Debug Cookie', () => {
  test('Verificar se cookie está sendo salvo corretamente', async ({ page }) => {
    // Interceptar requisições para debug
    page.on('request', request => {
      if (request.url().includes('/api/auth/set-token')) {
        console.log('🔍 Request para set-token:', request.url());
        console.log('📦 Body:', request.postData());
      }
    });

    page.on('response', response => {
      if (response.url().includes('/api/auth/set-token')) {
        console.log('🔍 Response do set-token:', response.status());
        console.log('🍪 Headers:', response.headers());
        console.log('🍪 Set-Cookie:', response.headers()['set-cookie']);
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
    
    // Aguardar um pouco para as requisições completarem
    await page.waitForTimeout(3000);
    
    // Verificar cookies
    const cookies = await page.context().cookies();
    console.log('🍪 Cookies encontrados:', cookies.length);
    
    const authCookie = cookies.find(c => c.name === 'auth-token');
    if (authCookie) {
      console.log('✅ Cookie auth-token encontrado:', authCookie.value.substring(0, 20) + '...');
      console.log('🍪 Cookie details:', {
        name: authCookie.name,
        value: authCookie.value.substring(0, 20) + '...',
        domain: authCookie.domain,
        path: authCookie.path,
        httpOnly: authCookie.httpOnly,
        secure: authCookie.secure,
        sameSite: authCookie.sameSite
      });
    } else {
      console.log('❌ Cookie auth-token NÃO encontrado');
    }
    
    // Verificar localStorage
    const userData = await page.evaluate(() => {
      return localStorage.getItem('user');
    });
    
    console.log('💾 Dados do usuário no localStorage:', userData);
    
    // Verificar URL atual
    const currentUrl = page.url();
    console.log('🌐 URL atual:', currentUrl);
    
    // Tentar acessar dashboard diretamente
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    const dashboardUrl = page.url();
    console.log('🌐 URL do dashboard:', dashboardUrl);
    
    // Verificar se há conteúdo na página
    const hasContent = await page.locator('body').isVisible();
    console.log('📄 Página tem conteúdo:', hasContent);
    
    if (hasContent) {
      const bodyText = await page.locator('body').textContent();
      console.log('📄 Conteúdo da página:', bodyText?.substring(0, 200) + '...');
    }
    
    // Verificar se foi redirecionado para login
    const wasRedirectedToLogin = dashboardUrl.includes('/login');
    console.log('🔄 Foi redirecionado para login:', wasRedirectedToLogin);
    
    // O teste passa se o cookie foi salvo
    expect(authCookie).toBeTruthy();
  });
});
