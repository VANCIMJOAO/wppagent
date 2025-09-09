/**
 * Real Analytics Hook - Substitui dados mock por endpoints reais
 * Integra com Error Boundaries e Toast para experiência robusta
 */

import { useState, useEffect, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';

// Tipos para os dados de analytics
interface DashboardSummary {
  key_metrics: {
    total_customers: number;
    total_messages: number;
    total_conversations: number;
    total_appointments: number;
    overall_conversion_rate: number;
    avg_response_time_minutes: number;
    satisfaction_score: number;
  };
  funnel: {
    stages: Array<{
      stage: string;
      count: number;
      conversionRate: number;
      previousStage: number;
    }>;
    overall_conversion: number;
  };
  channel_performance: Array<{
    channel: string;
    conversations: number;
    messages: number;
    avgResponseTime: number;
    satisfaction: number;
  }>;
  satisfaction_breakdown: Array<{
    rating: number;
    count: number;
    percentage: number;
    trend: number;
  }>;
  trends: {
    conversations: number;
    responseTime: number;
    satisfaction: number;
  };
  time_series: Array<{
    date: string;
    conversations: number;
    messages: number;
    responses: number;
    responseRate: number;
  }>;
}

interface ConversionFunnel {
  stages: Array<{
    stage: string;
    count: number;
    conversionRate: number;
    previousStage: number;
  }>;
  overall_conversion: number;
  total_visitors: number;
  total_conversions: number;
}

interface TemplatePerformance {
  templates: Array<{
    template_name: string;
    usage_count: number;
    unique_users: number;
    response_rate: number;
    conversion_rate: number;
    avg_response_time: number;
    effectiveness_score: number;
  }>;
  total_templates_analyzed: number;
}

interface TimeSeriesData {
  data: Array<{
    period: string;
    date: string;
    [metric: string]: any;
  }>;
  metadata: {
    period: { start: string; end: string };
    granularity: string;
    metrics: string[];
    total_data_points: number;
  };
}

interface UseRealAnalyticsReturn {
  // Dashboard Summary
  dashboardSummary: DashboardSummary | null;
  loadingDashboard: boolean;
  dashboardError: string | null;
  
  // Conversion Funnel
  conversionFunnel: ConversionFunnel | null;
  loadingFunnel: boolean;
  funnelError: string | null;
  
  // Template Performance
  templatePerformance: TemplatePerformance | null;
  loadingTemplates: boolean;
  templatesError: string | null;
  
  // Time Series
  timeSeriesData: TimeSeriesData | null;
  loadingTimeSeries: boolean;
  timeSeriesError: string | null;
  
  // Actions
  refreshDashboard: (days?: number) => Promise<void>;
  loadConversionFunnel: (startDate?: string, endDate?: string) => Promise<void>;
  loadTemplatePerformance: (days?: number) => Promise<void>;
  loadTimeSeriesData: (options?: {
    days?: number;
    granularity?: 'hourly' | 'daily' | 'weekly';
    metrics?: string[];
  }) => Promise<void>;
  
  // Unified loading state
  isLoading: boolean;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export function useRealAnalytics(): UseRealAnalyticsReturn {
  const { toast } = useToast();
  
  // Dashboard Summary State
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  
  // Conversion Funnel State
  const [conversionFunnel, setConversionFunnel] = useState<ConversionFunnel | null>(null);
  const [loadingFunnel, setLoadingFunnel] = useState(false);
  const [funnelError, setFunnelError] = useState<string | null>(null);
  
  // Template Performance State
  const [templatePerformance, setTemplatePerformance] = useState<TemplatePerformance | null>(null);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [templatesError, setTemplatesError] = useState<string | null>(null);
  
  // Time Series State
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData | null>(null);
  const [loadingTimeSeries, setLoadingTimeSeries] = useState(false);
  const [timeSeriesError, setTimeSeriesError] = useState<string | null>(null);
  
  // Unified loading state
  const isLoading = loadingDashboard || loadingFunnel || loadingTemplates || loadingTimeSeries;
  
  // Error handler
  const handleError = useCallback((error: any, context: string) => {
    console.error(`❌ Erro em ${context}:`, error);
    
    const errorMessage = error?.message || error?.toString() || 'Erro desconhecido';
    
    toast({
      title: `Erro ao carregar ${context}`,
      description: errorMessage,
      variant: "destructive",
    });
    
    return errorMessage;
  }, [toast]);
  
  // Fetch Dashboard Summary
  const refreshDashboard = useCallback(async (days: number = 30) => {
    setLoadingDashboard(true);
    setDashboardError(null);
    
    try {
      console.log(`📊 Carregando dashboard summary - ${days} dias`);
      
      const response = await fetch(`${BACKEND_URL}/api/analytics/dashboard-summary?days=${days}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          // TODO: Adicionar token de autenticação quando implementado
        },
        // 30s timeout
        signal: AbortSignal.timeout(30000)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Falha ao carregar dashboard');
      }
      
      setDashboardSummary(result.data);
      
      console.log(`✅ Dashboard carregado:`, {
        customers: result.data.key_metrics.total_customers,
        conversion: result.data.key_metrics.overall_conversion_rate.toFixed(1) + '%'
      });
      
      toast({
        title: "Dashboard atualizado",
        description: `Dados de ${days} dias carregados com sucesso`,
        variant: "default",
      });
      
    } catch (error) {
      const errorMsg = handleError(error, 'dashboard summary');
      setDashboardError(errorMsg);
    } finally {
      setLoadingDashboard(false);
    }
  }, [handleError, toast]);
  
  // Load Conversion Funnel
  const loadConversionFunnel = useCallback(async (startDate?: string, endDate?: string) => {
    setLoadingFunnel(true);
    setFunnelError(null);
    
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const url = `${BACKEND_URL}/api/analytics/conversion-funnel${params.toString() ? '?' + params.toString() : ''}`;
      
      console.log(`🔄 Carregando funil de conversão: ${url}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(30000)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Falha ao carregar funil');
      }
      
      setConversionFunnel(result.data);
      
      console.log(`✅ Funil carregado - Conversão: ${result.data.overall_conversion.toFixed(1)}%`);
      
    } catch (error) {
      const errorMsg = handleError(error, 'funil de conversão');
      setFunnelError(errorMsg);
    } finally {
      setLoadingFunnel(false);
    }
  }, [handleError]);
  
  // Load Template Performance
  const loadTemplatePerformance = useCallback(async (days: number = 30) => {
    setLoadingTemplates(true);
    setTemplatesError(null);
    
    try {
      console.log(`📋 Carregando performance de templates - ${days} dias`);
      
      const response = await fetch(`${BACKEND_URL}/api/analytics/template-performance?days=${days}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(30000)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Falha ao carregar templates');
      }
      
      setTemplatePerformance(result.data);
      
      console.log(`✅ Templates carregados: ${result.data.total_templates_analyzed} analisados`);
      
    } catch (error) {
      const errorMsg = handleError(error, 'performance de templates');
      setTemplatesError(errorMsg);
    } finally {
      setLoadingTemplates(false);
    }
  }, [handleError]);
  
  // Load Time Series Data
  const loadTimeSeriesData = useCallback(async (options: {
    days?: number;
    granularity?: 'hourly' | 'daily' | 'weekly';
    metrics?: string[];
  } = {}) => {
    setLoadingTimeSeries(true);
    setTimeSeriesError(null);
    
    try {
      const {
        days = 30,
        granularity = 'daily',
        metrics = ['conversations', 'messages', 'appointments']
      } = options;
      
      const params = new URLSearchParams({
        days: days.toString(),
        granularity,
        metrics: metrics.join(',')
      });
      
      const url = `${BACKEND_URL}/api/analytics/time-series?${params.toString()}`;
      
      console.log(`📈 Carregando série temporal: ${url}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(30000)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Falha ao carregar série temporal');
      }
      
      setTimeSeriesData({
        data: result.data,
        metadata: result.metadata
      });
      
      console.log(`✅ Série temporal carregada: ${result.metadata.total_data_points} pontos`);
      
    } catch (error) {
      const errorMsg = handleError(error, 'série temporal');
      setTimeSeriesError(errorMsg);
    } finally {
      setLoadingTimeSeries(false);
    }
  }, [handleError]);
  
  // Auto-load dashboard summary on mount
  useEffect(() => {
    console.log('🚀 useRealAnalytics: carregando dados iniciais');
    refreshDashboard(30);
  }, [refreshDashboard]);
  
  return {
    // Dashboard Summary
    dashboardSummary,
    loadingDashboard,
    dashboardError,
    
    // Conversion Funnel
    conversionFunnel,
    loadingFunnel,
    funnelError,
    
    // Template Performance
    templatePerformance,
    loadingTemplates,
    templatesError,
    
    // Time Series
    timeSeriesData,
    loadingTimeSeries,
    timeSeriesError,
    
    // Actions
    refreshDashboard,
    loadConversionFunnel,
    loadTemplatePerformance,
    loadTimeSeriesData,
    
    // Unified state
    isLoading
  };
}
