/**
 * 🔄 Hooks para Cache Invalidation Automática
 * ==========================================
 *
 * Hooks React que automatizam invalidação de cache baseado em eventos,
 * garantindo que o frontend sempre tenha dados atualizados.
 *
 * Funcionalidades:
 * - Auto-invalidation baseado em eventos
 * - WebSocket integration para real-time updates
 * - Query invalidation inteligente
 * - Context-aware cache management
 *
 * Autor: Claude AI
 * Status: Solução crítica para cache consistency
 */

import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useCallback, useRef } from 'react'
import { toast } from 'sonner'

// Helper para converter readyState em texto
function getReadyStateText(readyState: number): string {
  switch (readyState) {
    case WebSocket.CONNECTING: return 'CONNECTING'
    case WebSocket.OPEN: return 'OPEN'
    case WebSocket.CLOSING: return 'CLOSING'
    case WebSocket.CLOSED: return 'CLOSED'
    default: return 'UNKNOWN'
  }
}

// ===== TYPES =====

export interface CacheInvalidationEvent {
  type: 'cache_invalidated'
  event: string
  entity_id?: number
  context?: Record<string, any>
  timestamp: string
  server_id?: string
}

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

// ===== INVALIDATION MAPPING =====

const INVALIDATION_MAPPING: Record<string, string[]> = {
  // Appointment Events
  'appointment_created': [
    'appointments',
    'dashboard-stats',
    'appointments-calendar',
    'clients-stats',
    'analytics-funnel',
    'reports-appointments'
  ],
  'appointment_updated': [
    'appointments',
    'dashboard-stats',
    'clients-stats',
    'analytics-funnel'
  ],
  'appointment_deleted': [
    'appointments',
    'dashboard-stats',
    'clients-stats',
    'analytics-funnel',
    'reports-appointments'
  ],

  // Conversation Events
  'conversation_created': [
    'conversations',
    'dashboard-stats',
    'clients-stats',
    'analytics-conversations'
  ],
  'conversation_updated': [
    'conversations',
    'dashboard-stats',
    'analytics-conversations'
  ],

  // Client Events
  'client_created': [
    'clients',
    'clients-stats',
    'dashboard-stats'
  ],
  'client_updated': [
    'clients',
    'clients-stats'
  ],

  // Business Events
  'business_updated': [
    'business-config',
    'dashboard-stats'
  ],

  // Dashboard Events
  'dashboard_refresh': [
    'dashboard-stats',
    'dashboard-overview'
  ]
}

// ===== HOOKS =====

/**
 * 🔄 Hook principal para invalidação automática de cache
 *
 * Gerencia invalidações baseado em eventos específicos ou WebSocket.
 */
export function useApiWithInvalidation() {
  const queryClient = useQueryClient()

  const invalidateRelatedQueries = useCallback((
    event: string,
    entityId?: number,
    context?: Record<string, any>
  ) => {
    console.log(`🔄 Invalidating cache for event: ${event}`, { entityId, context })

    // Buscar queries relacionadas ao evento
    const queriesToInvalidate = INVALIDATION_MAPPING[event] || []

    // Invalidar queries gerais
    queriesToInvalidate.forEach(queryKey => {
      queryClient.invalidateQueries({ queryKey: [queryKey] })
      console.log(`  ✅ Invalidated: ${queryKey}`)
    })

    // Invalidar queries específicas com entity_id
    if (entityId) {
      if (event.includes('appointment')) {
        queryClient.invalidateQueries({ queryKey: ['appointment-detail', entityId] })
        console.log(`  ✅ Invalidated: appointment-detail:${entityId}`)
      }

      if (event.includes('conversation')) {
        queryClient.invalidateQueries({ queryKey: ['conversation-detail', entityId] })
        console.log(`  ✅ Invalidated: conversation-detail:${entityId}`)
      }

      if (event.includes('client')) {
        queryClient.invalidateQueries({ queryKey: ['client-detail', entityId] })
        queryClient.invalidateQueries({ queryKey: ['client-appointments', entityId] })
        console.log(`  ✅ Invalidated: client-detail:${entityId}`)
      }
    }

    // Invalidar queries baseado em context
    if (context) {
      if (context.client_id) {
        queryClient.invalidateQueries({ queryKey: ['client-appointments', context.client_id] })
        queryClient.invalidateQueries({ queryKey: ['client-conversations', context.client_id] })
        console.log(`  ✅ Invalidated client context: ${context.client_id}`)
      }

      if (context.business_id) {
        queryClient.invalidateQueries({ queryKey: ['business-stats', context.business_id] })
        console.log(`  ✅ Invalidated business context: ${context.business_id}`)
      }
    }

  }, [queryClient])

  return { invalidateRelatedQueries }
}

