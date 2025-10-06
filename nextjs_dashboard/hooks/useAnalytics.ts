/**
 * Hook useAnalytics - Integração completa com backend analytics
 * Consumo de dados reais do sistema para dashboards e relatórios
 */
'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import { debugLog } from '@/lib/debug';

// Tipos para dados de analytics
export interface AnalyticsTimeRange {
  startDate: Date;
  endDate: Date;
  preset?: 'today' | '7d' | '30d' | '90d' | 'custom';
}

export interface ConversationMetric {
  date: string;
  conversations: number;
  messages: number;
  responses: number;
  responseRate: number;
}

export interface FunnelMetric {
  stage: string;
  count: number;
  conversionRate: number;
  previousStage: number;
}

export interface ChannelMetric {
  channel: string;
  conversations: number;
  messages: number;
  avgResponseTime: number;
  satisfaction: number;
}

export interface AgentPerformanceMetric {
  agentId: string;
  agentName: string;
  conversations: number;
  avgResponseTime: number;
  satisfaction: number;
  resolutionRate: number;
}

export interface SatisfactionMetric {
  rating: number;
  count: number;
  percentage: number;
  trend: number;
}

export interface AnalyticsData {
  conversationsOverTime: ConversationMetric[];
  funnelData: FunnelMetric[];
  channelPerformance: ChannelMetric[];
  agentPerformance: AgentPerformanceMetric[];
  satisfactionBreakdown: SatisfactionMetric[];
  totalConversations: number;
  totalMessages: number;
  avgResponseTime: number;
  overallSatisfaction: number;
  trends: {
    conversations: number;
    responseTime: number;
    satisfaction: number;
  };
}

export interface AnalyticsFilters {
  timeRange?: AnalyticsTimeRange;
  channels?: string[];
  agents?: string[];
  status?: string[];
  tags?: string[];
}

