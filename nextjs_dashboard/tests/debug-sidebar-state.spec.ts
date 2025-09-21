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

test.describe('Debug Sidebar State - Investigar Estado do Componente', () => {
  test.beforeEach(async ({ page }) => {
    page.on('console', msg => console.log(`📝 Console Log: ${msg.text()}`));
    page.on('pageerror', error => console.log(`❌ Page Error: ${error.message}`));
    page.on('requestfailed', request => console.log(`❌ Request Failed: ${request.method()} ${request.url()} - ${request.failure()}`));
    page.on('response', async response => {
      if (!response.ok() && response.url().includes('/api/proxy')) {
        console.log(`❌ API Error Response: ${response.status()} ${response.url()}`);
        try {
          const body = await response.json();
          console.log('   Body:', body);
        } catch (e) {
          console.log('   Could not parse error body.');
        }
      }
    });

    await login(page);
    console.log('✅ Login realizado para debug do estado do sidebar');
  });

  test('Debug estado interno do sidebar', async ({ page }) => {
    console.log('🌐 Navegando para /dashboard para verificar estado do sidebar...');
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Verificar o estado interno do componente via JavaScript
    const sidebarState = await page.evaluate(() => {
      // Procurar por elementos que contenham "Carregando" ou "Redirecionando"
      const loadingElements = Array.from(document.querySelectorAll('*')).filter(el => 
        el.textContent?.includes('Carregando') || el.textContent?.includes('Redirecionando')
      );

      // Tentar acessar o estado do componente Sidebar (se exposto globalmente para debug)
      // Isso é mais complexo e geralmente requer ferramentas de dev ou modificações no código da aplicação
      // Para este teste, vamos inferir o estado a partir do DOM e logs
      const isSidebarVisibleInDOM = document.querySelector('div.flex.h-screen.bg-gray-50 > div.flex.flex-col') !== null;
      const hasUserInLocalStorage = localStorage.getItem('user') !== null;

      return {
        isLoadingDisplayed: loadingElements.length > 0,
        isSidebarVisibleInDOM,
        hasUserInLocalStorage,
        // Adicionar mais estados se puderem ser inferidos ou acessados
      };
    });

    console.log('📋 Estado inferido do sidebar:', sidebarState);

    // Verificar se "Carregando..." ou "Redirecionando..." não estão visíveis
    expect(sidebarState.isLoadingDisplayed).toBe(false);
    // Verificar se o sidebar principal está no DOM
    expect(sidebarState.isSidebarVisibleInDOM).toBe(true);
    // Verificar se o usuário está no localStorage
    expect(sidebarState.hasUserInLocalStorage).toBe(true);
  });
});