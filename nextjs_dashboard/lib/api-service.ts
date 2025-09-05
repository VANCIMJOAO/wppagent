/**
 * API Service for WPPAgent Dashboard
 * Handles authentication, API requests, and data management
 */

// Environment configuration
// CORREÇÃO: Desabilitar proxy e usar conexão direta
const API_BASE_URL = 'https://wppagent-production.up.railway.app';
const USE_PROXY = false; // DESABILITADO - usar sempre conexão direta
const PROXY_BASE_URL = '/api/proxy';

// Authentication state
let currentToken: string | null = null;
let tokenExpiry: number | null = null;
let loginPromise: Promise<string> | null = null; // Para evitar múltiplos logins simultâneos

// Admin credentials
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'senha_admin_segura';

// Types and interfaces
export interface User {
  id: number;
  nome: string;
  telefone: string;
  data_cadastro: string;
  status: 'ativo' | 'inativo' | 'bloqueado';
  ultima_interacao: string;
}

export interface Client {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  created_at: string;
  updated_at?: string;
  
  // Estatísticas calculadas
  total_conversations: number;
  total_messages: number;
  total_appointments: number;
  confirmed_appointments: number;
  cancelled_appointments: number;
  total_spent: number;
  last_contact?: string;
}

export interface Message {
  id: number; // Changed from string to number to match backend
  conversation_id: number;
  content: string;
  message_type: string;
  sender_type: string;
  created_at: string;
  whatsapp_id?: string | null;
}

export interface ConversationMessage {
  id: string;
  contactId: string;
  content: string;
  timestamp: string;
  isFromMe: boolean;
  type: 'text' | 'image' | 'audio' | 'document';
  status: 'sent' | 'delivered' | 'read';
}

export interface Contact {
  id: string;
  name: string;
  phone: string;
  lastMessage: string;
  timestamp: string;
  unreadCount: number;
  status: 'online' | 'offline' | 'typing';
  avatar?: string;
  tags: string[];
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
  id: number; // Changed from string to number to match backend
  user_id: number;
  status: string;
  last_message_at: string | null;
  created_at: string;
  updated_at: string | null;
  user_name?: string;
  user_phone?: string;
  total_messages?: number;
  unread_messages?: number;
  last_message?: string;
}

export interface DashboardStats {
  // Totais gerais (baseado na resposta real do backend)
  total_clients: number;
  total_conversations: number;
  total_appointments: number;
  total_messages: number;
  
  // Dados de hoje (baseado na resposta real do backend)
  new_clients_today: number;
  conversations_today: number;
  appointments_today: number;
  messages_today: number;
  
  // Outros dados (podem não estar disponíveis no backend)
  receita_mensal?: number;
  taxa_conversao?: number;
  tempo_resposta_medio?: number;
  satisfacao_cliente?: number;
}

export interface RecentActivity {
  id: string;
  type: 'message' | 'appointment' | 'call' | 'email';
  title: string;
  description: string;
  timestamp: string;
  user_name?: string;
  status?: string;
}

