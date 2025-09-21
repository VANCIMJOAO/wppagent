import { useState, useEffect } from 'react';

export interface Conversation {
  id: string;
  user_id: number;
  status: 'active' | 'human' | 'closed';
  last_message_at: string;
  created_at: string;
  updated_at: string;
  user: {
    id: number;
    wa_id: string;
    nome: string;
    telefone: string;
    created_at: string;
  };
  messages_count: number;
  last_message?: {
    content: string;
    created_at: string;
    direction: 'in' | 'out';
  };
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
  page: number;
  limit: number;
  total_pages: number;
}

export interface MessagesResponse {
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
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const fetchConversations = async (pageNum: number = 1, limit: number = 20) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/conversations?page=${pageNum}&limit=${limit}`);
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data: ConversationsResponse = await response.json();
      
      setConversations(data.conversations);
      setTotal(data.total);
      setPage(data.page);
      setTotalPages(data.total_pages);
      
    } catch (err) {
      console.error('❌ Erro ao buscar conversas:', err);
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const refreshConversations = () => {
    fetchConversations(page);
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  return {
    conversations,
    loading,
    error,
    total,
    page,
    totalPages,
    fetchConversations,
    refreshConversations,
  };
}

export function useMessages(conversationId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMessages = async (convId: string) => {
    if (!convId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/messages/${convId}`);
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data: MessagesResponse = await response.json();
      
      if (data.success) {
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

  useEffect(() => {
    if (conversationId) {
      fetchMessages(conversationId);
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  return {
    messages,
    loading,
    error,
    fetchMessages,
    sendMessage,
  };
}
