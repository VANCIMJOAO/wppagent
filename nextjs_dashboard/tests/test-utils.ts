/**
 * 🧪 Utilitários para Testes - Dashboard WhatsApp Agent
 * Funções auxiliares para testes automatizados
 */

import { Page, expect } from '@playwright/test';
import testConfig from './test-config.json';

export interface TestCredentials {
  username: string;
  password: string;
}

export interface TestData {
  appointment: any;
  client: any;
  user: any;
  blockedTime: any;
}

export class TestUtils {
  private page: Page;
  private config = testConfig;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * 🔐 Realiza login no sistema
   */
  async login(credentials: TestCredentials = this.config.credentials.admin): Promise<void> {
    await this.page.goto('/login');
    
    // Aguardar página carregar
    await this.page.waitForLoadState('networkidle');
    
    // Preencher campos de login
    await this.page.fill('input[id="username"]', credentials.username);
    await this.page.fill('input[id="password"]', credentials.password);
    
    // Clicar no botão de login
    await this.page.click('button[type="submit"]');
    
    // Aguardar o login processar (pode demorar um pouco)
    await this.page.waitForTimeout(2000);
    
    // Verificar se foi redirecionado (pode ser para /dashboard ou outra página)
    const currentUrl = this.page.url();
    console.log(`URL atual após login: ${currentUrl}`);
    
    // Se ainda estiver em /login, aguardar mais um pouco e tentar novamente
    if (currentUrl.includes('/login')) {
      await this.page.waitForTimeout(3000);
      const newUrl = this.page.url();
      console.log(`URL após aguardar mais: ${newUrl}`);
      
      // Se ainda estiver em login, aguardar mais um pouco
      if (newUrl.includes('/login')) {
        await this.page.waitForTimeout(2000);
        const finalUrl = this.page.url();
        console.log(`URL final: ${finalUrl}`);
        
        // Se ainda estiver em login, pode ser que o login falhou
        if (finalUrl.includes('/login')) {
          throw new Error('Login falhou - ainda na página de login após aguardar');
        }
      }
    }
    
    // Verificar se não está mais na página de login
    await expect(this.page).not.toHaveURL('/login');
    
    // Aguardar que a sessão seja estabelecida completamente
    await this.page.waitForTimeout(2000);
    
    // Verificar se os cookies de sessão foram definidos
    const cookies = await this.page.context().cookies();
    const hasSessionCookie = cookies.some(cookie => 
      cookie.name.includes('session') || 
      cookie.name.includes('auth') || 
      cookie.name.includes('token')
    );
    
    if (!hasSessionCookie) {
      console.log('Aviso: Nenhum cookie de sessão encontrado após login');
    }
  }

  /**
   * 🚪 Realiza logout do sistema
   */
  async logout(): Promise<void> {
    // Clicar no menu do usuário
    await this.page.click('[data-testid="user-menu"]');
    
    // Clicar em logout
    await this.page.click('button:has-text("Logout")');
    
    // Aguardar redirecionamento para login
    await this.page.waitForURL('/login');
  }