// Authentication functions
async function login(): Promise<string> {
  try {
    const loginUrl = USE_PROXY 
      ? `${PROXY_BASE_URL}/admin/login`
      : `${API_BASE_URL}/admin/login`;

    console.log('🔑 Attempting login to:', loginUrl);

    const response = await fetch(loginUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'senha_admin_segura'
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Login failed:', response.status, errorText);
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
    console.log('✅ Login successful, token acquired and stored');
    console.log('📝 Token length:', data.access_token.length);
    console.log('📝 Token expires at:', new Date(tokenExpiry).toISOString());
    return currentToken!;
  } catch (error) {
    console.error('❌ Login error:', error);
    throw error;
  }
}

// Get valid token (login if needed)
async function getValidToken(): Promise<string> {
  console.log('🔄 Getting valid token...');
  console.log('🔍 Current token exists:', !!currentToken);
  console.log('🔍 Token expiry:', tokenExpiry ? new Date(tokenExpiry).toISOString() : 'None');
  
  // If no token or token expired, login
  if (!currentToken || !tokenExpiry || Date.now() > tokenExpiry - 60000) { // Refresh 1 min before expiry
    console.log('🔄 Need to login - token missing or expired');
    
    // Se já existe uma tentativa de login em andamento, aguarda ela
    if (loginPromise) {
      console.log('🔄 Aguardando login em andamento...');
      return await loginPromise;
    }
    
    // Inicia novo login
    loginPromise = login();
    
    try {
      const token = await loginPromise;
      loginPromise = null; // Reset após sucesso
      return token;
    } catch (error) {
      loginPromise = null; // Reset após erro
      throw error;
    }
  }
  
  console.log('✅ Using existing token');
  return currentToken;
}

// Helper function to make API requests
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    const token = await getValidToken();
    const url = USE_PROXY ? `${PROXY_BASE_URL}${endpoint}` : `${API_BASE_URL}${endpoint}`;
    
    console.log('🌐 Making API request to:', url);
    console.log('🔑 Using token with length:', token.length);
    console.log('🔑 Token starts with:', token.substring(0, 20) + '...');
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
      redirect: 'follow', // Seguir redirects automaticamente
    });

    // Handle token expiration with retry
    if (response.status === 401) {
      console.warn('🔄 Token expired, retrying with new token...');
      
      // Pequeno delay para evitar rate limiting
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Force new login by clearing token state
      const oldToken = currentToken;
      currentToken = null;
      tokenExpiry = null;
      
      const newToken = await getValidToken();
      console.log('🔄 New token acquired for retry, old:', oldToken?.substring(0, 20) + '...', 'new:', newToken.substring(0, 20) + '...');
      
      const retryResponse = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${newToken}`,
          ...options.headers,
        },
        redirect: 'follow', // Seguir redirects automaticamente
      });
      
      if (!retryResponse.ok) {
        const errorText = await retryResponse.text();
        console.error('❌ Retry failed:', retryResponse.status, errorText);
        
        // Tratamento específico para rate limiting
        if (retryResponse.status === 429) {
          throw new Error('Muitas requisições. Aguarde alguns segundos e tente novamente.');
        }
        
        throw new Error(`Retry failed: ${retryResponse.status} - ${errorText}`);
      }
      
      console.log('✅ Retry successful');
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
      
      if (response.status === 429) {
        console.warn('⏰ Rate limit exceeded, waiting 5 seconds...');
        await new Promise(resolve => setTimeout(resolve, 5000));
        throw new Error('Muitas requisições. Aguarde alguns segundos e tente novamente.');
      }
      
      throw new Error(`Servidor retornou erro ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    console.log('✅ API request successful');
    return result;
  } catch (error) {
    console.error('❌ API request failed:', error);
    
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
export async function getDashboardStats(): Promise<DashboardStats> {
  try {
    console.log('🌐 Attempting to fetch dashboard stats from backend API');
    const response = await apiRequest<DashboardStats>('/api/dashboard/stats/daily', {
      method: 'GET'
    });
    
    console.log('✅ Dashboard stats fetched successfully:', response);
    return response;
  } catch (error) {
    console.error('Erro ao buscar estatísticas do dashboard:', error);
    // Retorna dados padrão em caso de erro
    return {
      total_clients: 0,
      total_conversations: 0,
      total_appointments: 0,
      total_messages: 0,
      new_clients_today: 0,
      conversations_today: 0,
      appointments_today: 0,
      messages_today: 0,
      receita_mensal: 0,
      taxa_conversao: 0,
      tempo_resposta_medio: 0,
      satisfacao_cliente: 0
    };
  }
}

export async function getRecentActivity(limit: number = 8): Promise<RecentActivity[]> {
  try {
    const response = await apiRequest<RecentActivity[]>(`/api/dashboard/recent-activity?limit=${limit}`, {
      method: 'GET'
    });
    console.log('✅ Recent activity fetched successfully');
    return response;
  } catch (error) {
    console.error('Erro ao buscar atividade recente:', error);
    return [];
  }
}

export const getUsers = async (): Promise<User[]> => {
  try {
    const users = await apiRequest<User[]>('/users');
    return users;
  } catch (error) {
    console.error('Erro ao buscar usuários:', error);
    return [];
  }
};

export const getMessages = async (): Promise<Message[]> => {
  try {
    const messages = await apiRequest<Message[]>('/messages');
    return messages;
  } catch (error) {
    console.error('Erro ao buscar mensagens:', error);
    return [];
  }
};

export const getAppointments = async (): Promise<Appointment[]> => {
  try {
    let allAppointments: Appointment[] = [];
    let offset = 0;
    const limit = 1000;
    let hasMoreData = true;

    console.log('🔍 Iniciando busca de TODOS os agendamentos...');

    while (hasMoreData) {
      let query = `/api/dashboard/appointments?limit=${limit}&offset=${offset}`;
      
      console.log(`📥 Buscando página ${Math.floor(offset/limit) + 1}, offset: ${offset}`);
      
      const response = await apiRequest<Appointment[]>(query);
      const appointments = response || [];
      
      if (appointments.length === 0) {
        hasMoreData = false;
      } else {
        allAppointments.push(...appointments);
        console.log(`✅ Página ${Math.floor(offset/limit) + 1}: ${appointments.length} agendamentos`);
        
        // Se retornou menos que o limite, não há mais dados
        if (appointments.length < limit) {
          hasMoreData = false;
        } else {
          offset += limit;
        }
      }
    }

    console.log(`🎉 TOTAL de agendamentos carregados: ${allAppointments.length}`);
    return allAppointments;
  } catch (error) {
    console.error('Erro ao buscar agendamentos:', error);
    return [];
  }
};

export const getClients = async (search?: string): Promise<Client[]> => {
  try {
    let allClients: Client[] = [];
    let offset = 0;
    const limit = 1000;
    let hasMoreData = true;

    console.log('🔍 Iniciando busca de TODOS os clientes...');
    console.log('🌐 API Base URL:', API_BASE_URL);
    console.log('🔐 Current Token:', currentToken ? 'Token exists' : 'No token');

    while (hasMoreData) {
      let query = `/api/dashboard/clients?limit=${limit}&offset=${offset}`;
      if (search) query += `&search=${encodeURIComponent(search)}`;
      
      console.log(`� Buscando página ${Math.floor(offset/limit) + 1}, offset: ${offset}`);
      
      const response = await apiRequest<any>(query);
      const clients = response?.clients || response || [];
      
      if (clients.length === 0) {
        hasMoreData = false;
      } else {
        allClients.push(...clients);
        console.log(`✅ Página ${Math.floor(offset/limit) + 1}: ${clients.length} clientes`);
        
        // Se retornou menos que o limite, não há mais dados
        if (clients.length < limit) {
          hasMoreData = false;
        } else {
          offset += limit;
        }
      }
    }

    console.log(`🎉 TOTAL de clientes carregados: ${allClients.length}`);
    console.log('📊 Sample client:', allClients?.[0]);
    
    return allClients;
  } catch (error) {
    console.error('❌ Erro ao buscar clientes:', error);
    return [];
  }
};

export const getConversations = async (limit = 50, offset = 0, status?: string, search?: string): Promise<{ conversations: Conversation[], total: number }> => {
  try {
    let query = `/conversations/?limit=${limit}&offset=${offset}`;
    if (status) query += `&status=${status}`;
    if (search) query += `&search=${encodeURIComponent(search)}`;
    
    console.log('🔍 Fetching conversations from:', query);
    console.log('🌐 API Base URL:', API_BASE_URL);
    
    const response = await apiRequest<{
      conversations: Conversation[],
      total: number,
      limit: number,
      offset: number,
      has_more: boolean
    }>(query);
    
    console.log('✅ Conversations response:', response);
    
    return {
      conversations: response.conversations || [],
      total: response.total || 0
    };
  } catch (error) {
    console.error('❌ Erro ao buscar conversas:', error);
    return {
      conversations: [],
      total: 0
    };
  }
};

export const getConversationMessages = async (conversationId: number, limit = 50, offset = 0): Promise<{ messages: Message[], total: number }> => {
  try {
    const response = await apiRequest<{
      messages: Message[],
      total: number,
      limit: number,
      offset: number,
      has_more: boolean
    }>(`/conversations/${conversationId}/messages?limit=${limit}&offset=${offset}`);
    
    return {
      messages: response.messages || [],
      total: response.total || 0
    };
  } catch (error) {
    console.error('Erro ao buscar mensagens da conversa:', error);
    return {
      messages: [],
      total: 0
    };
  }
};

export const getConversation = async (conversationId: number): Promise<Conversation | null> => {
  try {
    const conversation = await apiRequest<Conversation>(`/conversations/${conversationId}`);
    return conversation;
  } catch (error) {
    console.error('Erro ao buscar conversa:', error);
    return null;
  }
};

export const updateConversationStatus = async (conversationId: number, status: string): Promise<boolean> => {
  try {
    await apiRequest(`/conversations/${conversationId}/status?status=${status}`, {
      method: 'PUT'
    });
    return true;
  } catch (error) {
    console.error('Erro ao atualizar status da conversa:', error);
    return false;
  }
};

// Convert backend conversation data to frontend Contact interface
export const convertConversationToContact = (conversation: Conversation): Contact => {
  return {
    id: conversation.id.toString(), // Convert to string to match Contact interface
    name: conversation.user_name || 'Usuário',
    phone: conversation.user_phone || 'N/A',
    lastMessage: conversation.last_message || 'Sem mensagens',
    timestamp: conversation.last_message_at ? new Date(conversation.last_message_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : 'N/A',
    unreadCount: conversation.unread_messages || 0,
    status: conversation.status === 'active' ? 'online' : 'offline',
    tags: conversation.status === 'active' ? ['ativo'] : ['inativo']
  };
};

// Convert backend message data to frontend ConversationMessage interface
export const convertMessageToConversationMessage = (message: Message): ConversationMessage => {
  // Determinar se a mensagem é do sistema/bot ('out') ou do usuário ('in')
  // sender_type no frontend é equivalente ao campo 'direction' no backend
  const isFromMe = message.sender_type === 'out'; // 'out' = mensagem do bot/sistema
  
  return {
    id: message.id.toString(), // Convert to string to match ConversationMessage interface
    contactId: message.conversation_id.toString(),
    content: message.content || '',
    timestamp: new Date(message.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    isFromMe: isFromMe,
    type: (message.message_type || 'text') as 'text' | 'image' | 'audio' | 'document',
    status: 'read'
  };
};

// Default export for easy importing
const api = {
  getDashboardStats,
  getRecentActivity,
  getUsers,
  getMessages,
  getAppointments,
  getClients,
  getConversations,
  getConversationMessages,
  getConversation,
  updateConversationStatus,
  convertConversationToContact,
  convertMessageToConversationMessage,
};

export default api;
export { api };
