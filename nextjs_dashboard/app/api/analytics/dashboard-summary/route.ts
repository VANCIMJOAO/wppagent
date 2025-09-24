import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    console.log('📊 API: Dashboard summary solicitado');

    // Verificar autenticação
    const authToken = request.cookies.get('access_token')?.value;
    if (!authToken) {
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    // Simular dados do dashboard (por enquanto)
    const dashboardData = {
      key_metrics: {
        total_customers: 150,
        total_conversations: 89,
        total_appointments: 23,
        total_messages: 456,
        overall_conversion_rate: 15.3,
        avg_response_time_minutes: 2.5,
        satisfaction_score: 4.2,
        total_revenue: 12500.00,
        roi_percentage: 18.5
      },
      recent_activity: [
        {
          id: 1,
          type: 'conversation',
          message: 'Nova conversa iniciada',
          timestamp: new Date().toISOString(),
          status: 'active'
        },
        {
          id: 2,
          type: 'appointment',
          message: 'Agendamento confirmado',
          timestamp: new Date(Date.now() - 300000).toISOString(),
          status: 'confirmed'
        }
      ],
      performance_trends: {
        daily_conversations: [12, 15, 8, 20, 18, 25, 22],
        daily_revenue: [1200, 1500, 800, 2000, 1800, 2500, 2200],
        conversion_rates: [12.5, 15.2, 8.1, 20.3, 18.7, 25.1, 22.4]
      }
    };

    console.log('✅ Dashboard summary retornado com sucesso');

    return NextResponse.json({
      success: true,
      data: dashboardData
    });

  } catch (error: any) {
    console.error('❌ Erro na API dashboard-summary:', error.message);
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    );
  }
}
