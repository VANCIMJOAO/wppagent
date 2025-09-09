'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useToast } from '../components/error-boundaries/AdvancedToastProvider';
import { useErrorHandler } from '../components/error-boundaries/ErrorProvider';

// Types
interface ApiCallOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: ApiError) => void;
  retryAttempts?: number;
  retryDelay?: number;
  showToasts?: boolean;
  showErrorBoundary?: boolean;
  timeout?: number;
  debounceMs?: number;
  useCache?: boolean; // Renamed to avoid conflict with RequestInit.cache
  cacheTimeout?: number;
  optimistic?: boolean;
  rollback?: () => void;
  transform?: (data: any) => any;
  validate?: (data: any) => boolean | string;
}

interface ApiError extends Error {
  status?: number;
  endpoint?: string;
  data?: any;
  isRetryable?: boolean;
}

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  success: boolean;
  retryCount: number;
  lastUpdated: number | null;
}

interface CachedResponse<T> {
  data: T;
  timestamp: number;
  endpoint: string;
}

// Cache implementation
class ApiCache {
  private cache = new Map<string, CachedResponse<any>>();
  private defaultTimeout = 5 * 60 * 1000; // 5 minutes

  set<T>(key: string, data: T, endpoint: string, timeout?: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      endpoint
    });

    // Auto cleanup
    setTimeout(() => {
      this.cache.delete(key);
    }, timeout || this.defaultTimeout);
  }

  get<T>(key: string, maxAge?: number): T | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    const age = Date.now() - cached.timestamp;
    const maxAgeMs = maxAge || this.defaultTimeout;

    if (age > maxAgeMs) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  invalidate(pattern?: string): void {
    if (!pattern) {
      this.cache.clear();
      return;
    }

    const regex = new RegExp(pattern);
    const keysToDelete: string[] = [];
    
    this.cache.forEach((value, key) => {
      if (regex.test(key) || regex.test(value.endpoint)) {
        keysToDelete.push(key);
      }
    });

    keysToDelete.forEach(key => this.cache.delete(key));
  }

  getStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
      memory: JSON.stringify(Array.from(this.cache.entries())).length
    };
  }
}

const apiCache = new ApiCache();

// Network status detection
function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [connectionType, setConnectionType] = useState<string>('unknown');

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    const handleConnectionChange = () => {
      const connection = (navigator as any).connection;
      if (connection) {
        setConnectionType(connection.effectiveType || 'unknown');
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);
      
      const connection = (navigator as any).connection;
      if (connection) {
        connection.addEventListener('change', handleConnectionChange);
        handleConnectionChange();
      }

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        if (connection) {
          connection.removeEventListener('change', handleConnectionChange);
        }
      };
    }
  }, []);

  return { isOnline, connectionType, isSlowConnection: ['slow-2g', '2g'].includes(connectionType) };
}

