#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 EXECUTOR DE TESTES COMPLETOS DO DASHBOARD NEXT.JS');
console.log('====================================================');
console.log('');

// Verificar se Playwright está instalado
try {
  execSync('npx playwright --version', { stdio: 'pipe' });
  console.log('✅ Playwright encontrado');
} catch (error) {
  console.log('❌ Playwright não encontrado. Instalando...');
  execSync('npm install @playwright/test', { stdio: 'inherit' });
  execSync('npx playwright install', { stdio: 'inherit' });
  console.log('✅ Playwright instalado com sucesso');
}

// Verificar se servidor está rodando
const checkServer = () => {
  try {
    const response = execSync('curl -s http://localhost:3000', { stdio: 'pipe' });
    return true;
  } catch (error) {
    return false;
  }
};

if (!checkServer()) {
  console.log('⚠️  Servidor não está rodando. Iniciando servidor...');
  console.log('   Execute: npm run dev');
  console.log('   Aguarde o servidor iniciar e execute os testes novamente.');
  process.exit(1);
}

console.log('✅ Servidor está rodando');
console.log('');

// Executar testes
const testSuites = [
  {
    name: 'Dashboard Completo - Todas as Funcionalidades',
    file: 'dashboard-complete.spec.ts',
    description: 'Testa todas as 17 páginas e funcionalidades principais'
  },
  {
    name: 'CRUD Operations - Operações de Banco',
    file: 'crud-operations.spec.ts',
    description: 'Testa operações Create, Read, Update, Delete em todas as entidades'
  },
  {
    name: 'Funcionalidades em Tempo Real',
    file: 'realtime-features.spec.ts',
    description: 'Testa WebSocket, atualizações em tempo real e notificações'
  },
  {
    name: 'Exportação e Relatórios',
    file: 'export-reports.spec.ts',
    description: 'Testa exportação CSV, Excel, PDF e geração de relatórios'
  },
  {
    name: 'Autenticação e RBAC',
    file: 'auth-rbac.spec.ts',
    description: 'Testa login, logout, permissões e controle de acesso'
  },
  {
    name: 'PWA e Funcionalidades Offline',
    file: 'pwa-offline.spec.ts',
    description: 'Testa Service Worker, cache, offline e responsividade'
  }
];

// Função para executar um conjunto de testes
const runTestSuite = (suite) => {
  console.log(`🧪 Executando: ${suite.name}`);
  console.log(`   📝 ${suite.description}`);
  console.log('');
  
  try {
    execSync(`npx playwright test tests/${suite.file} --reporter=html`, { 
      stdio: 'inherit',
      cwd: process.cwd()
    });
    console.log(`✅ ${suite.name} - PASSOU`);
  } catch (error) {
    console.log(`❌ ${suite.name} - FALHOU`);
    console.log(`   Erro: ${error.message}`);
  }
  
  console.log('');
};

// Executar todos os conjuntos de testes
console.log('📊 RESUMO DOS TESTES:');
console.log('====================');
console.log('');

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

for (const suite of testSuites) {
  console.log(`📋 ${suite.name}`);
  console.log(`   ${suite.description}`);
  totalTests++;
  
  try {
    runTestSuite(suite);
    passedTests++;
  } catch (error) {
    failedTests++;
  }
}

// Relatório final
console.log('📈 RELATÓRIO FINAL:');
console.log('==================');
console.log(`Total de Suites: ${totalTests}`);
console.log(`✅ Passou: ${passedTests}`);
console.log(`❌ Falhou: ${failedTests}`);
console.log(`📊 Taxa de Sucesso: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
console.log('');

if (failedTests > 0) {
  console.log('🔍 Para ver detalhes dos testes que falharam:');
  console.log('   npx playwright show-report');
  console.log('');
}

console.log('🎯 TESTES CONCLUÍDOS!');
console.log('=====================');
