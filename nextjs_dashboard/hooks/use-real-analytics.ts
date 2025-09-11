/**
 * Real Analytics Hook - Substitui dados mock por endpoints reais
 * Integra com Error Boundaries e Toast para experiência robusta
 * OTIMIZADO: Usa API client com cache e rate limiting para Railway
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api-client';

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

// Global state to prevent multiple hook instances from making duplicate requests
let globalState = {
  dashboardSummary: null as DashboardSummary | null,
  loadingDashboard: false,
  lastFetch: 0,
  subscribers: new Set<() => void>()
};

export function useRealAnalytics(): UseRealAnalyticsReturn {
  const { toast } = useToast();
  const mounted = useRef(true);
  
  // Local state
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(globalState.dashboardSummary);
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
  
  // Subscribe to global state changes
  useEffect(() => {
    const updateState = () => {
      if (mounted.current) {
        setDashboardSummary(globalState.dashboardSummary);
        setLoadingDashboard(false); // Ensure loading is set to false when data is available
      }
    };
    
    globalState.subscribers.add(updateState);
    
    return () => {
      mounted.current = false;
      globalState.subscribers.delete(updateState);
    };
  }, []);

  // Sync with global state on mount
  useEffect(() => {
    if (globalState.dashboardSummary && !dashboardSummary) {
      setDashboardSummary(globalState.dashboardSummary);
      setLoadingDashboard(false);
    }
  }, [dashboardSummary]);

  // Error handler
  const handleError = useCallback((error: any, context: string) => {
    if (!mounted.current) return '';
    
    console.error(`❌ Erro em ${context}:`, error);
    
    const errorMessage = error?.message || error?.toString() || 'Erro desconhecido';
    
    // Only show toast for non-rate-limit errors
    if (!errorMessage.includes('429') && !errorMessage.includes('rate limit')) {
      toast({
        title: `Erro ao carregar ${context}`,
        description: errorMessage,
        variant: "destructive",
      });
    }
    
    return errorMessage;
  }, [toast]);
  
  // Fetch Dashboard Summary with global coordination
  const refreshDashboard = useCallback(async (days: number = 30) => {
    if (!mounted.current) return;
    
    // Check if data is fresh (less than 30 seconds old)
    const now = Date.now();
    const cacheAge = now - globalState.lastFetch;
    const cacheLimit = 30000; // 30 seconds
    
    if (globalState.dashboardSummary && cacheAge < cacheLimit) {
      console.log('📦 Using fresh global cache for dashboard');
      setDashboardSummary(globalState.dashboardSummary);
      return;
    }
    
    // Prevent duplicate requests
    if (globalState.loadingDashboard) {
      console.log('⏳ Dashboard request already in progress');
      return;
    }
    
    globalState.loadingDashboard = true;
    setLoadingDashboard(true);
    setDashboardError(null);
    
    try {
      console.log(`📊 Carregando dashboard summary - ${days} dias`);
      
      // Usar API route local do Next.js (que faz proxy para Railway)
      const result = await apiClient.get(
        `/api/analytics/overview?days=${days}`,
        { ttl: 60000 } // 1 minute cache
      );

      if (!result.success) {
        throw new Error(result.message || 'Falha ao carregar dashboard');
      }
      
      // Update global state
      globalState.dashboardSummary = result.data;
      globalState.lastFetch = now;
      
      // Notify all subscribers
      globalState.subscribers.forEach(callback => callback());
      
      // Always update local state - force update
      setDashboardSummary(result.data);
      
      console.log(`✅ Dashboard carregado:`, {
        customers: result.data.key_metrics?.total_customers,
        conversion: result.data.key_metrics?.overall_conversion_rate?.toFixed(1) + '%',
        source: result.source || 'backend'
      });
      
      // Only show success toast for real backend data
      if (result.source !== 'fallback') {
        toast({
          title: "Dashboard atualizado",
          description: `Dados de ${days} dias carregados com sucesso`,
          variant: "default",
        });
      }
      
    } catch (error) {
      if (!mounted.current) return;
      const errorMsg = handleError(error, 'dashboard summary');
      setDashboardError(errorMsg);
    } finally {
      if (mounted.current) {
        globalState.loadingDashboard = false;
        setLoadingDashboard(false);
      }
    }
  }, [handleError, toast]);
  
  // Load Conversion Funnel
  const loadConversionFunnel = useCallback(async (startDate?: string, endDate?: string) => {
    if (!mounted.current) return;
    
    setLoadingFunnel(true);
    setFunnelError(null);
    
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const endpoint = `/api/analytics/conversion-funnel${params.toString() ? '?' + params.toString() : ''}`;
      
      console.log(`🔄 Carregando funil de conversão: ${endpoint}`);
      
      const result = await apiClient.get(endpoint, { ttl: 120000 }); // 2 minute cache
      
      if (!mounted.current) return;
      
      if (!result.success) {
        throw new Error(result.message || 'Falha ao carregar funil');
      }
      
      setConversionFunnel(result.data);
      
      console.log(`✅ Funil carregado - Conversão: ${result.data.overall_conversion.toFixed(1)}%`);
      
    } catch (error) {
      if (!mounted.current) return;
      const errorMsg = handleError(error, 'funil de conversão');
      setFunnelError(errorMsg);
    } finally {
      if (mounted.current) {
        setLoadingFunnel(false);
      }
    }
  }, [handleError]);
  
  // Load Template Performance
  const loadTemplatePerformance = useCallback(async (days: number = 30) => {
    if (!mounted.current) return;
    
    setLoadingTemplates(true);
    setTemplatesError(null);
    
    try {
      console.log(`📋 Carregando performance de templates - ${days} dias`);
      
      const result = await apiClient.get(
        `/api/analytics/template-performance?days=${days}`,
        { ttl: 300000 } // 5 minute cache
      );
      
      if (!mounted.current) return;
      
      if (!result.success) {
        throw new Error(result.message || 'Falha ao carregar templates');
      }
      
      setTemplatePerformance(result.data);
      
      console.log(`✅ Templates carregados: ${result.data.total_templates_analyzed} analisados`);
      
    } catch (error) {
      if (!mounted.current) return;
      const errorMsg = handleError(error, 'performance de templates');
      setTemplatesError(errorMsg);
    } finally {
      if (mounted.current) {
        setLoadingTemplates(false);
      }
    }
  }, [handleError]);
  
  // Load Time Series Data
  const loadTimeSeriesData = useCallback(async (options: {
    days?: number;
    granularity?: 'hourly' | 'daily' | 'weekly';
    metrics?: string[];
  } = {}) => {
    if (!mounted.current) return;
    
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
      
      const endpoint = `/api/analytics/time-series?${params.toString()}`;
      
      console.log(`📈 Carregando série temporal: ${endpoint}`);
      
      const result = await apiClient.get(endpoint, { ttl: 180000 }); // 3 minute cache
      
      if (!mounted.current) return;
      
      if (!result.success) {
        throw new Error(result.message || 'Falha ao carregar série temporal');
      }
      
      setTimeSeriesData({
        data: result.data,
        metadata: result.metadata
      });
      
      console.log(`✅ Série temporal carregada: ${result.metadata.total_data_points} pontos`);
      
    } catch (error) {
      if (!mounted.current) return;
      const errorMsg = handleError(error, 'série temporal');
      setTimeSeriesError(errorMsg);
    } finally {
      if (mounted.current) {
        setLoadingTimeSeries(false);
      }
    }
  }, [handleError]);
  
  // Auto-load dashboard summary on mount - only if not already loaded
  useEffect(() => {
    if (!globalState.dashboardSummary || (Date.now() - globalState.lastFetch > 60000)) {
      console.log('🚀 useRealAnalytics: carregando dados iniciais');
      refreshDashboard(30);
    }
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
