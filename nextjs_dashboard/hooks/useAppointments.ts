import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/react-query'
import { toast } from 'sonner'
// ✅ CF-001: Using auto-generated types from OpenAPI
import type {
  Appointment,
  AppointmentCreateRequest,
  AppointmentUpdateRequest,
  AppointmentsListResponse
} from '@/types/api-cf001'
// TODO: CF-001 - Remove normalizers after full migration
import { normalizeAppointment, normalizeAppointments, toAppointmentCreateData, toAppointmentUpdateData } from '@/lib/appointment-normalizer'

// Simulando serviço de API - você pode substituir pela implementação real
const api = {
  async getAppointments(filters: {
    limit?: number
    page?: number
    status?: string
    date_from?: string
    date_to?: string
    user_id?: number
  }): Promise<AppointmentsListResponse> {
    const params = new URLSearchParams()

    if (filters.limit) params.append('limit', filters.limit.toString())
    if (filters.page) params.append('page', filters.page.toString())
    if (filters.status) params.append('status', filters.status)
    if (filters.date_from) params.append('date_from', filters.date_from)
    if (filters.date_to) params.append('date_to', filters.date_to)
    if (filters.user_id) params.append('user_id', filters.user_id.toString())

    const response = await fetch(`/api/appointments?${params}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
        // ✅ CF-001: HttpOnly cookies used instead of Authorization header
      }
    })

    if (!response.ok) {
      throw new Error(`Erro ao buscar agendamentos: ${response.statusText}`)
    }

    const data = await response.json()
    // ✅ Normalizar dados para garantir compatibilidade
    if (data.data) {
      data.data = normalizeAppointments(data.data)
    }

    return data
  },

  async getAppointment(id: number): Promise<Appointment> {
    const response = await fetch(`/api/appointments/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error('Erro ao buscar agendamento: ' + response.statusText)
    }

    const data = await response.json()
    // ✅ Normalizar dados para garantir compatibilidade
    const normalized = normalizeAppointment(data)
    return {
      ...normalized,
      userId: normalized.user_id ?? data.user_id,
      businessId: normalized.business_id ?? data.businessId ?? data.business_id,
      createdAt: normalized.created_at ?? data.createdAt ?? data.created_at,
    }
  },

  async createAppointment(data: AppointmentCreateRequest): Promise<Appointment> {
    // ✅ Converter para formato brasileiro antes de enviar
    const normalizedData = toAppointmentCreateData({
      ...data,
      service_id: data.service_id == null ? undefined : data.service_id,
      notes: data.notes == null ? undefined : data.notes
    })

    try {
      const response = await fetch('/api/appointments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(normalizedData)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Erro ao criar agendamento: ${response.statusText}`)
      }

      const result = await response.json()
      // ✅ Normalizar resposta
      const normalized = normalizeAppointment(result)
      return {
        ...normalized,
        userId: normalized.user_id ?? result.user_id,
        businessId: normalized.business_id ?? result.businessId ?? result.business_id,
        createdAt: normalized.created_at ?? result.createdAt ?? result.created_at,
      }
    } catch (error) {
      // Garantir que sempre retorna um valor ou lança erro
      throw error
    }
  },

  async updateAppointment(id: number, data: AppointmentUpdateRequest): Promise<Appointment> {
    // ✅ Converter para formato brasileiro antes de enviar
    const sanitizedData = {
      ...data,
      price: data.price == null ? undefined : data.price,
      duration_minutes: data.duration_minutes == null ? undefined : data.duration_minutes,
      date_time: data.date_time == null ? undefined : data.date_time,
      status: data.status == null ? undefined : data.status,
      notes: data.notes == null ? undefined : data.notes,
    }
    const normalizedData = toAppointmentUpdateData(sanitizedData)

    const response = await fetch(`/api/appointments/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(normalizedData)
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || `Erro ao atualizar agendamento: ${response.statusText}`)
    }

    const result = await response.json()
    // ✅ Normalizar resposta
    const normalized = normalizeAppointment(result)
    return {
      ...normalized,
      userId: normalized.user_id ?? result.user_id,
      businessId: normalized.business_id ?? result.businessId ?? result.business_id,
      createdAt: normalized.created_at ?? result.createdAt ?? result.created_at,
    }
  },

  async deleteAppointment(id: number): Promise<{ message: string; id: number }> {
    const response = await fetch(`/api/appointments/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
        // ✅ REMOVIDO: Authorization header inseguro
      }
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || `Erro ao excluir agendamento: ${response.statusText}`)
    }

    return response.json()
  }
}

// Hooks para agendamentos
export function useAppointments(filters: {
  limit?: number
  page?: number
  status?: string
  date_from?: string
  date_to?: string
  user_id?: number
} = {}) {
  return useQuery({
    queryKey: queryKeys.appointments.list(filters),
    queryFn: () => api.getAppointments(filters),
    staleTime: 2 * 60 * 1000, // 2 minutos
    gcTime: 5 * 60 * 1000, // 5 minutos
    refetchOnWindowFocus: false,
    retry: (failureCount, error: any) => {
      // Não retry em erros de autenticação
      if (error?.status === 401 || error?.status === 403) {
        return false
      }
      return failureCount < 2
    }
  })
}

