// API para conectar diretamente ao PostgreSQL e buscar TODAS as mensagens
import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// Configuração do banco PostgreSQL
const pool = new Pool({
  host: 'caboose.proxy.rlwy.net',
  port: 13910,
  database: 'railway',
  user: 'postgres',
  password: 'UGARTPCwAADBBeBLctoRnQXLsoUvLJxz',
  ssl: {
    rejectUnauthorized: false
  }
});

export async function GET(
  request: NextRequest,
  { params }: { params: { conversationId: string } }
) {
  let client;
  
  try {
    const conversationId = params.conversationId;
    
    console.log(`🔍 POSTGRESQL: Buscando TODAS as mensagens da conversa ${conversationId}`);
    
    // Conectar ao PostgreSQL
    client = await pool.connect();
    
    // Buscar TODAS as mensagens da conversa, ordenadas por data
    const query = `
      SELECT 
        id,
        direction,
        content,
        message_type,
        created_at,
        user_id
      FROM messages 
      WHERE conversation_id = $1 
      ORDER BY created_at ASC
    `;
    
    const result = await client.query(query, [conversationId]);
    
    if (result.rows.length === 0) {
      console.log(`⚠️ Nenhuma mensagem encontrada para conversa ${conversationId}`);
      
      return NextResponse.json({
        success: true,
        messages: [
          {
            id: Date.now(),
            content: `Esta conversa ainda não possui mensagens registradas.`,
            sender_type: 'agent',
            created_at: new Date().toISOString(),
            direction: 'out',
            message_type: 'text'
          }
        ],
        total: 0,
        conversation_id: conversationId,
        source: 'empty'
      });
    }
    
    // Converter mensagens para o formato da interface
    const formattedMessages = result.rows.map((row: any) => ({
      id: row.id,
      content: row.content || 'Mensagem sem conteúdo',
      sender_type: row.direction === 'in' ? 'user' as const : 'agent' as const,
      created_at: row.created_at,
      direction: row.direction,
      message_type: row.message_type || 'text'
    }));
    
    console.log(`✅ POSTGRESQL: ${formattedMessages.length} mensagens REAIS carregadas da conversa ${conversationId}`);
    
    return NextResponse.json({
      success: true,
      messages: formattedMessages,
      total: formattedMessages.length,
      conversation_id: conversationId,
      source: 'postgresql'
    });
    
  } catch (error) {
    console.error('❌ Erro ao conectar ao PostgreSQL:', error);
    
    return NextResponse.json({
      success: false,
      error: 'Erro ao carregar mensagens do banco',
      messages: [],
      details: error instanceof Error ? error.message : 'Erro desconhecido'
    }, { status: 500 });
    
  } finally {
    if (client) {
      client.release();
    }
  }
}
