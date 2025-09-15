/**
 * Hook para Dashboard com Error Recovery Robusto
 * Implementa retry logic, cache fallback, network detection e modo degradado
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { toast } from 'sonner'

// Interfaces
interface DashboardStats {
  conversations_today: number
  messages_today: number
  appointments_today: number
  new_clients_today: number
  total_conversations: number
  total_messages: number
  total_appointments: number
  total_clients: number
  conversion_rate: number
  growth_rate: number
  last_updated?: string
  is_cached?: boolean
  is_degraded?: boolean
}

interface ErrorRecoveryOptions {
  maxRetries?: number
  retryDelay?: number
  cacheTimeout?: number
  enableDegradedMode?: boolean
  enableNetworkDetection?: boolean
  enableOfflineMode?: boolean
}

interface NetworkStatus {
  isOnline: boolean
  connectionType: string
  effectiveType: string
  rtt: number
  downlink: number
}

interface CacheEntry<T> {
  data: T
  timestamp: number
  version: string
  isValid: boolean
}

// Utilitários para Error Recovery
class DashboardErrorRecovery {
  private static readonly CACHE_KEY = 'dashboard-stats-cache'
  private static readonly CACHE_VERSION = '1.0'
  
  // 1. Retry Logic com Exponential Backoff
  static async executeWithRetry<T>(
    operation: () => Promise<T>,
    options: ErrorRecoveryOptions = {}
  ): Promise<T> {
    const {
      maxRetries = 3,
      retryDelay = 1000,
    } = options
    
    let lastError: Error | null = null
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error as Error
        
        console.warn(`Tentativa ${attempt + 1}/${maxRetries + 1} falhou:`, error)
        
        if (attempt < maxRetries) {
          // Exponential backoff: 1s, 2s, 4s, 8s...
          const delay = retryDelay * Math.pow(2, attempt)
          console.log(`Tentando novamente em ${delay}ms...`)
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }
    }
    
    throw lastError
  }
  
  // 2. Cache Management
  static saveToCache<T>(key: string, data: T): void {
    try {
      const cacheEntry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        version: this.CACHE_VERSION,
        isValid: true
      }
      
      localStorage.setItem(key, JSON.stringify(cacheEntry))
      console.log('✅ Dados salvos no cache:', key)
    } catch (error) {
      console.error('❌ Erro ao salvar cache:', error)
    }
  }
  
  static loadFromCache<T>(key: string, maxAge: number = 30 * 60 * 1000): T | null {
    try {
      const cached = localStorage.getItem(key)
      if (!cached) return null
      
      const cacheEntry: CacheEntry<T> = JSON.parse(cached)
      
      // Verificar versão do cache
      if (cacheEntry.version !== this.CACHE_VERSION) {
        console.warn('⚠️ Versão do cache desatualizada, ignorando')
        localStorage.removeItem(key)
        return null
      }
      
      // Verificar idade do cache
      const age = Date.now() - cacheEntry.timestamp
      if (age > maxAge) {
        console.warn('⚠️ Cache expirado, ignorando')
        localStorage.removeItem(key)
        return null
      }
      
      console.log(`✅ Dados carregados do cache (idade: ${Math.round(age / 1000)}s)`)
      return {
        ...cacheEntry.data,
        is_cached: true,
        last_updated: new Date(cacheEntry.timestamp).toISOString()
      } as T
    } catch (error) {
      console.error('❌ Erro ao carregar cache:', error)
      return null
    }
  }
  
  // 3. Network Detection
  static getNetworkStatus(): NetworkStatus {
    const connection = (navigator as any)?.connection || (navigator as any)?.mozConnection || (navigator as any)?.webkitConnection
    
    return {
      isOnline: navigator.onLine,
      connectionType: connection?.type || 'unknown',
      effectiveType: connection?.effectiveType || 'unknown',
      rtt: connection?.rtt || 0,
      downlink: connection?.downlink || 0
    }
  }
  
  // 4. Degraded Mode Data
  static getDegradedModeData(): DashboardStats {
    console.warn('🟡 Ativando modo degradado com dados mínimos')
    
    return {
      conversations_today: 0,
      messages_today: 0,
      appointments_today: 0,
      new_clients_today: 0,
      total_conversations: 0,
      total_messages: 0,
      total_appointments: 0,
      total_clients: 0,
      conversion_rate: 0,
      growth_rate: 0,
      last_updated: new Date().toISOString(),
      is_degraded: true
    }
  }
  
  // 5. Authenticated Fetch com Error Handling
  static async authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = null // ✅ REMOVIDO: Token inseguro
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        'X-Client-Version': '1.0',
        'X-Timestamp': Date.now().toString(),
        ...options.headers,
      },
    })
    
    // Verificar status HTTP
    if (!response.ok) {
      if (response.status === 401) {
        // Token expirado
        // ✅ REMOVIDO: Token inseguro
        throw new Error('Sessão expirada. Faça login novamente.')
      } else if (response.status === 403) {
        throw new Error('Acesso negado. Permissões insuficientes.')
      } else if (response.status === 429) {
        throw new Error('Muitas requisições. Tente novamente em alguns minutos.')
      } else if (response.status >= 500) {
        throw new Error(`Erro no servidor (${response.status}). Tente novamente mais tarde.`)
      } else {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`)
      }
    }
    
    return response
  }
}

// Hook Principal com Error Recovery
export function useDashboardStatsRobust(options: ErrorRecoveryOptions = {}) {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    cacheTimeout = 30 * 60 * 1000, // 30 minutos
    enableDegradedMode = true,
    enableNetworkDetection = true,
    enableOfflineMode = true,
  } = options
  
  const [retryCount, setRetryCount] = useState(0)
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>(
    DashboardErrorRecovery.getNetworkStatus()
  )
  const [isOffline, setIsOffline] = useState(!navigator.onLine)
  const [lastError, setLastError] = useState<Error | null>(null)
  const [recoveryMode, setRecoveryMode] = useState<'normal' | 'cached' | 'degraded' | 'offline'>('normal')
  
  const queryClient = useQueryClient()
  
  // Monitorar status de rede
  useEffect(() => {
    if (!enableNetworkDetection) return
    
    const updateNetworkStatus = () => {
      const status = DashboardErrorRecovery.getNetworkStatus()
      setNetworkStatus(status)
      setIsOffline(!status.isOnline)
      
      if (status.isOnline && recoveryMode === 'offline') {
        console.log('🟢 Conexão restaurada, tentando recarregar dados')
        queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() })
        setRecoveryMode('normal')
      }
    }
    
    window.addEventListener('online', updateNetworkStatus)
    window.addEventListener('offline', updateNetworkStatus)
    
    // Verificar conexão periodicamente
    const interval = setInterval(updateNetworkStatus, 30000) // 30s
    
    return () => {
      window.removeEventListener('online', updateNetworkStatus)
      window.removeEventListener('offline', updateNetworkStatus)
      clearInterval(interval)
    }
  }, [recoveryMode, queryClient, enableNetworkDetection])
  
  // Função para buscar dados com recovery
  const fetchStatsWithRecovery = useCallback(async (): Promise<DashboardStats> => {
    setLastError(null)
    
    // 1. Verificar se está offline
    if (isOffline && enableOfflineMode) {
      console.log('📱 Modo offline detectado, tentando cache...')
      const cachedData = DashboardErrorRecovery.loadFromCache<DashboardStats>(
        DashboardErrorRecovery['CACHE_KEY'],
        24 * 60 * 60 * 1000 // Cache offline: 24h
      )
      
      if (cachedData) {
        setRecoveryMode('offline')
        return cachedData
      }
      
      if (enableDegradedMode) {
        setRecoveryMode('degraded')
        return DashboardErrorRecovery.getDegradedModeData()
      }
      
      throw new Error('Sem conexão com a internet e nenhum cache disponível')
    }
    
    // 2. Tentar buscar dados frescos com retry
    try {
      const data = await DashboardErrorRecovery.executeWithRetry(
        async () => {
          const response = await DashboardErrorRecovery.authenticatedFetch(
            '/api/dashboard/stats/daily'
          )
          return response.json()
        },
        { maxRetries, retryDelay }
      )
      
      // Salvar em cache
      DashboardErrorRecovery.saveToCache(DashboardErrorRecovery['CACHE_KEY'], data)
      setRecoveryMode('normal')
      setRetryCount(0)
      
      return {
        ...data,
        is_cached: false,
        is_degraded: false,
        last_updated: new Date().toISOString()
      }
      
    } catch (error) {
      console.error('🚨 Falha ao buscar dados frescos:', error)
      setLastError(error as Error)
      setRetryCount(prev => prev + 1)
      
      // 3. Tentar cache como fallback
      const cachedData = DashboardErrorRecovery.loadFromCache<DashboardStats>(
        DashboardErrorRecovery['CACHE_KEY'],
        cacheTimeout
      )
      
      if (cachedData) {
        console.log('📦 Usando dados em cache como fallback')
        setRecoveryMode('cached')
        
        // Mostrar aviso ao usuário
        toast.warning('Usando dados em cache devido a problemas de conexão', {
          action: {
            label: 'Tentar novamente',
            onClick: () => queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() })
          }
        })
        
        return cachedData
      }
      
      // 4. Modo degradado como último recurso
      if (enableDegradedMode) {
        console.log('🟡 Ativando modo degradado')
        setRecoveryMode('degraded')
        
        toast.error('Não foi possível carregar os dados. Exibindo informações básicas.', {
          action: {
            label: 'Tentar novamente',
            onClick: () => queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() })
          }
        })
        
        return DashboardErrorRecovery.getDegradedModeData()
      }
      
      // 5. Falha total
      throw error
    }
  }, [isOffline, maxRetries, retryDelay, cacheTimeout, enableDegradedMode, enableOfflineMode, queryClient])
  
  // Query principal
  const query = useQuery({
    queryKey: queryKeys.dashboard.stats(),
    queryFn: fetchStatsWithRecovery,
    staleTime: 3 * 60 * 1000, // 3 minutos
    gcTime: 15 * 60 * 1000, // 15 minutos
    refetchOnWindowFocus: false,
    refetchOnReconnect: true,
    retry: false, // Desabilitar retry padrão, usaremos nosso próprio
    retryDelay: undefined,
  })
  
  // Função para retry manual
  const manualRetry = useCallback(() => {
    setRetryCount(0)
    setLastError(null)
    setRecoveryMode('normal')
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() })
  }, [queryClient])
  
  // Clear cache
  const clearCache = useCallback(() => {
    localStorage.removeItem(DashboardErrorRecovery['CACHE_KEY'])
    toast.success('Cache limpo com sucesso')
    queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() })
  }, [queryClient])
  
  return {
    // Dados principais
    data: query.data,
    error: query.error || lastError,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    isError: query.isError,
    
    // Estados de recovery
    recoveryMode,
    retryCount,
    networkStatus,
    isOffline,
    
    // Ações
    refetch: query.refetch,
    manualRetry,
    clearCache,
    
    // Flags úteis
    isUsingCache: recoveryMode === 'cached' || query.data?.is_cached,
    isDegraded: recoveryMode === 'degraded' || query.data?.is_degraded,
    canRetry: retryCount < maxRetries,
    
    // Informações de debug
    debugInfo: {
      queryKey: queryKeys.dashboard.stats(),
      lastErrorMessage: lastError?.message,
      cacheAge: query.data?.last_updated 
        ? Date.now() - new Date(query.data.last_updated).getTime() 
        : null,
      networkRTT: networkStatus.rtt,
      connectionType: networkStatus.effectiveType
    }
  }
}
