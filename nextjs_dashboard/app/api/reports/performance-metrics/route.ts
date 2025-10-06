import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const startDate = searchParams.get('start_date');
    const endDate = searchParams.get('end_date');

    // Usar APIs de analytics que sabemos que funcionam
    const [revenueResponse, appointmentsResponse, clientsResponse] = await Promise.all([
      fetch(`http://localhost:8000/api/analytics/revenue?period=monthly&months=1`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${request.cookies.get('access_token')?.value}`,
          'Content-Type': 'application/json',
        },
      }),
      fetch(`http://localhost:8000/api/analytics/appointments/by-status?days=30`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${request.cookies.get('access_token')?.value}`,
          'Content-Type': 'application/json',
        },
      }),
      fetch(`http://localhost:8000/api/analytics/clients/new-daily?days=30`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${request.cookies.get('access_token')?.value}`,
          'Content-Type': 'application/json',
        },
      })
    ]);

    debugLog.info(`🔄 Proxying performance-metrics request`);

    // Obter token de autenticação dos cookies
    const accessToken = request.cookies.get('access_token')?.value;
    
    if (!accessToken) {
      debugLog.warn('❌ Nenhum token de acesso encontrado nos cookies');
      return NextResponse.json({
        success: false,
        error: 'Token de acesso não encontrado',
        data: []
      }, { status: 401 });
    }

    if (!revenueResponse.ok || !appointmentsResponse.ok || !clientsResponse.ok) {
      debugLog.warn(`Backend performance-metrics API returned error`);
      return NextResponse.json({
        success: false,
        error: `Backend API error`,
        data: []
      }, { status: 500 });
    }

    const revenueData = await revenueResponse.json();
    const appointmentsData = await appointmentsResponse.json();
    const clientsData = await clientsResponse.json();
    
    // Calcular métricas de performance baseadas nos dados reais
    const totalRevenue = revenueData.data?.reduce((sum: number, item: any) => sum + (item.value || 0), 0) || 0;
    const totalAppointments = appointmentsData.data?.reduce((sum: number, item: any) => sum + (item.count || 0), 0) || 0;
    const totalClients = clientsData.data?.length || 0;
    const avgTicketValue = totalAppointments > 0 ? totalRevenue / totalAppointments : 0;
    const conversionRate = totalClients > 0 ? (totalAppointments / totalClients) * 100 : 0;

    const performanceMetrics = {
      revenue: {
        total: totalRevenue,
        growth: 0, // TODO: Implementar comparação com período anterior
        target: totalRevenue * 1.2 // 20% acima do atual
      },
      appointments: {
        total: totalAppointments,
        growth: 0,
        target: totalAppointments * 1.15
      },
      clients: {
        total: totalClients,
        growth: 0,
        target: totalClients * 1.25
      },
      efficiency: {
        avg_ticket_value: avgTicketValue,
        conversion_rate: conversionRate,
        response_time_minutes: 15 // Valor padrão
      }
    };
    
    debugLog.success(`✅ Performance metrics data proxied successfully:`, {
      totalRevenue,
      totalAppointments,
      totalClients,
      avgTicketValue,
      conversionRate
    });

    return NextResponse.json({
      success: true,
      data: performanceMetrics
    });

  } catch (error) {
    debugLog.error('❌ Erro na API proxy de performance-metrics:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Erro ao conectar com backend',
      message: error instanceof Error ? error.message : 'Erro desconhecido',
      data: []
    }, { 
      status: 503,
      headers: {
        'Retry-After': '60'
      }
    });
  }
}
