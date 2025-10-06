import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    const backendUrl = `http://localhost:8000/api/analytics/clients/demographics`;

    debugLog.info(`🔄 Proxying clients demographics request to: ${backendUrl}`);

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
      debugLog.warn(`Backend clients demographics API returned ${response.status}: ${response.statusText}`);
      return NextResponse.json({
        success: false,
        error: `Backend API error: ${response.status}`,
        data: []
      }, { status: response.status });
    }

    const data = await response.json();
    
    debugLog.success(`✅ Clients demographics data proxied successfully:`, {
      ageGroups: data.data?.length || 0
    });

    return NextResponse.json(data);

  } catch (error) {
    debugLog.error('❌ Erro na API proxy de clients demographics:', error);
    
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
