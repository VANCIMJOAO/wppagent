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

test.describe('Debug Sidebar CSS - Investigar Problemas de Visibilidade', () => {
  test('Debug sidebar CSS e posicionamento', async ({ page }) => {
    await login(page);
    console.log('✅ Login realizado');

    // Aguardar sidebar carregar
    await page.waitForTimeout(3000);

    // Verificar se há elementos do sidebar no DOM
    const sidebarElements = await page.locator('[class*="sidebar"], [class*="Sidebar"], nav, aside').all();
    console.log('📋 Elementos de sidebar encontrados:', sidebarElements.length);

    // Verificar cada elemento
    for (let i = 0; i < sidebarElements.length; i++) {
      const element = sidebarElements[i];
      const tagName = await element.evaluate(el => el.tagName);
      const className = await element.getAttribute('class');
      const isVisible = await element.isVisible();
      const computedStyle = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return {
          display: style.display,
          visibility: style.visibility,
          opacity: style.opacity,
          position: style.position,
          left: style.left,
          top: style.top,
          width: style.width,
          height: style.height,
          transform: style.transform,
          zIndex: style.zIndex
        };
      });
      
      console.log(`  Elemento ${i}:`);
      console.log(`    Tag: ${tagName}`);
      console.log(`    Class: ${className}`);
      console.log(`    Visível: ${isVisible}`);
      console.log(`    CSS:`, computedStyle);
    }

    // Verificar se há elementos com texto específico
    const dashboardText = await page.locator('text=Dashboard').all();
    console.log('🏠 Elementos com "Dashboard":', dashboardText.length);
    
    for (let i = 0; i < dashboardText.length; i++) {
      const element = dashboardText[i];
      const isVisible = await element.isVisible();
      const parent = element.locator('..');
      const parentClass = await parent.getAttribute('class');
      console.log(`  Dashboard ${i}: visível=${isVisible}, parent class=${parentClass}`);
    }

    // Verificar se há elementos com texto "Agendamentos"
    const agendamentosText = await page.locator('text=Agendamentos').all();
    console.log('📅 Elementos com "Agendamentos":', agendamentosText.length);
    
    for (let i = 0; i < agendamentosText.length; i++) {
      const element = agendamentosText[i];
      const isVisible = await element.isVisible();
      const parent = element.locator('..');
      const parentClass = await parent.getAttribute('class');
      console.log(`  Agendamentos ${i}: visível=${isVisible}, parent class=${parentClass}`);
    }

    // Verificar se há elementos com texto "Conversas"
    const conversasText = await page.locator('text=Conversas').all();
    console.log('💬 Elementos com "Conversas":', conversasText.length);
    
    for (let i = 0; i < conversasText.length; i++) {
      const element = conversasText[i];
      const isVisible = await element.isVisible();
      const parent = element.locator('..');
      const parentClass = await parent.getAttribute('class');
      console.log(`  Conversas ${i}: visível=${isVisible}, parent class=${parentClass}`);
    }

    // Verificar se há elementos com classes específicas do sidebar
    const sidebarClasses = [
      'fixed', 'md:relative', 'inset-y-0', 'left-0', 'z-40',
      'w-80', 'bg-white', 'border-r', 'border-gray-200'
    ];
    
    for (const className of sidebarClasses) {
      const elements = await page.locator(`[class*="${className}"]`).all();
      console.log(`🎨 Elementos com classe "${className}":`, elements.length);
    }

    // Verificar se há elementos ocultos por CSS
    const hiddenElements = await page.locator('[style*="display: none"], [style*="visibility: hidden"], [style*="opacity: 0"]').all();
    console.log('👻 Elementos ocultos por CSS:', hiddenElements.length);

    // Verificar se há elementos com transform translate
    const transformedElements = await page.locator('[style*="transform"], [class*="translate"]').all();
    console.log('🔄 Elementos com transform:', transformedElements.length);

    // O teste passa se encontrou pelo menos alguns elementos
    expect(sidebarElements.length).toBeGreaterThan(0);
  });
});
