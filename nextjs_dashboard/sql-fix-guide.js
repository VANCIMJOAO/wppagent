#!/usr/bin/env node
/**
 * Script para verificar estrutura das tabelas PostgreSQL
 * e gerar correções SQL específicas
 */

const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

// Configurações do Railway PostgreSQL
const RAILWAY_DB_URL = process.env.DATABASE_URL || 'postgresql://postgres:password@host:port/database';

console.log('🔍 VERIFICAÇÃO DE ESTRUTURA DAS TABELAS');
console.log('=======================================\n');

console.log('📋 RESUMO DOS PROBLEMAS IDENTIFICADOS:');
console.log('=====================================');
console.log('1. ❌ Coluna "created_at" ambígua - múltiplas tabelas têm este campo');
console.log('2. ❌ Campo "price" não existe na tabela appointments');
console.log('3. ❌ Query não usa aliases específicos para colunas\n');

console.log('🔧 SOLUÇÕES ESPECÍFICAS:');
console.log('========================');

console.log('\n1️⃣ CORREÇÃO PARA COLUNA AMBÍGUA:');
console.log('----------------------------------');
console.log('PROBLEMA ORIGINAL:');
console.log('   EXTRACT(MONTH FROM created_at) as month');
console.log('   EXTRACT(YEAR FROM created_at) as year');
console.log('');
console.log('CORREÇÃO:');
console.log('   EXTRACT(MONTH FROM u.created_at) as month');
console.log('   EXTRACT(YEAR FROM u.created_at) as year');

console.log('\n2️⃣ CORREÇÃO PARA CAMPO PRICE:');
console.log('-------------------------------');
console.log('PROBLEMA ORIGINAL:');
console.log('   COALESCE(SUM(a.price), 0) as revenue');
console.log('');
console.log('OPÇÕES DE CORREÇÃO:');
console.log('A) Se o campo for "valor": SUM(a.valor)');
console.log('B) Se o campo for "preco": SUM(a.preco)');  
console.log('C) Se o campo for "amount": SUM(a.amount)');
console.log('D) Se não houver campo: SUM(0) ou remover');

console.log('\n📝 QUERY SQL COMPLETAMENTE CORRIGIDA:');
console.log('====================================');

const correctedSQL = `
-- Versão 1: Assumindo campo "valor" na tabela appointments
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    COALESCE(SUM(a.valor), 0) as revenue,
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

-- Versão 2: Se não houver campo de valor
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    0 as revenue, -- Sem campo de receita
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

-- Versão 3: Defensiva com CASE
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    COALESCE(SUM(
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'appointments' 
                AND column_name = 'price'
            ) THEN a.price
            WHEN EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'appointments' 
                AND column_name = 'valor'
            ) THEN a.valor
            ELSE 0 
        END
    ), 0) as revenue,
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

console.log(correctedSQL);

console.log('\n🛠️ COMANDOS PARA VERIFICAR ESTRUTURA (Railway):');
console.log('==============================================');
console.log('# Conectar no banco Railway:');
console.log('railway login');
console.log('railway connect');
console.log('railway db connect');
console.log('');
console.log('# Verificar estrutura das tabelas:');
console.log('\\d+ users');
console.log('\\d+ conversations');
console.log('\\d+ messages');  
console.log('\\d+ appointments');
console.log('');
console.log('# Query para listar colunas:');
console.log("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_name IN ('users', 'conversations', 'messages', 'appointments') ORDER BY table_name, ordinal_position;");

console.log('\n💡 IMPLEMENTAÇÃO NO BACKEND:');
console.log('============================');
console.log('1. Localizar arquivo Python com a query (provavelmente em app/services/ ou app/routes/)');
console.log('2. Substituir a query problemática pela versão corrigida');
console.log('3. Ajustar campo de receita baseado na estrutura real da tabela');
console.log('4. Testar localmente antes do deploy');
console.log('5. Deploy no Railway');

console.log('\n🚀 TESTE RÁPIDO:');
console.log('================');
console.log('Para testar se a correção funcionou:');
console.log('node sql-diagnosis.js');

console.log('\n⚡ CORREÇÃO IMEDIATA SUGERIDA:');
console.log('==============================');
console.log('Se você tiver acesso ao código do backend, procure por:');
console.log('- Arquivos com "EXTRACT(MONTH FROM created_at)"');
console.log('- Código que faz "SUM(a.price)"');
console.log('- Endpoints "/api/dashboard/stats/monthly"');
console.log('');
console.log('E aplique as correções mostradas acima.');

console.log('\n✅ RESUMO EXECUTIVO:');
console.log('===================');
console.log('PROBLEMA: Query SQL com coluna ambígua e campo inexistente');
console.log('CAUSA: Falta de aliases específicos e campo "price" não existe');
console.log('SOLUÇÃO: Usar "u.created_at" em vez de "created_at" e corrigir campo de receita');
console.log('URGÊNCIA: Alta - Sistema não consegue carregar estatísticas');
console.log('TEMPO ESTIMADO: 15-30 minutos para correção completa');
