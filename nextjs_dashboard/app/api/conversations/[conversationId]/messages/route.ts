import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import { debugLog } from '@/lib/debug';

// Force dynamic rendering for this route since it uses cookies
export const dynamic = 'force-dynamic';

// Configuração do banco PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway',
  ssl: {
    rejectUnauthorized: false
  }
});

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ conversationId: string }> }
) {
  let client;
  
  try {
    const { conversationId } = await params;
    debugLog.info(`🔍 API Messages: Buscando mensagens da conversa ${conversationId}`);

    // ✅ Extrair token do cookie HTTP-only para validação
    const authToken = request.cookies.get('access_token')?.value;
    debugLog.info('🔍 Token encontrado no cookie:', authToken ? 'Sim' : 'Não');

    if (!authToken) {
      debugLog.error('Token não encontrado');
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    // ✅ Extrair query params
    const searchParams = request.nextUrl.searchParams;
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    debugLog.info('📊 Parâmetros:', { conversationId, limit, offset });

    client = await pool.connect();
    
    // Query principal para buscar mensagens
    const messagesQuery = `
      SELECT 
        m.id,
        m.conversation_id,
        m.user_id,
        m.direction,
        m.content,
        m.message_type,
        m.message_id,
        m.created_at,
        u.nome as sender_name,
        u.telefone as sender_phone
      FROM messages m
      LEFT JOIN users u ON m.user_id = u.id
      WHERE m.conversation_id = $1
      ORDER BY m.created_at ASC
      LIMIT $2 OFFSET $3
    `;

    debugLog.info('🔍 Executando query de mensagens...');
    const messagesResult = await client.query(messagesQuery, [conversationId, limit, offset]);
    
    // Buscar total de mensagens para paginação
    const totalQuery = `SELECT COUNT(*) as total FROM messages WHERE conversation_id = $1`;
    const totalResult = await client.query(totalQuery, [conversationId]);
    const total = parseInt(totalResult.rows[0].total);

    // Formatar resposta
    const messages = messagesResult.rows.map(row => ({
      id: row.id,
      conversation_id: row.conversation_id,
      user_id: row.user_id,
      direction: row.direction,
      content: row.content,
      message_type: row.message_type,
      message_id: row.message_id,
      created_at: row.created_at,
      sender_name: row.sender_name && row.sender_name.trim() !== '' 
        ? row.sender_name 
        : row.sender_phone || 'Usuário',
      sender_phone: row.sender_phone,
    }));

    debugLog.info(`✅ Encontradas ${messages.length} mensagens de ${total} totais`);

    return NextResponse.json({
      success: true,
      data: messages,
      messages: messages, // Manter compatibilidade
      pagination: {
        total,
        limit,
        offset,
        hasMore: (offset + messages.length) < total,
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
    debugLog.error('Erro na API messages:', error);
    return NextResponse.json(
      { 
        error: 'Erro interno do servidor',
        message: error instanceof Error ? error.message : 'Erro desconhecido'
      },
      { status: 500 }
    );
  } finally {
    if (client) {
      client.release();
    }
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

