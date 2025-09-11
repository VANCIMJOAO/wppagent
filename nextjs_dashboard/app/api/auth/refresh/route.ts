/**
 * API Route: Refresh Token Seguro
 * Renovação automática de tokens com HttpOnly cookies
 */

import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/environment-config';

// Force dynamic rendering for this route since it uses cookies
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    // 🔍 Obter refresh token do cookie HttpOnly
    const refreshToken = request.cookies.get('refresh-token')?.value;
    const authToken = request.cookies.get('auth-token')?.value;

    if (!refreshToken && !authToken) {
      return NextResponse.json(
        { success: false, error: 'Nenhum token encontrado' },
        { status: 401 }
      );
    }

    // 🔄 Tentar renovar token com backend
    const backendResponse = await fetch(`${config.apiBaseUrl}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authToken ? `Bearer ${authToken}` : '',
      },
      body: JSON.stringify({
        refresh_token: refreshToken
      })
    });

    const refreshData = await backendResponse.json();

    if (!backendResponse.ok || !refreshData.success) {
      // Token inválido - limpar cookies
      const response = NextResponse.json(
        { success: false, error: 'Token expirado' },
        { status: 401 }
      );

      response.cookies.delete('auth-token');
      response.cookies.delete('refresh-token');
      response.cookies.delete('session-info');

      return response;
    }

    // ✅ Token renovado com sucesso
    const isProduction = config.environment === 'production';
    const tokenExpiry = Date.now() + (refreshData.expires_in || 3600) * 1000;

    const response = NextResponse.json({
      success: true,
      tokenExpiry
    });

    // 🔐 Definir novos cookies seguros
    response.cookies.set('auth-token', refreshData.access_token, {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'strict',
      maxAge: refreshData.expires_in || 3600,
      path: '/',
    });

    // 📊 Atualizar informações de sessão
    const sessionInfo = request.cookies.get('session-info')?.value;
    if (sessionInfo) {
      try {
        const currentSession = JSON.parse(sessionInfo);
        response.cookies.set('session-info', JSON.stringify({
          ...currentSession,
          tokenExpiry
        }), {
          httpOnly: false,
          secure: isProduction,
          sameSite: 'strict',
          maxAge: refreshData.expires_in || 3600,
          path: '/',
        });
      } catch (e) {
        console.error('Erro ao atualizar session-info:', e);
      }
    }

    return response;

  } catch (error) {
    console.error('🚨 Erro no refresh:', error);
    return NextResponse.json(
      { success: false, error: 'Erro interno do servidor' },
      { status: 500 }
    );
  }
}
