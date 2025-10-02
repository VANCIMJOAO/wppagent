import { test, expect, Page } from '@playwright/test';

/**
 * Testes E2E - WebSocket e Notificações em Tempo Real
 * =================================================
 * 
 * Testa funcionalidades de tempo real:
 * - Conexão WebSocket
 * - Notificações automáticas
 * - Atualizações em tempo real
 * - Reconexão automática
 */

// Configurações de teste
const TEST_CONFIG = {
  baseUrl: 'http://localhost:3000',
  timeout: 30000,
  credentials: {
    username: 'admin',
    password: 'admin123'
  }
};

// Utilitários para WebSocket
class WebSocketTestUtils {
  constructor(private page: Page) {}

  async login() {
    await this.page.goto('/login');
    await this.page.fill('input[id="username"]', TEST_CONFIG.credentials.username);
    await this.page.fill('input[id="password"]', TEST_CONFIG.credentials.password);
    await this.page.click('button[type="submit"]');
    await this.page.waitForURL('/dashboard');
  }

  async waitForWebSocketConnection() {
    // Aguardar conexão WebSocket
    await this.page.waitForFunction(() => {
      return window.navigator.onLine;
    }, { timeout: 10000 });

    // Verificar se WebSocket está conectado
    await this.page.waitForFunction(() => {
      return window.WebSocket && window.WebSocket.OPEN;
    }, { timeout: 10000 });
  }

  async simulateOffline() {
    await this.page.context().setOffline(true);
    await this.page.waitForTimeout(2000);
  }

  async simulateOnline() {
    await this.page.context().setOffline(false);
    await this.page.waitForTimeout(2000);
  }

  async captureWebSocketMessages() {
    const messages: any[] = [];
    
    this.page.on('console', msg => {
      if (msg.text().includes('WebSocket')) {
        messages.push(msg.text());
      }
    });

    return messages;
  }
}

