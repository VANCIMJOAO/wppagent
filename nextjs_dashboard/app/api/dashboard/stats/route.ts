import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

// Force dynamic rendering for this route since it uses cookies
export const dynamic = 'force-dynamic';

/**
 * Proxy para o endpoint de estatísticas do dashboard no backend
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const days = searchParams.get('days') || '30';

    const backendUrl = `http://localhost:8000/api/dashboard?days=${days}`;

    debugLog.info(`🔄 Proxying dashboard stats request to: ${backendUrl}`);

    const accessToken = request.cookies.get('access_token')?.value;
    
    if (!accessToken) {
      debugLog.warn('❌ Nenhum token de acesso encontrado nos cookies');
      return NextResponse.json({
        success: false,
        error: 'Token de acesso não encontrado',
        data: null
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
      const errorText = await response.text();
      debugLog.warn(`⚠️ Backend dashboard stats API returned ${response.status}: ${response.statusText}`);
      return NextResponse.json({
        success: false,
        error: `Backend error: ${response.status}`,
        data: null
      }, { status: response.status });
    }

    const data = await response.json();
    
    debugLog.success(`✅ Dashboard stats data proxied successfully`);

    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });

  } catch (error) {
    debugLog.error('Erro ao buscar dashboard stats:', error);
    return NextResponse.json({
      success: false,
      error: 'Erro ao conectar com o backend',
      message: error instanceof Error ? error.message : 'Erro desconhecido',
      data: null
    }, { status: 500 });
  }
}

// ✅ Handler para OPTIONS (CORS preflight)
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

