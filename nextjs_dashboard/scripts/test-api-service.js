#!/usr/bin/env node

/**
 * 🧪 Script de teste para API Service Corrigido
 * =============================================
 * 
 * Testa a conectividade, autenticação e endpoints do API Service
 * 
 * Uso: node scripts/test-api-service.js
 */

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🚀 Iniciando testes do API Service...\n');

// Configurações
const API_BASE_URL = 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'senha_admin_segura';

// Função para fazer requisições HTTP básicas
async function makeRequest(url, options = {}) {
  const { default: fetch } = await import('node-fetch');
  
  return await fetch(url, {
    mode: 'cors',
    credentials: 'omit',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Access-Control-Allow-Origin': '*',
      ...options.headers
    },
    ...options
  });
}

// Teste 1: Conectividade básica
async function testConnectivity() {
  console.log('🔍 Teste 1: Conectividade básica');
  console.log('================================\n');
  
  try {
    console.log(`📡 Testando conectividade com: ${API_BASE_URL}`);
    
    // Testar endpoint de health (se existir)
    try {
      const healthResponse = await makeRequest(`${API_BASE_URL}/health`);
      console.log(`✅ Health endpoint: ${healthResponse.status} ${healthResponse.statusText}`);
    } catch (error) {
      console.log(`⚠️  Health endpoint não disponível: ${error.message}`);
    }
    
    // Testar conectividade básica
    try {
      const basicResponse = await makeRequest(API_BASE_URL);
      console.log(`✅ Conectividade básica: ${basicResponse.status} ${basicResponse.statusText}`);
      return true;
    } catch (error) {
      console.error(`❌ Falha na conectividade básica: ${error.message}`);
      return false;
    }
    
  } catch (error) {
    console.error(`❌ Erro geral de conectividade: ${error.message}`);
    return false;
  }
}

// Teste 2: Autenticação
async function testAuthentication() {
  console.log('\n🔐 Teste 2: Autenticação');
  console.log('========================\n');
  
  try {
    console.log(`👤 Tentando login com usuário: ${ADMIN_USERNAME}`);
    console.log(`📡 URL: ${API_BASE_URL}/admin/login`);
    
    const response = await makeRequest(`${API_BASE_URL}/admin/login`, {
      method: 'POST',
      body: JSON.stringify({
        username: ADMIN_USERNAME,
        password: ADMIN_PASSWORD
      })
    });
    
    console.log(`📊 Status: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ Falha na autenticação:`, {
        status: response.status,
        body: errorText.substring(0, 200) + (errorText.length > 200 ? '...' : '')
      });
      
      // Sugestões baseadas no status
      if (response.status === 401) {
        console.log('💡 Sugestão: Verifique se as credenciais estão corretas');
      } else if (response.status === 404) {
        console.log('💡 Sugestão: Endpoint de login pode estar em /auth/login ou /login');
      } else if (response.status === 500) {
        console.log('💡 Sugestão: Verifique os logs do servidor backend');
      }
      
      return null;
    }
    
    const data = await response.json();
    
    if (data.access_token) {
      console.log('✅ Login bem sucedido!');
      console.log(`🔑 Token recebido: ${data.access_token.substring(0, 20)}...`);
      
      // Decodificar JWT para informações
      try {
        const payload = JSON.parse(Buffer.from(data.access_token.split('.')[1], 'base64').toString());
        console.log('📋 Informações do token:');
        console.log(`   - Usuário: ${payload.sub || payload.username || 'N/A'}`);
        console.log(`   - Expira em: ${new Date(payload.exp * 1000).toLocaleString()}`);
        console.log(`   - Emitido em: ${new Date(payload.iat * 1000).toLocaleString()}`);
      } catch (e) {
        console.log('⚠️  Não foi possível decodificar JWT');
      }
      
      return data.access_token;
    } else {
      console.error('❌ Token não encontrado na resposta');
      return null;
    }
    
  } catch (error) {
    console.error(`❌ Erro na autenticação: ${error.message}`);
    return null;
  }
}

