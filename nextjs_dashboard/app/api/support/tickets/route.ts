import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.info('🎫 Buscando tickets de suporte do PostgreSQL...');

    const searchParams = request.nextUrl.searchParams;
    const status = searchParams.get('status') || '';
    const priority = searchParams.get('priority') || '';
    const category = searchParams.get('category') || '';
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    let whereConditions = [];
    let queryParams: any[] = [];
    let paramIndex = 1;

    if (status) {
      whereConditions.push(`status = $${paramIndex}`);
      queryParams.push(status);
      paramIndex++;
    }

    if (priority) {
      whereConditions.push(`priority = $${paramIndex}`);
      queryParams.push(priority);
      paramIndex++;
    }

    if (category) {
      whereConditions.push(`category = $${paramIndex}`);
      queryParams.push(category);
      paramIndex++;
    }

    const whereClause = whereConditions.length > 0
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    const ticketsQuery = `
      SELECT
        id,
        name,
        email,
        category,
        priority,
        subject,
        message,
        status,
        created_at,
        updated_at,
        resolved_at
      FROM support_tickets
      ${whereClause}
      ORDER BY created_at DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    queryParams.push(limit, offset);

    const tickets = await executeQuery(ticketsQuery, queryParams);

    const countQuery = `
      SELECT COUNT(*) as total
      FROM support_tickets
      ${whereClause}
    `;

    const totalResult = await executeQuery(countQuery, queryParams.slice(0, -2));
    const total = parseInt(totalResult[0]?.total || '0');

    const formattedTickets = tickets.map(ticket => ({
      id: ticket.id.toString(),
      name: ticket.name,
      email: ticket.email,
      category: ticket.category,
      priority: ticket.priority,
      subject: ticket.subject,
      message: ticket.message,
      status: ticket.status,
      created_at: ticket.created_at,
      updated_at: ticket.updated_at,
      resolved_at: ticket.resolved_at
    }));

    debugLog.info(`✅ Encontrados ${formattedTickets.length} tickets (total: ${total})`);

    return NextResponse.json({
      success: true,
      data: formattedTickets,
      tickets: formattedTickets, // For compatibility
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total
      }
    });

  } catch (error) {
    debugLog.error('Erro ao buscar tickets:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido',
        data: []
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    debugLog.info('🎫 Criando novo ticket de suporte...');

    const body = await request.json();
    const { name, email, category, priority, subject, message } = body;

    if (!name || !email || !category || !priority || !subject || !message) {
      return NextResponse.json(
        {
          success: false,
          error: 'Todos os campos são obrigatórios'
        },
        { status: 400 }
      );
    }

    const insertQuery = `
      INSERT INTO support_tickets (
        name, email, category, priority, subject, message, 
        status, created_at, updated_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, 'open', NOW(), NOW())
      RETURNING id, name, email, category, priority, subject, message, status, created_at
    `;

    const result = await executeQuery(insertQuery, [name, email, category, priority, subject, message]);

    if (result.length === 0) {
      throw new Error('Falha ao criar ticket');
    }

    const newTicket = result[0];

    debugLog.info(`✅ Ticket criado com ID: ${newTicket.id}`);

    return NextResponse.json({
      success: true,
      data: newTicket,
      message: 'Ticket criado com sucesso'
    });

  } catch (error) {
    debugLog.error('Erro ao criar ticket:', error);
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
