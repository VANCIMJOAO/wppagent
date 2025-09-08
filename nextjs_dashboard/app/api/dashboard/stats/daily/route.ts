import { NextRequest, NextResponse } from 'next/server';
import { DashboardStatsComplete } from '@/types/api';

export async function GET(request: NextRequest) {
  try {
    // Simulando dados para desenvolvimento com loading state
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simular delay
    
    const mockStats: DashboardStatsComplete = {
      metrics: {
        total_clients: 150,
        active_conversations: 45,
        pending_appointments: 12,
        messages_today: 328,
        response_time_avg: 2.5,
        client_satisfaction: 4.8,
        growth_rate: 15.5,
        active_sessions: 23
      },
      recent_conversations: [],
      upcoming_appointments: [],
      activity_chart: [],
      client_stats: {
        total: 150,
        active: 120,
        inactive: 25,
        blocked: 5,
        new_this_month: 18,
        growth_percentage: 15.5
      },
      kpis: {
        totalClients: 150,
        totalConversations: 45,
        totalAppointments: 12,
        totalMessages: 328,
        responseTimeAvg: 2.5,
        satisfactionScore: 4.8,
        growthRate: 15.5,
        activeUsers: 23
      },
      charts: {
        conversationsOverTime: [
          { date: '2024-01-01', messages: 150, conversations: 45, appointments: 12, clients: 150 },
          { date: '2024-01-02', messages: 200, conversations: 55, appointments: 15, clients: 152 },
          { date: '2024-01-03', messages: 180, conversations: 48, appointments: 10, clients: 155 }
        ],
        appointmentsByStatus: [
          { status: 'confirmed', count: 8 },
          { status: 'pending', count: 4 },
          { status: 'cancelled', count: 2 }
        ],
        clientGrowth: [
          { date: '2024-01-01', messages: 0, conversations: 0, appointments: 0, clients: 148 },
          { date: '2024-01-02', messages: 0, conversations: 0, appointments: 0, clients: 149 },
          { date: '2024-01-03', messages: 0, conversations: 0, appointments: 0, clients: 150 }
        ]
      },
      recentActivity: [
        {
          id: 1,
          type: 'conversation',
          title: 'Nova conversa iniciada',
          description: 'Cliente João iniciou uma conversa',
          timestamp: new Date().toISOString()
        },
        {
          id: 2,
          type: 'appointment',
          title: 'Agendamento confirmado',
          description: 'Consulta com Maria confirmada para hoje às 14h',
          timestamp: new Date(Date.now() - 3600000).toISOString()
        },
        {
          id: 3,
          type: 'message',
          title: 'Mensagem automática enviada',
          description: 'Lembrete de consulta enviado para 5 clientes',
          timestamp: new Date(Date.now() - 7200000).toISOString()
        }
      ]
    };

    return NextResponse.json({
      data: mockStats,
      success: true,
      message: 'Estatísticas diárias carregadas com sucesso'
    });
  } catch (error) {
    console.error('Erro ao buscar estatísticas diárias:', error);
    return NextResponse.json(
      { 
        error: 'Erro interno do servidor ao buscar estatísticas',
        success: false 
      },
      { status: 500 }
    );
  }
}
