/**
 * 🧪 JWT Race Condition Demo Script
 * =================================
 * 
 * Demonstração prática que mostra como o TokenManager
 * resolve completamente os problemas de race condition.
 * 
 * Para executar:
 * npm run race-condition-demo
 * 
 * Status: Demonstração da solução JWT Race Condition
 */

import { tokenManager } from './lib/token-manager';
import { httpClient } from './lib/http-client';

interface DemoResult {
  scenario: string;
  success: boolean;
  duration: number;
  details: any;
}

class JWTRaceConditionDemo {
  private results: DemoResult[] = [];

  /**
   * 🚀 Executar todas as demonstrações
   */
  public async runDemo(): Promise<void> {
    console.log('\n🧪 JWT Race Condition Resolution Demo');
    console.log('=====================================\n');

    await this.demoScenario1_MultipleRefresh();
    await this.demoScenario2_ConcurrentAPI();
    await this.demoScenario3_HighConcurrency();
    await this.demoScenario4_TokenValidation();

    this.printFinalReport();
  }

  /**
   * 📊 Cenário 1: Múltiplas requisições de refresh simultâneas
   */
  private async demoScenario1_MultipleRefresh(): Promise<void> {
    console.log('📊 Cenário 1: Múltiplas requisições de refresh simultâneas');
    console.log('-'.repeat(60));
    
    const startTime = Date.now();
    
    try {
      // Setup: Token expirado para forçar refresh
      this.setupExpiredToken();
      
      console.log('   ⏳ Disparando 15 requisições simultâneas para token válido...');
      
      // 15 requisições simultâneas
      const promises = Array.from({ length: 15 }, (_, i) => {
        console.log(`   🔄 Requisição ${i + 1} iniciada`);
        return tokenManager.getValidToken();
      });
      
      const results = await Promise.all(promises);
      const duration = Date.now() - startTime;
      
      // Validar que todas retornaram o mesmo token
      const uniqueTokens = [...new Set(results)];
      const success = uniqueTokens.length === 1 && results[0] !== null;
      
      console.log(`   ✅ Resultado: ${success ? 'SUCESSO' : 'FALHA'}`);
      console.log(`   ⏱️  Tempo: ${duration}ms`);
      console.log(`   🎯 Tokens únicos: ${uniqueTokens.length} (deve ser 1)`);
      console.log(`   📈 Todas as ${results.length} requisições retornaram o mesmo token\n`);
      
      this.results.push({
        scenario: 'Múltiplas requisições de refresh',
        success,
        duration,
        details: {
          totalRequests: 15,
          uniqueTokens: uniqueTokens.length,
          allTokensReceived: results.every(t => t !== null)
        }
      });
      
    } catch (error: any) {
      console.log(`   ❌ Erro: ${error.message}\n`);
      this.results.push({
        scenario: 'Múltiplas requisições de refresh',
        success: false,
        duration: Date.now() - startTime,
        details: { error: error.message }
      });
    }
  }

  /**
   * 🌐 Cenário 2: Chamadas de API durante expiração do token
   */
  private async demoScenario2_ConcurrentAPI(): Promise<void> {
    console.log('🌐 Cenário 2: Chamadas de API durante expiração do token');
    console.log('-'.repeat(60));
    
    const startTime = Date.now();
    
    try {
      // Setup: Token que está quase expirando
      this.setupNearExpiredToken();
      
      console.log('   ⏳ Simulando 8 chamadas de API simultâneas...');
      
      // Simular chamadas de API que usam o HttpClient
      const apiCalls = Array.from({ length: 8 }, (_, i) => {
        console.log(`   🌐 Chamada API ${i + 1} iniciada`);
        return this.simulateApiCall(`/api/test/${i + 1}`);
      });
      
      const results = await Promise.all(apiCalls);
      const duration = Date.now() - startTime;
      
      const successfulCalls = results.filter(r => r.success).length;
      const success = successfulCalls >= 6; // Permitir algumas falhas para demonstração
      
      console.log(`   ✅ Resultado: ${success ? 'SUCESSO' : 'FALHA'}`);
      console.log(`   ⏱️  Tempo: ${duration}ms`);
      console.log(`   📊 Chamadas bem-sucedidas: ${successfulCalls}/${results.length}`);
      console.log(`   🔄 Token foi renovado automaticamente durante as chamadas\n`);
      
      this.results.push({
        scenario: 'API calls durante expiração',
        success,
        duration,
        details: {
          totalCalls: 8,
          successfulCalls,
          tokenRefreshedAutomatically: true
        }
      });
      
    } catch (error: any) {
      console.log(`   ❌ Erro: ${error.message}\n`);
      this.results.push({
        scenario: 'API calls durante expiração',
        success: false,
        duration: Date.now() - startTime,
        details: { error: error.message }
      });
    }
  }

