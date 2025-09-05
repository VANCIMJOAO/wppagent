// Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = process.env.NEXT_PUBLIC_ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || 'senha_admin_segura';

// Token management
let currentToken: string | null = null;
let tokenExpiry: number | null = null;

// Use proxy in development to avoid CORS issues
const USE_PROXY = typeof window !== 'undefined' && window.location.hostname === 'localhost';
const PROXY_BASE_URL = '/api/proxy';

// Login function to get new token
async function login(): Promise<string> {
  try {
    const loginUrl = `${API_BASE_URL}/admin/login`;
    const response = await fetch(loginUrl, {
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
      throw new Error(`Login failed: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data.access_token) {
      throw new Error('No access token received');
    }

    // Decode JWT to get expiry (basic decode, not verification)
    try {
      const payload = JSON.parse(atob(data.access_token.split('.')[1]));
      tokenExpiry = payload.exp * 1000; // Convert to milliseconds
    } catch (e) {
      // If we can't decode, assume 30 minutes
      tokenExpiry = Date.now() + (30 * 60 * 1000);
    }

    currentToken = data.access_token;
    return currentToken!;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

// Get valid token (login if needed)
async function getValidToken(): Promise<string> {
  // If no token or token expired, login
  if (!currentToken || !tokenExpiry || Date.now() > tokenExpiry - 60000) { // Refresh 1 min before expiry
    const token = await login();
    return token;
  }
  return currentToken;
}

// Types
export interface Client {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  data_cadastro: string;
  status: 'ativo' | 'inativo';
  tags?: string[];
}

export interface Appointment {
  id: number;
  cliente_id: number;
  cliente_nome: string;
  data_agendamento: string;
  horario: string;
  servico: string;
  status: 'agendado' | 'confirmado' | 'realizado' | 'cancelado';
  observacoes?: string;
}

export interface Conversation {
  id: number;
  cliente_id: number;
  cliente_nome: string;
  ultima_mensagem: string;
  data_ultima_mensagem: string;
  status: 'ativo' | 'arquivado';
  nao_lidas: number;
}

export interface DashboardStats {
  total_clientes: number;
  agendamentos_hoje: number;
  mensagens_nao_lidas: number;
  conversas_ativas: number;
  receita_mensal: number;
  crescimento_clientes: number;
}

// Helper function to make API requests
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    const token = await getValidToken();
    const url = USE_PROXY ? `${PROXY_BASE_URL}${endpoint}` : `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (response.status === 401) {
      // Token expired, try to refresh once
      currentToken = null; // Force new login
      const newToken = await getValidToken();
      
      // Retry the request with new token
      const retryResponse = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${newToken}`,
          ...options.headers,
        },
      });
      
      if (!retryResponse.ok) {
        const errorText = await retryResponse.text();
        throw new Error(`Servidor retornou erro ${retryResponse.status}: ${errorText}`);
      }
      
      return retryResponse.json();
    }

    if (!response.ok) {
      const errorText = await response.text();
      
      // Enhanced error handling for known backend SQL issues
      if (response.status === 500) {
        if (errorText.includes('AmbiguousColumnError')) {
          console.error('Backend SQL Error: Ambiguous column detected');
          throw new Error('Erro no servidor: Problema na consulta SQL (coluna ambígua). O backend precisa de correção.');
        }
        if (errorText.includes('has no attribute') && errorText.includes('price')) {
          console.error('Backend SQL Error: Missing price field');
          throw new Error('Erro no servidor: Campo "price" não encontrado. O backend precisa de correção.');
        }
        if (errorText.includes('ProgrammingError')) {
          console.error('Backend SQL Error: Programming error detected');
          throw new Error('Erro no servidor: Problema na consulta SQL. O backend precisa de correção.');
        }
        throw new Error('Erro interno do servidor. Tente novamente em alguns minutos.');
      }
      
      if (response.status === 404) {
        throw new Error('Endpoint não encontrado. Verifique se o backend está atualizado.');
      }
      
      throw new Error(`Servidor retornou erro ${response.status}: ${errorText}`);
    }

    return response.json();
  } catch (error) {
    console.error('API request failed:', error);
    
    if (error instanceof Error) {
      // Se for um erro de rede ou timeout
      if (error.message.includes('fetch')) {
        throw new Error('Erro de conectividade - Verifique sua conexão com a internet');
      }
      throw error;
    } else {
      throw new Error('Erro desconhecido ao conectar com o servidor');
    }
  }
}

// API methods with enhanced error handling
export const getDashboardStats = async (): Promise<DashboardStats> => {
  try {
    // Get daily stats from the new endpoint
    const dailyStats = await apiRequest<any>('/api/dashboard/stats/daily');
    
    console.log('Backend daily stats:', dailyStats);
    
    // Convert backend response to our interface with real daily data
    return {
      total_clientes: dailyStats.total_clients || 0,
      agendamentos_hoje: dailyStats.appointments_today || 0,
      mensagens_nao_lidas: dailyStats.messages_today || 0,
      conversas_ativas: dailyStats.total_conversations || 0,
      receita_mensal: 0, // TODO: implement revenue calculation
      crescimento_clientes: 5.2, // mock for now
    };
  } catch (error) {
    console.error('Erro ao buscar estatísticas do dashboard:', error);
    
    // Check if it's a known SQL error and provide better error message
    if (error instanceof Error) {
      if (error.message.includes('AmbiguousColumnError')) {
        console.warn('Backend SQL error detected: Ambiguous column. Using fallback data.');
      }
      if (error.message.includes('price')) {
        console.warn('Backend SQL error detected: Missing price field. Using fallback data.');
      }
    }
    
    // Return safe defaults when backend fails due to SQL errors
    return {
      total_clientes: 0,
      agendamentos_hoje: 0,
      mensagens_nao_lidas: 0,
      conversas_ativas: 0,
      receita_mensal: 0,
      crescimento_clientes: 0,
    };
  }
};

export const getClients = async (): Promise<Client[]> => {
  try {
    return await apiRequest<Client[]>('/api/dashboard/clients');
  } catch (error) {
    console.error('Erro ao buscar clientes:', error);
    
    // Check if it's a known backend error
    if (error instanceof Error) {
      if (error.message.includes('500')) {
        console.warn('Backend error detected for clients endpoint. Using empty list.');
      }
    }
    
    // Return empty array when backend fails
    return [];
  }
};

export const getClient = async (id: number): Promise<Client> => {
  return apiRequest<Client>(`/clients/${id}`);
};

export const createClient = async (client: Omit<Client, 'id' | 'data_cadastro'>): Promise<Client> => {
  return apiRequest<Client>('/clients', {
    method: 'POST',
    body: JSON.stringify(client),
  });
};

export const updateClient = async (id: number, client: Partial<Client>): Promise<Client> => {
  return apiRequest<Client>(`/clients/${id}`, {
    method: 'PUT',
    body: JSON.stringify(client),
  });
};

export const deleteClient = async (id: number): Promise<void> => {
  return apiRequest<void>(`/clients/${id}`, {
    method: 'DELETE',
  });
};

export const getAppointments = async (): Promise<Appointment[]> => {
  return apiRequest<Appointment[]>('/appointments');
};

export const getAppointment = async (id: number): Promise<Appointment> => {
  return apiRequest<Appointment>(`/appointments/${id}`);
};

export const createAppointment = async (appointment: Omit<Appointment, 'id'>): Promise<Appointment> => {
  return apiRequest<Appointment>('/appointments', {
    method: 'POST',
    body: JSON.stringify(appointment),
  });
};

export const updateAppointment = async (id: number, appointment: Partial<Appointment>): Promise<Appointment> => {
  return apiRequest<Appointment>(`/appointments/${id}`, {
    method: 'PUT',
    body: JSON.stringify(appointment),
  });
};

export const deleteAppointment = async (id: number): Promise<void> => {
  return apiRequest<void>(`/appointments/${id}`, {
    method: 'DELETE',
  });
};

// Recent activity interface
interface RecentActivity {
  id: number;
  type: string; // 'new_client', 'new_conversation', 'new_appointment', 'new_message'
  title: string;
  description: string;
  timestamp: string;
  user_name?: string;
  user_phone?: string;
}

export const getRecentActivity = async (limit: number = 10): Promise<RecentActivity[]> => {
  try {
    return await apiRequest<RecentActivity[]>(`/api/dashboard/recent-activity?limit=${limit}`);
  } catch (error) {
    console.error('Erro ao buscar atividades recentes:', error);
    
    // Return mock recent activities when backend fails
    return [
      {
        id: 1,
        type: 'new_client',
        title: 'Novo cliente cadastrado',
        description: 'Cliente se cadastrou no sistema',
        timestamp: new Date().toISOString(),
        user_name: 'Cliente Exemplo',
        user_phone: '5511999999999'
      },
      {
        id: 2,
        type: 'new_conversation',
        title: 'Nova conversa iniciada',
        description: 'Conversa iniciada via WhatsApp',
        timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 min ago
        user_name: 'Outro Cliente',
        user_phone: '5511888888888'
      }
    ];
  }
};

export const getConversations = async (): Promise<Conversation[]> => {
  return apiRequest<Conversation[]>('/conversations');
};

export const getConversation = async (id: number): Promise<Conversation> => {
  return apiRequest<Conversation>(`/conversations/${id}`);
};

// Configuration endpoints
export const getBotConfig = async () => {
  return apiRequest('/bot/config');
};

export const updateBotConfig = async (config: any) => {
  return apiRequest('/bot/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  });
};

export const getReports = async (type: string, startDate?: string, endDate?: string) => {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  
  return apiRequest(`/reports/${type}?${params.toString()}`);
};

// Export a default object for compatibility
export default {
  getDashboardStats,
  getClients,
  getClient,
  createClient,
  updateClient,
  deleteClient,
  getAppointments,
  getAppointment,
  createAppointment,
  updateAppointment,
  deleteAppointment,
  getRecentActivity,
  getConversations,
  getConversation,
  getBotConfig,
  updateBotConfig,
  getReports,
};