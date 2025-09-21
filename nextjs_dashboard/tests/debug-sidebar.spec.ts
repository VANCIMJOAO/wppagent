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
  
  await page.waitForURL('/dashboard');
  await page.waitForLoadState('networkidle');
}

test.describe('Debug Sidebar - Investigar Por que está vazio', () => {
  test('Debug sidebar rendering', async ({ page }) => {
    // Interceptar console logs
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Console Error:', msg.text());
      } else if (msg.type() === 'warn') {
        console.log('⚠️ Console Warning:', msg.text());
      } else if (msg.type() === 'log') {
        console.log('📝 Console Log:', msg.text());
      }
    });

    // Interceptar erros de página
    page.on('pageerror', error => {
      console.log('❌ Page Error:', error.message);
    });

    await login(page);
    console.log('✅ Login realizado');

    // Aguardar sidebar carregar
    await page.waitForTimeout(3000);

    // Verificar se há algum elemento do sidebar
    const sidebar = page.locator('[class*="sidebar"], [class*="Sidebar"], nav, aside').first();
    const sidebarVisible = await sidebar.isVisible();
    console.log('📋 Sidebar visível:', sidebarVisible);

    if (sidebarVisible) {
      const sidebarText = await sidebar.textContent();
      console.log('📋 Conteúdo do sidebar:', sidebarText?.substring(0, 200));
    }

    // Verificar se há loading
    const loading = page.locator('text=Carregando...');
    const isLoading = await loading.isVisible();
    console.log('⏳ Mostra "Carregando...":', isLoading);

    // Verificar se há erro
    const error = page.locator('text=Erro, text=Error');
    const hasError = await error.isVisible();
    console.log('❌ Tem erro:', hasError);

    // Verificar se há links
    const links = page.locator('a');
    const linkCount = await links.count();
    console.log('🔗 Número de links encontrados:', linkCount);

    // Listar todos os links
    for (let i = 0; i < Math.min(linkCount, 10); i++) {
      const link = links.nth(i);
      const href = await link.getAttribute('href');
      const text = await link.textContent();
      console.log(`  Link ${i}: ${href} - "${text}"`);
    }

    // Verificar se há elementos de menu
    const menuItems = page.locator('[role="menuitem"], [class*="menu"], [class*="nav"]');
    const menuCount = await menuItems.count();
    console.log('📋 Número de itens de menu:', menuCount);

    // Verificar se há elementos com texto "Agendamentos"
    const agendamentosElements = page.locator('text=Agendamentos');
    const agendamentosCount = await agendamentosElements.count();
    console.log('📅 Elementos com "Agendamentos":', agendamentosCount);

    // Verificar se há elementos com texto "Dashboard"
    const dashboardElements = page.locator('text=Dashboard');
    const dashboardCount = await dashboardElements.count();
    console.log('🏠 Elementos com "Dashboard":', dashboardCount);

    // Verificar se há elementos com texto "Conversas"
    const conversasElements = page.locator('text=Conversas');
    const conversasCount = await conversasElements.count();
    console.log('💬 Elementos com "Conversas":', conversasCount);

    // O teste passa se pelo menos encontrou algum elemento
    expect(linkCount).toBeGreaterThan(0);
  });
});