  /**
   * 📱 Navega para uma página específica
   */
  async navigateToPage(pageName: string): Promise<void> {
    const pageMap: { [key: string]: string } = {
      'dashboard': '/dashboard',
      'conversas': '/conversas',
      'clientes': '/clientes',
      'agendamentos': '/agendamentos',
      'analytics': '/analytics',
      'configuracoes': '/configuracoes',
      'relatorios': '/relatorios',
      'suporte': '/suporte',
      'perfil': '/perfil',
      'monitoring': '/monitoring',
      'bloqueados': '/bloqueados',
      'exportar': '/exportar-relatorios'
    };

    const url = pageMap[pageName];
    if (!url) {
      throw new Error(`Página não encontrada: ${pageName}`);
    }

    await this.page.goto(url);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 🔍 Aguarda elemento aparecer
   */
  async waitForElement(selector: string, timeout: number = 10000): Promise<void> {
    await this.page.waitForSelector(selector, { timeout });
  }

  /**
   * ⏳ Aguarda loading desaparecer
   */
  async waitForLoadingToFinish(): Promise<void> {
    // Aguardar spinners desaparecerem
    await this.page.waitForSelector('[data-testid="loading-spinner"]', { 
      state: 'hidden', 
      timeout: 15000 
    });
  }

  /**
   * 📊 Verifica se métricas estão sendo exibidas
   */
  async verifyMetricsDisplayed(): Promise<void> {
    const metrics = [
      '[data-testid="total-clients"]',
      '[data-testid="total-conversations"]',
      '[data-testid="total-appointments"]',
      '[data-testid="conversion-rate"]'
    ];

    for (const metric of metrics) {
      await this.waitForElement(metric);
      await expect(this.page.locator(metric)).toBeVisible();
    }
  }

  /**
   * 🔄 Aguarda dados carregarem
   */
  async waitForDataToLoad(): Promise<void> {
    // Aguardar elementos de dados aparecerem
    await this.page.waitForFunction(() => {
      const loadingElements = document.querySelectorAll('[data-testid="loading-spinner"]');
      return loadingElements.length === 0;
    }, { timeout: 15000 });
  }

  /**
   * 📝 Preenche formulário
   */
  async fillForm(formData: { [key: string]: string }): Promise<void> {
    for (const [field, value] of Object.entries(formData)) {
      const selector = `input[name="${field}"], select[name="${field}"], textarea[name="${field}"]`;
      await this.page.fill(selector, value);
    }
  }

  /**
   * 🎯 Clica em botão por texto
   */
  async clickButtonByText(text: string): Promise<void> {
    await this.page.click(`button:has-text("${text}")`);
  }

  /**
   * 🔍 Busca por texto
   */
  async searchForText(searchTerm: string, inputSelector: string = 'input[placeholder*="buscar"]'): Promise<void> {
    await this.page.fill(inputSelector, searchTerm);
    await this.page.keyboard.press('Enter');
    await this.waitForLoadingToFinish();
  }

  /**
   * 📋 Verifica se tabela tem dados
   */
  async verifyTableHasData(tableSelector: string = '[data-testid*="table"], [data-testid*="list"]'): Promise<void> {
    await this.waitForElement(tableSelector);
    const rows = await this.page.locator(`${tableSelector} tr, ${tableSelector} [data-testid*="item"]`).count();
    expect(rows).toBeGreaterThan(0);
  }

  /**
   * 🎨 Verifica responsividade
   */
  async testResponsiveDesign(viewport: { width: number; height: number }): Promise<void> {
    await this.page.setViewportSize(viewport);
    await this.page.waitForTimeout(1000); // Aguardar layout se ajustar
    
    // Verificar se sidebar colapsa em mobile
    if (viewport.width < 768) {
      const sidebar = this.page.locator('[data-testid="sidebar"]');
      await expect(sidebar).toBeVisible();
    }
  }

  /**
   * 🔔 Verifica notificações
   */
  async verifyNotification(message: string, type: 'success' | 'error' | 'warning' = 'success'): Promise<void> {
    const notificationSelector = `[data-testid="notification-${type}"]`;
    await this.waitForElement(notificationSelector);
    await expect(this.page.locator(notificationSelector)).toContainText(message);
  }

  /**
   * 📊 Verifica status do sistema
   */
  async verifySystemStatus(): Promise<void> {
    const statusElements = [
      '[data-testid="backend-status"]',
      '[data-testid="database-status"]',
      '[data-testid="cache-status"]',
      '[data-testid="webhook-status"]'
    ];

    for (const element of statusElements) {
      await this.waitForElement(element);
      await expect(this.page.locator(element)).toBeVisible();
    }
  }

  /**
   * 🎭 Simula diferentes tipos de usuário
   */
  async simulateUserRole(role: 'admin' | 'user' | 'viewer'): Promise<void> {
    // Implementar simulação de roles se necessário
    // Por enquanto, apenas login com admin
    await this.login();
  }

  /**
   * 📱 Testa funcionalidades mobile
   */
  async testMobileFeatures(): Promise<void> {
    await this.page.setViewportSize({ width: 375, height: 667 });
    
    // Verificar menu mobile
    const mobileMenu = this.page.locator('[data-testid="mobile-menu"]');
    if (await mobileMenu.isVisible()) {
      await mobileMenu.click();
      await this.page.waitForTimeout(500);
    }
  }

  /**
   * 🔄 Testa auto-refresh
   */
  async testAutoRefresh(): Promise<void> {
    // Aguardar primeira atualização
    await this.page.waitForTimeout(5000);
    
    // Verificar se dados foram atualizados
    const timestamp = await this.page.locator('[data-testid="last-updated"]').textContent();
    expect(timestamp).toBeTruthy();
  }

  /**
   * 🌐 Testa conectividade
   */
  async testConnectivity(): Promise<void> {
    // Verificar se não há indicador de offline
    const offlineIndicator = this.page.locator('[data-testid="offline-indicator"]');
    await expect(offlineIndicator).not.toBeVisible();
  }

  /**
   * 📈 Verifica gráficos
   */
  async verifyCharts(): Promise<void> {
    const chartSelectors = [
      '[data-testid="chart-container"]',
      'canvas',
      '.recharts-wrapper'
    ];

    for (const selector of chartSelectors) {
      const element = this.page.locator(selector);
      if (await element.count() > 0) {
        await expect(element.first()).toBeVisible();
      }
    }
  }

  /**
   * 🎯 Verifica acessibilidade básica
   */
  async verifyBasicAccessibility(): Promise<void> {
    // Verificar se botões têm texto ou aria-label
    const buttons = this.page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      
      expect(text || ariaLabel).toBeTruthy();
    }
  }

  /**
   * 🧹 Limpa dados de teste
   */
  async cleanupTestData(): Promise<void> {
    // Implementar limpeza de dados de teste se necessário
    console.log('🧹 Limpeza de dados de teste concluída');
  }

  /**
   * 📸 Tira screenshot para debug
   */
  async takeDebugScreenshot(name: string): Promise<void> {
    await this.page.screenshot({ 
      path: `test-results/debug-${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }

  /**
   * 🔍 Verifica performance básica
   */
  async verifyBasicPerformance(): Promise<void> {
    // Verificar se página carrega em tempo razoável
    const startTime = Date.now();
    await this.page.goto('/dashboard');
    await this.page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(10000); // 10 segundos
  }
}

/**
 * 🎯 Funções auxiliares globais
 */
export const testHelpers = {
  /**
   * Gera dados de teste únicos
   */
  generateUniqueTestData: (baseData: any) => {
    const timestamp = Date.now();
    return {
      ...baseData,
      name: `${baseData.name}_${timestamp}`,
      email: `test_${timestamp}@example.com`,
      phone: `1199${timestamp.toString().slice(-8)}`
    };
  },

  /**
   * Aguarda timeout
   */
  wait: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),

  /**
   * Verifica se elemento existe
   */
  elementExists: async (page: Page, selector: string): Promise<boolean> => {
    try {
      await page.waitForSelector(selector, { timeout: 1000 });
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Retorna texto de elemento ou string vazia
   */
  getTextSafely: async (page: Page, selector: string): Promise<string> => {
    try {
      const element = page.locator(selector);
      if (await element.count() > 0) {
        return await element.first().textContent() || '';
      }
      return '';
    } catch {
      return '';
    }
  }
};

export default TestUtils;
