import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const days = searchParams.get('days') || '30';

    const backendUrl = `http://localhost:8000/api/analytics/appointments/by-service?days=${days}`;

    debugLog.info(`🔄 Proxying appointments by-service request to: ${backendUrl}`);

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
      debugLog.warn(`Backend appointments by-service API returned ${response.status}: ${response.statusText}`);
      return NextResponse.json({
        success: false,
        error: `Backend API error: ${response.status}`,
        data: []
      }, { status: response.status });
    }

    const data = await response.json();
    
    debugLog.success(`✅ Appointments by-service data proxied successfully:`, {
      days,
      serviceCount: data.data?.length || 0
    });

    return NextResponse.json(data);

  } catch (error) {
    debugLog.error('❌ Erro na API proxy de appointments by-service:', error);
    
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
