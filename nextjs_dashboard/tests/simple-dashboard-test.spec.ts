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

test.describe('Teste Simples do Dashboard', () => {
  test('Login e acesso básico ao dashboard', async ({ page }) => {
    // Fazer login
    await login(page);
    
    // Verificar se estamos no dashboard
    expect(page.url()).toContain('/dashboard');
    
    // Aguardar um pouco para o conteúdo carregar
    await page.waitForTimeout(3000);
    
    // Verificar se a página tem algum conteúdo (mesmo que seja "Carregando...")
    const bodyContent = await page.textContent('body');
    expect(bodyContent).not.toBeNull();
    
    // Verificar se há pelo menos um elemento h1, h2 ou h3
    const hasHeading = await page.locator('h1, h2, h3').first().isVisible();
    expect(hasHeading).toBe(true);
    
    console.log('✅ Dashboard acessado com sucesso');
  });

  test('Verificar se sidebar está funcionando', async ({ page }) => {
    await login(page);
    
    // Aguardar sidebar carregar
    await page.waitForTimeout(2000);
    
    // Verificar se o logo está presente
    const logo = page.locator('h2:has-text("WppAgent")');
    const isLogoVisible = await logo.isVisible();
    expect(isLogoVisible).toBe(true);
    
    // Verificar se há pelo menos um link de navegação
    const navLinks = await page.locator('nav a, nav button').count();
    expect(navLinks).toBeGreaterThan(0);
    
    console.log('✅ Sidebar está funcionando');
  });

  test('Testar navegação para agendamentos', async ({ page }) => {
    await login(page);
    
    // Aguardar sidebar carregar
    await page.waitForTimeout(2000);
    
    // Tentar navegar para agendamentos
    await page.goto('/agendamentos');
    await page.waitForLoadState('networkidle');
    
    // Verificar se não foi redirecionado de volta para login
    expect(page.url()).toContain('/agendamentos');
    
    // Verificar se a página tem algum conteúdo
    const bodyContent = await page.textContent('body');
    expect(bodyContent).not.toBeNull();
    
    console.log('✅ Navegação para agendamentos funcionando');
  });
});
