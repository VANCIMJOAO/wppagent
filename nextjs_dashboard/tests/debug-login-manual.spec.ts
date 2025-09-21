import { test, expect, Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const TEST_CREDENTIALS = {
  username: 'admin',
  password: 'admin123'
};

test.describe('Debug Login - Simulação Manual', () => {
  test('Debug - Simular login manualmente via JavaScript', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Página carregada');
    
    // Executar login manualmente via JavaScript
    const result = await page.evaluate(async (credentials) => {
      try {
        console.log('🚀 Iniciando login manual...');
        
        // 1. Fazer login
        const loginResponse = await fetch('/api/proxy/admin/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(credentials)
        });
        
        console.log('📡 Login response status:', loginResponse.status);
        
        if (!loginResponse.ok) {
          throw new Error(`Login failed: ${loginResponse.status}`);
        }
        
        const loginData = await loginResponse.json();
        console.log('📦 Login data received:', loginData);
        
        // Verificar estrutura da resposta
        if (!loginData.success || !loginData.data || !loginData.data.access_token) {
          throw new Error('Resposta inválida do servidor');
        }
        
        // 2. Salvar token
        const tokenResponse = await fetch('/api/auth/set-token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ token: loginData.data.access_token })
        });
        
        console.log('🍪 Token response status:', tokenResponse.status);
        
        if (!tokenResponse.ok) {
          throw new Error(`Token save failed: ${tokenResponse.status}`);
        }
        
        const tokenData = await tokenResponse.json();
        console.log('🍪 Token data received:', tokenData);
        
        // 3. Decodificar JWT
        const payload = JSON.parse(atob(loginData.data.access_token.split('.')[1]));
        console.log('🔓 JWT payload:', payload);
        
        const userData = {
          username: payload.sub,
          role: payload.role,
          permissions: payload.permissions || []
        };
        
        // 4. Salvar no localStorage
        localStorage.setItem('user', JSON.stringify(userData));
        console.log('💾 User data saved to localStorage');
        
        // 5. Verificar cookies
        const cookies = document.cookie;
        console.log('🍪 Current cookies:', cookies);
        
        return {
          success: true,
          loginData,
          tokenData,
          userData,
          cookies,
          localStorage: localStorage.getItem('user')
        };
        
      } catch (error) {
        console.error('❌ Error during manual login:', error);
        return {
          success: false,
          error: error.message,
          stack: error.stack
        };
      }
    }, TEST_CREDENTIALS);
    
    console.log('📊 Resultado do login manual:', result);
    
    if (result.success) {
      console.log('✅ Login manual bem-sucedido!');
      console.log('🍪 Cookies:', result.cookies);
      console.log('💾 localStorage:', result.localStorage);
      
      // Verificar se o token está no cookie
      const hasToken = result.cookies.includes('auth-token');
      console.log('🔑 Token no cookie:', hasToken);
      
      // Verificar se os dados estão no localStorage
      const hasUserData = result.localStorage !== null;
      console.log('👤 Dados no localStorage:', hasUserData);
      
    } else {
      console.log('❌ Erro no login manual:', result.error);
      console.log('📚 Stack trace:', result.stack);
    }
  });
});
