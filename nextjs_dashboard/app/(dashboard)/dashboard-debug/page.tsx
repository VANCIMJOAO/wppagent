'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { useRouter } from 'next/navigation'

export default function DashboardDebugPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const router = useRouter()
  const [apiData, setApiData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ✅ Não redirecionar - página de debug deve funcionar sempre
  // useEffect(() => {
  //   if (!authLoading && !isAuthenticated) {
  //     router.replace('/login')
  //   }
  // }, [isAuthenticated, authLoading, router])

  const testApi = async () => {
    setLoading(true)
    setError(null)
    
    try {
      console.log('🧪 Testando API diretamente...')
      
      const response = await fetch('/api/analytics/real-dashboard-summary', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      console.log('📡 Status da resposta:', response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }
      
      const data = await response.json()
      console.log('✅ Dados recebidos:', data)
      setApiData(data)
      
    } catch (err) {
      console.error('❌ Erro na API:', err)
      setError(err instanceof Error ? err.message : 'Erro desconhecido')
    } finally {
      setLoading(false)
    }
  }

  const testAuth = async () => {
    try {
      console.log('🔐 Testando autenticação...')
      
      const response = await fetch('/api/auth/status', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      console.log('🔐 Status da autenticação:', response.status)
      
      if (response.ok) {
        const authData = await response.json()
        console.log('✅ Dados de autenticação:', authData)
        alert(`Autenticado: ${authData.isAuthenticated}`)
      } else {
        console.error('❌ Erro na autenticação')
        alert('Não autenticado')
      }
      
    } catch (error) {
      console.error('❌ Erro ao testar autenticação:', error)
      alert('Erro ao testar autenticação')
    }
  }

  // ✅ Página de debug sempre renderiza - não depende de autenticação

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Dashboard Debug</h1>
      
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Teste de API</h2>
        
        <div className="flex gap-4">
          <button
            onClick={testApi}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Testando...' : 'Testar API'}
          </button>
          
          <button
            onClick={testAuth}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Testar Autenticação
          </button>
        </div>
        
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
            <h3 className="font-semibold text-red-800">Erro:</h3>
            <p className="text-red-700">{error}</p>
          </div>
        )}
        
        {apiData && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
            <h3 className="font-semibold text-green-800">Dados Recebidos:</h3>
            <pre className="text-sm text-green-700 overflow-auto">
              {JSON.stringify(apiData, null, 2)}
            </pre>
          </div>
        )}
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Status da Aplicação</h2>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <strong>Autenticado:</strong> {isAuthenticated ? 'Sim' : 'Não'}
          </div>
          <div>
            <strong>Loading Auth:</strong> {authLoading ? 'Sim' : 'Não'}
          </div>
          <div>
            <strong>Loading API:</strong> {loading ? 'Sim' : 'Não'}
          </div>
          <div>
            <strong>Erro:</strong> {error ? 'Sim' : 'Não'}
          </div>
        </div>
      </div>
    </div>
  )
}
