#!/usr/bin/env node
/**
 * Script de Diagnóstico do Backend - WhatsApp Agent
 * 
 * Este script testa todos os endpoints do backend e identifica erros específicos
 * como SQL ambíguo, campos ausentes, problemas de autenticação, etc.
 */

const fetch = require('node-fetch');

// Configurações
const API_BASE_URL = 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'senha_admin_segura';

// Cores para output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  bold: '\x1b[1m'
};

function log(message, color = 'white') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(60));
  log(title, 'cyan');
  console.log('='.repeat(60));
}

function logError(message, error) {
  log(`❌ ${message}`, 'red');
  if (error) {
    log(`   Detalhes: ${error}`, 'yellow');
  }
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green');
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

function logInfo(message) {
  log(`ℹ️  ${message}`, 'blue');
}

// Função para fazer login e obter token
async function login() {
  try {
    logInfo('Fazendo login...');
    const response = await fetch(`${API_BASE_URL}/admin/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: ADMIN_USERNAME,
        password: ADMIN_PASSWORD,
      }),
    });

    if (!response.ok) {
      throw new Error(`Status: ${response.status} - ${await response.text()}`);
    }

    const data = await response.json();
    
    if (!data.access_token) {
      throw new Error('Token de acesso não encontrado na resposta');
    }

    // Decodificar JWT para verificar expiração
    try {
      const payload = JSON.parse(Buffer.from(data.access_token.split('.')[1], 'base64').toString());
      const expiry = new Date(payload.exp * 1000);
      logSuccess(`Login realizado com sucesso!`);
      logInfo(`Token expira em: ${expiry.toLocaleString()}`);
      logInfo(`Usuário: ${payload.sub || 'N/A'}`);
      logInfo(`Role: ${payload.role || 'N/A'}`);
      logInfo(`Permissões: ${payload.permissions ? payload.permissions.join(', ') : 'N/A'}`);
    } catch (e) {
      logWarning('Não foi possível decodificar o JWT');
    }

    return data.access_token;
  } catch (error) {
    logError('Falha no login', error.message);
    return null;
  }
}

// Função para testar endpoint específico
async function testEndpoint(token, endpoint, description) {
  try {
    logInfo(`Testando: ${endpoint}`);
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const responseText = await response.text();
    let responseData;
    
    try {
      responseData = JSON.parse(responseText);
    } catch (e) {
      responseData = responseText;
    }

    if (response.ok) {
      logSuccess(`${description}: OK (${response.status})`);
      
      // Mostrar estrutura da resposta se for JSON
      if (typeof responseData === 'object' && responseData !== null) {
        if (Array.isArray(responseData)) {
          logInfo(`   Retornou array com ${responseData.length} itens`);
          if (responseData.length > 0) {
            logInfo(`   Estrutura do primeiro item: ${Object.keys(responseData[0]).join(', ')}`);
          }
        } else {
          logInfo(`   Campos retornados: ${Object.keys(responseData).join(', ')}`);
        }
      }
      
      return { success: true, data: responseData, status: response.status };
    } else {
      logError(`${description}: ERRO (${response.status})`, '');
      
      // Análise específica de erros
      if (response.status === 401) {
        logWarning('   Problema de autenticação - token inválido ou expirado');
      } else if (response.status === 404) {
        logWarning('   Endpoint não encontrado');
      } else if (response.status === 500) {
        logWarning('   Erro interno do servidor');
        
        // Análise do erro SQL
        if (responseText.includes('AmbiguousColumnError')) {
          logError('   ERRO SQL: Coluna ambígua detectada!', '');
          const match = responseText.match(/column reference "([^"]+)" is ambiguous/);
          if (match) {
            logWarning(`   Coluna problemática: ${match[1]}`);
          }
          
          // Extrair query SQL se disponível
          const sqlMatch = responseText.match(/\[SQL: (.*?)\]/s);
          if (sqlMatch) {
            log('\n   Query SQL problemática:', 'yellow');
            const sql = sqlMatch[1].trim();
            console.log('   ' + sql.replace(/\n/g, '\n   '));
          }
        }
        
        if (responseText.includes('has no attribute')) {
          logError('   ERRO: Atributo não encontrado!', '');
          const attrMatch = responseText.match(/has no attribute '([^']+)'/);
          if (attrMatch) {
            logWarning(`   Atributo ausente: ${attrMatch[1]}`);
          }
        }
        
        if (responseText.includes('price')) {
          logError('   PROBLEMA ESPECÍFICO: Campo "price" não encontrado', '');
          logWarning('   Possível solução: Verificar se a tabela appointments tem o campo price');
        }
      }
      
      // Mostrar resposta completa se for pequena
      if (responseText.length < 1000) {
        log(`   Resposta completa: ${responseText}`, 'yellow');
      } else {
        log(`   Resposta muito longa (${responseText.length} chars), mostrando início:`, 'yellow');
        log(`   ${responseText.substring(0, 500)}...`, 'yellow');
      }
      
      return { success: false, data: responseData, status: response.status, error: responseText };
    }
  } catch (error) {
    logError(`${description}: FALHA DE REDE`, error.message);
    return { success: false, error: error.message };
  }
}

// Função para obter informações do OpenAPI
async function getOpenAPIInfo(token) {
  try {
    logInfo('Obtendo informações do OpenAPI...');
    const result = await testEndpoint(token, '/openapi.json', 'OpenAPI Schema');
    
    if (result.success && typeof result.data === 'object') {
      const openapi = result.data;
      logInfo(`API Title: ${openapi.info?.title || 'N/A'}`);
      logInfo(`API Version: ${openapi.info?.version || 'N/A'}`);
      
      if (openapi.paths) {
        const endpoints = Object.keys(openapi.paths);
        logInfo(`Total de endpoints disponíveis: ${endpoints.length}`);
        
        // Filtrar endpoints de dashboard
        const dashboardEndpoints = endpoints.filter(path => path.includes('dashboard'));
        if (dashboardEndpoints.length > 0) {
          log('\n   Endpoints do Dashboard encontrados:', 'cyan');
          dashboardEndpoints.forEach(endpoint => {
            log(`   - ${endpoint}`, 'white');
          });
        }
      }
      
      return openapi;
    }
    
    return null;
  } catch (error) {
    logError('Erro ao obter OpenAPI', error.message);
    return null;
  }
}

// Função principal
async function main() {
  logSection('🔍 DIAGNÓSTICO DO BACKEND - WHATSAPP AGENT');
  
  logInfo(`URL Base: ${API_BASE_URL}`);
  logInfo(`Usuário Admin: ${ADMIN_USERNAME}`);
  logInfo(`Data/Hora: ${new Date().toLocaleString()}`);
  
  // Teste 1: Login
  logSection('1. TESTE DE AUTENTICAÇÃO');
  const token = await login();
  
  if (!token) {
    logError('Impossível continuar sem token de autenticação');
    process.exit(1);
  }
  
  // Teste 2: OpenAPI
  logSection('2. INFORMAÇÕES DA API');
  await getOpenAPIInfo(token);
  
  // Teste 3: Endpoints do Dashboard
  logSection('3. TESTE DOS ENDPOINTS DO DASHBOARD');
  
  const dashboardEndpoints = [
    { 
      path: '/api/dashboard/stats/monthly', 
      description: 'Estatísticas Mensais do Dashboard',
      critical: true 
    },
    { 
      path: '/api/dashboard/clients', 
      description: 'Lista de Clientes',
      critical: true 
    },
    { 
      path: '/api/dashboard/stats/daily', 
      description: 'Estatísticas Diárias' 
    },
    { 
      path: '/api/dashboard/conversations', 
      description: 'Conversas' 
    },
    { 
      path: '/api/dashboard/appointments', 
      description: 'Agendamentos' 
    },
    { 
      path: '/api/dashboard/messages', 
      description: 'Mensagens' 
    }
  ];
  
  const results = [];
  
  for (const endpoint of dashboardEndpoints) {
    const result = await testEndpoint(token, endpoint.path, endpoint.description);
    results.push({
      endpoint: endpoint.path,
      description: endpoint.description,
      critical: endpoint.critical || false,
      ...result
    });
    
    // Pausa entre requests
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // Teste 4: Outros endpoints importantes
  logSection('4. TESTE DE OUTROS ENDPOINTS');
  
  const otherEndpoints = [
    { path: '/health', description: 'Health Check' },
    { path: '/api/users', description: 'Usuários' },
    { path: '/api/conversations', description: 'API de Conversas' },
    { path: '/api/appointments', description: 'API de Agendamentos' }
  ];
  
  for (const endpoint of otherEndpoints) {
    const result = await testEndpoint(token, endpoint.path, endpoint.description);
    results.push({
      endpoint: endpoint.path,
      description: endpoint.description,
      critical: false,
      ...result
    });
    
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // Resumo final
  logSection('📊 RESUMO DO DIAGNÓSTICO');
  
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);
  const criticalFailed = failed.filter(r => r.critical);
  
  logInfo(`Total de endpoints testados: ${results.length}`);
  logSuccess(`Endpoints funcionando: ${successful.length}`);
  logError(`Endpoints com erro: ${failed.length}`);
  
  if (criticalFailed.length > 0) {
    logError(`Endpoints críticos com falha: ${criticalFailed.length}`);
    criticalFailed.forEach(endpoint => {
      log(`   - ${endpoint.endpoint}: ${endpoint.description}`, 'red');
    });
  }
  
  // Análise de problemas específicos
  logSection('🔧 PROBLEMAS IDENTIFICADOS');
  
  const sqlErrors = results.filter(r => r.error && r.error.includes('AmbiguousColumnError'));
  const priceErrors = results.filter(r => r.error && r.error.includes('price'));
  const authErrors = results.filter(r => r.status === 401);
  
  if (sqlErrors.length > 0) {
    logError(`Encontrados ${sqlErrors.length} erros de SQL ambíguo`);
    logWarning('Solução sugerida: Prefixar colunas com alias de tabela (ex: u.created_at)');
  }
  
  if (priceErrors.length > 0) {
    logError(`Encontrados ${priceErrors.length} erros relacionados ao campo "price"`);
    logWarning('Solução sugerida: Verificar se a tabela appointments possui o campo price');
  }
  
  if (authErrors.length > 0) {
    logError(`Encontrados ${authErrors.length} erros de autenticação`);
    logWarning('Solução sugerida: Verificar configuração de JWT e permissões');
  }
  
  // Recomendações
  logSection('💡 RECOMENDAÇÕES');
  
  if (criticalFailed.length > 0) {
    log('AÇÃO IMEDIATA NECESSÁRIA:', 'red');
    log('1. Corrigir erros SQL ambíguos no backend', 'yellow');
    log('2. Verificar estrutura da tabela appointments (campo price)', 'yellow');
    log('3. Atualizar queries SQL para usar aliases específicos', 'yellow');
  } else {
    logSuccess('Sistema está funcionalmente operacional!');
    log('Melhorias opcionais:', 'blue');
    log('1. Implementar cache para queries pesadas', 'blue');
    log('2. Adicionar logs estruturados', 'blue');
    log('3. Implementar health checks mais detalhados', 'blue');
  }
  
  // Salvar log
  const logFile = `diagnostic-log-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
  require('fs').writeFileSync(logFile, JSON.stringify({
    timestamp: new Date().toISOString(),
    results,
    summary: {
      total: results.length,
      successful: successful.length,
      failed: failed.length,
      criticalFailed: criticalFailed.length
    }
  }, null, 2));
  
  logInfo(`Log detalhado salvo em: ${logFile}`);
  
  console.log('\n🎯 Diagnóstico concluído!');
}

// Executar se chamado diretamente
if (require.main === module) {
  main().catch(error => {
    console.error('Erro fatal no diagnóstico:', error);
    process.exit(1);
  });
}

module.exports = { main, testEndpoint, login };