// Hook principal useAnalytics
export const useAnalytics = (
  endpoint: string = 'overview',
  filters: AnalyticsFilters = {},
  refreshInterval?: number
) => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Memoizar parâmetros para evitar requests desnecessários
  const memoizedFilters = useMemo(() => {
    return {
      ...filters,
      timeRange: filters.timeRange || {
        startDate: subDays(new Date(), 30),
        endDate: new Date(),
        preset: '30d'
      }
    };
  }, [filters]);

  // Função para construir query string
  const buildQueryString = useCallback((filters: AnalyticsFilters): string => {
    const params = new URLSearchParams();

    if (filters.timeRange) {
      params.append('start_date', format(filters.timeRange.startDate, 'yyyy-MM-dd'));
      params.append('end_date', format(filters.timeRange.endDate, 'yyyy-MM-dd'));
    }

    if (filters.channels?.length) {
      params.append('channels', filters.channels.join(','));
    }

    if (filters.agents?.length) {
      params.append('agents', filters.agents.join(','));
    }

    if (filters.status?.length) {
      params.append('status', filters.status.join(','));
    }

    if (filters.tags?.length) {
      params.append('tags', filters.tags.join(','));
    }

    return params.toString();
  }, []);

  // Função principal de fetch
  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const queryString = buildQueryString(memoizedFilters);
      const url = `/api/analytics/${endpoint}${queryString ? `?${queryString}` : ''}`;

      // 🔒 SECURITY: Usando cookies HttpOnly seguros via credentials: 'include'
      const response = await fetch(url, {
        credentials: 'include', // Inclui cookies HttpOnly automaticamente
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      // Usar dados diretamente do campo 'data' da resposta
      setData(result.data);
      setLastUpdate(new Date());

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
      debugLog.error('Erro ao carregar analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [endpoint, memoizedFilters, buildQueryString]);

  // Processar dados do backend para formato padrão
  const processAnalyticsData = useCallback((rawData: any): AnalyticsData => {
    return {
      conversationsOverTime: rawData.conversations_over_time || [],
      funnelData: rawData.funnel_data || [],
      channelPerformance: rawData.channel_performance || [],
      agentPerformance: rawData.agent_performance || [],
      satisfactionBreakdown: rawData.satisfaction_breakdown || [],
      totalConversations: rawData.total_conversations || 0,
      totalMessages: rawData.total_messages || 0,
      avgResponseTime: rawData.avg_response_time || 0,
      overallSatisfaction: rawData.overall_satisfaction || 0,
      trends: {
        conversations: rawData.trends?.conversations || 0,
        responseTime: rawData.trends?.response_time || 0,
        satisfaction: rawData.trends?.satisfaction || 0,
      },
    };
  }, []);

  // Efeito principal para carregar dados
  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  // Efeito para refresh automático
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      const interval = setInterval(fetchAnalytics, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, fetchAnalytics]);

  return {
    data,
    loading,
    error,
    lastUpdate,
    refresh: fetchAnalytics,
    filters: memoizedFilters,
  };
};

// Hook para dados em tempo real
export const useRealTimeAnalytics = (
  endpoint: string = 'realtime',
  refreshInterval: number = 30000 // 30 segundos
) => {
  return useAnalytics(endpoint, {}, refreshInterval);
};

// Hook para comparação de períodos
export const usePeriodComparison = (
  currentPeriod: AnalyticsTimeRange,
  comparisonPeriod: AnalyticsTimeRange
) => {
  const current = useAnalytics('overview', { timeRange: currentPeriod });
  const comparison = useAnalytics('overview', { timeRange: comparisonPeriod });

  const percentageChange = useCallback((current: number, previous: number): number => {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
  }, []);

  const insights = useMemo(() => {
    if (!current.data || !comparison.data) return null;

    return {
      conversations: {
        current: current.data.totalConversations,
        previous: comparison.data.totalConversations,
        change: percentageChange(current.data.totalConversations, comparison.data.totalConversations),
      },
      messages: {
        current: current.data.totalMessages,
        previous: comparison.data.totalMessages,
        change: percentageChange(current.data.totalMessages, comparison.data.totalMessages),
      },
      responseTime: {
        current: current.data.avgResponseTime,
        previous: comparison.data.avgResponseTime,
        change: percentageChange(current.data.avgResponseTime, comparison.data.avgResponseTime),
      },
      satisfaction: {
        current: current.data.overallSatisfaction,
        previous: comparison.data.overallSatisfaction,
        change: percentageChange(current.data.overallSatisfaction, comparison.data.overallSatisfaction),
      },
    };
  }, [current.data, comparison.data, percentageChange]);

  return {
    current,
    comparison,
    insights,
    loading: current.loading || comparison.loading,
    error: current.error || comparison.error,
  };
};

// Hook para dados de exportação
export const useAnalyticsExport = () => {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const exportData = useCallback(async (
    exportFormat: 'csv' | 'excel' | 'pdf',
    filters: AnalyticsFilters,
    reportType: string = 'comprehensive'
  ) => {
    try {
      setExporting(true);
      setExportError(null);

      const queryString = new URLSearchParams({
        format: exportFormat,
        report_type: reportType,
        ...filters.timeRange && {
          start_date: format(filters.timeRange.startDate, 'yyyy-MM-dd'),
          end_date: format(filters.timeRange.endDate, 'yyyy-MM-dd'),
        },
        ...filters.channels?.length && { channels: filters.channels.join(',') },
        ...filters.agents?.length && { agents: filters.agents.join(',') },
      }).toString();

      // 🔒 SECURITY: Usando cookies HttpOnly seguros via credentials: 'include'
      const response = await fetch(`/api/analytics/export?${queryString}`, {
        credentials: 'include', // Inclui cookies HttpOnly automaticamente
        headers: {
          'Content-Type': 'application/json'
        },
      });

      if (!response.ok) {
        throw new Error(`Erro no export: ${response.statusText}`);
      }

      // Download do arquivo
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analytics-report-${exportFormat}.${exportFormat === 'excel' ? 'xlsx' : exportFormat}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      return true;
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Erro no export');
      return false;
    } finally {
      setExporting(false);
    }
  }, []);

  return {
    exportData,
    exporting,
    exportError,
  };
};

// Utility functions para formatação
export const formatMetricValue = (value: number, type: 'number' | 'percentage' | 'time' = 'number'): string => {
  switch (type) {
    case 'percentage':
      return `${value.toFixed(1)}%`;
    case 'time':
      if (value < 60) return `${value.toFixed(0)}s`;
      if (value < 3600) return `${(value / 60).toFixed(1)}min`;
      return `${(value / 3600).toFixed(1)}h`;
    default:
      return new Intl.NumberFormat('pt-BR').format(value);
  }
};

export const getColorByTrend = (trend: number): string => {
  if (trend > 5) return 'text-green-600';
  if (trend < -5) return 'text-red-600';
  return 'text-gray-600';
};

export const getIconByTrend = (trend: number): '↗' | '↘' | '→' => {
  if (trend > 5) return '↗';
  if (trend < -5) return '↘';
  return '→';
};

export default useAnalytics;
