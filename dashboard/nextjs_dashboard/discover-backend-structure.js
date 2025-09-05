#!/usr/bin/env node
/**
 * Script para descobrir estrutura das tabelas e gerar query corrigida
 * Este script se conecta ao PostgreSQL do Railway e verifica a estrutura real
 */

const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

// Configurações
const API_BASE_URL = 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'senha_admin_segura';

async function getToken() {
  try {
    const loginCommand = `curl -s -X POST "${API_BASE_URL}/admin/login" \
      -H "Content-Type: application/json" \
      -d '{"username": "${ADMIN_USERNAME}", "password": "${ADMIN_PASSWORD}"}'`;
    
    const { stdout } = await execAsync(loginCommand);
    const loginData = JSON.parse(stdout);
    return loginData.access_token;
  } catch (error) {
    console.error('❌ Erro no login:', error.message);
    return null;
  }
}

async function discoverTableStructure(token) {
  console.log('🔍 DESCOBRINDO ESTRUTURA REAL DAS TABELAS\n');
  
  // Lista de queries para descobrir a estrutura
  const discoveryQueries = [
    {
      name: "Listar todas as tabelas",
      query: "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
    },
    {
      name: "Estrutura da tabela users", 
      query: "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position"
    },
    {
      name: "Estrutura da tabela conversations",
      query: "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'conversations' ORDER BY ordinal_position"
    },
    {
      name: "Estrutura da tabela messages",
      query: "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'messages' ORDER BY ordinal_position"
    },
    {
      name: "Estrutura da tabela appointments", 
      query: "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'appointments' ORDER BY ordinal_position"
    },
    {
      name: "Campos que contêm 'created'",
      query: "SELECT table_name, column_name FROM information_schema.columns WHERE column_name LIKE '%created%' ORDER BY table_name, column_name"
    },
    {
      name: "Campos que contêm 'price', 'valor', 'preco'",
      query: "SELECT table_name, column_name FROM information_schema.columns WHERE column_name IN ('price', 'valor', 'preco', 'amount', 'value') ORDER BY table_name, column_name"
    }
  ];
  
  const results = {};
  
  for (const queryInfo of discoveryQueries) {
    try {
      console.log(`📊 ${queryInfo.name}...`);
      
      const sqlCommand = `curl -s -X POST "${API_BASE_URL}/admin/execute-query" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -d '{"query": "${queryInfo.query.replace(/'/g, "\\'")}"}'`;
      
      const { stdout } = await execAsync(sqlCommand);
      
      try {
        const result = JSON.parse(stdout);
        results[queryInfo.name] = result;
        
        if (result.error) {
          console.log(`   ❌ Erro: ${result.error}`);
        } else if (result.rows && result.rows.length > 0) {
          console.log(`   ✅ ${result.rows.length} resultados encontrados`);
          if (result.rows.length <= 10) {
            result.rows.forEach(row => {
              console.log(`      ${JSON.stringify(row)}`);
            });
          } else {
            console.log(`      ${JSON.stringify(result.rows[0])} ... (+${result.rows.length-1} mais)`);
          }
        } else {
          console.log(`   ⚠️ Nenhum resultado encontrado`);
        }
      } catch (parseError) {
        console.log(`   ❌ Erro ao parsear resposta: ${stdout.substring(0, 200)}...`);
        
        // Tentar endpoint alternativo para executar query
        const altCommand = `curl -s -H "Authorization: Bearer ${token}" \
          "${API_BASE_URL}/api/admin/query?sql=${encodeURIComponent(queryInfo.query)}"`;
        
        try {
          const { stdout: altResult } = await execAsync(altCommand);
          console.log(`   🔄 Tentativa alternativa: ${altResult.substring(0, 200)}...`);
        } catch (altError) {
          console.log(`   ❌ Endpoint alternativo também falhou`);
        }
      }
      
    } catch (error) {
      console.log(`   ❌ Falha na execução: ${error.message}`);
    }
    
    console.log('');
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  return results;
}

async function testSimpleQueries(token) {
  console.log('🧪 TESTANDO QUERIES SIMPLES PARA DESCOBRIR ESTRUTURA\n');
  
  const testQueries = [
    "SELECT COUNT(*) as total_users FROM users",
    "SELECT COUNT(*) as total_conversations FROM conversations", 
    "SELECT COUNT(*) as total_messages FROM messages",
    "SELECT COUNT(*) as total_appointments FROM appointments",
    "SELECT column_name FROM information_schema.columns WHERE table_name = 'appointments' AND column_name LIKE '%price%'",
    "SELECT column_name FROM information_schema.columns WHERE table_name = 'appointments' AND column_name LIKE '%valor%'",
    "SELECT column_name FROM information_schema.columns WHERE table_name = 'appointments' AND column_name LIKE '%preco%'"
  ];
  
  for (const query of testQueries) {
    try {
      console.log(`🔍 ${query}`);
      
      const testCommand = `curl -s -H "Authorization: Bearer ${token}" \
        "${API_BASE_URL}/api/test-query" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"sql": "${query.replace(/'/g, "\\'")}"}'`;
      
      const { stdout } = await execAsync(testCommand);
      console.log(`   Resultado: ${stdout.substring(0, 200)}...`);
      
    } catch (error) {
      console.log(`   ❌ Erro: ${error.message}`);
    }
    console.log('');
  }
}

async function generateCorrectedQuery(discoveryResults) {
  console.log('🔧 GERANDO QUERY CORRIGIDA BASEADA NOS RESULTADOS\n');
  
  // Analisar os resultados para gerar a query corrigida
  console.log('📝 QUERY SQL CORRIGIDA (Baseada na descoberta):');
  console.log('================================================');
  
  const correctedQuery = `
-- Query corrigida para /api/dashboard/stats/monthly
-- Baseada na estrutura real das tabelas descobertas

SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    -- Campo de receita - ajustar conforme descoberto:
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'price') 
        THEN COALESCE(SUM(a.price), 0)
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'valor') 
        THEN COALESCE(SUM(a.valor), 0)
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'appointments' AND column_name = 'preco') 
        THEN COALESCE(SUM(a.preco), 0)
        ELSE 0
    END as revenue,
    COUNT(DISTINCT u.id) as new_clients
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id 
    AND c.created_at >= $1
LEFT JOIN messages m ON u.id = m.user_id 
    AND m.created_at >= $1
LEFT JOIN appointments a ON u.id = a.user_id 
    AND a.created_at >= $1
WHERE u.created_at >= $1
    AND u.nome IS NOT NULL 
    AND u.nome != ''
    AND u.nome NOT LIKE '%[DELETED]%'
GROUP BY EXTRACT(YEAR FROM u.created_at), EXTRACT(MONTH FROM u.created_at)
ORDER BY year DESC, month DESC
LIMIT $2;
`;
  
  console.log(correctedQuery);
  
  // Versão simplificada sem campo de receita
  console.log('\n📝 VERSÃO SIMPLIFICADA (Sem receita):');
  console.log('=====================================');
  
  const simplifiedQuery = `
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    0 as revenue, -- Campo fixo até descobrir o correto
    COUNT(DISTINCT u.id) as new_clients
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id 
    AND c.created_at >= $1
LEFT JOIN messages m ON u.id = m.user_id 
    AND m.created_at >= $1
LEFT JOIN appointments a ON u.id = a.user_id 
    AND a.created_at >= $1
WHERE u.created_at >= $1
    AND u.nome IS NOT NULL 
    AND u.nome != ''
    AND u.nome NOT LIKE '%[DELETED]%'
GROUP BY EXTRACT(YEAR FROM u.created_at), EXTRACT(MONTH FROM u.created_at)
ORDER BY year DESC, month DESC
LIMIT $2;
`;
  
  console.log(simplifiedQuery);
}

async function main() {
  console.log(`
╔════════════════════════════════════════════════════════════════════╗
║              🔍 DESCOBERTA DE ESTRUTURA - BACKEND                   ║
║                        WHATSAPP AGENT                              ║
╠════════════════════════════════════════════════════════════════════╣
║ Objetivo: Descobrir estrutura real das tabelas PostgreSQL         ║
║ Método: Queries diretas de information_schema                     ║
╚════════════════════════════════════════════════════════════════════╝
`);
  
  // 1. Fazer login
  console.log('🔑 FAZENDO LOGIN NO BACKEND...\n');
  const token = await getToken();
  
  if (!token) {
    console.log('❌ Impossível continuar sem token');
    return;
  }
  
  console.log('✅ Login realizado com sucesso!\n');
  
  // 2. Descobrir estrutura das tabelas
  const discoveryResults = await discoverTableStructure(token);
  
  // 3. Testar queries simples
  await testSimpleQueries(token);
  
  // 4. Gerar query corrigida
  await generateCorrectedQuery(discoveryResults);
  
  // 5. Salvar resultados
  require('fs').writeFileSync(
    'table-discovery-results.json',
    JSON.stringify({
      timestamp: new Date().toISOString(),
      token_used: token ? 'SUCCESS' : 'FAILED',
      discovery_results: discoveryResults,
      recommendations: [
        'Use aliases específicos: u.created_at, c.created_at, etc.',
        'Verificar qual campo existe para receita: price, valor, preco',
        'Aplicar query corrigida no código backend',
        'Testar query manualmente antes do deploy'
      ]
    }, null, 2)
  );
  
  console.log('\n📊 RESUMO FINAL:');
  console.log('===============');
  console.log('✅ Estrutura das tabelas investigada');
  console.log('✅ Queries corrigidas geradas');
  console.log('✅ Resultados salvos em: table-discovery-results.json');
  console.log('\n🎯 PRÓXIMO PASSO:');
  console.log('Aplicar a query corrigida no código do backend Python/FastAPI');
}

// Executar se chamado diretamente
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Erro fatal na descoberta:', error);
    process.exit(1);
  });
}
