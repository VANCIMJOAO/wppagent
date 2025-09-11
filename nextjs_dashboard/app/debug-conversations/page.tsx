'use client'

import { useEffect, useState } from 'react'

export default function TestDirectConversations() {
  const [conversations, setConversations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    async function fetchData() {
      try {
        const token = localStorage.getItem('authToken') || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwicGVybWlzc2lvbnMiOlsicmVhZCIsIndyaXRlIiwiYWRtaW4iXSwidHlwZSI6ImFjY2VzcyIsImlhdCI6MTc1NzU1NzA0NiwiZXhwIjoxNzU3NTU3OTQ2LCJqdGkiOiIwMGU2Y2RhNy02YTkxLTQ2ODUtODIzZi05ZmYwOGM2MjUxNzciLCJpc3MiOiJ3aGF0c2FwcC1hZ2VudCIsImF1ZCI6IndoYXRzYXBwLWFnZW50LWFwaSJ9.E-S5-Zzjidw4cQwFkhyois67k6FjBFUjGF850rDuB7E'
        
        console.log('🔍 Fazendo requisição direta...')
        const response = await fetch('https://wppagent-production.up.railway.app/conversations/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data = await response.json()
        console.log('📦 Dados brutos:', data)
        console.log('📦 Tipo:', typeof data)
        console.log('📦 Tem conversations?', !!data.conversations)
        console.log('📦 É array conversations?', Array.isArray(data.conversations))
        
        if (data.conversations && Array.isArray(data.conversations)) {
          setConversations(data.conversations)
          console.log(`✅ ${data.conversations.length} conversas carregadas`)
        } else {
          console.log('❌ Estrutura inesperada:', data)
        }
      } catch (error) {
        console.error('❌ Erro:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return <div className="p-4">Carregando...</div>
  }

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">Teste Direto de Conversas</h1>
      <p className="mb-4">Total: {conversations.length} conversas</p>
      
      <div className="space-y-2">
        {conversations.slice(0, 5).map((conv, index) => (
          <div key={conv.id || index} className="border p-3 rounded">
            <div className="font-semibold">{conv.user_name || 'Sem nome'}</div>
            <div className="text-sm text-gray-600">{conv.user_phone}</div>
            <div className="text-xs text-gray-500">
              ID: {conv.id} | Messages: {conv.total_messages} | Status: {conv.status}
            </div>
          </div>
        ))}
      </div>
      
      {conversations.length > 5 && (
        <div className="mt-4 text-gray-500">
          ... e mais {conversations.length - 5} conversas
        </div>
      )}
    </div>
  )
}