/**
 * 🔗 Hook para conexão WebSocket com invalidação automática
 *
 * Conecta com o WebSocket do servidor e invalida cache automaticamente
 * quando recebe eventos de invalidação.
 */
export function useWebSocketCacheSync(
  enabled: boolean = true,
  wsUrl: string = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
) {
  const { invalidateRelatedQueries } = useApiWithInvalidation()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      console.log('🔗 Connecting to WebSocket:', wsUrl)
      console.log('🔍 Current time:', new Date().toISOString())
      console.log('🔍 Environment:', {
        isBrowser: typeof window !== 'undefined',
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'N/A',
        protocol: typeof location !== 'undefined' ? location.protocol : 'N/A'
      })
      
      const ws = new WebSocket(wsUrl)
      console.log('🔌 WebSocket object created:', {
        readyState: ws.readyState,
        readyStateText: getReadyStateText(ws.readyState),
        url: ws.url,
        protocol: ws.protocol
      })


      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)

          if (message.type === 'cache_invalidated') {
            const cacheEvent = message as CacheInvalidationEvent

            // Invalidar cache automaticamente
            invalidateRelatedQueries(
              cacheEvent.event,
              cacheEvent.entity_id,
              cacheEvent.context
            )

            console.log('🔔 Cache invalidated via WebSocket:', cacheEvent.event)
          }

          else if (message.type === 'connection_established') {
            console.log('🔌 WebSocket connection established:', message)
            toast.success('🔌 Conectado em tempo real', {
              description: 'Notificações ativas'
            })
          }

          else if (message.type === 'heartbeat') {
            // Responder heartbeat se necessário
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }))
            }
          }

          // Tratar eventos de agendamento
          else if (message.type === 'appointment_created') {
            console.log('📅 Novo agendamento:', message)
            toast.success('📅 Novo agendamento criado!', {
              description: message.data?.client_name ? `Para: ${message.data.client_name}` : 'Novo agendamento'
            })
            // Invalidar cache de agendamentos
            invalidateRelatedQueries('appointment_created', message.data?.id)
          }

          else if (message.type === 'appointment_updated') {
            console.log('✏️ Agendamento atualizado:', message)
            toast.info('✏️ Agendamento atualizado!', {
              description: message.data?.client_name ? `${message.data.client_name} - ${message.data.status}` : 'Agendamento atualizado'
            })
            // Invalidar cache de agendamentos
            invalidateRelatedQueries('appointment_updated', message.data?.id)
          }

          else if (message.type === 'appointment_cancelled') {
            console.log('❌ Agendamento cancelado:', message)
            toast.error('❌ Agendamento cancelado', {
              description: message.data?.client_name ? `Cliente: ${message.data.client_name}` : 'Agendamento cancelado'
            })
            // Invalidar cache de agendamentos
            invalidateRelatedQueries('appointment_cancelled', message.data?.id)
          }

          else if (message.type === 'system_notification') {
            console.log('🔔 Notificação do sistema:', message)
            toast.info('🔔 Notificação', {
              description: message.data?.title || message.data?.message || 'Nova notificação'
            })
          }

        } catch (error) {
          console.error('❌ Error processing WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        console.log('🔌 WebSocket connection closed:', event.code, event.reason)

        // Tentar reconectar após delay
        if (enabled && !reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectTimeoutRef.current = null
            connect()
          }, 5000) // Reconectar após 5 segundos
        }
      }

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', {
          error,
          errorType: typeof error,
          errorKeys: error ? Object.keys(error) : 'null',
          url: wsUrl,
          readyState: ws.readyState,
          readyStateText: getReadyStateText(ws.readyState),
          timestamp: new Date().toISOString()
        })
        
        // Tentar obter mais informações do erro
        if (error && error.target) {
          console.error('❌ Error target:', error.target)
          console.error('❌ Error target readyState:', (error.target as WebSocket)?.readyState)
        }
      }

      // Timeout para conexão
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.warn('⏰ WebSocket connection timeout')
          ws.close()
        }
      }, 10000) // 10 segundos

      ws.onopen = () => {
        clearTimeout(connectionTimeout)
        console.log('✅ WebSocket connected for cache sync')
        console.log('🔍 Connection details:', {
          url: wsUrl,
          readyState: ws.readyState,
          timestamp: new Date().toISOString()
        })

        // Enviar mensagem de inicialização
        ws.send(JSON.stringify({
          type: 'subscribe',
          events: ['all'] // Se inscrever em todos os eventos
        }))
      }

      ws.onclose = () => {
        clearTimeout(connectionTimeout)
      }

      wsRef.current = ws

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error)
    }
  }, [enabled, wsUrl, invalidateRelatedQueries])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
      console.log('🔌 WebSocket disconnected manually')
    }
  }, [])

  // Conectar/desconectar baseado no enabled
  useEffect(() => {
    if (enabled) {
      connect()
    } else {
      disconnect()
    }

    return disconnect
  }, [enabled, connect, disconnect])

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    connect,
    disconnect
  }
}

