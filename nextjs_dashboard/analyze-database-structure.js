#!/usr/bin/env node
/**
 * Script para conectar diretamente no PostgreSQL do Railway e capturar estrutura
 * Connection: postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway
 */

const { Client } = require('pg');

// Configuração da conexão
const connectionString = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway';

async function connectAndAnalyze() {
  const client = new Client({ connectionString });
  
  try {
    console.log('🔗 Conectando no PostgreSQL do Railway...');
    await client.connect();
    console.log('✅ Conectado com sucesso!\n');
    
    // 1. Listar todas as tabelas
    console.log('📋 LISTANDO TODAS AS TABELAS:');
    console.log('============================');
    const tablesQuery = `
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name;
    `;
    
    const tablesResult = await client.query(tablesQuery);
    console.log(`Encontradas ${tablesResult.rows.length} tabelas:`);
    tablesResult.rows.forEach(row => {
      console.log(`  📄 ${row.table_name}`);
    });
    
    // 2. Estrutura detalhada de cada tabela relevante
    const importantTables = ['users', 'conversations', 'messages', 'appointments'];
    const tableStructures = {};
    
    for (const tableName of importantTables) {
      console.log(`\n🔍 ESTRUTURA DA TABELA: ${tableName.toUpperCase()}`);
      console.log('='.repeat(40));
      
      const structureQuery = `
        SELECT 
          column_name,
          data_type,
          is_nullable,
          column_default,
          character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = $1
        AND table_schema = 'public'
        ORDER BY ordinal_position;
      `;
      
      try {
        const result = await client.query(structureQuery, [tableName]);
        
        if (result.rows.length > 0) {
          console.log(`📊 ${result.rows.length} colunas encontradas:`);
          result.rows.forEach(col => {
            const nullable = col.is_nullable === 'YES' ? 'NULL' : 'NOT NULL';
            const length = col.character_maximum_length ? `(${col.character_maximum_length})` : '';
            console.log(`  📍 ${col.column_name}: ${col.data_type}${length} ${nullable}`);
            if (col.column_default) {
              console.log(`      Default: ${col.column_default}`);
            }
          });
          tableStructures[tableName] = result.rows;
        } else {
          console.log(`  ❌ Tabela '${tableName}' não encontrada`);
          tableStructures[tableName] = [];
        }
      } catch (error) {
        console.log(`  ❌ Erro ao consultar tabela '${tableName}': ${error.message}`);
        tableStructures[tableName] = [];
      }
    }
    
    // 3. Procurar especificamente campos de data
    console.log('\n📅 CAMPOS COM "created" NO NOME:');
    console.log('===============================');
    const createdFieldsQuery = `
      SELECT table_name, column_name, data_type
      FROM information_schema.columns 
      WHERE column_name LIKE '%created%'
      AND table_schema = 'public'
      ORDER BY table_name, column_name;
    `;
    
    const createdFields = await client.query(createdFieldsQuery);
    if (createdFields.rows.length > 0) {
      createdFields.rows.forEach(row => {
        console.log(`  📅 ${row.table_name}.${row.column_name} (${row.data_type})`);
      });
    } else {
      console.log('  ❌ Nenhum campo com "created" encontrado');
    }
    
    // 4. Procurar campos de valor/preço
    console.log('\n💰 CAMPOS DE VALOR/PREÇO:');
    console.log('========================');
    const priceFieldsQuery = `
      SELECT table_name, column_name, data_type
      FROM information_schema.columns 
      WHERE column_name IN ('price', 'valor', 'preco', 'amount', 'value', 'cost', 'total')
      AND table_schema = 'public'
      ORDER BY table_name, column_name;
    `;
    
    const priceFields = await client.query(priceFieldsQuery);
    if (priceFields.rows.length > 0) {
      priceFields.rows.forEach(row => {
        console.log(`  💰 ${row.table_name}.${row.column_name} (${row.data_type})`);
      });
    } else {
      console.log('  ❌ Nenhum campo de preço/valor encontrado');
      
      // Procurar qualquer campo numérico na tabela appointments
      if (tableStructures.appointments && tableStructures.appointments.length > 0) {
        console.log('\n💡 CAMPOS NUMÉRICOS NA TABELA APPOINTMENTS:');
        const numericFields = tableStructures.appointments.filter(col => 
          col.data_type.includes('numeric') || 
          col.data_type.includes('decimal') || 
          col.data_type.includes('integer') ||
          col.data_type.includes('real') ||
          col.data_type.includes('double')
        );
        
        if (numericFields.length > 0) {
          numericFields.forEach(field => {
            console.log(`  🔢 ${field.column_name} (${field.data_type}) - Possível campo de valor`);
          });
        }
      }
    }
    
    // 5. Testar a query problemática com correções
    console.log('\n🧪 TESTANDO QUERY CORRIGIDA:');
    console.log('============================');
    
    // Primeiro, verificar se as tabelas têm dados
    const tablesWithData = {};
    for (const table of importantTables) {
      if (tableStructures[table] && tableStructures[table].length > 0) {
        try {
          const countResult = await client.query(`SELECT COUNT(*) as total FROM ${table}`);
          const count = parseInt(countResult.rows[0].total);
          tablesWithData[table] = count;
          console.log(`📊 ${table}: ${count} registros`);
        } catch (error) {
          console.log(`❌ Erro ao contar ${table}: ${error.message}`);
          tablesWithData[table] = 0;
        }
      }
    }
    
    // Agora testar a query corrigida
    let correctedQuery = ''; // Declarar no escopo correto
    
    if (tablesWithData.users > 0) {
      console.log('\n🔧 TESTANDO QUERY CORRIGIDA (últimos 30 dias):');
      
      correctedQuery = `
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
            AND c.created_at >= CURRENT_DATE - INTERVAL '30 days'
        LEFT JOIN messages m ON u.id = m.user_id 
            AND m.created_at >= CURRENT_DATE - INTERVAL '30 days'
        LEFT JOIN appointments a ON u.id = a.user_id 
            AND a.created_at >= CURRENT_DATE - INTERVAL '30 days'
        WHERE u.created_at >= CURRENT_DATE - INTERVAL '30 days'
            AND u.nome IS NOT NULL 
            AND u.nome != ''
            AND u.nome NOT LIKE '%[DELETED]%'
        GROUP BY EXTRACT(YEAR FROM u.created_at), EXTRACT(MONTH FROM u.created_at)
        ORDER BY year DESC, month DESC
        LIMIT 12;
      `;
      
      try {
        console.log('Executando query corrigida...');
        const result = await client.query(correctedQuery);
        console.log('✅ QUERY EXECUTADA COM SUCESSO!');
        console.log(`📊 Resultado: ${result.rows.length} linhas retornadas`);
        
        if (result.rows.length > 0) {
          console.log('📋 Primeiras linhas:');
          result.rows.slice(0, 3).forEach(row => {
            console.log(`   ${row.month}/${row.year}: ${row.new_clients} clientes, ${row.total_conversations} conversas`);
          });
        }
        
      } catch (error) {
        console.log(`❌ Erro na query corrigida: ${error.message}`);
        
        // Tentar versão mais simples
        console.log('🔄 Testando versão mais simples...');
        const simpleQuery = `
          SELECT 
              COUNT(*) as total_users,
              COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_users
          FROM users 
          WHERE nome IS NOT NULL 
              AND nome != ''
              AND nome NOT LIKE '%[DELETED]%'
          LIMIT 1;
        `;
        
        try {
          const simpleResult = await client.query(simpleQuery);
          console.log('✅ Query simples funcionou:');
          console.log(`   Total usuários: ${simpleResult.rows[0].total_users}`);
          console.log(`   Usuários recentes: ${simpleResult.rows[0].recent_users}`);
        } catch (simpleError) {
          console.log(`❌ Erro na query simples: ${simpleError.message}`);
        }
      }
    }
    
    // 6. Gerar arquivo de saída com estrutura completa
    const databaseStructure = {
      timestamp: new Date().toISOString(),
      connection_success: true,
      tables: Object.keys(tableStructures),
      table_structures: tableStructures,
      tables_with_data: tablesWithData,
      created_fields: createdFields.rows,
      price_fields: priceFields.rows,
      sql_fix_recommendations: {
        primary_issue: "Coluna 'created_at' ambígua - usar aliases específicos",
        secondary_issue: "Campo 'price' não existe - usar 0 ou encontrar campo correto",
        corrected_query: correctedQuery.trim()
      }
    };
    
    require('fs').writeFileSync(
      'database-structure-complete.json',
      JSON.stringify(databaseStructure, null, 2)
    );
    
    console.log('\n📝 GERANDO QUERY FINAL CORRIGIDA:');
    console.log('=================================');
    
    // Determinar qual campo usar para receita
    let revenueField = '0';
    if (priceFields.rows.length > 0) {
      const appointmentPriceField = priceFields.rows.find(f => f.table_name === 'appointments');
      if (appointmentPriceField) {
        revenueField = `COALESCE(SUM(a.${appointmentPriceField.column_name}), 0)`;
        console.log(`💰 Campo de receita encontrado: appointments.${appointmentPriceField.column_name}`);
      }
    }
    
    const finalQuery = `
-- QUERY CORRIGIDA FINAL PARA /api/dashboard/stats/monthly
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    ${revenueField} as revenue,
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
    `.trim();
    
    console.log(finalQuery);
    
    // Salvar query corrigida em arquivo separado
    require('fs').writeFileSync('corrected-sql-query.sql', finalQuery);
    
    console.log('\n🎉 ANÁLISE COMPLETA!');
    console.log('===================');
    console.log('✅ Estrutura do banco capturada');
    console.log('✅ Query corrigida gerada');
    console.log('✅ Arquivos salvos:');
    console.log('   📄 database-structure-complete.json');
    console.log('   📄 corrected-sql-query.sql');
    console.log('\n🎯 PRÓXIMO PASSO:');
    console.log('Aplicar a query corrigida no código backend Python/FastAPI');
    
  } catch (error) {
    console.error('❌ Erro de conexão:', error.message);
    
    // Salvar erro para debug
    require('fs').writeFileSync(
      'database-connection-error.json',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        error: error.message,
        connection_string_used: connectionString.replace(/:([^:@]+)@/, ':****@'),
        recommendations: [
          'Verificar se a string de conexão está correta',
          'Verificar se o banco está acessível',
          'Verificar se o módulo pg está instalado: npm install pg'
        ]
      }, null, 2)
    );
  } finally {
    try {
      await client.end();
      console.log('🔌 Conexão fechada');
    } catch (closeError) {
      console.log('⚠️ Erro ao fechar conexão:', closeError.message);
    }
  }
}

// Executar se chamado diretamente
if (require.main === module) {
  // Verificar se pg está instalado
  try {
    require('pg');
    connectAndAnalyze().catch(error => {
      console.error('❌ Erro fatal:', error);
      process.exit(1);
    });
  } catch (requireError) {
    console.error('❌ Módulo pg não encontrado. Instale com: npm install pg');
    console.error('   Ou use: yarn add pg');
    process.exit(1);
  }
}
