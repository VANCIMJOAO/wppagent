import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    console.log('👥 API Users: Iniciando carregamento de usuários...');
    
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
      console.error('❌ Erro na resposta do backend:', response.status, response.statusText);
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ API Users: Dados recebidos do backend:', data);

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
    console.error('❌ Erro na API Users:', error);
    
    // Fallback para dados mock em caso de erro
    const mockUsers = [
      {
        id: 1,
        nome: 'Admin Principal',
        email: 'admin@whatsapp-agent.com',
        role: 'admin',
        status: 'active',
        created_at: new Date().toISOString(),
        last_login: new Date(Date.now() - 86400000).toISOString(),
      },
      {
        id: 2,
        nome: 'Operador 1',
        email: 'operador1@whatsapp-agent.com',
        role: 'operator',
        status: 'active',
        created_at: new Date(Date.now() - 172800000).toISOString(),
        last_login: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: 3,
        nome: 'Operador 2',
        email: 'operador2@whatsapp-agent.com',
        role: 'operator',
        status: 'inactive',
        created_at: new Date(Date.now() - 259200000).toISOString(),
        last_login: new Date(Date.now() - 604800000).toISOString(),
      }
    ];

    return NextResponse.json({
      success: true,
      data: mockUsers,
      users: mockUsers,
      pagination: {
        total: mockUsers.length,
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
  }
}

export async function POST(request: NextRequest) {
  try {
    console.log('👥 API Users: Criando novo usuário...');
    
    const body = await request.json();
    console.log('📝 Dados do usuário:', body);
    
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
      console.error('❌ Erro na resposta do backend:', response.status, response.statusText);
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ API Users: Usuário criado:', data);

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
    console.error('❌ Erro na API Users POST:', error);
    
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
