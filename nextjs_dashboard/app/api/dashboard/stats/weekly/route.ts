import { NextRequest, NextResponse } from 'next/server';
import { DashboardStatsComplete } from '@/types/api';

export async function GET(request: NextRequest) {
  try {
    // Simulando dados para desenvolvimento com loading state
    await new Promise(resolve => setTimeout(resolve, 600)); // Simular delay

    const mockStats: DashboardStatsComplete = {
      metrics: {
        total_clients: 280,
        active_conversations: 85,
        pending_appointments: 18,
        messages_today: 645,
        response_time_avg: 2.3,
        client_satisfaction: 4.9,
        growth_rate: 18.2,
        active_sessions: 42
      },
      recent_conversations: [],
      upcoming_appointments: [],
      activity_chart: [],
      client_stats: {
        total: 280,
        active: 245,
        inactive: 28,
        blocked: 7,
        new_this_month: 35,
        growth_percentage: 18.2
      },
      kpis: {
        totalClients: 280,
        totalConversations: 85,
        totalAppointments: 18,
        totalMessages: 645,
        responseTimeAvg: 2.3,
        satisfactionScore: 4.9,
        growthRate: 18.2,
        activeUsers: 42
      },
      charts: {
        conversationsOverTime: [
          { date: '2024-01-01', messages: 420, conversations: 65, appointments: 15, clients: 265 },
          { date: '2024-01-02', messages: 520, conversations: 75, appointments: 16, clients: 272 },
          { date: '2024-01-03', messages: 645, conversations: 85, appointments: 18, clients: 280 }
        ],
        appointmentsByStatus: [
          { status: 'confirmed', count: 14 },
          { status: 'pending', count: 3 },
          { status: 'cancelled', count: 1 }
        ],
        clientGrowth: [
          { date: '2024-01-01', messages: 0, conversations: 0, appointments: 0, clients: 265 },
          { date: '2024-01-02', messages: 0, conversations: 0, appointments: 0, clients: 272 },
          { date: '2024-01-03', messages: 0, conversations: 0, appointments: 0, clients: 280 }
        ]
      },
      recentActivity: [
        {
          id: 1,
          type: 'conversation',
          title: 'Semana produtiva',
          description: 'Aumento de 25% nas conversas da semana',
          timestamp: new Date().toISOString()
        },
        {
          id: 2,
          type: 'appointment',
          title: 'Agendamentos semanais',
          description: '18 novos agendamentos na semana',
          timestamp: new Date(Date.now() - 1800000).toISOString()
        }
      ]
    };

    return NextResponse.json({
      data: mockStats,
      success: true,
      message: 'Estatísticas semanais carregadas com sucesso'
    });
  } catch (error) {
    console.error('Erro ao buscar estatísticas semanais:', error);
    return NextResponse.json(
      {
        error: 'Erro interno do servidor ao buscar estatísticas semanais',
        success: false
      },
      { status: 500 }
    );
  }
}
