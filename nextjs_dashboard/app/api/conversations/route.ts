import { NextRequest, NextResponse } from 'next/server';

// Force dynamic rendering for this route since it uses cookies
export const dynamic = 'force-dynamic';

const RAILWAY_API_URL = process.env.RAILWAY_API_URL || 'https://wppagent-production.up.railway.app';

export async function GET(request: NextRequest) {
  try {
    console.log('🔍 API Conversations: Iniciando proxy para Railway');
    
    // ✅ Extrair token do cookie HTTP-only
    const authToken = request.cookies.get('auth-token')?.value;
    console.log('🔍 Token encontrado no cookie:', authToken ? 'Sim' : 'Não');
    
    if (!authToken) {
      console.log('❌ Token não encontrado');
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    // ✅ Extrair query params (limit, offset, etc.)
    // Usar nextUrl.searchParams ao invés de new URL(request.url) para compatibilidade estática
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString();
    const railwayUrl = `${RAILWAY_API_URL}/conversations/${queryString ? '?' + queryString : ''}`;
    
    console.log('🚀 Fazendo requisição para:', railwayUrl);

    // ✅ Fazer requisição para o Railway com token
    const response = await fetch(railwayUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    console.log('📡 Resposta do Railway:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.log('❌ Erro do Railway:', errorText);
      
      return NextResponse.json(
        { error: `Erro do servidor: ${response.status} ${response.statusText}` },
        { status: response.status }
      );
    }

    // ✅ Retornar dados com CORS headers
    const data = await response.json();
    console.log('✅ Dados obtidos:', data ? 'Sim' : 'Não');

    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });

  } catch (error) {
    console.error('❌ Erro na API conversations:', error);
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // ✅ Extrair token do cookie HTTP-only
    const authToken = request.cookies.get('auth-token')?.value;
    
    if (!authToken) {
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    // ✅ Fazer requisição POST para o Railway
    const response = await fetch(`${RAILWAY_API_URL}/conversations/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Erro do servidor: ${response.status} ${response.statusText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });

  } catch (error) {
    console.error('❌ Erro na API conversations POST:', error);
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    );
  }
}

// ✅ Handler para OPTIONS (CORS preflight)
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}