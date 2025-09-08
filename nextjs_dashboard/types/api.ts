/**
 * Tipos TypeScript para API responses - WPPAgent Dashboard
 * Elimina o uso de 'any' types por tipos específicos e seguros
 */

// Resposta base da API
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
  error?: string;
  status?: number;
}

// Resposta paginada genérica
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
  next_page?: number;
  prev_page?: number;
}

// Cliente (compatível com api-service.ts)
export interface Client {
  id: number;
  wa_id: string;
  nome?: string;
  telefone?: string;
  email?: string;
  created_at: string;
  updated_at?: string;
  
  // Campos calculados
  total_conversations: number;
  total_messages: number;
  total_appointments: number;
  last_interaction?: string;
  status: 'active' | 'inactive' | 'new' | 'vip';
}

// Estatísticas detalhadas de um cliente
export interface ClientStatistics {
  total_conversations: number;
  total_messages: number;
  total_appointments: number;
  last_interaction?: string;
  avg_response_time_seconds: number;
}

// Detalhes completos de um cliente
export interface ClientDetail extends Client {
  statistics: ClientStatistics;
}

// Interface para update de cliente
export interface ClientUpdate {
  nome?: string;
  telefone?: string;
  email?: string;
}

// Interface para criação de cliente
export interface ClientCreate {
  wa_id: string;
  nome: string;
  telefone: string;
  email?: string;
}

// Resposta específica para clientes
export interface ClientsResponse {
  clients: Client[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// Usuário/Administrador
export interface User {
  id: number | string;
  nome: string;
  email: string;
  telefone?: string;
  role: 'admin' | 'user' | 'moderator';
  avatar_url?: string;
  data_cadastro: string;
  ultimo_acesso: string;
  status: 'ativo' | 'inativo';
}

// Dados de autenticação
export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  permissions?: string[];
}

// Login request
export interface LoginRequest {
  username: string;
  password: string;
  remember?: boolean;
}

// Conversa/Chat (compatível com api-service.ts)
export interface Conversation {
  id: number;
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

// Mensagem (compatível com api-service.ts)
export interface Message {
  id: number;
  conversation_id: number;
  content: string;
  sender_type: 'in' | 'out';
  created_at: string;
  message_type?: 'text' | 'image' | 'audio' | 'video' | 'document';
  media_url?: string;
  metadata?: Record<string, any>;
}

// ✅ AGENDAMENTO PADRONIZADO - Consistente com backend
export interface Appointment {
  id: number;
  user_id: number;  // ✅ Padronizado
  business_id: number;
  service_id?: number;
  
  // ✅ Campos padronizados com backend
  date_time: string;  // ✅ ISO string format
  duration_minutes: number;  // ✅ Padronizado
  end_time?: string;  // ISO string
  price: number;  // ✅ Unificado
  
  // Status e observações
  status: 'pendente' | 'confirmado' | 'realizado' | 'cancelado' | 'concluido' | 'bloqueado';
  notes?: string;
  
  // ✅ Campos relacionados com nomes padronizados
  cliente_nome?: string;  // Mapeado de user.nome
  cliente_telefone?: string;  // Mapeado de user.telefone
  cliente_email?: string;  // Mapeado de user.email
  servico_nome?: string;  // Mapeado de service.name
  business_name?: string;
  
  // Auditoria
  created_at: string;
  updated_at?: string;
  
  // Campos de cancelamento/confirmação (opcionais)
  cancelled_at?: string;
  cancellation_reason?: string;
  cancelled_by?: string;
  confirmed_at?: string;
  confirmed_by?: string;
}

// ✅ Tipos para mapeamento de status padronizados
export type AppointmentStatus = 'pendente' | 'confirmado' | 'realizado' | 'cancelado' | 'concluido' | 'bloqueado';

// Resposta de agendamentos
export interface AppointmentsResponse {
  appointments: Appointment[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// Métricas do Dashboard
export interface DashboardMetrics {
  total_clients: number;
  active_conversations: number;
  pending_appointments: number;
  messages_today: number;
  response_time_avg: number;
  client_satisfaction: number;
  growth_rate: number;
  active_sessions: number;
}

// Dados do Dashboard
export interface DashboardData {
  metrics: DashboardMetrics;
  recent_conversations: Conversation[];
  upcoming_appointments: Appointment[];
  activity_chart: ChartData[];
  client_stats: ClientStats;
}

// Dados de gráfico
export interface ChartData {
  date: string;
  messages: number;
  conversations: number;
  appointments: number;
  clients: number;
}

// Estatísticas de clientes
export interface ClientStats {
  total: number;
  active: number;
  new_this_month: number;
  inactive: number;
}

// Configuração do Bot
export interface BotConfig {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  auto_reply: boolean;
  greeting_message?: string;
  fallback_message?: string;
  working_hours: {
    start: string;
    end: string;
    days: string[];
  };
  settings: Record<string, any>;
}

// Resposta de erro da API
export interface ApiError {
  error: string;
  message: string;
  code?: string;
  details?: Record<string, any>;
  timestamp: string;
}

// Filtros de busca
export interface SearchFilters {
  query?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// Upload de arquivo
export interface FileUpload {
  file: File;
  type: 'image' | 'audio' | 'video' | 'document';
  progress?: number;
}

// Resposta de upload
export interface UploadResponse {
  url: string;
  filename: string;
  size: number;
  type: string;
  uploaded_at: string;
}

// Webhook payload
export interface WebhookPayload {
  event: string;
  data: Record<string, any>;
  timestamp: string;
  source: string;
}

// Sistema de logs
export interface LogEntry {
  id: number;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: string;
  source: string;
  user_id?: number;
  metadata?: Record<string, any>;
}

// Configurações do sistema
export interface SystemSettings {
  app_name: string;
  app_version: string;
  maintenance_mode: boolean;
  max_upload_size: number;
  allowed_file_types: string[];
  session_timeout: number;
  api_rate_limit: number;
  features: {
    auto_backup: boolean;
    email_notifications: boolean;
    sms_notifications: boolean;
    analytics: boolean;
  };
}

// Atividade Recente
export interface RecentActivity {
  id: number;
  type: 'conversation' | 'appointment' | 'message' | 'client' | 'system';
  title: string;
  description: string;
  timestamp: string;
  icon?: string;
  status?: string;
  metadata?: Record<string, any>;
}

// Dashboard Stats Completos para Loading States
export interface DashboardStatsComplete extends DashboardData {
  kpis: {
    totalClients: number;
    totalConversations: number;
    totalAppointments: number;
    totalMessages: number;
    responseTimeAvg?: number;
    satisfactionScore?: number;
    growthRate?: number;
    activeUsers?: number;
  };
  charts: {
    conversationsOverTime: ChartData[];
    appointmentsByStatus: any[];
    clientGrowth: ChartData[];
    messageVolume?: ChartData[];
  };
  recentActivity: RecentActivity[];
  loading?: boolean;
  error?: string | null;
}