// Testes de WebSocket
test.describe('WebSocket e Tempo Real', () => {
  let utils: WebSocketTestUtils;

  test.beforeEach(async ({ page }) => {
    utils = new WebSocketTestUtils(page);
    await utils.login();
  });

  test('Conexão WebSocket Estabelecida', async ({ page }) => {
    // Navegar para dashboard
    await page.goto('/dashboard');
    
    // Aguardar conexão WebSocket
    await utils.waitForWebSocketConnection();
    
    // Verificar se indicador de conexão está ativo
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/conectado|online/i);
  });

  test('Notificações em Tempo Real - Agendamentos', async ({ page }) => {
    // Navegar para agendamentos
    await page.goto('/agendamentos');
    
    // Aguardar conexão WebSocket
    await utils.waitForWebSocketConnection();
    
    // Capturar mensagens WebSocket
    const messages = await utils.captureWebSocketMessages();
    
    // Criar agendamento
    await page.click('button:has-text("Novo Agendamento")');
    await page.waitForSelector('[role="dialog"]');
    
    // Preencher formulário rapidamente
    await page.selectOption('select[name="user_id"]', { index: 1 });
    await page.selectOption('select[name="service_id"]', { index: 1 });
    await page.click('button:has-text("Selecione a data")');
    await page.click('[data-date]', { timeout: 5000 });
    await page.selectOption('select[name="hora_agendamento"]', { index: 1 });
    await page.click('button:has-text("Criar")');
    
    // Verificar notificação em tempo real
    await expect(page.locator('.toast-success')).toBeVisible({ timeout: 10000 });
    
    // Verificar se dados foram atualizados automaticamente
    await expect(page.locator('[data-testid="appointments-list"]')).toBeVisible();
  });

  test('Notificações em Tempo Real - Clientes', async ({ page }) => {
    // Navegar para clientes
    await page.goto('/clientes');
    
    // Aguardar conexão WebSocket
    await utils.waitForWebSocketConnection();
    
    // Criar cliente
    await page.click('button:has-text("Novo Cliente")');
    await page.waitForSelector('[role="dialog"]');
    
    // Preencher formulário
    await page.fill('input[name="nome"]', 'Cliente WebSocket Test');
    await page.fill('input[name="telefone"]', '11999999999');
    await page.fill('input[name="email"]', 'websocket@test.com');
    await page.click('button:has-text("Criar")');
    
    // Verificar notificação em tempo real
    await expect(page.locator('.toast-success')).toBeVisible({ timeout: 10000 });
    
    // Verificar se dados foram atualizados automaticamente
    await expect(page.locator('text=Cliente WebSocket Test')).toBeVisible();
  });

  test('Reconexão Automática WebSocket', async ({ page }) => {
    // Navegar para dashboard
    await page.goto('/dashboard');
    
    // Aguardar conexão inicial
    await utils.waitForWebSocketConnection();
    
    // Simular perda de conexão
    await utils.simulateOffline();
    
    // Verificar se indicador mostra desconectado
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/desconectado|offline/i);
    
    // Restaurar conexão
    await utils.simulateOnline();
    
    // Aguardar reconexão
    await utils.waitForWebSocketConnection();
    
    // Verificar se indicador mostra conectado novamente
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/conectado|online/i);
  });

  test('Sincronização de Dados em Tempo Real', async ({ page, context }) => {
    // Abrir duas abas
    const page1 = page;
    const page2 = await context.newPage();
    
    // Login em ambas as abas
    await utils.login();
    await page2.goto('/login');
    await page2.fill('input[name="username"]', TEST_CONFIG.credentials.username);
    await page2.fill('input[name="password"]', TEST_CONFIG.credentials.password);
    await page2.click('button[type="submit"]');
    await page2.waitForURL('/dashboard');
    
    // Navegar para agendamentos em ambas as abas
    await page1.goto('/agendamentos');
    await page2.goto('/agendamentos');
    
    // Aguardar conexão WebSocket em ambas
    await utils.waitForWebSocketConnection();
    await page2.waitForFunction(() => window.navigator.onLine, { timeout: 10000 });
    
    // Criar agendamento na primeira aba
    await page1.click('button:has-text("Novo Agendamento")');
    await page1.waitForSelector('[role="dialog"]');
    await page1.selectOption('select[name="user_id"]', { index: 1 });
    await page1.selectOption('select[name="service_id"]', { index: 1 });
    await page1.click('button:has-text("Selecione a data")');
    await page1.click('[data-date]', { timeout: 5000 });
    await page1.selectOption('select[name="hora_agendamento"]', { index: 1 });
    await page1.click('button:has-text("Criar")');
    
    // Verificar se segunda aba foi atualizada automaticamente
    await expect(page2.locator('.toast-success')).toBeVisible({ timeout: 10000 });
    
    // Fechar segunda aba
    await page2.close();
  });

  test('Performance WebSocket - Múltiplas Operações', async ({ page }) => {
    await page.goto('/agendamentos');
    await utils.waitForWebSocketConnection();
    
    const startTime = Date.now();
    
    // Realizar múltiplas operações rapidamente
    for (let i = 0; i < 5; i++) {
      await page.click('button:has-text("Novo Agendamento")');
      await page.waitForSelector('[role="dialog"]');
      await page.selectOption('select[name="user_id"]', { index: 1 });
      await page.selectOption('select[name="service_id"]', { index: 1 });
      await page.click('button:has-text("Selecione a data")');
      await page.click('[data-date]', { timeout: 5000 });
      await page.selectOption('select[name="hora_agendamento"]', { index: 1 });
      await page.click('button:has-text("Criar")');
      await page.waitForSelector('.toast-success', { timeout: 5000 });
    }
    
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    // Verificar se operações foram completadas em tempo razoável
    expect(duration).toBeLessThan(60000); // Menos de 1 minuto
  });

  test('Tratamento de Erros WebSocket', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Interceptar requisições WebSocket e simular erro
    await page.route('**/ws', route => {
      route.abort('failed');
    });
    
    // Aguardar tentativa de conexão
    await page.waitForTimeout(5000);
    
    // Verificar se há indicador de erro
    await expect(page.locator('[data-testid="connection-error"]')).toBeVisible();
    
    // Restaurar rota
    await page.unroute('**/ws');
    
    // Aguardar reconexão
    await utils.waitForWebSocketConnection();
    
    // Verificar se reconectou
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/conectado|online/i);
  });
});

