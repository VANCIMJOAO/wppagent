import { useEffect, useRef, useState, useCallback } from 'react'
import { useToast } from '@/components/shared/toast/ToastProvider-consolidated'
import { debugLog } from '@/lib/debug'

/**
 * Hook robusto para gerenciar conexão WebSocket
 * 
 * ✅ CORREÇÃO #21: Todos os logs são condicionais via debugLog
 * - console.log substituído por debugLog (15 ocorrências)
 * - Zero logs em produção (NODE_ENV=development apenas)
 * - Para produção, use sistema de monitoring (Sentry, DataDog)
 */
export function useWebSocketRobust(url: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const mountedRef = useRef(true)
  const { success: showSuccess, info: showInfo, warning: showWarning } = useToast()
  
  // ✅ CORREÇÃO #20: Usar refs para funções de toast (evitar mudanças de dependências)
  const toastRef = useRef({ showSuccess, showInfo, showWarning })
  
  // Atualizar refs quando funções mudarem
  useEffect(() => {
    toastRef.current = { showSuccess, showInfo, showWarning }
  }, [showSuccess, showInfo, showWarning])

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    // Se já existe uma conexão ativa, não criar nova
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      debugLog.info('✅ useWebSocketRobust: Já conectado')
      setIsConnected(true)
      setError(null)
      return
    }

    // Se está conectando, aguardar
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      debugLog.info('⏳ useWebSocketRobust: Conectando...')
      return
    }

    debugLog.info('🔗 useWebSocketRobust: Iniciando conexão para:', url)
    
    try {
      const ws = new WebSocket(url)
      
      // 🔧 FIX: Definir handlers como funções nomeadas para poder remover depois
      const handleOpen = () => {
        if (!mountedRef.current) return
        debugLog.success('✅ useWebSocketRobust: Conectado!')
        setIsConnected(true)
        setError(null)
      }

      const handleMessage = (event: MessageEvent) => {
        if (!mountedRef.current) return
        debugLog.info('📥 useWebSocketRobust: Mensagem recebida:', event.data)
        
        try {
          const data = JSON.parse(event.data)
          debugLog.info('🔍 useWebSocketRobust: Dados parseados:', data)
          debugLog.info('🔍 useWebSocketRobust: Tipo da mensagem:', data.type)
          
          // Processar notificações
          if (data.type === 'notification') {
            const { event_type, data: notificationData } = data
            debugLog.info(`🔔 useWebSocketRobust: Processando notificação: ${event_type}`, notificationData)
            
            // Mostrar toast baseado no tipo de evento
            switch (event_type) {
              case 'appointment_created':
                debugLog.info('🎯 useWebSocketRobust: Mostrando toast de agendamento criado')
                toastRef.current.showSuccess('📅 Novo Agendamento!', notificationData.message || 'Um novo agendamento foi criado')
                break
              case 'appointment_updated':
                toastRef.current.showInfo('✏️ Agendamento Atualizado!', notificationData.message || 'Um agendamento foi atualizado')
                break
              case 'appointment_cancelled':
                toastRef.current.showWarning('❌ Agendamento Cancelado!', notificationData.message || 'Um agendamento foi cancelado')
                break
              case 'system_notification':
                toastRef.current.showInfo('🔔 Notificação do Sistema', notificationData.message || 'Nova notificação do sistema')
                break
              case 'client_created':
                toastRef.current.showSuccess('👤 Novo Cliente!', notificationData.message || 'Um novo cliente foi cadastrado')
                break
              default:
                toastRef.current.showInfo('🔔 Nova Notificação', notificationData.message || 'Nova notificação recebida')
            }
          } else {
            debugLog.warn('⚠️ useWebSocketRobust: Tipo de mensagem não é notificação:', data.type)
          }
        } catch (error) {
          debugLog.error('❌ Erro ao processar mensagem WebSocket:', error)
        }
      }

      const handleError = (error: Event) => {
        if (!mountedRef.current) return
        debugLog.error('❌ useWebSocketRobust: Erro:', error)
        setError('Erro na conexão WebSocket')
        setIsConnected(false)
      }

      const handleClose = (event: CloseEvent) => {
        if (!mountedRef.current) return
        debugLog.info(`🔌 useWebSocketRobust: Fechado: code=${event.code} reason=${event.reason}`)
        setIsConnected(false)
        
        // 🔧 FIX: Remover todos os event listeners antes de reconectar
        ws.removeEventListener('open', handleOpen)
        ws.removeEventListener('message', handleMessage)
        ws.removeEventListener('error', handleError)
        ws.removeEventListener('close', handleClose)
        
        // Reconectar após 3 segundos se não foi fechado intencionalmente
        if (event.code !== 1000 && mountedRef.current) {
          debugLog.info('🔄 useWebSocketRobust: Tentando reconectar em 3s...')
          setTimeout(() => {
            if (mountedRef.current) {
              connect()
            }
          }, 3000)
        }
      }

      // 🔧 FIX: Usar addEventListener em vez de propriedades diretas
      // Isso permite remover os listeners depois
      ws.addEventListener('open', handleOpen)
      ws.addEventListener('message', handleMessage)
      ws.addEventListener('error', handleError)
      ws.addEventListener('close', handleClose)
      
      wsRef.current = ws

    } catch (err) {
      if (!mountedRef.current) return
      debugLog.error('❌ useWebSocketRobust: Erro ao criar WebSocket:', err)
      setError('Erro ao criar WebSocket')
    }
  }, [url]) // ✅ CORREÇÃO #20: Apenas url nas dependências (toast functions via ref)

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      // 🔧 FIX: Fechar conexão de forma limpa
      // O evento 'close' já vai remover os listeners via handleClose
      wsRef.current.close(1000, 'Disconnect requested')
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      // 🔧 FIX: Cleanup adequado
      mountedRef.current = false
      
      // Fechar conexão e limpar listeners
      if (wsRef.current) {
        // Se o WebSocket ainda existe, remover listeners manualmente
        // antes de fechar para evitar que handleClose tente reconectar
        const ws = wsRef.current
        
        // Criar dummy handlers para garantir que não há reconexão
        ws.onopen = null
        ws.onmessage = null
        ws.onerror = null
        ws.onclose = null
        
        ws.close(1000, 'Component unmounting')
        wsRef.current = null
      }
      
      setIsConnected(false)
    }
  }, [connect])

  return { isConnected, error, reconnect: connect, disconnect }
}

