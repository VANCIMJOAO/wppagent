/**
 * 🔄 Hooks para Operações de Appointments com Cache Invalidation
 * ===========================================================
 * 
 * Hooks que integram operações de appointment com invalidação automática
 * de cache, garantindo consistência de dados em tempo real.
 * 
 * Funcionalidades:
 * - Mutations com invalidação automática
 * - Optimistic updates
 * - Error handling com rollback
 * - Real-time synchronization
 * 
 * Autor: Claude AI
 * Status: Implementação crítica para UX consistente
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'
import { useAppointmentOperations } from './useApiWithInvalidation'

// Usar toast nativo ou biblioteca disponível
const toast = {
  success: (message: string, options?: any) => {
    console.log('✅', message)
    // Pode ser substituído por sonner, react-toastify, ou outro
  },
  error: (message: string, options?: any) => {
    console.error('❌', message)
    // Pode ser substituído por sonner, react-toastify, ou outro
  }
}

// ===== TYPES =====

export interface AppointmentCreateData {
  user_id: number
  business_id: number
  service_id?: number
  data_agendamento: string // ✅ Nomenclatura brasileira padronizada
  status?: string
  observacoes?: string // ✅ notes → observacoes
}

export interface AppointmentUpdateData {
  data_agendamento?: string // ✅ Nomenclatura brasileira padronizada
  status?: string
  observacoes?: string // ✅ notes → observacoes
  service_id?: number
}

export interface AppointmentResponse {
  id: number
  user_id: number
  business_id: number
  service_id?: number
  data_agendamento: string // ✅ Nomenclatura brasileira padronizada
  status: string
  observacoes?: string // ✅ notes → observacoes
  user_name?: string
  user_phone?: string
  business_name?: string
  service_name?: string
  created_at: string
  updated_at: string
}

// ===== API FUNCTIONS =====

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function createAppointment(data: AppointmentCreateData): Promise<AppointmentResponse> {
  const response = await fetch(`${API_BASE}/appointments/`, {
    method: 'POST',
    credentials: 'include', // ✅ HF-002: Usar cookies seguros
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Erro ao criar agendamento')
  }
  
  return response.json()
}

async function updateAppointment(id: number, data: AppointmentUpdateData): Promise<AppointmentResponse> {
  const response = await fetch(`${API_BASE}/appointments/${id}`, {
    method: 'PUT',
    credentials: 'include', // ✅ HF-002: Usar cookies seguros
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Erro ao atualizar agendamento')
  }
  
  return response.json()
}

async function deleteAppointment(id: number): Promise<{ message: string; id: number }> {
  const response = await fetch(`${API_BASE}/appointments/${id}`, {
    method: 'DELETE',
    credentials: 'include', // ✅ HF-002: Usar cookies seguros
    headers: {
      'Content-Type': 'application/json'
    }
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Erro ao excluir agendamento')
  }
  
  return response.json()
}

// ===== CUSTOM HOOKS =====

/**
 * 🔄 Hook para criar appointments com invalidação automática
 */
export function useCreateAppointment() {
  const { onAppointmentCreated } = useAppointmentOperations()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: createAppointment,
    onMutate: async (newAppointment) => {
      // Optimistic update opcional
      console.log('🔄 Creating appointment:', newAppointment)
    },
    onSuccess: (data, variables) => {
      // Invalidar cache automaticamente
      onAppointmentCreated(data.id, {
        client_id: data.user_id,
        business_id: data.business_id
      })
      
      toast.success('Agendamento criado com sucesso!', {
        duration: 3000,
        position: 'top-right'
      })
      
      console.log('✅ Appointment created successfully:', data.id)
    },
    onError: (error: Error, variables) => {
      console.error('❌ Error creating appointment:', error)
      
      toast.error(`Erro ao criar agendamento: ${error.message}`, {
        duration: 5000,
        position: 'top-right'
      })
    }
  })
}

/**
 * 🔄 Hook para atualizar appointments com invalidação automática
 */
export function useUpdateAppointment() {
  const { onAppointmentUpdated } = useAppointmentOperations()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: AppointmentUpdateData }) => 
      updateAppointment(id, data),
    onMutate: async ({ id, data }) => {
      // Optimistic update
      console.log(`🔄 Updating appointment ${id}:`, data)
      
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['appointment-detail', id] })
      
      // Snapshot current value
      const previousAppointment = queryClient.getQueryData(['appointment-detail', id])
      
      // Optimistically update
      if (previousAppointment) {
        queryClient.setQueryData(['appointment-detail', id], (old: any) => ({
          ...old,
          ...data,
          updated_at: new Date().toISOString()
        }))
      }
      
      return { previousAppointment, id }
    },
    onSuccess: (updatedAppointment, { id }) => {
      // Invalidar cache automaticamente
      onAppointmentUpdated(id, {
        client_id: updatedAppointment.user_id,
        business_id: updatedAppointment.business_id
      })
      
      toast.success('Agendamento atualizado com sucesso!', {
        duration: 3000,
        position: 'top-right'
      })
      
      console.log('✅ Appointment updated successfully:', id)
    },
    onError: (error: Error, { id }, context) => {
      // Rollback optimistic update
      if (context?.previousAppointment) {
        queryClient.setQueryData(['appointment-detail', id], context.previousAppointment)
      }
      
      console.error('❌ Error updating appointment:', error)
      
      toast.error(`Erro ao atualizar agendamento: ${error.message}`, {
        duration: 5000,
        position: 'top-right'
      })
    }
  })
}

