/**
 * API Route: Logout Seguro
 * Limpeza completa de cookies e invalidação de sessão
 */

import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/environment-config';

// Force dynamic rendering for this route since it uses cookies
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    // 🔍 Obter token do cookie para invalidar no backend
    const authToken = request.cookies.get('auth-token')?.value;

    // 🚪 Invalidar sessão no backend (se token disponível)
    if (authToken) {
      try {
        await fetch(`${config.apiBaseUrl}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          }
        });
      } catch (error) {
        console.error('Erro ao fazer logout no backend:', error);
        // Continuar com limpeza local mesmo se backend falhar
      }
    }

    // 🧹 Resposta com limpeza completa de cookies
    const response = NextResponse.json({
      success: true,
      message: 'Logout realizado com sucesso'
    });

    // 🗑️ Limpar todos os cookies de autenticação
    const cookieOptions = {
      httpOnly: true,
      secure: config.environment === 'production',
      sameSite: 'strict' as const,
      maxAge: 0, // Expirar imediatamente
      path: '/',
    };

    response.cookies.set('auth-token', '', cookieOptions);
    response.cookies.set('refresh-token', '', {
      ...cookieOptions,
      path: '/api/auth/refresh',
    });
    response.cookies.set('session-info', '', {
      ...cookieOptions,
      httpOnly: false, // Para ser acessível pelo JS
    });

    return response;

  } catch (error) {
    console.error('🚨 Erro no logout:', error);

    // Mesmo com erro, limpar cookies locais
    const response = NextResponse.json(
      { success: true, message: 'Logout local realizado' }
    );

    const cookieOptions = {
      httpOnly: true,
      secure: config.environment === 'production',
      sameSite: 'strict' as const,
      maxAge: 0,
      path: '/',
    };

    response.cookies.set('auth-token', '', cookieOptions);
    response.cookies.set('refresh-token', '', {
      ...cookieOptions,
      path: '/api/auth/refresh',
    });
    response.cookies.set('session-info', '', {
      ...cookieOptions,
      httpOnly: false,
    });

    return response;
  }
}
