import { test, expect, Page } from '@playwright/test';

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
  
  // Aguardar redirecionamento para dashboard
  await page.waitForURL('/dashboard');
  await page.waitForLoadState('networkidle');
}

test.describe('Debug Páginas - Investigar Problemas de Carregamento', () => {
  test('Debug página agendamentos', async ({ page }) => {
    await login(page);
    
    // Interceptar requisições para debug
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        console.log('🔍 Request:', request.method(), request.url());
      }
    });

    page.on('response', response => {
      if (response.url().includes('/api/')) {
        console.log('🔍 Response:', response.status(), response.url());
        if (response.status() !== 200) {
          console.log('❌ Erro na API:', response.status(), response.url());
        }
      }
    });

    // Interceptar console logs do navegador
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Console Error:', msg.text());
      } else if (msg.type() === 'warn') {
        console.log('⚠️ Console Warning:', msg.text());
      }
    });

    // Interceptar erros de página
    page.on('pageerror', error => {
      console.log('❌ Page Error:', error.message);
    });

    // Navegar para agendamentos
    console.log('🌐 Navegando para /agendamentos...');
    await page.goto('/agendamentos');
    await page.waitForLoadState('networkidle');
    
    console.log('🌐 URL atual:', page.url());
    
    // Aguardar um pouco para ver se carrega
    await page.waitForTimeout(5000);
    
    // Verificar se há conteúdo
    const bodyText = await page.locator('body').textContent();
    console.log('📄 Conteúdo da página:', bodyText?.substring(0, 200) + '...');
    
    // Verificar se há elementos específicos
    const hasTitle = await page.locator('h1:has-text("Agendamentos")').isVisible();
    console.log('📋 Tem título "Agendamentos":', hasTitle);
    
    const hasLoading = await page.locator('text=Carregando...').isVisible();
    console.log('⏳ Mostra "Carregando...":', hasLoading);
    
    const hasError = await page.locator('text=404').isVisible();
    console.log('❌ Mostra erro 404:', hasError);
    
    // Verificar se há dados carregados
    const hasStats = await page.locator('text=Total').isVisible();
    console.log('📊 Tem estatísticas:', hasStats);
    
    // Verificar se há lista de agendamentos
    const hasAppointments = await page.locator('text=Agendamentos').isVisible();
    console.log('📅 Tem seção de agendamentos:', hasAppointments);
    
    // O teste passa se pelo menos não redirecionou para login
    expect(page.url()).toContain('/agendamentos');
  });

  test('Debug API calls', async ({ page }) => {
    await login(page);
    
    // Interceptar todas as requisições
    const requests: string[] = [];
    const responses: { url: string; status: number; body?: any }[] = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        requests.push(`${request.method()} ${request.url()}`);
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/')) {
        let body = null;
        try {
          body = await response.json();
        } catch (e) {
          // Ignorar se não for JSON
        }
        responses.push({
          url: response.url(),
          status: response.status(),
          body
        });
      }
    });

    // Navegar para agendamentos
    await page.goto('/agendamentos');
    await page.waitForLoadState('networkidle');
    
    // Aguardar um pouco para capturar todas as requisições
    await page.waitForTimeout(3000);
    
    console.log('🔍 Requisições capturadas:');
    requests.forEach(req => console.log('  ', req));
    
    console.log('🔍 Respostas capturadas:');
    responses.forEach(resp => {
      console.log(`  ${resp.status} ${resp.url}`);
      if (resp.status !== 200) {
        console.log('    ❌ Erro:', resp.body);
      }
    });
    
    // Verificar se há requisições para APIs de agendamentos
    const hasAppointmentsAPI = requests.some(req => req.includes('appointments'));
    const hasDashboardAPI = requests.some(req => req.includes('dashboard'));
    
    console.log('📊 API de agendamentos chamada:', hasAppointmentsAPI);
    console.log('📊 API de dashboard chamada:', hasDashboardAPI);
    
    // O teste passa se pelo menos uma API foi chamada
    expect(hasAppointmentsAPI || hasDashboardAPI).toBeTruthy();
  });
});