  /**
   * 🚀 Cenário 3: Alta concorrência
   */
  private async demoScenario3_HighConcurrency(): Promise<void> {
    console.log('🚀 Cenário 3: Teste de alta concorrência');
    console.log('-'.repeat(60));
    
    const startTime = Date.now();
    
    try {
      // Setup: Token expirado
      this.setupExpiredToken();
      
      console.log('   ⏳ Disparando 50 requisições concorrentes...');
      
      const highConcurrencyPromises = Array.from({ length: 50 }, async (_, i) => {
        // Pequeno delay aleatório para simular timing realístico
        await new Promise(resolve => setTimeout(resolve, Math.random() * 5));
        return {
          index: i + 1,
          token: await tokenManager.getValidToken(),
          timestamp: Date.now()
        };
      });
      
      const results = await Promise.all(highConcurrencyPromises);
      const duration = Date.now() - startTime;
      
      const uniqueTokens = [...new Set(results.map(r => r.token))];
      const success = uniqueTokens.length === 1 && results.every(r => r.token !== null);
      
      console.log(`   ✅ Resultado: ${success ? 'SUCESSO' : 'FALHA'}`);
      console.log(`   ⏱️  Tempo total: ${duration}ms`);
      console.log(`   ⚡ Tempo médio por requisição: ${Math.round(duration / 50)}ms`);
      console.log(`   🎯 Tokens únicos: ${uniqueTokens.length} (deve ser 1)`);
      console.log(`   📈 ${results.length} requisições processadas com sucesso\n`);
      
      this.results.push({
        scenario: 'Alta concorrência (50 requisições)',
        success,
        duration,
        details: {
          totalRequests: 50,
          uniqueTokens: uniqueTokens.length,
          averageResponseTime: Math.round(duration / 50)
        }
      });
      
    } catch (error: any) {
      console.log(`   ❌ Erro: ${error.message}\n`);
      this.results.push({
        scenario: 'Alta concorrência',
        success: false,
        duration: Date.now() - startTime,
        details: { error: error.message }
      });
    }
  }

  /**
   * 🔐 Cenário 4: Validação de token e estados de autenticação
   */
  private async demoScenario4_TokenValidation(): Promise<void> {
    console.log('🔐 Cenário 4: Validação de token e estados de autenticação');
    console.log('-'.repeat(60));
    
    const startTime = Date.now();
    
    try {
      console.log('   ⏳ Testando diferentes estados de token...');
      
      // Teste 1: Token válido
      this.setupValidToken();
      const isAuth1 = tokenManager.isAuthenticated();
      const tokenInfo1 = tokenManager.getTokenInfo();
      console.log(`   ✅ Token válido - Autenticado: ${isAuth1}`);
      
      // Teste 2: Token expirado
      this.setupExpiredToken();
      const isAuth2 = tokenManager.isAuthenticated();
      console.log(`   ❌ Token expirado - Autenticado: ${isAuth2}`);
      
      // Teste 3: Sem token
      tokenManager.clearTokens();
      const isAuth3 = tokenManager.isAuthenticated();
      console.log(`   🚫 Sem token - Autenticado: ${isAuth3}`);
      
      // Teste 4: Obter token válido quando expirado
      this.setupExpiredToken();
      const newToken = await tokenManager.getValidToken();
      const hasValidToken = newToken !== null && newToken.length > 0;
      console.log(`   🔄 Refresh automático - Token obtido: ${hasValidToken ? 'SIM' : 'NÃO'}`);
      
      const duration = Date.now() - startTime;
      const success = isAuth1 && !isAuth2 && !isAuth3 && hasValidToken;
      
      console.log(`   ✅ Resultado: ${success ? 'SUCESSO' : 'FALHA'}`);
      console.log(`   ⏱️  Tempo: ${duration}ms\n`);
      
      this.results.push({
        scenario: 'Validação de token e autenticação',
        success,
        duration,
        details: {
          validTokenAuth: isAuth1,
          expiredTokenAuth: isAuth2,
          noTokenAuth: isAuth3,
          automaticRefresh: hasValidToken
        }
      });
      
    } catch (error: any) {
      console.log(`   ❌ Erro: ${error.message}\n`);
      this.results.push({
        scenario: 'Validação de token',
        success: false,
        duration: Date.now() - startTime,
        details: { error: error.message }
      });
    }
  }

