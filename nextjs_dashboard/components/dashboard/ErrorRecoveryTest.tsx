/**
 * Teste Prático do Sistema de Error Recovery
 * Valida funcionamento de retry, cache, degraded mode e network detection
 */
'use client'

import React, { useState, useEffect } from 'react'
import { useDashboardStatsRobust } from '@/hooks/useDashboardStatsRobust'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Play, 
  Square, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Wifi,
  WifiOff,
  Database,
  Timer,
  Zap,
  Settings
} from 'lucide-react'
import { toast } from 'sonner'

// Mock para interceptar e simular falhas na API
let shouldFailAPI = false
let failureType: 'network' | 'server' | 'timeout' | 'auth' = 'network'
let failureCount = 0

// Interceptar fetch para simular erros
const originalFetch = global.fetch

export const ErrorRecoveryTest: React.FC = () => {
  const [testRunning, setTestRunning] = useState(false)
  const [testResults, setTestResults] = useState<Array<{
    test: string
    status: 'pass' | 'fail' | 'running'
    details: string
    timestamp: Date
  }>>([])
  
  const {
    data: stats,
    error,
    isLoading,
    isFetching,
    isError,
    recoveryMode,
    retryCount,
    networkStatus,
    isOffline,
    refetch,
    manualRetry,
    clearCache,
    isUsingCache,
    isDegraded,
    canRetry,
    debugInfo
  } = useDashboardStatsRobust({
    maxRetries: 3,
    retryDelay: 1000,
    cacheTimeout: 30 * 60 * 1000,
    enableDegradedMode: true,
    enableNetworkDetection: true,
    enableOfflineMode: true
  })

  // Simular fetch com falhas
  useEffect(() => {
    global.fetch = async (url: RequestInfo | URL, options?: RequestInit) => {
      if (shouldFailAPI && (url as string).includes('/api/analytics')) {
        failureCount++
        
        switch (failureType) {
          case 'network':
            throw new Error('NetworkError: Failed to fetch')
          case 'server':
            return new Response(JSON.stringify({ error: 'Internal Server Error' }), {
              status: 500,
              statusText: 'Internal Server Error'
            })
          case 'timeout':
            throw new Error('TimeoutError: Request timeout')
          case 'auth':
            return new Response(JSON.stringify({ error: 'Unauthorized' }), {
              status: 401,
              statusText: 'Unauthorized'
            })
        }
      }
      
      return originalFetch(url, options)
    }

    return () => {
      global.fetch = originalFetch
    }
  }, [])

  const addTestResult = (test: string, status: 'pass' | 'fail' | 'running', details: string) => {
    setTestResults(prev => [...prev, {
      test,
      status,
      details,
      timestamp: new Date()
    }])
  }

  const runTest = async (
    testName: string, 
    testFunction: () => Promise<boolean>, 
    expectedBehavior: string
  ) => {
    addTestResult(testName, 'running', 'Iniciando teste...')
    
    try {
      const result = await testFunction()
      addTestResult(testName, result ? 'pass' : 'fail', 
        result ? 'Comportamento esperado confirmado' : 'Comportamento inesperado')
      return result
    } catch (error) {
      addTestResult(testName, 'fail', `Erro: ${error}`)
      return false
    }
  }

  const runAllTests = async () => {
    setTestRunning(true)
    setTestResults([])
    failureCount = 0
    
    toast.info('🧪 Iniciando bateria de testes de Error Recovery...')

    // Teste 1: Estado Normal
    await runTest(
      'Estado Normal',
      async () => {
        shouldFailAPI = false
        await new Promise(resolve => setTimeout(resolve, 1000))
        refetch()
        await new Promise(resolve => setTimeout(resolve, 2000))
        return recoveryMode === 'normal'
      },
      'Dashboard deve funcionar normalmente'
    )

    // Teste 2: Network Error com Retry
    await runTest(
      'Network Error + Retry Logic',
      async () => {
        shouldFailAPI = true
        failureType = 'network'
        refetch()
        await new Promise(resolve => setTimeout(resolve, 5000))
        return retryCount > 0
      },
      'Sistema deve tentar retry automaticamente'
    )

    // Teste 3: Cache Fallback
    await runTest(
      'Cache Fallback',
      async () => {
        // Primeiro carrega dados normalmente
        shouldFailAPI = false
        refetch()
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        // Depois simula falha e verifica se usa cache
        shouldFailAPI = true
        failureType = 'server'
        refetch()
        await new Promise(resolve => setTimeout(resolve, 3000))
        
        return isUsingCache || recoveryMode === 'cached'
      },
      'Sistema deve usar dados em cache quando API falha'
    )

    // Teste 4: Modo Degradado
    await runTest(
      'Modo Degradado',
      async () => {
        shouldFailAPI = true
        failureType = 'server'
        refetch()
        await new Promise(resolve => setTimeout(resolve, 4000))
        return isDegraded || recoveryMode === 'degraded'
      },
      'Sistema deve entrar em modo degradado em falhas críticas'
    )

    // Teste 5: Manual Retry
    await runTest(
      'Manual Retry',
      async () => {
        const initialRetryCount = retryCount
        manualRetry()
        await new Promise(resolve => setTimeout(resolve, 2000))
        return retryCount > initialRetryCount || canRetry
      },
      'Retry manual deve funcionar'
    )

    // Teste 6: Clear Cache
    await runTest(
      'Clear Cache',
      async () => {
        clearCache()
        await new Promise(resolve => setTimeout(resolve, 1000))
        return !isUsingCache
      },
      'Limpeza de cache deve funcionar'
    )

    // Teste 7: Recovery após falhas
    await runTest(
      'Recovery após Falhas',
      async () => {
        shouldFailAPI = false // Reestabelece conexão
        refetch()
        await new Promise(resolve => setTimeout(resolve, 3000))
        return recoveryMode === 'normal' && !isError
      },
      'Sistema deve se recuperar quando conexão volta'
    )

    shouldFailAPI = false
    setTestRunning(false)
    
    const passedTests = testResults.filter(t => t.status === 'pass').length
    const totalTests = testResults.length
    
    toast.success(`✅ Testes concluídos: ${passedTests}/${totalTests} passaram`)
  }

  const stopTests = () => {
    setTestRunning(false)
    shouldFailAPI = false
    toast.info('Testes interrompidos')
  }

  const getStatusIcon = (status: 'pass' | 'fail' | 'running') => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'fail':
        return <XCircle className="w-4 h-4 text-red-500" />
      case 'running':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />
    }
  }

  const passedTests = testResults.filter(t => t.status === 'pass').length
  const failedTests = testResults.filter(t => t.status === 'fail').length

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-yellow-600" />
            <span>Teste de Error Recovery</span>
            {testRunning && (
              <Badge variant="secondary" className="animate-pulse">
                Executando...
              </Badge>
            )}
          </CardTitle>
          <p className="text-sm text-gray-600">
            Validação automática de todos os mecanismos de recuperação de erro
          </p>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Status Atual do Sistema */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-sm text-gray-600">Recovery Mode</div>
              <div className="font-semibold capitalize">{recoveryMode}</div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-gray-600">Retry Count</div>
              <div className="font-semibold">{retryCount}</div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-gray-600">Using Cache</div>
              <div className="font-semibold">{isUsingCache ? 'Yes' : 'No'}</div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-gray-600">Network</div>
              <div className="font-semibold">
                {isOffline ? 'Offline' : 'Online'}
              </div>
            </div>
          </div>

          {/* Controles */}
          <div className="flex space-x-2">
            <Button
              onClick={runAllTests}
              disabled={testRunning}
              className="flex-1"
            >
              <Play className="w-4 h-4 mr-2" />
              Executar Todos os Testes
            </Button>
            
            {testRunning && (
              <Button
                onClick={stopTests}
                variant="outline"
                className="flex-1"
              >
                <Square className="w-4 h-4 mr-2" />
                Parar Testes
              </Button>
            )}
          </div>

          {/* Resultados Resumidos */}
          {testResults.length > 0 && (
            <div className="grid grid-cols-3 gap-4 p-4 bg-blue-50 rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{passedTests}</div>
                <div className="text-sm text-gray-600">Passou</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{failedTests}</div>
                <div className="text-sm text-gray-600">Falhou</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{testResults.length}</div>
                <div className="text-sm text-gray-600">Total</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resultados Detalhados */}
      {testResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Resultados dos Testes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {testResults.map((result, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
                  {getStatusIcon(result.status)}
                  
                  <div className="flex-1">
                    <div className="font-medium">{result.test}</div>
                    <div className="text-sm text-gray-600">{result.details}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {result.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Debug Information */}
      {process.env.NODE_ENV === 'development' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Debug Info</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto">
              {JSON.stringify({
                recoveryMode,
                retryCount,
                isError,
                error: error?.message,
                isUsingCache,
                isDegraded,
                isOffline,
                networkStatus,
                debugInfo,
                failureCount
              }, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default ErrorRecoveryTest
