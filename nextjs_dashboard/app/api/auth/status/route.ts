import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    console.log('🔍 Verificando status de autenticação...');

    // Verificar se há token nos cookies
    const accessToken = request.cookies.get('access_token')?.value;
    const sessionInfo = request.cookies.get('session-info')?.value;

    if (!accessToken) {
      console.log('❌ Nenhum token de acesso encontrado');
      return NextResponse.json({
        success: false,
        isAuthenticated: false,
        status: 'offline',
        message: 'Token de acesso não encontrado',
        timestamp: new Date().toISOString()
      });
    }

    // Verificar se o token ainda é válido fazendo uma requisição para o backend
    try {
      const backendResponse = await fetch('https://wppagent-production.up.railway.app/admin/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (backendResponse.ok) {
        console.log('✅ Token válido - usuário autenticado');
        return NextResponse.json({
          success: true,
          isAuthenticated: true,
          status: 'online',
          message: 'Usuário autenticado',
          timestamp: new Date().toISOString()
        });
      } else {
        console.log('❌ Token inválido ou expirado:', backendResponse.status);
        return NextResponse.json({
          success: false,
          isAuthenticated: false,
          status: 'offline',
          message: 'Token inválido ou expirado',
          timestamp: new Date().toISOString()
        });
      }
    } catch (backendError) {
      console.error('❌ Erro ao verificar token no backend:', backendError);
      return NextResponse.json({
        success: false,
        isAuthenticated: false,
        status: 'offline',
        message: 'Erro ao verificar token',
        timestamp: new Date().toISOString()
      });
    }

  } catch (error) {
    console.error('❌ Erro no sistema de autenticação:', error);
    return NextResponse.json(
      {
        success: false,
        isAuthenticated: false,
        status: 'offline',
        error: 'Sistema de autenticação indisponível',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
}