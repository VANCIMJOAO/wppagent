// API Route para buscar mensagens do PostgreSQL
import { NextRequest, NextResponse } from 'next/server';

// Função para buscar mensagens reais do Railway
async function fetchRealMessages(conversationId: string, authToken: string) {
  try {
    console.log(`🔍 API: Buscando mensagens REAIS para conversa ${conversationId}`);
    
    // Buscar mensagens reais do Railway (limite máximo 200 conforme Railway)
    const railwayResponse = await fetch(`https://wppagent-production.up.railway.app/conversations/${conversationId}/messages?limit=200`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!railwayResponse.ok) {
      const errorText = await railwayResponse.text();
      console.log(`⚠️ Railway erro ${railwayResponse.status} para conversa ${conversationId}:`, errorText);
      return null;
    }

    const railwayData = await railwayResponse.json();
    console.log(`✅ Mensagens reais obtidas para conversa ${conversationId}:`, railwayData);
    
    if (railwayData.success && railwayData.data && railwayData.data.messages) {
      return railwayData.data.messages; // ✅ Retornar apenas o array de mensagens
    }
    
    return null;
  } catch (error) {
    console.error(`❌ Erro ao buscar mensagens reais para conversa ${conversationId}:`, error);
    return null;
  }
}

// Função de fallback com dados mock (mantida para compatibilidade)
async function getFallbackMessages(conversationId: string) {
  try {
    // Simular consulta ao banco PostgreSQL baseada nos dados reais
    const messagesByConversation: { [key: string]: any[] } = {
      // João Victor Vancim (1865 mensagens)
      '10': [
        { id: 2643, content: 'SUPER TESTE - Conectividade', sender_type: 'user', created_at: '2025-08-19T21:42:03.617674Z' },
        { id: 2644, content: 'Como posso ajudar você? 😊\n\nPosso falar sobre serviços, agendar horários e muito mais!', sender_type: 'agent', created_at: '2025-08-19T21:42:03.642264Z' },
        { id: 2661, content: 'fsdfsdfsdfsdf', sender_type: 'user', created_at: '2025-08-29T15:33:12.816102Z' },
        { id: 2662, content: 'Perfeito! Vou providenciar isso agora.', sender_type: 'agent', created_at: '2025-08-29T15:33:13.928601Z' },
        { id: 2663, content: 'dasdasdsa', sender_type: 'user', created_at: '2025-08-29T16:04:35.896738Z' },
        { id: 2664, content: 'Entendi. Deixe-me verificar isso para você.', sender_type: 'agent', created_at: '2025-08-29T16:04:37.105057Z' },
        { id: 2665, content: 'dsadasdasdsada', sender_type: 'user', created_at: '2025-08-29T16:05:06.237772Z' },
        { id: 2666, content: 'Perfeito! Vou providenciar isso agora.', sender_type: 'agent', created_at: '2025-08-29T16:05:07.463508Z' },
        { id: 2667, content: 'fgdsfsdfsdf', sender_type: 'user', created_at: '2025-08-29T16:13:48.224428Z' },
        { id: 2668, content: 'Muito bem! Vou encaminhar sua solicitação.', sender_type: 'agent', created_at: '2025-08-29T16:13:49.344512Z' }
      ],
      // Load Test 1 (22 mensagens)
      '25': [
        { id: 1001, content: 'Load test message 1', sender_type: 'user', created_at: '2025-08-14T10:00:00Z' },
        { id: 1002, content: 'Como posso ajudar você? 😊\n\nPosso falar sobre serviços, agendar horários e muito mais!', sender_type: 'agent', created_at: '2025-08-14T10:00:05Z' },
        { id: 1003, content: 'Preciso de informações sobre agendamento', sender_type: 'user', created_at: '2025-08-14T10:01:00Z' },
        { id: 1004, content: 'Claro! Posso ajudar com agendamentos. Que tipo de serviço você precisa?', sender_type: 'agent', created_at: '2025-08-14T10:01:05Z' }
      ],
      // Load Test 3 (22 mensagens)
      '21': [
        { id: 1101, content: 'Load test message 3', sender_type: 'user', created_at: '2025-08-14T11:00:00Z' },
        { id: 1102, content: 'Como posso ajudar você? 😊\n\nPosso falar sobre serviços, agendar horários e muito mais!', sender_type: 'agent', created_at: '2025-08-14T11:00:05Z' },
        { id: 1103, content: 'Quais são os horários disponíveis?', sender_type: 'user', created_at: '2025-08-14T11:01:00Z' },
        { id: 1104, content: 'Vou verificar os horários disponíveis para você!', sender_type: 'agent', created_at: '2025-08-14T11:01:05Z' }
      ],
      // Fé (6 mensagens)
      '3': [
        { id: 301, content: 'Oi, boa tarde!', sender_type: 'user', created_at: '2025-08-12T14:30:00Z' },
        { id: 302, content: 'Boa tarde! Como posso ajudar você hoje?', sender_type: 'agent', created_at: '2025-08-12T14:30:05Z' },
        { id: 303, content: 'Gostaria de agendar um horário', sender_type: 'user', created_at: '2025-08-12T14:31:00Z' },
        { id: 304, content: 'Perfeito! Vou te ajudar com o agendamento. Qual serviço você precisa?', sender_type: 'agent', created_at: '2025-08-12T14:31:05Z' },
        { id: 305, content: 'Corte de cabelo', sender_type: 'user', created_at: '2025-08-12T14:32:00Z' },
        { id: 306, content: 'Ótimo! Temos horários disponíveis. Que dia seria melhor para você?', sender_type: 'agent', created_at: '2025-08-12T14:32:05Z' }
      ],
      // AITestUser634875 (8 mensagens)
      '28': [
        { id: 2801, content: 'Perfeito! Confirma o agendamento por favor', sender_type: 'user', created_at: '2025-08-15T16:00:00Z' },
        { id: 2802, content: 'Como posso ajudar você? 😊\n\nPosso falar sobre serviços, agendar horários e muito mais!', sender_type: 'agent', created_at: '2025-08-15T16:00:05Z' },
        { id: 2803, content: 'Quero confirmar meu agendamento de amanhã', sender_type: 'user', created_at: '2025-08-15T16:01:00Z' },
        { id: 2804, content: 'Vou verificar seu agendamento. Um momento, por favor.', sender_type: 'agent', created_at: '2025-08-15T16:01:05Z' }
      ],
      // João Silva (4 mensagens)
      '15': [
        { id: 1501, content: 'Bom dia!', sender_type: 'user', created_at: '2025-08-13T09:00:00Z' },
        { id: 1502, content: 'Bom dia! Como posso ajudar você?', sender_type: 'agent', created_at: '2025-08-13T09:00:05Z' },
        { id: 1503, content: 'Preciso remarcar meu agendamento', sender_type: 'user', created_at: '2025-08-13T09:01:00Z' },
        { id: 1504, content: 'Claro! Vou te ajudar com a remarcação.', sender_type: 'agent', created_at: '2025-08-13T09:01:05Z' }
      ]
    };

    return messagesByConversation[conversationId] || [];
  } catch (error) {
    console.error('❌ Erro ao buscar mensagens do banco:', error);
    return [];
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ conversationId: string }> }
) {
  try {
    const { conversationId } = await params;

    console.log(`🔍 API: Buscando mensagens REAIS para conversa ${conversationId}`);

    // Extrair token de autenticação
    const authToken = request.cookies.get('access_token')?.value;
    
    if (!authToken) {
      console.log('❌ Token não encontrado para buscar mensagens');
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    console.log(`🔑 Token encontrado para conversa ${conversationId}, length: ${authToken.length}`);

    // Buscar mensagens reais do Railway
    const realMessages = await fetchRealMessages(conversationId, authToken);

    if (!realMessages || realMessages.length === 0) {
      // Se não há mensagens reais, retornar array vazio (conversa sem mensagens)
      console.log(`📭 Conversa ${conversationId} não possui mensagens ainda`);

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
      .map(msg => ({
        ...msg,
        // ✅ CORRIGIDO: Mapear direction do Railway para frontend
        direction: msg.direction === 'incoming' ? 'in' : msg.direction === 'outgoing' ? 'out' : (msg.sender_type === 'user' ? 'in' : 'out'),
        message_type: msg.message_type || 'text',
        created_at: msg.created_at
      }))
      .reverse(); // ✅ CORRIGIDO: Inverter ordem para cronológica (mais antigas primeiro)

    console.log(`✅ API: Retornando ${formattedMessages.length} mensagens REAIS para conversa ${conversationId}`);

    return NextResponse.json({
      success: true,
      messages: formattedMessages,
      total: formattedMessages.length,
      conversation_id: conversationId,
      source: 'railway'
    });

  } catch (error) {
    console.error('❌ Erro na API de mensagens:', error);

    return NextResponse.json({
      success: false,
      error: 'Erro ao carregar mensagens',
      messages: []
    }, { status: 500 });
  }
}
