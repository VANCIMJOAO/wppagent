/**
 * Hook para testar conectividade e buscar dados reais do backend
 * Diagnóstico de APIs disponíveis
 */

import { useState, useEffect } from 'react'

export interface BackendStatus {
  connected: boolean;
  endpoints: {
    [key: string]: boolean;
  };
  lastCheck: Date;
  error?: string;
}

export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatus>({
    connected: false,
    endpoints: {},
    lastCheck: new Date()
  })

  useEffect(() => {
    const checkBackendStatus = async () => {
      const endpointsToCheck = [
        '/api/dashboard/stats',
        '/api/clients',
        '/api/clients/stats',
        '/api/conversations',
        '/api/appointments',
        '/api/health',
        '/api/status'
      ]

      const results: { [key: string]: boolean } = {}
      let connected = false
      let error: string | undefined

      try {
        // Testar cada endpoint
        for (const endpoint of endpointsToCheck) {
          try {
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), 5000)

            const response = await fetch(endpoint, {
              method: 'GET',
              signal: controller.signal
            })

            clearTimeout(timeoutId)

            results[endpoint] = response.ok || response.status !== 404
            if (response.ok) connected = true

            console.log(`Endpoint ${endpoint}: ${response.status}`)
          } catch (err) {
            results[endpoint] = false
            console.log(`Endpoint ${endpoint}: ERROR`, err)
          }
        }
      } catch (err) {
        error = err instanceof Error ? err.message : 'Erro de conexão'
      }

      setStatus({
        connected,
        endpoints: results,
        lastCheck: new Date(),
        error
      })
    }

    checkBackendStatus()

    // Recheck every 30 seconds
    const interval = setInterval(checkBackendStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  return status
}

// Hook para buscar dados reais disponíveis no backend
export function useRealDashboardData() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchRealData = async () => {
      setLoading(true)
      setError(null)

      try {
        // Tentar diferentes endpoints que podem existir no backend
        const possibleEndpoints = [
          '/api/proxy/dashboard',
          '/api/proxy/dashboard/stats',
          '/api/proxy/stats',
          '/api/proxy/metrics',
          '/api/proxy/admin/dashboard',
          '/api/proxy/api/dashboard'
        ]

        let fetchedData = null

        for (const endpoint of possibleEndpoints) {
          try {
            console.log(`Tentando endpoint: ${endpoint}`)
            const response = await fetch(endpoint)

            if (response.ok) {
              const responseData = await response.json()
              console.log(`Dados encontrados em ${endpoint}:`, responseData)
              fetchedData = {
                endpoint,
                data: responseData,
                status: response.status
              }
              break
            } else {
              console.log(`${endpoint}: ${response.status} ${response.statusText}`)
            }
          } catch (err) {
            console.log(`${endpoint}: ERROR`, err)
          }
        }

        if (fetchedData) {
          setData(fetchedData)
        } else {
          setError('Nenhum endpoint de dados encontrado')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao buscar dados')
      } finally {
        setLoading(false)
      }
    }

    fetchRealData()
  }, [])

  return { data, loading, error }
}
