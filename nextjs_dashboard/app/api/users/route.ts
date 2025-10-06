import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.info('API Users: Iniciando carregamento de usuários...');
    
    // Buscar dados do backend
    const backendUrl = process.env.RAILWAY_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/users`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
      },
    });

    if (!response.ok) {
      debugLog.error(`Erro na resposta do backend: ${response.status} ${response.statusText}`);
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    debugLog.success('API Users: Dados recebidos do backend');

    // Retornar dados padronizados
    return NextResponse.json({
      success: true,
      data: data.data || data,
      users: data.data || data, // Manter compatibilidade
      pagination: {
        total: data.data?.length || 0,
        limit: 100,
        offset: 0,
        hasMore: false,
      }
    }, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });

  } catch (error) {
    debugLog.error('Erro na API Users:', error);
    
    // Retornar erro apropriado sem fallback mock
    return NextResponse.json({
      success: false,
      error: 'Serviço de usuários temporariamente indisponível',
      message: error instanceof Error ? error.message : 'Erro ao conectar com backend',
      data: [],
      users: []
    }, { 
      status: 503, // Service Unavailable
      headers: {
        'Retry-After': '60', // Cliente deve tentar novamente em 60 segundos
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      }
    });
  }
}

export async function POST(request: NextRequest) {
  try {
    debugLog.info('API Users: Criando novo usuário...');
    
    const body = await request.json();
    debugLog.info('Dados do usuário recebidos');
    
    // Buscar dados do backend
    const backendUrl = process.env.RAILWAY_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      debugLog.error(`Erro na resposta do backend: ${response.status} ${response.statusText}`);
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    debugLog.success('API Users: Usuário criado');

    return NextResponse.json({
      success: true,
      data: data.data || data,
      message: 'Usuário criado com sucesso'
    }, {
      status: 201,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });

  } catch (error) {
    debugLog.error('Erro na API Users POST:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Erro ao criar usuário',
      message: error instanceof Error ? error.message : 'Erro desconhecido'
    }, {
      status: 500,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });
  }
}

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
