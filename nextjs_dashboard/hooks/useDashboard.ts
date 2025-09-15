import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { toast } from 'sonner'

// Tipos para dashboard
interface DashboardStats {
  total_appointments: number
  total_conversations: number
  pending_appointments: number
  active_conversations: number
  today_appointments: number
  today_messages: number
  conversion_rate: number
  response_time_avg: number
}

interface DashboardAnalytics {
  appointments_by_status: { [key: string]: number }
  messages_by_day: { date: string; count: number }[]
  peak_hours: { hour: number; count: number }[]
  top_services: { service: string; count: number }[]
  user_activity: { new_users: number; returning_users: number }
}

// Simulando serviço de API para dashboard
const dashboardApi = {
  async getStats(period: string = '7d'): Promise<DashboardStats> {
    const response = await fetch(`/api/dashboard/stats?period=${period}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}`
      }
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

    if (filters.start_date) params.append('start_date', filters.start_date)
    if (filters.end_date) params.append('end_date', filters.end_date)
    if (filters.metric_type) params.append('metric_type', filters.metric_type)

    const response = await fetch(`/api/dashboard/analytics?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}`
      }
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar analytics: ${response.statusText}`)
    }

    return response.json()
  },

  async getPerformanceReport(period: string = '30d'): Promise<{
    cache_hit_rate: number
    avg_response_time: number
    total_requests: number
    error_rate: number
    top_slow_endpoints: { endpoint: string; avg_time: number }[]
  }> {
    const response = await fetch(`/api/dashboard/performance?period=${period}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}`
      }
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar relatório de performance: ${response.statusText}`)
    }

    return response.json()
  }
}

// Hooks para dashboard
export function useDashboardStats(period: string = '7d') {
  return useQuery({
    queryKey: [...queryKeys.dashboard.stats(), period] as const,
    queryFn: () => dashboardApi.getStats(period),
    staleTime: 3 * 60 * 1000, // 3 minutos (dados agregados)
    gcTime: 10 * 60 * 1000, // 10 minutos
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      if (error?.status === 401 || error?.status === 403) {
        return false
      }
      return failureCount < 2
    }
  })
}

export function useDashboardAnalytics(filters: {
  start_date?: string
  end_date?: string
  metric_type?: string
} = {}) {
  return useQuery({
    queryKey: [...queryKeys.dashboard.analytics(), filters] as const,
    queryFn: () => dashboardApi.getAnalytics(filters),
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 15 * 60 * 1000, // 15 minutos
    refetchOnWindowFocus: false,
    enabled: true, // Sempre habilitado
  })
}

export function usePerformanceReport(period: string = '30d') {
  return useQuery({
    queryKey: ['dashboard', 'performance', period] as const,
    queryFn: () => dashboardApi.getPerformanceReport(period),
    staleTime: 10 * 60 * 1000, // 10 minutos
    gcTime: 30 * 60 * 1000, // 30 minutos
    refetchOnWindowFocus: false,
  })
}

// Hook para forçar refresh do dashboard
export function useRefreshDashboard() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      // Simular refresh forçado
      await new Promise(resolve => setTimeout(resolve, 500))
      return { success: true }
    },
    onSuccess: () => {
      // Invalidar todas as queries do dashboard
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all })

      // Invalidar também dados relacionados
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() })

      toast.success('Dashboard atualizado!')
    },
    onError: (error: any) => {
      console.error('Erro ao atualizar dashboard:', error)
      toast.error('Erro ao atualizar dashboard')
    }
  })
}

// Hook para invalidação seletiva do dashboard
export function useInvalidateDashboard() {
  const queryClient = useQueryClient()

  return {
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all }),
    invalidateStats: () => queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() }),
    invalidateAnalytics: () => queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.analytics() }),
    invalidatePerformance: () => queryClient.invalidateQueries({ queryKey: ['dashboard', 'performance'] }),
  }
}

// Hook para prefetch de dados do dashboard
export function usePrefetchDashboard() {
  const queryClient = useQueryClient()

  return {
    prefetchStats: (period: string = '7d') => {
      queryClient.prefetchQuery({
        queryKey: [...queryKeys.dashboard.stats(), period] as const,
        queryFn: () => dashboardApi.getStats(period),
        staleTime: 3 * 60 * 1000,
      })
    },

    prefetchAnalytics: (filters: any = {}) => {
      queryClient.prefetchQuery({
        queryKey: [...queryKeys.dashboard.analytics(), filters] as const,
        queryFn: () => dashboardApi.getAnalytics(filters),
        staleTime: 5 * 60 * 1000,
      })
    }
  }
}

// Hook customizado para dashboard completo
export function useDashboard(options: {
  period?: string
  analyticsFilters?: any
  autoRefresh?: boolean
  refreshInterval?: number
} = {}) {
  const {
    period = '7d',
    analyticsFilters = {},
    autoRefresh = true,
    refreshInterval = 5 * 60 * 1000 // 5 minutos
  } = options

  const stats = useDashboardStats(period)
  const analytics = useDashboardAnalytics(analyticsFilters)
  const performance = usePerformanceReport()

  // Auto refresh opcional
  const refreshDashboard = useRefreshDashboard()

  // Efeito para auto refresh
  React.useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      if (!stats.isFetching && !analytics.isFetching) {
        refreshDashboard.mutate()
      }
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, stats.isFetching, analytics.isFetching, refreshDashboard])

  return {
    stats,
    analytics,
    performance,
    refresh: refreshDashboard.mutate,
    isRefreshing: refreshDashboard.isPending,

    // Estados combinados
    isLoading: stats.isLoading || analytics.isLoading || performance.isLoading,
    isError: stats.isError || analytics.isError || performance.isError,
    error: stats.error || analytics.error || performance.error,

    // Dados combinados
    data: {
      stats: stats.data,
      analytics: analytics.data,
      performance: performance.data
    }
  }
}

// Importar React para useEffect
import React from 'react'
