import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.info('📅 Buscando agendamentos do PostgreSQL...');
    
    // Extrair parâmetros de query
    const searchParams = request.nextUrl.searchParams;
    const status = searchParams.get('status') || 'all';
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');

    // Construir query base
    let whereConditions = [];
    let queryParams: any[] = [];
    let paramIndex = 1;

    // Filtro de status
    if (status !== 'all') {
      whereConditions.push(`a.status = $${paramIndex}`);
      queryParams.push(status);
      paramIndex++;
    }

    const whereClause = whereConditions.length > 0 
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    // Query principal para buscar agendamentos
    const appointmentsQuery = `
      SELECT 
        a.id,
        a.user_id,
        a.date_time,
        a.duration_minutes,
        a.end_time,
        a.status,
        a.notes,
        a.price,
        a.created_at,
        a.updated_at,
        u.nome as customer_name,
        u.telefone as customer_phone,
        u.email as customer_email,
        u.wa_id,
        s.name as service_name,
        b.name as business_name
      FROM appointments a
      JOIN users u ON a.user_id = u.id
      LEFT JOIN services s ON a.service_id = s.id
      LEFT JOIN businesses b ON a.business_id = b.id
      ${whereClause}
      ORDER BY a.date_time DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    queryParams.push(limit, offset);

    // Executar query
    const appointments = await executeQuery(appointmentsQuery, queryParams);

    // Buscar total de agendamentos para paginação
    const countQuery = `
      SELECT COUNT(*) as total
      FROM appointments a
      ${whereClause}
    `;
    
    const totalResult = await executeQuery(countQuery, queryParams.slice(0, -2));
    const total = parseInt(totalResult[0]?.total || '0');

    // Formatar dados para o frontend
    const formattedAppointments = appointments.map(appointment => {
      const dateTime = appointment.date_time ? new Date(appointment.date_time) : null;
      return {
        id: appointment.id.toString(),
        user_id: appointment.user_id.toString(),
        data_agendamento: dateTime ? dateTime.toISOString().split('T')[0] : null,
        hora_agendamento: dateTime ? dateTime.toTimeString().split(' ')[0] : null,
        date_time: appointment.date_time,
        duration_minutes: appointment.duration_minutes,
        end_time: appointment.end_time,
        status: appointment.status,
        servico: appointment.service_name || 'Serviço não especificado',
        service_name: appointment.service_name,
        business_name: appointment.business_name,
        observacoes: appointment.notes,
        notes: appointment.notes,
        price: appointment.price,
        created_at: appointment.created_at,
        updated_at: appointment.updated_at,
        customer_name: appointment.customer_name || 'Cliente sem nome',
        customer_phone: appointment.customer_phone,
        customer_email: appointment.customer_email,
        wa_id: appointment.wa_id
      };
    });

    debugLog.info(`✅ Encontrados ${formattedAppointments.length} agendamentos (total: ${total})`);

    return NextResponse.json({
      success: true,
      data: formattedAppointments,
      appointments: formattedAppointments, // Manter compatibilidade
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total
      }
    });

  } catch (error) {
    debugLog.error('Erro ao buscar agendamentos:', error);
    return NextResponse.json(
      { 
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido',
        data: [] // Retornar array vazio em caso de erro
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { user_id, date_time, duration_minutes = 60, service_id, business_id, notes, status = 'agendado', price = 0 } = body;

    if (!user_id || !date_time) {
      return NextResponse.json(
        { success: false, error: 'user_id e date_time são obrigatórios' },
        { status: 400 }
      );
    }

    // Inserir novo agendamento
    const insertQuery = `
      INSERT INTO appointments (user_id, business_id, service_id, date_time, duration_minutes, status, notes, price, created_at)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
      RETURNING id, user_id, business_id, service_id, date_time, duration_minutes, status, notes, price, created_at
    `;

    const newAppointment = await executeQuery(insertQuery, [
      user_id, 
      business_id || 3, // Default business_id (primeiro ID válido)
      service_id || 1, // Default service_id
      date_time, 
      duration_minutes,
      status,
      notes,
      price
    ]);

    debugLog.success('Novo agendamento criado:', newAppointment[0]);

    return NextResponse.json({
      success: true,
      data: newAppointment[0],
      message: 'Agendamento criado com sucesso'
    });

  } catch (error) {
    debugLog.error('Erro ao criar agendamento:', error);
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
