'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface ApiError extends Error {
  status?: number;
  statusText?: string;
  data?: any;
  endpoint?: string;
  method?: string;
  isNetworkError?: boolean;
  isTimeoutError?: boolean;
  isRetryable?: boolean;
}

interface UseApiOptions {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  baseUrl?: string;
  showToast?: boolean;
  showLoading?: boolean;
  onError?: (error: ApiError) => void;
  onSuccess?: (data: any) => void;
  requireAuth?: boolean;
}

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  request: (endpoint: string, options?: RequestInit) => Promise<void>;
  reset: () => void;
  refetch: () => Promise<void>;
  abort: () => void;
}

export function useApiEnhanced<T>(options: UseApiOptions = {}): UseApiResult<T> {
  const {
    timeout = 30000,
    retries = 3,
    retryDelay = 1000,
    baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://wppagent-production.up.railway.app',
    showToast = true,
    showLoading: showLoadingToast = false,
    onError,
    onSuccess,
    requireAuth = true
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastRequestRef = useRef<{ endpoint: string; options?: RequestInit } | null>(null);

  const createApiError = (
    message: string,
    status?: number,
    statusText?: string,
    data?: any,
    endpoint?: string,
    method?: string
  ): ApiError => {
    const error = new Error(message) as ApiError;
    error.status = status;
    error.statusText = statusText;
    error.data = data;
    error.endpoint = endpoint;
    error.method = method;
    
    // Categorize error types
    error.isNetworkError = !status || status === 0;
    error.isTimeoutError = message.includes('timeout') || message.includes('aborted');
    error.isRetryable = error.isNetworkError || error.isTimeoutError || 
                       (status !== undefined && [408, 429, 500, 502, 503, 504].includes(status));
    
    return error;
  };

  const request = useCallback(async (endpoint: string, requestOptions: RequestInit = {}) => {
    // Store last request for refetch functionality
    lastRequestRef.current = { endpoint, options: requestOptions };

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    
    setLoading(true);
    setError(null);

    const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;

    try {
      // Get auth token if required
      let authHeaders: Record<string, string> = {};
      if (requireAuth) {
        const token = localStorage.getItem('auth_token');
        if (token) {
          authHeaders.Authorization = `Bearer ${token}`;
        }
      }

      // Merge headers
      const headers = {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...(requestOptions.headers || {})
      };

      for (let attempt = 0; attempt <= retries; attempt++) {
        try {
          const timeoutId = setTimeout(() => {
            if (abortControllerRef.current) {
              abortControllerRef.current.abort();
            }
          }, timeout);

          const response = await fetch(url, {
            ...requestOptions,
            headers,
            signal: abortControllerRef.current.signal,
          });

          clearTimeout(timeoutId);

          if (!response.ok) {
            let errorData;
            try {
              errorData = await response.json();
            } catch {
              errorData = { message: response.statusText };
            }

            throw createApiError(
              errorData.message || `HTTP ${response.status}`,
              response.status,
              response.statusText,
              errorData,
              endpoint,
              requestOptions.method as string
            );
          }

          let responseData;
          try {
            responseData = await response.json();
          } catch {
            // Handle non-JSON responses
            responseData = null;
          }

          setData(responseData);
          setError(null);

          // Call success handler
          if (onSuccess) {
            onSuccess(responseData);
          }

          return;

        } catch (fetchError: any) {
          if (fetchError.name === 'AbortError') {
            const timeoutError = createApiError(
              'Request timeout',
              408,
              'Request Timeout',
              null,
              endpoint,
              requestOptions.method as string
            );
            throw timeoutError;
          }

          // If this is the last attempt or the error is not retryable, throw it
          const apiError = fetchError as ApiError;
          if (attempt === retries || !apiError.isRetryable) {
            throw apiError;
          }

          // Wait before retrying
          if (attempt < retries) {
            const delay = retryDelay * Math.pow(2, attempt);
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }
      }
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);

      // Handle specific errors
      if (apiError.status === 401) {
        localStorage.removeItem('auth_token');
        // Could redirect to login here
      }

      // Call error handler
      if (onError) {
        onError(apiError);
      }

      throw apiError;
    } finally {
      setLoading(false);
    }
  }, [
    timeout, retries, retryDelay, baseUrl, requireAuth, onError, onSuccess
  ]);

  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const refetch = useCallback(async () => {
    if (lastRequestRef.current) {
      await request(lastRequestRef.current.endpoint, lastRequestRef.current.options);
    }
  }, [request]);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return { 
    data, 
    loading, 
    error, 
    request, 
    reset,
    refetch,
    abort
  };
}

// Legacy hook - keep existing functionality but add basic error handling
export function useApi<T>(options: UseApiOptions = {}): UseApiResult<T> {
  const {
    timeout = 30000,
    retries = 3,
    retryDelay = 1000,
    baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://wppagent-production.up.railway.app'
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastRequestRef = useRef<{ endpoint: string; options?: RequestInit } | null>(null);

  const createApiError = (message: string, status?: number): ApiError => {
    const error = new Error(message) as ApiError;
    error.status = status;
    error.isRetryable = status ? [408, 429, 500, 502, 503, 504].includes(status) : true;
    return error;
  };

  const request = useCallback(async (endpoint: string, requestOptions: RequestInit = {}) => {
    lastRequestRef.current = { endpoint, options: requestOptions };

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    const timeoutId = setTimeout(() => abortControllerRef.current?.abort(), timeout);
    
    setLoading(true);
    setError(null);

    const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...requestOptions,
          signal: abortControllerRef.current.signal,
          headers: {
            'Content-Type': 'application/json',
            ...requestOptions.headers,
          },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw createApiError(`HTTP ${response.status}: ${response.statusText}`, response.status);
        }

        const result = await response.json();
        setData(result);
        setLoading(false);
        return;

      } catch (err) {
        clearTimeout(timeoutId);
        
        if (err instanceof Error && err.name === 'AbortError') {
          return; // Request was cancelled
        }

        if (attempt === retries) {
          // Last attempt failed
          const apiError = err instanceof Error 
            ? createApiError(err.message) 
            : createApiError('Request failed');
          setError(apiError);
          setLoading(false);
          return;
        }

        // Wait before retry with exponential backoff
        await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, attempt)));
      }
    }
  }, [baseUrl, retries, retryDelay, timeout]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const refetch = useCallback(async () => {
    if (lastRequestRef.current) {
      await request(lastRequestRef.current.endpoint, lastRequestRef.current.options);
    }
  }, [request]);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return { data, loading, error, request, reset, refetch, abort };
}

