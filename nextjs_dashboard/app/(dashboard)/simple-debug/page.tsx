'use client'

import React, { useState } from 'react'

export default function SimpleDebugPage() {
  const [apiData, setApiData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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
      setError(err.message)
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

  return (
    <div style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px' }}>
        Simple Debug Page
      </h1>
      
      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', padding: '24px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
          Teste de API
        </h2>
        
        <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
          <button
            onClick={testApi}
            disabled={loading}
            style={{
              backgroundColor: loading ? '#9CA3AF' : '#2563EB',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Testando...' : 'Testar API'}
          </button>
          
          <button
            onClick={testAuth}
            style={{
              backgroundColor: '#059669',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            Testar Autenticação
          </button>
        </div>
        
        {error && (
          <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#FEF2F2', border: '1px solid #FECACA', borderRadius: '4px' }}>
            <h3 style={{ fontWeight: '600', color: '#991B1B' }}>Erro:</h3>
            <p style={{ color: '#B91C1C' }}>{error}</p>
          </div>
        )}
        
        {apiData && (
          <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '4px' }}>
            <h3 style={{ fontWeight: '600', color: '#166534' }}>Dados Recebidos:</h3>
            <pre style={{ fontSize: '12px', color: '#15803D', overflow: 'auto' }}>
              {JSON.stringify(apiData, null, 2)}
            </pre>
          </div>
        )}
      </div>
      
      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', padding: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px' }}>
          Status da Aplicação
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
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
