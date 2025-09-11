#!/usr/bin/env node

/**
 * 🔍 Discovery Script - Descobre endpoints disponíveis na API
 * ===========================================================
 * 
 * Este script explora a API para descobrir quais endpoints estão disponíveis
 * e quais métodos HTTP cada um aceita.
 */

const { exec } = require('child_process');

console.log('🔍 DESCOBRINDO ESTRUTURA DA API...\n');

// Configurações
const API_BASE_URL = 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'senha_admin_segura';

let authToken = null;

async function makeRequest(url, options = {}) {
  const { default: fetch } = await import('node-fetch');
  
  return await fetch(url, {
    mode: 'cors',
    credentials: 'omit',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers
    },
    ...options
  });
}

// Fazer login para obter token
async function authenticate() {
  console.log('🔑 Fazendo login...');
  
  const response = await makeRequest(`${API_BASE_URL}/admin/login`, {
    method: 'POST',
    body: JSON.stringify({
      username: ADMIN_USERNAME,
      password: ADMIN_PASSWORD
    })
  });
  
  if (!response.ok) {
    throw new Error(`Login falhou: ${response.status}`);
  }
  
  const data = await response.json();
  authToken = data.access_token;
  console.log('✅ Login bem sucedido\n');
  
  return authToken;
}

