import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    console.log('📝 API Templates: Iniciando carregamento de templates...');
    
    // Buscar dados do backend
    const backendUrl = process.env.RAILWAY_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/templates`, {
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
    console.log('✅ API Templates: Dados recebidos do backend:', data);

    // Retornar dados padronizados
    return NextResponse.json({
      success: true,
      data: data.data || data,
      templates: data.data || data, // Manter compatibilidade
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
    console.error('❌ Erro na API Templates:', error);
    
    // Fallback para dados mock em caso de erro
    const mockTemplates = [
      {
        id: 1,
        name: 'Boas-vindas',
        category: 'welcome',
        language: 'pt-BR',
        content: 'Olá {{name}}! Bem-vindo ao nosso atendimento. Como posso ajudá-lo hoje?',
        status: 'approved',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        variables: ['name'],
        approval_status: 'approved',
      },
      {
        id: 2,
        name: 'Confirmação de Agendamento',
        category: 'appointment',
        language: 'pt-BR',
        content: 'Seu agendamento foi confirmado para {{date}} às {{time}}. Aguardamos você!',
        status: 'approved',
        created_at: new Date(Date.now() - 86400000).toISOString(),
        updated_at: new Date(Date.now() - 86400000).toISOString(),
        variables: ['date', 'time'],
        approval_status: 'approved',
      },
      {
        id: 3,
        name: 'Lembrete de Consulta',
        category: 'reminder',
        language: 'pt-BR',
        content: 'Lembrete: Você tem uma consulta amanhã às {{time}}. Não esqueça!',
        status: 'pending',
        created_at: new Date(Date.now() - 172800000).toISOString(),
        updated_at: new Date(Date.now() - 172800000).toISOString(),
        variables: ['time'],
        approval_status: 'pending',
      },
      {
        id: 4,
        name: 'Cancelamento',
        category: 'cancellation',
        language: 'pt-BR',
        content: 'Seu agendamento para {{date}} foi cancelado. Entre em contato para reagendar.',
        status: 'approved',
        created_at: new Date(Date.now() - 259200000).toISOString(),
        updated_at: new Date(Date.now() - 259200000).toISOString(),
        variables: ['date'],
        approval_status: 'approved',
      }
    ];

    return NextResponse.json({
      success: true,
      data: mockTemplates,
      templates: mockTemplates,
      pagination: {
        total: mockTemplates.length,
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
    console.log('📝 API Templates: Criando novo template...');
    
    const body = await request.json();
    console.log('📝 Dados do template:', body);
    
    // Buscar dados do backend
    const backendUrl = process.env.RAILWAY_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/templates`, {
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
    console.log('✅ API Templates: Template criado:', data);

    return NextResponse.json({
      success: true,
      data: data.data || data,
      message: 'Template criado com sucesso'
    }, {
      status: 201,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });

  } catch (error) {
    console.error('❌ Erro na API Templates POST:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Erro ao criar template',
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
