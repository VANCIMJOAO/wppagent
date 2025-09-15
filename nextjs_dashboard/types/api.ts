/**
 * 📋 Tipos TypeScript Unificados - API Contracts
 * =============================================
 *
 * Tipos padronizados que correspondem exatamente aos schemas do backend.
 * Elimina divergências entre frontend e backend.
 *
 * Autor: Claude AI
 * Data: 2025-09-07
 * Status: Unificação crítica de contratos API
 */

// ✅ Enums padronizados (matching backend)
export type AppointmentStatus = 'agendado' | 'confirmado' | 'realizado' | 'cancelado' | 'pendente';
export type MessageDirection = 'in' | 'out';
export type ConversationStatus = 'active' | 'closed' | 'pending';
export type ClientStatus = 'active' | 'inactive' | 'new' | 'vip';

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

// ✅ TIPOS UNIFICADOS - Correspondem aos schemas do backend

/**
 * 📅 Agendamento unificado - C002: Usando camelCase padrão
 * ✅ API expõe camelCase, aceita snake_case para backward compatibility
 */
export interface Appointment {
  id: number;
  user_id: number;
  business_id: number;
  service_id?: number;

  // ✅ C002: Campos principais em camelCase (API padrão)
  dateTime: string; // ISO 8601 datetime (API principal)
  timeSlot?: string; // HH:MM format
  durationMinutes: number; // Duração em minutos
  price: number; // Valor do serviço
  status: AppointmentStatus;
  notes?: string; // Observações

  // ✅ Backward compatibility - campos em português/snake_case
  data_agendamento?: string; // Alias para dateTime
  horario?: string; // Alias para timeSlot
  duracao_minutos?: number; // Alias para durationMinutes
  valor?: number; // Alias para price
  observacoes?: string; // Alias para notes
  date_time?: string; // Alias antigo para dateTime
  duration_minutes?: number; // Alias antigo para durationMinutes

  // ✅ Dados relacionados padronizados
  cliente_nome: string;
  cliente_telefone: string;
  cliente_email?: string;
  servico_nome: string;
  servico_descricao?: string;
  business_name: string;

  // ✅ Timestamps padronizados
  created_at: string; // ISO 8601
  updated_at?: string; // ISO 8601
}

/**
 * 💬 Conversa unificada
 * Campos padronizados que correspondem ao ConversationResponseUnified
 */
export interface Conversation {
  id: number;
  user_id: number;
  status: ConversationStatus;
  last_message_at?: string; // ISO 8601
  created_at: string; // ISO 8601
  updated_at?: string; // ISO 8601

  // ✅ Dados relacionados padronizados
  user_name: string;
  user_phone?: string;
  total_messages: number;
  unread_messages: number;
  last_message?: string;
}

/**
 * 💬 Mensagem unificada
 * ✅ Padronizada para usar direction ('in' | 'out')
 */
export interface Message {
  id: number;
  conversation_id: number;
  content: string;
  message_type: string;
  direction: MessageDirection; // ✅ Padronizado: 'in' | 'out'
  created_at: string; // ISO 8601
  whatsapp_id?: string;

  // ✅ Campos adicionais
  is_read: boolean;
}

/**
 * 💬 Conversa com mensagens
 * Corresponde ao ConversationWithMessagesUnified
 */
export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

// ✅ TIPOS DE LISTAGEM UNIFICADOS

/**
 * 📅 Response para lista de agendamentos
 * Corresponde ao AppointmentsListResponseUnified
 */
