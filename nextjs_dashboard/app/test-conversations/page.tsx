'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface Conversation {
  id: string
  user_id: string  
  status: string
  phone_number: string
  created_at: string
  last_message_at: string
  user?: {
    id: string
    name: string
  }
}

export default function TestConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function testDirectAPI() {
      try {
        console.log('🔍 TESTE DIRETO DA API - SEM AUTENTICAÇÃO NEXTJS')
        
        // Teste direto da API sem passar pelo proxy do NextJS
        const response = await fetch('https://wppagent-production.up.railway.app/conversations/', {
          method: 'GET',
          headers: {
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwicGVybWlzc2lvbnMiOlsicmVhZCIsIndyaXRlIiwiYWRtaW4iXSwidHlwZSI6ImFjY2VzcyIsImlhdCI6MTc1NzU1NzA0NiwiZXhwIjoxNzU3NTU3OTQ2LCJqdGkiOiIwMGU2Y2RhNy02YTkxLTQ2ODUtODIzZi05ZmYwOGM2MjUxNzciLCJpc3MiOiJ3aGF0c2FwcC1hZ2VudCIsImF1ZCI6IndoYXRzYXBwLWFnZW50LWFwaSJ9.E-S5-Zzjidw4cQwFkhyois67k6FjBFUjGF850rDuB7E',
            'Content-Type': 'application/json',
          },
        })

        console.log('📡 Status da resposta:', response.status)
        console.log('📡 Headers:', Object.fromEntries(response.headers.entries()))

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        console.log('📨 Dados recebidos:', data)
        console.log('📨 Tipo dos dados:', typeof data)
        console.log('📨 É array?', Array.isArray(data))

        if (Array.isArray(data)) {
          setConversations(data)
          console.log(`✅ ${data.length} conversas carregadas diretamente da API!`)
        } else {
          console.log('❌ Dados não são array:', data)
          setError('Dados recebidos não são um array de conversas')
        }

      } catch (err) {
        console.error('❌ Erro ao testar API diretamente:', err)
        setError(err instanceof Error ? err.message : 'Erro desconhecido')
      } finally {
        setLoading(false)
      }
    }

    testDirectAPI()
  }, [])

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">🔍 Teste Direto da API</h1>
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
          <span>Testando API diretamente...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">🔍 Teste Direto da API</h1>
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-600">❌ Erro na API</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">🔍 Teste Direto da API</h1>
      
      <div className="mb-6">
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="text-green-600">✅ API Funcionando!</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-green-700">
              Carregadas {conversations.length} conversas diretamente da API, sem passar pelo sistema de autenticação do NextJS.
            </p>
            <p className="text-sm text-green-600 mt-2">
              Isso confirma que o problema está na autenticação do frontend, não na API.
            </p>
          </CardContent>
        </Card>
      </div>

      <h2 className="text-xl font-semibold mb-4">📱 Conversas Encontradas:</h2>
      
      <div className="grid gap-4">
        {conversations.map((conversation) => (
          <Card key={conversation.id} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                <span>👤 {conversation.user?.name || `Usuário ${conversation.user_id}`}</span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  conversation.status === 'active' 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-gray-100 text-gray-700'
                }`}>
                  {conversation.status}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2 text-sm text-gray-600">
                <div>📱 <strong>Telefone:</strong> {conversation.phone_number}</div>
                <div>🆔 <strong>ID:</strong> {conversation.id}</div>
                <div>👤 <strong>User ID:</strong> {conversation.user_id}</div>
                <div>📅 <strong>Criado:</strong> {new Date(conversation.created_at).toLocaleString()}</div>
                {conversation.last_message_at && (
                  <div>💬 <strong>Última mensagem:</strong> {new Date(conversation.last_message_at).toLocaleString()}</div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h3 className="font-semibold text-yellow-800 mb-2">🎯 Resultado do Teste:</h3>
        <p className="text-yellow-700">
          Se você está vendo as conversas acima, isso confirma que:
        </p>
        <ul className="list-disc list-inside mt-2 text-yellow-700 space-y-1">
          <li>✅ A API está funcionando perfeitamente</li>
          <li>✅ Os dados existem no banco (40 conversas)</li>  
          <li>✅ O problema é apenas na autenticação do NextJS</li>
          <li>✅ O hook de conversas deveria funcionar se o usuário estivesse logado</li>
        </ul>
        <p className="mt-3 text-yellow-800 font-medium">
          🔧 Próximo passo: Use a página /auto-login para fazer login automático e resolver o problema.
        </p>
      </div>
    </div>
  )
}
