/**
 * Hook para gerenciar dados de clientes com Loading States
 * BUG-006: Implementar Loading States
 * ATUALIZADO: Usando dados reais da API
 */

import { useState, useEffect, useCallback } from 'react'
import { useApiGet } from '@/hooks/useApi'
import { Client, PaginatedResponse } from '@/types/api'

export interface ClientsFilters {
  search?: string;
  status?: 'all' | 'active' | 'inactive' | 'new' | 'vip';
  page?: number;
  per_page?: number;
}

export function useClients(filters: ClientsFilters = {}) {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  
  const fetchClients = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Construir parâmetros de query
      const params = new URLSearchParams()
      if (filters.search) params.append('search', filters.search)
      if (filters.status && filters.status !== 'all') params.append('status', filters.status)
      if (filters.page) params.append('page', filters.page.toString())
      if (filters.per_page) params.append('per_page', filters.per_page.toString())
      
      const queryString = params.toString()
      const endpoint = `/api/proxy/clients${queryString ? `?${queryString}` : ''}`
      
      // Fazer requisição real para o backend
      const response = await fetch(endpoint, {
        headers: {
          'Content-Type': 'application/json',
          // Tentar obter token do localStorage se disponível
          ...(typeof window !== 'undefined' && null // ✅ REMOVIDO: Token inseguro 
            ? { 'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}` }
            : {})
        }
      })
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Erro ao carregar clientes')
      }
      
      // Transformar dados do backend para o formato esperado
      const transformedClients: Client[] = (data.clients || data.data || []).map((client: any) => ({
        id: client.id,
        nome: client.nome || client.name || '',
        telefone: client.telefone || client.phone || '',
        email: client.email || '',
        created_at: client.created_at || client.createdAt || new Date().toISOString(),
        updated_at: client.updated_at || client.updatedAt,
        total_conversations: client.total_conversations || client.totalConversations || 0,
        total_messages: client.total_messages || client.totalMessages || 0,
        total_appointments: client.total_appointments || client.totalAppointments || 0,
        confirmed_appointments: client.confirmed_appointments || client.confirmedAppointments || 0,
        cancelled_appointments: client.cancelled_appointments || client.cancelledAppointments || 0,
        total_spent: client.total_spent || client.totalSpent || 0,
        last_contact: client.last_contact || client.lastContact
      }))
      
      setClients(transformedClients)
      setTotal(data.total || data.pagination?.total || transformedClients.length)
    } catch (err) {
      console.error('Erro ao buscar clientes:', err)
      setError(err instanceof Error ? err.message : 'Erro ao carregar clientes')
      
      // Fallback com dados vazios em caso de erro
      setClients([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [filters])
  
  useEffect(() => {
    fetchClients()
  }, [fetchClients])
  
  return {
    clients,
    loading,
    error,
    total,
    refetch: fetchClients,
    reset: () => {
      setClients([])
      setError(null)
    }
  }
}

// Hook para estatísticas de clientes - dados reais
export function useClientStats() {
  const [stats, setStats] = useState<{
    total: number;
    active: number;
    new: number;
    vip: number;
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true)
      setError(null)
      
      try {
        // Buscar estatísticas reais do backend
        const response = await fetch('/api/proxy/clients/stats')
        const data = await response.json()
        
        if (!response.ok) {
          throw new Error(data.error || 'Erro ao carregar estatísticas')
        }
        
        // Transformar dados do backend
        setStats({
          total: data.total_clients || data.total || 0,
          active: data.active_clients || data.active || 0,
          new: data.new_clients || data.new_this_month || 0,
          vip: data.vip_clients || data.vip || 0
        })
      } catch (err) {
        console.error('Erro ao buscar stats de clientes:', err)
        setError(err instanceof Error ? err.message : 'Erro ao carregar estatísticas')
        
        // Fallback com dados vazios
        setStats({
          total: 0,
          active: 0,
          new: 0,
          vip: 0
        })
      } finally {
        setLoading(false)
      }
    }
    
    fetchStats()
  }, [])
  
  return { stats, loading, error }
}
