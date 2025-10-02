import { useEffect, useRef, useState, useCallback } from 'react'
import { useToast } from '@/components/error-boundaries/ToastProvider'

export function useWebSocketRobust(url: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const mountedRef = useRef(true)
  const { showSuccess, showInfo, showWarning } = useToast()

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    // Se já existe uma conexão ativa, não criar nova
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('✅ useWebSocketRobust: Já conectado')
      setIsConnected(true)
      setError(null)
      return
    }

    // Se está conectando, aguardar
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      console.log('⏳ useWebSocketRobust: Conectando...')
      return
    }

    console.log('🔗 useWebSocketRobust: Iniciando conexão para:', url)
    
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        console.log('✅ useWebSocketRobust: Conectado!')
        setIsConnected(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        if (!mountedRef.current) return
        console.log('📥 useWebSocketRobust: Mensagem recebida:', event.data)
        
        try {
          const data = JSON.parse(event.data)
          console.log('🔍 useWebSocketRobust: Dados parseados:', data)
          console.log('🔍 useWebSocketRobust: Tipo da mensagem:', data.type)
          
          // Processar notificações
          if (data.type === 'notification') {
            const { event_type, data: notificationData } = data
            console.log('🔔 useWebSocketRobust: Processando notificação:', event_type, notificationData)
            
            // Mostrar toast baseado no tipo de evento
            switch (event_type) {
              case 'appointment_created':
                console.log('🎯 useWebSocketRobust: Mostrando toast de agendamento criado')
                showSuccess('📅 Novo Agendamento!', notificationData.message || 'Um novo agendamento foi criado')
                break
              case 'appointment_updated':
                showInfo('✏️ Agendamento Atualizado!', notificationData.message || 'Um agendamento foi atualizado')
                break
              case 'appointment_cancelled':
                showWarning('❌ Agendamento Cancelado!', notificationData.message || 'Um agendamento foi cancelado')
                break
              case 'system_notification':
                showInfo('🔔 Notificação do Sistema', notificationData.message || 'Nova notificação do sistema')
                break
              case 'client_created':
                showSuccess('👤 Novo Cliente!', notificationData.message || 'Um novo cliente foi cadastrado')
                break
              default:
                showInfo('🔔 Nova Notificação', notificationData.message || 'Nova notificação recebida')
            }
          } else {
            console.log('⚠️ useWebSocketRobust: Tipo de mensagem não é notificação:', data.type)
          }
        } catch (error) {
          console.error('❌ Erro ao processar mensagem WebSocket:', error)
        }
      }

      ws.onerror = (error) => {
        if (!mountedRef.current) return
        console.error('❌ useWebSocketRobust: Erro:', error)
        setError('Erro na conexão WebSocket')
        setIsConnected(false)
      }

      ws.onclose = (event) => {
        if (!mountedRef.current) return
        console.log('🔌 useWebSocketRobust: Fechado:', event.code, event.reason)
        setIsConnected(false)
        
        // Reconectar após 3 segundos se não foi fechado intencionalmente
        if (event.code !== 1000 && mountedRef.current) {
          console.log('🔄 useWebSocketRobust: Tentando reconectar em 3s...')
          setTimeout(() => {
            if (mountedRef.current) {
              connect()
            }
          }, 3000)
        }
      }

    } catch (err) {
      if (!mountedRef.current) return
      console.error('❌ useWebSocketRobust: Erro ao criar WebSocket:', err)
      setError('Erro ao criar WebSocket')
    }
  }, [url])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'Disconnect requested')
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  useEffect(() => {
    mountedRef.current = true
    connect()

    return () => {
      mountedRef.current = false
      disconnect()
    }
  }, [connect, disconnect])

  return { isConnected, error, reconnect: connect, disconnect }
}