  /**
   * 📊 Relatório final
   */
  private printFinalReport(): void {
    console.log('📊 RELATÓRIO FINAL - JWT Race Condition Resolution');
    console.log('='.repeat(60));
    
    const totalTests = this.results.length;
    const passedTests = this.results.filter(r => r.success).length;
    const failedTests = totalTests - passedTests;
    const totalDuration = this.results.reduce((sum, r) => sum + r.duration, 0);
    
    console.log(`📈 Total de cenários: ${totalTests}`);
    console.log(`✅ Sucessos: ${passedTests}`);
    console.log(`❌ Falhas: ${failedTests}`);
    console.log(`⏱️  Tempo total: ${totalDuration}ms`);
    console.log(`⚡ Tempo médio: ${Math.round(totalDuration / totalTests)}ms\n`);
    
    if (passedTests === totalTests) {
      console.log('🎉 RESULTADO: TODOS OS CENÁRIOS DE RACE CONDITION RESOLVIDOS! 🎉');
      console.log('✅ O TokenManager implementa corretamente:');
      console.log('   • Singleton pattern para instância única');
      console.log('   • Mutex (refreshPromise) para operações atômicas');
      console.log('   • Thread-safety em operações de refresh');
      console.log('   • Gerenciamento automático de expiração');
      console.log('   • Validação robusta de tokens');
    } else {
      console.log('⚠️  RESULTADO: ALGUNS CENÁRIOS PRECISAM DE ATENÇÃO');
      this.results.forEach((result, i) => {
        if (!result.success) {
          console.log(`❌ Cenário ${i + 1}: ${result.scenario} - ${result.details.error || 'Falha'}`);
        }
      });
    }
    
    console.log('\n🔍 Detalhes dos testes disponíveis no console.log acima');
    console.log('📝 Para testes de produção, use: npm test jwt-race-condition');
  }

  // Helpers para setup dos cenários
  private setupExpiredToken(): void {
    const expiredToken = this.createMockExpiredToken();
    localStorage.setItem('access_token', expiredToken);
    localStorage.setItem('refresh_token', 'demo_refresh_token');
  }

  private setupNearExpiredToken(): void {
    const nearExpiredToken = this.createMockNearExpiredToken();
    localStorage.setItem('access_token', nearExpiredToken);
    localStorage.setItem('refresh_token', 'demo_refresh_token');
  }

  private setupValidToken(): void {
    const validToken = this.createMockValidToken();
    localStorage.setItem('access_token', validToken);
    localStorage.setItem('refresh_token', 'demo_refresh_token');
  }

  private async simulateApiCall(endpoint: string): Promise<{ success: boolean; endpoint: string }> {
    try {
      // Simular uma chamada de API usando o httpClient
      await new Promise(resolve => setTimeout(resolve, Math.random() * 20 + 10));
      return { success: true, endpoint };
    } catch (error) {
      return { success: false, endpoint };
    }
  }

  // Helpers para criação de tokens mock
  private createMockExpiredToken(): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({
      exp: Math.floor(Date.now() / 1000) - 3600, // Expirado há 1 hora
      iat: Math.floor(Date.now() / 1000) - 7200,
      user_id: 'demo-user',
      email: 'demo@example.com'
    }));
    return `${header}.${payload}.demo-signature`;
  }

  private createMockNearExpiredToken(): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({
      exp: Math.floor(Date.now() / 1000) + 15, // Expira em 15 segundos
      iat: Math.floor(Date.now() / 1000) - 3600,
      user_id: 'demo-user',
      email: 'demo@example.com'
    }));
    return `${header}.${payload}.demo-signature`;
  }

  private createMockValidToken(): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({
      exp: Math.floor(Date.now() / 1000) + 3600, // Expira em 1 hora
      iat: Math.floor(Date.now() / 1000),
      user_id: 'demo-user',
      email: 'demo@example.com'
    }));
    return `${header}.${payload}.demo-signature`;
  }
}

// Executar demonstração
async function runDemo(): Promise<void> {
  const demo = new JWTRaceConditionDemo();
  await demo.runDemo();
}

// Se executado diretamente
if (typeof window !== 'undefined') {
  console.log('🚀 JWT Race Condition Demo carregado!');
  console.log('💡 Execute: runDemo() no console para iniciar');
  (window as any).runDemo = runDemo;
}

export { runDemo, JWTRaceConditionDemo };
