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

test.describe('Dashboard Funcional - Testes Básicos', () => {
  test('Login e acesso ao dashboard', async ({ page }) => {
    await login(page);
    
    // Verificar se estamos no dashboard
    expect(page.url()).toContain('/dashboard');
    
    // Verificar se a página carregou (mesmo que seja "Carregando...")
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toBeTruthy();
    
    console.log('✅ Login e acesso ao dashboard funcionando');
  });

  test('Navegação para outras páginas', async ({ page }) => {
    await login(page);
    
    // Testar navegação para agendamentos
    await page.goto('/agendamentos');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/agendamentos');
    
    // Testar navegação para conversas
    await page.goto('/conversas');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/conversas');
    
    // Testar navegação para clientes
    await page.goto('/clientes');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/clientes');
    
    console.log('✅ Navegação entre páginas funcionando');
  });

  test('Verificar autenticação persistente', async ({ page }) => {
    await login(page);
    
    // Verificar se o cookie está presente
    const cookies = await page.context().cookies();
    const authCookie = cookies.find(c => c.name === 'auth-token');
    expect(authCookie).toBeTruthy();
    
    // Verificar se o localStorage tem dados do usuário
    const userData = await page.evaluate(() => {
      return localStorage.getItem('user');
    });
    expect(userData).toBeTruthy();
    
    // Verificar se não é redirecionado para login ao acessar dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/dashboard');
    expect(page.url()).not.toContain('/login');
    
    console.log('✅ Autenticação persistente funcionando');
  });

  test('Verificar middleware de autenticação', async ({ page }) => {
    // Tentar acessar dashboard sem login
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Deve ser redirecionado para login
    expect(page.url()).toContain('/login');
    
    // Fazer login
    await login(page);
    
    // Agora deve conseguir acessar dashboard
    expect(page.url()).toContain('/dashboard');
    
    console.log('✅ Middleware de autenticação funcionando');
  });

  test('Verificar APIs do backend', async ({ page }) => {
    await login(page);
    
    // Testar API de status de autenticação
    const response = await page.request.get('/api/proxy/auth/status');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toBeTruthy();
    
    console.log('✅ APIs do backend funcionando');
  });
});
