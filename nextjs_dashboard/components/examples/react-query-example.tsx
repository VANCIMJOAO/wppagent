'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { LoadingSpinner } from '@/components/ui/loading-states'
import { useAppointments, useCreateAppointment, useUpdateAppointment, useDeleteAppointment } from '@/hooks/useAppointments'
import { useConversations } from '@/hooks/useConversations'
import { useDashboard } from '@/hooks/useDashboard'
import type { Appointment, AppointmentStatus } from '@/types/api'

// Componente de exemplo para mostrar como usar os hooks do React Query
export function ReactQueryExample() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<AppointmentStatus | undefined>()

  // Usando hooks do React Query
  const { 
    data: appointmentsData, 
    isLoading: appointmentsLoading, 
    error: appointmentsError,
    refetch: refetchAppointments 
  } = useAppointments({ 
    page, 
    limit: 10, 
    status 
  })

  const { 
    data: conversationsData, 
    isLoading: conversationsLoading 
  } = useConversations({ 
    page: 1, 
    limit: 5 
  })

  const { 
    data: dashboardData, 
    isLoading: dashboardLoading,
    refresh: refreshDashboard,
    isRefreshing 
  } = useDashboard({ 
    period: '7d',
    autoRefresh: true 
  })

  // Mutations
  const createAppointment = useCreateAppointment()
  const updateAppointment = useUpdateAppointment()
  const deleteAppointment = useDeleteAppointment()

  const handleCreateAppointment = () => {
    createAppointment.mutate({
      user_id: 1,
      business_id: 1,
      service_id: 1,
      date_time: new Date().toISOString(),
      notes: 'Agendamento criado via React Query'
    })
  }

  const handleUpdateAppointment = (appointment: Appointment) => {
    updateAppointment.mutate({
      id: appointment.id,
      data: {
        status: 'realizado' as AppointmentStatus,
        notes: 'Atualizado via React Query'
      }
    })
  }

  const handleDeleteAppointment = (id: number) => {
    if (confirm('Deseja realmente excluir este agendamento?')) {
      deleteAppointment.mutate(id)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">React Query Example</h1>
        <Button 
          onClick={() => refreshDashboard()}
          disabled={isRefreshing}
          className="flex items-center gap-2"
        >
          {isRefreshing && <LoadingSpinner size="sm" />}
          Atualizar Dashboard
        </Button>
      </div>

      {/* Dashboard Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Dashboard Stats</CardTitle>
          <CardDescription>Estatísticas em tempo real</CardDescription>
        </CardHeader>
        <CardContent>
          {dashboardLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : dashboardData?.stats ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {dashboardData.stats.total_appointments}
                </div>
                <div className="text-sm text-gray-600">Total Agendamentos</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {dashboardData.stats.total_conversations}
                </div>
                <div className="text-sm text-gray-600">Total Conversas</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {dashboardData.stats.pending_appointments}
                </div>
                <div className="text-sm text-gray-600">Pendentes</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {dashboardData.stats.today_appointments}
                </div>
                <div className="text-sm text-gray-600">Hoje</div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500">Sem dados disponíveis</div>
          )}
        </CardContent>
      </Card>

      {/* Controles de filtro */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros de Agendamentos</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4 items-center">
          <select 
            value={status || ''} 
            onChange={(e) => setStatus(e.target.value as AppointmentStatus || undefined)}
            className="border rounded px-3 py-2"
          >
            <option value="">Todos os status</option>
            <option value="pendente">Pendente</option>
            <option value="confirmado">Confirmado</option>
            <option value="realizado">Realizado</option>
            <option value="cancelado">Cancelado</option>
          </select>

          <Button 
            variant="outline" 
            onClick={() => refetchAppointments()}
            disabled={appointmentsLoading}
          >
            {appointmentsLoading && <LoadingSpinner size="sm" />}
            Atualizar
          </Button>

          <Button 
            onClick={handleCreateAppointment}
            disabled={createAppointment.isPending}
          >
            {createAppointment.isPending && <LoadingSpinner size="sm" />}
            Criar Agendamento
          </Button>
        </CardContent>
      </Card>

      {/* Lista de Agendamentos */}
      <Card>
        <CardHeader>
          <CardTitle>Agendamentos</CardTitle>
          <CardDescription>
            {appointmentsData ? 
              `${appointmentsData.total} agendamentos encontrados` : 
              'Carregando agendamentos...'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {appointmentsError ? (
            <div className="text-center text-red-500 py-8">
              Erro ao carregar agendamentos: {appointmentsError.message}
            </div>
          ) : appointmentsLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : appointmentsData?.appointments.length ? (
            <div className="space-y-4">
              {appointmentsData.appointments.map((appointment) => (
                <div 
                  key={appointment.id} 
                  className="border rounded-lg p-4 flex items-center justify-between"
                >
                  <div>
                    <div className="font-semibold">{appointment.cliente_nome}</div>
                    <div className="text-sm text-gray-600">
                      {appointment.servico_nome} - {appointment.data_agendamento} às {appointment.horario}
                    </div>
                    {appointment.observacoes && (
                      <div className="text-sm text-gray-500 mt-1">{appointment.observacoes}</div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={
                      appointment.status === 'realizado' ? 'default' :
                      appointment.status === 'confirmado' ? 'secondary' :
                      appointment.status === 'pendente' ? 'outline' : 'destructive'
                    }>
                      {appointment.status}
                    </Badge>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleUpdateAppointment(appointment)}
                      disabled={updateAppointment.isPending}
                    >
                      {updateAppointment.isPending && <LoadingSpinner size="sm" />}
                      Atualizar
                    </Button>
                    <Button 
                      size="sm" 
                      variant="destructive"
                      onClick={() => handleDeleteAppointment(appointment.id)}
                      disabled={deleteAppointment.isPending}
                    >
                      {deleteAppointment.isPending && <LoadingSpinner size="sm" />}
                      Excluir
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              Nenhum agendamento encontrado
            </div>
          )}

          {/* Paginação */}
          {appointmentsData && appointmentsData.has_more && (
            <div className="flex justify-center mt-6">
              <Button 
                onClick={() => setPage(p => p + 1)}
                disabled={appointmentsLoading}
              >
                Carregar mais
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Conversas Recentes */}
      <Card>
        <CardHeader>
          <CardTitle>Conversas Recentes</CardTitle>
        </CardHeader>
        <CardContent>
          {conversationsLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : conversationsData?.conversations.length ? (
            <div className="space-y-3">
              {conversationsData.conversations.map((conversation) => (
                <div 
                  key={conversation.id} 
                  className="border rounded p-3 flex items-center justify-between"
                >
                  <div>
                    <div className="font-medium">{conversation.user_name}</div>
                    <div className="text-sm text-gray-600">
                      {conversation.last_message || 'Sem mensagens'}
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant="secondary">
                      {conversation.unread_messages} não lidas
                    </Badge>
                    <div className="text-xs text-gray-500 mt-1">
                      {conversation.last_message_at && 
                        new Date(conversation.last_message_at).toLocaleString()
                      }
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              Nenhuma conversa encontrada
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
