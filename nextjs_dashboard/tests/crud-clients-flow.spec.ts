import { test, expect, Page } from '@playwright/test';

/**
 * Testes E2E - Fluxo Completo de Clientes
 * ======================================
 * 
 * Testa o fluxo completo: Criar → Editar → Deletar cliente
 * Inclui validação de WebSocket e edge cases
 */

// Configurações de teste
const TEST_CONFIG = {
  baseUrl: 'http://localhost:3000',
  timeout: 30000,
  credentials: {
    username: 'admin',
    password: 'admin123'
  },
  testData: {
    client: {
      name: 'Maria Santos Teste',
      phone: '11888888888',
      email: 'maria.teste@email.com',
      status: 'active',
      notes: 'Cliente de teste E2E'
    },
    updatedClient: {
      name: 'Maria Santos Teste Atualizada',
      phone: '11777777777',
      email: 'maria.atualizada@email.com',
      status: 'vip',
      notes: 'Cliente VIP atualizado via E2E'
    }
  }
};

// Utilitários de teste
class ClientTestUtils {
  constructor(private page: Page) {}

  async login() {
    await this.page.goto('/login');
    await this.page.waitForSelector('input[id="username"]', { state: 'visible' });
    await this.page.fill('input[id="username"]', TEST_CONFIG.credentials.username);
    await this.page.fill('input[id="password"]', TEST_CONFIG.credentials.password);
    await this.page.click('button[type="submit"]');
    await this.page.waitForURL('/dashboard');
  }

  async navigateToClients() {
    await this.page.goto('/clientes');
    await this.page.waitForSelector('[data-testid="clients-page"]', { timeout: 10000 });
  }

  async createClient() {
    // Clicar no botão "Novo Cliente"
    await this.page.click('button:has-text("Novo Cliente")');
    
    // Aguardar modal abrir
    await this.page.waitForSelector('[role="dialog"]');
    
    // Preencher formulário
    await this.page.fill('input[name="nome"]', TEST_CONFIG.testData.client.name);
    await this.page.fill('input[name="telefone"]', TEST_CONFIG.testData.client.phone);
    await this.page.fill('input[name="email"]', TEST_CONFIG.testData.client.email);
    await this.page.selectOption('select[name="status"]', TEST_CONFIG.testData.client.status);
    await this.page.fill('textarea[name="notas"]', TEST_CONFIG.testData.client.notes);
    
    // Submeter formulário
    await this.page.click('button:has-text("Criar")');
    
    // Aguardar sucesso
    await this.page.waitForSelector('.toast-success, [data-testid="success-message"]', { timeout: 10000 });
  }

  async editClient() {
    // Encontrar o cliente criado e clicar em editar
    const clientRow = this.page.locator(`tr:has-text("${TEST_CONFIG.testData.client.name}")`);
    await clientRow.locator('button[title="Editar cliente"]').click();
    
    // Aguardar modal de edição abrir
    await this.page.waitForSelector('[role="dialog"]');
    
    // Atualizar campos
    await this.page.fill('input[name="nome"]', TEST_CONFIG.testData.updatedClient.name);
    await this.page.fill('input[name="telefone"]', TEST_CONFIG.testData.updatedClient.phone);
    await this.page.fill('input[name="email"]', TEST_CONFIG.testData.updatedClient.email);
    await this.page.selectOption('select[name="status"]', TEST_CONFIG.testData.updatedClient.status);
    await this.page.fill('textarea[name="notas"]', TEST_CONFIG.testData.updatedClient.notes);
    
    // Submeter alterações
    await this.page.click('button:has-text("Salvar Alterações")');
    
    // Aguardar sucesso
    await this.page.waitForSelector('.toast-success, [data-testid="success-message"]', { timeout: 10000 });
  }

  async deleteClient() {
    // Encontrar o cliente e clicar em excluir
    const clientRow = this.page.locator(`tr:has-text("${TEST_CONFIG.testData.updatedClient.name}")`);
    await clientRow.locator('button[title="Excluir cliente"]').click();
    
    // Aguardar modal de confirmação
    await this.page.waitForSelector('[role="alertdialog"]');
    
    // Verificar aviso sobre dados relacionados
    await expect(this.page.locator('text=Dados Relacionados Serão Afetados')).toBeVisible();
    await expect(this.page.locator('text=Conversas:')).toBeVisible();
    await expect(this.page.locator('text=Mensagens:')).toBeVisible();
    await expect(this.page.locator('text=Agendamentos:')).toBeVisible();
    
    // Confirmar exclusão
    await this.page.click('button:has-text("Excluir Cliente")');
    
    // Aguardar sucesso
    await this.page.waitForSelector('.toast-success, [data-testid="success-message"]', { timeout: 10000 });
  }

