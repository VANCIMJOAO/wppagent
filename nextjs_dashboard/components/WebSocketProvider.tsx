/**
 * 🔗 WebSocket Provider para Cache Synchronization
 * ==============================================
 *
 * Provider React que gerencia conexão WebSocket global e
 * sincronização automática de cache em tempo real.
 *
 * Funcionalidades:
 * - Conexão WebSocket REAL com WebSocket API
 * - Auto-reconnection com exponential backoff
 * - Cache invalidation automática
 * - Status monitoring em tempo real
 * - Error handling robusto
 * - Cleanup correto de event listeners
 *
 * ✅ CORREÇÃO #27: Implementação real de WebSocket (não mais fake)
 * ✅ CORREÇÃO #28: Debug component com tree-shaking + logs condicionais
 * 
 * Autor: Claude AI
 * Status: Infraestrutura crítica para real-time updates
 */

'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { debugLog } from '@/lib/debug'
// import { useWebSocketCacheSync } from '../hooks/useApiWithInvalidation' // Hook removido na consolidação

// ===== TYPES =====

export interface WebSocketContextType {
  isConnected: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastMessage: any | null
  reconnectCount: number
  connect: () => void
  disconnect: () => void
}

export interface WebSocketProviderProps {
  children: ReactNode
  wsUrl?: string
  autoConnect?: boolean
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

// ===== CONTEXT =====

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}

// ===== PROVIDER COMPONENT =====

