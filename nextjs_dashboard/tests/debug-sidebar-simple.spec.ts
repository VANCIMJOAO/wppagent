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

test.describe('Debug Sidebar Simple - Verificar se está renderizando', () => {
  test('Verificar se sidebar está sendo renderizado', async ({ page }) => {
    await login(page);
    console.log('✅ Login realizado');

    // Aguardar sidebar carregar
    await page.waitForTimeout(3000);

    // Verificar se há texto "Carregando" ou "Redirecionando"
    const loadingText = await page.locator('text=Carregando').count();
    const redirectingText = await page.locator('text=Redirecionando').count();
    
    console.log('⏳ Elementos com "Carregando":', loadingText);
    console.log('🔄 Elementos com "Redirecionando":', redirectingText);

    // Verificar se há elementos com classes específicas do sidebar
    const sidebarContainer = await page.locator('div.flex.h-screen.bg-gray-50').count();
    console.log('📋 Container principal do sidebar:', sidebarContainer);

    // Verificar se há elementos com texto de menu
    const dashboardText = await page.locator('text=Dashboard').count();
    const agendamentosText = await page.locator('text=Agendamentos').count();
    const conversasText = await page.locator('text=Conversas').count();
    
    console.log('🏠 Elementos com "Dashboard":', dashboardText);
    console.log('📅 Elementos com "Agendamentos":', agendamentosText);
    console.log('💬 Elementos com "Conversas":', conversasText);

    // Verificar se há elementos com classes específicas
    const fixedElements = await page.locator('[class*="fixed"]').count();
    const w80Elements = await page.locator('[class*="w-80"]').count();
    const bgWhiteElements = await page.locator('[class*="bg-white"]').count();
    
    console.log('🎨 Elementos com classe "fixed":', fixedElements);
    console.log('🎨 Elementos com classe "w-80":', w80Elements);
    console.log('🎨 Elementos com classe "bg-white":', bgWhiteElements);

    // Verificar se há elementos ocultos
    const hiddenElements = await page.locator('[style*="display: none"]').count();
    console.log('👻 Elementos ocultos:', hiddenElements);

    // Verificar o conteúdo da página
    const bodyText = await page.textContent('body');
    console.log('📄 Conteúdo da página (primeiros 200 chars):', bodyText?.substring(0, 200));

    // O teste passa se encontrou pelo menos alguns elementos de menu
    expect(dashboardText + agendamentosText + conversasText).toBeGreaterThan(0);
  });
});
