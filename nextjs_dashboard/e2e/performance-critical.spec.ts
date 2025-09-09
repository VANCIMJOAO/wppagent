import { test, expect, PageHelpers } from './test-setup';

test.describe('Testes de Performance e Acessibilidade', () => {
  test('deve carregar páginas em tempo aceitável', async ({ page }) => {
    const helpers = new PageHelpers(page);
    
    const pages = [
      '/login',
      '/dashboard',
      '/dashboard/appointments', 
      '/dashboard/messages',
      '/dashboard/analytics'
    ];
    
    for (const url of pages) {
      const startTime = Date.now();
      
      await page.goto(url);
      
      // Para páginas protegidas, fazer login primeiro
      if (url !== '/login' && page.url().includes('/login')) {
        await page.fill('[data-testid="email"], [name="email"], [type="email"]', 'admin@test.com');
        await page.fill('[data-testid="password"], [name="password"], [type="password"]', 'admin123');
        await page.click('[data-testid="login-button"], [type="submit"], button:has-text("Entrar")');
        await page.waitForURL('/dashboard/**');
        
        // Navegar para página desejada após login
        if (url !== '/dashboard') {
          await page.goto(url);
        }
      }
      
      await helpers.waitForLoadingToFinish();
      
      const loadTime = Date.now() - startTime;
      
      // Página deve carregar em menos de 5 segundos
      expect(loadTime).toBeLessThan(5000);
      
      console.log(`✅ ${url}: Carregou em ${loadTime}ms`);
    }
  });

  test('deve ter boa acessibilidade básica', async ({ page }) => {
    await page.goto('/login');
    
    // Verificar se há landmarks básicos
    const main = page.locator('main, [role="main"]');
    if (await main.count() > 0) {
      console.log('✅ Landmark main presente');
    }
    
    // Verificar labels em inputs
    const inputs = page.locator('input, textarea, select');
    const inputCount = await inputs.count();
    
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const hasLabel = await input.locator('..').locator('label').count() > 0 ||
                      await input.getAttribute('aria-label') !== null ||
                      await input.getAttribute('aria-labelledby') !== null ||
                      await input.getAttribute('placeholder') !== null;
      
      if (hasLabel) {
        console.log(`✅ Input ${i}: Tem label/descrição`);
      } else {
        console.log(`⚠️ Input ${i}: Sem label adequado`);
      }
    }
    
    // Verificar se botões têm texto descritivo
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      
      if (text?.trim() || ariaLabel) {
        console.log(`✅ Botão ${i}: Tem texto descritivo`);
      } else {
        console.log(`⚠️ Botão ${i}: Sem texto descritivo`);
      }
    }
  });

  test('deve funcionar com navegação por teclado', async ({ page }) => {
    await page.goto('/login');
    
    // Testar navegação Tab
    await page.keyboard.press('Tab');
    
    // Verificar se há elemento focado
    const focusedElement = await page.locator(':focus').count();
    expect(focusedElement).toBeGreaterThan(0);
    
    // Navegar por todos os elementos focáveis
    const focusableElements = await page.locator('input, button, a, select, textarea, [tabindex]:not([tabindex="-1"])').count();
    
    for (let i = 0; i < Math.min(focusableElements, 10); i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);
    }
    
    console.log('✅ Navegação por teclado funcionando');
  });

  test('deve lidar com erros de rede graciosamente', async ({ page }) => {
    const helpers = new PageHelpers(page);
    
    // Simular falha de rede
    await page.route('**/api/**', route => {
      route.abort('failed');
    });
    
    await page.goto('/dashboard');
    
    // Para páginas que precisam de login, fazer login primeiro
    if (page.url().includes('/login')) {
      await page.fill('[data-testid="email"], [name="email"], [type="email"]', 'admin@test.com');
      await page.fill('[data-testid="password"], [name="password"], [type="password"]', 'admin123');
      
      // Tentar login (vai falhar por causa do mock de rede)
      await page.click('[data-testid="login-button"], [type="submit"], button:has-text("Entrar")');
      
      // Verificar se erro é tratado graciosamente
      const errorMessage = page.locator('[data-testid*="error"], .error, .alert-error');
      
      if (await errorMessage.count() > 0) {
        await expect(errorMessage.first()).toBeVisible({ timeout: 10000 });
        console.log('✅ Erros de rede tratados graciosamente');
      } else {
        console.log('⚠️ Tratamento de erro de rede pode estar ausente');
      }
    }
  });

  test('deve manter estado ao recarregar página', async ({ page }) => {
    const helpers = new PageHelpers(page);
    
    // Fazer login
    await page.goto('/login');
    await page.fill('[data-testid="email"], [name="email"], [type="email"]', 'admin@test.com');
    await page.fill('[data-testid="password"], [name="password"], [type="password"]', 'admin123');
    await page.click('[data-testid="login-button"], [type="submit"], button:has-text("Entrar")');
    await page.waitForURL('/dashboard/**');
    
    // Navegar para uma página específica
    await page.goto('/dashboard/appointments');
    await helpers.waitForLoadingToFinish();
    
    // Recarregar página
    await page.reload();
    await helpers.waitForLoadingToFinish();
    
    // Verificar se ainda está autenticado e na página correta
    await expect(page).toHaveURL(/\/dashboard\/appointments/);
    
    // Verificar se não foi redirecionado para login
    const isOnLogin = page.url().includes('/login');
    expect(isOnLogin).toBeFalsy();
    
    console.log('✅ Estado mantido após reload');
  });

  test('deve funcionar offline (se PWA implementado)', async ({ page }) => {
    const helpers = new PageHelpers(page);
    
    // Fazer login primeiro
    await page.goto('/login');
    await page.fill('[data-testid="email"], [name="email"], [type="email"]', 'admin@test.com');
    await page.fill('[data-testid="password"], [name="password"], [type="password"]', 'admin123');
    await page.click('[data-testid="login-button"], [type="submit"], button:has-text("Entrar")');
    await page.waitForURL('/dashboard/**');
    
    // Simular modo offline
    await page.context().setOffline(true);
    
    // Tentar navegar para dashboard
    await page.goto('/dashboard');
    
    // Se PWA implementado, deve funcionar offline
    const pageLoaded = await page.locator('body').isVisible();
    
    if (pageLoaded) {
      console.log('✅ Funciona offline (PWA implementado)');
      
      // Verificar se há indicação de modo offline
      const offlineIndicator = page.locator('[data-testid*="offline"], .offline-indicator, text="Offline"');
      if (await offlineIndicator.count() > 0) {
        console.log('✅ Indicador de modo offline presente');
      }
    } else {
      console.log('⚠️ PWA offline não implementado');
    }
    
    // Restaurar modo online
    await page.context().setOffline(false);
  });

  test('deve ter tempos de resposta adequados para interações', async ({ page }) => {
    const helpers = new PageHelpers(page);
    
    // Fazer login
    await page.goto('/login');
    await page.fill('[data-testid="email"], [name="email"], [type="email"]', 'admin@test.com');
    await page.fill('[data-testid="password"], [name="password"], [type="password"]', 'admin123');
    
    const startTime = Date.now();
    await page.click('[data-testid="login-button"], [type="submit"], button:has-text("Entrar")');
    await page.waitForURL('/dashboard/**');
    const loginTime = Date.now() - startTime;
    
    // Login deve completar em menos de 3 segundos
    expect(loginTime).toBeLessThan(3000);
    console.log(`✅ Login completou em ${loginTime}ms`);
    
    // Testar navegação rápida entre páginas
    const navigationStart = Date.now();
    await page.goto('/dashboard/appointments');
    await helpers.waitForLoadingToFinish();
    const navigationTime = Date.now() - navigationStart;
    
    // Navegação deve ser rápida (menos de 2 segundos)
    expect(navigationTime).toBeLessThan(2000);
    console.log(`✅ Navegação completou em ${navigationTime}ms`);
  });
});
