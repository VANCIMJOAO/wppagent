#!/usr/bin/env node
/**
 * Script específico para analisar e sugerir correções para erros SQL
 */

const fetch = require('node-fetch');

// Configurações
const API_BASE_URL = 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'senha_admin_segura';

async function login() {
  const response = await fetch(`${API_BASE_URL}/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: ADMIN_USERNAME,
      password: ADMIN_PASSWORD,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Login failed: ${response.status}`);
  }
  
  const data = await response.json();
  return data.access_token;
}

async function analyzeSQL() {
  console.log('🔍 ANÁLISE DE ERROS SQL - BACKEND');
  console.log('=====================================\n');
  
  try {
    const token = await login();
    console.log('✅ Login realizado com sucesso\n');
    
    // Testar endpoint problemático
    console.log('📊 Testando endpoint com erro SQL...');
    const response = await fetch(`${API_BASE_URL}/api/dashboard/stats/monthly`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    const errorText = await response.text();
    
    if (response.status === 500 && errorText.includes('AmbiguousColumnError')) {
      console.log('❌ ERRO SQL CONFIRMADO: Coluna ambígua\n');
      
      // Extrair informações do erro
      const columnMatch = errorText.match(/column reference "([^"]+)" is ambiguous/);
      const sqlMatch = errorText.match(/\[SQL: (.*?)\]/s);
      
      if (columnMatch) {
        console.log(`🎯 Coluna problemática: ${columnMatch[1]}\n`);
      }
      
      if (sqlMatch) {
        const sql = sqlMatch[1].trim();
        console.log('📝 Query SQL problemática:');
        console.log('----------------------------');
        console.log(sql);
        console.log('----------------------------\n');
        
        // Analisar e sugerir correções
        console.log('🔧 SUGESTÕES DE CORREÇÃO:\n');
        
        if (sql.includes('created_at') && !sql.includes('u.created_at')) {
          console.log('1. PROBLEMA: Referência ambígua à coluna "created_at"');
          console.log('   CAUSA: Multiple tabelas (users, conversations, messages, appointments) têm created_at');
          console.log('   SOLUÇÃO: Especificar qual tabela usar:\n');
          
          // Sugerir query corrigida
          const fixedSQL = sql
            .replace(/EXTRACT\(MONTH FROM created_at\)/g, 'EXTRACT(MONTH FROM u.created_at)')
            .replace(/EXTRACT\(YEAR FROM created_at\)/g, 'EXTRACT(YEAR FROM u.created_at)')
            .replace(/GROUP BY EXTRACT\(YEAR FROM u\.created_at\), EXTRACT\(MONTH FROM u\.created_at\)/g, 
                    'GROUP BY EXTRACT(YEAR FROM u.created_at), EXTRACT(MONTH FROM u.created_at)');
          
          console.log('   Query SQL corrigida:');
          console.log('   --------------------');
          console.log(fixedSQL);
          console.log('   --------------------\n');
        }
        
        if (sql.includes('SUM(a.price)')) {
          console.log('2. PROBLEMA: Campo "price" não existe na tabela appointments');
          console.log('   SOLUÇÃO: Verificar estrutura da tabela ou usar campo correto\n');
          
          console.log('   Opções possíveis:');
          console.log('   - a.valor (se o campo for "valor")');
          console.log('   - a.preco (se o campo for "preco")');
          console.log('   - a.amount (se o campo for "amount")');
          console.log('   - 0 (se não houver campo de valor)\n');
        }
        
        console.log('3. RECOMENDAÇÃO GERAL:');
        console.log('   - Sempre usar aliases de tabela (u., c., m., a.)');
        console.log('   - Verificar estrutura real das tabelas no PostgreSQL');
        console.log('   - Testar queries individualmente antes de implementar\n');
        
        // Gerar comando SQL para verificar estrutura
        console.log('🔍 COMANDOS PARA VERIFICAR ESTRUTURA DAS TABELAS:\n');
        console.log('-- No PostgreSQL, execute:');
        console.log('\\d+ users');
        console.log('\\d+ conversations');
        console.log('\\d+ messages');
        console.log('\\d+ appointments');
        console.log('');
        console.log('-- Ou use SQL:');
        console.log('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = \'appointments\';');
      }
      
    } else {
      console.log('✅ Endpoint funcionando ou erro diferente');
      console.log(`Status: ${response.status}`);
      console.log(`Response: ${errorText.substring(0, 500)}...`);
    }
    
  } catch (error) {
    console.error('❌ Erro durante análise:', error.message);
  }
}

// Função para gerar SQL corrigido
function generateFixedSQL() {
  console.log('\n📝 QUERY SQL CORRIGIDA SUGERIDA:');
  console.log('=================================');
  
  const correctedSQL = `
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    -- Substituir 'price' pelo campo correto ou usar 0
    COALESCE(SUM(a.valor), 0) as revenue,  -- Ajustar nome do campo
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
LIMIT $2
  `.trim();
  
  console.log(correctedSQL);
  console.log('\n⚠️  ATENÇÃO: Verificar se o campo "valor" existe na tabela appointments');
  console.log('   Caso contrário, substituir por 0 ou pelo campo correto\n');
}

async function main() {
  await analyzeSQL();
  generateFixedSQL();
  
  console.log('🎯 PRÓXIMOS PASSOS:');
  console.log('==================');
  console.log('1. Executar: node debug-backend.js (para diagnóstico completo)');
  console.log('2. Verificar estrutura das tabelas no PostgreSQL');
  console.log('3. Corrigir as queries SQL no backend');
  console.log('4. Testar novamente após correções');
}

if (require.main === module) {
  main().catch(console.error);
}
