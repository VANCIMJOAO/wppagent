import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || 'daily';
    const days = searchParams.get('days') || '7';
    const months = searchParams.get('months') || '6';
    const years = searchParams.get('years') || '3';

    // Construir URL da API do backend
    const backendUrl = `http://localhost:8000/api/analytics/revenue`;
    const url = new URL(backendUrl);
    url.searchParams.set('period', period);
    
    if (period === 'daily') {
      url.searchParams.set('days', days);
    } else if (period === 'monthly') {
      url.searchParams.set('months', months);
    } else if (period === 'yearly') {
      url.searchParams.set('years', years);
    }

    debugLog.info(`🔄 Proxying revenue request to: ${url.toString()}`);

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

    // Fazer request para o backend
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      debugLog.warn(`Backend revenue API returned ${response.status}: ${response.statusText}`);
      return NextResponse.json({
        success: false,
        error: `Backend API error: ${response.status}`,
        data: []
      }, { status: response.status });
    }

    const data = await response.json();
    
    debugLog.success(`✅ Revenue data proxied successfully:`, {
      period,
      dataPoints: data.data?.length || 0
    });

    return NextResponse.json(data);

  } catch (error) {
    debugLog.error('❌ Erro na API proxy de revenue:', error);
    
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
