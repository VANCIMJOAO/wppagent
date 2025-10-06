import { useState, useCallback, useEffect } from 'react'
import { debugLog } from '@/lib/debug';

/**
 * 🎯 Hook para Estados Loading/Erro
 * ===============================
 *
 * Hook customizado para gerenciar estados de loading, erro e dados
 * de forma consistente em todo o dashboard.
 *
 * Autor: Claude AI
 * Data: 2025-09-07
 */

// ✅ Tipo para estado de async operation
export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: Error | string | null
}

// ✅ Hook principal para async states
export function useAsyncState<T>(initialData: T | null = null) {
  const [state, setState] = useState<AsyncState<T>>({
    data: initialData,
    loading: false,
    error: null
  })

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading, error: loading ? null : prev.error }))
  }, [])

  const setData = useCallback((data: T) => {
    setState({ data, loading: false, error: null })
  }, [])

  const setError = useCallback((error: Error | string) => {
    setState({ data: null, loading: false, error })
  }, [])

  const reset = useCallback(() => {
    setState({ data: initialData, loading: false, error: null })
  }, [initialData])

  // ✅ Execute async operation with automatic state management
  const execute = useCallback(async (asyncFn: () => Promise<T>) => {
    setLoading(true)
    try {
      const result = await asyncFn()
      setData(result)
      return result
    } catch (error) {
      const errorMsg = error instanceof Error ? error : String(error)
      setError(errorMsg)
      throw error
    }
  }, [setLoading, setData, setError])

  return {
    ...state,
    setLoading,
    setData,
    setError,
    reset,
    execute
  }
}

// ✅ Hook para operações de lista (GET com filtros)
export function useAsyncList<T>(fetchFn?: (filters?: any) => Promise<T[]>) {
  const [filters, setFilters] = useState<any>({})
  const asyncState = useAsyncState<T[]>([])

  const refresh = useCallback(async (newFilters?: any) => {
    if (!fetchFn) return

    const currentFilters = newFilters || filters
    setFilters(currentFilters)

    return asyncState.execute(() => fetchFn(currentFilters))
  }, [fetchFn, filters, asyncState])

  const updateFilters = useCallback((newFilters: any) => {
    const updatedFilters = { ...filters, ...newFilters }
    setFilters(updatedFilters)
    return refresh(updatedFilters)
  }, [filters, refresh])

  return {
    ...asyncState,
    filters,
    setFilters,
    updateFilters,
    refresh
  }
}

// ✅ Hook para operações CRUD
export function useAsyncCrud<T extends { id: number | string }>(
  fetchFn?: (id: string | number) => Promise<T>,
  createFn?: (data: Partial<T>) => Promise<T>,
  updateFn?: (id: string | number, data: Partial<T>) => Promise<T>,
  deleteFn?: (id: string | number) => Promise<void>
) {
  const asyncState = useAsyncState<T>()
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const fetch = useCallback(async (id: string | number) => {
    if (!fetchFn) return
    return asyncState.execute(() => fetchFn(id))
  }, [fetchFn, asyncState])

  const create = useCallback(async (data: Partial<T>) => {
    if (!createFn) return
    setSaving(true)
    try {
      const result = await createFn(data)
      asyncState.setData(result)
      return result
    } catch (error) {
      asyncState.setError(error instanceof Error ? error : String(error))
      throw error
    } finally {
      setSaving(false)
    }
  }, [createFn, asyncState])

  const update = useCallback(async (id: string | number, data: Partial<T>) => {
    if (!updateFn) return
    setSaving(true)
    try {
      const result = await updateFn(id, data)
      asyncState.setData(result)
      return result
    } catch (error) {
      asyncState.setError(error instanceof Error ? error : String(error))
      throw error
    } finally {
      setSaving(false)
    }
  }, [updateFn, asyncState])

  const remove = useCallback(async (id: string | number) => {
    if (!deleteFn) return
    setDeleting(true)
    try {
      await deleteFn(id)
      asyncState.reset() // Use reset instead of setData(null)
    } catch (error) {
      asyncState.setError(error instanceof Error ? error : String(error))
      throw error
    } finally {
      setDeleting(false)
    }
  }, [deleteFn, asyncState])

  return {
    ...asyncState,
    saving,
    deleting,
    fetch,
    create,
    update,
    remove
  }
}

// ✅ Hook para retry logic
export function useRetry(maxRetries: number = 3, delay: number = 1000) {
  const [retryCount, setRetryCount] = useState(0)
  const [retrying, setRetrying] = useState(false)

  const retry = useCallback(async (operation: () => Promise<any>) => {
    if (retryCount >= maxRetries) {
      throw new Error(`Máximo de ${maxRetries} tentativas atingido`)
    }

    setRetrying(true)
    try {
      // Add delay before retry
      if (retryCount > 0) {
        await new Promise(resolve => setTimeout(resolve, delay * retryCount))
      }

      const result = await operation()
      setRetryCount(0) // Reset on success
      return result
    } catch (error) {
      setRetryCount(prev => prev + 1)
      throw error
    } finally {
      setRetrying(false)
    }
  }, [retryCount, maxRetries, delay])

  const resetRetries = useCallback(() => {
    setRetryCount(0)
  }, [])

  return {
    retryCount,
    retrying,
    canRetry: retryCount < maxRetries,
    retry,
    resetRetries
  }
}

// ✅ Hook para debounced operations
export function useDebouncedCallback<T extends any[]>(
  callback: (...args: T) => void | Promise<void>,
  delay: number = 300
) {
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null)

  const debouncedCallback = useCallback((...args: T) => {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }

    const timer = setTimeout(() => {
      callback(...args)
    }, delay)

    setDebounceTimer(timer)
  }, [callback, delay, debounceTimer])

  // Cleanup on unmount
  const cancel = useCallback(() => {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      setDebounceTimer(null)
    }
  }, [debounceTimer])

  return {
    debouncedCallback,
    cancel
  }
}

// ✅ Hook para network status
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true)

  const updateNetworkStatus = useCallback(() => {
    setIsOnline(navigator.onLine)
  }, [])

  // Setup event listeners on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', updateNetworkStatus)
      window.addEventListener('offline', updateNetworkStatus)

      return () => {
        window.removeEventListener('online', updateNetworkStatus)
        window.removeEventListener('offline', updateNetworkStatus)
      }
    }
  }, [updateNetworkStatus])

  return isOnline
}

// ✅ Hook para localStorage state
export function useLocalStorageState<T>(
  key: string,
  initialValue: T
): [T, (value: T) => void] {
  const [state, setState] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue

    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      debugLog.warn(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  const setValue = useCallback((value: T) => {
    try {
      setState(value)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(value))
      }
    } catch (error) {
      debugLog.error(`Error setting localStorage key "${key}":`, error)
    }
  }, [key])

  return [state, setValue]
}
