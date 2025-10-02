import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// Force dynamic rendering for this route since it uses cookies
export const dynamic = 'force-dynamic';

// Configuração do banco PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway',
  ssl: {
    rejectUnauthorized: false
  }
});

export async function GET(request: NextRequest) {
  let client;
  
  try {
    console.log('🔍 API Conversations: Buscando dados reais do PostgreSQL');

    // ✅ Extrair token do cookie HTTP-only para validação
    const authToken = request.cookies.get('access_token')?.value;
    console.log('🔍 Token encontrado no cookie:', authToken ? 'Sim' : 'Não');

    if (!authToken) {
      console.log('❌ Token não encontrado');
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    // ✅ Extrair query params
    const searchParams = request.nextUrl.searchParams;
    const limit = parseInt(searchParams.get('limit') || '500');
    const offset = parseInt(searchParams.get('offset') || '0');
    const status = searchParams.get('status');
    const search = searchParams.get('search');

    console.log('📊 Parâmetros:', { limit, offset, status, search });

    client = await pool.connect();
    
    // Query principal para buscar conversas com dados do usuário
    let conversationsQuery = `
      SELECT 
        c.id,
        c.user_id,
        c.status,
        c.last_message_at,
        c.created_at,
        c.updated_at,
        u.nome as user_name,
        u.telefone as user_phone,
        COUNT(m.id) as total_messages,
        (
          SELECT m2.content 
          FROM messages m2 
          WHERE m2.conversation_id = c.id 
          ORDER BY m2.created_at DESC 
          LIMIT 1
        ) as last_message_content,
        (
          SELECT m2.created_at 
          FROM messages m2 
          WHERE m2.conversation_id = c.id 
          ORDER BY m2.created_at DESC 
          LIMIT 1
        ) as last_message_time
      FROM conversations c
      JOIN users u ON c.user_id = u.id
      LEFT JOIN messages m ON c.id = m.conversation_id
    `;

    const conditions = [];
    const params = [];
    let paramCount = 0;

    // Aplicar filtros
    if (status) {
      paramCount++;
      conditions.push(`c.status = $${paramCount}`);
      params.push(status);
    }

    if (search) {
      paramCount++;
      conditions.push(`(u.nome ILIKE $${paramCount} OR u.telefone ILIKE $${paramCount})`);
      params.push(`%${search}%`);
    }

    if (conditions.length > 0) {
      conversationsQuery += ` WHERE ${conditions.join(' AND ')}`;
    }

    conversationsQuery += `
      GROUP BY c.id, u.nome, u.telefone, c.status, c.last_message_at, c.created_at, c.updated_at
      ORDER BY c.last_message_at DESC
      LIMIT $${paramCount + 1} OFFSET $${paramCount + 2}
    `;
    
    params.push(limit, offset);

    console.log('🔍 Executando query de conversas...');
    const conversationsResult = await client.query(conversationsQuery, params);
    
    // Buscar total de conversas para paginação
    let totalQuery = `SELECT COUNT(*) as total FROM conversations c JOIN users u ON c.user_id = u.id`;
    const totalParams = [];
    let totalParamCount = 0;

    if (status) {
      totalParamCount++;
      totalQuery += ` WHERE c.status = $${totalParamCount}`;
      totalParams.push(status);
    }

    if (search) {
      totalParamCount++;
      const whereClause = totalParamCount === 1 ? ' WHERE' : ' AND';
      totalQuery += `${whereClause} (u.nome ILIKE $${totalParamCount} OR u.telefone ILIKE $${totalParamCount})`;
      totalParams.push(`%${search}%`);
    }

    const totalResult = await client.query(totalQuery, totalParams);
    const total = parseInt(totalResult.rows[0].total);

    // Formatear resposta
    const conversations = conversationsResult.rows.map(row => ({
      id: row.id,
      user_id: row.user_id,
      status: row.status,
      last_message_at: row.last_message_at,
      created_at: row.created_at,
      updated_at: row.updated_at,
      nome: row.user_name,  // Mapear para nome esperado pelo frontend
      phone: row.user_phone,  // Mapear para phone esperado pelo frontend
      message_count: parseInt(row.total_messages) || 0,  // Mapear para message_count
      unread_messages: 0,  // Placeholder - sem campo is_read
      last_message: row.last_message_content || "Nenhuma mensagem",  // Usar última mensagem real
      last_message_time: row.last_message_time || row.last_message_at,  // Usar timestamp real
    }));

    console.log(`✅ Encontradas ${conversations.length} conversas de ${total} totais`);

    const responseData = {
      conversations,
      total,
      limit,
      offset,
      has_more: (offset + conversations.length) < total,
    };

    return NextResponse.json({
      success: true,
      data: conversations,
      conversations: conversations, // Manter compatibilidade
      pagination: {
        total,
        limit,
        offset,
        hasMore: (offset + conversations.length) < total,
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
    console.error('❌ Erro na API conversations:', error);
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    );
  } finally {
    if (client) {
      client.release();
    }
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // ✅ Extrair token do cookie HTTP-only
    const authToken = request.cookies.get('access_token')?.value;

    if (!authToken) {
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    // ✅ Fazer requisição POST para o Railway
    const response = await fetch(`${process.env.RAILWAY_API_URL || 'http://localhost:8000'}/conversations/`, {
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
