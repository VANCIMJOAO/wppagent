"use client"

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  Database,
  MessageSquare,
  TrendingUp,
  RefreshCw,
  Settings,
  Plus,
  Edit,
  Trash2,
  TestTube,
  Bell,
  Mail,
  Slack,
  Webhook,
  Monitor
} from 'lucide-react'
import { toast } from 'sonner'
import api from '@/lib/api-service'

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

interface AlertRule {
  name: string
  metric_name: string
  condition: string
  threshold: number
  duration: number
  severity: string
  description: string
  tags: Record<string, string>
  enabled: boolean
}

interface NotificationConfig {
  channel: string
  target: string
  min_severity: string
  rate_limit: number
  enabled: boolean
}

interface Metric {
  name: string
  description: string
  unit: string
  type: string
}

export default function MonitoringPage() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [resolvingAlerts, setResolvingAlerts] = useState<Set<string>>(new Set())
  
  // Alert configuration states
  const [alertRules, setAlertRules] = useState<AlertRule[]>([])
  const [notificationConfigs, setNotificationConfigs] = useState<NotificationConfig[]>([])
  const [availableMetrics, setAvailableMetrics] = useState<Metric[]>([])
  const [alertSystemStatus, setAlertSystemStatus] = useState<any>(null)
  
  // Dialog states
  const [ruleDialog, setRuleDialog] = useState(false)
  const [notificationDialog, setNotificationDialog] = useState(false)
  const [testDialog, setTestDialog] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null)
  const [editingNotification, setEditingNotification] = useState<NotificationConfig | null>(null)
  
  // Form states
  const [ruleForm, setRuleForm] = useState({
    name: '',
    metric_name: '',
    condition: 'gte',
    threshold: 0,
    duration: 60,
    severity: 'medium',
    description: '',
    enabled: true
  })
  
  const [notificationForm, setNotificationForm] = useState({
    channel: 'email',
    target: '',
    min_severity: 'medium',
    rate_limit: 300,
    enabled: true
  })
  
  const [testForm, setTestForm] = useState({
    rule_name: '',
    test_value: 0
  })

  const loadData = async () => {
    try {
      const [alertsResponse, healthResponse] = await Promise.all([
        api.getActiveAlerts(),
        api.getSystemHealth()
      ])

      // Acessa os dados das respostas da API
      setAlerts(alertsResponse.data || [])
      setSystemHealth(healthResponse.data || null)
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Erro ao carregar dados de monitoramento:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAlertConfigData = async () => {
    try {
      const [rulesResponse, notificationsResponse, metricsResponse, statusResponse] = await Promise.all([
        api.get('/alert-config/rules'),
        api.get('/alert-config/notifications'),
        api.get('/alert-config/metrics'),
        api.get('/alert-config/status')
      ])

      setAlertRules(rulesResponse.data || [])
      setNotificationConfigs(notificationsResponse.data || [])
      setAvailableMetrics(metricsResponse.data.metrics || [])
      setAlertSystemStatus(statusResponse.data || null)
    } catch (error) {
      console.error('Erro ao carregar configuração de alertas:', error)
      toast.error('Erro ao carregar configuração de alertas')
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

  // Alert rule management functions
  const createAlertRule = async () => {
    try {
      await api.post('/alert-config/rules', ruleForm)
      toast.success('Regra de alerta criada com sucesso!')
      setRuleDialog(false)
      resetRuleForm()
      loadAlertConfigData()
    } catch (error) {
      console.error('Erro ao criar regra de alerta:', error)
      toast.error('Erro ao criar regra de alerta')
    }
  }

  const updateAlertRule = async () => {
    try {
      await api.put(`/alert-config/rules/${editingRule?.name}`, ruleForm)
      toast.success('Regra de alerta atualizada com sucesso!')
      setRuleDialog(false)
      setEditingRule(null)
      resetRuleForm()
      loadAlertConfigData()
    } catch (error) {
      console.error('Erro ao atualizar regra de alerta:', error)
      toast.error('Erro ao atualizar regra de alerta')
    }
  }

  const deleteAlertRule = async (ruleName: string) => {
    try {
      await api.delete(`/alert-config/rules/${ruleName}`)
      toast.success('Regra de alerta deletada com sucesso!')
      loadAlertConfigData()
    } catch (error) {
      console.error('Erro ao deletar regra de alerta:', error)
      toast.error('Erro ao deletar regra de alerta')
    }
  }

  const testAlertRule = async () => {
    try {
      const response = await api.post('/alert-config/test', testForm)
      const result = response.data
      
      if (result.triggered) {
        toast.success(`✅ ${result.message}`)
      } else {
        toast.info(`ℹ️ ${result.message}`)
      }
      
      setTestDialog(false)
    } catch (error) {
      console.error('Erro ao testar regra de alerta:', error)
      toast.error('Erro ao testar regra de alerta')
    }
  }

  const resetRuleForm = () => {
    setRuleForm({
      name: '',
      metric_name: '',
      condition: 'gte',
      threshold: 0,
      duration: 60,
      severity: 'medium',
      description: '',
      enabled: true
    })
  }

  const openRuleDialog = (rule?: AlertRule) => {
    if (rule) {
      setEditingRule(rule)
      setRuleForm({
        name: rule.name,
        metric_name: rule.metric_name,
        condition: rule.condition,
        threshold: rule.threshold,
        duration: rule.duration,
        severity: rule.severity,
        description: rule.description,
        enabled: rule.enabled
      })
    } else {
      setEditingRule(null)
      resetRuleForm()
    }
    setRuleDialog(true)
  }

  useEffect(() => {
    loadData()
    if (activeTab === 'alerts-config') {
      loadAlertConfigData()
    }

    // Atualizar a cada 30 segundos
    const interval = setInterval(() => {
      loadData()
      if (activeTab === 'alerts-config') {
        loadAlertConfigData()
      }
    }, 30000)
    return () => clearInterval(interval)
  }, [activeTab])

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

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="dashboard" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="alerts" className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            Alertas
          </TabsTrigger>
          <TabsTrigger value="alerts-config" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Configuração
          </TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
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
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-6">
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
        </TabsContent>

        {/* Alert Configuration Tab */}
        <TabsContent value="alerts-config" className="space-y-6">
          {/* Status do Sistema de Alertas */}
          {alertSystemStatus && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="w-5 h-5" />
                  Status do Sistema de Alertas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{alertSystemStatus.total_rules}</p>
                    <p className="text-sm text-gray-600">Total de Regras</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{alertSystemStatus.active_rules}</p>
                    <p className="text-sm text-gray-600">Regras Ativas</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">{alertSystemStatus.total_notifications}</p>
                    <p className="text-sm text-gray-600">Canais de Notificação</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-orange-600">{alertSystemStatus.active_alerts}</p>
                    <p className="text-sm text-gray-600">Alertas Ativos</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Regras de Alerta */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Regras de Alerta
                </span>
                <Button onClick={() => openRuleDialog()}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nova Regra
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Métrica</TableHead>
                    <TableHead>Condição</TableHead>
                    <TableHead>Limite</TableHead>
                    <TableHead>Severidade</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alertRules.map((rule) => (
                    <TableRow key={rule.name}>
                      <TableCell className="font-medium">{rule.name}</TableCell>
                      <TableCell className="text-sm text-gray-600">{rule.metric_name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{rule.condition}</Badge>
                      </TableCell>
                      <TableCell>{rule.threshold}</TableCell>
                      <TableCell>
                        <Badge className={getSeverityColor(rule.severity)}>
                          {rule.severity.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={rule.enabled ? "default" : "secondary"}>
                          {rule.enabled ? "Ativo" : "Inativo"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openRuleDialog(rule)}
                          >
                            <Edit className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setTestForm({ rule_name: rule.name, test_value: 0 })
                              setTestDialog(true)
                            }}
                          >
                            <TestTube className="w-3 h-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => deleteAlertRule(rule.name)}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Canais de Notificação */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Bell className="w-5 h-5" />
                  Canais de Notificação
                </span>
                <Button onClick={() => setNotificationDialog(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Canal
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {notificationConfigs.map((config, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {config.channel === 'email' && <Mail className="w-4 h-4" />}
                        {config.channel === 'slack' && <Slack className="w-4 h-4" />}
                        {config.channel === 'webhook' && <Webhook className="w-4 h-4" />}
                        {config.channel === 'console' && <Monitor className="w-4 h-4" />}
                        <span className="font-medium capitalize">{config.channel}</span>
                      </div>
                      <Badge variant={config.enabled ? "default" : "secondary"}>
                        {config.enabled ? "Ativo" : "Inativo"}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">{config.target}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>Severidade mínima: {config.min_severity}</span>
                      <span>•</span>
                      <span>Rate limit: {config.rate_limit}s</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      {/* Rule Dialog */}
      <Dialog open={ruleDialog} onOpenChange={setRuleDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingRule ? 'Editar Regra de Alerta' : 'Nova Regra de Alerta'}
            </DialogTitle>
            <DialogDescription>
              Configure uma nova regra de alerta para monitorar métricas do sistema.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="rule-name">Nome da Regra</Label>
                <Input
                  id="rule-name"
                  value={ruleForm.name}
                  onChange={(e) => setRuleForm({...ruleForm, name: e.target.value})}
                  placeholder="ex: high_cpu_usage"
                />
              </div>
              <div>
                <Label htmlFor="metric-name">Métrica</Label>
                <Select value={ruleForm.metric_name} onValueChange={(value) => setRuleForm({...ruleForm, metric_name: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione uma métrica" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableMetrics.map((metric) => (
                      <SelectItem key={metric.name} value={metric.name}>
                        {metric.name} - {metric.description}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="condition">Condição</Label>
                <Select value={ruleForm.condition} onValueChange={(value) => setRuleForm({...ruleForm, condition: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gt">Maior que (&gt;)</SelectItem>
                    <SelectItem value="gte">Maior ou igual (&gt;=)</SelectItem>
                    <SelectItem value="lt">Menor que (&lt;)</SelectItem>
                    <SelectItem value="lte">Menor ou igual (&lt;=)</SelectItem>
                    <SelectItem value="eq">Igual (=)</SelectItem>
                    <SelectItem value="ne">Diferente (!=)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="threshold">Limite</Label>
                <Input
                  id="threshold"
                  type="number"
                  value={ruleForm.threshold}
                  onChange={(e) => setRuleForm({...ruleForm, threshold: parseFloat(e.target.value)})}
                />
              </div>
              <div>
                <Label htmlFor="duration">Duração (s)</Label>
                <Input
                  id="duration"
                  type="number"
                  value={ruleForm.duration}
                  onChange={(e) => setRuleForm({...ruleForm, duration: parseInt(e.target.value)})}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="severity">Severidade</Label>
                <Select value={ruleForm.severity} onValueChange={(value) => setRuleForm({...ruleForm, severity: value})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Baixa</SelectItem>
                    <SelectItem value="medium">Média</SelectItem>
                    <SelectItem value="high">Alta</SelectItem>
                    <SelectItem value="critical">Crítica</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="enabled"
                  checked={ruleForm.enabled}
                  onCheckedChange={(checked) => setRuleForm({...ruleForm, enabled: checked})}
                />
                <Label htmlFor="enabled">Regra ativa</Label>
              </div>
            </div>

            <div>
              <Label htmlFor="description">Descrição</Label>
              <Textarea
                id="description"
                value={ruleForm.description}
                onChange={(e) => setRuleForm({...ruleForm, description: e.target.value})}
                placeholder="Descreva o que esta regra monitora..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRuleDialog(false)}>
              Cancelar
            </Button>
            <Button onClick={editingRule ? updateAlertRule : createAlertRule}>
              {editingRule ? 'Atualizar' : 'Criar'} Regra
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Test Dialog */}
      <Dialog open={testDialog} onOpenChange={setTestDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Testar Regra de Alerta</DialogTitle>
            <DialogDescription>
              Teste uma regra de alerta com um valor específico.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="test-rule">Regra</Label>
              <Select value={testForm.rule_name} onValueChange={(value) => setTestForm({...testForm, rule_name: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma regra" />
                </SelectTrigger>
                <SelectContent>
                  {alertRules.map((rule) => (
                    <SelectItem key={rule.name} value={rule.name}>
                      {rule.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="test-value">Valor para Teste</Label>
              <Input
                id="test-value"
                type="number"
                value={testForm.test_value}
                onChange={(e) => setTestForm({...testForm, test_value: parseFloat(e.target.value)})}
                placeholder="Digite um valor para testar"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTestDialog(false)}>
              Cancelar
            </Button>
            <Button onClick={testAlertRule}>
              <TestTube className="w-4 h-4 mr-2" />
              Testar Regra
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
