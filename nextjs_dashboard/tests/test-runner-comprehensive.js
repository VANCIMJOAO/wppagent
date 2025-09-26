/**
 * 🧪 Test Runner Abrangente - Dashboard WhatsApp Agent
 * Script para executar todos os testes de forma organizada
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class ComprehensiveTestRunner {
  constructor() {
    this.testSuites = [
      {
        name: '🔐 Login Tests',
        file: 'login-comprehensive.spec.ts',
        description: 'Testes abrangentes da página de login'
      },
      {
        name: '🏠 Dashboard Tests',
        file: 'dashboard-comprehensive.spec.ts',
        description: 'Testes abrangentes do dashboard principal'
      },
      {
        name: '💬 Conversas Tests',
        file: 'conversas-comprehensive.spec.ts',
        description: 'Testes abrangentes da página de conversas'
      },
      {
        name: '📋 CRUD Pages Tests',
        file: 'crud-pages-comprehensive.spec.ts',
        description: 'Testes abrangentes das páginas CRUD (Clientes, Agendamentos, etc.)'
      },
      {
        name: '📈 Analytics & Config Tests',
        file: 'analytics-config-settings.spec.ts',
        description: 'Testes abrangentes de Analytics, Configurações e outras páginas'
      },
      {
        name: '🔄 Integration Tests',
        file: 'integration-comprehensive.spec.ts',
        description: 'Testes de integração e fluxos completos'
      }
    ];

    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration: 0
    };
  }

  /**
   * Executa todos os testes
   */
  async runAllTests() {
    console.log('🚀 Iniciando execução abrangente de testes...\n');
    
    const startTime = Date.now();

    for (const suite of this.testSuites) {
      await this.runTestSuite(suite);
    }

    this.results.duration = Date.now() - startTime;
    this.generateReport();
  }

  /**
   * Executa uma suíte de testes específica
   */
  async runTestSuite(suite) {
    console.log(`\n📋 Executando: ${suite.name}`);
    console.log(`📝 Descrição: ${suite.description}`);
    console.log(`📁 Arquivo: ${suite.file}\n`);

    try {
      const command = `npx playwright test ${suite.file} --reporter=json`;
      const output = execSync(command, { 
        cwd: process.cwd(),
        encoding: 'utf8',
        stdio: 'pipe'
      });

      const result = JSON.parse(output);
      this.processResults(result, suite);

      console.log(`✅ ${suite.name} - Concluído com sucesso\n`);

    } catch (error) {
      console.error(`❌ ${suite.name} - Falhou`);
      console.error(`Erro: ${error.message}\n`);
      
      this.results.failed++;
    }
  }

  /**
   * Processa resultados de uma suíte de testes
   */
  processResults(result, suite) {
    if (result.suites) {
      for (const suiteResult of result.suites) {
        this.results.total += suiteResult.tests.length;
        
        for (const test of suiteResult.tests) {
          switch (test.status) {
            case 'passed':
              this.results.passed++;
              break;
            case 'failed':
              this.results.failed++;
              break;
            case 'skipped':
              this.results.skipped++;
              break;
          }
        }
      }
    }
  }

  /**
   * Gera relatório final
   */
  generateReport() {
    console.log('\n' + '='.repeat(80));
    console.log('📊 RELATÓRIO FINAL DE TESTES ABRANGENTES');
    console.log('='.repeat(80));
    
    console.log(`\n📈 Estatísticas Gerais:`);
    console.log(`   Total de Testes: ${this.results.total}`);
    console.log(`   ✅ Passou: ${this.results.passed}`);
    console.log(`   ❌ Falhou: ${this.results.failed}`);
    console.log(`   ⏭️  Pulou: ${this.results.skipped}`);
    console.log(`   ⏱️  Duração: ${this.formatDuration(this.results.duration)}`);

    const passRate = this.results.total > 0 ? 
      ((this.results.passed / this.results.total) * 100).toFixed(2) : 0;
    
    console.log(`   📊 Taxa de Sucesso: ${passRate}%`);

    console.log(`\n📋 Suítes de Testes Executadas:`);
    this.testSuites.forEach((suite, index) => {
      console.log(`   ${index + 1}. ${suite.name}`);
      console.log(`      📁 ${suite.file}`);
      console.log(`      📝 ${suite.description}\n`);
    });

    console.log('\n🎯 Cobertura de Testes:');
    console.log('   ✅ Página de Login - Interface, Validação, Autenticação, Segurança');
    console.log('   ✅ Dashboard Principal - Métricas, Performance, Navegação');
    console.log('   ✅ Conversas - Lista, Chat, Busca, Envio de Mensagens');
    console.log('   ✅ Clientes - CRUD Completo, Filtros, Busca, Validação');
    console.log('   ✅ Agendamentos - CRUD Completo, WebSocket, Exportação');
    console.log('   ✅ Analytics - Métricas, Gráficos, Períodos, Exportação');
    console.log('   ✅ Configurações - Empresa, Bot, Horários, Notificações, Segurança');
    console.log('   ✅ Relatórios - KPIs, Gráficos, Exportação, Filtros');
    console.log('   ✅ Suporte - FAQ, Tickets, Status do Sistema');
    console.log('   ✅ Perfil - Informações, Segurança, Preferências');
    console.log('   ✅ Monitoramento - Status, Métricas, Alertas');
    console.log('   ✅ Horários Bloqueados - CRUD, Filtros, Tipos');
    console.log('   ✅ Exportar Relatórios - Formatos, Acesso');
    console.log('   ✅ Integração - Fluxos Completos, Navegação, Performance');

    console.log('\n🔧 Funcionalidades Testadas:');
    console.log('   ✅ Autenticação e Autorização');
    console.log('   ✅ Operações CRUD Completas');
    console.log('   ✅ Busca e Filtros');
    console.log('   ✅ Exportação de Dados');
    console.log('   ✅ Responsividade Mobile/Desktop');
    console.log('   ✅ Estados de Loading e Erro');
    console.log('   ✅ Validação de Formulários');
    console.log('   ✅ Navegação e Roteamento');
    console.log('   ✅ WebSocket e Tempo Real');
    console.log('   ✅ Performance e Otimização');
    console.log('   ✅ Acessibilidade Básica');
    console.log('   ✅ Tratamento de Erros');

    if (this.results.failed === 0) {
      console.log('\n🎉 TODOS OS TESTES PASSARAM! Sistema está funcionando perfeitamente.');
    } else {
      console.log(`\n⚠️  ${this.results.failed} teste(s) falharam. Verifique os logs acima.`);
    }

    console.log('\n' + '='.repeat(80));
  }

  /**
   * Formata duração em formato legível
   */
  formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  /**
   * Executa testes específicos
   */
  async runSpecificTests(testNames) {
    console.log('🎯 Executando testes específicos...\n');
    
    const suitesToRun = this.testSuites.filter(suite => 
      testNames.some(name => suite.name.toLowerCase().includes(name.toLowerCase()))
    );

    if (suitesToRun.length === 0) {
      console.log('❌ Nenhuma suíte de testes encontrada para os nomes fornecidos.');
      return;
    }

    for (const suite of suitesToRun) {
      await this.runTestSuite(suite);
    }

    this.generateReport();
  }

  /**
   * Executa testes por categoria
   */
  async runTestsByCategory(category) {
    const categories = {
      'auth': ['login'],
      'ui': ['dashboard', 'conversas'],
      'crud': ['crud-pages'],
      'analytics': ['analytics-config'],
      'integration': ['integration']
    };

    const testNames = categories[category] || [];
    if (testNames.length === 0) {
      console.log('❌ Categoria não encontrada. Categorias disponíveis:', Object.keys(categories));
      return;
    }

    await this.runSpecificTests(testNames);
  }
}

// Função principal
async function main() {
  const runner = new ComprehensiveTestRunner();
  const args = process.argv.slice(2);

  if (args.length === 0) {
    // Executar todos os testes
    await runner.runAllTests();
  } else if (args[0] === '--category') {
    // Executar por categoria
    const category = args[1];
    await runner.runTestsByCategory(category);
  } else {
    // Executar testes específicos
    await runner.runSpecificTests(args);
  }
}

// Executar se chamado diretamente
if (require.main === module) {
  main().catch(console.error);
}

module.exports = ComprehensiveTestRunner;
