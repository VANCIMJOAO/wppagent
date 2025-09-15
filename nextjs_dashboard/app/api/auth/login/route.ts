/**
 * API Route: Login Seguro
 * Autenticação server-side com HttpOnly cookies seguros
 */

import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/lib/environment-config';

interface LoginRequest {
  username: string;
  password: string;
  totp?: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: LoginRequest = await request.json();

    // Validação básica
    if (!body.username || !body.password) {
      return NextResponse.json(
        { success: false, error: 'Credenciais obrigatórias' },
        { status: 400 }
      );
    }

    // 🔐 Autenticar com backend
    const backendResponse = await fetch(`${config.apiBaseUrl}/admin/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'NextJS-Dashboard/1.0',
      },
      body: JSON.stringify({
        username: body.username,
        password: body.password
      })
    });

    const authData = await backendResponse.json();

    if (!backendResponse.ok) {
      return NextResponse.json(
        {
          success: false,
          error: authData.error || 'Credenciais inválidas'
        },
        { status: backendResponse.status }
      );
    }

    // 🛡️ Configurar resposta com cookies seguros
    const isProduction = config.environment === 'production';
    const tokenExpiry = Date.now() + (3600 * 1000); // 1 hora

    const response = NextResponse.json({
      success: true,
      user: authData.user || { username: body.username, role: 'admin' },
      tokenExpiry
    });

    // 🔐 Access Token (HttpOnly - NUNCA acessível via JavaScript)
    if (authData.access_token) {
      response.cookies.set('auth-token', authData.access_token, {
        httpOnly: true,          // 🛡️ Proteção XSS
        secure: isProduction,    // 🔒 HTTPS apenas em produção
        sameSite: 'strict',      // 🚫 Proteção CSRF
        maxAge: 3600,           // 1 hora
        path: '/',
      });
    }

    // 📊 Informações de sessão (acessível para UI)
    response.cookies.set('session-info', JSON.stringify({
      user: authData.user || { username: body.username, role: 'admin' },
      isAuthenticated: true,
      tokenExpiry
    }), {
      httpOnly: false,         // Acessível para React
      secure: isProduction,
      sameSite: 'strict',
      maxAge: 3600,
      path: '/',
    });

    return response;

  } catch (error) {
    console.error('🚨 Erro no login:', error);
    return NextResponse.json(
      { success: false, error: 'Erro interno do servidor' },
      { status: 500 }
    );
  }
}
