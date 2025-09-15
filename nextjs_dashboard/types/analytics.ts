/**
 * Tipos TypeScript para Analytics e Relatórios
 */

// Business Overview - Visão geral do negócio
export interface BusinessOverview {
  // KPIs principais
  total_revenue: number;
  total_conversations: number;
  active_clients: number;
  conversion_rate: number;

  // Crescimento (comparação com período anterior)
  revenue_growth: number;
  conversations_growth: number;
  clients_growth: number;
  conversion_growth: number;

  // Distribuições
  revenue_by_source: Array<{
    source: string;
    value: number;
  }>;

  conversations_by_status: Array<{
    status: string;
    count: number;
  }>;
}

// Conversation Funnel - Funil de conversão
export interface ConversationFunnel {
  stages: Array<{
    stage: string;
    count: number;
    percentage: number;
  }>;

  // Taxas de conversão entre estágios
  lead_to_interested_rate: number;
  interested_to_negotiation_rate: number;
  negotiation_to_client_rate: number;

  overall_conversion_rate: number;
}

// Performance Metrics - Métricas de performance
export interface PerformanceMetrics {
  // Tempo de resposta
  avg_response_time: number;
  response_time: {
    avg: number;
    min: number;
    max: number;
    p95: number;
  };

  // Engajamento
  engagement_rate: number;
  satisfaction_score: number;
  messages_per_conversation: number;

  // Distribuição de tempo de resposta
  response_time_distribution: Array<{
    range: string;
    count: number;
  }>;
}

// Time Series Data - Dados temporais para gráficos
export interface TimeSeriesData {
  metric_type: 'conversations' | 'revenue' | 'appointments' | 'clients';
  granularity: 'hour' | 'day' | 'week' | 'month';
  period: {
    start_date: string;
    end_date: string;
  };
  data: Array<{
    timestamp: string;
    value: number;
  }>;
}
