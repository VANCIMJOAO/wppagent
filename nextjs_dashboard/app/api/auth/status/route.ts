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

    // ✅ CORREÇÃO: Verificar token localmente como o middleware
    try {
      const { jwtVerify } = await import('jose');
      const secret = process.env.JWT_SECRET || 'fallback-secret-key';
      const secretKey = new TextEncoder().encode(secret);
      
      const result = await jwtVerify(accessToken, secretKey);
      
      if (result.payload) {
        console.log('✅ Token válido - usuário autenticado localmente');
        return NextResponse.json({
          success: true,
          isAuthenticated: true,
          status: 'online',
          message: 'Usuário autenticado',
          timestamp: new Date().toISOString(),
          user: {
            user_id: result.payload.user_id,
            username: result.payload.username,
            role: result.payload.role
          }
        });
      } else {
        console.log('❌ Token inválido - payload vazio');
        return NextResponse.json({
          success: false,
          isAuthenticated: false,
          status: 'offline',
          message: 'Token inválido',
          timestamp: new Date().toISOString()
        });
      }
    } catch (jwtError) {
      console.error('❌ Erro ao verificar token JWT:', jwtError);
      return NextResponse.json({
        success: false,
        isAuthenticated: false,
        status: 'offline',
        message: 'Token inválido ou expirado',
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