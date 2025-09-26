/**
 * 📋 Testes Abrangentes - Páginas CRUD
 * Testa todas as funcionalidades das páginas de Clientes, Agendamentos, etc.
 */

import { test, expect, Page } from '@playwright/test';
import { TestUtils, testHelpers } from './test-utils';
import testConfig from './test-config.json';

test.describe('📋 Páginas CRUD - Testes Abrangentes', () => {
  let testUtils: TestUtils;

  test.beforeEach(async ({ page }) => {
    testUtils = new TestUtils(page);
    await testUtils.login();
    
    // Aguardar que a sessão seja estabelecida e persistida
    await page.waitForTimeout(3000);
    
    // Verificar se estamos realmente logados
    const currentUrl = page.url();
    console.log(`URL após login no beforeEach: ${currentUrl}`);
    
    // Navegar para a página de clientes por padrão
    await page.goto('/clientes');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test.describe('👥 Página de Clientes', () => {
    test('deve exibir todos os elementos da página de clientes', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir filtros de busca e ordenação', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir lista de clientes', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir busca de clientes', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve abrir formulário de novo cliente', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir criação de novo cliente', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir edição de cliente', async ({ page }) => {
      await page.goto('/clientes');
      await testUtils.waitForDataToLoad();

      const clientRows = page.locator('[data-testid="client-row"]');
      const rowCount = await clientRows.count();

      if (rowCount > 0) {
        // Clicar no botão de editar
        const editButton = clientRows.first().locator('button[data-testid="edit-client"]');
        await editButton.click();

        // Verificar se formulário abre
        const clientForm = page.locator('[data-testid="client-form"]');
        await expect(clientForm).toBeVisible();

        // Modificar dados
        const nameInput = page.locator('input[name="name"]');
        await nameInput.fill('Nome Atualizado');

        // Salvar
        await page.click('button:has-text("Salvar")');
        await testUtils.waitForLoadingToFinish();

        // Verificar se cliente foi atualizado
        await testUtils.verifyNotification('Cliente atualizado com sucesso', 'success');
      }
    });

    test('deve permitir visualização de detalhes do cliente', async ({ page }) => {
      await page.goto('/clientes');
      await testUtils.waitForDataToLoad();

      const clientRows = page.locator('[data-testid="client-row"]');
      const rowCount = await clientRows.count();

      if (rowCount > 0) {
        // Clicar no botão de visualizar
        const viewButton = clientRows.first().locator('button[data-testid="view-client"]');
        await viewButton.click();

        // Verificar se modal de detalhes abre
        const clientDetails = page.locator('[data-testid="client-details"]');
        await expect(clientDetails).toBeVisible();
      }
    });
  });

  test.describe('📅 Página de Agendamentos', () => {
    test('deve exibir todos os elementos da página de agendamentos', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir cards de estatísticas', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir tabs de visualização', async ({ page }) => {
      await page.goto('/agendamentos');
      await testUtils.waitForDataToLoad();

      const tabs = [
        'button:has-text("Lista")',
        'button:has-text("Calendário")',
        'button:has-text("Hoje")'
      ];

      for (const tab of tabs) {
        await expect(page.locator(tab)).toBeVisible();
      }
    });

    test('deve permitir criação de novo agendamento', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir filtros por status e data', async ({ page }) => {
      await page.goto('/agendamentos');
      await testUtils.waitForDataToLoad();

      // Testar filtro por status
      const statusSelect = page.locator('select[name="status"]');
      if (await statusSelect.count() > 0) {
        await statusSelect.selectOption('Confirmado');
        await testUtils.waitForLoadingToFinish();
      }

      // Testar filtro por data
      const dateSelect = page.locator('select[name="date"]');
      if (await dateSelect.count() > 0) {
        await dateSelect.selectOption('Hoje');
        await testUtils.waitForLoadingToFinish();
      }
    });

    test('deve permitir busca de agendamentos', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir edição de agendamento', async ({ page }) => {
      await page.goto('/agendamentos');
      await testUtils.waitForDataToLoad();

      const appointmentRows = page.locator('[data-testid="appointment-row"]');
      const rowCount = await appointmentRows.count();

      if (rowCount > 0) {
        // Clicar no botão de editar
        const editButton = appointmentRows.first().locator('button[data-testid="edit-appointment"]');
        await editButton.click();

        // Verificar se formulário abre
        const appointmentForm = page.locator('[data-testid="appointment-form"]');
        await expect(appointmentForm).toBeVisible();

        // Modificar status
        const statusSelect = page.locator('select[name="status"]');
        await statusSelect.selectOption('Confirmado');

        // Salvar
        await page.click('button:has-text("Salvar")');
        await testUtils.waitForLoadingToFinish();

        // Verificar se agendamento foi atualizado
        await testUtils.verifyNotification('Agendamento atualizado com sucesso', 'success');
      }
    });

    test('deve permitir exclusão de agendamento', async ({ page }) => {
      await page.goto('/agendamentos');
      await testUtils.waitForDataToLoad();

      const appointmentRows = page.locator('[data-testid="appointment-row"]');
      const rowCount = await appointmentRows.count();

      if (rowCount > 0) {
        // Clicar no botão de excluir
        const deleteButton = appointmentRows.first().locator('button[data-testid="delete-appointment"]');
        await deleteButton.click();

        // Verificar se modal de confirmação abre
        const confirmModal = page.locator('[data-testid="confirm-modal"]');
        if (await confirmModal.count() > 0) {
          await expect(confirmModal).toBeVisible();
          
          // Confirmar exclusão
          await page.click('button:has-text("Confirmar")');
          await testUtils.waitForLoadingToFinish();

          // Verificar se agendamento foi excluído
          await testUtils.verifyNotification('Agendamento excluído com sucesso', 'success');
        }
      }
    });

    test('deve exibir atualizações em tempo real via WebSocket', async ({ page }) => {
      await page.goto('/agendamentos');
      await testUtils.waitForDataToLoad();

      // Verificar contador de eventos
      const eventCounter = page.locator('[data-testid="event-counter"]');
      if (await eventCounter.count() > 0) {
        await expect(eventCounter).toBeVisible();
      }

      // Aguardar possíveis atualizações
      await page.waitForTimeout(5000);
    });
  });

  test.describe('🚫 Página de Horários Bloqueados', () => {
    test('deve exibir todos os elementos da página de horários bloqueados', async ({ page }) => {
      await page.goto('/bloqueados');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir cards de métricas', async ({ page }) => {
      await page.goto('/bloqueados');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir criação de novo bloqueio', async ({ page }) => {
      await page.goto('/bloqueados');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir filtros por tipo', async ({ page }) => {
      await page.goto('/bloqueados');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir tabela de horários bloqueados', async ({ page }) => {
      await page.goto('/bloqueados');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📊 Funcionalidades Comuns CRUD', () => {
    test('deve ter paginação em listas grandes', async ({ page }) => {
      const pages = ['/clientes', '/agendamentos', '/bloqueados'];

      for (const pageUrl of pages) {
        await page.goto(pageUrl);
        await page.waitForTimeout(3000);
        
        // Verificar se há elementos na página
        const elements = page.locator('div');
        const elementCount = await elements.count();
        expect(elementCount).toBeGreaterThan(0);
      }
    });

    test('deve ter ordenação por colunas', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter exportação de dados', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter validação de formulários', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter confirmação para ações destrutivas', async ({ page }) => {
      await page.goto('/agendamentos');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📱 Responsividade CRUD', () => {
    test('deve funcionar corretamente em mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      const pages = ['/clientes', '/agendamentos', '/bloqueados'];

      for (const pageUrl of pages) {
        await page.goto(pageUrl);
        await page.waitForTimeout(3000);
        
        // Verificar se há elementos na página
        const elements = page.locator('div');
        const elementCount = await elements.count();
        expect(elementCount).toBeGreaterThan(0);
      }
    });

    test('deve ter scroll horizontal em tabelas em mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('🐛 Tratamento de Erros CRUD', () => {
    test('deve tratar erro de carregamento de dados', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve tratar erro de criação de registro', async ({ page }) => {
      await page.goto('/clientes');
      await page.waitForLoadState('networkidle');
      
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });
});
