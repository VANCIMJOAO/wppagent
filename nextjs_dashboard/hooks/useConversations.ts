import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { toast } from 'sonner'
import type { Conversation, Message } from '@/types/api'
import { debugLog } from '@/lib/debug';

// Simulando serviço de API para conversas
const conversationsApi = {
  async getConversations(filters: {
    limit?: number
    page?: number
    status?: string
    user_id?: number
  }): Promise<{ conversations: Conversation[]; total: number; page: number; per_page: number; has_more: boolean }> {
    const params = new URLSearchParams()

    if (filters.limit) params.append('limit', filters.limit.toString())
    if (filters.page) params.append('page', filters.page.toString())
    if (filters.status) params.append('status', filters.status)
    if (filters.user_id) params.append('user_id', filters.user_id.toString())

    // 🔒 SECURITY: Usando cookies HttpOnly seguros via credentials: 'include'
    const response = await fetch(`/api/conversations?${params}`, {
      method: 'GET',
      credentials: 'include', // Inclui cookies HttpOnly automaticamente
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar conversas: ${response.statusText}`)
    }

    return response.json()
  },

  async getConversation(id: number): Promise<Conversation> {
    // 🔒 SECURITY: Usando cookies HttpOnly seguros via credentials: 'include'
    const response = await fetch(`/api/conversations/${id}`, {
      method: 'GET',
      credentials: 'include', // Inclui cookies HttpOnly automaticamente
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar conversa: ${response.statusText}`)
    }

    return response.json()
  },

  async getMessages(conversationId: number, filters: {
    limit?: number
    page?: number
  } = {}): Promise<{ messages: Message[]; total: number; page: number; per_page: number; has_more: boolean }> {
    const params = new URLSearchParams()

    if (filters.limit) params.append('limit', filters.limit.toString())
    if (filters.page) params.append('page', filters.page.toString())

    // 🔒 SECURITY: Usando cookies HttpOnly seguros via credentials: 'include'
    const response = await fetch(`/api/conversations/${conversationId}/messages?${params}`, {
      method: 'GET',
      credentials: 'include', // Inclui cookies HttpOnly automaticamente
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar mensagens: ${response.statusText}`)
    }

    return response.json()
  },

  async sendMessage(conversationId: number, data: { content: string; message_type?: string }): Promise<Message> {
    // 🔒 SECURITY: Usando cookies HttpOnly seguros via credentials: 'include'
    const response = await fetch(`/api/conversations/${conversationId}/messages`, {
      method: 'POST',
      credentials: 'include', // Inclui cookies HttpOnly automaticamente
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || `Erro ao enviar mensagem: ${response.statusText}`)
    }

    return response.json()
  }
}

// Hooks para conversas
export function useConversations(filters: {
  limit?: number
  page?: number
  status?: string
  user_id?: number
} = {}) {
  return useQuery({
    queryKey: queryKeys.conversations.list(filters),
    queryFn: () => conversationsApi.getConversations(filters),
    staleTime: 1 * 60 * 1000, // 1 minuto (dados mais dinâmicos)
    gcTime: 3 * 60 * 1000, // 3 minutos
    refetchOnWindowFocus: true, // Refetch ao focar na janela
    refetchInterval: 30 * 1000, // Refetch a cada 30 segundos
    retry: (failureCount, error: any) => {
      if (error?.status === 401 || error?.status === 403) {
        return false
      }
      return failureCount < 2
    }
  })
}

export function useConversation(id: number, enabled: boolean = true) {
  return useQuery({
    queryKey: [...queryKeys.conversations.all, 'detail', id] as const,
    queryFn: () => conversationsApi.getConversation(id),
    enabled: enabled && !!id,
    staleTime: 2 * 60 * 1000, // 2 minutos
    gcTime: 5 * 60 * 1000, // 5 minutos
  })
}

export function useMessages(conversationId: number, filters: {
  limit?: number
  page?: number
} = {}, enabled: boolean = true) {
  return useQuery({
    queryKey: [...queryKeys.conversations.messages(conversationId), JSON.stringify(filters)] as const,
    queryFn: () => conversationsApi.getMessages(conversationId, filters),
    enabled: enabled && !!conversationId,
    staleTime: 30 * 1000, // 30 segundos (mensagens são muito dinâmicas)
    gcTime: 2 * 60 * 1000, // 2 minutos
    refetchOnWindowFocus: true,
    refetchInterval: 10 * 1000, // Refetch a cada 10 segundos quando ativo
  })
}

export function useSendMessage() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ conversationId, data }: {
      conversationId: number
      data: { content: string; message_type?: string }
    }) => conversationsApi.sendMessage(conversationId, data),

    onMutate: async ({ conversationId, data }) => {
      // Cancelar queries de mensagens em andamento
      await queryClient.cancelQueries({
        queryKey: queryKeys.conversations.messages(conversationId)
      })

      // Snapshot dos dados anteriores
      const previousMessages = queryClient.getQueryData(
        queryKeys.conversations.messages(conversationId)
      )

      // Optimistic update - adicionar mensagem temporária
      const tempMessage = {
        id: Date.now(), // ID temporário
        conversation_id: conversationId,
        content: data.content,
        message_type: data.message_type || 'text',
        direction: 'out' as const, // Corrigido para 'out'
        created_at: new Date().toISOString(),
        is_read: false,
        whatsapp_id: undefined,
        sender_type: 'admin',
      } as Message

      queryClient.setQueryData(
        queryKeys.conversations.messages(conversationId),
        (old: any) => {
          if (!old) return { messages: [tempMessage], total: 1 }
          return {
            ...old,
            messages: [tempMessage, ...old.messages],
            total: old.total + 1
          }
        }
      )

      return { previousMessages, conversationId, tempMessage }
    },

    onSuccess: (newMessage, variables, context) => {
      // Atualizar com a mensagem real do servidor
      queryClient.setQueryData(
        queryKeys.conversations.messages(variables.conversationId),
        (old: any) => {
          if (!old) return { messages: [newMessage], total: 1 }

          // Substituir mensagem temporária pela real
          const updatedMessages = old.messages.map((msg: Message) =>
            msg.id === context?.tempMessage.id ? newMessage : msg
          )

          return {
            ...old,
            messages: updatedMessages
          }
        }
      )

      // Invalidar lista de conversas para atualizar última mensagem
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() })

      toast.success('Mensagem enviada!')
    },

    onError: (error: any, variables, context) => {
      // Reverter optimistic update
      if (context?.previousMessages) {
        queryClient.setQueryData(
          queryKeys.conversations.messages(variables.conversationId),
          context.previousMessages
        )
      }

      debugLog.error('Erro ao enviar mensagem:', error)
      toast.error(error.message || 'Erro ao enviar mensagem')
    },

    onSettled: (data, error, variables) => {
      // Sempre refetch após operação
      queryClient.invalidateQueries({
        queryKey: queryKeys.conversations.messages(variables.conversationId)
      })
    }
  })
}

// Hook para marcar mensagens como lidas
export function useMarkAsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ conversationId, messageIds }: {
      conversationId: number
      messageIds: number[]
    }) => {
      // 🔒 SECURITY: Usando cookies HttpOnly seguros via credentials: 'include'
      const response = await fetch(`/api/conversations/${conversationId}/messages/read`, {
        method: 'POST',
        credentials: 'include', // Inclui cookies HttpOnly automaticamente
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message_ids: messageIds })
      })

      if (!response.ok) {
        throw new Error('Erro ao marcar mensagens como lidas')
      }

      return response.json()
    },

    onSuccess: (data, variables) => {
      // Atualizar status das mensagens
      queryClient.setQueryData(
        queryKeys.conversations.messages(variables.conversationId),
        (old: any) => {
          if (!old) return old

          return {
            ...old,
            messages: old.messages.map((msg: Message) =>
              variables.messageIds.includes(msg.id)
                ? { ...msg, status: 'read' }
                : msg
            )
          }
        }
      )

      // Invalidar lista de conversas para atualizar contadores
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() })
    },

    onError: (error: any) => {
      debugLog.error('Erro ao marcar como lida:', error)
      toast.error('Erro ao marcar mensagens como lidas')
    }
  })
}

// Hook para invalidação manual de conversas
export function useInvalidateConversations() {
  const queryClient = useQueryClient()

  return {
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: queryKeys.conversations.all }),
    invalidateLists: () => queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() }),
    invalidateMessages: (conversationId: number) =>
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.messages(conversationId) }),
  }
}
