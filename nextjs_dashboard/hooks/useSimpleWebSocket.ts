import { useEffect, useRef, useState } from 'react'

export function useSimpleWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const connectingRef = useRef(false)

  useEffect(() => {
    // Evitar múltiplas conexões simultâneas
    if (connectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING)) {
      console.log('⏳ useSimpleWebSocket: Conexão já em andamento, ignorando...')
      return
    }

    console.log('🔗 useSimpleWebSocket: Iniciando conexão para:', url)
    connectingRef.current = true
    
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('✅ useSimpleWebSocket: Conectado!')
        setIsConnected(true)
        setError(null)
        connectingRef.current = false
      }

      ws.onmessage = (event) => {
        console.log('📥 useSimpleWebSocket: Mensagem recebida:', event.data)
      }

      ws.onerror = (error) => {
        console.error('❌ useSimpleWebSocket: Erro:', error)
        setError('Erro na conexão WebSocket')
        setIsConnected(false)
        connectingRef.current = false
      }

      ws.onclose = (event) => {
        console.log('🔌 useSimpleWebSocket: Fechado:', event.code, event.reason)
        setIsConnected(false)
        connectingRef.current = false
      }

      return () => {
        console.log('🧹 useSimpleWebSocket: Limpando conexão')
        connectingRef.current = false
        if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
          wsRef.current.close()
        }
      }

    } catch (err) {
      console.error('❌ useSimpleWebSocket: Erro ao criar WebSocket:', err)
      setError('Erro ao criar WebSocket')
      connectingRef.current = false
    }
  }, [url])

  return { isConnected, error }
}
