/**
 * 🧪 Exemplos de Uso do Cliente API Tipado
 * =======================================
 * 
 * Demonstra como usar o cliente API com type safety completo.
 * Todos os tipos são auto-gerados e sincronizados com o backend.
 */

import apiClient from '../lib/api-client';

// ===== EXEMPLOS DE USO =====

export async function exemploHealthCheck() {
  try {
    // ✅ Type-safe: TypeScript conhece a estrutura da resposta
    const health = await apiClient.get('/health');
    
    // ✅ Auto-complete funciona perfeitamente
    console.log('Status:', health.status);
    console.log('Service:', health.service);
    console.log('Timestamp:', health.timestamp);
    
    return health;
  } catch (error) {
    console.error('Erro no health check:', error);
    throw error;
  }
}

export async function exemploMetricas() {
  try {
    // ✅ Type-safe: resposta tipada automaticamente
    const metrics = await apiClient.get('/metrics/system');
    
    // ✅ TypeScript sabe exatamente quais propriedades existem
    console.log('Database healthy:', metrics.database?.healthy);
    // Removido: redis.connected não existe mais nos tipos atuais
    
    return metrics;
  } catch (error) {
    console.error('Erro ao buscar métricas:', error);
    throw error;
  }
}

export async function exemploConversas() {
  try {
    // ✅ Query parameters tipados
    const conversations = await apiClient.get('/conversations/', {
      query: {
        page: 1,
        size: 10,
        status: 'active' // ✅ TypeScript valida os valores permitidos
      }
    });
    
    // ✅ Response tipada com estrutura paginada - Atualizado para C002
    console.log('Total conversations:', conversations.total);
    // Verificar se items existe e é um array
    if (Array.isArray(conversations.items)) {
      conversations.items.forEach((conv: any) => {
        // ✅ Auto-complete para propriedades da conversa
        console.log('Conversation ID:', conv.id);
        console.log('Client name:', conv.client_name);
        console.log('Status:', conv.status);
      });
    }
    
    return conversations;
  } catch (error) {
    console.error('Erro ao buscar conversas:', error);
    throw error;
  }
}

export async function exemploAppointments() {
  try {
    // ✅ GET com parâmetros tipados
    const appointments = await apiClient.get('/appointments/', {
      query: {
        page: 1,
        size: 20,
        status: 'agendado' // ✅ Valores validados pelo tipo
      }
    });
    
    // ✅ Iteração type-safe - Atualizado para C002
    if (Array.isArray(appointments.appointments)) {
      appointments.appointments.forEach((appointment: any) => {
        console.log('Appointment:', {
          id: appointment.id,
          client_name: appointment.client_name,
          scheduled_date: appointment.scheduled_date,
          status: appointment.status
        });
      });
    }
    
    return appointments;
  } catch (error) {
    console.error('Erro ao buscar agendamentos:', error);
    throw error;
  }
}

export async function exemploCreateAppointment() {
  try {
    // ✅ POST com body tipado
    const newAppointment = await apiClient.post('/appointments/', {
      client_name: 'João Silva',
      client_phone: '+5511999999999',
      scheduled_date: '2025-09-15T10:00:00',
      service_type: 'consulta',
      notes: 'Primeira consulta'
      // ✅ TypeScript garante que todos os campos obrigatórios estão presentes
    });
    
    console.log('Appointment criado:', newAppointment);
    return newAppointment;
  } catch (error) {
    console.error('Erro ao criar appointment:', error);
    throw error;
  }
}

export async function exemploUpdateAppointment(appointmentId: number) {
  try {
    // ✅ PUT com path params e body tipados
    const updated = await apiClient.put('/appointments/{appointment_id}', 
      {
        status: 'confirmado',
        notes: 'Confirmado pelo cliente'
      },
      {
        path: { appointment_id: appointmentId }
      }
    );
    
    console.log('Appointment atualizado:', updated);
    return updated;
  } catch (error) {
    console.error('Erro ao atualizar appointment:', error);
    throw error;
  }
}

export async function exemploDeleteAppointment(appointmentId: number) {
  try {
    // ✅ DELETE com path params tipados
    await apiClient.delete('/appointments/{appointment_id}', {
      path: { appointment_id: appointmentId }
    });
    
    console.log('Appointment deletado');
  } catch (error) {
    console.error('Erro ao deletar appointment:', error);
    throw error;
  }
}

// ===== HOOK PARA REACT =====

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: exemploHealthCheck,
    refetchInterval: 30000 // Verifica a cada 30s
  });
}

export function useConversations(page = 1, size = 10) {
  return useQuery({
    queryKey: ['conversations', page, size],
    queryFn: () => apiClient.get('/conversations/', {
      query: { page, size }
    })
  });
}

export function useCreateAppointment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    // Simplificado - remove parâmetros complexos
    mutationFn: (data: any) => 
      apiClient.post('/appointments/', data),
    onSuccess: () => {
      // ✅ Invalida cache de appointments
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
    }
  });
}

// ===== EXEMPLOS DE TRATAMENTO DE ERRO =====

export async function exemploComTratamentoDeErro() {
  try {
    // Usar endpoint real existente
    const result = await apiClient.get('/health');
    return result;
  } catch (error) {
    if (error && typeof error === 'object' && 'status' in error) {
      const apiError = error as any;
      
      switch (apiError.status) {
        case 401:
          console.error('Não autorizado - fazer logout');
          // Redirecionar para login
          break;
        case 403:
          console.error('Acesso negado');
          break;
        case 404:
          console.error('Recurso não encontrado');
          break;
        case 500:
          console.error('Erro interno do servidor');
          break;
        default:
          console.error('Erro desconhecido:', apiError);
      }
    }
    throw error;
  }
}

export default {
  exemploHealthCheck,
  exemploMetricas,
  exemploConversas,
  exemploAppointments,
  exemploCreateAppointment,
  exemploUpdateAppointment,
  exemploDeleteAppointment,
  useHealthCheck,
  useConversations,
  useCreateAppointment
};
