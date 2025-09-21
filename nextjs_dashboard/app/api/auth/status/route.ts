/**
 * API Route: Status de Autenticação
 * Verifica se o usuário está autenticado via cookies seguros
 */

import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/environment-config';

// Force dynamic rendering for this route since we use cookies
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    // 🔍 Verificar cookies de autenticação
    const authToken = request.cookies.get('auth-token')?.value;
    const sessionInfo = request.cookies.get('session-info')?.value;

    if (!authToken) {
      return NextResponse.json({
        isAuthenticated: false,
        error: 'Nenhum token encontrado'
      });
    }

    // 📊 Tentar obter informações do usuário do cookie de sessão
    let userData = null;
    if (sessionInfo) {
      try {
        userData = JSON.parse(sessionInfo);

        // Verificar se o token não expirou
        if (userData.tokenExpiry && Date.now() > userData.tokenExpiry) {
          return NextResponse.json({
            isAuthenticated: false,
            error: 'Token expirado'
          });
        }
      } catch (e) {
        console.error('Erro ao parsear session-info:', e);
      }
    }

    // 🔐 Validar token JWT localmente (mais rápido e confiável)
    try {
      // Decodificar JWT para verificar se é válido
      const tokenParts = authToken.split('.');
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1]));
        const now = Math.floor(Date.now() / 1000);
        
        // Verificar se o token não expirou
        if (payload.exp && payload.exp < now) {
          return NextResponse.json({
            isAuthenticated: false,
            error: 'Token expirado'
          });
        }

        // Token válido
        return NextResponse.json({
          isAuthenticated: true,
          user: {
            id: payload.sub,
            role: payload.role,
            permissions: payload.permissions || []
          },
          tokenExpiry: payload.exp ? payload.exp * 1000 : null
        });
      }
    } catch (error) {
      console.error('Erro ao decodificar token:', error);
    }

    // 📋 Fallback: usar dados do cookie se backend não disponível
    if (userData && userData.isAuthenticated) {
      return NextResponse.json({
        isAuthenticated: true,
        user: userData.user,
        tokenExpiry: userData.tokenExpiry
      });
    }

    return NextResponse.json({
      isAuthenticated: false,
      error: 'Token inválido'
    });

  } catch (error) {
    console.error('🚨 Erro ao verificar status:', error);
    return NextResponse.json(
      {
        isAuthenticated: false,
        error: 'Erro interno do servidor'
      },
      { status: 500 }
    );
  }
}
