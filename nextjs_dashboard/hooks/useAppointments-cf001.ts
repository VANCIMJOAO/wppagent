/**
 * 🚀 CF-001: Updated useAppointments Hook 
 * ========================================
 * 
 * ✅ Uses auto-generated types from export function useAppointments(filters: {
  limit?: number
  page?: number
  status?: string
  date_from?: string
  date_to?: string
  user_id?: number
} = {}) {
  return useQuery({
    queryKey: queryKeys.appointments.list(filters),
    queryFn: () => appointmentApi.getAppointments(filters),
    // ✅ CF-001: Return type is automatically inferred as AppointmentsListResponse
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30 seconds
  })
}✅ Full type safety guaranteed
 * ✅ camelCase fields from backend aliases
 * ✅ Eliminates manual type maintenance
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '../lib/react-query'
import { toast } from 'sonner'
// ✅ CF-001: Using auto-generated types from OpenAPI
import type { 
  Appointment, 
  AppointmentCreateRequest, 
  AppointmentUpdateRequest,
  AppointmentsListResponse 
} from '../types/api-cf001'

// ===============================================
// 🔧 API SERVICE - CF001 COMPATIBLE
// ===============================================

const appointmentApi = {
  /**
   * 📅 Get Appointments with Filters
   * ✅ CF-001: Uses generated AppointmentsListResponse type
   */
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
      },
      credentials: 'include' // ✅ Include cookies for auth
    })
    
    if (!response.ok) {
      throw new Error(`Erro ao buscar agendamentos: ${response.statusText}`)
    }
    
    return response.json()
  },

  /**
   * 📅 Create Appointment  
   * ✅ CF-001: Uses generated AppointmentCreateRequest type
   */
  async createAppointment(data: AppointmentCreateRequest): Promise<Appointment> {
    const response = await fetch('/api/appointments', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include', // ✅ Include cookies for auth
      body: JSON.stringify(data)
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || `Erro ao criar agendamento: ${response.statusText}`)
    }
    
    return response.json()
  },

  /**
   * 📅 Update Appointment
   * ✅ CF-001: Uses generated AppointmentUpdateRequest type
   */
  async updateAppointment(id: number, data: AppointmentUpdateRequest): Promise<Appointment> {
    const response = await fetch(`/api/appointments/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include', // ✅ Include cookies for auth
      body: JSON.stringify(data)
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || `Erro ao atualizar agendamento: ${response.statusText}`)
    }
    
    return response.json()
  },

  /**
   * 📅 Delete Appointment
   */
  async deleteAppointment(id: number): Promise<{ message: string; id: number }> {
    const response = await fetch(`/api/appointments/${id}`, {
      method: 'DELETE',
      credentials: 'include' // ✅ Include cookies for auth
    })
    
    if (!response.ok) {
      throw new Error(`Erro ao deletar agendamento: ${response.statusText}`)
    }
    
    return response.json()
  }
}

// ===============================================
// 🪝 REACT QUERY HOOKS - CF001 TYPES
// ===============================================

/**
 * 📋 Hook para listar agendamentos
 * ✅ CF-001: Uses Appointment[] with proper camelCase fields
 */
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
    queryFn: () => appointmentApi.getAppointments(filters),
    // ✅ CF-001: Return type is automatically inferred as AppointmentsListResponse
    refetchOnWindowFocus: false,
    staleTime: 30000, // 30 seconds
  })
}

/**
 * 📝 Hook para criar agendamento
 * ✅ CF-001: Uses AppointmentCreateRequest type
 */
export function useCreateAppointment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: AppointmentCreateRequest) => appointmentApi.createAppointment(data),
    onSuccess: (data: Appointment) => {
      // ✅ CF-001: data is properly typed as Appointment with camelCase fields
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })
      toast.success(`Agendamento criado: ${data.clientName || 'Cliente'}`)
    },
    onError: (error: Error) => {
      toast.error(`Erro ao criar agendamento: ${error.message}`)
    }
  })
}

/**
 * ✏️ Hook para atualizar agendamento
 * ✅ CF-001: Uses AppointmentUpdateRequest type
 */
export function useUpdateAppointment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AppointmentUpdateRequest }) => 
      appointmentApi.updateAppointment(id, data),
    onSuccess: (data: Appointment) => {
      // ✅ CF-001: data is properly typed with camelCase fields  
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.detail(data.id) })
      toast.success(`Agendamento atualizado: ${data.clientName || 'Cliente'}`)
    },
    onError: (error: Error) => {
      toast.error(`Erro ao atualizar agendamento: ${error.message}`)
    }
  })
}

/**
 * 🗑️ Hook para deletar agendamento
 */
export function useDeleteAppointment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => appointmentApi.deleteAppointment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.appointments.lists() })
      toast.success('Agendamento deletado com sucesso')
    },
    onError: (error: Error) => {
      toast.error(`Erro ao deletar agendamento: ${error.message}`)
    }
  })
}

// ===============================================
// 📊 CF001 VALIDATION & METADATA
// ===============================================

/**
 * ✅ CF-001 Type Validation Helper
 * Demonstrates that generated types have proper camelCase fields
 */
export function validateCF001Types() {
  const sampleAppointment: Appointment = {
    id: 1,
    userId: 1, // ✅ camelCase from backend user_id
    businessId: 1, // ✅ camelCase from backend business_id  
    serviceId: 1, // ✅ camelCase from backend service_id
    dateTime: '2025-09-15T10:00:00Z', // ✅ camelCase from backend date_time
    durationMinutes: 60, // ✅ camelCase from backend duration_minutes
    createdAt: '2025-09-14T10:00:00Z', // ✅ camelCase from backend created_at
    status: 'agendado',
    clientName: 'João Silva', // ✅ camelCase from backend client_name
    serviceName: 'Corte de Cabelo' // ✅ camelCase from backend service_name
  }
  
  console.log('✅ CF-001 Types validated:', sampleAppointment)
  return sampleAppointment
}

/**
 * 📋 CF-001 Migration Status
 */
export const CF001_MIGRATION_STATUS = {
  types_generated: '✅ Complete',
  hooks_updated: '✅ Complete', 
  camelCase_fields: '✅ Complete',
  api_calls: '✅ Complete',
  auth_cookies: '✅ Complete',
  legacy_removed: '🔄 In Progress',
  testing_needed: '⏳ Pending'
} as const