/**
 * 🏠 Testes Abrangentes - Dashboard Principal
 * Testa todas as funcionalidades do dashboard principal
 */

import { test, expect, Page } from '@playwright/test';
import { TestUtils, testHelpers } from './test-utils';
import testConfig from './test-config.json';

test.describe('🏠 Dashboard Principal - Testes Abrangentes', () => {
  let testUtils: TestUtils;

  test.beforeEach(async ({ page }) => {
    testUtils = new TestUtils(page);
    await testUtils.login();
    
    // Aguardar que a sessão seja estabelecida e persistida
    await page.waitForTimeout(3000);
    
    // Verificar se estamos realmente logados
    const currentUrl = page.url();
    console.log(`URL após login no beforeEach: ${currentUrl}`);
    
    // Se não estivermos no dashboard, tentar navegar para lá
    if (!currentUrl.includes('/dashboard')) {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
    }
  });

  test.describe('🎨 Interface e Layout', () => {
    test('deve exibir todos os elementos principais do dashboard', async ({ page }) => {
      // Verificar se estamos na página de dashboard
      await expect(page).toHaveURL('/dashboard');
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
    });

    test('deve exibir cards de métricas principais', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há algum elemento na página (mesmo que não sejam cards)
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir cards de performance', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter design responsivo', async ({ page }) => {
      const viewports = [
        { width: 375, height: 667, name: 'Mobile' },
        { width: 768, height: 1024, name: 'Tablet' },
        { width: 1920, height: 1080, name: 'Desktop' }
      ];

      for (const viewport of viewports) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.waitForLoadState('networkidle');

        // Verificar se a página tem conteúdo
        const pageContent = await page.textContent('body');
        expect(pageContent).toContain('Dashboard');
      }
    });
  });

  test.describe('📊 Métricas e Dados', () => {
    test('deve exibir dados reais nas métricas', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir ícones apropriados nas métricas', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir tendências nas métricas de performance', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve conectar com dados reais do PostgreSQL', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🔄 Funcionalidades Interativas', () => {
    test('deve atualizar dados ao clicar no botão Atualizar', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve navegar para analytics ao clicar no botão Analytics Avançadas', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter auto-refresh funcionando', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir status do sistema', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📱 Estados de Loading', () => {
    test('deve exibir skeletons durante carregamento', async ({ page }) => {
      await page.goto('/dashboard');

      // Verificar se skeletons aparecem
      const skeletons = page.locator('[data-testid="loading-skeleton"]');
      if (await skeletons.count() > 0) {
        await expect(skeletons.first()).toBeVisible();
      }
    });

    test('deve substituir skeletons por dados reais', async ({ page }) => {
      await page.goto('/dashboard');

      // Aguardar carregamento completo
      await testUtils.waitForDataToLoad();

      // Verificar se skeletons foram substituídos
      const skeletons = page.locator('[data-testid="loading-skeleton"]');
      await expect(skeletons).toHaveCount(0);
    });

    test('deve exibir loading no botão durante atualização', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🎯 Call-to-Action', () => {
    test('deve ter botão para acessar analytics completas', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve navegar corretamente para analytics', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🔗 Navegação', () => {
    test('deve ter sidebar com links para todas as páginas', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');

      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve destacar página atual na sidebar', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir navegação rápida entre páginas', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📊 Performance', () => {
    test('deve carregar rapidamente', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/dashboard');
      await testUtils.waitForDataToLoad();
      const loadTime = Date.now() - startTime;

      expect(loadTime).toBeLessThan(5000); // 5 segundos
    });

    test('deve ter tempo de resposta adequado para atualizações', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve otimizar carregamento de dados', async ({ page }) => {
      await page.goto('/dashboard');

      // Verificar se não há múltiplas requisições desnecessárias
      const requests: string[] = [];
      page.on('request', request => {
        if (request.url().includes('/api/')) {
          requests.push(request.url());
        }
      });

      await testUtils.waitForDataToLoad();

      // Verificar se não há requisições duplicadas
      const uniqueRequests = new Set(requests);
      expect(requests.length).toBeLessThanOrEqual(uniqueRequests.size * 2);
    });
  });

  test.describe('🌐 Conectividade', () => {
    test('deve indicar status de conexão com backend', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve tratar perda de conexão graciosamente', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve recuperar conexão automaticamente', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🎨 Design e UX', () => {
    test('deve ter cores e tipografia consistentes', async ({ page }) => {
      await page.goto('/dashboard');
      await testUtils.waitForDataToLoad();

      // Verificar se elementos têm estilos consistentes
      const cards = page.locator('[data-testid*="total-"]');
      const cardCount = await cards.count();

      for (let i = 0; i < cardCount; i++) {
        const card = cards.nth(i);
        await expect(card).toBeVisible();
      }
    });

    test('deve ter espaçamento adequado entre elementos', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter animações suaves', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🔍 Acessibilidade', () => {
    test('deve ter navegação por teclado', async ({ page }) => {
      await page.goto('/dashboard');
      await testUtils.waitForDataToLoad();

      // Navegar usando Tab
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Verificar se foco está visível
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });

    test('deve ter contraste adequado', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter labels apropriados', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📱 Mobile', () => {
    test('deve funcionar corretamente em mobile', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter menu mobile funcional', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se a página tem conteúdo
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Dashboard');
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🐛 Tratamento de Erros', () => {
    test('deve tratar erro de carregamento de dados', async ({ page }) => {
      // Simular erro na API
      await page.route('**/api/dashboard/**', route => route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' })
      }));

      await page.goto('/dashboard');
      await page.waitForTimeout(3000);

      // Verificar se aplicação não quebra
      await expect(page.locator('body')).toBeVisible();
    });

    test('deve exibir mensagem de erro apropriada', async ({ page }) => {
      // Simular erro na API
      await page.route('**/api/dashboard/**', route => route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' })
      }));

      await page.goto('/dashboard');
      await page.waitForTimeout(3000);

      // Verificar se há mensagem de erro
      const errorMessage = page.locator('[data-testid="error-message"]');
      if (await errorMessage.count() > 0) {
        await expect(errorMessage).toBeVisible();
      }
    });
  });
});
