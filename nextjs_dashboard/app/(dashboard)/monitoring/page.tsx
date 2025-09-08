"use client"

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  Activity,
  Database,
  MessageSquare,
  TrendingUp,
  RefreshCw
} from 'lucide-react'
import { api } from '@/lib/api-service'

interface Alert {
  id: string
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  message: string
  timestamp: string
  data?: any
}

interface SystemHealth {
  overall_status: 'healthy' | 'degraded' | 'critical'
  components: {
    whatsapp_api: 'healthy' | 'unhealthy'
    database: 'healthy' | 'unhealthy'
    cache: 'healthy' | 'unhealthy'
    webhook: 'healthy' | 'unhealthy'
  }
  metrics: {
    response_time: number
    error_rate: number
    message_success_rate: number
    uptime: number
  }
}

export default function MonitoringPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [resolvingAlerts, setResolvingAlerts] = useState<Set<string>>(new Set())

  const loadData = async () => {
    try {
      const [alertsData, healthData] = await Promise.all([
        api.getActiveAlerts(),
        api.getSystemHealth()
      ])
      
      setAlerts(alertsData)
      setSystemHealth(healthData)
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Erro ao carregar dados de monitoramento:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleResolveAlert = async (alertId: string) => {
    try {
      setResolvingAlerts(prev => new Set(prev).add(alertId))
      
      await api.resolveAlert(alertId, 'Resolvido manualmente via dashboard')
      
      // Remover o alerta da lista local
      setAlerts(prev => prev.filter(alert => alert.id !== alertId))
      
    } catch (error) {
      console.error('Erro ao resolver alerta:', error)
    } finally {
      setResolvingAlerts(prev => {
        const newSet = new Set(prev)
        newSet.delete(alertId)
        return newSet
      })
    }
  }

  useEffect(() => {
    loadData()
    
    // Atualizar a cada 30 segundos
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  const getSeverityColor = (severity: string) => {
    const colors = {
      low: 'bg-blue-100 text-blue-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    }
    return colors[severity as keyof typeof colors] || colors.low
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Monitoramento</h1>
          <p className="text-gray-600 mt-1">
            Status do sistema • Atualizado {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <Button onClick={loadData} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Atualizar
        </Button>
      </div>

      {/* Status Geral */}
      {systemHealth && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Status Geral do Sistema
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="flex items-center justify-center mb-2">
                  {getStatusIcon(systemHealth.components.whatsapp_api)}
                </div>
                <p className="font-medium">WhatsApp API</p>
                <p className="text-sm text-gray-600 capitalize">
                  {systemHealth.components.whatsapp_api}
                </p>
              </div>
              
              <div className="text-center">
                <div className="flex items-center justify-center mb-2">
                  {getStatusIcon(systemHealth.components.database)}
                </div>
                <p className="font-medium">Banco de Dados</p>
                <p className="text-sm text-gray-600 capitalize">
                  {systemHealth.components.database}
                </p>
              </div>
              
              <div className="text-center">
                <div className="flex items-center justify-center mb-2">
                  {getStatusIcon(systemHealth.components.cache)}
                </div>
                <p className="font-medium">Cache Redis</p>
                <p className="text-sm text-gray-600 capitalize">
                  {systemHealth.components.cache}
                </p>
              </div>
              
              <div className="text-center">
                <div className="flex items-center justify-center mb-2">
                  {getStatusIcon(systemHealth.components.webhook)}
                </div>
                <p className="font-medium">Webhook</p>
                <p className="text-sm text-gray-600 capitalize">
                  {systemHealth.components.webhook}
                </p>
              </div>
            </div>

            {/* Métricas */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Tempo Resposta</p>
                    <p className="text-2xl font-bold">
                      {systemHealth.metrics.response_time.toFixed(0)}ms
                    </p>
                  </div>
                  <Clock className="w-8 h-8 text-blue-500" />
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Taxa de Erro</p>
                    <p className="text-2xl font-bold">
                      {(systemHealth.metrics.error_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  <XCircle className="w-8 h-8 text-red-500" />
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Sucesso Mensagens</p>
                    <p className="text-2xl font-bold">
                      {(systemHealth.metrics.message_success_rate * 100).toFixed(1)}%
                    </p>
                  </div>
                  <MessageSquare className="w-8 h-8 text-green-500" />
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Uptime</p>
                    <p className="text-2xl font-bold">
                      {systemHealth.metrics.uptime.toFixed(1)}%
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-purple-500" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alertas Ativos */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            Alertas Ativos ({alerts.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900">Nenhum alerta ativo</p>
              <p className="text-gray-600">Todos os sistemas estão funcionando normalmente</p>
            </div>
          ) : (
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="border rounded-lg p-4 bg-white shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <Badge className={getSeverityColor(alert.severity)}>
                          {alert.severity.toUpperCase()}
                        </Badge>
                        <Badge variant="outline">
                          {alert.type.replace('_', ' ').toUpperCase()}
                        </Badge>
                      </div>
                      <h3 className="font-semibold text-gray-900 mb-1">
                        {alert.title}
                      </h3>
                      <p className="text-gray-600 text-sm mb-2">
                        {alert.message}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleString()}
                      </p>
                    </div>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={resolvingAlerts.has(alert.id)}
                      onClick={() => handleResolveAlert(alert.id)}
                    >
                      {resolvingAlerts.has(alert.id) ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        'Resolver'
                      )}
                    </Button>
                  </div>
                  
                  {alert.data && Object.keys(alert.data).length > 0 && (
                    <details className="mt-4">
                      <summary className="text-sm font-medium text-gray-700 cursor-pointer">
                        Detalhes técnicos
                      </summary>
                      <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                        {JSON.stringify(alert.data, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