/**
 * 🔄 Hook para excluir appointments com invalidação automática
 */
export function useDeleteAppointment() {
  const { onAppointmentDeleted } = useAppointmentOperations()
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: deleteAppointment,
    onMutate: async (appointmentId) => {
      console.log(`🗑️ Deleting appointment ${appointmentId}`)
      
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['appointment-detail', appointmentId] })
      
      // Snapshot current value
      const previousAppointment = queryClient.getQueryData(['appointment-detail', appointmentId])
      
      // Optimistically remove from lists
      queryClient.setQueriesData(
        { queryKey: ['appointments'] },
        (old: any) => {
          if (!old?.appointments) return old
          
          return {
            ...old,
            appointments: old.appointments.filter((apt: any) => apt.id !== appointmentId),
            total: Math.max(0, old.total - 1)
          }
        }
      )
      
      return { previousAppointment, appointmentId }
    },
    onSuccess: (result, appointmentId, context) => {
      // Extrair informações para invalidation
      const appointment = context?.previousAppointment as AppointmentResponse
      
      // Invalidar cache automaticamente
      onAppointmentDeleted(appointmentId, {
        client_id: appointment?.user_id,
        business_id: appointment?.business_id
      })
      
      toast.success('Agendamento excluído com sucesso!', {
        duration: 3000,
        position: 'top-right'
      })
      
      console.log('✅ Appointment deleted successfully:', appointmentId)
    },
    onError: (error: Error, appointmentId, context) => {
      // Rollback optimistic updates
      if (context?.previousAppointment) {
        queryClient.setQueryData(['appointment-detail', appointmentId], context.previousAppointment)
        
        // Restore in lists (mais complexo, deixamos o refetch fazer o trabalho)
        queryClient.invalidateQueries({ queryKey: ['appointments'] })
      }
      
      console.error('❌ Error deleting appointment:', error)
      
      toast.error(`Erro ao excluir agendamento: ${error.message}`, {
        duration: 5000,
        position: 'top-right'
      })
    }
  })
}

/**
 * 🔄 Hook para operações em lote de appointments
 */
export function useBulkAppointmentOperations() {
  const { onAppointmentUpdated, onAppointmentDeleted } = useAppointmentOperations()
  const queryClient = useQueryClient()
  
  const bulkDelete = useMutation({
    mutationFn: async (appointmentIds: number[]) => {
      const results = await Promise.allSettled(
        appointmentIds.map(id => deleteAppointment(id))
      )
      
      return results
    },
    onSuccess: (results, appointmentIds) => {
      // Invalidar cache para todos os appointments afetados
      appointmentIds.forEach(id => {
        onAppointmentDeleted(id)
      })
      
      const successful = results.filter(r => r.status === 'fulfilled').length
      const failed = results.filter(r => r.status === 'rejected').length
      
      if (successful > 0) {
        toast.success(`${successful} agendamento(s) excluído(s) com sucesso!`)
      }
      
      if (failed > 0) {
        toast.error(`Falha ao excluir ${failed} agendamento(s)`)
      }
    },
    onError: (error) => {
      console.error('❌ Error in bulk delete:', error)
      toast.error('Erro na exclusão em lote')
    }
  })
  
  const bulkUpdateStatus = useMutation({
    mutationFn: async ({ ids, status }: { ids: number[]; status: string }) => {
      const results = await Promise.allSettled(
        ids.map(id => updateAppointment(id, { status }))
      )
      
      return results
    },
    onSuccess: (results, { ids, status }) => {
      // Invalidar cache para todos os appointments afetados
      ids.forEach(id => {
        onAppointmentUpdated(id)
      })
      
      const successful = results.filter(r => r.status === 'fulfilled').length
      
      toast.success(`${successful} agendamento(s) atualizado(s) para '${status}'`)
    },
    onError: (error) => {
      console.error('❌ Error in bulk update:', error)
      toast.error('Erro na atualização em lote')
    }
  })
  
  return {
    bulkDelete,
    bulkUpdateStatus
  }
}

/**
 * 🔄 Hook para sincronizar appointment específico com servidor
 */
export function useAppointmentSync() {
  const queryClient = useQueryClient()
  
  const syncAppointment = useCallback(async (appointmentId: number) => {
    try {
      // Force refetch do appointment
      await queryClient.refetchQueries({ 
        queryKey: ['appointment-detail', appointmentId],
        type: 'active'
      })
      
      console.log(`🔄 Appointment ${appointmentId} synced with server`)
      return true
      
    } catch (error) {
      console.error(`❌ Failed to sync appointment ${appointmentId}:`, error)
      return false
    }
  }, [queryClient])
  
  const syncAllAppointments = useCallback(async () => {
    try {
      // Force refetch de todas as listas de appointments
      await queryClient.refetchQueries({ 
        queryKey: ['appointments'],
        type: 'active'
      })
      
      console.log('🔄 All appointments synced with server')
      return true
      
    } catch (error) {
      console.error('❌ Failed to sync appointments:', error)
      return false
    }
  }, [queryClient])
  
  return {
    syncAppointment,
    syncAllAppointments
  }
}
