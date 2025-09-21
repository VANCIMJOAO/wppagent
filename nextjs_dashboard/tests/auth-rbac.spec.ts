import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

test.describe('Autenticação e RBAC', () => {
  test('Login - Formulário e Validação', async ({ page }) => {
    await page.goto('/login');
    
    // Verificar elementos do formulário
    await expect(page.locator('input[id="username"]')).toBeVisible();
    await expect(page.locator('input[id="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Testar validação de campos obrigatórios
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Campo obrigatório')).toBeVisible();
    
    // Testar credenciais inválidas
    await page.fill('input[id="username"]', 'usuario_inexistente');
    await page.fill('input[id="password"]', 'senha_errada');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Credenciais inválidas')).toBeVisible();
    
    // Testar login com credenciais válidas
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    
    // Verificar redirecionamento para dashboard
    await page.waitForURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('Logout - Limpeza de Sessão', async ({ page }) => {
    // Fazer login primeiro
    await page.goto('/login');
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Fazer logout
    await page.click('button:has-text("Logout")');
    await page.waitForURL('/login');
    
    // Verificar se foi redirecionado para login
    await expect(page.locator('input[id="username"]')).toBeVisible();
    
    // Tentar acessar página protegida
    await page.goto('/dashboard');
    await page.waitForURL('/login');
    
    // Verificar se foi redirecionado para login
    await expect(page.locator('input[id="username"]')).toBeVisible();
  });

  test('Proteção de Rotas - Acesso Negado', async ({ page }) => {
    // Tentar acessar página protegida sem login
    await page.goto('/dashboard');
    await page.waitForURL('/login');
    
    await page.goto('/agendamentos');
    await page.waitForURL('/login');
    
    await page.goto('/conversas');
    await page.waitForURL('/login');
    
    await page.goto('/clientes');
    await page.waitForURL('/login');
    
    await page.goto('/analytics');
    await page.waitForURL('/login');
    
    await page.goto('/relatorios');
    await page.waitForURL('/login');
    
    await page.goto('/configuracoes');
    await page.waitForURL('/login');
    
    await page.goto('/perfil');
    await page.waitForURL('/login');
    
    await page.goto('/monitoring');
    await page.waitForURL('/login');
    
    await page.goto('/bloqueados');
    await page.waitForURL('/login');
    
    await page.goto('/suporte');
    await page.waitForURL('/login');
    
    await page.goto('/rbac');
    await page.waitForURL('/login');
    
    await page.goto('/reports');
    await page.waitForURL('/login');
    
    await page.goto('/diagnostic');
    await page.waitForURL('/login');
  });

  test('RBAC - Gerenciamento de Usuários', async ({ page }) => {
    // Fazer login como admin
    await page.goto('/login');
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Navegar para RBAC
    await page.goto('/rbac');
    
    // Verificar elementos principais
    await expect(page.locator('h1')).toContainText('Gerenciamento de Usuários');
    await expect(page.locator('[data-testid="users-table"]')).toBeVisible();
    await expect(page.locator('button:has-text("Novo Usuário")')).toBeVisible();
    
    // Criar novo usuário
    await page.click('button:has-text("Novo Usuário")');
    await page.waitForSelector('[data-testid="user-form"]');
    
    await page.fill('input[id="username"]', 'novo_usuario');
    await page.fill('input[name="email"]', 'novo@email.com');
    await page.fill('input[id="password"]', 'senha123');
    await page.selectOption('select[name="role"]', 'USER');
    
    await page.click('button:has-text("Salvar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se usuário foi criado
    await expect(page.locator('text=novo_usuario')).toBeVisible();
    
    // Editar usuário
    await page.click('button[data-testid="edit-user"]');
    await page.waitForSelector('[data-testid="user-form"]');
    
    await page.fill('input[id="username"]', 'novo_usuario_atualizado');
    await page.selectOption('select[name="role"]', 'ADMIN');
    
    await page.click('button:has-text("Atualizar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se usuário foi atualizado
    await expect(page.locator('text=novo_usuario_atualizado')).toBeVisible();
    
    // Excluir usuário
    await page.click('button[data-testid="delete-user"]');
    await page.click('button:has-text("Confirmar Exclusão")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se usuário foi excluído
    await expect(page.locator('text=novo_usuario_atualizado')).not.toBeVisible();
  });

  test('RBAC - Gerenciamento de Roles', async ({ page }) => {
    // Fazer login como admin
    await page.goto('/login');
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Navegar para RBAC
    await page.goto('/rbac');
    
    // Gerenciar roles
    await page.click('button:has-text("Gerenciar Roles")');
    await page.waitForSelector('[data-testid="roles-section"]');
    
    // Verificar roles existentes
    await expect(page.locator('text=ADMIN')).toBeVisible();
    await expect(page.locator('text=USER')).toBeVisible();
    await expect(page.locator('text=MANAGER')).toBeVisible();
    
    // Criar nova role
    await page.click('button:has-text("Nova Role")');
    await page.waitForSelector('[data-testid="role-form"]');
    
    await page.fill('input[name="name"]', 'OPERATOR');
    await page.fill('textarea[name="description"]', 'Operador do sistema');
    
    await page.click('button:has-text("Salvar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se role foi criada
    await expect(page.locator('text=OPERATOR')).toBeVisible();
  });

  test('RBAC - Gerenciamento de Permissões', async ({ page }) => {
    // Fazer login como admin
    await page.goto('/login');
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Navegar para RBAC
    await page.goto('/rbac');
    
    // Gerenciar permissões
    await page.click('button:has-text("Gerenciar Permissões")');
    await page.waitForSelector('[data-testid="permissions-section"]');
    
    // Verificar permissões existentes
    await expect(page.locator('text=READ_APPOINTMENTS')).toBeVisible();
    await expect(page.locator('text=WRITE_APPOINTMENTS')).toBeVisible();
    await expect(page.locator('text=DELETE_APPOINTMENTS')).toBeVisible();
    
    // Criar nova permissão
    await page.click('button:has-text("Nova Permissão")');
    await page.waitForSelector('[data-testid="permission-form"]');
    
    await page.fill('input[name="name"]', 'EXPORT_REPORTS');
    await page.fill('textarea[name="description"]', 'Exportar relatórios');
    await page.selectOption('select[name="category"]', 'reports');
    
    await page.click('button:has-text("Salvar")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se permissão foi criada
    await expect(page.locator('text=EXPORT_REPORTS')).toBeVisible();
  });

  test('RBAC - Atribuição de Roles', async ({ page }) => {
    // Fazer login como admin
    await page.goto('/login');
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Navegar para RBAC
    await page.goto('/rbac');
    
    // Atribuir role a usuário
    await page.click('button[data-testid="assign-role"]');
    await page.waitForSelector('[data-testid="assign-role-form"]');
    
    await page.selectOption('select[name="user"]', 'admin');
    await page.selectOption('select[name="role"]', 'ADMIN');
    
    await page.click('button:has-text("Atribuir")');
    await page.waitForSelector('[data-testid="success-message"]');
    
    // Verificar se role foi atribuída
    await expect(page.locator('text=Role atribuída com sucesso')).toBeVisible();
  });

  test('RBAC - Controle de Acesso por Permissão', async ({ page }) => {
    // Fazer login como admin
    await page.goto('/login');
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Testar acesso a páginas protegidas por permissão
    await page.goto('/agendamentos');
    await expect(page.locator('h1')).toContainText('Agendamentos');
    
    await page.goto('/conversas');
    await expect(page.locator('h1')).toContainText('Conversas');
    
    await page.goto('/clientes');
    await expect(page.locator('h1')).toContainText('Clientes');
    
    await page.goto('/analytics');
    await expect(page.locator('h1')).toContainText('Analytics');
    
    await page.goto('/relatorios');
    await expect(page.locator('h1')).toContainText('Relatórios');
    
    await page.goto('/configuracoes');
    await expect(page.locator('h1')).toContainText('Configurações');
    
    await page.goto('/perfil');
    await expect(page.locator('h1')).toContainText('Perfil');
    
    await page.goto('/monitoring');
    await expect(page.locator('h1')).toContainText('Monitoramento');
    
    await page.goto('/bloqueados');
    await expect(page.locator('h1')).toContainText('Horários Bloqueados');
    
    await page.goto('/suporte');
    await expect(page.locator('h1')).toContainText('Suporte');
    
    await page.goto('/rbac');
    await expect(page.locator('h1')).toContainText('Gerenciamento de Usuários');
    
    await page.goto('/reports');
    await expect(page.locator('h1')).toContainText('Exportar Relatórios');
    
    await page.goto('/diagnostic');
    await expect(page.locator('h1')).toContainText('Diagnóstico do Sistema');
  });

  test('Sessão - Expiração e Renovação', async ({ page }) => {
    // Fazer login
    await page.goto('/login');
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Simular expiração de sessão
    await page.evaluate(() => {
      localStorage.removeItem('token');
      sessionStorage.removeItem('token');
    });
    
    // Tentar acessar página protegida
    await page.goto('/dashboard');
    await page.waitForURL('/login');
    
    // Verificar se foi redirecionado para login
    await expect(page.locator('input[id="username"]')).toBeVisible();
  });

  test('2FA - Autenticação de Dois Fatores', async ({ page }) => {
    await page.goto('/login');
    
    // Preencher credenciais
    await page.fill('input[id="username"]', TEST_CREDENTIALS.username);
    await page.fill('input[id="password"]', TEST_CREDENTIALS.password);
    await page.click('button[type="submit"]');
    
    // Verificar se 2FA é solicitado
    if (await page.locator('[data-testid="2fa-form"]').isVisible()) {
      await expect(page.locator('input[name="code"]')).toBeVisible();
      await expect(page.locator('button:has-text("Verificar Código")')).toBeVisible();
      
      // Simular código 2FA
      await page.fill('input[name="code"]', '123456');
      await page.click('button:has-text("Verificar Código")');
      
      // Verificar se foi redirecionado para dashboard
      await page.waitForURL('/dashboard');
      await expect(page.locator('h1')).toContainText('Dashboard');
    }
  });

  test('Rate Limiting - Proteção contra Ataques', async ({ page }) => {
    // Tentar múltiplas tentativas de login
    for (let i = 0; i < 5; i++) {
      await page.goto('/login');
      await page.fill('input[id="username"]', 'usuario_inexistente');
      await page.fill('input[id="password"]', 'senha_errada');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(1000);
    }
    
    // Verificar se rate limiting foi ativado
    await expect(page.locator('text=Muitas tentativas de login')).toBeVisible();
  });
});
