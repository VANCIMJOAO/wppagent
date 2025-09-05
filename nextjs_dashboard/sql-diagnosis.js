#!/usr/bin/env node
/**
 * Script para análise de erros SQL - Versão simplificada usando curl
 */

const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

// Configurações
const API_BASE_URL = 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'senha_admin_segura';

async function login() {
  try {
    console.log('🔑 Fazendo login...');
    
    const loginCommand = `curl -s -X POST "${API_BASE_URL}/admin/login" \
      -H "Content-Type: application/json" \
      -d '{"username": "${ADMIN_USERNAME}", "password": "${ADMIN_PASSWORD}"}'`;
    
    const { stdout } = await execAsync(loginCommand);
    const loginData = JSON.parse(stdout);
    
    if (loginData.access_token) {
      console.log('✅ Login realizado com sucesso!\n');
      return loginData.access_token;
    } else {
      throw new Error('Token não encontrado na resposta');
    }
  } catch (error) {
    console.error('❌ Erro no login:', error.message);
    return null;
  }
}

async function testEndpoint(token, endpoint, description) {
  try {
    console.log(`📊 Testando: ${endpoint}`);
    
    const testCommand = `curl -s -H "Authorization: Bearer ${token}" \
      -H "Content-Type: application/json" \
      -w "\\n%{http_code}" \
      "${API_BASE_URL}${endpoint}"`;
    
    const { stdout } = await execAsync(testCommand);
    const lines = stdout.trim().split('\n');
    const statusCode = lines[lines.length - 1];
    const responseBody = lines.slice(0, -1).join('\n');
    
    console.log(`   Status: ${statusCode}`);
    
    if (statusCode === '200') {
      console.log('✅ Endpoint funcionando!\n');
      try {
        const data = JSON.parse(responseBody);
        if (Array.isArray(data)) {
          console.log(`   Retornou: Array com ${data.length} itens`);
        } else {
          console.log(`   Campos: ${Object.keys(data).join(', ')}`);
        }
      } catch (e) {
        console.log(`   Resposta: ${responseBody.substring(0, 100)}...`);
      }
      console.log('');
      return { success: true, status: statusCode, data: responseBody };
    } else if (statusCode === '500') {
      console.log('❌ Erro 500 - Analisando...\n');
      
      if (responseBody.includes('AmbiguousColumnError')) {
        console.log('🎯 PROBLEMA IDENTIFICADO: Coluna SQL Ambígua');
        
        // Extrair detalhes do erro
        const columnMatch = responseBody.match(/column reference "([^"]+)" is ambiguous/);
        if (columnMatch) {
          console.log(`   Coluna problemática: ${columnMatch[1]}`);
        }
        
        if (responseBody.includes('created_at')) {
          console.log('\n🔧 SOLUÇÃO PARA created_at:');
          console.log('   PROBLEMA: Multiple tabelas têm created_at (users, conversations, messages, appointments)');
          console.log('   CORREÇÃO: Usar aliases específicos:');
          console.log('   - u.created_at (para users)');
          console.log('   - c.created_at (para conversations)');
          console.log('   - m.created_at (para messages)');
          console.log('   - a.created_at (para appointments)');
        }
        
        if (responseBody.includes('price')) {
          console.log('\n💰 PROBLEMA COM CAMPO "price":');
          console.log('   ERRO: Campo "price" não existe na tabela appointments');
          console.log('   SOLUÇÕES POSSÍVEIS:');
          console.log('   1. Verificar nome correto do campo (valor, preco, amount)');
          console.log('   2. Criar o campo "price" na tabela appointments');
          console.log('   3. Usar 0 como valor padrão se não houver campo de preço');
        }
        
        console.log('\n📝 QUERY SQL PROBLEMÁTICA ENCONTRADA:');
        const sqlMatch = responseBody.match(/\[SQL: (.*?)\]/s);
        if (sqlMatch) {
          console.log('-------------------------------------------');
          console.log(sqlMatch[1].trim());
          console.log('-------------------------------------------');
        }
      }
      
      console.log('');
      return { success: false, status: statusCode, error: responseBody };
    } else {
      console.log(`⚠️ Status ${statusCode}: ${responseBody.substring(0, 200)}...\n`);
      return { success: false, status: statusCode, error: responseBody };
    }
    
  } catch (error) {
    console.error(`❌ Erro ao testar ${endpoint}:`, error.message);
    return { success: false, error: error.message };
  }
}

