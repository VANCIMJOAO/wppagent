// hooks/useWebSocket.ts
import { useEffect, useRef, useCallback, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { authService } from '@/lib/auth-service'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
  user_id?: string
}

type WebSocketEventHandler = (data: any) => void

interface UseWebSocketOptions {
  subscriptions?: string[]
  autoReconnect?: boolean
  heartbeatInterval?: number
  reconnectDelay?: number
}

interface ConnectionStats {
  connected: boolean
  connectionTime?: Date
  lastHeartbeat?: Date
  reconnectCount: number
  subscriptions: string[]
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { 
    subscriptions = ['dashboard', 'appointments', 'conversations'],
    autoReconnect = true,
    heartbeatInterval = 30000, // 30 seconds
    reconnectDelay = 5000 // 5 seconds
  } = options
  
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  
  // Get token from authService
  const getToken = useCallback(() => {
    return authService.getAccessToken()
  }, [])
  
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStats, setConnectionStats] = useState<ConnectionStats>({
    connected: false,
    reconnectCount: 0,
    subscriptions: []
  })
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const eventHandlersRef = useRef<Map<string, Set<WebSocketEventHandler>>>(new Map())
  const reconnectCountRef = useRef(0)
  
  // Event handler registration
  const subscribe = useCallback((eventType: string, handler: WebSocketEventHandler) => {
    if (!eventHandlersRef.current.has(eventType)) {
      eventHandlersRef.current.set(eventType, new Set())
    }
    eventHandlersRef.current.get(eventType)!.add(handler)
    
    // Return unsubscribe function
    return () => {
      eventHandlersRef.current.get(eventType)?.delete(handler)
    }
  }, [])
  
  const handleMessage = useCallback((message: WebSocketMessage) => {
    const handlers = eventHandlersRef.current.get(message.type)
    
    // Built-in handlers for automatic cache management
    switch (message.type) {
      case 'connection_status':
        if (message.data.connected) {
          setConnectionStats(prev => ({
            ...prev,
            connected: true,
            connectionTime: new Date(),
            subscriptions: message.data.subscriptions || prev.subscriptions
          }))
        }
        break
        
      case 'heartbeat_response':
        setConnectionStats(prev => ({
          ...prev,
          lastHeartbeat: new Date()
        }))
        break
        
      case 'dashboard_stats_update':
        if (message.data.stats) {
          // Update React Query cache with fresh stats
          queryClient.setQueryData(['dashboard-stats'], message.data.stats)
          console.log('📊 Dashboard stats updated via WebSocket', message.data.stats)
        }
        if (message.data.metric && message.data.increment) {
          // Increment specific metric
          queryClient.setQueryData(['dashboard-stats'], (old: any) => {
            const newStats = { ...old }
            if (newStats[message.data.metric] !== undefined) {
              newStats[message.data.metric] += message.data.increment
            }
            return newStats
          })
        }
        break
        
      case 'appointment_created':
        // Invalidate appointments list and dashboard stats
        queryClient.invalidateQueries({ queryKey: ['appointments'] })
        queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
        
        // Show success notification
        if (message.data.appointment && message.data.notification) {
          toast.success(message.data.notification.title, {
            description: message.data.notification.body
          })
        } else {
          toast.success(`Novo agendamento: ${message.data.appointment?.client_name || 'Cliente'}`)
        }
        break
        
      case 'appointment_updated':
        // Invalidate appointments list and specific appointment
        queryClient.invalidateQueries({ queryKey: ['appointments'] })
        if (message.data.appointment_id) {
          queryClient.invalidateQueries({ 
            queryKey: ['appointment-detail', message.data.appointment_id] 
          })
        }
        
        // Show update notification
        if (message.data.notification) {
          toast.info(message.data.notification.title, {
            description: message.data.notification.body
          })
        } else {
          toast.info('Agendamento atualizado')
        }
        break
        
      case 'appointment_cancelled':
        queryClient.invalidateQueries({ queryKey: ['appointments'] })
        queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
        
        toast.warning('Agendamento cancelado', {
          description: message.data.client_name || 'Um agendamento foi cancelado'
        })
        break
        
      case 'appointment_confirmed':
        queryClient.invalidateQueries({ queryKey: ['appointments'] })
        queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
        
        toast.success('Agendamento confirmado', {
          description: message.data.client_name || 'Um agendamento foi confirmado'
        })
        break
        
      case 'new_message':
        // Update conversations
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
        if (message.data.conversation_id) {
          queryClient.invalidateQueries({ 
            queryKey: ['conversation-messages', message.data.conversation_id] 
          })
        }
        
        toast.info(`Nova mensagem`, {
          description: `De: ${message.data.sender_name || 'Cliente'}`
        })
        break
        
      case 'conversation_started':
        queryClient.invalidateQueries({ queryKey: ['conversations'] })
        queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
        
        toast.info('Nova conversa iniciada', {
          description: message.data.client_name || 'Um cliente iniciou uma conversa'
        })
        break
        
      case 'client_created':
        queryClient.invalidateQueries({ queryKey: ['clients'] })
        queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
        
        toast.success('Novo cliente cadastrado', {
          description: message.data.client_name || 'Um novo cliente foi cadastrado'
        })
        break
        
      case 'whatsapp_status_change':
        // Update system status
        const status = message.data.status
        if (status === 'disconnected') {
          toast.error('WhatsApp desconectado!', {
            description: 'Verifique a conexão do WhatsApp'
          })
        } else if (status === 'connected') {
          toast.success('WhatsApp reconectado!', {
            description: 'A conexão foi restabelecida'
          })
        } else if (status === 'qr_code') {
          toast.warning('QR Code necessário', {
            description: 'Escaneie o QR Code para conectar o WhatsApp'
          })
        }
        break
        
      case 'system_alert':
        // Handle system alerts
        const alertType = message.data.alert_type || 'info'
        const alertMessage = message.data.message || 'Alerta do sistema'
        
        switch (alertType) {
          case 'error':
            toast.error('Erro do Sistema', { description: alertMessage })
            break
          case 'warning':
            toast.warning('Aviso do Sistema', { description: alertMessage })
            break
          default:
            toast.info('Sistema', { description: alertMessage })
        }
        break
        
      case 'cache_invalidated':
        // Handle cache invalidation events
        if (message.data.patterns) {
          message.data.patterns.forEach((pattern: string) => {
            if (pattern.includes('appointments')) {
              queryClient.invalidateQueries({ queryKey: ['appointments'] })
            }
            if (pattern.includes('dashboard')) {
              queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
            }
            if (pattern.includes('conversations')) {
              queryClient.invalidateQueries({ queryKey: ['conversations'] })
            }
            if (pattern.includes('clients')) {
              queryClient.invalidateQueries({ queryKey: ['clients'] })
            }
          })
          console.log('🗂️ Cache invalidated via WebSocket:', message.data.patterns)
        }
        break
        
      case 'analytics_update':
        // Handle analytics updates
        if (message.data.report_type) {
          queryClient.invalidateQueries({ 
            queryKey: ['analytics', message.data.report_type] 
          })
        }
        queryClient.invalidateQueries({ queryKey: ['analytics-summary'] })
        break
    }
    
    // Call custom handlers
    handlers?.forEach(handler => {
      try {
        handler(message.data)
      } catch (error) {
        console.error('Error in WebSocket handler:', error)
      }
    })
  }, [queryClient])
  
  const connect = useCallback(() => {
    const token = getToken()
    
    if (!token) {
      console.log('🔐 No token available for WebSocket connection')
      return
    }
    
    const subscriptionsParam = subscriptions.join(',')
    const wsUrl = `${process.env.NODE_ENV === 'development' ? 'ws://localhost:8000' : 'wss://wppagent-production.up.railway.app'}/ws?token=${token}&subscriptions=${subscriptionsParam}`
    
    try {
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = () => {
        console.log('✅ WebSocket connected')
        setIsConnected(true)
        reconnectCountRef.current = 0
        
        setConnectionStats(prev => ({
          ...prev,
          connected: true,
          connectionTime: new Date(),
          subscriptions: subscriptions
        }))
        
        // Start heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
        }
        
        heartbeatIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'heartbeat',
              timestamp: new Date().toISOString()
            }))
          }
        }, heartbeatInterval)
        
        // Show connection notification only after reconnection
        if (reconnectCountRef.current > 0) {
          toast.success('Conectado', {
            description: 'Conexão em tempo real restabelecida'
          })
        }
      }
      
      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      wsRef.current.onclose = (event) => {
        console.log('❌ WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        
        setConnectionStats(prev => ({
          ...prev,
          connected: false,
          reconnectCount: reconnectCountRef.current
        }))
        
        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
          heartbeatIntervalRef.current = null
        }
        
        // Attempt reconnect if enabled and not a normal closure
        if (autoReconnect && event.code !== 1000) {
          reconnectCountRef.current++
          const delay = Math.min(reconnectDelay * Math.pow(2, reconnectCountRef.current - 1), 30000)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`🔄 Attempting WebSocket reconnection (attempt ${reconnectCountRef.current})...`)
            connect()
          }, delay)
          
          // Show reconnection notification after first disconnect
          if (reconnectCountRef.current === 1) {
            toast.warning('Conexão perdida', {
              description: 'Tentando reconectar...'
            })
          }
        }
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      toast.error('Erro de conexão', {
        description: 'Não foi possível conectar ao servidor'
      })
    }
  }, [getToken, subscriptions, autoReconnect, heartbeatInterval, reconnectDelay, handleMessage])
  
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
    
    reconnectCountRef.current = 0
  }, [])
  
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    }
    console.warn('WebSocket not connected, cannot send message:', message)
    return false
  }, [])
  
  const requestStats = useCallback(() => {
    return sendMessage({ type: 'request_stats' })
  }, [sendMessage])
  
  const updateSubscriptions = useCallback((newSubscriptions: string[]) => {
    return sendMessage({ 
      type: 'subscribe', 
      topics: newSubscriptions 
    })
  }, [sendMessage])
  
  // Connect on mount, disconnect on unmount
  useEffect(() => {
    if (isAuthenticated && getToken()) {
      connect()
    }
    
    return () => {
      disconnect()
    }
  }, [connect, disconnect, isAuthenticated, getToken])
  
  return {
    isConnected,
    connectionStats,
    subscribe,
    sendMessage,
    requestStats,
    updateSubscriptions,
    connect,
    disconnect
  }
}

