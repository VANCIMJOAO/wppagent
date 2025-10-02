#!/usr/bin/env node

/**
 * Script de Execução de Testes E2E
 * ================================
 * 
 * Executa todos os testes E2E dos fluxos críticos:
 * - CRUD de Agendamentos
 * - CRUD de Clientes  
 * - WebSocket e Tempo Real
 * - Edge Cases e Validações
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configurações
const CONFIG = {
  baseUrl: 'http://localhost:3000',
  timeout: 30000,
  retries: 2,
  workers: 4,
  browsers: ['chromium', 'firefox', 'webkit'],
  mobileBrowsers: ['Mobile Chrome', 'Mobile Safari']
};

// Cores para output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Utilitários
function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  log(`\n${'='.repeat(60)}`, 'cyan');
  log(`  ${title}`, 'bright');
  log(`${'='.repeat(60)}`, 'cyan');
}

function logStep(step) {
  log(`\n▶ ${step}`, 'yellow');
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green');
}

function logError(message) {
  log(`❌ ${message}`, 'red');
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

// Verificações pré-teste
function checkPrerequisites() {
  logSection('VERIFICAÇÕES PRÉ-TESTE');
  
  // Verificar se Node.js está instalado
  try {
    const nodeVersion = execSync('node --version', { encoding: 'utf8' }).trim();
    logSuccess(`Node.js: ${nodeVersion}`);
  } catch (error) {
    logError('Node.js não encontrado');
    process.exit(1);
  }
  
  // Verificar se Playwright está instalado
  try {
    const playwrightVersion = execSync('npx playwright --version', { encoding: 'utf8' }).trim();
    logSuccess(`Playwright: ${playwrightVersion}`);
  } catch (error) {
    logError('Playwright não encontrado. Execute: npm install @playwright/test');
    process.exit(1);
  }
  
  // Verificar se servidor está rodando
  try {
    execSync('curl -s http://localhost:3000 > /dev/null', { encoding: 'utf8' });
    logSuccess('Servidor Next.js rodando em http://localhost:3000');
  } catch (error) {
    logWarning('Servidor Next.js não está rodando. Iniciando...');
    // Aqui você pode adicionar lógica para iniciar o servidor
  }
  
  // Verificar se backend está rodando
  try {
    execSync('curl -s http://localhost:8000/health > /dev/null', { encoding: 'utf8' });
    logSuccess('Backend rodando em http://localhost:8000');
  } catch (error) {
    logWarning('Backend não está rodando. Alguns testes podem falhar.');
  }
}

// Executar testes por categoria
function runTestCategory(category, description) {
  logSection(`EXECUTANDO: ${description}`);
  
  const testFiles = {
    'crud-appointments': 'tests/crud-appointments-flow.spec.ts',
    'crud-clients': 'tests/crud-clients-flow.spec.ts',
    'websocket': 'tests/websocket-realtime.spec.ts',
    'edge-cases': 'tests/edge-cases-validation.spec.ts'
  };
  
  const testFile = testFiles[category];
  if (!testFile) {
    logError(`Categoria de teste não encontrada: ${category}`);
    return false;
  }
  
  try {
    logStep(`Executando ${testFile}...`);
    
    const command = `npx playwright test ${testFile} --reporter=html,json,junit`;
    const output = execSync(command, { 
      encoding: 'utf8',
      stdio: 'pipe',
      timeout: 300000 // 5 minutos
    });
    
    logSuccess(`${description} - Concluído`);
    return true;
  } catch (error) {
    logError(`${description} - Falhou`);
    logError(error.message);
    return false;
  }
}

// Executar todos os testes
function runAllTests() {
  logSection('EXECUTANDO TODOS OS TESTES E2E');
  
  const testCategories = [
    { category: 'crud-appointments', description: 'CRUD de Agendamentos' },
    { category: 'crud-clients', description: 'CRUD de Clientes' },
    { category: 'websocket', description: 'WebSocket e Tempo Real' },
    { category: 'edge-cases', description: 'Edge Cases e Validações' }
  ];
  
  const results = {};
  
  for (const test of testCategories) {
    results[test.category] = runTestCategory(test.category, test.description);
  }
  
  return results;
}

// Executar testes por navegador
function runTestsByBrowser() {
  logSection('EXECUTANDO TESTES POR NAVEGADOR');
  
  const browsers = CONFIG.browsers.concat(CONFIG.mobileBrowsers);
  const results = {};
  
  for (const browser of browsers) {
    logStep(`Executando testes no ${browser}...`);
    
    try {
      const command = `npx playwright test --project="${browser}" --reporter=html,json,junit`;
      execSync(command, { 
        encoding: 'utf8',
        stdio: 'pipe',
        timeout: 300000
      });
      
      logSuccess(`${browser} - Concluído`);
      results[browser] = true;
    } catch (error) {
      logError(`${browser} - Falhou`);
      results[browser] = false;
    }
  }
  
  return results;
}

// Gerar relatório final
function generateReport(results) {
  logSection('RELATÓRIO FINAL');
  
  const totalTests = Object.keys(results).length;
  const passedTests = Object.values(results).filter(Boolean).length;
  const failedTests = totalTests - passedTests;
  
  log(`\n📊 RESUMO DOS TESTES:`);
  log(`   Total: ${totalTests}`);
  log(`   ✅ Aprovados: ${passedTests}`, 'green');
  log(`   ❌ Falharam: ${failedTests}`, failedTests > 0 ? 'red' : 'green');
  log(`   📈 Taxa de Sucesso: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
  
  if (failedTests > 0) {
    log(`\n❌ TESTES QUE FALHARAM:`);
    Object.entries(results).forEach(([test, passed]) => {
      if (!passed) {
        log(`   - ${test}`, 'red');
      }
    });
  }
  
  log(`\n📁 RELATÓRIOS GERADOS:`);
  log(`   - HTML: playwright-report/index.html`);
  log(`   - JSON: test-results/results.json`);
  log(`   - JUnit: test-results/results.xml`);
  
  log(`\n🔍 PARA DEBUG:`);
  log(`   - Screenshots: test-results/`);
  log(`   - Videos: test-results/`);
  log(`   - Trace: npx playwright show-trace test-results/trace.zip`);
}

// Função principal
function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'all';
  
  logSection('TESTES E2E - FLUXOS CRÍTICOS');
  log(`Comando: ${command}`);
  log(`Timestamp: ${new Date().toISOString()}`);
  
  // Verificações pré-teste
  checkPrerequisites();
  
  let results = {};
  
  switch (command) {
    case 'all':
      results = runAllTests();
      break;
      
    case 'appointments':
      results = { 'crud-appointments': runTestCategory('crud-appointments', 'CRUD de Agendamentos') };
      break;
      
    case 'clients':
      results = { 'crud-clients': runTestCategory('crud-clients', 'CRUD de Clientes') };
      break;
      
    case 'websocket':
      results = { 'websocket': runTestCategory('websocket', 'WebSocket e Tempo Real') };
      break;
      
    case 'edge-cases':
      results = { 'edge-cases': runTestCategory('edge-cases', 'Edge Cases e Validações') };
      break;
      
    case 'browsers':
      results = runTestsByBrowser();
      break;
      
    case 'help':
      log(`\n📖 COMANDOS DISPONÍVEIS:`);
      log(`   all          - Executar todos os testes`);
      log(`   appointments - Testes de CRUD de agendamentos`);
      log(`   clients      - Testes de CRUD de clientes`);
      log(`   websocket    - Testes de WebSocket e tempo real`);
      log(`   edge-cases   - Testes de edge cases e validações`);
      log(`   browsers     - Executar testes em todos os navegadores`);
      log(`   help         - Mostrar esta ajuda`);
      return;
      
    default:
      logError(`Comando não reconhecido: ${command}`);
      log(`Use 'help' para ver comandos disponíveis`);
      process.exit(1);
  }
  
  // Gerar relatório
  generateReport(results);
  
  // Exit code baseado nos resultados
  const hasFailures = Object.values(results).some(result => !result);
  process.exit(hasFailures ? 1 : 0);
}

// Executar se chamado diretamente
if (require.main === module) {
  main();
}

module.exports = {
  runAllTests,
  runTestCategory,
  runTestsByBrowser,
  generateReport
};