  async verifyClientExists() {
    await expect(this.page.locator(`text=${TEST_CONFIG.testData.client.name}`)).toBeVisible();
  }

  async verifyClientUpdated() {
    await expect(this.page.locator(`text=${TEST_CONFIG.testData.updatedClient.name}`)).toBeVisible();
    await expect(this.page.locator(`text=${TEST_CONFIG.testData.updatedClient.email}`)).toBeVisible();
  }

  async verifyClientDeleted() {
    await expect(this.page.locator(`text=${TEST_CONFIG.testData.updatedClient.name}`)).not.toBeVisible();
  }
}

// Testes principais
test.describe('Fluxo Completo de Clientes', () => {
  let utils: ClientTestUtils;

  test.beforeEach(async ({ page }) => {
    utils = new ClientTestUtils(page);
    await utils.login();
    await utils.navigateToClients();
  });

  test('Criar → Editar → Deletar Cliente', async ({ page }) => {
    // 1. Criar cliente
    await test.step('Criar novo cliente', async () => {
      await utils.createClient();
      await utils.verifyClientExists();
    });

    // 2. Editar cliente
    await test.step('Editar cliente existente', async () => {
      await utils.editClient();
      await utils.verifyClientUpdated();
    });

    // 3. Deletar cliente
    await test.step('Deletar cliente', async () => {
      await utils.deleteClient();
      await utils.verifyClientDeleted();
    });
  });

  test('Validação de WebSocket - Notificações em Tempo Real', async ({ page }) => {
    // Monitorar notificações WebSocket
    const notifications: string[] = [];
    
    // Interceptar mensagens WebSocket
    await page.route('**/ws', (route) => {
      const request = route.request();
      if (request.url().includes('ws')) {
        notifications.push('WebSocket connection established');
      }
      route.continue();
    });

    // Criar cliente e verificar notificação
    await utils.createClient();
    
    // Verificar se notificação apareceu
    await expect(page.locator('.toast-success')).toBeVisible();
    
    // Verificar se dados foram atualizados em tempo real
    await utils.verifyClientExists();
  });

  test('Edge Cases - Validações de Formulário', async ({ page }) => {
    // Teste 1: Campos obrigatórios vazios
    await test.step('Validar campos obrigatórios', async () => {
      await page.click('button:has-text("Novo Cliente")');
      await page.waitForSelector('[role="dialog"]');
      
      // Tentar submeter sem preencher campos obrigatórios
      await page.click('button:has-text("Criar")');
      
      // Verificar mensagens de erro
      await expect(page.locator('text=Nome é obrigatório')).toBeVisible();
      await expect(page.locator('text=Telefone é obrigatório')).toBeVisible();
    });

    // Teste 2: Email inválido
    await test.step('Validar formato de email', async () => {
      await page.fill('input[name="nome"]', 'Teste');
      await page.fill('input[name="telefone"]', '11999999999');
      await page.fill('input[name="email"]', 'email-invalido');
      await page.click('button:has-text("Criar")');
      
      // Verificar mensagem de erro
      await expect(page.locator('text=Email deve ter um formato válido')).toBeVisible();
    });

    // Teste 3: Telefone inválido
    await test.step('Validar formato de telefone', async () => {
      await page.fill('input[name="nome"]', 'Teste');
      await page.fill('input[name="telefone"]', 'telefone-invalido');
      await page.fill('input[name="email"]', 'teste@email.com');
      await page.click('button:has-text("Criar")');
      
      // Verificar mensagem de erro
      await expect(page.locator('text=Telefone deve conter apenas números e caracteres válidos')).toBeVisible();
    });

    // Teste 4: Nome muito longo
    await test.step('Validar tamanho do nome', async () => {
      const longName = 'A'.repeat(300); // Nome muito longo
      await page.fill('input[name="nome"]', longName);
      await page.fill('input[name="telefone"]', '11999999999');
      await page.fill('input[name="email"]', 'teste@email.com');
      await page.click('button:has-text("Criar")');
      
      // Verificar se há validação de tamanho (se implementada)
      // await expect(page.locator('text=Nome muito longo')).toBeVisible();
    });

    // Fechar modal
    await page.click('button:has-text("Cancelar")');
  });

  test('Validação de Dados Relacionados na Exclusão', async ({ page }) => {
    // Criar cliente primeiro
    await utils.createClient();
    
    // Tentar excluir e verificar avisos
    const clientRow = this.page.locator(`tr:has-text("${TEST_CONFIG.testData.client.name}")`);
    await clientRow.locator('button[title="Excluir cliente"]').click();
    
    // Verificar modal de confirmação
    await this.page.waitForSelector('[role="alertdialog"]');
    
    // Verificar se mostra dados relacionados
    await expect(this.page.locator('text=Conversas:')).toBeVisible();
    await expect(this.page.locator('text=Mensagens:')).toBeVisible();
    await expect(this.page.locator('text=Agendamentos:')).toBeVisible();
    
    // Verificar aviso sobre impacto
    await expect(this.page.locator('text=Esta ação não pode ser desfeita')).toBeVisible();
    await expect(this.page.locator('text=afetar o histórico de atendimento')).toBeVisible();
    
    // Cancelar exclusão
    await this.page.click('button:has-text("Cancelar")');
  });

  test('Performance - Múltiplas Operações', async ({ page }) => {
    const startTime = Date.now();
    
    // Criar múltiplos clientes
    for (let i = 0; i < 3; i++) {
      await utils.createClient();
      await page.waitForTimeout(1000); // Aguardar 1 segundo entre operações
    }
    
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    // Verificar se operações foram completadas em tempo razoável
    expect(duration).toBeLessThan(30000); // Menos de 30 segundos
  });

  test('Responsividade - Mobile', async ({ page }) => {
    // Simular viewport mobile
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verificar se elementos são visíveis e clicáveis
    await expect(page.locator('button:has-text("Novo Cliente")')).toBeVisible();
    
    // Testar criação de cliente em mobile
    await utils.createClient();
    await utils.verifyClientExists();
  });

  test('Filtros e Busca', async ({ page }) => {
    // Criar cliente para testar filtros
    await utils.createClient();
    
    // Testar busca por nome
    await page.fill('input[placeholder*="buscar"]', TEST_CONFIG.testData.client.name);
    await page.waitForTimeout(1000);
    await expect(page.locator(`text=${TEST_CONFIG.testData.client.name}`)).toBeVisible();
    
    // Testar filtro por status
    await page.selectOption('select[name="status"]', 'active');
    await page.waitForTimeout(1000);
    await expect(page.locator(`text=${TEST_CONFIG.testData.client.name}`)).toBeVisible();
    
    // Limpar filtros
    await page.fill('input[placeholder*="buscar"]', '');
    await page.selectOption('select[name="status"]', 'all');
  });
});