async function generateSQLFix() {
  console.log('\n📝 QUERY SQL CORRIGIDA SUGERIDA:');
  console.log('=================================');
  
  const correctedSQL = `
-- Query corrigida com aliases específicos
SELECT 
    EXTRACT(MONTH FROM u.created_at) as month,
    EXTRACT(YEAR FROM u.created_at) as year,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    -- Corrigir campo price (verificar nome real na tabela)
    COALESCE(SUM(CASE 
        WHEN a.price IS NOT NULL THEN a.price 
        WHEN a.valor IS NOT NULL THEN a.valor 
        WHEN a.preco IS NOT NULL THEN a.preco 
        ELSE 0 
    END), 0) as revenue,
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
LIMIT $2`;
  
  console.log(correctedSQL);
  
  console.log('\n🔍 VERIFICAÇÃO NECESSÁRIA:');
  console.log('=========================');
  console.log('1. Conectar no PostgreSQL e verificar estrutura:');
  console.log('   \\d+ appointments');
  console.log('   SELECT column_name FROM information_schema.columns WHERE table_name = \'appointments\';');
  console.log('\n2. Verificar qual campo representa o valor/preço:');
  console.log('   - price');
  console.log('   - valor');  
  console.log('   - preco');
  console.log('   - amount');
  console.log('\n3. Atualizar a query no backend com o campo correto');
}

async function main() {
  console.log('🔍 DIAGNÓSTICO DE ERROS SQL - WHATSAPP AGENT');
  console.log('=============================================\n');
  
  // Login
  const token = await login();
  if (!token) {
    console.log('❌ Impossível continuar sem token');
    return;
  }
  
  // Testar endpoints problemáticos
  console.log('📊 TESTANDO ENDPOINTS PROBLEMÁTICOS');
  console.log('====================================');
  
  const endpoints = [
    { path: '/api/dashboard/stats/monthly', desc: 'Estatísticas Mensais' },
    { path: '/api/dashboard/clients', desc: 'Lista de Clientes' },
    { path: '/api/dashboard/stats/daily', desc: 'Estatísticas Diárias' }
  ];
  
  const results = [];
  
  for (const endpoint of endpoints) {
    const result = await testEndpoint(token, endpoint.path, endpoint.desc);
    results.push({ endpoint: endpoint.path, ...result });
    
    // Pausa entre requests
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // Resumo
  console.log('📋 RESUMO DOS RESULTADOS');
  console.log('========================');
  
  const working = results.filter(r => r.success);
  const broken = results.filter(r => !r.success);
  
  console.log(`✅ Funcionando: ${working.length}`);
  console.log(`❌ Com erro: ${broken.length}`);
  
  working.forEach(r => console.log(`   ✓ ${r.endpoint}`));
  broken.forEach(r => console.log(`   ✗ ${r.endpoint} (${r.status || 'erro'})`));
  
  if (broken.length > 0) {
    await generateSQLFix();
  }
  
  console.log('\n🎯 PRÓXIMOS PASSOS:');
  console.log('==================');
  console.log('1. Verificar estrutura das tabelas no PostgreSQL');
  console.log('2. Corrigir queries SQL no backend');
  console.log('3. Testar novamente após correções');
  console.log('4. Implementar logs estruturados para facilitar debug');
}

// Executar
if (require.main === module) {
  main().catch(console.error);
}