// Descobrir endpoints
async function discoverEndpoints() {
  const token = await authenticate();
  
  console.log('🌍 TESTANDO ENDPOINTS COMUNS...\n');
  
  // Lista de endpoints para testar com diferentes métodos
  const endpointsToTest = [
    // Dashboard endpoints
    '/api/dashboard/stats',
    '/api/dashboard/conversations',
    '/api/dashboard/clients',
    '/api/dashboard/appointments',
    '/api/dashboard/recent-activity',
    
    // Direct endpoints
    '/conversations',
    '/clients',
    '/appointments',
    '/messages',
    '/users',
    '/stats',
    '/health',
    
    // Admin endpoints
    '/admin/conversations',
    '/admin/clients',
    '/admin/appointments',
    '/admin/stats',
    
    // Other possibilities
    '/api/conversations',
    '/api/clients',
    '/api/appointments',
    '/api/messages',
    '/api/users',
    '/api/stats'
  ];
  
  const methods = ['GET', 'POST'];
  const workingEndpoints = [];
  
  for (const endpoint of endpointsToTest) {
    console.log(`🔍 Testando: ${endpoint}`);
    
    for (const method of methods) {
      try {
        const response = await makeRequest(`${API_BASE_URL}${endpoint}`, {
          method: method,
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        const statusText = `${method} ${response.status}`;
        
        if (response.ok) {
          console.log(`   ✅ ${statusText} - FUNCIONANDO`);
          workingEndpoints.push({ 
            endpoint, 
            method, 
            status: response.status,
            working: true
          });
          
          // Tentar ver o formato da resposta
          try {
            const data = await response.json();
            const keys = Object.keys(data).slice(0, 5);
            console.log(`      📋 Estrutura: {${keys.join(', ')}}${Object.keys(data).length > 5 ? '...' : ''}`);
            
            // Se for uma lista, mostrar quantos items
            if (Array.isArray(data)) {
              console.log(`      📊 Array com ${data.length} items`);
            } else if (data.items && Array.isArray(data.items)) {
              console.log(`      📊 ${data.items.length} items, total: ${data.total || 'N/A'}`);
            } else if (data.conversations && Array.isArray(data.conversations)) {
              console.log(`      💬 ${data.conversations.length} conversas, total: ${data.total || 'N/A'}`);
            } else if (data.appointments && Array.isArray(data.appointments)) {
              console.log(`      📅 ${data.appointments.length} agendamentos, total: ${data.total || 'N/A'}`);
            }
          } catch (e) {
            console.log(`      📄 Resposta não é JSON`);
          }
        } else if (response.status === 405) {
          console.log(`   ⚠️  ${statusText} - Método não permitido`);
        } else if (response.status === 404) {
          console.log(`   ❌ ${statusText} - Não encontrado`);
          break; // Se GET 404, não testar POST
        } else if (response.status === 401) {
          console.log(`   🔒 ${statusText} - Não autorizado (token pode ter expirado)`);
        } else if (response.status === 422) {
          console.log(`   📝 ${statusText} - Dados inválidos (normal para POST sem body)`);
        } else {
          console.log(`   ❌ ${statusText} - ${response.statusText}`);
        }
      } catch (error) {
        console.log(`   💥 ${method} ERRO - ${error.message}`);
      }
    }
    
    console.log(''); // Linha em branco
  }
  
  return workingEndpoints;
}

// Função para testar estruturas específicas descobertas
async function testSpecificStructures(workingEndpoints) {
  console.log('\n🧪 TESTANDO ESTRUTURAS ESPECÍFICAS...\n');
  
  const token = authToken;
  
  // Testar endpoints que funcionaram com parâmetros específicos
  for (const { endpoint, method } of workingEndpoints.filter(ep => ep.working)) {
    console.log(`🔍 Testando ${method} ${endpoint} com parâmetros...`);
    
    // Tentar com parâmetros de paginação
    if (method === 'GET') {
      try {
        const withParams = `${endpoint}${endpoint.includes('?') ? '&' : '?'}limit=5&offset=0`;
        const response = await makeRequest(`${API_BASE_URL}${withParams}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          console.log(`   ✅ Com paginação: OK`);
          const data = await response.json();
          
          // Analisar estrutura mais detalhada
          if (endpoint.includes('conversation')) {
            console.log(`      💬 Formato de conversa detectado`);
            if (data.conversations && data.conversations[0]) {
              const conv = data.conversations[0];
              console.log(`         Campos: ${Object.keys(conv).join(', ')}`);
            }
          } else if (endpoint.includes('client')) {
            console.log(`      👤 Formato de cliente detectado`);
            if (data.clients && data.clients[0]) {
              const client = data.clients[0];
              console.log(`         Campos: ${Object.keys(client).join(', ')}`);
            }
          } else if (endpoint.includes('appointment')) {
            console.log(`      📅 Formato de agendamento detectado`);
            if (data.appointments && data.appointments[0]) {
              const apt = data.appointments[0];
              console.log(`         Campos: ${Object.keys(apt).join(', ')}`);
            }
          } else if (endpoint.includes('stats')) {
            console.log(`      📊 Formato de estatísticas detectado`);
            console.log(`         Campos: ${Object.keys(data).join(', ')}`);
          }
        } else {
          console.log(`   ❌ Com paginação: ${response.status}`);
        }
      } catch (error) {
        console.log(`   💥 Erro com parâmetros: ${error.message}`);
      }
    }
    
    console.log('');
  }
}

// Função principal
async function runDiscovery() {
  try {
    console.log('🔍 DISCOVERY DA API - WPPAgent Backend');
    console.log('='.repeat(50));
    console.log(`Backend: ${API_BASE_URL}`);
    console.log(`Data: ${new Date().toLocaleString()}`);
    console.log('='.repeat(50));
    
    const workingEndpoints = await discoverEndpoints();
    
    console.log('\n📊 RESUMO DOS ENDPOINTS FUNCIONAIS');
    console.log('='.repeat(40));
    
    if (workingEndpoints.length === 0) {
      console.log('❌ Nenhum endpoint funcionou');
    } else {
      console.log(`✅ ${workingEndpoints.length} endpoints funcionando:\n`);
      
      workingEndpoints.forEach(ep => {
        console.log(`   ${ep.method} ${ep.endpoint} - Status ${ep.status}`);
      });
    }
    
    // Testar estruturas específicas se encontramos endpoints
    if (workingEndpoints.length > 0) {
      await testSpecificStructures(workingEndpoints);
    }
    
    // Gerar recomendações
    console.log('\n🚀 RECOMENDAÇÕES PARA O API SERVICE:');
    console.log('='.repeat(45));
    
    if (workingEndpoints.length === 0) {
      console.log('1. Verificar se o backend está funcionando corretamente');
      console.log('2. Verificar documentação da API para endpoints corretos');
      console.log('3. Usar dados mock até resolver problema no backend');
    } else {
      console.log('1. Usar apenas os endpoints que funcionaram:');
      workingEndpoints.forEach(ep => {
        console.log(`   - ${ep.method} ${ep.endpoint}`);
      });
      
      console.log('\n2. Implementar fallback para dados mock quando endpoints falharem');
      console.log('3. Usar estrutura de dados descoberta para TypeScript types');
      console.log('4. Implementar cache local para reduzir chamadas à API');
    }
    
    console.log('\n✨ Discovery concluído!');
    
  } catch (error) {
    console.error('💥 Erro durante discovery:', error);
    process.exit(1);
  }
}

// Executar se chamado diretamente
if (require.main === module) {
  runDiscovery();
}

module.exports = { runDiscovery, discoverEndpoints };