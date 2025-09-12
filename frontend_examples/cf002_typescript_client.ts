/**
 * 🔧 CF002 - TypeScript Client Examples para Response Wrapper Padronizado
 * =======================================================================
 * 
 * Demonstra como consumir as APIs com response wrapper padronizado.
 * Todos os endpoints retornam: {success: boolean, data: any, error: string|null}
 */

// 🔄 Interface do Response Wrapper Padronizado CF002
export interface ApiResponse<T = any> {
  success: boolean;
  data: T | null;
  error: string | null;
}

// Tipos específicos para demonstrations
export interface Appointment {
  id: number;
  userId: number;
  dateTime: string;
  status: string;
  createdAt?: string;
}

export interface AppointmentList {
  appointments: Appointment[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  service: string;
  version?: string;
  uptime_seconds?: number;
  database?: {
    status: string;
    latency_ms: number;
  };
  memory?: {
    used_mb: number;
    available_mb: number;
  };
}

/**
 * 🔧 CF002 - API Client com Response Wrapper Padronizado
 */
export class WhatsAgentApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic API call handler que processa response wrapper automático
   */
  private async apiCall<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      const result: ApiResponse<T> = await response.json();

      // ✅ CF002 - Response wrapper padronizado sempre presente
      if (result.success) {
        return result.data!;
      } else {
        throw new Error(result.error || 'Unknown API error');
      }
    } catch (error) {
      console.error(`API call failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // 📋 CF002 Demo - Appointments
  async getAppointmentsBefore(): Promise<any> {
    // ANTES CF002 - resposta inconsistente, estrutura diferente
    return this.apiCall('/appointments-demo/before');
  }

  async getAppointmentsAfter(): Promise<AppointmentList> {
    // DEPOIS CF002 - sempre result.data contém os dados
    return this.apiCall<AppointmentList>('/appointments-demo/after');
  }

  async createAppointment(appointmentData: Partial<Appointment>): Promise<{appointment: Appointment, message: string}> {
    return this.apiCall('/appointments-demo/create-demo', {
      method: 'POST',
      body: JSON.stringify(appointmentData),
    });
  }

  // 🏥 CF002 Demo - Health Checks
  async getSimpleHealth(): Promise<HealthStatus> {
    return this.apiCall<HealthStatus>('/health-demo/simple');
  }

  async getDetailedHealth(): Promise<HealthStatus> {
    return this.apiCall<HealthStatus>('/health-demo/detailed');
  }

  async getMetrics(): Promise<any> {
    return this.apiCall('/health-demo/metrics');
  }

  // ⚠️ CF002 Demo - Error Handling
  async triggerNotFoundError(): Promise<never> {
    // Este método sempre lança erro - para demonstrar error handling
    return this.apiCall('/appointments-demo/error-demo');
  }

  async triggerValidationError(): Promise<never> {
    return this.apiCall('/appointments-demo/validation-error-demo');
  }

  async triggerServerError(): Promise<never> {
    return this.apiCall('/appointments-demo/server-error-demo');
  }
}

/**
 * 🔧 CF002 - Hooks React para consumo simplificado
 */
export const useApiCall = <T>(apiCall: () => Promise<T>) => {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const execute = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, execute };
};

/**
 * 🔧 CF002 - Exemplo de uso nos componentes React
 */
export const AppointmentListComponent: React.FC = () => {
  const client = new WhatsAgentApiClient();
  
  const {
    data: appointments,
    loading,
    error,
    execute: loadAppointments
  } = useApiCall(() => client.getAppointmentsAfter());

  React.useEffect(() => {
    loadAppointments();
  }, []);

  if (loading) return <div>Carregando agendamentos...</div>;
  if (error) return <div>Erro: {error}</div>;
  if (!appointments) return <div>Nenhum agendamento encontrado</div>;

  return (
    <div>
      <h2>Agendamentos ({appointments.total})</h2>
      {appointments.appointments.map(appointment => (
        <div key={appointment.id}>
          <p>ID: {appointment.id}</p>
          <p>Usuário: {appointment.userId}</p>
          <p>Data: {appointment.dateTime}</p>
          <p>Status: {appointment.status}</p>
        </div>
      ))}
      {appointments.has_next && (
        <button>Carregar mais</button>
      )}
    </div>
  );
};

/**
 * 🔧 CF002 - Demonstração de error handling padronizado
 */
export const ErrorHandlingDemo: React.FC = () => {
  const client = new WhatsAgentApiClient();
  const [lastError, setLastError] = React.useState<string>('');

  const testErrors = async () => {
    const errorTests = [
      { name: '404 Not Found', call: () => client.triggerNotFoundError() },
      { name: '400 Validation Error', call: () => client.triggerValidationError() },
      { name: '500 Server Error', call: () => client.triggerServerError() },
    ];

    for (const test of errorTests) {
      try {
        await test.call();
      } catch (error) {
        console.log(`✅ ${test.name}: ${error instanceof Error ? error.message : error}`);
        setLastError(`${test.name}: ${error instanceof Error ? error.message : error}`);
      }
    }
  };

  return (
    <div>
      <h2>CF002 - Error Handling Demo</h2>
      <button onClick={testErrors}>Testar Erros Padronizados</button>
      {lastError && (
        <div style={{backgroundColor: '#ffebee', padding: '10px', marginTop: '10px'}}>
          <strong>Último erro capturado:</strong> {lastError}
        </div>
      )}
    </div>
  );
};

// 🔧 CF002 - Export da instância cliente para uso global
export const apiClient = new WhatsAgentApiClient();
