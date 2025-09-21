import { test, expect, Page } from '@playwright/test';
import path from 'path';

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

test.describe('Exportação e Relatórios', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('Exportação CSV - Agendamentos', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="export-section"]');
    
    // Selecionar tipo de relatório
    await page.click('button:has-text("Agendamentos")');
    
    // Selecionar formato CSV
    await page.click('button:has-text("CSV")');
    
    // Configurar período
    await page.fill('input[name="startDate"]', '2024-01-01');
    await page.fill('input[name="endDate"]', '2024-12-31');
    
    // Iniciar exportação
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Exportar")');
    
    const download = await downloadPromise;
    
    // Verificar se download foi iniciado
    expect(download.suggestedFilename()).toContain('.csv');
    
    // Verificar se arquivo foi baixado
    const downloadPath = await download.path();
    expect(downloadPath).toBeTruthy();
  });

  test('Exportação Excel - Conversas', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="export-section"]');
    
    // Selecionar tipo de relatório
    await page.click('button:has-text("Conversas")');
    
    // Selecionar formato Excel
    await page.click('button:has-text("Excel")');
    
    // Configurar período
    await page.fill('input[name="startDate"]', '2024-01-01');
    await page.fill('input[name="endDate"]', '2024-12-31');
    
    // Iniciar exportação
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Exportar")');
    
    const download = await downloadPromise;
    
    // Verificar se download foi iniciado
    expect(download.suggestedFilename()).toContain('.xlsx');
    
    // Verificar se arquivo foi baixado
    const downloadPath = await download.path();
    expect(downloadPath).toBeTruthy();
  });

  test('Exportação PDF - Dashboard', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="export-section"]');
    
    // Selecionar tipo de relatório
    await page.click('button:has-text("Dashboard")');
    
    // Selecionar formato PDF
    await page.click('button:has-text("PDF")');
    
    // Configurar período
    await page.fill('input[name="startDate"]', '2024-01-01');
    await page.fill('input[name="endDate"]', '2024-12-31');
    
    // Iniciar exportação
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Exportar")');
    
    const download = await downloadPromise;
    
    // Verificar se download foi iniciado
    expect(download.suggestedFilename()).toContain('.pdf');
    
    // Verificar se arquivo foi baixado
    const downloadPath = await download.path();
    expect(downloadPath).toBeTruthy();
  });

  test('Relatórios - Gráficos Interativos', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="reports-container"]');
    
    // Testar tab Visão Geral
    await page.click('button:has-text("Visão Geral")');
    await expect(page.locator('[data-testid="overview-charts"]')).toBeVisible();
    
    // Testar tab Funil
    await page.click('button:has-text("Funil")');
    await expect(page.locator('[data-testid="funnel-charts"]')).toBeVisible();
    
    // Testar tab Performance
    await page.click('button:has-text("Performance")');
    await expect(page.locator('[data-testid="performance-charts"]')).toBeVisible();
    
    // Testar tab Tendências
    await page.click('button:has-text("Tendências")');
    await expect(page.locator('[data-testid="trends-charts"]')).toBeVisible();
  });

  test('Filtros de Período - Personalização', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="filters-section"]');
    
    // Testar filtro de período personalizado
    await page.click('button:has-text("Período Personalizado")');
    
    // Preencher datas
    await page.fill('input[name="startDate"]', '2024-06-01');
    await page.fill('input[name="endDate"]', '2024-06-30');
    
    // Aplicar filtro
    await page.click('button:has-text("Aplicar Filtro")');
    
    // Verificar se dados foram filtrados
    await expect(page.locator('[data-testid="filtered-data"]')).toBeVisible();
    
    // Testar filtro de período rápido
    await page.click('button:has-text("Últimos 7 dias")');
    await expect(page.locator('[data-testid="filtered-data"]')).toBeVisible();
    
    await page.click('button:has-text("Últimos 30 dias")');
    await expect(page.locator('[data-testid="filtered-data"]')).toBeVisible();
    
    await page.click('button:has-text("Últimos 90 dias")');
    await expect(page.locator('[data-testid="filtered-data"]')).toBeVisible();
  });

  test('KPIs Executivos - Métricas Principais', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="kpi-section"]');
    
    // Verificar KPIs principais
    await expect(page.locator('[data-testid="revenue-kpi"]')).toBeVisible();
    await expect(page.locator('[data-testid="conversations-kpi"]')).toBeVisible();
    await expect(page.locator('[data-testid="clients-kpi"]')).toBeVisible();
    await expect(page.locator('[data-testid="conversion-kpi"]')).toBeVisible();
    
    // Verificar se valores estão sendo exibidos
    const revenue = await page.textContent('[data-testid="revenue-kpi"]');
    const conversations = await page.textContent('[data-testid="conversations-kpi"]');
    const clients = await page.textContent('[data-testid="clients-kpi"]');
    const conversion = await page.textContent('[data-testid="conversion-kpi"]');
    
    expect(revenue).toBeTruthy();
    expect(conversations).toBeTruthy();
    expect(clients).toBeTruthy();
    expect(conversion).toBeTruthy();
  });

  test('Funil de Conversão - Análise de Etapas', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="funnel-section"]');
    
    // Navegar para tab Funil
    await page.click('button:has-text("Funil")');
    
    // Verificar etapas do funil
    await expect(page.locator('[data-testid="funnel-step-1"]')).toBeVisible();
    await expect(page.locator('[data-testid="funnel-step-2"]')).toBeVisible();
    await expect(page.locator('[data-testid="funnel-step-3"]')).toBeVisible();
    await expect(page.locator('[data-testid="funnel-step-4"]')).toBeVisible();
    
    // Verificar taxas de conversão
    await expect(page.locator('[data-testid="conversion-rate-1"]')).toBeVisible();
    await expect(page.locator('[data-testid="conversion-rate-2"]')).toBeVisible();
    await expect(page.locator('[data-testid="conversion-rate-3"]')).toBeVisible();
  });

  test('Métricas de Performance - Análise Detalhada', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="performance-section"]');
    
    // Navegar para tab Performance
    await page.click('button:has-text("Performance")');
    
    // Verificar métricas de performance
    await expect(page.locator('[data-testid="response-time-metric"]')).toBeVisible();
    await expect(page.locator('[data-testid="engagement-metric"]')).toBeVisible();
    await expect(page.locator('[data-testid="satisfaction-metric"]')).toBeVisible();
    
    // Verificar gráficos de performance
    await expect(page.locator('[data-testid="performance-chart-1"]')).toBeVisible();
    await expect(page.locator('[data-testid="performance-chart-2"]')).toBeVisible();
  });

  test('Análise Temporal - Tendências', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="trends-section"]');
    
    // Navegar para tab Tendências
    await page.click('button:has-text("Tendências")');
    
    // Verificar gráficos de tendências
    await expect(page.locator('[data-testid="trends-chart-1"]')).toBeVisible();
    await expect(page.locator('[data-testid="trends-chart-2"]')).toBeVisible();
    
    // Testar mudança de granularidade
    await page.selectOption('select[name="granularity"]', 'daily');
    await expect(page.locator('[data-testid="trends-chart-1"]')).toBeVisible();
    
    await page.selectOption('select[name="granularity"]', 'weekly');
    await expect(page.locator('[data-testid="trends-chart-1"]')).toBeVisible();
    
    await page.selectOption('select[name="granularity"]', 'monthly');
    await expect(page.locator('[data-testid="trends-chart-1"]')).toBeVisible();
  });

  test('Formatação Brasileira - Moeda e Números', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="kpi-section"]');
    
    // Verificar formatação de moeda
    const revenue = await page.textContent('[data-testid="revenue-kpi"]');
    expect(revenue).toMatch(/R\$/); // Deve conter R$
    
    // Verificar formatação de números
    const clients = await page.textContent('[data-testid="clients-kpi"]');
    expect(clients).toMatch(/\d+/); // Deve conter números
    
    // Verificar formatação de porcentagem
    const conversion = await page.textContent('[data-testid="conversion-kpi"]');
    expect(conversion).toMatch(/%/); // Deve conter %
  });

  test('Exportação em Lote - Múltiplos Relatórios', async ({ page }) => {
    await page.goto('/reports');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="batch-export-section"]');
    
    // Selecionar múltiplos relatórios
    await page.check('input[value="appointments"]');
    await page.check('input[value="conversations"]');
    await page.check('input[value="dashboard"]');
    
    // Selecionar formato
    await page.click('button:has-text("Excel")');
    
    // Configurar período
    await page.fill('input[name="startDate"]', '2024-01-01');
    await page.fill('input[name="endDate"]', '2024-12-31');
    
    // Iniciar exportação em lote
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Exportar em Lote")');
    
    const download = await downloadPromise;
    
    // Verificar se download foi iniciado
    expect(download.suggestedFilename()).toContain('.xlsx');
    
    // Verificar se arquivo foi baixado
    const downloadPath = await download.path();
    expect(downloadPath).toBeTruthy();
  });

  test('Validação de Dados - Verificação de Integridade', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="data-validation"]');
    
    // Verificar se dados estão sendo validados
    await expect(page.locator('[data-testid="data-integrity-check"]')).toBeVisible();
    
    // Verificar se não há dados duplicados
    await expect(page.locator('[data-testid="duplicate-check"]')).toBeVisible();
    
    // Verificar se dados estão completos
    await expect(page.locator('[data-testid="completeness-check"]')).toBeVisible();
  });

  test('Relatórios Automáticos - Agendamento', async ({ page }) => {
    await page.goto('/relatorios');
    
    // Aguardar carregamento da página
    await page.waitForSelector('[data-testid="automated-reports"]');
    
    // Configurar relatório automático
    await page.click('button:has-text("Configurar Relatório Automático")');
    
    // Preencher configurações
    await page.fill('input[name="email"]', 'admin@exemplo.com');
    await page.selectOption('select[name="frequency"]', 'weekly');
    await page.selectOption('select[name="format"]', 'pdf');
    
    // Salvar configuração
    await page.click('button:has-text("Salvar Configuração")');
    
    // Verificar se configuração foi salva
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });
});
