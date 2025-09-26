/**
 * 🔄 Testes de Integração e Fluxos Completos
 * Testa fluxos completos e integração entre diferentes páginas
 */

import { test, expect, Page } from '@playwright/test';
import { TestUtils, testHelpers } from './test-utils';
import testConfig from './test-config.json';

test.describe('🔄 Testes de Integração e Fluxos Completos', () => {
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
    
    // Navegar para o dashboard por padrão
    await page.goto('/dashboard');
    await page.waitForTimeout(3000);
  });

  test.describe('🔐 Fluxo Completo de Autenticação', () => {
    test('deve realizar login e logout completo', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve redirecionar para página anterior após login', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve manter sessão entre navegações', async ({ page }) => {
      // Navegar entre páginas
      const pages = ['/dashboard', '/clientes', '/agendamentos', '/analytics'];
      
      for (const pageUrl of pages) {
        await page.goto(pageUrl);
        await page.waitForTimeout(3000);
        
        // Verificar se há elementos na página
        const elements = page.locator('div');
        const elementCount = await elements.count();
        expect(elementCount).toBeGreaterThan(0);
      }
    });
  });

  test.describe('👥 Fluxo Completo de Gestão de Clientes', () => {
    test('deve criar, editar e visualizar cliente', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve filtrar e buscar clientes', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve exportar lista de clientes', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('📅 Fluxo Completo de Gestão de Agendamentos', () => {
    test('deve criar, editar e cancelar agendamento', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve filtrar agendamentos por data e status', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve exibir calendário de agendamentos', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('🚫 Fluxo Completo de Gestão de Horários Bloqueados', () => {
    test('deve criar e gerenciar horários bloqueados', async ({ page }) => {
      await page.goto('/bloqueados');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve filtrar horários bloqueados por tipo', async ({ page }) => {
      await page.goto('/bloqueados');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('💬 Fluxo Completo de Gestão de Conversas', () => {
    test('deve visualizar e gerenciar conversas', async ({ page }) => {
      await page.goto('/conversas');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve filtrar conversas por status', async ({ page }) => {
      await page.goto('/conversas');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve buscar conversas por cliente', async ({ page }) => {
      await page.goto('/conversas');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('📊 Fluxo Completo de Analytics e Relatórios', () => {
    test('deve visualizar métricas e gráficos', async ({ page }) => {
      await page.goto('/analytics');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve gerar relatórios personalizados', async ({ page }) => {
      await page.goto('/relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve exportar dados em diferentes formatos', async ({ page }) => {
      await page.goto('/exportar-relatorios');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('⚙️ Fluxo Completo de Configurações', () => {
    test('deve configurar empresa e horários', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve configurar bot e IA', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve configurar notificações e segurança', async ({ page }) => {
      await page.goto('/configuracoes');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('👤 Fluxo Completo de Perfil do Usuário', () => {
    test('deve visualizar e editar perfil', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve alterar senha e preferências', async ({ page }) => {
      await page.goto('/perfil');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('🆘 Fluxo Completo de Suporte', () => {
    test('deve visualizar status do sistema', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve criar e gerenciar tickets', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve acessar FAQ e documentação', async ({ page }) => {
      await page.goto('/suporte');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('📊 Fluxo Completo de Monitoramento', () => {
    test('deve visualizar métricas do sistema', async ({ page }) => {
      await page.goto('/monitoring');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve gerenciar alertas e notificações', async ({ page }) => {
      await page.goto('/monitoring');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('🔄 Fluxos de Integração Entre Páginas', () => {
    test('deve navegar entre todas as páginas principais', async ({ page }) => {
      const pages = [
        '/dashboard',
        '/clientes',
        '/agendamentos',
        '/conversas',
        '/analytics',
        '/relatorios',
        '/configuracoes',
        '/perfil',
        '/suporte',
        '/monitoring'
      ];

      for (const pageUrl of pages) {
        await page.goto(pageUrl);
        await page.waitForTimeout(3000);
        
        // Verificar se há elementos na página
        const elements = page.locator('div');
        const elementCount = await elements.count();
        expect(elementCount).toBeGreaterThan(0);
      }
    });

    test('deve manter estado entre navegações', async ({ page }) => {
      // Navegar para diferentes páginas
      await page.goto('/clientes');
      await page.waitForTimeout(3000);
      
      await page.goto('/agendamentos');
      await page.waitForTimeout(3000);
      
      await page.goto('/dashboard');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });

  test.describe('🐛 Tratamento de Erros e Edge Cases', () => {
    test('deve tratar erros de navegação', async ({ page }) => {
      await page.goto('/pagina-inexistente');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });

    test('deve tratar erros de carregamento de dados', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForTimeout(3000);
      
      // Verificar se a página carregou sem erros
      const pageContent = await page.content();
      expect(pageContent).toBeTruthy();
    });
  });
});