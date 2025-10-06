/**
 * 🎣 Hook para gerenciar dados de clientes
 * Conecta com a API real do PostgreSQL
 */

import { useState, useEffect, useCallback } from 'react';
import type { Client } from '@/types/api';
import { debugLog } from '@/lib/debug';

export interface ClientsResponse {
  success: boolean;
  clients: Client[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

export interface UseClientsOptions {
  search?: string;
  status?: string;
  sortBy?: string;
  limit?: number;
  offset?: number;
  autoFetch?: boolean;
}

export interface UseClientsReturn {
  clients: Client[];
  loading: boolean;
  error: string | null;
  pagination: ClientsResponse['pagination'] | null;
  refetch: () => Promise<void>;
  createClient: (clientData: { name: string; email: string; phone: string }) => Promise<Client | null>;
  updateFilters: (filters: Partial<UseClientsOptions>) => void;
}

export function useClients(options: UseClientsOptions = {}): UseClientsReturn {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<ClientsResponse['pagination'] | null>(null);
  const [filters, setFilters] = useState<UseClientsOptions>({
    search: '',
    status: 'all',
    sortBy: 'name',
    limit: 50,
    offset: 0,
    autoFetch: true,
    ...options
  });

  const fetchClients = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const searchParams = new URLSearchParams();
      
      if (filters.search) searchParams.set('search', filters.search);
      if (filters.status && filters.status !== 'all') searchParams.set('status', filters.status);
      if (filters.sortBy) searchParams.set('sortBy', filters.sortBy);
      if (filters.limit) searchParams.set('limit', filters.limit.toString());
      if (filters.offset) searchParams.set('offset', filters.offset.toString());

      const response = await fetch(`/api/clients?${searchParams.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      const data: ClientsResponse = await response.json();

      if (data.success) {
        setClients(data.clients);
        setPagination(data.pagination);
      } else {
        throw new Error('Falha ao carregar clientes');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      debugLog.error('Erro ao buscar clientes:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const createClient = useCallback(async (clientData: { name: string; email: string; phone: string }): Promise<Client | null> => {
    try {
      const response = await fetch('/api/clients', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(clientData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Erro ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        // Recarregar a lista de clientes
        await fetchClients();
        return data.client;
      } else {
        throw new Error(data.error || 'Falha ao criar cliente');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      debugLog.error('Erro ao criar cliente:', err);
      return null;
    }
  }, [fetchClients]);

  const updateFilters = useCallback((newFilters: Partial<UseClientsOptions>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters,
      offset: 0 // Reset offset when filters change
    }));
  }, []);

  // Auto-fetch quando os filtros mudarem
  useEffect(() => {
    if (filters.autoFetch !== false) {
      fetchClients();
    }
  }, [fetchClients, filters.autoFetch]);

  return {
    clients,
    loading,
    error,
    pagination,
    refetch: fetchClients,
    createClient,
    updateFilters
  };
}