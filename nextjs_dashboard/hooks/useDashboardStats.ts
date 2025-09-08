/**
 * Hook específico para carregar estatísticas do Dashboard
 * Implementa estados de loading apropriados para BUG-006
 * ATUALIZADO: Usando dados reais da API
 */

import { useApiGet } from '@/hooks/useApi'
import { DashboardStatsComplete } from '@/types/api'
import { useAuth } from '@/hooks/useAuth'

import { useState, useEffect } from 'react'

export interface DashboardStats {
  // Dados de hoje
  conversations_today: number
  messages_today: number
  appointments_today: number
  new_clients_today: number
  
  // Totais gerais
  total_conversations: number
  total_messages: number
  total_appointments: number
  total_clients: number
  
  // Stats de clientes
  active_clients?: number
  avg_messages?: number
  
  // Calculados no frontend
  conversion_rate?: number
  growth_rate?: number
}

export function useDashboardStats() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { authenticatedFetch, isAuthenticated, loading: authLoading } = useAuth()

  useEffect(() => {
    // Aguardar carregamento da autenticação
    if (authLoading) {
      return
    }

    // Só fazer fetch se estiver autenticado
    if (!isAuthenticated) {
      setLoading(false)
      return
    }

    const fetchStats = async () => {
      setLoading(true)
      setError(null)

      try {
        // Buscar estatísticas diárias principais
        const dailyResponse = await authenticatedFetch('/api/proxy/api/dashboard/stats/daily')

        if (!dailyResponse.ok) {
          throw new Error(`Erro ao buscar dados: ${dailyResponse.status} ${dailyResponse.statusText}`)
        }

        const dailyData = await dailyResponse.json()

        // Buscar estatísticas de clientes em paralelo (opcional)
        let clientStats = {}
        try {
          const clientStatsResponse = await authenticatedFetch('/api/proxy/api/dashboard/clients/stats')
          if (clientStatsResponse.ok) {
            clientStats = await clientStatsResponse.json()
          }
        } catch (clientError) {
          console.warn('Erro ao buscar stats de clientes:', clientError)
        }

        // Combinar dados
        const combinedStats: DashboardStats = {
          ...dailyData,
          ...clientStats,
          // Calcular métricas derivadas
          conversion_rate: dailyData.total_appointments > 0 && dailyData.total_conversations > 0
            ? (dailyData.total_appointments / dailyData.total_conversations) * 100 
            : 0,
          growth_rate: dailyData.new_clients_today > 0 && dailyData.total_clients > dailyData.new_clients_today
            ? (dailyData.new_clients_today / (dailyData.total_clients - dailyData.new_clients_today)) * 100
            : 0
        }

        setStats(combinedStats)

      } catch (err) {
        console.error('Erro ao buscar estatísticas:', err)
        setError(err instanceof Error ? err.message : 'Erro desconhecido')
        
        // Fallback com zeros em caso de erro
        setStats({
          conversations_today: 0,
          messages_today: 0,
          appointments_today: 0,
          new_clients_today: 0,
          total_conversations: 0,
          total_messages: 0,
          total_appointments: 0,
          total_clients: 0,
          conversion_rate: 0,
          growth_rate: 0
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [isAuthenticated, authLoading, authenticatedFetch]) // Refetch quando authentication status muda

  return { stats, loading, error }
}

// Hook para estatísticas semanais - dados reais
export function useDashboardStatsWeekly() {
  const { data, loading, error, get } = useApiGet<any>('/api/proxy/dashboard/stats/weekly')
  
  const transformedStats: DashboardStatsComplete | null = data ? {
    // Mesma transformação para dados semanais
    metrics: {
      total_clients: data.total_clients || 0,
      active_conversations: data.active_conversations || 0,
      pending_appointments: data.pending_appointments || 0,
      messages_today: data.messages_week || 0,
      response_time_avg: data.response_time_avg || 0,
      client_satisfaction: data.client_satisfaction || 0,
      growth_rate: data.growth_rate || 0,
      active_sessions: data.active_sessions || 0
    },
    recent_conversations: data.recent_conversations || [],
    upcoming_appointments: data.upcoming_appointments || [],
    activity_chart: data.activity_chart || [],
    client_stats: {
      total: data.client_stats?.total || 0,
      active: data.client_stats?.active || 0,
      inactive: data.client_stats?.inactive || 0,
      blocked: data.client_stats?.blocked || 0,
      new_this_month: data.client_stats?.new_this_week || 0,
      growth_percentage: data.client_stats?.growth_percentage || 0
    },
    kpis: {
      totalClients: data.total_clients || 0,
      totalConversations: data.active_conversations || 0,
      totalAppointments: data.pending_appointments || 0,
      totalMessages: data.messages_week || 0,
      responseTimeAvg: data.response_time_avg || 0,
      satisfactionScore: data.client_satisfaction || 0,
      growthRate: data.growth_rate || 0,
      activeUsers: data.active_sessions || 0
    },
    charts: {
      conversationsOverTime: data.charts?.conversations_over_time || [],
      appointmentsByStatus: data.charts?.appointments_by_status || [],
      clientGrowth: data.charts?.client_growth || []
    },
    recentActivity: data.recent_activity || []
  } : null
  
  return {
    stats: transformedStats,
    loading,
    error,
    refetch: get
  }
}

// Hook para estatísticas mensais - dados reais
export function useDashboardStatsMonthly() {
  const { data, loading, error, get } = useApiGet<any>('/api/proxy/dashboard/stats/monthly')
  
  const transformedStats: DashboardStatsComplete | null = data ? {
    metrics: {
      total_clients: data.total_clients || 0,
      active_conversations: data.active_conversations || 0,
      pending_appointments: data.pending_appointments || 0,
      messages_today: data.messages_month || 0,
      response_time_avg: data.response_time_avg || 0,
      client_satisfaction: data.client_satisfaction || 0,
      growth_rate: data.growth_rate || 0,
      active_sessions: data.active_sessions || 0
    },
    recent_conversations: data.recent_conversations || [],
    upcoming_appointments: data.upcoming_appointments || [],
    activity_chart: data.activity_chart || [],
    client_stats: {
      total: data.client_stats?.total || 0,
      active: data.client_stats?.active || 0,
      inactive: data.client_stats?.inactive || 0,
      blocked: data.client_stats?.blocked || 0,
      new_this_month: data.client_stats?.new_this_month || 0,
      growth_percentage: data.client_stats?.growth_percentage || 0
    },
    kpis: {
      totalClients: data.total_clients || 0,
      totalConversations: data.active_conversations || 0,
      totalAppointments: data.pending_appointments || 0,
      totalMessages: data.messages_month || 0,
      responseTimeAvg: data.response_time_avg || 0,
      satisfactionScore: data.client_satisfaction || 0,
      growthRate: data.growth_rate || 0,
      activeUsers: data.active_sessions || 0
    },
    charts: {
      conversationsOverTime: data.charts?.conversations_over_time || [],
      appointmentsByStatus: data.charts?.appointments_by_status || [],
      clientGrowth: data.charts?.client_growth || []
    },
    recentActivity: data.recent_activity || []
  } : null
  
  return {
    stats: transformedStats,
    loading,
    error,
    refetch: get
  }
}

// Hook com período customizado - dados reais
export function useDashboardStatsCustom(period: 'daily' | 'weekly' | 'monthly' | 'yearly' = 'daily') {
  const endpoint = period === 'daily' ? '/api/proxy/dashboard/stats' : 
                  period === 'weekly' ? '/api/proxy/dashboard/stats/weekly' :
                  period === 'monthly' ? '/api/proxy/dashboard/stats/monthly' :
                  '/api/proxy/dashboard/stats/yearly'
                  
  const { data, loading, error, get } = useApiGet<any>(endpoint)
  
  const transformedStats: DashboardStatsComplete | null = data ? {
    metrics: {
      total_clients: data.total_clients || 0,
      active_conversations: data.active_conversations || 0,
      pending_appointments: data.pending_appointments || 0,
      messages_today: data[`messages_${period}`] || data.messages_today || 0,
      response_time_avg: data.response_time_avg || 0,
      client_satisfaction: data.client_satisfaction || 0,
      growth_rate: data.growth_rate || 0,
      active_sessions: data.active_sessions || 0
    },
    recent_conversations: data.recent_conversations || [],
    upcoming_appointments: data.upcoming_appointments || [],
    activity_chart: data.activity_chart || [],
    client_stats: {
      total: data.client_stats?.total || 0,
      active: data.client_stats?.active || 0,
      inactive: data.client_stats?.inactive || 0,
      blocked: data.client_stats?.blocked || 0,
      new_this_month: data.client_stats?.[`new_this_${period.replace('ly', '')}`] || data.client_stats?.new_this_month || 0,
      growth_percentage: data.client_stats?.growth_percentage || 0
    },
    kpis: {
      totalClients: data.total_clients || 0,
      totalConversations: data.active_conversations || 0,
      totalAppointments: data.pending_appointments || 0,
      totalMessages: data[`messages_${period}`] || data.messages_today || 0,
      responseTimeAvg: data.response_time_avg || 0,
      satisfactionScore: data.client_satisfaction || 0,
      growthRate: data.growth_rate || 0,
      activeUsers: data.active_sessions || 0
    },
    charts: {
      conversationsOverTime: data.charts?.conversations_over_time || [],
      appointmentsByStatus: data.charts?.appointments_by_status || [],
      clientGrowth: data.charts?.client_growth || []
    },
    recentActivity: data.recent_activity || []
  } : null
  
  return {
    stats: transformedStats,
    loading,
    error,
    refetch: get,
    period
  }
}
