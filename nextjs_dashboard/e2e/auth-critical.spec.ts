import { test, expect, PageHelpers } from './test-setup';

test.describe('Fluxo Crítico de Autenticação', () => {
  test('deve fazer login com credenciais válidas', async ({ page, testData }) => {
    const helpers = new PageHelpers(page);
    
    await page.goto('/login');
    
    // Verificar se formulário de login existe
    await expect(page.locator('form')).toBeVisible();
    
    // Preencher credenciais válidas
    await helpers.fillFormField('[data-testid="email"], [name="email"], [type="email"]', testData.users.admin.email);
    await helpers.fillFormField('[data-testid="password"], [name="password"], [type="password"]', testData.users.admin.password);
    
    // Interceptar chamada de login
    await helpers.interceptApiCalls('**/api/auth/login');
    
    // Submeter formulário
    await helpers.clickAndWaitForNavigation('[data-testid="login-button"], [type="submit"], button:has-text("Entrar")');
    
    // Verificar redirecionamento para dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Verificar elementos do dashboard
    await expect(page.locator('h1, h2').filter({ hasText: /dashboard|painel/i }).first()).toBeVisible();
    
    console.log('✅ Login realizado com sucesso');
  });

  test('deve rejeitar credenciais inválidas', async ({ page, testData }) => {
    const helpers = new PageHelpers(page);
    
    await page.goto('/login');
    
    // Preencher credenciais inválidas
    await helpers.fillFormField('[data-testid="email"], [name="email"], [type="email"]', 'invalid@test.com');
    await helpers.fillFormField('[data-testid="password"], [name="password"], [type="password"]', 'wrongpassword');
    
    // Submeter formulário
    await page.click('[data-testid="login-button"], [type="submit"], button:has-text("Entrar")');
    
    // Verificar mensagem de erro
    await expect(page.locator('[data-testid="error-message"], .error, .alert-error').first()).toBeVisible({ timeout: 10000 });
    
    // Verificar que não foi redirecionado
    await expect(page).toHaveURL(/\/login/);
    
    console.log('✅ Credenciais inválidas rejeitadas corretamente');
  });

  test('deve fazer logout corretamente', async ({ authenticatedPage: page }) => {
    const helpers = new PageHelpers(page);
    
    // Verificar que está logado
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Procurar botão de logout
    const logoutButton = page.locator('[data-testid="logout-button"], button:has-text("Sair"), button:has-text("Logout")');
    
    if (await logoutButton.count() === 0) {
      // Se não encontrar botão direto, procurar em menu dropdown
      const userMenu = page.locator('[data-testid="user-menu"], .user-menu, [role="button"]:has([data-testid="avatar"])');
      if (await userMenu.count() > 0) {
        await userMenu.first().click();
        await page.locator('text="Sair", text="Logout"').first().click();
      }
    } else {
      await logoutButton.first().click();
    }
    
    // Verificar redirecionamento para login
    await expect(page).toHaveURL(/\/login/);
    
    console.log('✅ Logout realizado com sucesso');
  });

  test('deve proteger rotas autenticadas', async ({ page }) => {
    // Tentar acessar dashboard sem autenticação
    await page.goto('/dashboard');
    
    // Deve ser redirecionado para login
    await expect(page).toHaveURL(/\/login/);
    
    // Tentar acessar outras rotas protegidas
    const protectedRoutes = ['/dashboard/appointments', '/dashboard/messages', '/dashboard/analytics'];
    
    for (const route of protectedRoutes) {
      await page.goto(route);
      await expect(page).toHaveURL(/\/login/);
    }
    
    console.log('✅ Rotas protegidas funcionando corretamente');
  });
});