export interface AppointmentsListResponse {
  appointments: Appointment[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

/**
 * 💬 Response para lista de conversas
 * Corresponde ao ConversationsListResponseUnified
 */
export interface ConversationsListResponse {
  conversations: Conversation[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// ✅ TIPOS PARA CRIAÇÃO/ATUALIZAÇÃO

/**
 * 📅 Request para criação de agendamento
 * Corresponde ao AppointmentCreateRequest
 * ✅ Usando nomenclatura padronizada brasileira
 */
export interface AppointmentCreateRequest {
  user_id: number;
  business_id: number;
  service_id?: number;
  data_agendamento: string; // ISO 8601 datetime
  duracao_minutos?: number;
  valor?: number;
  observacoes?: string;
}

/**
 * 📅 Request para atualização de agendamento
 * Corresponde ao AppointmentUpdateRequest
 * ✅ Usando nomenclatura padronizada brasileira
 */
export interface AppointmentUpdateRequest {
  data_agendamento?: string; // ISO 8601 datetime
  duracao_minutos?: number;
  valor?: number;
  status?: AppointmentStatus;
  observacoes?: string;
}

/**
 * 💬 Request para criação de mensagem
 * Corresponde ao MessageCreateRequest
 */
export interface MessageCreateRequest {
  conversation_id: number;
  content: string;
  message_type?: string;
  direction?: MessageDirection;
  whatsapp_id?: string;
}

// ✅ TIPOS LEGADOS (para compatibilidade temporária)

/**
 * 👤 Cliente
 * Mantido para compatibilidade com api-service.ts existente
 */
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
  status: ClientStatus;
}

/**
 * 📊 Estatísticas detalhadas de um cliente
 */
export interface ClientStatistics {
  total_conversations: number;
  total_messages: number;
  total_appointments: number;
  last_interaction?: string;
  avg_response_time_seconds: number;
  engagement_score: number;
  preferred_contact_time?: string;
  last_appointment_date?: string;
  conversion_rate: number;
}

/**
 * 🏢 Empresa/Negócio
 */
export interface Business {
  id: number;
  name: string;
  description?: string;
  phone?: string;
  email?: string;
  address?: string;
  website?: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

/**
 * 🛍️ Serviço
 */
export interface Service {
  id: number;
  business_id: number;
  name: string;
  description?: string;
  duration_minutes: number;
  price: number;
  is_active: boolean;
  category?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * 👤 Usuário do sistema
 */
export interface User {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  wa_id?: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

// ✅ TIPOS PARA ANALYTICS (compatibilidade com sistema de analytics)

/**
 * 📊 Visão geral do negócio
 */
export interface BusinessOverview {
  total_appointments: number;
  total_conversations: number;
  total_messages: number;
  total_clients: number;
  active_conversations: number;
  pending_appointments: number;
  revenue_total: number;
  revenue_this_month: number;
  conversion_rate: number;
  avg_response_time_minutes: number;
}

/**
 * 📈 Dados do funil de conversão
 */
export interface ConversationFunnelData {
  stage: string;
  count: number;
  percentage: number;
  conversion_rate?: number;
}

/**
 * ⚡ Métricas de performance
 */
export interface PerformanceMetrics {
  avg_response_time_seconds: number;
  peak_hours: Array<{
    hour: number;
    message_count: number;
  }>;
  busiest_days: Array<{
    day_name: string;
    appointment_count: number;
  }>;
  service_popularity: Array<{
    service_name: string;
    appointment_count: number;
    revenue: number;
  }>;
}

/**
 * 📈 Dados de série temporal
 */
export interface TimeSeriesData {
  date: string;
  appointments: number;
  conversations: number;
  messages: number;
  revenue: number;
}

/**
 * 📊 Response completa de analytics
 */
export interface AnalyticsResponse {
  business_overview: BusinessOverview;
  conversation_funnel: ConversationFunnelData[];
  performance_metrics: PerformanceMetrics;
  time_series: TimeSeriesData[];
  generated_at: string;
}

// ✅ TIPOS PARA AUTENTICAÇÃO

/**
 * 🔐 Request de login
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 🔐 Response de login
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user: {
    id: number;
    username: string;
    email?: string;
    role: string;
  };
}

/**
 * 🔐 Usuário autenticado
 */
export interface AuthenticatedUser {
  id: number;
  username: string;
  email?: string;
  role: string;
  permissions: string[];
}

// ✅ TIPOS PARA FILTROS E PARÂMETROS

/**
 * 🔍 Filtros para listagem de agendamentos
 */
export interface AppointmentFilters {
  status?: AppointmentStatus;
  date_from?: string;
  date_to?: string;
  service_id?: number;
  client_id?: number;
  page?: number;
  limit?: number;
}

/**
 * 🔍 Filtros para listagem de conversas
 */
export interface ConversationFilters {
  status?: ConversationStatus;
  search?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}

/**
 * 🔍 Filtros para analytics
 */
export interface AnalyticsFilters {
  date_from?: string;
  date_to?: string;
  service_id?: number;
  business_id?: number;
  granularity?: 'day' | 'week' | 'month';
}

// ✅ UTILITÁRIOS DE TIPO

/**
 * 🔄 Tipo utilitário para transformação de dados
 */
export type ApiDataTransformer<T, R> = (data: T) => R;

/**
 * 📝 Tipo para campos opcionais em updates
 */
export type PartialUpdate<T> = Partial<T>;

/**
 * 🔒 Tipo para campos obrigatórios em criação
 */
export type RequiredCreate<T, K extends keyof T> = T & Required<Pick<T, K>>;

// ✅ Export de constantes úteis
export const APPOINTMENT_STATUSES: AppointmentStatus[] = [
  'agendado', 'confirmado', 'realizado', 'cancelado', 'pendente'
];

export const MESSAGE_DIRECTIONS: MessageDirection[] = ['in', 'out'];

export const CONVERSATION_STATUSES: ConversationStatus[] = [
  'active', 'closed', 'pending'
];

export const CLIENT_STATUSES: ClientStatus[] = [
  'active', 'inactive', 'new', 'vip'
];

// ✅ TIPOS PARA DASHBOARD

/**
 * 📊 Métricas do Dashboard
 */
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

/**
 * 📊 Dados de gráfico
 */
export interface ChartData {
  date: string;
  messages: number;
  conversations: number;
  appointments: number;
  clients: number;
}

/**
 * 📊 Estatísticas de clientes
 */
export interface ClientStats {
  total: number;
  active: number;
  new_this_month: number;
  inactive: number;
  blocked?: number;
  growth_percentage?: number;
}

/**
 * 📊 Dados do Dashboard
 */
export interface DashboardData {
  metrics: DashboardMetrics;
  recent_conversations: Conversation[];
  upcoming_appointments: Appointment[];
  activity_chart: ChartData[];
  client_stats: ClientStats;
}

/**
 * 📊 Atividade Recente
 */
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

/**
 * 📊 Dashboard Stats Completos para Loading States
 */
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
  conversation_stats?: {
    total: number;
    resolved: number;
    pending: number;
    escalated: number;
    avg_resolution_time: number;
    satisfaction_rate: number;
  };
  appointment_stats?: {
    total: number;
    confirmed: number;
    pending: number;
    cancelled: number;
    completion_rate: number;
    no_show_rate: number;
  };
  performance_metrics?: {
    response_time: {
      avg: number;
      median: number;
      p95: number;
    };
    resolution_time: {
      avg: number;
      median: number;
      p95: number;
    };
    satisfaction_score: number;
    first_contact_resolution: number;
  };
  alerts?: any[];
  system_health?: {
    api_status: string;
    database_status: string;
    webhook_status: string;
    last_backup: string;
    uptime_percentage: number;
  };
}