export function useAppointment(id: number, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.appointments.detail(id),
    queryFn: () => api.getAppointment(id),
    enabled: enabled && !!id,
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 10 * 60 * 1000, // 10 minutos
  })
}

export function useCreateAppointment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.createAppointment,
    onMutate: async (newAppointment) => {
      // Cancelar queries em andamento
      await queryClient.cancelQueries({ queryKey: queryKeys.appointments.lists() })

      // Optimistic update seria implementado aqui se necessário
      return { newAppointment }
    },
    onSuccess: (data) => {
      // Invalidar listas de agendamentos
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })

      // Adicionar aos dados existentes
      queryClient.setQueryData(
        queryKeys.appointments.detail(data.id),
        data
      )

      // Invalidar dashboard stats se existir
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() })

      toast.success('Agendamento criado com sucesso!')
    },
    onError: (error: any, variables, context) => {
      // Reverter optimistic update se implementado
      console.error('Erro ao criar agendamento:', error)
      toast.error(error.message || 'Erro ao criar agendamento')
    },
    onSettled: () => {
      // Sempre invalidar após a operação
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })
    }
  })
}

export function useUpdateAppointment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number, data: AppointmentUpdateRequest }) =>
      api.updateAppointment(id, data),
    onMutate: async ({ id, data }) => {
      // Cancelar queries em andamento
      await queryClient.cancelQueries({ queryKey: queryKeys.appointments.detail(id) })

      // Snapshot do valor anterior
      const previousAppointment = queryClient.getQueryData(queryKeys.appointments.detail(id))

      // Optimistic update
      queryClient.setQueryData(queryKeys.appointments.detail(id), (old: any) => ({
        ...old,
        ...data,
        updated_at: new Date().toISOString()
      }))

      return { previousAppointment, id }
    },
    onSuccess: (data, variables) => {
      // Atualizar cache específico com dados do servidor
      queryClient.setQueryData(
        queryKeys.appointments.detail(variables.id),
        data
      )

      // Invalidar listas para refletir mudanças
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })

      // Invalidar dashboard se status mudou
      if (variables.data.status) {
        queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() })
      }

      toast.success('Agendamento atualizado!')
    },
    onError: (error: any, variables, context) => {
      // Reverter optimistic update
      if (context?.previousAppointment) {
        queryClient.setQueryData(
          queryKeys.appointments.detail(context.id),
          context.previousAppointment
        )
      }

      console.error('Erro ao atualizar agendamento:', error)
      toast.error(error.message || 'Erro ao atualizar agendamento')
    },
    onSettled: (data, error, variables) => {
      // Sempre invalidar após a operação
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.detail(variables.id) })
    }
  })
}

export function useDeleteAppointment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: api.deleteAppointment,
    onMutate: async (id) => {
      // Cancelar queries em andamento
      await queryClient.cancelQueries({ queryKey: queryKeys.appointments.detail(id) })
      await queryClient.cancelQueries({ queryKey: queryKeys.appointments.lists() })

      // Snapshot dos dados para rollback
      const previousAppointment = queryClient.getQueryData(queryKeys.appointments.detail(id))

      // Optimistic update - remover das listas
      queryClient.setQueriesData(
        { queryKey: queryKeys.appointments.lists() },
        (old: any) => {
          if (!old) return old
          return {
            ...old,
            appointments: old.appointments?.filter((apt: Appointment) => apt.id !== id) || [],
            total: Math.max(0, (old.total || 1) - 1)
          }
        }
      )

      return { previousAppointment, id }
    },
    onSuccess: (data, id) => {
      // Remover do cache individual
      queryClient.removeQueries({ queryKey: queryKeys.appointments.detail(id) })

      // Invalidar listas para garantir consistência
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })

      // Invalidar dashboard stats
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats() })

      toast.success('Agendamento excluído com sucesso!')
    },
    onError: (error: any, id, context) => {
      // Reverter optimistic update
      if (context?.previousAppointment) {
        queryClient.setQueryData(
          queryKeys.appointments.detail(id),
          context.previousAppointment
        )
      }

      // Invalidar listas para reverter mudanças
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })

      console.error('Erro ao excluir agendamento:', error)
      toast.error(error.message || 'Erro ao excluir agendamento')
    }
  })
}

// Hook para prefetch de agendamentos
export function usePrefetchAppointment() {
  const queryClient = useQueryClient()

  return (id: number) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.appointments.detail(id),
      queryFn: () => api.getAppointment(id),
      staleTime: 5 * 60 * 1000, // 5 minutos
    })
  }
}

// Hook para invalidação manual
export function useInvalidateAppointments() {
  const queryClient = useQueryClient()

  return {
    invalidateAll: () => queryClient.invalidateQueries({ queryKey: queryKeys.appointments.all }),
    invalidateLists: () => queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() }),
    invalidateDetail: (id: number) => queryClient.invalidateQueries({ queryKey: queryKeys.appointments.detail(id) }),
  }
}