// Teste 3: Endpoints com token
async function testEndpoints(token) {
  if (!token) {
    console.log('\n⏭️  Pulando teste de endpoints (sem token)');
    return;
  }
  
  console.log('\n🛠️  Teste 3: Endpoints da API');
  console.log('===============================\n');
  
  const endpoints = [
    '/api/dashboard/conversations',
    '/conversations/',
    '/admin/conversations/',
    '/api/dashboard/stats',
    '/dashboard/stats',
    '/stats'
  ];
  
  const workingEndpoints = [];
  
  for (const endpoint of endpoints) {
    try {
      console.log(`🔍 Testando: ${endpoint}`);
      
      const response = await makeRequest(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log(`   Status: ${response.status}`);
      
      if (response.ok) {
        console.log(`   ✅ Funcionando`);
        workingEndpoints.push(endpoint);
        
        // Tentar parsear resposta para ver estrutura
        try {
          const data = await response.json();
          const keys = Object.keys(data);
          console.log(`   📋 Chaves da resposta: ${keys.slice(0, 5).join(', ')}${keys.length > 5 ? '...' : ''}`);
        } catch (e) {
          console.log(`   📄 Resposta não é JSON válido`);
        }
      } else {
        console.log(`   ❌ Status: ${response.status}`);
      }
      
    } catch (error) {
      console.log(`   ❌ Erro: ${error.message}`);
    }
    
    console.log(''); // Linha em branco
  }
  
  console.log(`📊 Resumo: ${workingEndpoints.length}/${endpoints.length} endpoints funcionando`);
  if (workingEndpoints.length > 0) {
    console.log('✅ Endpoints funcionais:');
    workingEndpoints.forEach(ep => console.log(`   - ${ep}`));
  }
  
  return workingEndpoints;
}

// Teste 4: Validação do TypeScript (se possível)
async function testTypeScript() {
  console.log('\n🔧 Teste 4: Validação TypeScript');
  console.log('=================================\n');
  
  return new Promise((resolve) => {
    // Verificar se o arquivo existe
    const apiServicePath = path.join(__dirname, '../lib/api-service.ts');
    
    if (!fs.existsSync(apiServicePath)) {
      console.log('❌ Arquivo api-service.ts não encontrado');
      resolve(false);
      return;
    }
    
    console.log('📁 Arquivo api-service.ts encontrado');
    
    // Tentar compilar TypeScript
    exec('npx tsc --noEmit --skipLibCheck lib/api-service.ts', (error, stdout, stderr) => {
      if (error) {
        console.log('❌ Erros de TypeScript encontrados:');
        console.log(stderr);
        resolve(false);
      } else {
        console.log('✅ Validação TypeScript passou');
        resolve(true);
      }
    });
  });
}

// Função principal
async function runAllTests() {
  console.log('🧪 RELATÓRIO DE TESTES - API SERVICE CORRIGIDO');
  console.log('='.repeat(50));
  console.log(`Data: ${new Date().toLocaleString()}`);
  console.log(`Backend: ${API_BASE_URL}`);
  console.log('='.repeat(50));
  
  const results = {
    connectivity: false,
    authentication: false,
    endpoints: [],
    typescript: false
  };
  
  // Executar testes
  results.connectivity = await testConnectivity();
  const token = await testAuthentication();
  results.authentication = !!token;
  results.endpoints = await testEndpoints(token) || [];
  results.typescript = await testTypeScript();
  
  // Relatório final
  console.log('\n📊 RELATÓRIO FINAL');
  console.log('==================\n');
  
  console.log(`🌐 Conectividade: ${results.connectivity ? '✅ OK' : '❌ FALHOU'}`);
  console.log(`🔐 Autenticação: ${results.authentication ? '✅ OK' : '❌ FALHOU'}`);
  console.log(`🛠️  Endpoints: ${results.endpoints.length > 0 ? `✅ ${results.endpoints.length} funcionando` : '❌ Nenhum funcionando'}`);
  console.log(`🔧 TypeScript: ${results.typescript ? '✅ OK' : '⚠️  Com problemas'}`);
  
  // Pontuação geral
  const score = [
    results.connectivity,
    results.authentication, 
    results.endpoints.length > 0,
    results.typescript
  ].filter(Boolean).length;
  
  console.log(`\n🎯 Pontuação geral: ${score}/4`);
  
  if (score === 4) {
    console.log('🎉 Todos os testes passaram! API Service está funcionando perfeitamente.');
  } else if (score >= 2) {
    console.log('⚠️  Alguns problemas encontrados, mas funcionalidade básica OK.');
  } else {
    console.log('❌ Problemas significativos encontrados. Revisar configuração.');
  }
  
  // Próximos passos
  console.log('\n🚀 PRÓXIMOS PASSOS:');
  if (!results.connectivity) {
    console.log('1. Verificar se o backend está rodando');
    console.log('2. Verificar URL do backend');
    console.log('3. Verificar configurações de firewall/rede');
  }
  if (!results.authentication) {
    console.log('1. Verificar credenciais de admin');
    console.log('2. Verificar endpoint de login');
    console.log('3. Verificar configuração CORS no backend');
  }
  if (results.endpoints.length === 0 && results.authentication) {
    console.log('1. Verificar rotas disponíveis no backend');
    console.log('2. Verificar permissões do usuário admin');
    console.log('3. Verificar logs do backend para erros');
  }
  if (!results.typescript) {
    console.log('1. Verificar imports dos tipos');
    console.log('2. Verificar se lib/debug.ts existe');
    console.log('3. Verificar se types/api.ts está atualizado');
  }
  
  console.log('\n✨ Teste concluído!');
}

// Executar se chamado diretamente
if (require.main === module) {
  runAllTests().catch(error => {
    console.error('💥 Erro fatal nos testes:', error);
    process.exit(1);
  });
}

module.exports = { runAllTests, testConnectivity, testAuthentication, testEndpoints };