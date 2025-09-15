import { useState, useCallback } from 'react'

/**
 * 🎯 Hook para Estados Padronizados de API
 * =======================================
 *
 * Hook simples e focado para gerenciar estados de loading, dados e erro
 * em chamadas de API. Versão simplificada do useAsyncState.
 *
 * Autor: Desenvolvedor
 * Data: 2025-09-08
 */

export interface ApiState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

export function useApiState<T>(initialData: T | null = null) {
  const [state, setState] = useState<ApiState<T>>({
    data: initialData,
    loading: false,
    error: null
  })

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading, error: null }))
  }, [])

  const setData = useCallback((data: T) => {
    setState({ data, loading: false, error: null })
  }, [])

  const setError = useCallback((error: Error) => {
    setState(prev => ({ ...prev, error, loading: false }))
  }, [])

  const reset = useCallback(() => {
    setState({ data: initialData, loading: false, error: null })
  }, [initialData])

  return {
    ...state,
    setLoading,
    setData,
    setError,
    reset
  }
}
