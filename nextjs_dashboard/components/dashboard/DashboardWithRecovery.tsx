/**
 * Componente de Dashboard com Error Recovery Avançado
 * Demonstra uso do hook robusto com estados visuais de recovery
 */
'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useDashboardStatsRobust } from '@/hooks/useDashboardStatsRobust'
import {
  AlertTriangle,
  Wifi,
  WifiOff,
  RefreshCw,
  Database,
  Clock,
  TrendingUp,
  Users,
  MessageSquare,
  Calendar,
  Activity,
  Trash2,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { toast } from 'sonner'

interface DashboardRecoveryProps {
  className?: string
}

export const DashboardWithRecovery: React.FC<DashboardRecoveryProps> = ({
  className = ''
}) => {
  const {
    data: stats,
    error,
    isLoading,
    isFetching,
    isError,
    recoveryMode,
    retryCount,
    networkStatus,
    isOffline,
    refetch,
    manualRetry,
    clearCache,
    isUsingCache,
    isDegraded,
    canRetry,
    debugInfo
  } = useDashboardStatsRobust({
    maxRetries: 3,
    retryDelay: 1000,
    cacheTimeout: 30 * 60 * 1000, // 30 min
    enableDegradedMode: true,
    enableNetworkDetection: true,
    enableOfflineMode: true
  })

  // Status visual baseado no modo de recovery
  const getStatusInfo = () => {
    switch (recoveryMode) {
      case 'normal':
        return {
          color: 'bg-green-500',
          icon: <CheckCircle className="w-4 h-4" />,
          text: 'Online - Dados atualizados',
          description: 'Conectado ao servidor com dados em tempo real'
        }
      case 'cached':
        return {
          color: 'bg-yellow-500',
          icon: <Database className="w-4 h-4" />,
          text: 'Cache - Dados salvos',
          description: 'Usando dados em cache devido a problemas de conexão'
        }
      case 'degraded':
        return {
          color: 'bg-orange-500',
          icon: <AlertTriangle className="w-4 h-4" />,
          text: 'Degradado - Funcionalidade limitada',
          description: 'Exibindo dados básicos devido a falhas de sistema'
        }
      case 'offline':
        return {
          color: 'bg-red-500',
          icon: <WifiOff className="w-4 h-4" />,
          text: 'Offline - Sem conexão',
          description: 'Sem conexão com internet, usando dados salvos'
        }
      default:
        return {
          color: 'bg-gray-500',
          icon: <AlertCircle className="w-4 h-4" />,
          text: 'Status desconhecido',
          description: 'Estado não reconhecido'
        }
    }
  }

  const statusInfo = getStatusInfo()

  // Métricas principais do dashboard
  const metrics = [
    {
      title: 'Conversas Hoje',
      value: stats?.conversations_today || 0,
      icon: MessageSquare,
      color: 'text-blue-600',
    },
    {
      title: 'Mensagens Hoje',
      value: stats?.messages_today || 0,
      icon: TrendingUp,
      color: 'text-green-600',
    },
    {
      title: 'Agendamentos',
      value: stats?.appointments_today || 0,
      icon: Calendar,
      color: 'text-purple-600',
    },
    {
      title: 'Novos Clientes',
      value: stats?.new_clients_today || 0,
      icon: Users,
      color: 'text-orange-600',
    },
  ]

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Cabeçalho com Status de Recovery */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-blue-600" />
                <span>Dashboard - Error Recovery System</span>
              </CardTitle>
            </div>

            {/* Status Badge */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${statusInfo.color} animate-pulse`}></div>
              <Badge variant="secondary" className="flex items-center space-x-1">
                {statusInfo.icon}
                <span>{statusInfo.text}</span>
              </Badge>
            </div>
          </div>

          {/* Descrição do Status */}
          <p className="text-sm text-gray-600">
            {statusInfo.description}
          </p>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Informações de Network/Recovery */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              {isOffline ? (
                <WifiOff className="w-4 h-4 text-red-500" />
              ) : (
                <Wifi className="w-4 h-4 text-green-500" />
              )}
              <span className="text-sm">
                {isOffline ? 'Offline' : `Online (${networkStatus.effectiveType})`}
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-blue-500" />
              <span className="text-sm">
                RTT: {networkStatus.rtt}ms
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <Database className="w-4 h-4 text-purple-500" />
              <span className="text-sm">
                {isUsingCache ? 'Cache ativo' : 'Dados frescos'}
              </span>
            </div>
          </div>

          {/* Controles de Recovery */}
          <div className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isFetching ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>

            {(isError || retryCount > 0) && canRetry && (
              <Button
                size="sm"
                variant="outline"
                onClick={manualRetry}
                disabled={isFetching}
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                Tentar Novamente ({retryCount}/{3})
              </Button>
            )}

            <Button
              size="sm"
              variant="ghost"
              onClick={clearCache}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Limpar Cache
            </Button>
          </div>

          {/* Alertas de Error Recovery */}
          {isDegraded && (
            <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-orange-600" />
                <span className="text-sm font-medium text-orange-800">
                  Modo Degradado Ativo
                </span>
              </div>
              <p className="text-xs text-orange-700 mt-1">
                Alguns dados podem estar desatualizados. Funcionalidade limitada.
              </p>
            </div>
          )}

          {isUsingCache && !isDegraded && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <Database className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-800">
                  Usando Dados em Cache
                </span>
              </div>
              <p className="text-xs text-yellow-700 mt-1">
                Última atualização: {stats?.last_updated
                  ? new Date(stats.last_updated).toLocaleString('pt-BR')
                  : 'Desconhecido'
                }
              </p>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <XCircle className="w-4 h-4 text-red-600" />
                <span className="text-sm font-medium text-red-800">
                  Erro de Conexão
                </span>
              </div>
              <p className="text-xs text-red-700 mt-1">
                {error.message}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Métricas Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <Card key={metric.title} className={isDegraded ? 'opacity-60' : ''}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    {metric.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {isLoading ? '...' : metric.value.toLocaleString()}
                  </p>

                  {isDegraded && (
                    <p className="text-xs text-orange-600 mt-1">
                      Dados limitados
                    </p>
                  )}

                  {isUsingCache && !isDegraded && (
                    <p className="text-xs text-yellow-600 mt-1">
                      Cache
                    </p>
                  )}
                </div>
                <metric.icon className={`h-8 w-8 ${metric.color} ${isDegraded ? 'opacity-50' : ''}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Métricas Totais */}
      <Card>
        <CardHeader>
          <CardTitle>Totais Acumulados</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {(stats?.total_conversations || 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Total Conversas</div>
            </div>

            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {(stats?.total_messages || 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Total Mensagens</div>
            </div>

            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {(stats?.conversion_rate || 0).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Taxa Conversão</div>
            </div>

            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {(stats?.growth_rate || 0) > 0 ? '+' : ''}{(stats?.growth_rate || 0).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Crescimento</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Debug Information (dev only) */}
      {process.env.NODE_ENV === 'development' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Debug Info</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto">
              {JSON.stringify({
                recoveryMode,
                retryCount,
                isOffline,
                networkStatus,
                debugInfo
              }, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default DashboardWithRecovery