// Specialized hooks for specific use cases
export function useDashboardWebSocket() {
  const { subscribe, isConnected, connectionStats, requestStats } = useWebSocket({
    subscriptions: ['dashboard', 'system', 'analytics']
  })
  
  const [dashboardStats, setDashboardStats] = useState<any>(null)
  const [systemAlerts, setSystemAlerts] = useState<any[]>([])
  const [analyticsUpdates, setAnalyticsUpdates] = useState<any[]>([])
  
  useEffect(() => {
    const unsubStats = subscribe('dashboard_stats_update', (data) => {
      if (data.stats) {
        setDashboardStats(data.stats)
      }
    })
    
    const unsubAlerts = subscribe('system_alert', (data) => {
      setSystemAlerts(prev => [
        { ...data, timestamp: Date.now() },
        ...prev.slice(0, 9)
      ]) // Keep last 10 alerts
    })
    
    const unsubAnalytics = subscribe('analytics_update', (data) => {
      setAnalyticsUpdates(prev => [
        { ...data, timestamp: Date.now() },
        ...prev.slice(0, 19)
      ]) // Keep last 20 updates
    })
    
    // Request fresh stats on connection
    if (isConnected) {
      requestStats()
    }
    
    return () => {
      unsubStats()
      unsubAlerts()
      unsubAnalytics()
    }
  }, [subscribe, isConnected, requestStats])
  
  return { 
    dashboardStats, 
    systemAlerts, 
    analyticsUpdates,
    isConnected, 
    connectionStats,
    requestStats
  }
}

