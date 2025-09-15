/**
 * 🔐 API Route Segura para Login Admin
 * Credenciais são mantidas apenas no servidor
 */

import { NextRequest, NextResponse } from 'next/server';

// ✅ SEGURO: Credenciais apenas no servidor via environment variables
const BACKEND_URL = process.env.BACKEND_URL || 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = process.env.ADMIN_USERNAME || 'admin';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;

// Validação de configuração segura
if (!ADMIN_PASSWORD) {
  console.error('❌ ADMIN_PASSWORD não configurado nas variáveis de ambiente!');
}

export async function POST(request: NextRequest) {
  try {
    console.log('🔐 Login admin via API route segura...');

    // Validar configuração
    if (!ADMIN_PASSWORD) {
      return NextResponse.json(
        { error: 'Configuração de autenticação inválida' },
        { status: 500 }
      );
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      // ✅ SEGURO: Credenciais ficam apenas no servidor
      const response = await fetch(`${BACKEND_URL}/auth/admin/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          username: ADMIN_USERNAME,
          password: ADMIN_PASSWORD
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        console.error(`❌ Login falhou: ${response.status} ${response.statusText}`);
        return NextResponse.json(
          { error: 'Falha na autenticação' },
          { status: response.status }
        );
      }

      const data = await response.json();

      if (!data.token) {
        console.error('❌ Token não encontrado na resposta do backend');
        return NextResponse.json(
          { error: 'Token inválido recebido' },
          { status: 500 }
        );
      }

      console.log('✅ Login admin realizado com sucesso via API route');

      // ✅ SEGURO: Apenas o token é retornado ao cliente
      return NextResponse.json({
        token: data.token,
        expires_in: data.expires_in || 14 * 60 * 1000, // 14 minutos
      });

    } catch (fetchError: any) {
      clearTimeout(timeoutId);

      if (fetchError.name === 'AbortError') {
        console.error('❌ Timeout no login - backend não respondeu');
        return NextResponse.json(
          { error: 'Timeout na autenticação' },
          { status: 504 }
        );
      }

      console.error('❌ Erro na requisição de login:', fetchError.message);
      return NextResponse.json(
        { error: 'Erro interno na autenticação' },
        { status: 500 }
      );
    }

  } catch (error: any) {
    console.error('❌ Erro geral na API route de login:', error.message);
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    );
  }
}

// Método GET não permitido para segurança
export async function GET() {
  return NextResponse.json(
    { error: 'Método não permitido' },
    { status: 405 }
  );
}
