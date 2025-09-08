/**
 * 📅 Exemplo de Uso - Loading States em Appointments
 * ================================================
 * 
 * Demonstra como usar os componentes de loading states padronizados
 * em um componente real de agendamentos.
 * 
 * Autor: Claude AI
 * Data: 2025-09-07
 */

'use client'

import { useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { 
  DataStateWrapper,
  LoadingSpinner,
  ErrorFallback,
  EmptyState,
  TableSkeleton,
  ButtonLoading,
  NetworkStatus
} from "@/components/ui/loading-states"
import { useAsyncList, useNetworkStatus } from "@/hooks/use-async-state"
import { Appointment, AppointmentsListResponse } from "@/types/api"

// Mock API service para exemplo
const appointmentsAPI = {
  async getAppointments(filters?: any): Promise<Appointment[]> {
    // Simular delay de rede
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Simular erro ocasional
    if (Math.random() < 0.1) {
      throw new Error('Erro de conexão com o servidor')
    }
    
    // Simular dados vazios ocasionalmente
    if (Math.random() < 0.2) {
      return []
    }
    
    // Retornar dados simulados
    return [
      {
        id: 1,
        user_id: 123,
        business_id: 456,
        data_agendamento: '2025-09-08T10:00:00Z',
        horario: '10:00',
        duracao_minutos: 60,
        valor: 150.0,
        status: 'agendado' as const,
        observacoes: 'Primeira consulta',
        cliente_nome: 'João Silva',
        cliente_telefone: '11999999999',
        servico_nome: 'Consulta',
        business_name: 'Clínica Exemplo',
        created_at: '2025-09-07T00:00:00Z'
      }
    ]
  }
}

export function AppointmentsListExample() {
  const isOnline = useNetworkStatus()
  const {
    data: appointments,
    loading,
    error,
    refresh,
    updateFilters
  } = useAsyncList<Appointment>(appointmentsAPI.getAppointments)

  // Carregar dados na inicialização
  useEffect(() => {
    refresh()
  }, [refresh])

  // Handler para retry
  const handleRetry = () => {
    refresh()
  }

  // Handler para filtros
  const handleFilterChange = (newFilters: any) => {
    updateFilters(newFilters)
  }

  return (
    <div className="space-y-6">
      {/* ✅ Network status indicator */}
      <NetworkStatus isOnline={isOnline} />
      
      {/* ✅ Header com loading state */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Agendamentos</h1>
        <Button 
          onClick={() => refresh()} 
          disabled={loading}
          variant="outline"
        >
          <ButtonLoading loading={loading}>
            Atualizar
          </ButtonLoading>
        </Button>
      </div>

      {/* ✅ Filtros (exemplo) */}
      <div className="flex space-x-4">
        <Button
          onClick={() => handleFilterChange({ status: 'agendado' })}
          variant="outline"
        >
          Agendados
        </Button>
        <Button
          onClick={() => handleFilterChange({ status: 'confirmado' })}
          variant="outline"
        >
          Confirmados
        </Button>
        <Button
          onClick={() => handleFilterChange({})}
          variant="outline"
        >
          Todos
        </Button>
      </div>

      {/* ✅ Lista com estados padronizados */}
      <div className="border border-gray-200 rounded-lg">
        <DataStateWrapper<Appointment[]>
          data={appointments}
          loading={loading}
          error={error}
          retry={handleRetry}
          emptyTitle="Nenhum agendamento encontrado"
          emptyDescription="Não há agendamentos para os filtros selecionados."
          emptyAction={
            <Button onClick={handleRetry} variant="outline">
              Recarregar
            </Button>
          }
        >
          {(appointmentsList: Appointment[]) => (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Data/Horário
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Serviço
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Valor
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {appointmentsList.map((appointment: Appointment) => (
                    <tr key={appointment.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {appointment.cliente_nome}
                          </div>
                          <div className="text-sm text-gray-500">
                            {appointment.cliente_telefone}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {new Date(appointment.data_agendamento).toLocaleDateString('pt-BR')}
                        </div>
                        <div className="text-sm text-gray-500">
                          {appointment.horario}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {appointment.servico_nome}
                        </div>
                        <div className="text-sm text-gray-500">
                          {appointment.duracao_minutos} min
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          appointment.status === 'agendado' ? 'bg-yellow-100 text-yellow-800' :
                          appointment.status === 'confirmado' ? 'bg-green-100 text-green-800' :
                          appointment.status === 'realizado' ? 'bg-blue-100 text-blue-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {appointment.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        R$ {appointment.valor.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Button size="sm" variant="outline">
                          Ver Detalhes
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </DataStateWrapper>
      </div>
    </div>
  )
}

// ✅ Componente com loading skeleton para tabelas
export function AppointmentsTableSkeleton() {
  return (
    <div className="border border-gray-200 rounded-lg p-6">
      <div className="space-y-4">
        {/* Header skeleton */}
        <div className="flex justify-between items-center">
          <div className="h-8 w-48 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
        </div>
        
        {/* Filter skeleton */}
        <div className="flex space-x-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-10 w-20 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
        
        {/* Table skeleton */}
        <TableSkeleton rows={5} cols={6} />
      </div>
    </div>
  )
}

// ✅ Componente de erro específico para appointments
export function AppointmentsErrorFallback({ 
  error, 
  retry 
}: { 
  error: Error | string
  retry: () => void 
}) {
  return (
    <ErrorFallback
      error={error}
      retry={retry}
      title="Erro ao carregar agendamentos"
    />
  )
}

// ✅ Estado vazio específico para appointments
export function AppointmentsEmptyState({ 
  onCreateNew 
}: { 
  onCreateNew?: () => void 
}) {
  return (
    <EmptyState
      title="Nenhum agendamento encontrado"
      description="Você ainda não possui agendamentos. Que tal criar o primeiro?"
      action={
        onCreateNew && (
          <Button onClick={onCreateNew}>
            Novo Agendamento
          </Button>
        )
      }
    />
  )
}
