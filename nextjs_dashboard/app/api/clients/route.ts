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
    console.log('🔍 API Clients: Buscando dados reais do PostgreSQL');

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
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');
    const search = searchParams.get('search');

    console.log('📊 Parâmetros:', { limit, offset, search });

    client = await pool.connect();
    
    // Query para buscar clientes (usuários)
    let clientsQuery = `
      SELECT 
        u.id,
        u.nome,
        u.telefone,
        u.email,
        u.created_at,
        COUNT(DISTINCT c.id) as total_conversations,
        COUNT(DISTINCT a.id) as total_appointments
      FROM users u
      LEFT JOIN conversations c ON u.id = c.user_id
      LEFT JOIN appointments a ON u.id = a.user_id
    `;

    const conditions = [];
    const params = [];
    let paramCount = 0;

    // Aplicar filtro de busca
    if (search) {
      paramCount++;
      conditions.push(`(u.nome ILIKE $${paramCount} OR u.telefone ILIKE $${paramCount} OR u.email ILIKE $${paramCount})`);
      params.push(`%${search}%`);
    }

    if (conditions.length > 0) {
      clientsQuery += ` WHERE ${conditions.join(' AND ')}`;
    }

    clientsQuery += `
      GROUP BY u.id, u.nome, u.telefone, u.email, u.created_at
      ORDER BY u.nome ASC
      LIMIT $${paramCount + 1} OFFSET $${paramCount + 2}
    `;
    
    params.push(limit, offset);

    console.log('🔍 Executando query de clientes...');
    const clientsResult = await client.query(clientsQuery, params);
    
    // Buscar total de clientes para paginação
    let totalQuery = `SELECT COUNT(*) as total FROM users u`;
    const totalParams = [];
    let totalParamCount = 0;

    if (search) {
      totalParamCount++;
      totalQuery += ` WHERE (u.nome ILIKE $${totalParamCount} OR u.telefone ILIKE $${totalParamCount} OR u.email ILIKE $${totalParamCount})`;
      totalParams.push(`%${search}%`);
    }

    const totalResult = await client.query(totalQuery, totalParams);
    const total = parseInt(totalResult.rows[0].total);

    // Formatear resposta
    const clients = clientsResult.rows.map(row => ({
      id: row.id,
      nome: row.nome,
      telefone: row.telefone,
      email: row.email,
      created_at: row.created_at,
      total_conversations: parseInt(row.total_conversations) || 0,
      total_appointments: parseInt(row.total_appointments) || 0,
      status: 'active', // Status padrão - pode ser expandido no futuro
      wa_id: row.telefone, // Usar telefone como wa_id por enquanto
      last_interaction: null, // Campo para compatibilidade
    }));

    console.log(`✅ Encontrados ${clients.length} clientes de ${total} totais`);

    const responseData = {
      clients,
      total,
      limit,
      offset,
      has_more: (offset + clients.length) < total,
    };

    return NextResponse.json({
      success: true,
      data: clients,
      clients: clients, // Manter compatibilidade
      pagination: {
        total,
        limit,
        offset,
        hasMore: (offset + clients.length) < total,
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
    console.error('❌ Erro na API clients:', error);
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