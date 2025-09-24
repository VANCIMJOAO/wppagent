import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    console.log('🔄 API: Solicitação de renovação de token recebida');

    // Verificar se há token atual nos cookies
    const currentToken = req.cookies.get('access_token')?.value;
    
    if (!currentToken) {
      console.log('❌ Nenhum token atual encontrado para renovação');
      return NextResponse.json({
        success: false,
        error: 'Token atual não encontrado'
      }, { status: 401 });
    }

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

    console.log('🔐 API: Fazendo login no backend para renovar token...');

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
    const newToken = loginData.data?.access_token || loginData.access_token;

    if (!newToken) {
      throw new Error('Token não foi retornado pelo backend');
    }

    console.log('✅ API: Novo token obtido com sucesso');

    // Criar resposta com o novo token
    const response = NextResponse.json({
      success: true,
      message: 'Token renovado com sucesso',
      token: newToken,
      expires_in: 7200 // 2 horas
    });

    // Configurar cookie com o novo token (2 horas)
    response.cookies.set('access_token', newToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 2 * 60 * 60 * 1000, // 2 horas
      path: '/'
    });

    // Atualizar cookie de sessão
    const sessionInfo = {
      isAuthenticated: true,
      tokenExpiry: Date.now() + (2 * 60 * 60 * 1000) // 2 horas
    };

    response.cookies.set('session-info', JSON.stringify(sessionInfo), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 2 * 60 * 60 * 1000, // 2 horas
      path: '/'
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
