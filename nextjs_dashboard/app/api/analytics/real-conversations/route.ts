import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import { debugLog } from '@/lib/debug';

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
    debugLog.info('💬 Buscando conversas reais do PostgreSQL...');
    
    // Extrair query params
    const searchParams = request.nextUrl.searchParams;
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');
    
    client = await pool.connect();
    
    // Buscar conversas com dados do usuário
    const conversationsQuery = `
      SELECT 
        c.id,
        u.nome as customer_name,
        u.telefone as customer_phone,
        c.status,
        c.last_message_at,
        c.created_at,
        COUNT(m.id) as message_count,
        (
          SELECT m2.content 
          FROM messages m2 
          WHERE m2.conversation_id = c.id 
          ORDER BY m2.created_at DESC 
          LIMIT 1
        ) as last_message
      FROM conversations c
      JOIN users u ON c.user_id = u.id
      LEFT JOIN messages m ON c.id = m.conversation_id
      GROUP BY c.id, u.nome, u.telefone, c.status, c.last_message_at, c.created_at
      ORDER BY c.last_message_at DESC
      LIMIT $1 OFFSET $2
    `;
    
    const conversationsResult = await client.query(conversationsQuery, [limit, offset]);
    
    // Buscar total de conversas para paginação
    const totalQuery = `SELECT COUNT(*) as total FROM conversations`;
    const totalResult = await client.query(totalQuery);
    const total = parseInt(totalResult.rows[0].total);
    
    const conversations = conversationsResult.rows.map(conv => ({
      id: conv.id,
      customer_name: conv.customer_name || 'Cliente',
      customer_phone: conv.customer_phone || '',
      status: conv.status || 'active',
      last_message: conv.last_message || 'Nenhuma mensagem',
      last_message_time: conv.last_message_at,
      created_at: conv.created_at,
      message_count: parseInt(conv.message_count) || 0
    }));
    
    debugLog.success('Conversas reais obtidas:', {
      total: total,
      returned: conversations.length,
      limit: limit,
      offset: offset
    });
    
    return NextResponse.json({
      conversations,
      total,
      limit,
      offset
    });
    
  } catch (error) {
    debugLog.error('Erro ao buscar conversas:', error);
    return NextResponse.json(
      { error: 'Erro ao buscar conversas' },
      { status: 500 }
    );
  } finally {
    if (client) {
      client.release();
    }
  }
}

