/**
 * Script de teste para verificar o status da página de conversas
 * Execute no console do navegador para diagnóstico
 */

console.log('🔍 INICIANDO DIAGNÓSTICO DA PÁGINA CONVERSAS');
console.log('============================================');

// 1. Verificar se estamos na página correta
console.log('📍 URL atual:', window.location.href);
console.log('📍 Esperado: http://localhost:3000/conversas');

// 2. Ativar debug detalhado
localStorage.setItem('DEBUG_API', 'true');
localStorage.setItem('DEBUG_AUTH', 'true');

// 3. Verificar localStorage
console.log('\n🔍 VERIFICANDO LOCALSTORAGE:');
console.log('Token:', localStorage.getItem('auth_token') ? 'PRESENTE' : 'AUSENTE');
console.log('Token Expiry:', localStorage.getItem('token_expiry'));

// 4. Testar conectividade básica
async function testBackendConnectivity() {
  console.log('\n🌐 TESTANDO CONECTIVIDADE COM BACKEND:');
  
  const testUrls = [
    'https://wppagent-production.up.railway.app/',
    'https://wppagent-production.up.railway.app/health',
    'https://wppagent-production.up.railway.app/docs',
    'https://wppagent-production.up.railway.app/admin/login'
  ];
  
  for (const url of testUrls) {
    try {
      console.log(`📞 Testando: ${url}`);
      const response = await fetch(url, {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit'
      });
      console.log(`   ✅ Status: ${response.status} ${response.statusText}`);
    } catch (error) {
      console.log(`   ❌ Erro: ${error.message}`);
    }
  }
}

// 5. Testar API Service
async function testApiService() {
  console.log('\n🔧 TESTANDO API SERVICE:');
  
  try {
    // Verifica se apiService está disponível globalmente
    if (typeof window.apiService !== 'undefined') {
      console.log('✅ ApiService disponível globalmente');
      
      const result = await window.apiService.testConnection();
      console.log('🔬 Resultado do teste:', result);
    } else {
      console.log('❌ ApiService não está disponível globalmente');
      console.log('💡 Tentando importar dinamicamente...');
      
      // Simula chamada da API
      const testResult = await fetch('/api/test', { method: 'GET' })
        .then(r => r.json())
        .catch(e => ({ error: e.message }));
      
      console.log('📊 Resultado do teste de API:', testResult);
    }
  } catch (error) {
    console.log('❌ Erro no teste de API Service:', error);
  }
}

// 6. Verificar Console Errors
console.log('\n🚨 VERIFICANDO ERROS NO CONSOLE:');
const originalError = console.error;
console.error = function(...args) {
  console.log('🔴 ERRO CAPTURADO:', args);
  originalError.apply(console, args);
};

// 7. Executar testes
testBackendConnectivity();
testApiService();

// 8. Instruções finais
console.log('\n📋 PRÓXIMOS PASSOS:');
console.log('1. Execute este script na página /conversas');
console.log('2. Verifique os resultados dos testes acima');
console.log('3. Procure por mensagens de erro em vermelho');
console.log('4. Observe a aba Network (F12) para requisições falhas');
console.log('5. Reporte os resultados para análise');

console.log('\n🎯 DIAGNÓSTICO CONCLUÍDO');