// Testes de edge cases para WebSocket
test.describe('Edge Cases - WebSocket', () => {
  let utils: WebSocketTestUtils;

  test.beforeEach(async ({ page }) => {
    utils = new WebSocketTestUtils(page);
    await utils.login();
  });

  test('Conexão Lenta', async ({ page }) => {
    // Simular conexão lenta
    await page.route('**/ws', route => {
      setTimeout(() => {
        route.continue();
      }, 5000);
    });
    
    await page.goto('/dashboard');
    
    // Aguardar conexão mesmo com latência
    await utils.waitForWebSocketConnection();
    
    // Verificar se funcionou
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/conectado|online/i);
  });

  test('Múltiplas Reconexões', async ({ page }) => {
    await page.goto('/dashboard');
    await utils.waitForWebSocketConnection();
    
    // Simular múltiplas desconexões e reconexões
    for (let i = 0; i < 3; i++) {
      await utils.simulateOffline();
      await page.waitForTimeout(1000);
      await utils.simulateOnline();
      await utils.waitForWebSocketConnection();
    }
    
    // Verificar se ainda funciona
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/conectado|online/i);
  });

  test('Dados Grandes via WebSocket', async ({ page }) => {
    await page.goto('/agendamentos');
    await utils.waitForWebSocketConnection();
    
    // Criar muitos agendamentos para testar transferência de dados grandes
    for (let i = 0; i < 10; i++) {
      await page.click('button:has-text("Novo Agendamento")');
      await page.waitForSelector('[role="dialog"]');
      await page.selectOption('select[name="user_id"]', { index: 1 });
      await page.selectOption('select[name="service_id"]', { index: 1 });
      await page.click('button:has-text("Selecione a data")');
      await page.click('[data-date]', { timeout: 5000 });
      await page.selectOption('select[name="hora_agendamento"]', { index: 1 });
      await page.click('button:has-text("Criar")');
      await page.waitForSelector('.toast-success', { timeout: 5000 });
    }
    
    // Verificar se todos foram criados
    await expect(page.locator('[data-testid="appointments-list"] tr')).toHaveCount(10);
  });
});

// Testes de acessibilidade para WebSocket
test.describe('Acessibilidade - WebSocket', () => {
  test('Indicadores Visuais de Conexão', async ({ page }) => {
    const utils = new WebSocketTestUtils(page);
    await utils.login();
    await page.goto('/dashboard');
    
    // Verificar se há indicadores visuais de conexão
    await expect(page.locator('[data-testid="connection-status"]')).toBeVisible();
    
    // Verificar se indicador tem texto descritivo
    await expect(page.locator('[data-testid="connection-status"]')).toHaveAttribute('aria-label');
    
    // Simular desconexão e verificar mudança visual
    await utils.simulateOffline();
    await expect(page.locator('[data-testid="connection-status"]')).toHaveText(/desconectado|offline/i);
  });

  test('Notificações Acessíveis', async ({ page }) => {
    const utils = new WebSocketTestUtils(page);
    await utils.login();
    await page.goto('/agendamentos');
    await utils.waitForWebSocketConnection();
    
    // Criar agendamento
    await page.click('button:has-text("Novo Agendamento")');
    await page.waitForSelector('[role="dialog"]');
    await page.selectOption('select[name="user_id"]', { index: 1 });
    await page.selectOption('select[name="service_id"]', { index: 1 });
    await page.click('button:has-text("Selecione a data")');
    await page.click('[data-date]', { timeout: 5000 });
    await page.selectOption('select[name="hora_agendamento"]', { index: 1 });
    await page.click('button:has-text("Criar")');
    
    // Verificar se notificação é acessível
    const notification = page.locator('.toast-success');
    await expect(notification).toBeVisible();
    await expect(notification).toHaveAttribute('role', 'alert');
    await expect(notification).toHaveAttribute('aria-live', 'polite');
  });
});
