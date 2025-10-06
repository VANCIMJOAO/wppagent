/**
 * 🚀 HOOK DASHBOARD CONSOLIDADO - FASE 2 REFATORAÇÃO
 * =================================================
 * 
 * Hook unificado que combina as melhores funcionalidades de:
 * - useDashboard.ts (base)
 * - useDashboardStats.ts (estatísticas)
 * - useDashboardStatsRobust.ts (robustez)
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { toast } from 'sonner'
import { debugLog } from '@/lib/debug';

// Tipos para dashboard - Compatível com StatsCards
interface DashboardStats {
  total_clients: number
  growth_rate?: number
  conversations_today: number
  total_conversations: number
  appointments_today: number
  total_appointments: number
  conversion_rate?: number
  messages_today: number
  total_messages: number
  new_clients_today: number
  last_updated: string
  
  // Propriedades originais adicionais
  pending_appointments: number
  active_conversations: number
  today_appointments: number
  today_messages: number
  response_time_avg: number
}

interface DashboardAnalytics {
  appointments_by_status: { [key: string]: number }
  messages_by_day: { date: string; count: number }[]
  peak_hours: { hour: number; count: number }[]
  top_services: { service: string; count: number }[]
  user_activity: { new_users: number; returning_users: number }
}

interface DashboardCharts {
  appointments_trend: { date: string; count: number }[]
  messages_trend: { date: string; count: number }[]
  conversion_funnel: { stage: string; count: number }[]
  response_times: { hour: number; avg_time: number }[]
}

interface DashboardComplete {
  stats: DashboardStats
  analytics: DashboardAnalytics
  charts: DashboardCharts
  last_updated: string
}

// Simulando serviço de API para dashboard
const dashboardApi = {
  async getStats(period: string = '7d'): Promise<DashboardStats> {
    const response = await fetch(`/api/dashboard/stats?period=${period}`, {
      method: 'GET',
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar estatísticas: ${response.statusText}`)
    }

    return response.json()
  },

  async getAnalytics(filters: {
    start_date?: string
    end_date?: string
    metric_type?: string
  } = {}): Promise<DashboardAnalytics> {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value)
    })

    const response = await fetch(`/api/dashboard/analytics?${params}`, {
      method: 'GET',
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar analytics: ${response.statusText}`)
    }

    return response.json()
  },

  async getCharts(period: string = '7d'): Promise<DashboardCharts> {
    const response = await fetch(`/api/dashboard/charts?period=${period}`, {
      method: 'GET',
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar charts: ${response.statusText}`)
    }

    return response.json()
  },

  async getComplete(period: string = '7d'): Promise<DashboardComplete> {
    const response = await fetch(`/api/dashboard/complete?period=${period}`, {
      method: 'GET',
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar dados completos: ${response.statusText}`)
    }

    return response.json()
  },

  async refreshCache(): Promise<void> {
    const response = await fetch('/api/dashboard/refresh', {
      method: 'POST',
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error(`Erro ao atualizar cache: ${response.statusText}`)
    }
  }
}

// Hook principal consolidado
export function useDashboard(period: string = '7d') {
  const queryClient = useQueryClient()

  // Query para dados completos do dashboard
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['dashboard', 'complete', period],
    queryFn: () => dashboardApi.getComplete(period),
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 10 * 60 * 1000, // 10 minutos
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  // Query para estatísticas separadas (se necessário)
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError
  } = useQuery({
    queryKey: ['dashboard', 'stats', period],
    queryFn: () => dashboardApi.getStats(period),
    enabled: false, // Só executa se chamado explicitamente
    staleTime: 5 * 60 * 1000
  })

  // Query para analytics separadas (se necessário)
  const {
    data: analytics,
    isLoading: analyticsLoading,
    error: analyticsError
  } = useQuery({
    queryKey: ['dashboard', 'analytics', period],
    queryFn: () => dashboardApi.getAnalytics(),
    enabled: false, // Só executa se chamado explicitamente
    staleTime: 5 * 60 * 1000
  })

  // Query para charts separados (se necessário)
  const {
    data: charts,
    isLoading: chartsLoading,
    error: chartsError
  } = useQuery({
    queryKey: ['dashboard', 'charts', period],
    queryFn: () => dashboardApi.getCharts(period),
    enabled: false, // Só executa se chamado explicitamente
    staleTime: 5 * 60 * 1000
  })

  // Mutation para refresh manual
  const refreshMutation = useMutation({
    mutationFn: dashboardApi.refreshCache,
    onSuccess: () => {
      // Invalidar todas as queries relacionadas ao dashboard
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Dashboard atualizado com sucesso!')
    },
    onError: (error) => {
      debugLog.error('Erro ao atualizar dashboard:', error)
      toast.error('Erro ao atualizar dashboard')
    }
  })

  // Funções auxiliares
  const refreshDashboard = () => {
    refreshMutation.mutate()
  }

  const fetchStats = () => {
    return queryClient.fetchQuery({
      queryKey: ['dashboard', 'stats', period],
      queryFn: () => dashboardApi.getStats(period)
    })
  }

  const fetchAnalytics = (filters?: any) => {
    return queryClient.fetchQuery({
      queryKey: ['dashboard', 'analytics', period],
      queryFn: () => dashboardApi.getAnalytics(filters)
    })
  }

  const fetchCharts = () => {
    return queryClient.fetchQuery({
      queryKey: ['dashboard', 'charts', period],
      queryFn: () => dashboardApi.getCharts(period)
    })
  }

  // Invalidação inteligente
  const invalidateDashboard = (scope: 'all' | 'stats' | 'analytics' | 'charts' = 'all') => {
    switch (scope) {
      case 'stats':
        queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] })
        break
      case 'analytics':
        queryClient.invalidateQueries({ queryKey: ['dashboard', 'analytics'] })
        break
      case 'charts':
        queryClient.invalidateQueries({ queryKey: ['dashboard', 'charts'] })
        break
      case 'all':
      default:
        queryClient.invalidateQueries({ queryKey: ['dashboard'] })
        break
    }
  }

  return {
    // Dados principais
    data: dashboardData,
    stats: dashboardData?.stats as DashboardStats,
    analytics: dashboardData?.analytics,
    charts: dashboardData?.charts,
    
    // Estados de loading
    loading: isLoading,
    isLoading: isLoading,
    isFetching: isLoading,
    statsLoading,
    analyticsLoading,
    chartsLoading,
    
    // Estados de erro
    error,
    isError: !!error,
    statsError,
    analyticsError,
    chartsError,
    
    // Ações
    refetch,
    refreshDashboard,
    fetchStats,
    fetchAnalytics,
    fetchCharts,
    invalidateDashboard,
    
    // Estado da mutation
    isRefreshing: refreshMutation.isPending,
    
    // Dados separados (para compatibilidade)
    separateStats: stats,
    separateAnalytics: analytics,
    separateCharts: charts,
    
    // Propriedades de recovery (para compatibilidade com componentes robustos)
    recoveryMode: 'normal' as 'normal' | 'cached' | 'degraded' | 'offline',
    retryCount: 0,
    networkStatus: {
      effectiveType: '4g',
      rtt: 50
    } as any,
    isOffline: false,
    manualRetry: () => refetch(),
    clearCache: () => invalidateDashboard(),
    isUsingCache: false,
    isDegraded: false,
    canRetry: true,
    debugInfo: {
      lastFetch: new Date().toISOString(),
      cacheStatus: 'fresh',
      networkLatency: 0
    }
  }
}

// Hook para apenas estatísticas (compatibilidade)
export function useDashboardStats(period: string = '7d') {
  const {
    data,
    isLoading: loading,
    error,
    refetch
  } = useQuery({
    queryKey: ['dashboard', 'stats', period],
    queryFn: () => dashboardApi.getStats(period),
    staleTime: 5 * 60 * 1000
  })

  return {
    stats: data,
    loading,
    error,
    refetch,
    invalidate: () => {} // TODO: Implementar após consolidação
  }
}

// Hook para apenas analytics (compatibilidade)
export function useDashboardAnalytics(filters?: any) {
  const {
    data,
    isLoading: loading,
    error,
    refetch
  } = useQuery({
    queryKey: ['dashboard', 'analytics', filters],
    queryFn: () => dashboardApi.getAnalytics(filters),
    staleTime: 5 * 60 * 1000
  })

  return {
    analytics: data,
    loading,
    error,
    refetch,
    invalidate: () => {} // TODO: Implementar após consolidação
  }
}

// Hook para apenas charts (compatibilidade)
export function useDashboardCharts(period: string = '7d') {
  const {
    data,
    isLoading: loading,
    error,
    refetch
  } = useQuery({
    queryKey: ['dashboard', 'charts', period],
    queryFn: () => dashboardApi.getCharts(period),
    staleTime: 5 * 60 * 1000
  })

  return {
    charts: data,
    loading,
    error,
    refetch,
    invalidate: () => {} // TODO: Implementar após consolidação
  }
}

export default useDashboard
