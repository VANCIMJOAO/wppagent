'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from 'recharts'
import { 
  Calendar,
  Download,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  MessageSquare,
  Target,
  Clock,
  Activity,
  FileText,
  Filter,
  Eye,
  BarChart3,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon
} from 'lucide-react'

// Import API service methods
import { 
  getBusinessOverview, 
  getConversationFunnel, 
  getPerformanceMetrics, 
  getTimeSeriesData, 
  exportAnalytics 
} from '@/lib/api-service-robust'

// Import types
import type { 
  BusinessOverview, 
  ConversationFunnel, 
  PerformanceMetrics, 
  TimeSeriesData 
} from '@/types/analytics'

// Color palette for charts
const CHART_COLORS = {
  primary: '#3B82F6',    // blue-500
  secondary: '#10B981',  // emerald-500
  accent: '#F59E0B',     // amber-500
  danger: '#EF4444',     // red-500
  warning: '#F97316',    // orange-500
  info: '#6366F1',       // indigo-500
  success: '#22C55E',    // green-500
  muted: '#6B7280'       // gray-500
}

const FUNNEL_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']

export default function RelatoriosPage() {
  // State for data
  const [businessOverview, setBusinessOverview] = useState<BusinessOverview | null>(null)
  const [conversationFunnel, setConversationFunnel] = useState<ConversationFunnel | null>(null)
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null)
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData | null>(null)

  // State for UI controls
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    to: new Date()
  })
  const [timeSeriesMetric, setTimeSeriesMetric] = useState<'conversations' | 'revenue' | 'appointments' | 'clients'>('conversations')
  const [granularity, setGranularity] = useState<'hour' | 'day' | 'week' | 'month'>('day')
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  // Load initial data
  useEffect(() => {
    loadAllData()
  }, [dateRange])

  // Load time series data when metric or granularity changes
  useEffect(() => {
    loadTimeSeriesData()
  }, [timeSeriesMetric, granularity, dateRange])

  const loadAllData = async () => {
    setIsLoading(true)
    try {
      const startDate = dateRange?.from ? formatDate(dateRange.from) : undefined
      const endDate = dateRange?.to ? formatDate(dateRange.to) : undefined

      const [overviewResponse, funnelResponse, performanceResponse] = await Promise.all([
        getBusinessOverview(startDate, endDate),
        getConversationFunnel(startDate, endDate),
        getPerformanceMetrics(startDate, endDate)
      ])

      // Acessa os dados das respostas da API
      setBusinessOverview(overviewResponse.data)
      setConversationFunnel(funnelResponse.data)
      setPerformanceMetrics(performanceResponse.data)
    } catch (error) {
      console.error('Erro ao carregar dados de relatórios:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadTimeSeriesData = async () => {
    try {
      const startDate = dateRange?.from ? formatDate(dateRange.from) : undefined
      const endDate = dateRange?.to ? formatDate(dateRange.to) : undefined

      const timeSeriesResponse = await getTimeSeriesData(timeSeriesMetric, granularity, startDate, endDate)
      setTimeSeriesData(timeSeriesResponse.data)
    } catch (error) {
      console.error('Erro ao carregar dados temporais:', error)
    }
  }

  const handleExport = async (format: 'json' | 'csv' | 'excel') => {
    try {
      const startDate = dateRange?.from ? formatDate(dateRange.from) : undefined
      const endDate = dateRange?.to ? formatDate(dateRange.to) : undefined

      const exportResponse = await exportAnalytics('full', format, startDate, endDate)
      const blob = exportResponse.data
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `relatorio-completo-${format === 'excel' ? 'xlsx' : format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Erro ao exportar dados:', error)
    }
  }

  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0]
  }

  const formatCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null || isNaN(value)) {
      return 'R$ 0,00'
    }
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value)
  }

  const formatPercentage = (value: number | undefined | null) => {
    if (value === undefined || value === null || isNaN(value)) {
      return '0.0%'
    }
    return `${value.toFixed(1)}%`
  }

  const formatNumber = (value: number | undefined | null) => {
    if (value === undefined || value === null || isNaN(value)) {
      return '0'
    }
    return new Intl.NumberFormat('pt-BR').format(value)
  }

  const getTrendIcon = (trend: number | undefined | null) => {
    if (trend === undefined || trend === null || isNaN(trend)) {
      return <Activity className="h-4 w-4 text-gray-500" />
    }
    if (trend > 0) return <TrendingUp className="h-4 w-4 text-green-500" />
    if (trend < 0) return <TrendingDown className="h-4 w-4 text-red-500" />
    return <Activity className="h-4 w-4 text-gray-500" />
  }

  const getTrendColor = (trend: number | undefined | null) => {
    if (trend === undefined || trend === null || isNaN(trend)) {
      return 'text-gray-500'
    }
    if (trend > 0) return 'text-green-500'
    if (trend < 0) return 'text-red-500'
    return 'text-gray-500'
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Executivos</h1>
          <p className="text-muted-foreground">
            Relatórios abrangentes e insights de negócio
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2">
          <Button
            onClick={loadAllData}
            disabled={isLoading}
            size="sm"
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {/* Export Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Exportar Relatórios
          </CardTitle>
          <CardDescription>
            Baixe os dados em diferentes formatos para análise externa
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => handleExport('csv')} variant="outline" size="sm">
              <FileText className="h-4 w-4 mr-2" />
              CSV
            </Button>
            <Button onClick={() => handleExport('excel')} variant="outline" size="sm">
              <BarChart3 className="h-4 w-4 mr-2" />
              Excel
            </Button>
            <Button onClick={() => handleExport('json')} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              JSON
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Analytics Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Visão Geral
          </TabsTrigger>
          <TabsTrigger value="funnel" className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Funil
          </TabsTrigger>
          <TabsTrigger value="performance" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Performance
          </TabsTrigger>
          <TabsTrigger value="trends" className="flex items-center gap-2">
            <LineChartIcon className="h-4 w-4" />
            Tendências
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {businessOverview && (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Receita Total</CardTitle>
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatCurrency(businessOverview.total_revenue)}</div>
                    <div className={`text-xs flex items-center gap-1 ${getTrendColor(businessOverview.revenue_growth)}`}>
                      {getTrendIcon(businessOverview.revenue_growth)}
                      {formatPercentage(businessOverview.revenue_growth)} vs período anterior
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Conversas Totais</CardTitle>
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatNumber(businessOverview.total_conversations)}</div>
                    <div className={`text-xs flex items-center gap-1 ${getTrendColor(businessOverview.conversations_growth)}`}>
                      {getTrendIcon(businessOverview.conversations_growth)}
                      {formatPercentage(businessOverview.conversations_growth)} vs período anterior
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Clientes Ativos</CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatNumber(businessOverview.active_clients)}</div>
                    <div className={`text-xs flex items-center gap-1 ${getTrendColor(businessOverview.clients_growth)}`}>
                      {getTrendIcon(businessOverview.clients_growth)}
                      {formatPercentage(businessOverview.clients_growth)} vs período anterior
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Taxa de Conversão</CardTitle>
                    <Target className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatPercentage(businessOverview.conversion_rate)}</div>
                    <div className={`text-xs flex items-center gap-1 ${getTrendColor(businessOverview.conversion_growth)}`}>
                      {getTrendIcon(businessOverview.conversion_growth)}
                      {formatPercentage(businessOverview.conversion_growth)} vs período anterior
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Revenue and Conversations Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Revenue by Source */}
                <Card>
                  <CardHeader>
                    <CardTitle>Receita por Fonte</CardTitle>
                    <CardDescription>Distribuição de receita por canal</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={businessOverview.revenue_by_source || []}
                          dataKey="value"
                          nameKey="source"
                          cx="50%"
                          cy="50%"
                          outerRadius={100}
                          label={({ source, percent }) => `${source}: ${((percent || 0) * 100).toFixed(1)}%`}
                        >
                          {(businessOverview.revenue_by_source || []).map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={FUNNEL_COLORS[index % FUNNEL_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => formatCurrency(value as number)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Conversations by Status */}
                <Card>
                  <CardHeader>
                    <CardTitle>Conversas por Status</CardTitle>
                    <CardDescription>Distribuição atual das conversas</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={businessOverview.conversations_by_status || []}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="status" />
                        <YAxis />
                        <Tooltip formatter={(value) => formatNumber(value as number)} />
                        <Bar dataKey="count" fill={CHART_COLORS.primary} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        {/* Funnel Tab */}
        <TabsContent value="funnel" className="space-y-6">
          {conversationFunnel && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Funil de Conversão</CardTitle>
                  <CardDescription>
                    Jornada do lead até cliente convertido
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={conversationFunnel.stages || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="stage" />
                      <YAxis />
                      <Tooltip 
                        formatter={(value, name) => [
                          formatNumber(value as number),
                          name === 'count' ? 'Quantidade' : name
                        ]}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="count" 
                        stroke={CHART_COLORS.primary} 
                        fill={CHART_COLORS.primary}
                        fillOpacity={0.3}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Conversion Rates */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Taxa Lead → Interessado</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatPercentage(conversationFunnel.lead_to_interested_rate)}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Taxa Interessado → Negociação</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatPercentage(conversationFunnel.interested_to_negotiation_rate)}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Taxa Negociação → Cliente</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatPercentage(conversationFunnel.negotiation_to_client_rate)}</div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          {performanceMetrics && (
            <>
              {/* Performance KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Tempo Médio de Resposta</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{(performanceMetrics.avg_response_time || 0).toFixed(1)}s</div>
                    <Badge variant={performanceMetrics.avg_response_time < 30 ? "default" : "destructive"}>
                      {performanceMetrics.avg_response_time < 30 ? "Excelente" : "Melhorar"}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Taxa de Engajamento</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{formatPercentage(performanceMetrics.engagement_rate)}</div>
                    <Badge variant={performanceMetrics.engagement_rate > 70 ? "default" : "secondary"}>
                      {performanceMetrics.engagement_rate > 70 ? "Alto" : "Médio"}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Satisfação do Cliente</CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{(performanceMetrics.satisfaction_score || 0).toFixed(1)}/5</div>
                    <Badge variant={performanceMetrics.satisfaction_score > 4 ? "default" : "secondary"}>
                      {performanceMetrics.satisfaction_score > 4 ? "Muito Bom" : "Bom"}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Mensagens por Conversa</CardTitle>
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{(performanceMetrics.messages_per_conversation || 0).toFixed(1)}</div>
                    <p className="text-xs text-muted-foreground">Média por conversa</p>
                  </CardContent>
                </Card>
              </div>

              {/* Response Time Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Distribuição de Tempo de Resposta</CardTitle>
                  <CardDescription>Análise detalhada dos tempos de resposta</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={performanceMetrics.response_time_distribution || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="range" />
                      <YAxis />
                      <Tooltip formatter={(value) => formatNumber(value as number)} />
                      <Bar dataKey="count" fill={CHART_COLORS.info} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-6">
          {/* Time Series Controls */}
          <Card>
            <CardHeader>
              <CardTitle>Configuração do Gráfico</CardTitle>
              <CardDescription>Personalize a visualização dos dados temporais</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <label className="text-sm font-medium mb-2 block">Métrica</label>
                  <Select value={timeSeriesMetric} onValueChange={(value: any) => setTimeSeriesMetric(value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="conversations">Conversas</SelectItem>
                      <SelectItem value="revenue">Receita</SelectItem>
                      <SelectItem value="appointments">Agendamentos</SelectItem>
                      <SelectItem value="clients">Clientes</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex-1">
                  <label className="text-sm font-medium mb-2 block">Granularidade</label>
                  <Select value={granularity} onValueChange={(value: any) => setGranularity(value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hour">Por Hora</SelectItem>
                      <SelectItem value="day">Por Dia</SelectItem>
                      <SelectItem value="week">Por Semana</SelectItem>
                      <SelectItem value="month">Por Mês</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Time Series Chart */}
          {timeSeriesData && (
            <Card>
              <CardHeader>
                <CardTitle>
                  Tendência - {timeSeriesData?.metric_type ? timeSeriesData.metric_type.charAt(0).toUpperCase() + timeSeriesData.metric_type.slice(1) : 'Métrica'}
                </CardTitle>
                <CardDescription>
                  Evolução temporal da métrica selecionada
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={timeSeriesData?.data || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis 
                      tickFormatter={(value) => 
                        timeSeriesMetric === 'revenue' ? formatCurrency(value) : formatNumber(value)
                      }
                    />
                    <Tooltip 
                      formatter={(value) => [
                        timeSeriesMetric === 'revenue' ? formatCurrency(value as number) : formatNumber(value as number),
                        timeSeriesData?.metric_type || 'Métrica'
                      ]}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke={CHART_COLORS.primary} 
                      strokeWidth={2}
                      dot={{ fill: CHART_COLORS.primary, strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, stroke: CHART_COLORS.primary, strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}