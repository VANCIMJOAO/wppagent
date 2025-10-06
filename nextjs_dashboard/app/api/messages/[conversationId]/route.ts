// API Route para buscar mensagens do PostgreSQL
import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

// Função para buscar mensagens reais do Railway
async function fetchRealMessages(conversationId: string, authToken: string) {
  try {
    debugLog.info(`🔍 API: Buscando mensagens REAIS para conversa ${conversationId}`);
    
    // Buscar mensagens reais do Railway (limite máximo 200 conforme Railway)
    const backendUrl = process.env.BACKEND_URL || (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : 'https://wppagent-production.up.railway.app');
    const railwayResponse = await fetch(`${backendUrl}/conversations/${conversationId}/messages?limit=200`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!railwayResponse.ok) {
      const errorText = await railwayResponse.text();
      debugLog.info(`⚠️ Railway erro ${railwayResponse.status} para conversa ${conversationId}:`, errorText);
      return null;
    }

    const railwayData = await railwayResponse.json();
    debugLog.info(`✅ Mensagens reais obtidas para conversa ${conversationId}:`, railwayData);
    
    if (railwayData.success && railwayData.data && railwayData.data.messages) {
      return railwayData.data.messages; // ✅ Retornar apenas o array de mensagens
    }
    
    return null;
  } catch (error) {
    debugLog.error(`❌ Erro ao buscar mensagens reais para conversa ${conversationId}:`, error);
    return null;
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ conversationId: string }> }
) {
  try {
    const { conversationId } = await params;

    debugLog.info(`🔍 API: Buscando mensagens REAIS para conversa ${conversationId}`);

    // Extrair token de autenticação
    const authToken = request.cookies.get('access_token')?.value;
    
    if (!authToken) {
      debugLog.error('Token não encontrado para buscar mensagens');
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    debugLog.info(`🔑 Token encontrado para conversa ${conversationId}, length: ${authToken.length}`);

    // Buscar mensagens reais do Railway
    const realMessages = await fetchRealMessages(conversationId, authToken);

    if (!realMessages || realMessages.length === 0) {
      // Se não há mensagens reais, retornar array vazio (conversa sem mensagens)
      debugLog.info(`📭 Conversa ${conversationId} não possui mensagens ainda`);

      return NextResponse.json({
        success: true,
        messages: [],
        total: 0,
        conversation_id: conversationId,
        source: 'empty'
      });
    }

    // ✅ Mensagens reais obtidas do Railway - formatar para o frontend
    const formattedMessages = realMessages
      .map((msg: any) => ({
        ...msg,
        // ✅ CORRIGIDO: Mapear direction do Railway para frontend
        direction: msg.direction === 'incoming' ? 'in' : msg.direction === 'outgoing' ? 'out' : (msg.sender_type === 'user' ? 'in' : 'out'),
        message_type: msg.message_type || 'text',
        created_at: msg.created_at
      }))
      .reverse(); // ✅ CORRIGIDO: Inverter ordem para cronológica (mais antigas primeiro)

    debugLog.info(`✅ API: Retornando ${formattedMessages.length} mensagens REAIS para conversa ${conversationId}`);

    return NextResponse.json({
      success: true,
      messages: formattedMessages,
      total: formattedMessages.length,
      conversation_id: conversationId,
      source: 'railway'
    });

  } catch (error) {
    let conversationId = 'unknown';
    try {
      conversationId = (await params).conversationId;
    } catch {}
    
    debugLog.error(`Erro ao buscar mensagens para conversa ${conversationId}:`, error);
    
    return NextResponse.json({
      success: false,
      error: 'Erro ao carregar mensagens',
      message: error instanceof Error ? error.message : 'Erro ao conectar com backend',
      messages: [],
      total: 0,
      conversation_id: conversationId
    }, { 
      status: 503, // Service Unavailable
      headers: {
        'Retry-After': '30' // Cliente deve tentar novamente em 30 segundos
      }
    });
  }
}