// Enhanced fetch with timeout and retry logic
async function enhancedFetch(
  url: string,
  options: RequestInit = {},
  timeout = 10000
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

// Main useApi hook
export function useApi<T = any>(defaultOptions: ApiCallOptions = {}) {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
    success: false,
    retryCount: 0,
    lastUpdated: null
  });

  const { error: toastError, success: toastSuccess, loading: toastLoading, removeToast } = useToast();
  const { addApiError, addNetworkError } = useErrorHandler();
  const { isOnline, isSlowConnection } = useNetworkStatus();

  const abortControllerRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const loadingToastRef = useRef<string | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      if (loadingToastRef.current) {
        removeToast(loadingToastRef.current);
      }
    };
  }, [removeToast]);

  const createApiError = (message: string, status?: number, endpoint?: string, data?: any): ApiError => {
    const error = new Error(message) as ApiError;
    error.status = status;
    error.endpoint = endpoint;
    error.data = data;
    error.isRetryable = !status || status >= 500 || status === 408 || status === 429;
    return error;
  };

  const shouldRetry = (error: ApiError, retryCount: number, maxRetries: number): boolean => {
    if (retryCount >= maxRetries) return false;
    if (!error.isRetryable) return false;
    if (!isOnline) return false;
    return true;
  };

  const calculateRetryDelay = (retryCount: number, baseDelay = 1000): number => {
    return Math.min(baseDelay * Math.pow(2, retryCount), 10000); // Max 10s
  };

  const executeRequest = useCallback(async <TData = T>(
    endpoint: string,
    options: (RequestInit & ApiCallOptions) | ApiCallOptions = {}
  ): Promise<TData> => {
    const {
      retryAttempts = 3,
      retryDelay = 1000,
      showToasts = true,
      showErrorBoundary = false,
      timeout = isSlowConnection ? 20000 : 10000,
      useCache = false,
      cacheTimeout,
      optimistic = false,
      rollback,
      transform,
      validate,
      onSuccess,
      onError,
      debounceMs,
      ...fetchOptions
    } = { ...defaultOptions, ...options };
    
    // For caching, we need to extract method from the actual request
    const method = (fetchOptions && 'method' in fetchOptions ? fetchOptions.method : undefined) || 'GET';
    
    // Check cache first
    if (useCache && method !== 'POST' && method !== 'PUT' && method !== 'DELETE') {
      const cacheKey = `${endpoint}_${JSON.stringify(fetchOptions)}`;
      const cached = apiCache.get<TData>(cacheKey, cacheTimeout);
      if (cached) {
        setState(prev => ({ ...prev, data: cached as T, loading: false, success: true, lastUpdated: Date.now() }));
        return cached;
      }
    }

    // Abort previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    // Set loading state
    setState(prev => ({ 
      ...prev, 
      loading: true, 
      error: null, 
      success: false 
    }));

    // Show loading toast
    if (showToasts) {
      loadingToastRef.current = toastLoading(
        'Carregando...',
        `Processando solicitação para ${endpoint}`
      );
    }

    let lastError: ApiError | null = null;

    for (let attempt = 0; attempt <= retryAttempts; attempt++) {
      try {
        // Network check
        if (!isOnline) {
          throw createApiError('Sem conexão com a internet', 0, endpoint);
        }

        // Make request
        const response = await enhancedFetch(
          endpoint,
          {
            ...fetchOptions,
            signal: abortControllerRef.current.signal
          },
          timeout
        );

        // Handle response
        if (!response.ok) {
          const errorData = await response.text().then(text => {
            try { return JSON.parse(text); } catch { return { message: text }; }
          });

          throw createApiError(
            errorData.message || `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            endpoint,
            errorData
          );
        }

        // Parse response
        let data: TData;
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
          data = await response.json();
        } else {
          data = await response.text() as any;
        }

        // Transform data if provided
        if (transform) {
          data = transform(data);
        }

        // Validate data if provided
        if (validate) {
          const validation = validate(data);
          if (validation !== true) {
            throw createApiError(
              typeof validation === 'string' ? validation : 'Dados recebidos são inválidos',
              0,
              endpoint,
              data
            );
          }
        }

        // Cache successful response
        if (useCache) {
          const cacheKey = `${endpoint}_${JSON.stringify(fetchOptions)}`;
          apiCache.set(cacheKey, data, endpoint, cacheTimeout);
        }

        // Update state
        setState(prev => ({
          ...prev,
          data: data as unknown as T,
          loading: false,
          error: null,
          success: true,
          retryCount: attempt,
          lastUpdated: Date.now()
        }));

        // Remove loading toast and show success
        if (loadingToastRef.current) {
          removeToast(loadingToastRef.current);
          loadingToastRef.current = null;
        }

        if (showToasts && attempt > 0) {
          toastSuccess('Sucesso!', `Operação completada após ${attempt + 1} tentativa(s)`);
        }

        // Call success callback
        if (onSuccess) {
          onSuccess(data);
        }

        return data;

      } catch (error: any) {
        lastError = error.name === 'AbortError' ? 
          createApiError('Operação cancelada', 0, endpoint) :
          error instanceof Error ?
            createApiError(error.message, (error as ApiError).status, endpoint, (error as ApiError).data) :
            createApiError('Erro desconhecido', 0, endpoint);

        setState(prev => ({ 
          ...prev, 
          retryCount: attempt,
          error: lastError
        }));

        // Check if should retry
        if (shouldRetry(lastError, attempt, retryAttempts)) {
          const delay = calculateRetryDelay(attempt, retryDelay);
          
          if (showToasts) {
            toastError(
              'Tentando novamente...',
              `Tentativa ${attempt + 2}/${retryAttempts + 1} em ${delay}ms`,
              { duration: delay }
            );
          }

          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }

        // Max retries reached or non-retryable error
        break;
      }
    }

    // Handle final error
    setState(prev => ({ 
      ...prev, 
      loading: false, 
      error: lastError, 
      success: false 
    }));

    // Remove loading toast
    if (loadingToastRef.current) {
      removeToast(loadingToastRef.current);
      loadingToastRef.current = null;
    }

    // Show error feedback
    if (showToasts && lastError) {
      if (lastError.status) {
        addApiError(lastError.message, { 
          endpoint, 
          status: lastError.status, 
          context: lastError.data 
        });
      } else {
        addNetworkError(lastError.message);
      }
    }

    // Show error boundary if requested
    if (showErrorBoundary && lastError) {
      throw lastError;
    }

    // Call error callback
    if (onError && lastError) {
      onError(lastError);
    }

    // Rollback optimistic updates
    if (optimistic && rollback) {
      rollback();
    }

    throw lastError;
  }, [defaultOptions, isOnline, isSlowConnection, toastError, toastSuccess, toastLoading, removeToast, addApiError, addNetworkError]);

  // Debounced version of executeRequest
  const debouncedExecute = useCallback((
    endpoint: string,
    options: RequestInit & ApiCallOptions = {}
  ) => {
    const debounceMs = options.debounceMs || 0;

    if (debounceMs > 0) {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(() => {
        executeRequest(endpoint, options);
      }, debounceMs);
    } else {
      return executeRequest(endpoint, options);
    }
  }, [executeRequest]);

  // Convenience methods
  const get = useCallback((endpoint: string, options?: ApiCallOptions) => {
    const { method, ...requestOptions } = { method: 'GET', ...options };
    return debouncedExecute(endpoint, requestOptions);
  }, [debouncedExecute]);

  const post = useCallback((endpoint: string, data?: any, options?: ApiCallOptions) => {
    const { method, body, ...requestOptions } = { 
      method: 'POST', 
      body: data ? JSON.stringify(data) : undefined,
      ...options
    };
    return debouncedExecute(endpoint, requestOptions);
  }, [debouncedExecute]);

  const put = useCallback((endpoint: string, data?: any, options?: ApiCallOptions) => {
    const { method, body, ...requestOptions } = { 
      method: 'PUT', 
      body: data ? JSON.stringify(data) : undefined,
      ...options
    };
    return debouncedExecute(endpoint, requestOptions);
  }, [debouncedExecute]);

  const del = useCallback((endpoint: string, options?: ApiCallOptions) => {
    const { method, ...requestOptions } = { method: 'DELETE', ...options };
    return debouncedExecute(endpoint, requestOptions);
  }, [debouncedExecute]);

  const patch = useCallback((endpoint: string, data?: any, options?: ApiCallOptions) => {
    const { method, body, ...requestOptions } = { 
      method: 'PATCH', 
      body: data ? JSON.stringify(data) : undefined,
      ...options
    };
    return debouncedExecute(endpoint, requestOptions);
  }, [debouncedExecute]);

  // State management
  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      success: false,
      retryCount: 0,
      lastUpdated: null
    });
  }, []);

  const retry = useCallback(() => {
    if (state.error?.endpoint) {
      executeRequest(state.error.endpoint);
    }
  }, [state.error, executeRequest]);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (loadingToastRef.current) {
      removeToast(loadingToastRef.current);
      loadingToastRef.current = null;
    }
    setState(prev => ({ ...prev, loading: false }));
  }, [removeToast]);

  return {
    // State
    ...state,
    isOnline,
    isSlowConnection,

    // Methods
    execute: executeRequest,
    get,
    post,
    put,
    delete: del,
    patch,

    // Control
    reset,
    retry,
    cancel,

    // Cache control
    invalidateCache: apiCache.invalidate.bind(apiCache),
    getCacheStats: apiCache.getStats.bind(apiCache)
  };
}

// Specialized hooks
export function useQuery<T = any>(
  endpoint: string, 
  options: ApiCallOptions & { enabled?: boolean; refetchInterval?: number } = {}
) {
  const { enabled = true, refetchInterval, ...apiOptions } = options;
  const api = useApi<T>(apiOptions);

  useEffect(() => {
    if (enabled) {
      api.get(endpoint);
    }
  }, [endpoint, enabled]);

  useEffect(() => {
    if (refetchInterval && enabled) {
      const interval = setInterval(() => {
        api.get(endpoint);
      }, refetchInterval);

      return () => clearInterval(interval);
    }
  }, [endpoint, refetchInterval, enabled]);

  return api;
}

export function useMutation<T = any>(options: ApiCallOptions = {}) {
  return useApi<T>(options);
}

export default useApi;
