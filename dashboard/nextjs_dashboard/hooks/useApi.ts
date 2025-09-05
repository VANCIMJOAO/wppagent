/**
 * Hooks personalizados para integração com API
 */

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api-service';

interface DashboardKPIs {
  total_conversations: number;
  unique_users: number;
  total_appointments: number;
  total_messages: number;
  messages_today: number;
  conversations_today: number;
  appointments_today: number;
  growth_conversations: number;
  growth_messages: number;
  growth_appointments: number;
}

interface DashboardCharts {
  conversations_chart: Array<{ date: string; count: number }>;
  messages_chart: Array<{ date: string; count: number }>;
  appointments_chart: Array<{ date: string; count: number }>;
  status_distribution: Array<{ status: string; count: number }>;
}

export function useDashboardData(days: number = 30) {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [charts, setCharts] = useState<DashboardCharts | null>(null);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const dashboardStats = await api.getDashboardStats();
      
      const kpisData: DashboardKPIs = {
        total_conversations: dashboardStats.conversas_ativas,
        unique_users: dashboardStats.total_clientes,
        total_appointments: dashboardStats.agendamentos_hoje,
        total_messages: dashboardStats.mensagens_nao_lidas,
        messages_today: dashboardStats.mensagens_nao_lidas,
        conversations_today: dashboardStats.conversas_ativas,
        appointments_today: dashboardStats.agendamentos_hoje,
        growth_conversations: dashboardStats.crescimento_clientes,
        growth_messages: 8.3,
        growth_appointments: 15.2
      };

      const chartsData: DashboardCharts = {
        conversations_chart: [],
        messages_chart: [],
        appointments_chart: [],
        status_distribution: [
          { status: 'confirmed', count: Math.floor(dashboardStats.agendamentos_hoje * 0.6) },
          { status: 'pending', count: Math.floor(dashboardStats.agendamentos_hoje * 0.3) },
          { status: 'cancelled', count: Math.floor(dashboardStats.agendamentos_hoje * 0.1) }
        ]
      };

      // Buscar atividades recentes
      const recentActivities = await api.getRecentActivity(8);

      setKpis(kpisData);
      setCharts(chartsData);
      setRecentActivity(recentActivities);

    } catch (err: any) {
      setError(`Erro ao conectar com o backend: ${err.message || 'Verifique se o servidor está funcionando'}`);
      console.error('Erro no useDashboardData:', err);
      
      // Limpar dados em caso de erro
      setKpis(null);
      setCharts(null);
      setRecentActivity([]);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    kpis,
    charts,
    recentActivity,
    loading,
    error,
    refetch: fetchData
  };
}
