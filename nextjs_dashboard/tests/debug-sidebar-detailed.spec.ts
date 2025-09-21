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

test.describe('Debug Sidebar Detalhado', () => {
  test('Investigar por que os links não aparecem', async ({ page }) => {
    await login(page);
    
    // Aguardar sidebar carregar
    await page.waitForTimeout(3000);
    
    // Capturar logs do console
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`❌ Console Error: ${msg.text()}`);
      } else if (msg.type() === 'log') {
        console.log(`📝 Console Log: ${msg.text()}`);
      }
    });
    
    // Verificar se o container do sidebar existe (usar seletor mais específico)
    const sidebarContainer = page.locator('div.flex.h-screen.bg-gray-50 > div.fixed.md\\:relative.inset-y-0.left-0.z-40');
    const sidebarExists = await sidebarContainer.isVisible();
    console.log('🔍 Sidebar container existe:', sidebarExists);
    
    // Verificar se o logo está presente
    const logo = page.locator('h2:has-text("WppAgent")');
    const logoVisible = await logo.isVisible();
    console.log('🔍 Logo "WppAgent" visível:', logoVisible);
    
    // Verificar se a seção de navegação existe
    const navSection = page.locator('h3:has-text("Navegação")');
    const navSectionVisible = await navSection.isVisible();
    console.log('🔍 Seção "Navegação" visível:', navSectionVisible);
    
    // Verificar se há botões no sidebar
    const buttons = await page.locator('button').all();
    console.log('🔍 Total de botões encontrados:', buttons.length);
    
    // Listar todos os botões
    for (let i = 0; i < Math.min(buttons.length, 10); i++) {
      const button = buttons[i];
      const text = await button.textContent();
      const isVisible = await button.isVisible();
      console.log(`  Botão ${i}: "${text?.trim()}" - visível: ${isVisible}`);
    }
    
    // Verificar se há elementos com texto "Dashboard"
    const dashboardElements = await page.locator('text=Dashboard').all();
    console.log('🔍 Elementos com "Dashboard":', dashboardElements.length);
    
    for (let i = 0; i < dashboardElements.length; i++) {
      const el = dashboardElements[i];
      const isVisible = await el.isVisible();
      const tagName = await el.evaluate(e => e.tagName);
      const parentClass = await el.evaluate(e => e.parentElement?.className);
      console.log(`  Dashboard ${i}: ${tagName} - visível: ${isVisible} - parent class: ${parentClass}`);
    }
    
    // Verificar se há elementos com texto "Agendamentos"
    const agendamentosElements = await page.locator('text=Agendamentos').all();
    console.log('🔍 Elementos com "Agendamentos":', agendamentosElements.length);
    
    for (let i = 0; i < agendamentosElements.length; i++) {
      const el = agendamentosElements[i];
      const isVisible = await el.isVisible();
      const tagName = await el.evaluate(e => e.tagName);
      const parentClass = await el.evaluate(e => e.parentElement?.className);
      console.log(`  Agendamentos ${i}: ${tagName} - visível: ${isVisible} - parent class: ${parentClass}`);
    }
    
    // Verificar se o menuItems está sendo renderizado
    const menuItems = await page.evaluate(() => {
      // Procurar por elementos que contenham os textos dos menu items
      const items = ['Dashboard', 'Conversas', 'Clientes', 'Agendamentos', 'Relatórios'];
      const found = [];
      
      items.forEach(item => {
        const elements = Array.from(document.querySelectorAll('*')).filter(el => 
          el.textContent?.includes(item) && el.textContent?.trim() === item
        );
        found.push({ item, count: elements.length, elements: elements.map(el => ({
          tagName: el.tagName,
          className: el.className,
          visible: el.offsetParent !== null
        })) });
      });
      
      return found;
    });
    
    console.log('🔍 Menu items encontrados:', menuItems);
    
    // Verificar se há algum erro de JavaScript
    const errors = await page.evaluate(() => {
      return window.console.errors || [];
    });
    
    if (errors.length > 0) {
      console.log('❌ Erros JavaScript encontrados:', errors);
    }
    
    // O teste passa se pelo menos o logo estiver visível
    expect(logoVisible).toBe(true);
  });
});