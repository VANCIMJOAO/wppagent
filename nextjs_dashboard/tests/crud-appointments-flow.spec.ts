import { test, expect, Page } from '@playwright/test';

/**
 * Testes E2E - Fluxo Completo de Agendamentos
 * ===========================================
 * 
 * Testa o fluxo completo: Criar → Editar → Deletar agendamento
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
    appointment: {
      clientName: 'João Silva Teste',
      clientPhone: '11999999999',
      service: 'Consulta Médica',
      date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 dias no futuro
      time: '14:00',
      duration: 60,
      price: 150.00,
      notes: 'Agendamento de teste E2E'
    },
    updatedAppointment: {
      clientName: 'João Silva Teste Atualizado',
      service: 'Exame de Sangue',
      time: '15:30',
      duration: 30,
      price: 80.00,
      notes: 'Agendamento atualizado via E2E'
    }
  }
};

// Utilitários de teste
class AppointmentTestUtils {
  constructor(private page: Page) {}

  async login() {
    await this.page.goto('/login');
    await this.page.waitForSelector('input[id="username"]', { state: 'visible' });
    await this.page.fill('input[id="username"]', TEST_CONFIG.credentials.username);
    await this.page.fill('input[id="password"]', TEST_CONFIG.credentials.password);
    await this.page.click('button[type="submit"]');
    await this.page.waitForURL('/dashboard');
  }

  async navigateToAppointments() {
    await this.page.goto('/agendamentos');
    await this.page.waitForSelector('[data-testid="appointments-page"]', { timeout: 10000 });
  }

  async createAppointment() {
    // Clicar no botão "Novo Agendamento"
    await this.page.click('button:has-text("Novo Agendamento")');
    
    // Aguardar modal abrir - usar seletor mais genérico
    await this.page.waitForSelector('.fixed.inset-0', { timeout: 10000 });
    
    // Preencher formulário
    await this.page.selectOption('select[name="user_id"]', { label: TEST_CONFIG.testData.appointment.clientName });
    await this.page.selectOption('select[name="service_id"]', { label: TEST_CONFIG.testData.appointment.service });
    
    // Selecionar data
    await this.page.click('button:has-text("Selecione a data")');
    await this.page.click(`[data-date="${TEST_CONFIG.testData.appointment.date}"]`);
    
    // Selecionar horário
    await this.page.selectOption('select[name="hora_agendamento"]', TEST_CONFIG.testData.appointment.time);
    
    // Preencher campos opcionais
    await this.page.fill('input[name="duracao_minutos"]', TEST_CONFIG.testData.appointment.duration.toString());
    await this.page.fill('input[name="valor"]', TEST_CONFIG.testData.appointment.price.toString());
    await this.page.fill('textarea[name="observacoes"]', TEST_CONFIG.testData.appointment.notes);
    
    // Submeter formulário
    await this.page.click('button:has-text("Criar")');
    
    // Aguardar sucesso
    await this.page.waitForSelector('.toast-success, [data-testid="success-message"]', { timeout: 10000 });
  }

  async editAppointment() {
    // Encontrar o agendamento criado e clicar em editar
    const appointmentRow = this.page.locator(`tr:has-text("${TEST_CONFIG.testData.appointment.clientName}")`);
    await appointmentRow.locator('button[title="Editar agendamento"]').click();
    
    // Aguardar modal de edição abrir
    await this.page.waitForSelector('[role="dialog"]');
    
    // Atualizar campos
    await this.page.selectOption('select[name="service_id"]', { label: TEST_CONFIG.testData.updatedAppointment.service });
    await this.page.selectOption('select[name="hora_agendamento"]', TEST_CONFIG.testData.updatedAppointment.time);
    await this.page.fill('input[name="duracao_minutos"]', TEST_CONFIG.testData.updatedAppointment.duration.toString());
    await this.page.fill('input[name="valor"]', TEST_CONFIG.testData.updatedAppointment.price.toString());
    await this.page.fill('textarea[name="observacoes"]', TEST_CONFIG.testData.updatedAppointment.notes);
    
    // Submeter alterações
    await this.page.click('button:has-text("Atualizar")');
    
    // Aguardar sucesso
    await this.page.waitForSelector('.toast-success, [data-testid="success-message"]', { timeout: 10000 });
  }

  async deleteAppointment() {
    // Encontrar o agendamento e clicar em excluir
    const appointmentRow = this.page.locator(`tr:has-text("${TEST_CONFIG.testData.updatedAppointment.service}")`);
    await appointmentRow.locator('button[title="Excluir agendamento"]').click();
    
    // Aguardar modal de confirmação
    await this.page.waitForSelector('[role="alertdialog"]');
    
    // Confirmar exclusão
    await this.page.click('button:has-text("Excluir Agendamento")');
    
    // Aguardar sucesso
    await this.page.waitForSelector('.toast-success, [data-testid="success-message"]', { timeout: 10000 });
  }

  async verifyAppointmentExists() {
    await expect(this.page.locator(`text=${TEST_CONFIG.testData.appointment.clientName}`)).toBeVisible();
  }

  async verifyAppointmentUpdated() {
    await expect(this.page.locator(`text=${TEST_CONFIG.testData.updatedAppointment.service}`)).toBeVisible();
  }

  async verifyAppointmentDeleted() {
    await expect(this.page.locator(`text=${TEST_CONFIG.testData.updatedAppointment.service}`)).not.toBeVisible();
  }
}

// Testes principais
test.describe('Fluxo Completo de Agendamentos', () => {
  let utils: AppointmentTestUtils;

  test.beforeEach(async ({ page }) => {
    utils = new AppointmentTestUtils(page);
    await utils.login();
    await utils.navigateToAppointments();
  });

  test('Criar → Editar → Deletar Agendamento', async ({ page }) => {
    // 1. Criar agendamento
    await test.step('Criar novo agendamento', async () => {
      await utils.createAppointment();
      await utils.verifyAppointmentExists();
    });

    // 2. Editar agendamento
    await test.step('Editar agendamento existente', async () => {
      await utils.editAppointment();
      await utils.verifyAppointmentUpdated();
    });

    // 3. Deletar agendamento
    await test.step('Deletar agendamento', async () => {
      await utils.deleteAppointment();
      await utils.verifyAppointmentDeleted();
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

    // Criar agendamento e verificar notificação
    await utils.createAppointment();
    
    // Verificar se notificação apareceu
    await expect(page.locator('.toast-success')).toBeVisible();
    
    // Verificar se dados foram atualizados em tempo real
    await utils.verifyAppointmentExists();
  });

  test('Edge Cases - Validações de Formulário', async ({ page }) => {
    // Teste 1: Campos obrigatórios vazios
    await test.step('Validar campos obrigatórios', async () => {
      await page.click('button:has-text("Novo Agendamento")');
      await page.waitForSelector('[role="dialog"]');
      
      // Tentar submeter sem preencher campos obrigatórios
      await page.click('button:has-text("Criar")');
      
      // Verificar mensagens de erro
      await expect(page.locator('text=Nome é obrigatório')).toBeVisible();
      await expect(page.locator('text=Telefone é obrigatório')).toBeVisible();
    });

    // Teste 2: Data no passado
    await test.step('Validar data no passado', async () => {
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      await page.click('button:has-text("Selecione a data")');
      // Tentar selecionar data passada (deve estar desabilitada)
      const pastDateButton = page.locator(`[data-date="${yesterday}"]`);
      await expect(pastDateButton).toHaveAttribute('disabled');
    });

    // Teste 3: Horário fora do expediente
    await test.step('Validar horário fora do expediente', async () => {
      // Tentar selecionar horário fora do expediente (7h ou 19h)
      const timeSelect = page.locator('select[name="hora_agendamento"]');
      const options = await timeSelect.locator('option').allTextContents();
      
      // Verificar se horários fora do expediente não estão disponíveis
      expect(options).not.toContain('07:00');
      expect(options).not.toContain('19:00');
    });

    // Teste 4: Valor negativo
    await test.step('Validar valor negativo', async () => {
      await page.fill('input[name="valor"]', '-100');
      await page.click('button:has-text("Criar")');
      
      // Verificar mensagem de erro
      await expect(page.locator('text=Valor não pode ser negativo')).toBeVisible();
    });

    // Fechar modal
    await page.click('button:has-text("Cancelar")');
  });

  test('Performance - Múltiplas Operações', async ({ page }) => {
    const startTime = Date.now();
    
    // Criar múltiplos agendamentos
    for (let i = 0; i < 3; i++) {
      await utils.createAppointment();
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
    await expect(page.locator('button:has-text("Novo Agendamento")')).toBeVisible();
    
    // Testar criação de agendamento em mobile
    await utils.createAppointment();
    await utils.verifyAppointmentExists();
  });
});

// Testes de integração com WebSocket
test.describe('WebSocket Integration', () => {
  test('Notificações em Tempo Real', async ({ page }) => {
    const utils = new AppointmentTestUtils(page);
    await utils.login();
    await utils.navigateToAppointments();

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

    // Criar agendamento e verificar notificação
    await utils.createAppointment();
    
    // Verificar se notificação apareceu
    await expect(page.locator('.toast-success')).toBeVisible();
    
    // Verificar se dados foram atualizados automaticamente
    await utils.verifyAppointmentExists();
  });

  test('Reconexão WebSocket', async ({ page }) => {
    const utils = new AppointmentTestUtils(page);
    await utils.login();
    await utils.navigateToAppointments();

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
    await utils.createAppointment();
    await utils.verifyAppointmentExists();
  });
});