/**
 * 🎯 Hook específico para operações de appointment com invalidação
 */
export function useAppointmentOperations() {
  const { invalidateRelatedQueries } = useApiWithInvalidation()

  const onAppointmentCreated = useCallback((appointmentId: number, context?: Record<string, any>) => {
    invalidateRelatedQueries('appointment_created', appointmentId, context)
  }, [invalidateRelatedQueries])

  const onAppointmentUpdated = useCallback((appointmentId: number, context?: Record<string, any>) => {
    invalidateRelatedQueries('appointment_updated', appointmentId, context)
  }, [invalidateRelatedQueries])

  const onAppointmentDeleted = useCallback((appointmentId: number, context?: Record<string, any>) => {
    invalidateRelatedQueries('appointment_deleted', appointmentId, context)
  }, [invalidateRelatedQueries])

  return {
    onAppointmentCreated,
    onAppointmentUpdated,
    onAppointmentDeleted
  }
}

/**
 * 🎯 Hook específico para operações de conversation com invalidação
 */
export function useConversationOperations() {
  const { invalidateRelatedQueries } = useApiWithInvalidation()

  const onConversationCreated = useCallback((conversationId: number, context?: Record<string, any>) => {
    invalidateRelatedQueries('conversation_created', conversationId, context)
  }, [invalidateRelatedQueries])

  const onConversationUpdated = useCallback((conversationId: number, context?: Record<string, any>) => {
    invalidateRelatedQueries('conversation_updated', conversationId, context)
  }, [invalidateRelatedQueries])

  return {
    onConversationCreated,
    onConversationUpdated
  }
}

/**
 * 🎯 Hook específico para operações de client com invalidação
 */
export function useClientOperations() {
  const { invalidateRelatedQueries } = useApiWithInvalidation()

  const onClientCreated = useCallback((clientId: number, context?: Record<string, any>) => {
    invalidateRelatedQueries('client_created', clientId, context)
  }, [invalidateRelatedQueries])

  const onClientUpdated = useCallback((clientId: number, context?: Record<string, any>) => {
    invalidateRelatedQueries('client_updated', clientId, context)
  }, [invalidateRelatedQueries])

  return {
    onClientCreated,
    onClientUpdated
  }
}
