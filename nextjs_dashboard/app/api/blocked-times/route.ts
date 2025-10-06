import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.info('🚫 Buscando horários bloqueados do PostgreSQL...');
    
    // Extrair parâmetros de query
    const searchParams = request.nextUrl.searchParams;
    const search = searchParams.get('search') || '';
    const filterType = searchParams.get('filterType') || 'all';
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');

    // Construir query base
    let whereConditions = [];
    let queryParams: any[] = [];
    let paramIndex = 1;

    // Filtro de busca
    if (search) {
      whereConditions.push(`(
        bt.reason ILIKE $${paramIndex} OR 
        bt.block_type ILIKE $${paramIndex}
      )`);
      queryParams.push(`%${search}%`);
      paramIndex++;
    }

    // Filtro de tipo
    if (filterType !== 'all') {
      if (filterType === 'recurring') {
        whereConditions.push(`bt.is_recurring = true`);
      } else if (filterType === 'one-time') {
        whereConditions.push(`bt.is_recurring = false`);
      }
    }

    const whereClause = whereConditions.length > 0 
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    // Query principal para buscar horários bloqueados
    const blockedTimesQuery = `
      SELECT 
        bt.id,
        bt.business_id,
        bt.start_date,
        bt.end_date,
        bt.start_time,
        bt.end_time,
        bt.reason,
        bt.block_type,
        bt.is_recurring,
        bt.recurrence_pattern,
        bt.created_at,
        bt.created_by,
        b.name as business_name
      FROM blocked_times bt
      LEFT JOIN businesses b ON bt.business_id = b.id
      ${whereClause}
      ORDER BY bt.start_time DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    queryParams.push(limit, offset);

    // Executar query
    const blockedTimes = await executeQuery(blockedTimesQuery, queryParams);

    // Buscar total de horários bloqueados para paginação
    const countQuery = `
      SELECT COUNT(*) as total
      FROM blocked_times bt
      ${whereClause}
    `;
    
    const totalResult = await executeQuery(countQuery, queryParams.slice(0, -2));
    const total = parseInt(totalResult[0]?.total || '0');

    // Formatar dados para o frontend
    const formattedBlockedTimes = blockedTimes.map(blockedTime => ({
      id: blockedTime.id.toString(),
      business_id: blockedTime.business_id?.toString(),
      business_name: blockedTime.business_name || 'Negócio não especificado',
      start_time: blockedTime.start_time,
      end_time: blockedTime.end_time,
      start_date: blockedTime.start_date,
      end_date: blockedTime.end_date,
      reason: blockedTime.reason || 'Sem motivo especificado',
      block_type: blockedTime.block_type || 'manual',
      is_recurring: blockedTime.is_recurring || false,
      recurrence_pattern: blockedTime.recurrence_pattern,
      created_at: blockedTime.created_at,
      created_by: blockedTime.created_by || 'Sistema',
      // Campos adicionais para compatibilidade com o frontend
      notes: blockedTime.reason || '', // Usar reason como notes para compatibilidade
    }));

    debugLog.info(`✅ Encontrados ${formattedBlockedTimes.length} horários bloqueados (total: ${total})`);

    return NextResponse.json({
      success: true,
      data: formattedBlockedTimes,
      blockedTimes: formattedBlockedTimes, // Manter compatibilidade
      pagination: {
        total,
        limit,
        offset,
        hasMore: offset + limit < total
      }
    });

  } catch (error) {
    debugLog.error('Erro ao buscar horários bloqueados:', error);
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
    const { 
      business_id = 1, // Default business_id
      start_time, 
      end_time, 
      reason, 
      block_type = 'manual',
      is_recurring = false,
      recurrence_pattern = null,
      created_by = 'admin'
    } = body;

    if (!start_time || !end_time || !reason) {
      return NextResponse.json(
        { success: false, error: 'start_time, end_time e reason são obrigatórios' },
        { status: 400 }
      );
    }

    // Inserir novo horário bloqueado
    const insertQuery = `
      INSERT INTO blocked_times (
        business_id, start_date, end_date, start_time, end_time, 
        reason, block_type, is_recurring, recurrence_pattern, 
        created_by, created_at
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
      RETURNING id, business_id, start_date, end_date, start_time, end_time, 
                reason, block_type, is_recurring, recurrence_pattern, 
                created_at, created_by
    `;

    const newBlockedTime = await executeQuery(insertQuery, [
      business_id,
      start_time, // start_date
      end_time,   // end_date
      start_time, // start_time
      end_time,   // end_time
      reason,
      block_type,
      is_recurring,
      recurrence_pattern ? JSON.stringify(recurrence_pattern) : null,
      created_by
    ]);

    debugLog.success('Novo horário bloqueado criado:', newBlockedTime[0]);

    return NextResponse.json({
      success: true,
      data: newBlockedTime[0],
      message: 'Horário bloqueado criado com sucesso'
    });

  } catch (error) {
    debugLog.error('Erro ao criar horário bloqueado:', error);
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
