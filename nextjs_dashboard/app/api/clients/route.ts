import { NextRequest, NextResponse } from 'next/server';
import { executeQuery, executeCount } from '@/lib/database';

export async function GET(request: NextRequest) {
  try {
    console.log('👥 Buscando clientes do PostgreSQL...');
    
    // Extrair parâmetros de query
    const searchParams = request.nextUrl.searchParams;
    const search = searchParams.get('search') || '';
    const status = searchParams.get('status') || 'all';
    const sortBy = searchParams.get('sortBy') || 'name';
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    // Construir query base
    let whereConditions = [];
    let queryParams: any[] = [];
    let paramIndex = 1;

    // Filtro de busca
    if (search) {
      whereConditions.push(`(
        u.nome ILIKE $${paramIndex} OR 
        u.email ILIKE $${paramIndex} OR 
        u.telefone ILIKE $${paramIndex}
      )`);
      queryParams.push(`%${search}%`);
      paramIndex++;
    }

    // Filtro de status (baseado na última conversa)
    if (status !== 'all') {
      whereConditions.push(`c.status = $${paramIndex}`);
      queryParams.push(status);
      paramIndex++;
    }

    const whereClause = whereConditions.length > 0 
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    // Ordenação
    let orderBy = 'ORDER BY u.nome ASC';
    switch (sortBy) {
      case 'registrationDate':
        orderBy = 'ORDER BY u.created_at DESC';
        break;
      case 'lastVisit':
        orderBy = 'ORDER BY c.last_message_at DESC NULLS LAST';
        break;
      case 'appointments':
        orderBy = 'ORDER BY appointment_count DESC';
        break;
      default:
        orderBy = 'ORDER BY u.nome ASC';
    }

    // Query principal para buscar clientes
    const clientsQuery = `
      SELECT 
        u.id,
        u.wa_id,
        u.nome as name,
        u.email,
        u.telefone as phone,
        u.created_at as registration_date,
        c.status,
        c.last_message_at as last_visit,
        COUNT(DISTINCT a.id) as total_appointments,
        COUNT(DISTINCT c.id) as total_conversations,
        COUNT(DISTINCT m.id) as total_messages,
        CASE 
          WHEN COUNT(DISTINCT a.id) >= 10 THEN 'vip'
          WHEN c.status = 'active' THEN 'active'
          WHEN c.status = 'closed' OR c.status IS NULL THEN 'inactive'
          ELSE 'active'
        END as client_status
      FROM users u
      LEFT JOIN conversations c ON u.id = c.user_id
      LEFT JOIN appointments a ON u.id = a.user_id
      LEFT JOIN messages m ON u.id = m.user_id
      ${whereClause}
      GROUP BY u.id, u.wa_id, u.nome, u.email, u.telefone, u.created_at, c.status, c.last_message_at
      ${orderBy}
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    queryParams.push(limit, offset);

    // Executar query
    const clients = await executeQuery(clientsQuery, queryParams);

    // Buscar total de clientes para paginação
    const countQuery = `
      SELECT COUNT(DISTINCT u.id) as total
      FROM users u
      LEFT JOIN conversations c ON u.id = c.user_id
      ${whereClause}
    `;
    
    const totalResult = await executeQuery(countQuery, queryParams.slice(0, -2));
    const total = parseInt(totalResult[0]?.total || '0');

    // Formatar dados para o frontend
    const formattedClients = clients.map(client => ({
      id: client.id.toString(),
      wa_id: client.wa_id,
      name: client.name || 'Cliente sem nome',
      email: client.email || '',
      phone: client.phone || '',
      birthDate: null, // Não temos data de nascimento na tabela users
      registrationDate: client.registration_date,
      lastVisit: client.last_visit,
      totalAppointments: parseInt(client.total_appointments || '0'),
      totalConversations: parseInt(client.total_conversations || '0'),
      totalMessages: parseInt(client.total_messages || '0'),
      status: client.client_status,
      notes: null // Podemos adicionar notas futuramente
    }));

    console.log(`✅ Encontrados ${formattedClients.length} clientes (total: ${total})`);

    return NextResponse.json({
      success: true,
      clients: formattedClients,
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total
      }
    });

  } catch (error) {
    console.error('❌ Erro ao buscar clientes:', error);
    return NextResponse.json(
      { 
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, email, phone } = body;

    if (!name || !phone || !email) {
      return NextResponse.json(
        { success: false, error: 'Nome, telefone e email são obrigatórios' },
        { status: 400 }
      );
    }

    // Validar formato do email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { success: false, error: 'Formato de email inválido' },
        { status: 400 }
      );
    }

    // Gerar wa_id baseado no telefone
    const wa_id = phone.replace(/\D/g, ''); // Remove caracteres não numéricos

    // Verificar se já existe um usuário com este telefone ou email
    const existingUser = await executeQuery(
      'SELECT id FROM users WHERE telefone = $1 OR wa_id = $2 OR email = $3',
      [phone, wa_id, email]
    );

    if (existingUser.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Já existe um cliente com este telefone ou email' },
        { status: 409 }
      );
    }

    // Inserir novo cliente
    const insertQuery = `
      INSERT INTO users (wa_id, nome, email, telefone, created_at)
      VALUES ($1, $2, $3, $4, NOW())
      RETURNING id, wa_id, nome, email, telefone, created_at
    `;

    const newClient = await executeQuery(insertQuery, [wa_id, name, email, phone]);

    console.log('✅ Novo cliente criado:', newClient[0]);

    return NextResponse.json({
      success: true,
      client: {
        id: newClient[0].id.toString(),
        wa_id: newClient[0].wa_id,
        name: newClient[0].nome,
        email: newClient[0].email,
        phone: newClient[0].telefone,
        registrationDate: newClient[0].created_at,
        status: 'active',
        totalAppointments: 0,
        totalConversations: 0,
        totalMessages: 0
      }
    });

  } catch (error) {
    console.error('❌ Erro ao criar cliente:', error);
    return NextResponse.json(
      { 
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      },
      { status: 500 }
    );
  }
}
