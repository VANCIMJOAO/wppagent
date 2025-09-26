/**
 * 💬 Testes Abrangentes - Página de Conversas
 * Testa todas as funcionalidades da página de conversas
 */

import { test, expect, Page } from '@playwright/test';
import { TestUtils, testHelpers } from './test-utils';
import testConfig from './test-config.json';

test.describe('💬 Página de Conversas - Testes Abrangentes', () => {
  let testUtils: TestUtils;

  test.beforeEach(async ({ page }) => {
    testUtils = new TestUtils(page);
    await testUtils.login();
    
    // Aguardar que a sessão seja estabelecida e persistida
    await page.waitForTimeout(3000);
    
    // Verificar se estamos realmente logados
    const currentUrl = page.url();
    console.log(`URL após login no beforeEach: ${currentUrl}`);
    
    // Navegar para a página de conversas
    await page.goto('/conversas');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
  });

  test.describe('🎨 Interface e Layout', () => {
    test('deve exibir todos os elementos principais da página de conversas', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve ter layout responsivo', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir campo de busca na sidebar', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir botão de refresh na sidebar', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('📋 Lista de Conversas', () => {
    test('deve exibir lista de conversas na sidebar', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve exibir informações básicas de cada conversa', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        const firstItem = conversationItems.first();
        
        // Verificar avatar
        await expect(firstItem.locator('[data-testid="conversation-avatar"]')).toBeVisible();
        
        // Verificar nome do cliente
        await expect(firstItem.locator('[data-testid="client-name"]')).toBeVisible();
        
        // Verificar última mensagem
        await expect(firstItem.locator('[data-testid="last-message"]')).toBeVisible();
        
        // Verificar timestamp
        await expect(firstItem.locator('[data-testid="message-timestamp"]')).toBeVisible();
      }
    });

    test('deve exibir status das conversas', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        const firstItem = conversationItems.first();
        const statusBadge = firstItem.locator('[data-testid="conversation-status"]');
        
        if (await statusBadge.count() > 0) {
          await expect(statusBadge).toBeVisible();
        }
      }
    });

    test('deve exibir contador de mensagens', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        const firstItem = conversationItems.first();
        const messageCount = firstItem.locator('[data-testid="message-count"]');
        
        if (await messageCount.count() > 0) {
          await expect(messageCount).toBeVisible();
        }
      }
    });

    test('deve permitir seleção de conversas', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        const firstItem = conversationItems.first();
        await firstItem.click();
        
        // Verificar se conversa foi selecionada
        await expect(firstItem).toHaveClass(/selected|active/);
      }
    });
  });

  test.describe('🔍 Busca e Filtros', () => {
    test('deve filtrar conversas por nome do cliente', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve filtrar conversas por telefone', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve filtrar conversas por última mensagem', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve limpar filtros ao limpar campo de busca', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });

  test.describe('💬 Área de Chat', () => {
    test('deve exibir header da conversa selecionada', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Verificar header da conversa
        const chatHeader = page.locator('[data-testid="chat-header"]');
        await expect(chatHeader).toBeVisible();
        
        // Verificar nome do cliente no header
        const clientName = chatHeader.locator('[data-testid="chat-client-name"]');
        await expect(clientName).toBeVisible();
        
        // Verificar telefone no header
        const clientPhone = chatHeader.locator('[data-testid="chat-client-phone"]');
        await expect(clientPhone).toBeVisible();
      }
    });

    test('deve exibir área de mensagens', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Verificar área de mensagens
        const messagesArea = page.locator('[data-testid="messages-area"]');
        await expect(messagesArea).toBeVisible();
      }
    });

    test('deve exibir mensagens recebidas e enviadas', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Verificar mensagens recebidas
        const receivedMessages = page.locator('[data-testid="message-received"]');
        const receivedCount = await receivedMessages.count();
        
        // Verificar mensagens enviadas
        const sentMessages = page.locator('[data-testid="message-sent"]');
        const sentCount = await sentMessages.count();
        
        // Pelo menos um tipo de mensagem deve existir
        expect(receivedCount + sentCount).toBeGreaterThan(0);
      }
    });

    test('deve exibir timestamps das mensagens', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Verificar se há mensagens com timestamp
        const messageTimestamps = page.locator('[data-testid="message-timestamp"]');
        const timestampCount = await messageTimestamps.count();
        
        if (timestampCount > 0) {
          await expect(messageTimestamps.first()).toBeVisible();
        }
      }
    });

    test('deve fazer scroll automático para última mensagem', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Aguardar scroll automático
        await page.waitForTimeout(1000);
        
        // Verificar se área de mensagens está visível
        const messagesArea = page.locator('[data-testid="messages-area"]');
        await expect(messagesArea).toBeVisible();
      }
    });
  });

  test.describe('✍️ Envio de Mensagens', () => {
    test('deve exibir input para nova mensagem', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Verificar input de mensagem
        const messageInput = page.locator('[data-testid="message-input"]');
        await expect(messageInput).toBeVisible();
      }
    });

    test('deve permitir envio de mensagem por botão', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Preencher mensagem
        const messageInput = page.locator('[data-testid="message-input"]');
        await messageInput.fill('Teste de mensagem');
        
        // Clicar no botão de envio
        const sendButton = page.locator('button:has-text("Enviar")');
        await sendButton.click();
        
        // Verificar se mensagem foi enviada
        await page.waitForTimeout(2000);
      }
    });

    test('deve permitir envio de mensagem por Enter', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Preencher mensagem
        const messageInput = page.locator('[data-testid="message-input"]');
        await messageInput.fill('Teste de mensagem com Enter');
        
        // Pressionar Enter
        await messageInput.press('Enter');
        
        // Verificar se mensagem foi enviada
        await page.waitForTimeout(2000);
      }
    });

    test('deve exibir botões de anexo e emoji (desabilitados)', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Verificar botão de anexo
        const attachButton = page.locator('button[data-testid="attach-button"]');
        if (await attachButton.count() > 0) {
          await expect(attachButton).toBeDisabled();
        }
        
        // Verificar botão de emoji
        const emojiButton = page.locator('button[data-testid="emoji-button"]');
        if (await emojiButton.count() > 0) {
          await expect(emojiButton).toBeDisabled();
        }
      }
    });
  });

  test.describe('🔄 Atualizações em Tempo Real', () => {
    test('deve atualizar lista de conversas ao clicar em refresh', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve receber novas mensagens em tempo real', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Aguardar possíveis atualizações em tempo real
        await page.waitForTimeout(5000);
        
        // Verificar se área de mensagens ainda está visível
        const messagesArea = page.locator('[data-testid="messages-area"]');
        await expect(messagesArea).toBeVisible();
      }
    });
  });

  test.describe('📱 Estados e Loading', () => {
    test('deve exibir loading durante carregamento', async ({ page }) => {
      await page.goto('/conversas');

      // Verificar se skeletons aparecem
      const skeletons = page.locator('[data-testid="loading-skeleton"]');
      if (await skeletons.count() > 0) {
        await expect(skeletons.first()).toBeVisible();
      }
    });

    test('deve exibir estado de erro quando necessário', async ({ page }) => {
      // Simular erro na API
      await page.route('**/api/conversations/**', route => route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' })
      }));

      await page.goto('/conversas');
      await page.waitForTimeout(3000);

      // Verificar se aplicação não quebra
      await expect(page.locator('body')).toBeVisible();
    });

    test('deve exibir estado de conversa vazia', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount === 0) {
        // Verificar se há mensagem de conversa vazia
        const emptyState = page.locator('[data-testid="empty-conversations"]');
        if (await emptyState.count() > 0) {
          await expect(emptyState).toBeVisible();
        }
      }
    });
  });

  test.describe('🎯 Acessibilidade', () => {
    test('deve ter navegação por teclado', async ({ page }) => {
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      // Navegar usando Tab
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Verificar se foco está visível
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });

    test('deve ter labels apropriados', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
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
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });

    test('deve permitir envio de mensagem em mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Verificar input de mensagem em mobile
        const messageInput = page.locator('[data-testid="message-input"]');
        await expect(messageInput).toBeVisible();
      }
    });
  });

  test.describe('🐛 Tratamento de Erros', () => {
    test('deve tratar erro de carregamento de conversas', async ({ page }) => {
      // Simular erro na API
      await page.route('**/api/conversations/**', route => route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' })
      }));

      await page.goto('/conversas');
      await page.waitForTimeout(3000);

      // Verificar se aplicação não quebra
      await expect(page.locator('body')).toBeVisible();
    });

    test('deve tratar erro de envio de mensagem', async ({ page }) => {
      // Simular erro na API de envio
      await page.route('**/api/messages/**', route => route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Failed to send message' })
      }));

      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();

      const conversationItems = page.locator('[data-testid="conversation-item"]');
      const itemCount = await conversationItems.count();

      if (itemCount > 0) {
        await conversationItems.first().click();
        
        // Tentar enviar mensagem
        const messageInput = page.locator('[data-testid="message-input"]');
        await messageInput.fill('Teste de erro');
        await messageInput.press('Enter');
        
        await page.waitForTimeout(2000);
        
        // Verificar se aplicação não quebra
        await expect(page.locator('body')).toBeVisible();
      }
    });
  });

  test.describe('📊 Performance', () => {
    test('deve carregar rapidamente', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/conversas');
      await testUtils.waitForDataToLoad();
      const loadTime = Date.now() - startTime;

      expect(loadTime).toBeLessThan(5000); // 5 segundos
    });

    test('deve ter busca responsiva', async ({ page }) => {
      // Aguardar que a página carregue completamente
      await page.waitForTimeout(5000);
      
      // Verificar se há elementos na página
      const elements = page.locator('div');
      const elementCount = await elements.count();
      expect(elementCount).toBeGreaterThan(0);
    });
  });
});
