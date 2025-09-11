/**
 * 🧪 TESTE DA API CORRIGIDA
 * ========================
 */

const API_BASE_URL = 'https://wppagent-production.up.railway.app';

async function testCorrectedAPI() {
  console.log('🧪 TESTE DA API CORRIGIDA');
  console.log('========================');
  console.log('');
  
  try {
    // Teste 1: Saúde do backend
    console.log('1️⃣ Testando conectividade...');
    const healthResponse = await fetch(`${API_BASE_URL}/health`);
    console.log(`   Status: ${healthResponse.status} ${healthResponse.statusText}`);
    
    if (healthResponse.ok) {
      console.log('   ✅ Backend acessível');
    } else {
      console.log('   ❌ Backend não acessível');
      return;
    }
    
    // Teste 2: Autenticação
    console.log('');
    console.log('2️⃣ Testando autenticação...');
    
    const authResponse = await fetch(`${API_BASE_URL}/admin/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'senha_admin_segura'
      }),
    });
    
    console.log(`   Status: ${authResponse.status} ${authResponse.statusText}`);
    
    if (authResponse.ok) {
      const authData = await authResponse.json();
      console.log('   ✅ Autenticação funcionando');
      console.log('   🔑 Token obtido com sucesso');
      
      const token = authData.access_token;
      
      // Teste 3: Endpoints com token
      console.log('');
      console.log('3️⃣ Testando endpoints com autenticação...');
      
      const endpointsToTest = [
        '/api/conversations',
        '/conversations', 
        '/api/clients',
        '/clients',
        '/api/appointments',
        '/appointments',
        '/api/dashboard/stats',
        '/dashboard/stats',
        '/admin/stats'
      ];
      
      let workingEndpoints = [];
      
      for (const endpoint of endpointsToTest) {
        try {
          const testResponse = await fetch(`${API_BASE_URL}${endpoint}?limit=5`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            }
          });
          
          if (testResponse.ok) {
            workingEndpoints.push(endpoint);
            console.log(`   ✅ ${endpoint} - Status: ${testResponse.status}`);
          } else {
            console.log(`   ❌ ${endpoint} - Status: ${testResponse.status} ${testResponse.statusText}`);
          }
        } catch (error) {
          console.log(`   💥 ${endpoint} - Erro: ${error.message}`);
        }
      }
      
      console.log('');
      console.log('📊 RESUMO DO TESTE');
      console.log('=================');
      console.log(`✅ Endpoints funcionando: ${workingEndpoints.length}`);
      console.log(`❌ Endpoints com problema: ${endpointsToTest.length - workingEndpoints.length}`);
      
      if (workingEndpoints.length > 0) {
        console.log('');
        console.log('✅ ENDPOINTS FUNCIONAIS:');
        workingEndpoints.forEach(ep => console.log(`   • ${ep}`));
      }
      
      console.log('');
      console.log('🎯 PRÓXIMOS PASSOS:');
      console.log('==================');
      console.log('1. Iniciar o servidor de desenvolvimento: npm run dev');
      console.log('2. Abrir http://localhost:3000 no navegador');
      console.log('3. Verificar console do navegador para logs detalhados');
      console.log('4. A API corrigida tentará múltiplos endpoints automaticamente');
      console.log('5. Se alguns endpoints não funcionarem, dados mock serão usados');
      
    } else {
      console.log('   ❌ Falha na autenticação');
      const errorText = await authResponse.text();
      console.log(`   Erro: ${errorText}`);
    }
    
  } catch (error) {
    console.error('💥 Erro geral no teste:', error);
  }
}

// Executar teste
testCorrectedAPI();
