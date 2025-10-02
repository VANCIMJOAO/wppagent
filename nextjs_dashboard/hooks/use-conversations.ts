import { useState, useEffect, useRef } from 'react';

export interface Conversation {
  id: number;
  user_id: number;
  status: 'active' | 'human' | 'closed';
  phone: string; // COALESCE(c.phone_number, u.telefone)
  nome: string; // u.nome
  last_message: string;
  last_message_time: string;
  message_count: number;
  created_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  content: string;
  message_type: string;
  direction: 'in' | 'out';
  created_at: string;
  whatsapp_id?: string;
}

export interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface MessagesResponse {
  error: string;
  success: any;
  messages: Message[];
  total: number;
  conversation_id: string;
  source: string;
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const fetchConversations = async (pageNum: number = 1, limit: number = 500) => {
    try {
      setLoading(true);
      setError(null);

      // Converter page para offset (page 1 = offset 0)
      const offset = (pageNum - 1) * limit;
      const response = await fetch(`/api/conversations?offset=${offset}&limit=${limit}`);
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const apiResponse = await response.json();
      
      console.log('🔍 Resposta completa da API:', apiResponse);
      
      // ✅ Verificar se há erro de autenticação
      if (apiResponse.error && apiResponse.status === 401) {
        throw new Error('Sessão expirada. Faça login novamente.');
      }
      
      // ✅ Extrair dados da estrutura aninhada { success: true, data: { conversations: [...] } }
      const data = apiResponse.data || apiResponse;
      
      console.log('🔍 Dados extraídos:', data);
      console.log('🔍 Conversas encontradas:', data.conversations?.length || 0);
      
      if (data.conversations && data.conversations.length > 0) {
        console.log('📝 Primeira conversa:', data.conversations[0]);
      }
      
      setConversations(data.conversations || []);
      setTotal(data.total || 0);
      setOffset(data.offset || 0);
      setHasMore(data.has_more || false);
      
    } catch (err) {
      console.error('❌ Erro ao buscar conversas:', err);
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const refreshConversations = () => {
    const currentPage = Math.floor(offset / 20) + 1;
    fetchConversations(currentPage);
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  return {
    conversations,
    loading,
    error,
    total,
    offset,
    hasMore,
    fetchConversations,
    refreshConversations,
  };
}

export function useMessages(conversationId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchMessages = async (convId: string) => {
    if (!convId) return;

    try {
      console.log(`🔍 useMessages: Iniciando busca de mensagens para conversa ${convId}`);
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/messages/${convId}`);
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data: MessagesResponse = await response.json();
      console.log(`📨 useMessages: Dados recebidos para conversa ${convId}:`, data);
      
      if (data.success) {
        console.log(`✅ useMessages: ${data.messages.length} mensagens carregadas para conversa ${convId}`);
        setMessages(data.messages);
      } else {
        throw new Error(data.error || 'Erro ao carregar mensagens');
      }
      
    } catch (err) {
      console.error('❌ Erro ao buscar mensagens:', err);
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (content: string) => {
    if (!conversationId || !content.trim()) return;

    try {
      const response = await fetch(`/api/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          direction: 'out',
          message_type: 'text',
        }),
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Recarregar mensagens após envio
        await fetchMessages(conversationId);
      }
      
    } catch (err) {
      console.error('❌ Erro ao enviar mensagem:', err);
      setError(err instanceof Error ? err.message : 'Erro ao enviar mensagem');
    }
  };

  // Função para scroll automático para a última mensagem
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    console.log(`🔄 useMessages: useEffect executado com conversationId: ${conversationId}`);
    if (conversationId) {
      console.log(`📞 useMessages: Chamando fetchMessages para conversa ${conversationId}`);
      fetchMessages(conversationId);
    } else {
      console.log(`🧹 useMessages: Limpando mensagens (conversationId vazio)`);
      setMessages([]);
    }
  }, [conversationId]);

  // Auto-scroll quando mensagens carregarem ou mudarem
  useEffect(() => {
    if (messages.length > 0 && !loading) {
      // Pequeno delay para garantir que o DOM foi atualizado
      setTimeout(scrollToBottom, 100);
    }
  }, [messages, loading]);

  return {
    messages,
    loading,
    error,
    fetchMessages,
    sendMessage,
    messagesEndRef, // Exportar ref para uso no componente
    scrollToBottom, // Exportar função de scroll
  };
}
