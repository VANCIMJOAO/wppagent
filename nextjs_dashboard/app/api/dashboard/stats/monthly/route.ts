import { NextRequest, NextResponse } from 'next/server';
import { DashboardStatsComplete } from '@/types/api';

export async function GET(request: NextRequest) {
  try {
    // Simulando dados para desenvolvimento com loading state
    await new Promise(resolve => setTimeout(resolve, 800)); // Simular delay

    const mockStats: DashboardStatsComplete = {
      metrics: {
        total_clients: 580,
        active_conversations: 125,
        pending_appointments: 35,
        messages_today: 1247,
        response_time_avg: 2.8,
        client_satisfaction: 4.7,
        growth_rate: 22.3,
        active_sessions: 67
      },
      recent_conversations: [],
      upcoming_appointments: [],
      activity_chart: [],
      client_stats: {
        total: 580,
        active: 485,
        inactive: 78,
        blocked: 17,
        new_this_month: 125,
        growth_percentage: 22.3
      },
      kpis: {
        totalClients: 580,
        totalConversations: 125,
        totalAppointments: 35,
        totalMessages: 1247,
        responseTimeAvg: 2.8,
        satisfactionScore: 4.7,
        growthRate: 22.3,
        activeUsers: 67
      },
      charts: {
        conversationsOverTime: [
          { date: '2024-01-01', messages: 850, conversations: 125, appointments: 35, clients: 550 },
          { date: '2024-01-02', messages: 920, conversations: 135, appointments: 40, clients: 565 },
          { date: '2024-01-03', messages: 1100, conversations: 140, appointments: 38, clients: 580 }
        ],
        appointmentsByStatus: [
          { status: 'confirmed', count: 22 },
          { status: 'pending', count: 8 },
          { status: 'cancelled', count: 5 }
        ],
        clientGrowth: [
          { date: '2024-01-01', messages: 0, conversations: 0, appointments: 0, clients: 550 },
          { date: '2024-01-02', messages: 0, conversations: 0, appointments: 0, clients: 565 },
          { date: '2024-01-03', messages: 0, conversations: 0, appointments: 0, clients: 580 }
        ]
      },
      recentActivity: [
        {
          id: 1,
          type: 'conversation',
          title: 'Pico mensal de conversas',
          description: 'Recorde de 140 conversas ativas em um dia',
          timestamp: new Date().toISOString()
        },
        {
          id: 2,
          type: 'appointment',
          title: 'Meta mensal atingida',
          description: '35 agendamentos confirmados no mês',
          timestamp: new Date(Date.now() - 3600000).toISOString()
        }
      ]
    };

    return NextResponse.json({
      data: mockStats,
      success: true,
      message: 'Estatísticas mensais carregadas com sucesso'
    });
  } catch (error) {
    console.error('Erro ao buscar estatísticas mensais:', error);
    return NextResponse.json(
      {
        error: 'Erro interno do servidor ao buscar estatísticas mensais',
        success: false
      },
      { status: 500 }
    );
  }
}
