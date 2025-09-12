/**
 * 🔧 CF002 - JavaScript Client Examples para Response Wrapper Padronizado
 * =======================================================================
 * 
 * Demonstra como consumir as APIs com response wrapper padronizado.
 * Todos os endpoints retornam: {success: boolean, data: any, error: string|null}
 */

/**
 * 🔧 CF002 - API Client com Response Wrapper Padronizado
 */
class WhatsAgentApiClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic API call handler que processa response wrapper automático
   */
  async apiCall(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      const result = await response.json();

      // ✅ CF002 - Response wrapper padronizado sempre presente
      if (result.success) {
        return result.data;
      } else {
        throw new Error(result.error || 'Unknown API error');
      }
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // 📋 CF002 Demo - Appointments
  async getAppointmentsBefore() {
    // ANTES CF002 - resposta inconsistente, estrutura diferente
    return this.apiCall('/appointments-demo/before');
  }

  async getAppointmentsAfter() {
    // DEPOIS CF002 - sempre result.data contém os dados
    return this.apiCall('/appointments-demo/after');
  }

  async createAppointment(appointmentData) {
    return this.apiCall('/appointments-demo/create-demo', {
      method: 'POST',
      body: JSON.stringify(appointmentData),
    });
  }

  // 🏥 CF002 Demo - Health Checks
  async getSimpleHealth() {
    return this.apiCall('/health-demo/simple');
  }

  async getDetailedHealth() {
    return this.apiCall('/health-demo/detailed');
  }

  async getMetrics() {
    return this.apiCall('/health-demo/metrics');
  }

  // ⚠️ CF002 Demo - Error Handling
  async triggerNotFoundError() {
    // Este método sempre lança erro - para demonstrar error handling
    return this.apiCall('/appointments-demo/error-demo');
  }

  async triggerValidationError() {
    return this.apiCall('/appointments-demo/validation-error-demo');
  }

  async triggerServerError() {
    return this.apiCall('/appointments-demo/server-error-demo');
  }

  async triggerDatabaseError() {
    return this.apiCall('/health-demo/database-error');
  }

  async triggerUnauthorizedError() {
    return this.apiCall('/health-demo/unauthorized');
  }
}

/**
 * 🔧 CF002 - Exemplos de uso prático
 */

// Exemplo 1: Listar agendamentos com response padronizado
async function exemploListarAgendamentos() {
  const client = new WhatsAgentApiClient();
  
  try {
    console.log('📋 CF002 - Testando endpoints de appointments...\n');
    
    // ANTES CF002 - estrutura inconsistente
    const responseAntes = await client.getAppointmentsBefore();
    console.log('❌ ANTES CF002 - Estrutura inconsistente:');
    console.log(JSON.stringify(responseAntes, null, 2));
    console.log('Frontend precisa saber que os dados estão em "appointments"\n');
    
    // DEPOIS CF002 - estrutura padronizada  
    const responseDepois = await client.getAppointmentsAfter();
    console.log('✅ DEPOIS CF002 - Estrutura padronizada:');
    console.log(JSON.stringify(responseDepois, null, 2));
    console.log('Frontend sempre sabe que os dados estão em result.data\n');
    
  } catch (error) {
    console.error('Erro ao listar agendamentos:', error.message);
  }
}

// Exemplo 2: Criar agendamento
async function exemploCriarAgendamento() {
  const client = new WhatsAgentApiClient();
  
  try {
    console.log('➕ CF002 - Testando criação de agendamento...\n');
    
    const novoAgendamento = {
      userId: 789,
      dateTime: '2025-09-12T17:00:00Z'
    };
    
    const resultado = await client.createAppointment(novoAgendamento);
    console.log('✅ Agendamento criado com response padronizado:');
    console.log(JSON.stringify(resultado, null, 2));
    
  } catch (error) {
    console.error('Erro ao criar agendamento:', error.message);
  }
}

