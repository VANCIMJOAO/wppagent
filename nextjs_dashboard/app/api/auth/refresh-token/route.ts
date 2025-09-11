import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    console.log('🔄 API: Solicitação de renovação de token recebida');
    
    // ✅ SEGURO: Credenciais via environment variables
    const credentials = {
      username: process.env.ADMIN_USERNAME || 'admin',
      password: process.env.ADMIN_PASSWORD
    };
    
    // Validação de segurança
    if (!credentials.password) {
      return NextResponse.json(
        { error: 'Configuração de autenticação inválida' },
        { status: 500 }
      );
    }
    
    console.log('🔐 API: Fazendo login no backend...');
    
    // Login no backend para obter novo token
    const loginResponse = await fetch('https://wppagent-production.up.railway.app/admin/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials)
    });

    if (!loginResponse.ok) {
      const errorText = await loginResponse.text();
      console.error('❌ API: Falha no login do backend:', loginResponse.status, errorText);
      throw new Error(`Login falhou: ${loginResponse.status}`);
    }

    const loginData = await loginResponse.json();
    const newToken = loginData.access_token;
    
    if (!newToken) {
      throw new Error('Token não foi retornado pelo backend');
    }

    console.log('✅ API: Novo token obtido com sucesso');
    
    // Criar resposta com o novo token
    const response = NextResponse.json({
      success: true,
      message: 'Token renovado com sucesso',
      token: newToken,
      expires_in: loginData.expires_in || 900
    });

    // Configurar cookie com o novo token
    response.cookies.set('auth-token', newToken, {
      path: '/',
      maxAge: 86400, // 24 horas
      httpOnly: false, // Permitir acesso via JavaScript
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax'
    });

    return response;

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
    console.error('❌ API: Erro ao renovar token:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Falha ao renovar token',
      details: errorMessage
    }, { status: 500 });
  }
}

export async function GET() {
  return NextResponse.json({
    message: 'Endpoint de renovação de token',
    usage: 'POST /api/auth/refresh-token',
    description: 'Renova automaticamente o token de autenticação'
  });
}
