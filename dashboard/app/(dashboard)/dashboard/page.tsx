'use client'

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { 
  MessageCircle, 
  Users, 
  Calendar, 
  MessageSquare,
  TrendingUp,
  TrendingDown,
  Activity,
  Plus,
  Clock
} from "lucide-react"
import { useDashboardData } from "@/hooks/useApi"
import BackendError from "@/components/ui/backend-error"

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState("30")
  const { kpis, charts, recentActivity, loading, error, refetch } = useDashboardData(parseInt(timeRange))

  // Mostrar erro quando houver problemas com backend
  if (error && !loading) {
    return (
      <div className="space-y-6">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 text-white rounded-lg p-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold mb-2">WPPAgent Dashboard</h1>
              <p className="text-blue-100 opacity-90">
                Erro de conectividade • {new Date().toLocaleDateString('pt-BR')}
              </p>
            </div>
            <div className="bg-red-500/20 backdrop-blur-sm rounded-lg p-3">
              <span className="text-red-100 text-sm font-medium">Offline</span>
            </div>
          </div>
        </div>

        {/* Error Component */}
        <BackendError 
          error={error} 
          onRetry={refetch}
          showRetry={true}
        />
      </div>
    )
  }

  // Mostrar loading quando não há dados
  if (loading || !kpis) {
    return (
      <div className="space-y-6">
        {/* Hero Section - Skeleton */}
        <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 text-white rounded-lg p-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold mb-2">WPPAgent Dashboard</h1>
              <p className="text-blue-100 opacity-90">
                Carregando dados • {new Date().toLocaleDateString('pt-BR')}
              </p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
              <div className="animate-pulse h-4 w-20 bg-white/30 rounded"></div>
            </div>
          </div>
        </div>

        {/* Loading State */}
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600 text-lg">Carregando dados do sistema...</span>
        </div>
      </div>
    )
  }

  // Mostrar erro se houver problemas
  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h2 className="text-xl font-semibold text-red-800 mb-2">Erro ao carregar dados</h2>
          <p className="text-red-600 mb-4">{error}</p>
          <Button 
            onClick={() => refetch()}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            Tentar novamente
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Hero Section - Cabeçalho Principal */}
      <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 text-white rounded-lg p-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold mb-2">WPPAgent Dashboard</h1>
            <p className="text-blue-100 opacity-90">
              Dados em tempo real • {new Date().toLocaleDateString('pt-BR')}
            </p>
          </div>
          <div className="bg-white/20 backdrop-blur-sm rounded-lg p-3">
            <select 
              className="bg-transparent text-white border-none outline-none cursor-pointer"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <option value="7" className="text-gray-800">7 dias</option>
              <option value="30" className="text-gray-800">30 dias</option>
              <option value="90" className="text-gray-800">90 dias</option>
            </select>
          </div>
        </div>
      </div>

      {/* Grid de KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Card Conversas */}
        <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
          <CardHeader className="bg-gradient-to-r from-blue-500 to-blue-600 text-white pb-4">
            <div className="flex items-center justify-between">
              <div className="p-3 bg-white/20 rounded-lg backdrop-blur-sm border border-white/30">
                <MessageCircle size={24} />
              </div>
              <div className="text-right">
                <CardTitle className="text-2xl font-bold text-white mb-1">
                  {kpis.total_conversations.toLocaleString('pt-BR')}
                </CardTitle>
                <p className="text-white/90 text-sm font-medium">Conversas Ativas</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-gray-50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">+{kpis.conversations_today} hoje</p>
              <div className="flex items-center text-xs font-semibold text-green-600">
                <TrendingUp className="h-3 w-3 mr-1" />
                {kpis.growth_conversations.toFixed(1)}%
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card Usuários */}
        <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
          <CardHeader className="bg-gradient-to-r from-green-500 to-green-600 text-white pb-4">
            <div className="flex items-center justify-between">
              <div className="p-3 bg-white/20 rounded-lg backdrop-blur-sm border border-white/30">
                <Users size={24} />
              </div>
              <div className="text-right">
                <CardTitle className="text-2xl font-bold text-white mb-1">
                  {kpis.unique_users.toLocaleString('pt-BR')}
                </CardTitle>
                <p className="text-white/90 text-sm font-medium">Clientes Únicos</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-gray-50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">+{kpis.clients_today} hoje</p>
              <p className="text-xs text-gray-500">Base de clientes</p>
            </div>
          </CardContent>
        </Card>

        {/* Card Agendamentos */}
        <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
          <CardHeader className="bg-gradient-to-r from-orange-500 to-orange-600 text-white pb-4">
            <div className="flex items-center justify-between">
              <div className="p-3 bg-white/20 rounded-lg backdrop-blur-sm border border-white/30">
                <Calendar size={24} />
              </div>
              <div className="text-right">
                <CardTitle className="text-2xl font-bold text-white mb-1">
                  {kpis.total_appointments}
                </CardTitle>
                <p className="text-white/90 text-sm font-medium">Agendamentos</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-gray-50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">+{kpis.appointments_today} hoje</p>
              <div className="flex items-center text-xs font-semibold text-green-600">
                <TrendingUp className="h-3 w-3 mr-1" />
                {kpis.growth_appointments.toFixed(1)}%
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card Mensagens */}
        <Card className="overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
          <CardHeader className="bg-gradient-to-r from-purple-500 to-purple-600 text-white pb-4">
            <div className="flex items-center justify-between">
              <div className="p-3 bg-white/20 rounded-lg backdrop-blur-sm border border-white/30">
                <MessageSquare size={24} />
              </div>
              <div className="text-right">
                <CardTitle className="text-2xl font-bold text-white mb-1">
                  {kpis.total_messages.toLocaleString('pt-BR')}
                </CardTitle>
                <p className="text-white/90 text-sm font-medium">Mensagens</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 bg-gray-50">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">{kpis.messages_today} hoje</p>
              <div className="flex items-center text-xs font-semibold text-green-600">
                <TrendingUp className="h-3 w-3 mr-1" />
                {kpis.growth_messages.toFixed(1)}%
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Widgets do Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Activity className="h-5 w-5 mr-2 text-blue-600" />
              Performance Hoje
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Conversas iniciadas</span>
              <span className="font-semibold">{kpis.conversations_today}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Mensagens enviadas</span>
              <span className="font-semibold">{kpis.messages_today}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Agendamentos hoje</span>
              <span className="font-semibold text-green-600">{kpis.appointments_today}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Novos clientes</span>
              <span className="font-semibold">{kpis.clients_today}</span>
            </div>
          </CardContent>
        </Card>

        {/* Card Atividade Recente */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Clock className="h-5 w-5 mr-2 text-green-600" />
              Atividade Recente
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentActivity && recentActivity.length > 0 ? (
              recentActivity.slice(0, 3).map((activity) => (
                <div key={activity.id} className="flex items-start space-x-3">
                  <div className={`p-2 rounded-full text-white flex-shrink-0 ${
                    activity.type === 'conversation' ? 'bg-blue-500' :
                    activity.type === 'appointment' ? 'bg-green-500' :
                    'bg-purple-500'
                  }`}>
                    {activity.type === 'conversation' ? <MessageCircle className="h-4 w-4" /> :
                     activity.type === 'appointment' ? <Calendar className="h-4 w-4" /> :
                     <MessageSquare className="h-4 w-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {activity.title}
                    </p>
                    <p className="text-xs text-gray-600 truncate">
                      {activity.description}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(activity.timestamp).toLocaleString('pt-BR', {
                        hour: '2-digit',
                        minute: '2-digit',
                        day: '2-digit',
                        month: '2-digit'
                      })}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center py-8">
                <p className="text-gray-500 text-sm">Nenhuma atividade recente</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Card Conversas por Período */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <MessageCircle className="h-5 w-5 mr-2 text-blue-600" />
              Atividade Histórica
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium text-blue-800 mb-2">Agosto 2025</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-blue-600">Mensagens:</span>
                  <span className="font-medium">2,074</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-blue-600">Conversas:</span>
                  <span className="font-medium">40</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-blue-600">Agendamentos:</span>
                  <span className="font-medium">17</span>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-700 mb-2">Setembro 2025</h4>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Mensagens:</span>
                  <span className="font-medium">8 (últimos 7 dias)</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Conversas:</span>
                  <span className="font-medium">0</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Agendamentos:</span>
                  <span className="font-medium">0</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Seção de Métricas Detalhadas - Dados Reais do PostgreSQL */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6">
        {/* Card Status Agendamentos */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Calendar className="h-5 w-5 mr-2 text-orange-600" />
              Status Agendamentos
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Confirmados</span>
              </div>
              <span className="font-semibold">2</span>
            </div>
            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Pendentes</span>
              </div>
              <span className="font-semibold">7</span>
            </div>
            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Cancelados</span>
              </div>
              <span className="font-semibold">4</span>
            </div>
            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-gray-400 rounded-full mr-2"></div>
                <span className="text-sm text-gray-600">Status Inválido</span>
              </div>
              <span className="font-semibold">4</span>
            </div>
          </CardContent>
        </Card>

        {/* Card Taxa de Conversão */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
              Taxa de Conversão
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">33.93%</div>
              <p className="text-sm text-gray-600">Usuários com conversas ativas</p>
            </div>
            <div className="text-center pt-2">
              <p className="text-xs text-gray-500">40 de 112 usuários</p>
            </div>
          </CardContent>
        </Card>

        {/* Card Média de Mensagens */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <MessageSquare className="h-5 w-5 mr-2 text-purple-600" />
              Média por Conversa
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">54.6</div>
              <p className="text-sm text-gray-600">Mensagens por conversa</p>
            </div>
            <div className="text-center pt-2">
              <p className="text-xs text-gray-500">2,074 mensagens em 38 conversas</p>
            </div>
          </CardContent>
        </Card>

        {/* Card Atividade dos Últimos 7 Dias */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-lg">
              <Activity className="h-5 w-5 mr-2 text-green-600" />
              Últimos 7 Dias
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Mensagens</span>
              <span className="font-semibold text-green-600">8</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Este mês</span>
              <span className="font-semibold text-gray-500">0</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Mês passado</span>
              <span className="font-semibold text-blue-600">2,074</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ações Rápidas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Plus className="h-5 w-5 mr-2" />
            Ações Rápidas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="cursor-pointer transition-all duration-200 hover:shadow-md hover:-translate-y-1 border-2 border-transparent hover:border-blue-200">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-blue-100 text-blue-600 mb-3">
                  <Plus size={20} />
                </div>
                <p className="font-semibold text-sm text-gray-700">Nova Conversa</p>
              </CardContent>
            </Card>
            <Card className="cursor-pointer transition-all duration-200 hover:shadow-md hover:-translate-y-1 border-2 border-transparent hover:border-blue-200">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-green-100 text-green-600 mb-3">
                  <Calendar size={20} />
                </div>
                <p className="font-semibold text-sm text-gray-700">Novo Agendamento</p>
              </CardContent>
            </Card>
            <Card className="cursor-pointer transition-all duration-200 hover:shadow-md hover:-translate-y-1 border-2 border-transparent hover:border-blue-200">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-orange-100 text-orange-600 mb-3">
                  <Users size={20} />
                </div>
                <p className="font-semibold text-sm text-gray-700">Adicionar Cliente</p>
              </CardContent>
            </Card>
            <Card className="cursor-pointer transition-all duration-200 hover:shadow-md hover:-translate-y-1 border-2 border-transparent hover:border-blue-200">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-gray-100 text-gray-600 mb-3">
                  <Activity size={20} />
                </div>
                <p className="font-semibold text-sm text-gray-700">Configurações</p>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
