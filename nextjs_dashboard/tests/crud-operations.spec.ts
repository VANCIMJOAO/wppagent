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

test.describe('CRUD Operations - Testes Completos', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('CRUD de Agendamentos', async ({ page }) => {
    await page.goto('/agendamentos');
    
    // CREATE - Criar novo agendamento
    await page.click('button:has-text("Novo Agendamento")');
    await page.waitForSelector('[data-testid="appointment-form"]');
    
    await page.fill('input[name="clientName"]', 'João Silva');
    await page.fill('input[name="clientPhone"]', '11999999999');
    await page.selectOption('select[name="service"]', 'Limpeza de Pele');
    await page.fill('input[name="date"]', '2024-12-25');
    await page.fill('input[name="time"]', '14:00');
    await page.selectOption('select[name="status"]', 'agendado');
    
    await page.click('button:has-text("Salvar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // READ - Verificar se foi criado
    await expect(page.locator('text=João Silva')).toBeVisible();
    await expect(page.locator('text=Limpeza de Pele')).toBeVisible();
    
    // UPDATE - Editar agendamento
    await page.click('button[data-testid="edit-appointment"]');
    await page.waitForSelector('[data-testid="appointment-form"]');
    
    await page.fill('input[name="clientName"]', 'João Silva Santos');
    await page.selectOption('select[name="status"]', 'confirmado');
    
    await page.click('button:has-text("Atualizar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi atualizado
    await expect(page.locator('text=João Silva Santos')).toBeVisible();
    await expect(page.locator('text=Confirmado')).toBeVisible();
    
    // DELETE - Excluir agendamento
    await page.click('button[data-testid="delete-appointment"]');
    await page.click('button:has-text("Confirmar Exclusão")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi excluído
    await expect(page.locator('text=João Silva Santos')).not.toBeVisible();
  });

  test('CRUD de Clientes', async ({ page }) => {
    await page.goto('/clientes');
    
    // CREATE - Criar novo cliente
    await page.click('button:has-text("Novo Cliente")');
    await page.waitForSelector('[data-testid="client-form"]');
    
    await page.fill('input[name="name"]', 'Maria Santos');
    await page.fill('input[name="phone"]', '11888888888');
    await page.fill('input[name="email"]', 'maria@email.com');
    await page.fill('textarea[name="address"]', 'Rua das Flores, 123');
    await page.selectOption('select[name="status"]', 'ativo');
    
    await page.click('button:has-text("Salvar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // READ - Verificar se foi criado
    await expect(page.locator('text=Maria Santos')).toBeVisible();
    await expect(page.locator('text=maria@email.com')).toBeVisible();
    
    // UPDATE - Editar cliente
    await page.click('button[data-testid="edit-client"]');
    await page.waitForSelector('[data-testid="client-form"]');
    
    await page.fill('input[name="name"]', 'Maria Santos Silva');
    await page.selectOption('select[name="status"]', 'vip');
    
    await page.click('button:has-text("Atualizar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi atualizado
    await expect(page.locator('text=Maria Santos Silva')).toBeVisible();
    await expect(page.locator('text=VIP')).toBeVisible();
    
    // DELETE - Excluir cliente
    await page.click('button[data-testid="delete-client"]');
    await page.click('button:has-text("Confirmar Exclusão")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi excluído
    await expect(page.locator('text=Maria Santos Silva')).not.toBeVisible();
  });

  test('CRUD de Horários Bloqueados', async ({ page }) => {
    await page.goto('/bloqueados');
    
    // CREATE - Criar novo bloqueio
    await page.click('button:has-text("Novo Bloqueio")');
    await page.waitForSelector('[data-testid="block-form"]');
    
    await page.fill('input[name="startDate"]', '2024-12-25');
    await page.fill('input[name="endDate"]', '2024-12-25');
    await page.fill('input[name="startTime"]', '09:00');
    await page.fill('input[name="endTime"]', '12:00');
    await page.selectOption('select[name="type"]', 'recorrente');
    await page.fill('textarea[name="reason"]', 'Feriado de Natal');
    
    await page.click('button:has-text("Salvar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // READ - Verificar se foi criado
    await expect(page.locator('text=Feriado de Natal')).toBeVisible();
    await expect(page.locator('text=Recorrente')).toBeVisible();
    
    // UPDATE - Editar bloqueio
    await page.click('button[data-testid="edit-block"]');
    await page.waitForSelector('[data-testid="block-form"]');
    
    await page.fill('textarea[name="reason"]', 'Feriado de Natal - Atualizado');
    await page.selectOption('select[name="type"]', 'único');
    
    await page.click('button:has-text("Atualizar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi atualizado
    await expect(page.locator('text=Feriado de Natal - Atualizado')).toBeVisible();
    await expect(page.locator('text=Único')).toBeVisible();
    
    // DELETE - Excluir bloqueio
    await page.click('button[data-testid="delete-block"]');
    await page.click('button:has-text("Confirmar Exclusão")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi excluído
    await expect(page.locator('text=Feriado de Natal - Atualizado')).not.toBeVisible();
  });

  test('CRUD de Usuários RBAC', async ({ page }) => {
    await page.goto('/rbac');
    
    // CREATE - Criar novo usuário
    await page.click('button:has-text("Novo Usuário")');
    await page.waitForSelector('[data-testid="user-form"]');
    
    await page.fill('input[name="username"]', 'novo_usuario');
    await page.fill('input[name="email"]', 'novo@email.com');
    await page.fill('input[name="password"]', 'senha123');
    await page.selectOption('select[name="role"]', 'USER');
    
    await page.click('button:has-text("Salvar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // READ - Verificar se foi criado
    await expect(page.locator('text=novo_usuario')).toBeVisible();
    await expect(page.locator('text=novo@email.com')).toBeVisible();
    
    // UPDATE - Editar usuário
    await page.click('button[data-testid="edit-user"]');
    await page.waitForSelector('[data-testid="user-form"]');
    
    await page.fill('input[name="username"]', 'novo_usuario_atualizado');
    await page.selectOption('select[name="role"]', 'ADMIN');
    
    await page.click('button:has-text("Atualizar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi atualizado
    await expect(page.locator('text=novo_usuario_atualizado')).toBeVisible();
    await expect(page.locator('text=ADMIN')).toBeVisible();
    
    // DELETE - Excluir usuário
    await page.click('button[data-testid="delete-user"]');
    await page.click('button:has-text("Confirmar Exclusão")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi excluído
    await expect(page.locator('text=novo_usuario_atualizado')).not.toBeVisible();
  });

  test('Validação de Formulários', async ({ page }) => {
    await page.goto('/agendamentos');
    
    // Testar validação de campos obrigatórios
    await page.click('button:has-text("Novo Agendamento")');
    await page.waitForSelector('[data-testid="appointment-form"]');
    
    // Tentar salvar sem preencher campos obrigatórios
    await page.click('button:has-text("Salvar")');
    
    // Verificar mensagens de erro
    await expect(page.locator('text=Campo obrigatório')).toBeVisible();
    await expect(page.locator('text=Nome do cliente é obrigatório')).toBeVisible();
    await expect(page.locator('text=Telefone é obrigatório')).toBeVisible();
    
    // Preencher campos inválidos
    await page.fill('input[name="clientPhone"]', '123'); // Telefone inválido
    await page.fill('input[name="email"]', 'email-invalido'); // Email inválido
    
    await page.click('button:has-text("Salvar")');
    
    // Verificar mensagens de validação
    await expect(page.locator('text=Telefone inválido')).toBeVisible();
    await expect(page.locator('text=Email inválido')).toBeVisible();
  });

  test('Paginação e Filtros', async ({ page }) => {
    await page.goto('/agendamentos');
    
    // Testar paginação
    if (await page.locator('button:has-text("Próxima")').isVisible()) {
      await page.click('button:has-text("Próxima")');
      await page.waitForLoadState('networkidle');
    }
    
    if (await page.locator('button:has-text("Anterior")').isVisible()) {
      await page.click('button:has-text("Anterior")');
      await page.waitForLoadState('networkidle');
    }
    
    // Testar filtros
    await page.selectOption('select[name="status"]', 'confirmado');
    await page.waitForLoadState('networkidle');
    
    // Verificar se apenas agendamentos confirmados são exibidos
    const statusElements = await page.locator('[data-testid="appointment-status"]').all();
    for (const element of statusElements) {
      await expect(element).toContainText('Confirmado');
    }
    
    // Testar busca
    await page.fill('input[placeholder*="buscar"]', 'teste');
    await page.waitForLoadState('networkidle');
    
    // Verificar se apenas resultados da busca são exibidos
    const searchResults = await page.locator('[data-testid="appointment-item"]').all();
    expect(searchResults.length).toBeGreaterThan(0);
  });

  test('Confirmação de Exclusão', async ({ page }) => {
    await page.goto('/clientes');
    
    // Criar um cliente para testar exclusão
    await page.click('button:has-text("Novo Cliente")');
    await page.waitForSelector('[data-testid="client-form"]');
    
    await page.fill('input[name="name"]', 'Cliente Teste');
    await page.fill('input[name="phone"]', '11777777777');
    await page.fill('input[name="email"]', 'teste@email.com');
    
    await page.click('button:has-text("Salvar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Testar cancelamento de exclusão
    await page.click('button[data-testid="delete-client"]');
    await page.click('button:has-text("Cancelar")');
    
    // Verificar se o cliente ainda existe
    await expect(page.locator('text=Cliente Teste')).toBeVisible();
    
    // Testar confirmação de exclusão
    await page.click('button[data-testid="delete-client"]');
    await page.click('button:has-text("Confirmar Exclusão")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se foi excluído
    await expect(page.locator('text=Cliente Teste')).not.toBeVisible();
  });
});
