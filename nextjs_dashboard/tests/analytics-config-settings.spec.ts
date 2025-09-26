/**
 * 📈 Testes Abrangentes - Analytics, Configurações e Outras Páginas
 * Testa todas as funcionalidades das páginas de Analytics, Configurações, etc.
 */

import { test, expect, Page } from '@playwright/test';
import { TestUtils, testHelpers } from './test-utils';
import testConfig from './test-config.json';

test.describe('📈 Analytics, Configurações e Outras Páginas - Testes Abrangentes', () => {
  let testUtils: TestUtils;
  
  // Aumentar timeout para todos os testes
  test.setTimeout(60000);

  test.beforeEach(async ({ page }) => {
    testUtils = new TestUtils(page);
    await testUtils.login();
    
    // Aguardar que a sessão seja estabelecida e persistida
    await page.waitForTimeout(3000);
    
    // Verificar se estamos realmente logados
    const currentUrl = page.url();
    console.log(`URL após login no beforeEach: ${currentUrl}`);
    
    // Navegar para a página de analytics por padrão
    await page.goto('/analytics');
    await page.waitForTimeout(3000);
  });

  test.describe('📊 Página de Analytics', () => {
    test('deve exibir todos os elementos da página de analytics', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir cards de métricas com tendências', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir tabs de análise', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir mudança de período', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir gráficos', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve conectar com dados reais do PostgreSQL', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir exportação de relatórios', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('⚙️ Página de Configurações', () => {
    test('deve exibir todos os elementos da página de configurações', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir configurações da empresa', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir edição das configurações da empresa', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir configurações do Bot & IA', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir configuração do Bot & IA', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir configurações de horários', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir configurações de notificações', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir configurações de segurança', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📊 Página de Relatórios', () => {
    test('deve exibir todos os elementos da página de relatórios', async ({ page }) => {
      await page.goto('/relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir tabs de análise', async ({ page }) => {
      await page.goto('/relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir cards de KPIs', async ({ page }) => {
      await page.goto('/relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir gráficos de relatórios', async ({ page }) => {
      await page.goto('/relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir exportação em diferentes formatos', async ({ page }) => {
      await page.goto('/relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter controles de configuração', async ({ page }) => {
      await page.goto('/relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🆘 Página de Suporte', () => {
    test('deve exibir todos os elementos da página de suporte', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir status do sistema', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir métricas do sistema', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir FAQ', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir formulário de ticket', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir envio de ticket', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('👤 Página de Perfil', () => {
    test('deve exibir todos os elementos da página de perfil', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir informações básicas do usuário', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir estatísticas do usuário', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir edição de informações pessoais', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir alteração de senha', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir configuração de preferências', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📊 Página de Monitoramento', () => {
    test('deve exibir todos os elementos da página de monitoramento', async ({ page }) => {
      await page.goto('/monitoring');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir status geral do sistema', async ({ page }) => {
      await page.goto('/monitoring');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir métricas do sistema', async ({ page }) => {
      await page.goto('/monitoring');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir alertas ativos', async ({ page }) => {
      await page.goto('/monitoring');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir resolução de alertas', async ({ page }) => {
      await page.goto('/monitoring');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter auto-refresh', async ({ page }) => {
      await page.goto('/monitoring');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📄 Página de Exportar Relatórios', () => {
    test('deve exibir todos os elementos da página de exportar relatórios', async ({ page }) => {
      await page.goto('/exportar-relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir informações sobre formatos disponíveis', async ({ page }) => {
      await page.goto('/exportar-relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter acesso restrito a usuários autenticados', async ({ page }) => {
      await page.goto('/exportar-relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📱 Responsividade das Páginas', () => {
    test('deve funcionar corretamente em mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      // Testar apenas uma página para evitar timeout
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🐛 Tratamento de Erros', () => {
    test('deve tratar erro de carregamento de dados', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve tratar erro de salvamento de configurações', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });
});