// Exemplo 3: Health checks com estruturas diferentes
async function exemploHealthChecks() {
  const client = new WhatsAgentApiClient();
  
  try {
    console.log('🏥 CF002 - Testando health checks...\n');
    
    // Simple health
    const simpleHealth = await client.getSimpleHealth();
    console.log('✅ Simple Health (wrapper automático):');
    console.log(JSON.stringify(simpleHealth, null, 2));
    console.log('');
    
    // Detailed health
    const detailedHealth = await client.getDetailedHealth();
    console.log('✅ Detailed Health (wrapper automático):');
    console.log(JSON.stringify(detailedHealth, null, 2));
    console.log('');
    
    // Metrics
    const metrics = await client.getMetrics();
    console.log('✅ Metrics (wrapper automático):');
    console.log(JSON.stringify(metrics, null, 2));
    
  } catch (error) {
    console.error('Erro ao verificar health:', error.message);
  }
}

// Exemplo 4: Error handling padronizado
async function exemploErrorHandling() {
  const client = new WhatsAgentApiClient();
  
  console.log('⚠️ CF002 - Testando error handling padronizado...\n');
  
  const errorTests = [
    { name: '404 Not Found', method: () => client.triggerNotFoundError() },
    { name: '400 Validation Error', method: () => client.triggerValidationError() },
    { name: '500 Server Error', method: () => client.triggerServerError() },
    { name: '503 Database Error', method: () => client.triggerDatabaseError() },
    { name: '401 Unauthorized', method: () => client.triggerUnauthorizedError() },
  ];

  for (const test of errorTests) {
    try {
      await test.method();
      console.log(`❌ ${test.name}: Erro esperado não foi lançado`);
    } catch (error) {
      console.log(`✅ ${test.name}: ${error.message}`);
    }
  }
}

// Exemplo 5: Demonstração completa com comparação antes/depois
async function demonstracaoCompletaCF002() {
  console.log('🔧 CF002 - DEMONSTRAÇÃO COMPLETA DO RESPONSE WRAPPER PADRONIZADO');
  console.log('================================================================\n');
  
  console.log('🎯 OBJETIVO: Padronizar todas as respostas da API no formato:');
  console.log('   {success: boolean, data: any, error: string|null}\n');
  
  console.log('📝 BENEFÍCIOS:');
  console.log('   ✅ Frontend sempre sabe onde encontrar os dados');
  console.log('   ✅ Error handling consistente em toda a aplicação');
  console.log('   ✅ Facilita integração com ferramentas de monitoramento');
  console.log('   ✅ Melhora experiência do desenvolvedor\n');
  
  await exemploListarAgendamentos();
  await exemploCriarAgendamento();
  await exemploHealthChecks();
  await exemploErrorHandling();
  
  console.log('\n🎉 CF002 - Demonstração concluída!');
  console.log('📋 Todos os endpoints agora retornam response wrapper padronizado');
}

/**
 * 🔧 CF002 - Utilitários para testes frontend
 */

// Função para simular chamadas do frontend
function criarMockFrontend() {
  const client = new WhatsAgentApiClient();
  
  return {
    // Simula componente de lista de agendamentos
    async carregarAgendamentos() {
      try {
        const agendamentos = await client.getAppointmentsAfter();
        // Frontend sempre sabe que dados estão em result.data
        return {
          success: true,
          appointments: agendamentos.appointments,
          total: agendamentos.total,
          hasNext: agendamentos.has_next
        };
      } catch (error) {
        return {
          success: false,
          error: error.message
        };
      }
    },
    
    // Simula componente de status da aplicação
    async verificarStatus() {
      try {
        const status = await client.getDetailedHealth();
        return {
          success: true,
          status: status.status,
          uptime: status.uptime_seconds,
          database: status.database?.status
        };
      } catch (error) {
        return {
          success: false,
          error: error.message
        };
      }
    },
    
    // Simula notificação de erro global
    async handleGlobalError(endpoint) {
      try {
        await client.apiCall(endpoint);
      } catch (error) {
        // CF002 garante que todos os erros têm formato consistente
        console.log(`🚨 Erro global capturado: ${error.message}`);
        return {
          shouldShowNotification: true,
          message: error.message,
          type: 'error'
        };
      }
    }
  };
}

// Instância global do cliente
const apiClient = new WhatsAgentApiClient();

// Executar demonstração se script for executado diretamente
if (typeof window === 'undefined') {
  // Node.js environment
  demonstracaoCompletaCF002().catch(console.error);
}

// Export para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    WhatsAgentApiClient,
    apiClient,
    exemploListarAgendamentos,
    exemploCriarAgendamento,
    exemploHealthChecks,
    exemploErrorHandling,
    demonstracaoCompletaCF002,
    criarMockFrontend
  };
}
