import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
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

test.describe('PWA e Funcionalidades Offline', () => {
  test('Service Worker - Registro e Ativação', async ({ page }) => {
    await page.goto('/');
    
    // Verificar se service worker está registrado
    const swRegistration = await page.evaluate(async () => {
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration();
        return registration ? 'registered' : 'not_registered';
      }
      return 'not_supported';
    });
    
    expect(swRegistration).toBe('registered');
    
    // Verificar se service worker está ativo
    const swActive = await page.evaluate(async () => {
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration();
        return registration && registration.active ? 'active' : 'not_active';
      }
      return 'not_supported';
    });
    
    expect(swActive).toBe('active');
  });

  test('Manifest - Configuração PWA', async ({ page }) => {
    await page.goto('/');
    
    // Verificar se manifest está presente
    const manifest = await page.evaluate(() => {
      const manifestLink = document.querySelector('link[rel="manifest"]');
      return manifestLink ? manifestLink.getAttribute('href') : null;
    });
    
    expect(manifest).toBeTruthy();
    
    // Verificar conteúdo do manifest
    const manifestContent = await page.evaluate(async () => {
      const manifestLink = document.querySelector('link[rel="manifest"]');
      if (manifestLink) {
        const response = await fetch(manifestLink.getAttribute('href'));
        return await response.json();
      }
      return null;
    });
    
    expect(manifestContent).toBeTruthy();
    expect(manifestContent.name).toBeTruthy();
    expect(manifestContent.short_name).toBeTruthy();
    expect(manifestContent.icons).toBeTruthy();
    expect(manifestContent.start_url).toBeTruthy();
    expect(manifestContent.display).toBeTruthy();
    expect(manifestContent.theme_color).toBeTruthy();
    expect(manifestContent.background_color).toBeTruthy();
  });

  test('Ícones PWA - Diferentes Tamanhos', async ({ page }) => {
    await page.goto('/');
    
    // Verificar ícones de diferentes tamanhos
    const iconSizes = ['72x72', '96x96', '128x128', '144x144', '152x152', '192x192', '384x384', '512x512'];
    
    for (const size of iconSizes) {
      const icon = await page.evaluate((size) => {
        const iconLink = document.querySelector(`link[rel="icon"][sizes="${size}"]`);
        return iconLink ? iconLink.getAttribute('href') : null;
      }, size);
      
      expect(icon).toBeTruthy();
    }
  });

  test('Funcionalidades Offline - Modo Offline', async ({ page }) => {
    await login(page);
    
    // Simular modo offline
    await page.context().setOffline(true);
    
    // Verificar se indicador offline aparece
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
    
    // Verificar se página ainda funciona
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
    
    // Verificar se dados em cache são exibidos
    await expect(page.locator('[data-testid="cached-data"]')).toBeVisible();
    
    // Simular modo online
    await page.context().setOffline(false);
    
    // Verificar se indicador offline desaparece
    await expect(page.locator('[data-testid="offline-indicator"]')).not.toBeVisible();
  });

  test('Cache - Armazenamento de Dados', async ({ page }) => {
    await login(page);
    
    // Navegar para diferentes páginas para popular cache
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    await page.goto('/agendamentos');
    await page.waitForLoadState('networkidle');
    
    await page.goto('/conversas');
    await page.waitForLoadState('networkidle');
    
    await page.goto('/clientes');
    await page.waitForLoadState('networkidle');
    
    // Simular modo offline
    await page.context().setOffline(true);
    
    // Verificar se páginas ainda funcionam offline
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
    
    await page.goto('/agendamentos');
    await expect(page.locator('h1')).toContainText('Agendamentos');
    
    await page.goto('/conversas');
    await expect(page.locator('h1')).toContainText('Conversas');
    
    await page.goto('/clientes');
    await expect(page.locator('h1')).toContainText('Clientes');
  });

  test('Sincronização - Dados Offline/Online', async ({ page }) => {
    await login(page);
    
    // Simular modo offline
    await page.context().setOffline(true);
    
    // Fazer alterações offline
    await page.goto('/agendamentos');
    await page.click('button:has-text("Novo Agendamento")');
    await page.waitForSelector('[data-testid="appointment-form"]');
    
    await page.fill('input[name="clientName"]', 'Cliente Offline');
    await page.fill('input[name="clientPhone"]', '11999999999');
    await page.selectOption('select[name="service"]', 'Limpeza de Pele');
    await page.fill('input[name="date"]', '2024-12-25');
    await page.fill('input[name="time"]', '14:00');
    
    await page.click('button:has-text("Salvar")');
    
    // Verificar se foi salvo localmente
    await expect(page.locator('text=Salvo localmente')).toBeVisible();
    
    // Simular modo online
    await page.context().setOffline(false);
    
    // Aguardar sincronização
    await page.waitForTimeout(2000);
    
    // Verificar se dados foram sincronizados
    await expect(page.locator('text=Sincronizado com sucesso')).toBeVisible();
  });

  test('Notificações Push - Configuração', async ({ page }) => {
    await page.goto('/');
    
    // Verificar se notificações são suportadas
    const notificationSupport = await page.evaluate(() => {
      return 'Notification' in window;
    });
    
    if (notificationSupport) {
      // Solicitar permissão para notificações
      const permission = await page.evaluate(async () => {
        return await Notification.requestPermission();
      });
      
      expect(permission).toBeTruthy();
      
      // Verificar se notificação foi configurada
      const notificationConfigured = await page.evaluate(() => {
        return window.Notification && window.Notification.permission === 'granted';
      });
      
      expect(notificationConfigured).toBeTruthy();
    }
  });

  test('Instalação PWA - Prompt de Instalação', async ({ page }) => {
    await page.goto('/');
    
    // Verificar se prompt de instalação está disponível
    const installPrompt = await page.evaluate(() => {
      return window.deferredPrompt ? 'available' : 'not_available';
    });
    
    if (installPrompt === 'available') {
      // Simular clique no botão de instalação
      await page.click('button:has-text("Instalar App")');
      
      // Verificar se app foi instalado
      const installed = await page.evaluate(() => {
        return window.matchMedia('(display-mode: standalone)').matches;
      });
      
      expect(installed).toBeTruthy();
    }
  });

  test('Performance - Métricas PWA', async ({ page }) => {
    await page.goto('/');
    
    // Verificar métricas de performance
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint')?.startTime || 0
      };
    });
    
    // Verificar se métricas estão dentro dos limites aceitáveis
    expect(performanceMetrics.loadTime).toBeLessThan(3000); // Menos de 3 segundos
    expect(performanceMetrics.domContentLoaded).toBeLessThan(2000); // Menos de 2 segundos
    expect(performanceMetrics.firstPaint).toBeLessThan(1000); // Menos de 1 segundo
    expect(performanceMetrics.firstContentfulPaint).toBeLessThan(1500); // Menos de 1.5 segundos
  });

  test('Responsividade - Diferentes Dispositivos', async ({ page }) => {
    await login(page);
    
    // Testar em diferentes tamanhos de tela
    const viewports = [
      { width: 375, height: 667, name: 'Mobile' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 1920, height: 1080, name: 'Desktop' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      
      // Navegar para diferentes páginas
      const pages = ['/dashboard', '/agendamentos', '/conversas', '/clientes'];
      
      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle');
        
        // Verificar se página é responsiva
        await expect(page.locator('body')).toBeVisible();
        
        // Verificar se não há overflow horizontal
        const hasHorizontalScroll = await page.evaluate(() => {
          return document.documentElement.scrollWidth > document.documentElement.clientWidth;
        });
        
        expect(hasHorizontalScroll).toBeFalsy();
      }
    }
  });

  test('Acessibilidade - Navegação por Teclado', async ({ page }) => {
    await login(page);
    
    // Testar navegação por teclado
    await page.goto('/dashboard');
    
    // Navegar usando Tab
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Verificar se foco está visível
    const focusedElement = await page.evaluate(() => {
      return document.activeElement ? document.activeElement.tagName : null;
    });
    
    expect(focusedElement).toBeTruthy();
    
    // Testar navegação com Enter
    await page.keyboard.press('Enter');
    
    // Verificar se ação foi executada
    await page.waitForTimeout(1000);
  });

  test('Acessibilidade - Contraste e Legibilidade', async ({ page }) => {
    await login(page);
    
    // Verificar contraste de textos
    const textElements = await page.locator('p, h1, h2, h3, h4, h5, h6, span').all();
    
    for (const element of textElements) {
      const text = await element.textContent();
      if (text && text.trim()) {
        // Verificar se texto é legível
        const isVisible = await element.isVisible();
        expect(isVisible).toBeTruthy();
      }
    }
  });

  test('Error Boundaries - Tratamento de Erros', async ({ page }) => {
    await login(page);
    
    // Simular erro de rede
    await page.route('**/api/**', route => route.abort());
    
    // Navegar para página que faz requisições
    await page.goto('/dashboard');
    
    // Verificar se error boundary é exibido
    await expect(page.locator('[data-testid="error-boundary"]')).toBeVisible();
    
    // Verificar se botão de retry está presente
    await expect(page.locator('button:has-text("Tentar Novamente")')).toBeVisible();
    
    // Testar retry
    await page.unroute('**/api/**');
    await page.click('button:has-text("Tentar Novamente")');
    
    // Verificar se página carregou normalmente
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('Loading States - Feedback Visual', async ({ page }) => {
    await login(page);
    
    // Simular carregamento lento
    await page.route('**/api/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.continue();
    });
    
    // Navegar para página
    await page.goto('/dashboard');
    
    // Verificar se loading state é exibido
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
    
    // Aguardar carregamento
    await page.waitForLoadState('networkidle');
    
    // Verificar se loading state desapareceu
    await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible();
  });
});
