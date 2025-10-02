'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export default function WebSocketTestPage() {
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
  const [messages, setMessages] = useState<string[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)

  const connectWebSocket = () => {
    console.log('🚀 Iniciando teste WebSocket...')
    
    if (ws) {
      console.log('🔌 Fechando conexão anterior...')
      ws.close()
    }

    setWsStatus('connecting')
    setMessages(prev => [...prev, '🔄 Tentando conectar...'])

    try {
      // Testar diferentes endpoints
      const endpoints = [
        'ws://localhost:8000/ws',
        'ws://localhost:8000/ws'
      ]

      console.log('📋 Endpoints a testar:', endpoints)

      const testEndpoint = (url: string, index: number) => {
        console.log(`🔌 Testando endpoint ${index + 1}: ${url}`)
        setMessages(prev => [...prev, `🔌 Testando: ${url}`])
        
        const testWs = new WebSocket(url)
        
        // Timeout para evitar conexão infinita
        const timeout = setTimeout(() => {
          console.log(`⏰ Timeout de 5s para ${url}`)
          if (testWs.readyState === WebSocket.CONNECTING) {
            console.log(`❌ Timeout - fechando conexão para ${url}`)
            testWs.close()
            setMessages(prev => [...prev, `❌ Timeout em: ${url}`])
          }
        }, 5000)
        
        testWs.onopen = () => {
          console.log(`✅ WebSocket conectado: ${url}`)
          clearTimeout(timeout) // Limpar timeout
          setWsStatus('connected')
          setMessages(prev => [...prev, `✅ Conectado em: ${url}`])
          setWs(testWs)
          
          // Enviar heartbeat imediatamente após conectar
          setTimeout(() => {
            if (testWs.readyState === WebSocket.OPEN) {
              const heartbeat = JSON.stringify({
                type: 'heartbeat',
                timestamp: new Date().toISOString()
              })
              console.log('💓 Enviando heartbeat:', heartbeat)
              testWs.send(heartbeat)
            }
          }, 1000)
        }

        testWs.onmessage = (event) => {
          console.log(`📥 Mensagem recebida: ${event.data}`)
          setMessages(prev => [...prev, `📥 Mensagem: ${event.data}`])
        }

        testWs.onerror = (error) => {
          console.error(`❌ Erro WebSocket em ${url}:`, error)
          clearTimeout(timeout) // Limpar timeout
          setMessages(prev => [...prev, `❌ Erro em ${url}: ${error}`])
        }

        testWs.onclose = (event) => {
          console.log(`🔌 WebSocket fechado: ${url}, código: ${event.code}, motivo: ${event.reason}`)
          clearTimeout(timeout) // Limpar timeout
          setWsStatus('disconnected')
          setMessages(prev => [...prev, `🔌 Desconectado de: ${url} (código: ${event.code})`])
        }

        return testWs
      }

      // Testar endpoints sequencialmente com timeout
      let currentEndpoint = 0
      
      const testNextEndpoint = () => {
        if (currentEndpoint < endpoints.length) {
          console.log(`🔌 Testando endpoint ${currentEndpoint + 1}/${endpoints.length}`)
          const testWs = testEndpoint(endpoints[currentEndpoint], currentEndpoint)
          currentEndpoint++
          
          // Testar próximo endpoint após 3 segundos se este falhar
          setTimeout(() => {
            if (testWs.readyState === WebSocket.CLOSED || testWs.readyState === WebSocket.CONNECTING) {
              console.log('🔄 Endpoint falhou, testando próximo...')
              testNextEndpoint()
            }
          }, 3000)
        } else {
          console.log('❌ Todos os endpoints falharam')
          setMessages(prev => [...prev, '❌ Todos os endpoints falharam'])
        }
      }
      
      testNextEndpoint()

    } catch (error) {
      setWsStatus('error')
      setMessages(prev => [...prev, `❌ Erro: ${error}`])
    }
  }

  const sendMessage = () => {
    console.log('📤 Tentando enviar mensagem...')
    console.log('🔌 WebSocket status:', ws ? ws.readyState : 'null')
    
    if (ws && ws.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({
        type: 'test',
        message: 'Hello WebSocket!',
        timestamp: new Date().toISOString()
      })
      console.log('📤 Enviando mensagem:', message)
      ws.send(message)
      setMessages(prev => [...prev, `📤 Enviado: ${message}`])
    } else {
      console.log('❌ WebSocket não está conectado')
      setMessages(prev => [...prev, '❌ WebSocket não está conectado'])
    }
  }

  const disconnect = () => {
    if (ws) {
      ws.close()
      setWs(null)
      setWsStatus('disconnected')
    }
  }

  const clearMessages = () => {
    setMessages([])
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Teste de WebSocket</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Status da Conexão</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <span>Status:</span>
                <Badge variant={
                  wsStatus === 'connected' ? 'default' :
                  wsStatus === 'connecting' ? 'secondary' :
                  wsStatus === 'error' ? 'destructive' : 'outline'
                }>
                  {wsStatus}
                </Badge>
              </div>
              
              <div className="flex gap-2">
                <Button onClick={connectWebSocket} disabled={wsStatus === 'connecting'}>
                  Conectar
                </Button>
                <Button onClick={sendMessage} disabled={wsStatus !== 'connected'}>
                  Enviar Mensagem
                </Button>
                <Button onClick={disconnect} variant="outline">
                  Desconectar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Mensagens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span>Log de mensagens:</span>
                <Button onClick={clearMessages} variant="outline" size="sm">
                  Limpar
                </Button>
              </div>
              <div className="h-64 overflow-y-auto border rounded p-2 bg-gray-50">
                {messages.length === 0 ? (
                  <p className="text-gray-500">Nenhuma mensagem ainda...</p>
                ) : (
                  messages.map((msg, index) => (
                    <div key={index} className="text-sm mb-1">
                      {msg}
                    </div>
                  ))
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Informações do Teste</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p><strong>Backend:</strong> http://localhost:8000</p>
            <p><strong>Frontend:</strong> http://localhost:3000</p>
            <p><strong>Endpoints testados:</strong></p>
            <ul className="list-disc list-inside ml-4">
              <li>ws://localhost:8000/ws (novo endpoint simples)</li>
              <li>ws://localhost:8000/ws (endpoint principal)</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