export function WebSocketCacheSyncProvider({
  children,
  wsUrl = 'ws://localhost:8000/ws', // ✅ URL padrão do WebSocket
  autoConnect = true,
  reconnectInterval = 5000,
  maxReconnectAttempts = 10
}: WebSocketProviderProps) {
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any | null>(null)
  const [reconnectCount, setReconnectCount] = useState(0)
  const [shouldConnect, setShouldConnect] = useState(autoConnect)
  
  // Refs para gerenciar conexão
  const wsRef = useRef<WebSocket | null>(null)
  const mountedRef = useRef(true)
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null)
  
  // Query client para invalidar cache
  const queryClient = useQueryClient()

  // ✅ CORREÇÃO #27: Implementar conexão WebSocket REAL
  const connect = useCallback(() => {
    if (!mountedRef.current) return

    // Se já existe uma conexão ativa, não criar nova
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      debugLog.info('✅ WebSocketProvider: Já conectado')
      setIsConnected(true)
      setConnectionStatus('connected')
      return
    }

    // Se está conectando, aguardar
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      debugLog.info('⏳ WebSocketProvider: Conectando...')
      return
    }

    debugLog.info(`🔗 WebSocketProvider: Conectando a ${wsUrl}...`)
    setConnectionStatus('connecting')
    
    try {
      const ws = new WebSocket(wsUrl)
      
      // 📡 Handler: Conexão aberta
      const handleOpen = () => {
        if (!mountedRef.current) return
        debugLog.success('✅ WebSocketProvider: Conectado com sucesso!')
        setIsConnected(true)
        setConnectionStatus('connected')
        setReconnectCount(0)
      }

      // 📨 Handler: Mensagem recebida
      const handleMessage = (event: MessageEvent) => {
        if (!mountedRef.current) return
        debugLog.info('📥 WebSocketProvider: Mensagem recebida:', event.data)
        
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          
          // Invalidar cache baseado no tipo de mensagem
          if (data.type === 'notification') {
            const { event_type } = data
            debugLog.info(`🔔 WebSocketProvider: Notificação recebida - ${event_type}`)
            
            // Invalidar queries relevantes
            switch (event_type) {
              case 'appointment_created':
              case 'appointment_updated':
              case 'appointment_cancelled':
                queryClient.invalidateQueries({ queryKey: ['appointments'] })
                debugLog.info('♻️ Cache de agendamentos invalidado')
                break
              case 'client_created':
              case 'client_updated':
                queryClient.invalidateQueries({ queryKey: ['clients'] })
                debugLog.info('♻️ Cache de clientes invalidado')
                break
              case 'message_received':
                queryClient.invalidateQueries({ queryKey: ['conversations'] })
                debugLog.info('♻️ Cache de conversas invalidado')
                break
              case 'stats_updated':
                queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
                debugLog.info('♻️ Cache de estatísticas invalidado')
                break
              default:
                debugLog.info(`⚠️ Tipo de evento desconhecido: ${event_type}`)
            }
          }
        } catch (error) {
          debugLog.error('❌ Erro ao processar mensagem WebSocket:', error)
        }
      }

      // ❌ Handler: Erro de conexão
      const handleError = (error: Event) => {
        if (!mountedRef.current) return
        debugLog.error('❌ WebSocketProvider: Erro na conexão:', error)
        setConnectionStatus('error')
        setIsConnected(false)
      }

      // 🔌 Handler: Conexão fechada
      const handleClose = (event: CloseEvent) => {
        if (!mountedRef.current) return
        debugLog.info(`🔌 WebSocketProvider: Conexão fechada (code: ${event.code}, reason: ${event.reason})`)
        setIsConnected(false)
        
        // Remover listeners
        ws.removeEventListener('open', handleOpen)
        ws.removeEventListener('message', handleMessage)
        ws.removeEventListener('error', handleError)
        ws.removeEventListener('close', handleClose)
        
        // Auto-reconnect se não foi fechado intencionalmente
        if (event.code !== 1000 && shouldConnect && reconnectCount < maxReconnectAttempts && mountedRef.current) {
          const delay = Math.min(reconnectInterval * Math.pow(2, reconnectCount), 30000) // Exponential backoff, max 30s
          debugLog.info(`🔄 WebSocketProvider: Reconectando em ${delay}ms (tentativa ${reconnectCount + 1}/${maxReconnectAttempts})`)
          setConnectionStatus('connecting')
          
          reconnectTimerRef.current = setTimeout(() => {
            if (mountedRef.current && shouldConnect) {
              setReconnectCount(prev => prev + 1)
              connect()
            }
          }, delay)
        } else if (reconnectCount >= maxReconnectAttempts) {
          debugLog.error('❌ WebSocketProvider: Máximo de tentativas de reconexão atingido')
          setConnectionStatus('error')
          setShouldConnect(false)
        } else {
          setConnectionStatus('disconnected')
        }
      }

      // Registrar event listeners
      ws.addEventListener('open', handleOpen)
      ws.addEventListener('message', handleMessage)
      ws.addEventListener('error', handleError)
      ws.addEventListener('close', handleClose)
      
      wsRef.current = ws

    } catch (err) {
      if (!mountedRef.current) return
      debugLog.error('❌ WebSocketProvider: Erro ao criar WebSocket:', err)
      setConnectionStatus('error')
      setIsConnected(false)
    }
  }, [wsUrl, reconnectInterval, maxReconnectAttempts, shouldConnect, reconnectCount, queryClient])

  // ✅ CORREÇÃO #27: Implementar disconnect REAL
  const disconnect = useCallback(() => {
    debugLog.info('🔌 WebSocketProvider: Desconectando...')
    setShouldConnect(false)
    
    // Limpar timer de reconexão
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    
    // Fechar conexão WebSocket
    if (wsRef.current) {
      wsRef.current.close(1000, 'Disconnect requested')
      wsRef.current = null
    }
    
    setIsConnected(false)
    setConnectionStatus('disconnected')
    setReconnectCount(0)
  }, [])

  // Funções de controle públicas
  const handleConnect = useCallback(() => {
    debugLog.info('🔗 WebSocketProvider: Solicitação de conexão')
    setShouldConnect(true)
    setReconnectCount(0)
    connect()
  }, [connect])

  const handleDisconnect = useCallback(() => {
    debugLog.info('🔌 WebSocketProvider: Solicitação de desconexão')
    disconnect()
  }, [disconnect])

  // ✅ Effect para auto-connect e cleanup
  useEffect(() => {
    mountedRef.current = true
    
    // Auto-connect se habilitado
    if (autoConnect && shouldConnect) {
      debugLog.info('🚀 WebSocketProvider: Auto-connect habilitado')
      connect()
    }

    // Cleanup ao desmontar
    return () => {
      debugLog.info('🧹 WebSocketProvider: Limpando recursos...')
      mountedRef.current = false
      
      // Limpar timer de reconexão
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      
      // Fechar conexão WebSocket
      if (wsRef.current) {
        // Remover handlers para evitar reconexão
        const ws = wsRef.current
        ws.onopen = null
        ws.onmessage = null
        ws.onerror = null
        ws.onclose = null
        
        ws.close(1000, 'Component unmounting')
        wsRef.current = null
      }
      
      setIsConnected(false)
      setConnectionStatus('disconnected')
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  // Apenas uma vez no mount - connect é estável via useCallback

  // Context value
  const contextValue: WebSocketContextType = {
    isConnected,
    connectionStatus,
    lastMessage,
    reconnectCount,
    connect: handleConnect,
    disconnect: handleDisconnect
  }

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  )
}

// ===== STATUS COMPONENT =====

/**
 * 📡 Componente para mostrar status da conexão WebSocket
 */
export function WebSocketStatus({ className = '' }: { className?: string }) {
  const { isConnected, connectionStatus, reconnectCount } = useWebSocket()

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-500'
      case 'connecting':
        return 'text-yellow-500'
      case 'disconnected':
        return 'text-gray-500'
      case 'error':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return '🟢'
      case 'connecting':
        return '🟡'
      case 'disconnected':
        return '🔴'
      case 'error':
        return '❌'
      default:
        return '⚪'
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Conectado'
      case 'connecting':
        return `Conectando${reconnectCount > 0 ? ` (${reconnectCount})` : ''}...`
      case 'disconnected':
        return 'Desconectado'
      case 'error':
        return 'Erro de conexão'
      default:
        return 'Desconhecido'
    }
  }

  return (
    <div className={`flex items-center gap-2 text-sm ${className}`}>
      <span>{getStatusIcon()}</span>
      <span className={getStatusColor()}>
        {getStatusText()}
      </span>
    </div>
  )
}

