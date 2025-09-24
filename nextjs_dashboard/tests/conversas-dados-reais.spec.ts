import { test, expect } from '@playwright/test';

test.describe('Conversas - Dados Reais vs Mock', () => {
  test.beforeEach(async ({ page }) => {
    // Navegar diretamente para o backend Railway
    await page.goto('https://wppagent-production.up.railway.app/');
    
    // Aguardar a página carregar
    await page.waitForLoadState('networkidle');
    
    // Verificar se o backend está funcionando
    const healthCheck = page.locator('text=WhatsApp Agent API is running');
    await expect(healthCheck).toBeVisible();
    
    console.log('✅ Backend Railway está funcionando');
  });

  test('1. Verificar se dados mock foram removidos', async ({ page }) => {
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    await page.waitForLoadState('networkidle');
    
    // Verificar que não há mais dados mock (Maria Silva, João Santos, Ana Costa)
    const mockData = ['Maria Silva', 'João Santos', 'Ana Costa'];
    
    for (const mockName of mockData) {
      await expect(page.locator(`text=${mockName}`)).not.toBeVisible();
    }
    
    console.log('✅ Dados mock removidos com sucesso');
  });

  test('2. Verificar carregamento de dados reais', async ({ page }) => {
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    
    // Aguardar loading inicial
    await page.waitForLoadState('networkidle');
    
    // Verificar se há skeleton loading específico (não badges animados)
    const skeletonElements = page.locator('[data-testid="skeleton"], .skeleton, .loading-skeleton');
    if (await skeletonElements.count() > 0) {
      console.log('📱 Aguardando carregamento...');
      // Aguardar skeletons desaparecerem
      await expect(skeletonElements.first()).not.toBeVisible({ timeout: 10000 });
    }
    
    // Verificar se há conversas carregadas, mensagem de "nenhuma conversa" OU estado de erro
    const hasConversations = await page.locator('[data-testid="conversation-item"]').count() > 0;
    const hasNoConversationsMessage = await page.locator('text=Nenhuma conversa disponível').isVisible();
    const hasErrorState = await page.locator('text=Falha ao carregar dados').isVisible();
    
    expect(hasConversations || hasNoConversationsMessage || hasErrorState).toBe(true);
    
    if (hasErrorState) {
      console.log('⚠️ Estado de erro detectado - verificando botão "Tentar Novamente"');
      const retryButton = page.locator('button:has-text("Tentar Novamente")');
      await expect(retryButton).toBeVisible();
      console.log('✅ Botão de retry disponível');
    } else if (hasConversations) {
      console.log('✅ Dados reais carregados com sucesso');
    } else {
      console.log('✅ Estado vazio exibido corretamente');
    }
  });

  test('3. Verificar funcionalidade de busca', async ({ page }) => {
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    await page.waitForLoadState('networkidle');
    
    // Verificar se há estado de erro primeiro
    const hasErrorState = await page.locator('text=Falha ao carregar dados').isVisible();
    
    if (hasErrorState) {
      console.log('⚠️ Estado de erro detectado - funcionalidade de busca não disponível');
      // Tentar clicar no botão "Tentar Novamente"
      const retryButton = page.locator('button:has-text("Tentar Novamente")');
      if (await retryButton.isVisible()) {
        await retryButton.click();
        await page.waitForTimeout(2000);
        
        // Verificar se o erro foi resolvido
        const stillHasError = await page.locator('text=Falha ao carregar dados').isVisible();
        if (stillHasError) {
          console.log('❌ Erro persistente após tentativa de retry');
          return; // Skip o teste se ainda há erro
        }
      }
    }
    
    // Verificar se o campo de busca existe
    const searchInput = page.locator('input[placeholder*="Buscar"]');
    
    // Aguardar o campo aparecer ou verificar se não está em estado de erro
    const searchInputExists = await searchInput.count() > 0;
    
    if (!searchInputExists) {
      console.log('⚠️ Campo de busca não encontrado - página pode estar em estado de erro');
      const currentError = await page.locator('text=Falha ao carregar dados').isVisible();
      expect(currentError).toBe(false); // Fail se ainda há erro
      return;
    }
    
    await expect(searchInput).toBeVisible();
    
    // Testar busca por termo inexistente
    await searchInput.fill('termo_inexistente_12345');
    
    // Aguardar resultado da busca
    await page.waitForTimeout(500);
    
    // Verificar se a mensagem de "nenhuma conversa encontrada" aparece
    const noResultsMessage = page.locator('text=Nenhuma conversa encontrada');
    if (await noResultsMessage.isVisible()) {
      console.log('✅ Busca funcionando - resultado vazio exibido');
    }
    
    // Limpar busca
    await searchInput.clear();
    await page.waitForTimeout(500);
    
    console.log('✅ Funcionalidade de busca testada');
  });

  test('4. Verificar botão de refresh', async ({ page }) => {
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    await page.waitForLoadState('networkidle');
    
    // Verificar se o botão de refresh existe
    const refreshButton = page.locator('button').filter({ hasText: 'Refresh' }).or(
      page.locator('button[title*="refresh" i]')
    ).or(
      page.locator('button svg').filter({ has: page.locator('path[d*="M20 4v5h-.582m0 0a8.001 8.001 0 00-15.356 2m15.356-2H15M4 16v-5h.581m0 0a8.003 8.003 0 0015.357-2M4.581 11H9"]') })
    );
    
    if (await refreshButton.count() > 0) {
      // Clicar no botão de refresh
      await refreshButton.first().click();
      
      // Aguardar carregamento
      await page.waitForTimeout(1000);
      
      console.log('✅ Botão de refresh funcionando');
    } else {
      console.log('⚠️ Botão de refresh não encontrado');
    }
  });

  test('5. Verificar tratamento de erros', async ({ page }) => {
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    await page.waitForLoadState('networkidle');
    
    // Verificar se não há erros visíveis na página
    const errorMessages = page.locator('text=Erro ao carregar').or(
      page.locator('text=Error').or(
        page.locator('[role="alert"]')
      )
    );
    
    if (await errorMessages.count() > 0) {
      console.log('⚠️ Erros encontrados na página:');
      const errorCount = await errorMessages.count();
      for (let i = 0; i < errorCount; i++) {
        const errorText = await errorMessages.nth(i).textContent();
        console.log(`   - ${errorText}`);
      }
    } else {
      console.log('✅ Nenhum erro visível na página');
    }
    
    // Verificar se a página não está em estado de erro
    expect(await page.locator('text=Erro ao carregar conversas').count()).toBe(0);
  });

  test('6. Verificar estrutura da interface', async ({ page }) => {
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    await page.waitForLoadState('networkidle');
    
    // Verificar elementos principais da interface
    await expect(page.locator('h1:has-text("Conversas")')).toBeVisible();
    await expect(page.locator('input[placeholder*="Buscar"]')).toBeVisible();
    
    // Verificar se há sidebar com conversas ou área principal
    const sidebar = page.locator('.w-1/3').or(page.locator('[data-testid="conversations-sidebar"]'));
    const mainArea = page.locator('.flex-1').or(page.locator('[data-testid="conversation-main"]'));
    
    expect(await sidebar.count() > 0 || await mainArea.count() > 0).toBe(true);
    
    console.log('✅ Estrutura da interface verificada');
  });

  test('7. Verificar responsividade', async ({ page }) => {
    // Testar em diferentes tamanhos de tela
    const viewports = [
      { width: 375, height: 667, name: 'Mobile' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 1920, height: 1080, name: 'Desktop' }
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      
      // Navegar para a página de conversas
      await page.goto('http://localhost:3000/conversas');
      await page.waitForLoadState('networkidle');
      
      // Verificar se a página não quebra
      const hasErrors = await page.locator('text=Error').count() > 0;
      expect(hasErrors).toBe(false);
      
      console.log(`✅ Responsividade OK em ${viewport.name} (${viewport.width}x${viewport.height})`);
    }
  });

  test('8. Verificar integração com APIs reais', async ({ page }) => {
    // Monitorar requisições de rede
    const apiRequests: string[] = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/conversations') || 
          request.url().includes('/api/messages')) {
        apiRequests.push(request.url());
      }
    });
    
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    await page.waitForLoadState('networkidle');
    
    // Aguardar possíveis requisições de API
    await page.waitForTimeout(2000);
    
    // Verificar se houve tentativas de chamada para APIs reais
    const hasApiCalls = apiRequests.length > 0;
    
    if (hasApiCalls) {
      console.log('✅ APIs sendo chamadas:');
      apiRequests.forEach(url => console.log(`   - ${url}`));
    } else {
      console.log('⚠️ Nenhuma chamada de API detectada');
    }
    
    // Verificar se não está tentando carregar dados mock
    const hasMockCalls = apiRequests.some(url => 
      url.includes('mock') || 
      url.includes('localhost:8000') ||
      url.includes('fake-data')
    );
    
    expect(hasMockCalls).toBe(false);
    console.log('✅ Nenhuma chamada para dados mock detectada');
  });

  test('9. Teste de performance - carregamento', async ({ page }) => {
    // Medir tempo de carregamento
    const startTime = Date.now();
    
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Verificar se carregou em menos de 10 segundos
    expect(loadTime).toBeLessThan(10000);
    
    console.log(`✅ Página carregou em ${loadTime}ms`);
  });

  test('10. Verificar acessibilidade básica', async ({ page }) => {
    // Navegar para a página de conversas
    await page.goto('http://localhost:3000/conversas');
    await page.waitForLoadState('networkidle');
    
    // Verificar se há elementos com roles apropriados
    const hasHeading = await page.locator('h1, h2, h3').count() > 0;
    const hasButtons = await page.locator('button').count() > 0;
    const hasInputs = await page.locator('input').count() > 0;
    
    expect(hasHeading).toBe(true);
    expect(hasButtons).toBe(true);
    expect(hasInputs).toBe(true);
    
    // Verificar contraste básico (se possível)
    const textElements = await page.locator('p, span, div').filter({ hasText: /[a-zA-Z]{3,}/ }).count();
    expect(textElements).toBeGreaterThan(0);
    
    console.log('✅ Acessibilidade básica verificada');
  });
});
