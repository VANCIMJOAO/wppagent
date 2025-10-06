import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const startDate = searchParams.get('start_date');
    const endDate = searchParams.get('end_date');

    // Usar a API dashboard que sabemos que funciona
    const backendUrl = `http://localhost:8000/api/dashboard?days=30`;

    debugLog.info(`🔄 Proxying business-overview request to: ${backendUrl}`);

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

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      debugLog.warn(`Backend business-overview API returned ${response.status}: ${response.statusText}`);
      return NextResponse.json({
        success: false,
        error: `Backend API error: ${response.status}`,
        data: []
      }, { status: response.status });
    }

    const data = await response.json();
    
    // Transformar dados do dashboard para formato de business overview
    const businessOverview = {
      total_customers: data.data?.total_customers || 0,
      total_conversations: data.data?.total_conversations || 0,
      total_messages: data.data?.total_messages || 0,
      total_appointments: data.data?.total_appointments || 0,
      overall_conversion_rate: data.data?.overall_conversion_rate || 0,
      avg_response_time_minutes: data.data?.avg_response_time_minutes || 0,
      satisfaction_score: data.data?.satisfaction_score || 0,
      trend_conversations: data.data?.trend_conversations || 0
    };
    
    debugLog.success(`✅ Business overview data proxied successfully:`, {
      customers: businessOverview.total_customers,
      conversations: businessOverview.total_conversations,
      appointments: businessOverview.total_appointments
    });

    return NextResponse.json({
      success: true,
      data: businessOverview
    });

  } catch (error) {
    debugLog.error('❌ Erro na API proxy de business-overview:', error);
    
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
