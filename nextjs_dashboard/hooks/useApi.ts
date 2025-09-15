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

  const request = useCallback(async (endpoint: string, requestOptions: RequestInit = {}) => {
    // Cancel previous request
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
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
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
          const apiError: ApiError = {
            name: 'ApiError',
            message: err instanceof Error ? err.message : 'Request failed',
            status: err instanceof Response ? err.status : 0,
            statusText: err instanceof Response ? err.statusText : 'Unknown error'
          };
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

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const refetch = useCallback(async () => {
    // This would need to store the last request parameters
    // For now, it's a placeholder
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
  const [error, setError] = useState<string | null>(null);

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
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
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
    kpis,
    charts,
    recentActivity,
    data,
    loading,
    error,
    fetchDashboardData,
    refetch,
    reset: () => {
      setData(null);
      setError(null);
    }
  };
}
