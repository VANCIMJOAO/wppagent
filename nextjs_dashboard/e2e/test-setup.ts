import { test as base, expect, Page, Route } from '@playwright/test';

/**
 * Configuração global para testes E2E
 * Inclui helpers, fixtures e utilitários comuns
 */

// Definir tipos para fixtures customizadas
type TestFixtures = {
  authenticatedPage: Page;
  testData: any;
};

// Extend base test with custom fixtures
export const test = base.extend<TestFixtures>({
  // Fixture para login automatizado
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/login');
    
    // Aguardar formulário de login carregar
    await page.waitForSelector('form', { timeout: 10000 });
    
    // Preencher credenciais de teste
    await page.fill('[data-testid="email"], [name="email"], [type="email"]', 'admin@test.com');
    await page.fill('[data-testid="password"], [name="password"], [type="password"]', 'admin123');
    
    // Submeter formulário
    await page.click('[data-testid="login-button"], [type="submit"], button:has-text("Entrar")');
    
    // Aguardar redirecionamento
    await page.waitForURL('/dashboard/**', { timeout: 15000 });
    
    await use(page);
  },

  // Fixture para dados de teste
  testData: async ({}, use: (r: any) => Promise<void>) => {
    const testData = {
      users: {
        admin: {
          email: 'admin@test.com',
          password: 'admin123',
          name: 'Administrador Teste'
        },
        regular: {
          email: 'user@test.com', 
          password: 'user123',
          name: 'Usuário Teste'
        }
      },
      appointments: {
        valid: {
          clientName: 'João Silva',
          phone: '(11) 99999-9999',
          service: 'Consulta',
          date: '2025-09-15',
          time: '14:00'
        },
        invalid: {
          clientName: '',
          phone: 'invalid-phone',
          service: '',
          date: '2020-01-01',
          time: ''
        }
      },
      messages: {
        text: 'Mensagem de teste E2E',
        media: 'test-image.jpg'
      }
    };
    
    await use(testData);
  }
});

// Helper functions
export class PageHelpers {
  constructor(private page: any) {}

  async waitForLoadingToFinish() {
    // Aguardar indicadores de loading desaparecerem
    await this.page.waitForFunction(() => {
      const loadingElements = document.querySelectorAll('[data-testid*="loading"], .loading, .spinner');
      return loadingElements.length === 0;
    }, { timeout: 10000 });
  }

  async fillFormField(selector: string, value: string) {
    await this.page.waitForSelector(selector, { timeout: 5000 });
    await this.page.fill(selector, value);
  }

  async clickAndWaitForNavigation(selector: string, urlPattern?: string) {
    await this.page.click(selector);
    if (urlPattern) {
      await this.page.waitForURL(new RegExp(urlPattern), { timeout: 10000 });
    }
  }

  async takeScreenshotOnFailure(testName: string) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${testName}-failure.png`,
      fullPage: true
    });
  }

  async interceptApiCalls(pattern: string, mockResponse?: any) {
    await this.page.route(pattern, (route: Route) => {
      if (mockResponse) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockResponse)
        });
      } else {
        route.continue();
      }
    });
  }
}

export { expect };