// Specialized hooks for common HTTP methods
export function useApiGet<T>(endpoint: string, options?: UseApiOptions) {
  const api = useApi<T>(options);
  
  const get = useCallback(() => {
    return api.request(endpoint, { method: 'GET' });
  }, [api.request, endpoint]);

  return { ...api, get };
}

export function useApiPost<T>(options?: UseApiOptions) {
  const api = useApi<T>(options);
  
  const post = useCallback((endpoint: string, body: unknown) => {
    return api.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }, [api.request]);

  return { ...api, post };
}

export function useApiPut<T>(options?: UseApiOptions) {
  const api = useApi<T>(options);
  
  const put = useCallback((endpoint: string, body: unknown) => {
    return api.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }, [api.request]);

  return { ...api, put };
}

export function useApiDelete<T>(options?: UseApiOptions) {
  const api = useApi<T>(options);
  
  const del = useCallback((endpoint: string) => {
    return api.request(endpoint, { method: 'DELETE' });
  }, [api.request]);

  return { ...api, delete: del };
}

// Hook específico para dados do dashboard
export function useDashboardData() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  
  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Simular dados do dashboard para desenvolvimento
      const mockData = {
        kpis: {
          totalClients: 150,
          totalConversations: 45,
          totalAppointments: 12,
          totalMessages: 328
        },
        charts: {
          conversationsOverTime: [],
          appointmentsByStatus: [],
          clientGrowth: []
        },
        recentActivity: [
          {
            id: 1,
            type: 'conversation',
            title: 'Nova conversa',
            description: 'Cliente João iniciou uma conversa',
            timestamp: new Date().toISOString()
          },
          {
            id: 2,
            type: 'appointment',
            title: 'Agendamento confirmado',
            description: 'Consulta com Maria confirmada',
            timestamp: new Date().toISOString()
          }
        ]
      };
      
      setData(mockData);
      return mockData;
    } catch (err) {
      const apiError = err instanceof Error 
        ? err as ApiError
        : new Error('Erro desconhecido') as ApiError;
      setError(apiError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);
  
  const refetch = useCallback(() => {
    return fetchDashboardData();
  }, [fetchDashboardData]);
  
  // Extrair dados para compatibilidade
  const kpis = data?.kpis;
  const charts = data?.charts;
  const recentActivity = data?.recentActivity;
  
  return {
    data,
    kpis,
    charts,
    recentActivity,
    loading,
    error,
    refetch
  };
}
