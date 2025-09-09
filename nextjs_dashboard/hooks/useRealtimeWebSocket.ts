/**
 * 💬 Frontend Hook para WebSocket Real-Time
 * ==========================================
 *
 * Hook React customizado para integração WebSocket otimizada:
 * - Conexão automática com JWT
 * - Reconexão inteligente com backoff exponencial  
 * - Gerenciamento de estado robusto
 * - Integração React Query com cache
 * - TypeScript para type safety
 * - Callbacks especializados por evento
 */

import { useEffect, useRef, useState, useCallback, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'

// Simple toast replacement
const toast = {
    success: (message: string) => console.log('✅', message),
    error: (message: string) => console.error('❌', message)
}

// ============= TYPES & INTERFACES =============
export enum RealtimeEventType {
    // Chat & Messages
    NEW_MESSAGE = 'new_message',
    MESSAGE_SENT = 'message_sent',
    MESSAGE_DELIVERED = 'message_delivered',
    MESSAGE_READ = 'message_read',
    TYPING_START = 'typing_start',
    TYPING_STOP = 'typing_stop',
    CONVERSATION_UPDATED = 'conversation_updated',
    
    // Appointments
    APPOINTMENT_CREATED = 'appointment_created',
    APPOINTMENT_UPDATED = 'appointment_updated',
    APPOINTMENT_CANCELLED = 'appointment_cancelled',
    APPOINTMENT_CONFIRMED = 'appointment_confirmed',
    APPOINTMENT_REMINDER = 'appointment_reminder',
    
    // Users & Status
    USER_STATUS_CHANGED = 'user_status_changed',
    USER_ONLINE = 'user_online',
    USER_OFFLINE = 'user_offline',
    CLIENT_CREATED = 'client_created',
    CLIENT_UPDATED = 'client_updated',
    
    // Dashboard & Analytics
    DASHBOARD_STATS_UPDATE = 'dashboard_stats_update',
    KPI_UPDATE = 'kpi_update',
    ANALYTICS_UPDATE = 'analytics_update',
    METRIC_INCREMENT = 'metric_increment',
    
    // System
    WHATSAPP_STATUS_CHANGE = 'whatsapp_status_change',
    SYSTEM_ALERT = 'system_alert',
    SYSTEM_NOTIFICATION = 'system_notification',
    CONNECTION_STATUS = 'connection_status',
    HEARTBEAT = 'heartbeat',
    HEARTBEAT_RESPONSE = 'heartbeat_response',
    
    // Admin
    ADMIN_ALERT = 'admin_alert',
    CACHE_INVALIDATED = 'cache_invalidated',
    DATA_SYNC_REQUIRED = 'data_sync_required'
}

export enum ConnectionStatus {
    DISCONNECTED = 'disconnected',
    CONNECTING = 'connecting',
    CONNECTED = 'connected',
    AUTHENTICATED = 'authenticated',
    RECONNECTING = 'reconnecting',
    ERROR = 'error'
}

export interface WebSocketMessage {
    type: string
    data: Record<string, any>
    timestamp: string
    id: string
    room?: string
    target_user?: string
    source_user?: string
    priority?: number
    expires_at?: string
}

export interface WebSocketConfig {
    url?: string
    token?: string
    subscriptions?: string[]
    room?: string
    autoReconnect?: boolean
    maxReconnectAttempts?: number
    reconnectInterval?: number
    heartbeatInterval?: number
}

export interface WebSocketCallbacks {
    onMessage?: (message: WebSocketMessage) => void
    onConnect?: (event: Event) => void
    onDisconnect?: (event: CloseEvent) => void
    onError?: (event: Event) => void
    onReconnect?: (attempt: number) => void
    onTyping?: (data: any) => void
    onNewMessage?: (data: any) => void
    onAppointmentUpdate?: (data: any) => void
    onDashboardUpdate?: (data: any) => void
    onSystemAlert?: (data: any) => void
}

export interface WebSocketState {
    status: ConnectionStatus
    isConnected: boolean
    isReconnecting: boolean
    lastMessage: WebSocketMessage | null
    connectionId: string | null
    subscriptions: string[]
    error: string | null
    reconnectAttempts: number
    lastHeartbeat: Date | null
}

// ============= REALTIME WEBSOCKET HOOK =============
export function useRealtimeWebSocket(config: WebSocketConfig, callbacks?: WebSocketCallbacks) {
    const queryClient = useQueryClient()
    const wsRef = useRef<WebSocket | null>(null)
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
    const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null)
    const lastHeartbeatRef = useRef<Date | null>(null)
    
    // Default config values
    const defaultConfig = useMemo(() => ({
        url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
        autoReconnect: true,
        maxReconnectAttempts: 10,
        reconnectInterval: 1000,
        heartbeatInterval: 30000,
        subscriptions: [],
        ...config
    }), [config])
    
    // WebSocket state
    const [state, setState] = useState<WebSocketState>({
        status: ConnectionStatus.DISCONNECTED,
        isConnected: false,
        isReconnecting: false,
        lastMessage: null,
        connectionId: null,
        subscriptions: defaultConfig.subscriptions || [],
        error: null,
        reconnectAttempts: 0,
        lastHeartbeat: null
    })
    
    // Update status helper
    const updateStatus = useCallback((newStatus: ConnectionStatus, error?: string) => {
        setState(prev => ({
            ...prev,
            status: newStatus,
            isConnected: newStatus === ConnectionStatus.CONNECTED || newStatus === ConnectionStatus.AUTHENTICATED,
            isReconnecting: newStatus === ConnectionStatus.RECONNECTING,
            error: error || null
        }))
    }, [])
    
    // Build WebSocket URL with query parameters
    const buildWebSocketUrl = useCallback(() => {
        const baseUrl = defaultConfig.url
        const params = new URLSearchParams()
        
        if (defaultConfig.token) {
            params.append('token', defaultConfig.token)
        }
        
        if (defaultConfig.subscriptions && defaultConfig.subscriptions.length > 0) {
            params.append('subscriptions', defaultConfig.subscriptions.join(','))
        }
        
        if (defaultConfig.room) {
            params.append('room', defaultConfig.room)
        }
        
        return `${baseUrl}?${params.toString()}`
    }, [defaultConfig])
    
    // Send message to WebSocket
    const sendMessage = useCallback((type: string, data: Record<string, any> = {}) => {
        if (wsRef.current && state.isConnected) {
            try {
                const message = {
                    type,
                    data,
                    timestamp: new Date().toISOString(),
                    id: Math.random().toString(36).substr(2, 9)
                }
                wsRef.current.send(JSON.stringify(message))
                return true
            } catch (error) {
                console.error('❌ Erro ao enviar mensagem WebSocket:', error)
                return false
            }
        }
        return false
    }, [state.isConnected])
    
    // Heartbeat mechanism
    const startHeartbeat = useCallback(() => {
        if (heartbeatTimeoutRef.current) {
            clearInterval(heartbeatTimeoutRef.current)
        }
        
        heartbeatTimeoutRef.current = setInterval(() => {
            if (sendMessage('heartbeat')) {
                lastHeartbeatRef.current = new Date()
                setState(prev => ({ ...prev, lastHeartbeat: lastHeartbeatRef.current }))
            }
        }, defaultConfig.heartbeatInterval)
    }, [sendMessage, defaultConfig.heartbeatInterval])
    
    const stopHeartbeat = useCallback(() => {
        if (heartbeatTimeoutRef.current) {
            clearInterval(heartbeatTimeoutRef.current)
            heartbeatTimeoutRef.current = null
        }
    }, [])
    
    // Handle incoming messages
    const handleMessage = useCallback((event: MessageEvent) => {
        try {
            const message: WebSocketMessage = JSON.parse(event.data)
            
            setState(prev => ({ 
                ...prev, 
                lastMessage: message,
                error: null
            }))
            
            // Handle specific message types
            switch (message.type as RealtimeEventType) {
                case RealtimeEventType.CONNECTION_STATUS:
                    if (message.data.status === 'connected') {
                        updateStatus(ConnectionStatus.AUTHENTICATED)
                        setState(prev => ({ 
                            ...prev, 
                            connectionId: message.data.connection_id,
                            subscriptions: message.data.subscriptions || []
                        }))
                        startHeartbeat()
                    }
                    break
                
                case RealtimeEventType.HEARTBEAT_RESPONSE:
                    lastHeartbeatRef.current = new Date()
                    setState(prev => ({ ...prev, lastHeartbeat: lastHeartbeatRef.current }))
                    break
                
                case RealtimeEventType.NEW_MESSAGE:
                    // Invalidate messages cache
                    queryClient.invalidateQueries({ queryKey: ['messages'] })
                    queryClient.invalidateQueries({ queryKey: ['conversations'] })
                    
                    // Show notification
                    if (message.data.user_name && message.data.content) {
                        toast.success(`💬 Nova mensagem de ${message.data.user_name}`)
                    }
                    
                    callbacks?.onNewMessage?.(message.data)
                    break
                
                case RealtimeEventType.APPOINTMENT_CREATED:
                case RealtimeEventType.APPOINTMENT_UPDATED:
                case RealtimeEventType.APPOINTMENT_CANCELLED:
                case RealtimeEventType.APPOINTMENT_CONFIRMED:
                    // Invalidate appointments cache
                    queryClient.invalidateQueries({ queryKey: ['appointments'] })
                    queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] })
                    
                    // Show notification
                    const appointmentMsg = message.type === RealtimeEventType.APPOINTMENT_CREATED 
                        ? '📅 Novo agendamento criado'
                        : '📅 Agendamento atualizado'
                    toast.success(appointmentMsg)
                    
                    callbacks?.onAppointmentUpdate?.(message.data)
                    break
                
                case RealtimeEventType.DASHBOARD_STATS_UPDATE:
                case RealtimeEventType.KPI_UPDATE:
                case RealtimeEventType.ANALYTICS_UPDATE:
                    // Invalidate dashboard caches
                    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
                    queryClient.invalidateQueries({ queryKey: ['stats'] })
                    queryClient.invalidateQueries({ queryKey: ['kpis'] })
                    
                    callbacks?.onDashboardUpdate?.(message.data)
                    break
                
                case RealtimeEventType.TYPING_START:
                    callbacks?.onTyping?.({ ...message.data, typing: true })
                    break
                
                case RealtimeEventType.TYPING_STOP:
                    callbacks?.onTyping?.({ ...message.data, typing: false })
                    break
                
                case RealtimeEventType.SYSTEM_ALERT:
                case RealtimeEventType.SYSTEM_NOTIFICATION:
                    toast.error(`⚠️ ${message.data.message || 'Alerta do sistema'}`)
                    callbacks?.onSystemAlert?.(message.data)
                    break
                
                case RealtimeEventType.CACHE_INVALIDATED:
                    // Invalidate all relevant caches
                    queryClient.invalidateQueries()
                    break
                
                case RealtimeEventType.DATA_SYNC_REQUIRED:
                    // Force refetch all data
                    queryClient.refetchQueries()
                    break
                
                default:
                    console.log('🔄 Mensagem WebSocket recebida:', message.type, message.data)
            }
            
            // Call general message callback
            callbacks?.onMessage?.(message)
            
        } catch (error) {
            console.error('❌ Erro ao processar mensagem WebSocket:', error)
            setState(prev => ({ ...prev, error: 'Erro ao processar mensagem' }))
        }
    }, [callbacks, queryClient, updateStatus, startHeartbeat])
    
    // Connect to WebSocket
    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return // Already connected
        }
        
        try {
            updateStatus(ConnectionStatus.CONNECTING)
            
            const wsUrl = buildWebSocketUrl()
            console.log('🔌 Conectando WebSocket:', wsUrl)
            
            wsRef.current = new WebSocket(wsUrl)
            
            wsRef.current.onopen = (event) => {
                console.log('✅ WebSocket conectado')
                updateStatus(ConnectionStatus.CONNECTED)
                setState(prev => ({ ...prev, reconnectAttempts: 0 }))
                callbacks?.onConnect?.(event)
            }
            
            wsRef.current.onmessage = handleMessage
            
            wsRef.current.onclose = (event) => {
                console.log('🔌 WebSocket desconectado:', event.code, event.reason)
                updateStatus(ConnectionStatus.DISCONNECTED)
                stopHeartbeat()
                
                setState(prev => ({ 
                    ...prev, 
                    connectionId: null,
                    lastHeartbeat: null
                }))
                
                callbacks?.onDisconnect?.(event)
                
                // Auto reconnect
                if (defaultConfig.autoReconnect && 
                    state.reconnectAttempts < defaultConfig.maxReconnectAttempts &&
                    event.code !== 1000) { // Not normal closure
                    
                    const delay = Math.min(
                        defaultConfig.reconnectInterval * Math.pow(2, state.reconnectAttempts),
                        30000 // Max 30 seconds
                    )
                    
                    console.log(`🔄 Reconectando em ${delay}ms (tentativa ${state.reconnectAttempts + 1})`)
                    updateStatus(ConnectionStatus.RECONNECTING)
                    
                    reconnectTimeoutRef.current = setTimeout(() => {
                        setState(prev => ({ ...prev, reconnectAttempts: prev.reconnectAttempts + 1 }))
                        callbacks?.onReconnect?.(state.reconnectAttempts + 1)
                        connect()
                    }, delay)
                }
            }
            
            wsRef.current.onerror = (event) => {
                console.error('❌ Erro WebSocket:', event)
                updateStatus(ConnectionStatus.ERROR, 'Erro de conexão WebSocket')
                callbacks?.onError?.(event)
            }
            
        } catch (error) {
            console.error('❌ Erro ao conectar WebSocket:', error)
            updateStatus(ConnectionStatus.ERROR, 'Falha ao conectar')
        }
    }, [buildWebSocketUrl, callbacks, defaultConfig, handleMessage, state.reconnectAttempts, 
        stopHeartbeat, updateStatus])
    
    // Disconnect from WebSocket
    const disconnect = useCallback(() => {
        console.log('🔌 Desconectando WebSocket...')
        
        // Clear timeouts
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current)
            reconnectTimeoutRef.current = null
        }
        
        stopHeartbeat()
        
        // Close connection
        if (wsRef.current) {
            wsRef.current.close(1000, 'Manual disconnect')
            wsRef.current = null
        }
        
        updateStatus(ConnectionStatus.DISCONNECTED)
        setState(prev => ({ 
            ...prev, 
            connectionId: null,
            reconnectAttempts: 0,
            lastHeartbeat: null
        }))
    }, [stopHeartbeat, updateStatus])
    
    // Reconnect manually
    const reconnect = useCallback(() => {
        console.log('🔄 Reconexão manual iniciada...')
        disconnect()
        setTimeout(connect, 1000)
    }, [connect, disconnect])
    
    // Join room
    const joinRoom = useCallback((roomId: string) => {
        return sendMessage('join_room', { room: roomId })
    }, [sendMessage])
    
    // Leave room
    const leaveRoom = useCallback((roomId: string) => {
        return sendMessage('leave_room', { room: roomId })
    }, [sendMessage])
    
    // Subscribe to topic
    const subscribe = useCallback((subscription: string) => {
        return sendMessage('subscribe', { subscription })
    }, [sendMessage])
    
    // Unsubscribe from topic
    const unsubscribe = useCallback((subscription: string) => {
        return sendMessage('unsubscribe', { subscription })
    }, [sendMessage])
    
    // Send typing indicators
    const sendTypingStart = useCallback(() => {
        return sendMessage('typing_start')
    }, [sendMessage])
    
    const sendTypingStop = useCallback(() => {
        return sendMessage('typing_stop')
    }, [sendMessage])
    
    // Send chat message
    const sendChatMessage = useCallback((content: string, clientPhone?: string, conversationId?: number) => {
        return sendMessage('send_message', {
            content,
            client_phone: clientPhone,
            conversation_id: conversationId
        })
    }, [sendMessage])
    
    // Mark message as read
    const markMessageRead = useCallback((messageId: number) => {
        return sendMessage('mark_message_read', { message_id: messageId })
    }, [sendMessage])
    
    // Update appointment
    const updateAppointment = useCallback((appointmentId: number, updates: Record<string, any>) => {
        return sendMessage('update_appointment', {
            appointment_id: appointmentId,
            ...updates
        })
    }, [sendMessage])
    
    // Refresh dashboard data
    const refreshDashboard = useCallback(() => {
        return sendMessage('get_dashboard_data')
    }, [sendMessage])
    
    // Effect: Auto-connect when token is available
    useEffect(() => {
        if (defaultConfig.token) {
            connect()
        }
        
        return () => {
            disconnect()
        }
    }, [defaultConfig.token]) // Only reconnect when token changes
    
    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnect()
        }
    }, [disconnect])
    
    return {
        // State
        ...state,
        
        // Actions
        connect,
        disconnect,
        reconnect,
        sendMessage,
        joinRoom,
        leaveRoom,
        subscribe,
        unsubscribe,
        
        // Chat functions
        sendTypingStart,
        sendTypingStop,
        sendChatMessage,
        markMessageRead,
        
        // App functions  
        updateAppointment,
        refreshDashboard,
        
        // Config
        config: defaultConfig
    }
}