export function useAppointmentsWebSocket() {
  const { subscribe, isConnected, connectionStats } = useWebSocket({
    subscriptions: ['appointments', 'dashboard']
  })
  
  const [recentActivity, setRecentActivity] = useState<any[]>([])
  const [appointmentCounts, setAppointmentCounts] = useState({
    created: 0,
    updated: 0,
    confirmed: 0,
    cancelled: 0
  })
  
  useEffect(() => {
    const unsubCreate = subscribe('appointment_created', (data) => {
      setRecentActivity(prev => [
        { 
          type: 'created', 
          ...data, 
          timestamp: Date.now(),
          id: `created_${Date.now()}`
        },
        ...prev.slice(0, 19) // Keep last 20 activities
      ])
      
      setAppointmentCounts(prev => ({
        ...prev,
        created: prev.created + 1
      }))
    })
    
    const unsubUpdate = subscribe('appointment_updated', (data) => {
      setRecentActivity(prev => [
        { 
          type: 'updated', 
          ...data, 
          timestamp: Date.now(),
          id: `updated_${Date.now()}`
        },
        ...prev.slice(0, 19)
      ])
      
      setAppointmentCounts(prev => ({
        ...prev,
        updated: prev.updated + 1
      }))
    })
    
    const unsubConfirm = subscribe('appointment_confirmed', (data) => {
      setRecentActivity(prev => [
        { 
          type: 'confirmed', 
          ...data, 
          timestamp: Date.now(),
          id: `confirmed_${Date.now()}`
        },
        ...prev.slice(0, 19)
      ])
      
      setAppointmentCounts(prev => ({
        ...prev,
        confirmed: prev.confirmed + 1
      }))
    })
    
    const unsubCancel = subscribe('appointment_cancelled', (data) => {
      setRecentActivity(prev => [
        { 
          type: 'cancelled', 
          ...data, 
          timestamp: Date.now(),
          id: `cancelled_${Date.now()}`
        },
        ...prev.slice(0, 19)
      ])
      
      setAppointmentCounts(prev => ({
        ...prev,
        cancelled: prev.cancelled + 1
      }))
    })
    
    return () => {
      unsubCreate()
      unsubUpdate()
      unsubConfirm()
      unsubCancel()
    }
  }, [subscribe])
  
  const clearActivity = useCallback(() => {
    setRecentActivity([])
    setAppointmentCounts({
      created: 0,
      updated: 0,
      confirmed: 0,
      cancelled: 0
    })
  }, [])
  
  return { 
    recentActivity, 
    appointmentCounts,
    clearActivity,
    isConnected, 
    connectionStats 
  }
}

export function useConversationsWebSocket() {
  const { subscribe, isConnected, connectionStats } = useWebSocket({
    subscriptions: ['conversations']
  })
  
  const [newMessages, setNewMessages] = useState<any[]>([])
  const [conversationUpdates, setConversationUpdates] = useState<any[]>([])
  
  useEffect(() => {
    const unsubMessages = subscribe('new_message', (data) => {
      setNewMessages(prev => [
        { ...data, timestamp: Date.now() },
        ...prev.slice(0, 49) // Keep last 50 messages
      ])
    })
    
    const unsubConversations = subscribe('conversation_status_changed', (data) => {
      setConversationUpdates(prev => [
        { ...data, timestamp: Date.now() },
        ...prev.slice(0, 19) // Keep last 20 updates
      ])
    })
    
    return () => {
      unsubMessages()
      unsubConversations()
    }
  }, [subscribe])
  
  return { 
    newMessages, 
    conversationUpdates, 
    isConnected, 
    connectionStats 
  }
}
