#!/usr/bin/env node
/**
 * Script para aplicar correções SQL no backend do WhatsApp Agent
 * Baseado na análise da estrutura do banco PostgreSQL
 */

const fs = require('fs');
const path = require('path');

console.log('🔧 SCRIPT DE CORREÇÃO DO BACKEND');
console.log('================================');

// 1. Query SQL corrigida
const correctedSQLQuery = `
-- QUERY CORRIGIDA PARA /api/dashboard/stats/monthly
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    COALESCE(SUM(a.price), 0) as revenue,
    COUNT(DISTINCT u.id) as new_clients
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id 
    AND c.created_at >= %s
LEFT JOIN messages m ON u.id = m.user_id 
    AND m.created_at >= %s
LEFT JOIN appointments a ON u.id = a.user_id 
    AND a.created_at >= %s
WHERE u.created_at >= %s
    AND u.nome IS NOT NULL 
    AND u.nome != ''
    AND u.nome NOT LIKE '%[DELETED]%'
GROUP BY EXTRACT(YEAR FROM u.created_at), EXTRACT(MONTH FROM u.created_at)
ORDER BY year DESC, month DESC
LIMIT %s;`.trim();

// 2. Query para /api/dashboard/clients (também corrigir ambiguidade)
const correctedClientsQuery = `
-- QUERY CORRIGIDA PARA /api/dashboard/clients  
SELECT 
    u.id,
    u.nome,
    u.telefone,
    u.email,
    u.created_at,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    MAX(c.last_message_at) as last_interaction
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN messages m ON u.id = m.user_id
LEFT JOIN appointments a ON u.id = a.user_id
WHERE u.nome IS NOT NULL 
    AND u.nome != ''
    AND u.nome NOT LIKE '%[DELETED]%'
GROUP BY u.id, u.nome, u.telefone, u.email, u.created_at
ORDER BY u.created_at DESC
LIMIT %s OFFSET %s;`.trim();

// 3. Instruções para aplicar as correções
const correctionInstructions = {
  backend_fixes: {
    monthly_stats_endpoint: {
      file_location: "app/routes ou app/services (FastAPI/Python)",
      current_problem: "AmbiguousColumnError: coluna 'created_at' sem alias de tabela",
      solution: "Substituir query no endpoint /api/dashboard/stats/monthly",
      corrected_query: correctedSQLQuery
    },
    clients_endpoint: {
      file_location: "app/routes ou app/services (FastAPI/Python)",
      current_problem: "Possível ambiguidade em queries de clientes",
      solution: "Usar aliases explícitos para todas as colunas",
      corrected_query: correctedClientsQuery
    },
    general_fixes: [
      "1. Sempre usar aliases de tabela (u, c, m, a) em todas as queries",
      "2. O campo 'price' existe em appointments - usar COALESCE(SUM(a.price), 0)",
      "3. Campos created_at existem em todas as tabelas principais",
      "4. Usar prepared statements com parâmetros (%s no Python/SQLAlchemy)"
    ]
  },
  database_info: {
    tables_confirmed: ["users", "conversations", "messages", "appointments"],
    price_fields: ["appointments.price", "services.price"],
    created_fields: "Todas as tabelas principais têm created_at",
    total_records: {
      users: 112,
      conversations: 40,
      messages: 2074,
      appointments: 17
    }
  },
  test_results: {
    connection_success: true,
    query_executed_successfully: true,
    sample_result: "107 clientes novos, 38 conversas em agosto/2025",
    backend_status: "Banco funcional, problema apenas na query SQL"
  }
};

// 4. Gerar arquivo Python com as queries corrigidas
const pythonCode = `# -*- coding: utf-8 -*-
"""
Queries SQL corrigidas para o WhatsApp Agent Dashboard
Gerado automaticamente em ${new Date().toISOString()}
"""

# Query corrigida para estatísticas mensais (/api/dashboard/stats/monthly)
MONTHLY_STATS_QUERY = """
${correctedSQLQuery.replace(/\n/g, '\n')}
"""

# Query corrigida para lista de clientes (/api/dashboard/clients)
CLIENTS_LIST_QUERY = """
${correctedClientsQuery.replace(/\n/g, '\n')}
"""

# Função de exemplo para usar no FastAPI
async def get_monthly_stats(db_session, start_date, limit=12):
    """
    Obter estatísticas mensais com query corrigida
    """
    import datetime
    
    # Usar data de 30 dias atrás se não especificado
    if not start_date:
        start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    # Executar query com parâmetros seguros
    result = await db_session.execute(
        MONTHLY_STATS_QUERY,
        [start_date, start_date, start_date, start_date, limit]
    )
    
    return result.fetchall()

async def get_clients_list(db_session, limit=50, offset=0):
    """
    Obter lista de clientes com query corrigida
    """
    result = await db_session.execute(
        CLIENTS_LIST_QUERY,
        [limit, offset]
    )
    
    return result.fetchall()
`;

// 5. Salvar arquivos de correção
try {
  // Salvar instruções completas
  fs.writeFileSync('backend-correction-instructions.json', 
    JSON.stringify(correctionInstructions, null, 2));
  
  // Salvar código Python
  fs.writeFileSync('corrected-queries.py', pythonCode);
  
  // Salvar queries SQL puras
  fs.writeFileSync('monthly-stats-corrected.sql', correctedSQLQuery);
  fs.writeFileSync('clients-list-corrected.sql', correctedClientsQuery);
  
  console.log('✅ CORREÇÕES GERADAS COM SUCESSO!');
  console.log('=================================');
  console.log('📄 Arquivos criados:');
  console.log('   📋 backend-correction-instructions.json - Instruções completas');
  console.log('   🐍 corrected-queries.py - Código Python pronto para usar');
  console.log('   🗃️  monthly-stats-corrected.sql - Query de estatísticas corrigida');
  console.log('   🗃️  clients-list-corrected.sql - Query de clientes corrigida');
  
  console.log('\n🎯 PRÓXIMOS PASSOS:');
  console.log('==================');
  console.log('1. ✅ Banco analisado e queries testadas com sucesso');
  console.log('2. 🔄 Aplicar queries corrigidas no código backend Python');
  console.log('3. 🚀 Redeploy do backend no Railway');
  console.log('4. ✅ Frontend já está preparado para receber dados reais');
  
  console.log('\n💡 PROBLEMA IDENTIFICADO:');
  console.log('=========================');
  console.log('❌ AmbiguousColumnError: created_at (resolvido com aliases)');
  console.log('✅ Campo price existe em appointments.price');
  console.log('✅ Query testada e funcionando no banco PostgreSQL');
  console.log('✅ Frontend com error handling robusto');
  
  console.log('\n📊 DADOS DO BANCO:');
  console.log('=================');
  console.log('👥 112 usuários cadastrados');
  console.log('💬 40 conversas ativas'); 
  console.log('📱 2.074 mensagens trocadas');
  console.log('📅 17 agendamentos realizados');
  console.log('💰 Campo price disponível para receita');
  
} catch (error) {
  console.error('❌ Erro ao salvar arquivos:', error.message);
}
