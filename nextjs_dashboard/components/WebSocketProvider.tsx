/**
 * 🔗 WebSocket Provider para Cache Synchronization
 * ==============================================
 * 
 * Provider React que gerencia conexão WebSocket global e
 * sincronização automática de cache em tempo real.
 * 
 * Funcionalidades:
 * - Conexão WebSocket global
 * - Auto-reconnection
 * - Cache invalidation automática
 * - Status monitoring
 * - Error handling
 * 
 * Autor: Claude AI
 * Status: Infraestrutura crítica para real-time updates
 */

'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useWebSocketCacheSync } from '../hooks/useApiWithInvalidation'

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
  wsUrl,
  autoConnect = true,
  reconnectInterval = 5000,
  maxReconnectAttempts = 10
}: WebSocketProviderProps) {
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [lastMessage, setLastMessage] = useState<any | null>(null)
  const [reconnectCount, setReconnectCount] = useState(0)
  const [shouldConnect, setShouldConnect] = useState(autoConnect)
  
  // Usar o hook de WebSocket
  const { isConnected, connect, disconnect } = useWebSocketCacheSync(
    shouldConnect,
    wsUrl
  )
  
  // Monitorar status da conexão
  useEffect(() => {
    if (isConnected) {
      setConnectionStatus('connected')
      setReconnectCount(0) // Reset contador ao conectar
    } else if (shouldConnect) {
      if (reconnectCount < maxReconnectAttempts) {
        setConnectionStatus('connecting')
      } else {
        setConnectionStatus('error')
        setShouldConnect(false) // Para de tentar após max attempts
      }
    } else {
      setConnectionStatus('disconnected')
    }
  }, [isConnected, shouldConnect, reconnectCount, maxReconnectAttempts])
  
  // Auto-reconnect logic
  useEffect(() => {
    if (!isConnected && shouldConnect && reconnectCount < maxReconnectAttempts) {
      const timer = setTimeout(() => {
        console.log(`🔄 WebSocket reconnect attempt ${reconnectCount + 1}/${maxReconnectAttempts}`)
        setReconnectCount(prev => prev + 1)
        connect()
      }, reconnectInterval)
      
      return () => clearTimeout(timer)
    }
  }, [isConnected, shouldConnect, reconnectCount, maxReconnectAttempts, reconnectInterval, connect])
  
  // Funções de controle
  const handleConnect = () => {
    setShouldConnect(true)
    setReconnectCount(0)
    connect()
  }
  
  const handleDisconnect = () => {
    setShouldConnect(false)
    disconnect()
  }
  
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
 */
export function WebSocketDebugPanel({ className = '' }: { className?: string }) {
  const { isConnected, connectionStatus, reconnectCount } = useWebSocket()
  const { messageCount, lastActivity } = useWebSocketActivity()
  
  if (process.env.NODE_ENV !== 'development') {
    return null
  }
  
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
