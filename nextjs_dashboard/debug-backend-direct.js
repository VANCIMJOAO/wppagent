#!/usr/bin/env node
/**
 * Script para debug direto do backend - descobrir endpoints e estrutura
 */

const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

async function main() {
  console.log('🔍 DEBUG DO BACKEND - DESCOBERTA DE ENDPOINTS E ESTRUTURA\n');
  
  // 1. Login
  console.log('1️⃣ FAZENDO LOGIN...');
  const loginCmd = `curl -s -X POST "https://wppagent-production.up.railway.app/admin/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "senha_admin_segura"}'`;
  
  const { stdout: loginResult } = await execAsync(loginCmd);
  const loginData = JSON.parse(loginResult);
  const token = loginData.access_token;
  
  console.log('✅ Token obtido!\n');
  
  // 2. Descobrir endpoints disponíveis via OpenAPI
  console.log('2️⃣ DESCOBRINDO ENDPOINTS DISPONÍVEIS...');
  const openApiCmd = `curl -s -H "Authorization: Bearer ${token}" \
    "https://wppagent-production.up.railway.app/openapi.json"`;
  
  const { stdout: openApiResult } = await execAsync(openApiCmd);
  const openApi = JSON.parse(openApiResult);
  
  console.log('📋 Endpoints encontrados:');
  const endpoints = Object.keys(openApi.paths);
  endpoints.forEach(endpoint => {
    const methods = Object.keys(openApi.paths[endpoint]);
    console.log(`   ${endpoint} [${methods.join(', ').toUpperCase()}]`);
  });
  
  // 3. Procurar endpoints relacionados a admin/database
  console.log('\n3️⃣ PROCURANDO ENDPOINTS DE ADMIN/DATABASE...');
  const adminEndpoints = endpoints.filter(ep => 
    ep.includes('admin') || 
    ep.includes('query') || 
    ep.includes('sql') ||
    ep.includes('database')
  );
  
  console.log('🔍 Endpoints de admin encontrados:');
  adminEndpoints.forEach(ep => console.log(`   ${ep}`));
  
  // 4. Testar endpoint de health para ver se há informações sobre DB
  console.log('\n4️⃣ TESTANDO ENDPOINT DE HEALTH...');
  try {
    const healthCmd = `curl -s -H "Authorization: Bearer ${token}" \
      "https://wppagent-production.up.railway.app/health"`;
    const { stdout: healthResult } = await execAsync(healthCmd);
    console.log('Health response:', healthResult.substring(0, 500));
  } catch (error) {
    console.log('❌ Endpoint health não disponível');
  }
  
  // 5. Procurar endpoint que liste tabelas
  console.log('\n5️⃣ TESTANDO POSSÍVEIS ENDPOINTS DE DATABASE...');
  const possibleDbEndpoints = [
    '/api/admin/tables',
    '/api/database/tables', 
    '/admin/tables',
    '/api/admin/schema',
    '/api/schema',
    '/tables',
    '/api/admin/query',
    '/admin/query'
  ];
  
  for (const endpoint of possibleDbEndpoints) {
    try {
      console.log(`🔍 Testando ${endpoint}...`);
      const testCmd = `curl -s -w "%{http_code}" -H "Authorization: Bearer ${token}" \
        "https://wppagent-production.up.railway.app${endpoint}"`;
      const { stdout: testResult } = await execAsync(testCmd);
      const statusCode = testResult.slice(-3);
      const body = testResult.slice(0, -3);
      
      console.log(`   Status: ${statusCode}`);
      if (statusCode === '200') {
        console.log(`   ✅ Endpoint funcional! Response: ${body.substring(0, 200)}...`);
      } else if (statusCode === '404') {
        console.log(`   ❌ Não encontrado`);
      } else {
        console.log(`   ⚠️ Status ${statusCode}: ${body.substring(0, 100)}...`);
      }
    } catch (error) {
      console.log(`   ❌ Erro: ${error.message}`);
    }
  }
  
  // 6. Ver se existe endpoint para executar SQL diretamente
  console.log('\n6️⃣ PROCURANDO ENDPOINT PARA EXECUTAR SQL...');
  
  // Testar alguns payloads comuns
  const sqlPayloads = [
    {
      method: 'POST',
      endpoint: '/api/admin/execute',
      payload: { sql: 'SELECT table_name FROM information_schema.tables LIMIT 5;' }
    },
    {
      method: 'POST', 
      endpoint: '/admin/execute',
      payload: { query: 'SELECT table_name FROM information_schema.tables LIMIT 5;' }
    },
    {
      method: 'GET',
      endpoint: '/api/admin/tables',
      payload: null
    }
  ];
  
  for (const test of sqlPayloads) {
    try {
      console.log(`🧪 Testando ${test.method} ${test.endpoint}...`);
      
      let cmd;
      if (test.method === 'POST' && test.payload) {
        cmd = `curl -s -w "%{http_code}" -X POST \
          -H "Authorization: Bearer ${token}" \
          -H "Content-Type: application/json" \
          -d '${JSON.stringify(test.payload)}' \
          "https://wppagent-production.up.railway.app${test.endpoint}"`;
      } else {
        cmd = `curl -s -w "%{http_code}" -H "Authorization: Bearer ${token}" \
          "https://wppagent-production.up.railway.app${test.endpoint}"`;
      }
      
      const { stdout: result } = await execAsync(cmd);
      const statusCode = result.slice(-3);
      const body = result.slice(0, -3);
      
      console.log(`   Status: ${statusCode}`);
      if (statusCode === '200') {
        console.log(`   🎉 SUCESSO! Response: ${body.substring(0, 300)}...`);
        
        // Tentar parsear como JSON
        try {
          const jsonResult = JSON.parse(body);
          console.log(`   📊 Dados estruturados recebidos!`);
          if (Array.isArray(jsonResult)) {
            console.log(`   📋 Array com ${jsonResult.length} itens`);
          } else {
            console.log(`   📝 Objeto com chaves: ${Object.keys(jsonResult).join(', ')}`);
          }
        } catch (parseError) {
          console.log(`   📄 Resposta em texto simples`);
        }
      }
    } catch (error) {
      console.log(`   ❌ Erro: ${error.message}`);
    }
  }
  
  // 7. Tentar descobrir estrutura via logs/debug endpoints
  console.log('\n7️⃣ PROCURANDO ENDPOINTS DE DEBUG/LOGS...');
  const debugEndpoints = [
    '/api/debug',
    '/debug', 
    '/api/admin/debug',
    '/admin/debug',
    '/api/logs',
    '/logs',
    '/api/status',
    '/status'
  ];
  
  for (const endpoint of debugEndpoints) {
    try {
      console.log(`🔍 ${endpoint}...`);
      const cmd = `curl -s -w "%{http_code}" -H "Authorization: Bearer ${token}" \
        "https://wppagent-production.up.railway.app${endpoint}"`;
      const { stdout: result } = await execAsync(cmd);
      const statusCode = result.slice(-3);
      
      if (statusCode === '200') {
        const body = result.slice(0, -3);
        console.log(`   ✅ Disponível! ${body.substring(0, 150)}...`);
      }
    } catch (error) {
      // Silent fail
    }
  }
  
  // 8. Gerar relatório final
  console.log('\n📊 RELATÓRIO FINAL DE DESCOBERTA:');
  console.log('================================');
  
  const report = {
    timestamp: new Date().toISOString(),
    login_status: 'SUCCESS',
    total_endpoints: endpoints.length,
    admin_endpoints: adminEndpoints,
    recommendations: [
      'Backend tem ' + endpoints.length + ' endpoints disponíveis',
      'Verificar se existe endpoint para executar SQL diretamente',
      'Considerar acessar Railway CLI para conectar diretamente no PostgreSQL',
      'Aplicar correção SQL manual no código backend'
    ],
    sql_fix: `
-- CORREÇÃO PRINCIPAL: Usar aliases específicos
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    0 as revenue, -- Temporário até descobrir campo correto
    COUNT(DISTINCT u.id) as new_clients
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id AND c.created_at >= $1
LEFT JOIN messages m ON u.id = m.user_id AND m.created_at >= $1
LEFT JOIN appointments a ON u.id = a.user_id AND a.created_at >= $1
WHERE u.created_at >= $1
    AND u.nome IS NOT NULL 
    AND u.nome != ''
    AND u.nome NOT LIKE '%[DELETED]%'
GROUP BY EXTRACT(YEAR FROM u.created_at), EXTRACT(MONTH FROM u.created_at)
ORDER BY year DESC, month DESC
LIMIT $2;
    `.trim()
  };
  
  require('fs').writeFileSync('backend-discovery-report.json', JSON.stringify(report, null, 2));
  
  console.log('✅ Endpoints mapeados');
  console.log('✅ Relatório salvo em: backend-discovery-report.json');
  console.log('\n💡 PRÓXIMAS AÇÕES:');
  console.log('1. Usar Railway CLI para conectar diretamente no PostgreSQL');
  console.log('2. Executar: railway db connect');
  console.log('3. Verificar estrutura: \\d+ appointments');  
  console.log('4. Aplicar correção SQL no código backend');
  console.log('\n📋 OU ALTERNATIVA RÁPIDA:');
  console.log('Aplicar a query corrigida diretamente no arquivo Python do backend que contém a query problemática.');
}

if (require.main === module) {
  main().catch(console.error);
}
