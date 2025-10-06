import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export const dynamic = 'force-dynamic';

/**
 * GET /api/users/me - Retorna dados do usuário autenticado atual
 */
export async function GET(request: NextRequest) {
  try {
    debugLog.info('🔍 API Users/Me: Buscando dados do usuário autenticado...');
    
    // Verificar token de autenticação
    const accessToken = request.cookies.get('access_token')?.value;
    
    if (!accessToken) {
      debugLog.warn('❌ Token de acesso não encontrado');
      return NextResponse.json({
        success: false,
        error: 'Não autenticado',
        user: null
      }, { status: 401 });
    }

    // Buscar dados do backend
    const backendUrl = process.env.NEXT_PUBLIC_DEV_API_URL || 'http://localhost:8000';
    
    debugLog.info(`🔄 Buscando usuário autenticado do backend: ${backendUrl}`);
    
    const response = await fetch(`${backendUrl}/api/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      debugLog.error(`⚠️ Backend retornou ${response.status}: ${response.statusText}`);
      
      // Se o backend não tiver /api/me, usar dados do token
      // Decodificar token JWT (base64)
      try {
        const tokenParts = accessToken.split('.');
        if (tokenParts.length === 3) {
          const payload = JSON.parse(atob(tokenParts[1]));
          
          debugLog.info('✅ Usando dados do token JWT');
          
          return NextResponse.json({
            success: true,
            user: {
              id: payload.sub || payload.user_id || 1,
              username: payload.username || 'admin',
              email: payload.email || payload.username + '@sistema.local',
              full_name: payload.full_name || payload.username,
              role: payload.role || 'admin',
              created_at: payload.iat ? new Date(payload.iat * 1000).toISOString() : new Date().toISOString(),
              last_login: new Date().toISOString(),
              is_active: true
            }
          }, { status: 200 });
        }
      } catch (decodeError) {
        debugLog.error('Erro ao decodificar token:', decodeError);
      }
      
      return NextResponse.json({
        success: false,
        error: response.statusText,
        user: null
      }, { status: response.status });
    }

    const data = await response.json();
    debugLog.success('✅ Dados do usuário recebidos do backend');

    return NextResponse.json({
      success: true,
      user: data.user || data.data || data
    }, { status: 200 });

  } catch (error) {
    debugLog.error('❌ Erro na API Users/Me:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Erro interno do servidor',
      message: error instanceof Error ? error.message : 'Unknown error',
      user: null
    }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}

