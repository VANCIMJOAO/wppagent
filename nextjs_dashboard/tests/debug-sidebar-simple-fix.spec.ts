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

test.describe('Debug Sidebar Simples - Verificar Elementos Básicos', () => {
  test.beforeEach(async ({ page }) => {
    page.on('console', msg => console.log(`📝 Console Log: ${msg.text()}`));
    page.on('pageerror', error => console.log(`❌ Page Error: ${error.message}`));

    await login(page);
    console.log('✅ Login realizado para debug simples do sidebar');
  });

  test('Debug simples - Verificar elementos do sidebar', async ({ page }) => {
    console.log('🌐 Navegando para /dashboard...');
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Aguardar um tempo para componente carregar
    await page.waitForTimeout(3000);

    // Verificar elementos usando JavaScript puro (sem seletores CSS avançados)
    const sidebarDetails = await page.evaluate(() => {
      // Verificar localStorage
      const userInLocalStorage = localStorage.getItem('user');
      
      // Buscar elementos usando seletores simples
      const h2Elements = Array.from(document.querySelectorAll('h2'));
      const logoElement = h2Elements.find(el => el.textContent?.includes('WppAgent'));
      
      const h3Elements = Array.from(document.querySelectorAll('h3'));
      const navigationSection = h3Elements.find(el => el.textContent?.includes('Navegação'));
      
      const buttonElements = Array.from(document.querySelectorAll('button'));
      const dashboardButton = buttonElements.find(el => el.textContent?.includes('Dashboard'));
      const agendamentosButton = buttonElements.find(el => el.textContent?.includes('Agendamentos'));
      const conversasButton = buttonElements.find(el => el.textContent?.includes('Conversas'));
      
      // Verificar elementos de carregamento
      const allElements = Array.from(document.querySelectorAll('*'));
      const loadingElements = allElements.filter(el => el.textContent === 'Carregando...');
      const redirectingElements = allElements.filter(el => el.textContent === 'Redirecionando...');
      
      // Verificar containers do sidebar
      const sidebarContainer = document.querySelector('div.flex.h-screen.bg-gray-50');
      const sidebarFixed = document.querySelector('.fixed.md\\:relative.inset-y-0.left-0');
      
      // Contar todos os botões
      const allButtons = Array.from(document.querySelectorAll('button'));
      
      return {
        userInLocalStorage: userInLocalStorage !== null,
        userDataParsed: userInLocalStorage ? JSON.parse(userInLocalStorage) : null,
        logoPresent: logoElement !== undefined,
        logoText: logoElement?.textContent,
        navigationSectionPresent: navigationSection !== undefined,
        navigationText: navigationSection?.textContent,
        dashboardButtonPresent: dashboardButton !== undefined,
        dashboardButtonText: dashboardButton?.textContent,
        agendamentosButtonPresent: agendamentosButton !== undefined,
        agendamentosButtonText: agendamentosButton?.textContent,
        conversasButtonPresent: conversasButton !== undefined,
        conversasButtonText: conversasButton?.textContent,
        loadingElementsCount: loadingElements.length,
        redirectingElementsCount: redirectingElements.length,
        sidebarContainerPresent: sidebarContainer !== null,
        sidebarFixedPresent: sidebarFixed !== null,
        totalButtonsCount: allButtons.length,
        allButtonTexts: allButtons.map(btn => btn.textContent?.trim()).filter(Boolean).slice(0, 10), // Primeiros 10
        h2Count: h2Elements.length,
        h3Count: h3Elements.length,
        allH2Texts: h2Elements.map(el => el.textContent?.trim()).filter(Boolean),
        allH3Texts: h3Elements.map(el => el.textContent?.trim()).filter(Boolean)
      };
    });

    console.log('📋 Detalhes do sidebar:');
    console.log(`   🔐 Usuário no localStorage: ${sidebarDetails.userInLocalStorage}`);
    console.log(`   📝 Logo presente: ${sidebarDetails.logoPresent} (${sidebarDetails.logoText})`);
    console.log(`   📝 Seção navegação: ${sidebarDetails.navigationSectionPresent} (${sidebarDetails.navigationText})`);
    console.log(`   📝 Botão Dashboard: ${sidebarDetails.dashboardButtonPresent} (${sidebarDetails.dashboardButtonText})`);
    console.log(`   📝 Botão Agendamentos: ${sidebarDetails.agendamentosButtonPresent} (${sidebarDetails.agendamentosButtonText})`);
    console.log(`   📝 Botão Conversas: ${sidebarDetails.conversasButtonPresent} (${sidebarDetails.conversasButtonText})`);
    console.log(`   📝 Total de botões: ${sidebarDetails.totalButtonsCount}`);
    console.log(`   📝 Textos dos botões: ${sidebarDetails.allButtonTexts.join(', ')}`);
    console.log(`   📝 Total H2: ${sidebarDetails.h2Count} - ${sidebarDetails.allH2Texts.join(', ')}`);
    console.log(`   📝 Total H3: ${sidebarDetails.h3Count} - ${sidebarDetails.allH3Texts.join(', ')}`);
    console.log(`   📝 Elementos "Carregando": ${sidebarDetails.loadingElementsCount}`);
    console.log(`   📝 Elementos "Redirecionando": ${sidebarDetails.redirectingElementsCount}`);
    console.log(`   📝 Container sidebar: ${sidebarDetails.sidebarContainerPresent}`);
    console.log(`   📝 Sidebar fixed: ${sidebarDetails.sidebarFixedPresent}`);

    // Verificações básicas
    expect(sidebarDetails.userInLocalStorage).toBe(true);
    expect(sidebarDetails.loadingElementsCount).toBe(0);
    expect(sidebarDetails.redirectingElementsCount).toBe(0);
    expect(sidebarDetails.sidebarContainerPresent).toBe(true);
    
    // Se não há logo, isso indica problema na renderização do sidebar
    if (!sidebarDetails.logoPresent) {
      console.log('❌ PROBLEMA CRÍTICO: Logo "WppAgent" não encontrado!');
      console.log('   Isso indica que o sidebar não está renderizando corretamente.');
    }
    
    // Se não há seção de navegação, isso confirma o problema
    if (!sidebarDetails.navigationSectionPresent) {
      console.log('❌ PROBLEMA CRÍTICO: Seção "Navegação" não encontrada!');
      console.log('   Isso confirma que os links do menu não estão sendo renderizados.');
    }
    
    // Se não há botões principais, isso é o problema
    if (!sidebarDetails.dashboardButtonPresent && !sidebarDetails.agendamentosButtonPresent) {
      console.log('❌ PROBLEMA CRÍTICO: Botões de navegação não encontrados!');
      console.log('   Os links do menu principal não estão sendo renderizados.');
    }
  });
});
