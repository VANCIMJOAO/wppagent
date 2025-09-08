/**
 * 📊 Guia de Implementação - Loading States
 * ========================================
 * 
 * Guia prático para implementar os componentes de loading states
 * em componentes existentes do dashboard.
 * 
 * Autor: Claude AI
 * Data: 2025-09-07
 */

'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  LoadingSpinner,
  ErrorFallback,
  EmptyState,
  ButtonLoading,
  CardSkeleton,
  DataStateWrapper
} from "@/components/ui/loading-states"
import { useAsyncState, useRetry } from "@/hooks/use-async-state"

// ✅ 1. Uso Básico do LoadingSpinner
export function BasicLoadingExample() {
  const [loading, setLoading] = useState(false)
  
  const handleAction = async () => {
    setLoading(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setLoading(false)
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Loading Básico</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button onClick={handleAction} disabled={loading}>
          <ButtonLoading loading={loading}>
            Executar Ação
          </ButtonLoading>
        </Button>
        
        {loading && (
          <div className="p-8">
            <LoadingSpinner size="lg" />
            <p className="text-center text-sm text-gray-600 mt-2">Processando...</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ✅ 2. Uso do ErrorFallback
export function ErrorHandlingExample() {
  const [error, setError] = useState<Error | null>(null)
  
  const simulateError = () => {
    setError(new Error('Erro simulado para demonstração'))
  }
  
  const clearError = () => {
    setError(null)
  }
  
  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <ErrorFallback
            error={error}
            retry={clearError}
            title="Ops! Algo deu errado"
          />
        </CardContent>
      </Card>
    )
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Tratamento de Erro</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={simulateError} variant="destructive">
          Simular Erro
        </Button>
      </CardContent>
    </Card>
  )
}

// ✅ 3. Uso do EmptyState
export function EmptyStateExample() {
  const [hasData, setHasData] = useState(false)
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Estado Vazio</CardTitle>
      </CardHeader>
      <CardContent>
        {!hasData ? (
          <EmptyState
            title="Sem dados para exibir"
            description="Adicione alguns itens para começar."
            action={
              <Button onClick={() => setHasData(true)}>
                Adicionar Item
              </Button>
            }
          />
        ) : (
          <div className="space-y-2">
            <p>✅ Dados carregados com sucesso!</p>
            <Button 
              onClick={() => setHasData(false)} 
              variant="outline"
            >
              Limpar Dados
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// ✅ 4. Uso do useAsyncState Hook
export function AsyncStateExample() {
  // Simulação de API
  const fetchData = async (): Promise<string[]> => {
    await new Promise(resolve => setTimeout(resolve, 1500))
    if (Math.random() < 0.3) {
      throw new Error('Falha na rede')
    }
    return ['Item 1', 'Item 2', 'Item 3']
  }
  
  const { data, loading, error, execute } = useAsyncState<string[]>()
  
  const handleLoad = () => {
    execute(fetchData)
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Hook useAsyncState</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Button onClick={handleLoad} disabled={loading}>
            <ButtonLoading loading={loading}>
              Carregar Dados
            </ButtonLoading>
          </Button>
          
          <DataStateWrapper<string[]>
            data={data}
            loading={loading}
            error={error}
            retry={handleLoad}
            emptyTitle="Nenhum item encontrado"
            emptyDescription="Clique em 'Carregar Dados' para buscar itens."
          >
            {(items: string[]) => (
              <ul className="space-y-2">
                {items.map((item, index) => (
                  <li key={index} className="p-2 bg-gray-100 rounded">
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </DataStateWrapper>
        </div>
      </CardContent>
    </Card>
  )
}

// ✅ 5. Skeleton para Cards
export function SkeletonExample() {
  const [showSkeleton, setShowSkeleton] = useState(true)
  
  return (
    <div className="space-y-4">
      <Button 
        onClick={() => setShowSkeleton(!showSkeleton)}
        variant="outline"
      >
        {showSkeleton ? 'Mostrar Conteúdo' : 'Mostrar Skeleton'}
      </Button>
      
      {showSkeleton ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Vendas</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">R$ 12.500</p>
              <p className="text-sm text-gray-600">+12% este mês</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Clientes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">1.234</p>
              <p className="text-sm text-gray-600">+5% este mês</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Pedidos</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">89</p>
              <p className="text-sm text-gray-600">+8% este mês</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

// ✅ 6. Exemplo com useRetry
export function RetryExample() {
  const [shouldFail, setShouldFail] = useState(true)
  const asyncState = useAsyncState<string>()
  
  const fetchData = async (): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1000))
    if (shouldFail) {
      throw new Error('Conexão falhou')
    }
    return 'Dados carregados com sucesso!'
  }
  
  const { retryCount, retry } = useRetry(3, 1000)
  
  const handleLoad = async () => {
    try {
      await asyncState.execute(fetchData)
    } catch (error) {
      // Tentativa de retry
      if (retryCount < 3) {
        await retry(fetchData)
      }
    }
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Sistema de Retry</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex space-x-2">
          <Button onClick={handleLoad} disabled={asyncState.loading}>
            <ButtonLoading loading={asyncState.loading}>
              Carregar
            </ButtonLoading>
          </Button>
          
          <Button 
            onClick={() => setShouldFail(!shouldFail)}
            variant="outline"
          >
            {shouldFail ? 'Desabilitar Falha' : 'Habilitar Falha'}
          </Button>
        </div>
        
        {retryCount > 0 && (
          <p className="text-sm text-gray-600">
            Tentativas: {retryCount}/3
          </p>
        )}
        
        <DataStateWrapper<string>
          data={asyncState.data}
          loading={asyncState.loading}
          error={asyncState.error}
          retry={handleLoad}
          emptyTitle="Nenhum dado carregado"
          emptyDescription="Clique em 'Carregar' para buscar dados."
        >
          {(result: string) => (
            <div className="p-4 bg-green-100 text-green-800 rounded">
              {result}
            </div>
          )}
        </DataStateWrapper>
      </CardContent>
    </Card>
  )
}

// ✅ 7. Dashboard com todos os estados
export function LoadingStatesDashboard() {
  return (
    <div className="space-y-8 p-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">Loading States - Exemplos</h1>
        <p className="text-gray-600">
          Demonstração de todos os componentes de loading states
        </p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <BasicLoadingExample />
        <ErrorHandlingExample />
        <EmptyStateExample />
        <AsyncStateExample />
        <RetryExample />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold mb-4">Skeleton Loading</h2>
        <SkeletonExample />
      </div>
    </div>
  )
}

export default LoadingStatesDashboard
