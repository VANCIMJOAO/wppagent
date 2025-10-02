import { test, expect } from '@playwright/test';

test.describe('Debug Modal', () => {
  test('deve abrir modal de novo agendamento', async ({ page }) => {
    // Fazer login primeiro
    await page.goto('/login');
    await page.waitForSelector('input[id="username"]', { state: 'visible' });
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    
    // Ir para a página de agendamentos
    await page.goto('/agendamentos');
    
    // Aguardar página carregar
    await page.waitForSelector('[data-testid="appointments-page"]', { timeout: 10000 });
    
    // Verificar se o botão existe e usar o primeiro
    const button = page.locator('button:has-text("Novo Agendamento")').first();
    await expect(button).toBeVisible();
    
    // Clicar no botão
    await button.click();
    
    // Aguardar um pouco para ver o que acontece
    await page.waitForTimeout(2000);
    
    // Verificar se algum modal apareceu
    const modal = page.locator('.fixed.inset-0');
    const isModalVisible = await modal.isVisible();
    
    console.log('Modal visível:', isModalVisible);
    
    // Verificar se há erros no console
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Aguardar um pouco mais para capturar erros
    await page.waitForTimeout(1000);
    
    if (consoleErrors.length > 0) {
      console.log('Erros no console:', consoleErrors);
    }
    
    // Verificar se há elementos com role="dialog"
    const dialogElements = await page.locator('[role="dialog"]').count();
    console.log('Elementos com role="dialog":', dialogElements);
    
    // Verificar se há elementos com classe modal
    const modalElements = await page.locator('.modal, [data-modal], [aria-modal="true"]').count();
    console.log('Elementos modal encontrados:', modalElements);
  });
});