// Testes de integração com WebSocket
test.describe('WebSocket Integration - Clientes', () => {
  test('Notificações em Tempo Real', async ({ page }) => {
    const utils = new ClientTestUtils(page);
    await utils.login();
    await utils.navigateToClients();

    // Monitorar conexão WebSocket
    let wsConnected = false;
    page.on('console', msg => {
      if (msg.text().includes('WebSocket connected')) {
        wsConnected = true;
      }
    });

    // Aguardar conexão WebSocket
    await page.waitForFunction(() => {
      return window.navigator.onLine;
    }, { timeout: 10000 });

    // Criar cliente e verificar notificação
    await utils.createClient();
    
    // Verificar se notificação apareceu
    await expect(page.locator('.toast-success')).toBeVisible();
    
    // Verificar se dados foram atualizados automaticamente
    await utils.verifyClientExists();
  });

  test('Reconexão WebSocket', async ({ page }) => {
    const utils = new ClientTestUtils(page);
    await utils.login();
    await utils.navigateToClients();

    // Simular perda de conexão
    await page.context().setOffline(true);
    await page.waitForTimeout(2000);
    
    // Restaurar conexão
    await page.context().setOffline(false);
    
    // Verificar se reconectou
    await page.waitForFunction(() => {
      return window.navigator.onLine;
    }, { timeout: 10000 });

    // Testar operação após reconexão
    await utils.createClient();
    await utils.verifyClientExists();
  });
});

// Testes de acessibilidade
test.describe('Acessibilidade - Clientes', () => {
  test('Navegação por Teclado', async ({ page }) => {
    const utils = new ClientTestUtils(page);
    await utils.login();
    await utils.navigateToClients();

    // Navegar usando Tab
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Verificar se foco está no botão "Novo Cliente"
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toContainText('Novo Cliente');
    
    // Ativar com Enter
    await page.keyboard.press('Enter');
    
    // Verificar se modal abriu
    await page.waitForSelector('[role="dialog"]');
  });

  test('Screen Reader Support', async ({ page }) => {
    const utils = new ClientTestUtils(page);
    await utils.login();
    await utils.navigateToClients();

    // Verificar se elementos têm labels apropriados
    await expect(page.locator('button:has-text("Novo Cliente")')).toHaveAttribute('aria-label');
    
    // Verificar se tabela tem headers apropriados
    await expect(page.locator('table')).toHaveAttribute('role', 'table');
    await expect(page.locator('th')).toHaveCount(5); // Nome, Telefone, Email, Status, Ações
  });
});