// ============= SPECIALIZED HOOKS =============

// Dashboard WebSocket hook
export function useDashboardWebSocket(token?: string) {
    return useRealtimeWebSocket(
        {
            token,
            subscriptions: ['dashboard', 'appointments', 'analytics'],
            room: 'dashboard'
        },
        {
            onDashboardUpdate: (data) => {
                console.log('📊 Dashboard atualizado:', data)
            },
            onConnect: () => {
                toast.success('📊 Dashboard conectado em tempo real')
            },
            onDisconnect: () => {
                toast.error('📊 Dashboard desconectado')
            }
        }
    )
}

// Messages/Chat WebSocket hook  
export function useMessagesWebSocket(token?: string, conversationId?: number) {
    const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set())
    
    const ws = useRealtimeWebSocket(
        {
            token,
            subscriptions: ['messages', 'conversations'],
            room: conversationId ? `conversation_${conversationId}` : 'messages'
        },
        {
            onNewMessage: (data) => {
                console.log('💬 Nova mensagem:', data)
                // Play notification sound
                if ('Notification' in window && Notification.permission === 'granted') {
                    new Notification(`Nova mensagem de ${data.user_name}`, {
                        body: data.content,
                        icon: '/icon-192x192.png'
                    })
                }
            },
            onTyping: (data) => {
                const userId = data.user_id
                if (data.typing) {
                    setTypingUsers(prev => new Set(prev).add(userId))
                } else {
                    setTypingUsers(prev => {
                        const newSet = new Set(prev)
                        newSet.delete(userId)
                        return newSet
                    })
                }
                
                // Clear typing after 5 seconds
                setTimeout(() => {
                    setTypingUsers(prev => {
                        const newSet = new Set(prev)
                        newSet.delete(userId)
                        return newSet
                    })
                }, 5000)
            },
            onConnect: () => {
                toast.success('💬 Chat conectado em tempo real')
            }
        }
    )
    
    return {
        ...ws,
        typingUsers: Array.from(typingUsers)
    }
}

// Appointments WebSocket hook
export function useAppointmentsWebSocket(token?: string) {
    return useRealtimeWebSocket(
        {
            token,
            subscriptions: ['appointments', 'dashboard'],
            room: 'appointments'
        },
        {
            onAppointmentUpdate: (data) => {
                console.log('📅 Agendamento atualizado:', data)
            },
            onConnect: () => {
                toast.success('📅 Agendamentos conectados em tempo real')
            }
        }
    )
}

// System monitoring WebSocket hook
export function useSystemWebSocket(token?: string) {
    return useRealtimeWebSocket(
        {
            token,
            subscriptions: ['system', 'admin'],
            room: 'system'
        },
        {
            onSystemAlert: (data) => {
                console.log('⚠️ Alerta do sistema:', data)
            },
            onConnect: () => {
                console.log('🔧 Sistema conectado em tempo real')
            }
        }
    )
}

export default useRealtimeWebSocket