// ===== HOOKS UTILITIES =====

/**
 * 🔧 Hook para controlar conexão WebSocket
 */
export function useWebSocketControl() {
  const { connect, disconnect, isConnected, connectionStatus } = useWebSocket()

  const toggleConnection = () => {
    if (isConnected) {
      disconnect()
    } else {
      connect()
    }
  }

  return {
    connect,
    disconnect,
    toggleConnection,
    isConnected,
    connectionStatus
  }
}

/**
 * 📊 Hook para monitorar atividade WebSocket
 */
export function useWebSocketActivity() {
  const { isConnected, connectionStatus, reconnectCount, lastMessage } = useWebSocket()
  const [messageCount, setMessageCount] = useState(0)
  const [lastActivity, setLastActivity] = useState<Date | null>(null)

  // Contar mensagens recebidas
  useEffect(() => {
    if (lastMessage) {
      setMessageCount(prev => prev + 1)
      setLastActivity(new Date())
    }
  }, [lastMessage])

  // Reset contador quando conectar
  useEffect(() => {
    if (isConnected) {
      setMessageCount(0)
    }
  }, [isConnected])

  return {
    messageCount,
    lastActivity,
    isActive: isConnected && connectionStatus === 'connected',
    reconnectAttempts: reconnectCount
  }
}

// ===== DEBUG COMPONENT =====

/**
 * 🐛 Componente de debug para desenvolvimento
 * 
 * ✅ CORREÇÃO #28: Tree-shaking automático com process.env.NODE_ENV
 * - Em produção (NODE_ENV=production), todo este código é REMOVIDO do bundle
 * - Webpack/Next.js automaticamente elimina código dentro de if (false)
 * - Zero overhead em produção (nem código, nem runtime checks)
 */
export function WebSocketDebugPanel({ className = '' }: { className?: string }) {
  // ✅ Tree-shaking: Este código é REMOVIDO completamente em produção
  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { isConnected, connectionStatus, reconnectCount } = useWebSocket()
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { messageCount, lastActivity } = useWebSocketActivity()

  return (
    <div className={`bg-gray-100 p-4 rounded-lg text-xs ${className}`}>
      <h3 className="font-bold mb-2">🐛 WebSocket Debug</h3>
      <div className="space-y-1">
        <div>Status: <span className="font-mono">{connectionStatus}</span></div>
        <div>Connected: <span className="font-mono">{isConnected ? 'Yes' : 'No'}</span></div>
        <div>Reconnects: <span className="font-mono">{reconnectCount}</span></div>
        <div>Messages: <span className="font-mono">{messageCount}</span></div>
        <div>Last Activity: <span className="font-mono">
          {lastActivity ? lastActivity.toLocaleTimeString() : 'None'}
        </span></div>
      </div>
    </div>
  )
}
