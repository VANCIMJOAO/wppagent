'use client'

import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { debugLog } from '@/lib/debug';
import ReportExportComponent from '@/components/ReportExportComponent';
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
  const searchParams = useSearchParams();
  
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

  // Ler parâmetro da URL para definir tab inicial
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && ['overview', 'funnel', 'performance', 'trends', 'export'].includes(tab)) {
      setActiveTab(tab);
    }
  }, [searchParams]);

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
      debugLog.error('Erro ao carregar dados de relatórios:', error)
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
      debugLog.error('Erro ao carregar dados temporais:', error)
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
      debugLog.error('Erro ao exportar dados:', error)
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
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-white min-h-screen">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Relatórios</h1>
          <p className="text-gray-600 mt-2 text-lg">
            Analytics abrangentes e insights de negócio
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            onClick={loadAllData}
            disabled={isLoading}
            variant="outline"
            className="h-10 shadow-sm hover:shadow-md transition-all hover:scale-105"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {/* Main Analytics Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 bg-white p-1.5 rounded-xl shadow-md">
          <TabsTrigger 
            value="overview" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <Eye className="h-4 w-4" />
            Visão Geral
          </TabsTrigger>
          <TabsTrigger 
            value="funnel" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <Target className="h-4 w-4" />
            Funil
          </TabsTrigger>
          <TabsTrigger 
            value="performance" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <Activity className="h-4 w-4" />
            Performance
          </TabsTrigger>
          <TabsTrigger 
            value="trends" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <LineChartIcon className="h-4 w-4" />
            Tendências
          </TabsTrigger>
          <TabsTrigger 
            value="export" 
            className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            <Download className="h-4 w-4" />
            Exportar
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          {businessOverview && (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-green-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-600 mb-2">Receita Total</p>
                        <p className="text-3xl font-bold text-gray-900 mb-3">
                          {formatCurrency(businessOverview.total_revenue)}
                        </p>
                        <div className={`flex items-center gap-1.5 text-xs font-medium ${getTrendColor(businessOverview.revenue_growth)}`}>
                          {getTrendIcon(businessOverview.revenue_growth)}
                          {formatPercentage(businessOverview.revenue_growth)} vs anterior
                        </div>
                      </div>
                      <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg">
                        <DollarSign className="h-7 w-7 text-white" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-blue-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-600 mb-2">Conversas Totais</p>
                        <p className="text-3xl font-bold text-gray-900 mb-3">
                          {formatNumber(businessOverview.total_conversations)}
                        </p>
                        <div className={`flex items-center gap-1.5 text-xs font-medium ${getTrendColor(businessOverview.conversations_growth)}`}>
                          {getTrendIcon(businessOverview.conversations_growth)}
                          {formatPercentage(businessOverview.conversations_growth)} vs anterior
                        </div>
                      </div>
                      <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
                        <MessageSquare className="h-7 w-7 text-white" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-purple-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-600 mb-2">Clientes Ativos</p>
                        <p className="text-3xl font-bold text-gray-900 mb-3">
                          {formatNumber(businessOverview.active_clients)}
                        </p>
                        <div className={`flex items-center gap-1.5 text-xs font-medium ${getTrendColor(businessOverview.clients_growth)}`}>
                          {getTrendIcon(businessOverview.clients_growth)}
                          {formatPercentage(businessOverview.clients_growth)} vs anterior
                        </div>
                      </div>
                      <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg">
                        <Users className="h-7 w-7 text-white" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-orange-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-600 mb-2">Taxa de Conversão</p>
                        <p className="text-3xl font-bold text-gray-900 mb-3">
                          {formatPercentage(businessOverview.conversion_rate)}
                        </p>
                        <div className={`flex items-center gap-1.5 text-xs font-medium ${getTrendColor(businessOverview.conversion_growth)}`}>
                          {getTrendIcon(businessOverview.conversion_growth)}
                          {formatPercentage(businessOverview.conversion_growth)} vs anterior
                        </div>
                      </div>
                      <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-orange-500 to-red-600 shadow-lg">
                        <Target className="h-7 w-7 text-white" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Revenue and Conversations Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Revenue by Source */}
                <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
                  <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                    <CardTitle className="flex items-center gap-2 text-xl font-bold">
                      <PieChartIcon className="h-5 w-5 text-primary" />
                      Receita por Fonte
                    </CardTitle>
                    <CardDescription className="text-gray-600">Distribuição de receita por canal</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
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
                        <Tooltip 
                          formatter={(value) => formatCurrency(value as number)}
                          contentStyle={{ 
                            backgroundColor: 'white', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Conversations by Status */}
                <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
                  <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                    <CardTitle className="flex items-center gap-2 text-xl font-bold">
                      <BarChart3 className="h-5 w-5 text-primary" />
                      Conversas por Status
                    </CardTitle>
                    <CardDescription className="text-gray-600">Distribuição atual das conversas</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-6">
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={businessOverview.conversations_by_status || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis dataKey="status" tick={{ fontSize: 12 }} />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip 
                          formatter={(value) => formatNumber(value as number)}
                          contentStyle={{ 
                            backgroundColor: 'white', 
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                            boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                          }}
                        />
                        <Bar dataKey="count" fill={CHART_COLORS.primary} radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        {/* Funnel Tab */}
        <TabsContent value="funnel" className="space-y-6 mt-6">
          {conversationFunnel && (
            <>
              <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
                <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                  <CardTitle className="flex items-center gap-2 text-xl font-bold">
                    <Target className="h-5 w-5 text-primary" />
                    Funil de Conversão
                  </CardTitle>
                  <CardDescription className="text-gray-600">
                    Jornada do lead até cliente convertido
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={conversationFunnel.stages || []}>
                      <defs>
                        <linearGradient id="colorFunnel" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="stage" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip 
                        formatter={(value, name) => [
                          formatNumber(value as number),
                          name === 'count' ? 'Quantidade' : name
                        ]}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="count" 
                        stroke={CHART_COLORS.primary} 
                        fill="url(#colorFunnel)"
                        fillOpacity={1}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Conversion Rates */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-blue-50/30">
                  <CardContent className="p-6">
                    <p className="text-sm font-semibold text-gray-600 mb-3">Taxa Lead → Interessado</p>
                    <p className="text-3xl font-bold text-blue-600">{formatPercentage(conversationFunnel.lead_to_interested_rate)}</p>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-purple-50/30">
                  <CardContent className="p-6">
                    <p className="text-sm font-semibold text-gray-600 mb-3">Taxa Interessado → Negociação</p>
                    <p className="text-3xl font-bold text-purple-600">{formatPercentage(conversationFunnel.interested_to_negotiation_rate)}</p>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-green-50/30">
                  <CardContent className="p-6">
                    <p className="text-sm font-semibold text-gray-600 mb-3">Taxa Negociação → Cliente</p>
                    <p className="text-3xl font-bold text-green-600">{formatPercentage(conversationFunnel.negotiation_to_client_rate)}</p>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6 mt-6">
          {performanceMetrics && (
            <>
              {/* Performance KPIs */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-blue-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-gray-600">Tempo Médio de Resposta</p>
                      <Clock className="h-5 w-5 text-blue-600" />
                    </div>
                    <p className="text-3xl font-bold text-gray-900 mb-3">{(performanceMetrics.avg_response_time || 0).toFixed(1)}s</p>
                    <Badge 
                      variant={performanceMetrics.avg_response_time < 30 ? "default" : "destructive"}
                      className="font-semibold shadow-sm"
                    >
                      {performanceMetrics.avg_response_time < 30 ? "Excelente" : "Melhorar"}
                    </Badge>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-purple-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-gray-600">Taxa de Engajamento</p>
                      <Activity className="h-5 w-5 text-purple-600" />
                    </div>
                    <p className="text-3xl font-bold text-gray-900 mb-3">{formatPercentage(performanceMetrics.engagement_rate)}</p>
                    <Badge 
                      variant={performanceMetrics.engagement_rate > 70 ? "default" : "secondary"}
                      className="font-semibold shadow-sm"
                    >
                      {performanceMetrics.engagement_rate > 70 ? "Alto" : "Médio"}
                    </Badge>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-green-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-gray-600">Satisfação do Cliente</p>
                      <Users className="h-5 w-5 text-green-600" />
                    </div>
                    <p className="text-3xl font-bold text-gray-900 mb-3">{(performanceMetrics.satisfaction_score || 0).toFixed(1)}/5</p>
                    <Badge 
                      variant={performanceMetrics.satisfaction_score > 4 ? "default" : "secondary"}
                      className="font-semibold shadow-sm"
                    >
                      {performanceMetrics.satisfaction_score > 4 ? "Muito Bom" : "Bom"}
                    </Badge>
                  </CardContent>
                </Card>

                <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-orange-50/30">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-gray-600">Mensagens por Conversa</p>
                      <MessageSquare className="h-5 w-5 text-orange-600" />
                    </div>
                    <p className="text-3xl font-bold text-gray-900 mb-3">{(performanceMetrics.messages_per_conversation || 0).toFixed(1)}</p>
                    <p className="text-xs text-gray-500 font-medium">Média por conversa</p>
                  </CardContent>
                </Card>
              </div>

              {/* Response Time Distribution */}
              <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
                <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                  <CardTitle className="flex items-center gap-2 text-xl font-bold">
                    <Clock className="h-5 w-5 text-primary" />
                    Distribuição de Tempo de Resposta
                  </CardTitle>
                  <CardDescription className="text-gray-600">Análise detalhada dos tempos de resposta</CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={performanceMetrics.response_time_distribution || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip 
                        formatter={(value) => formatNumber(value as number)}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                      />
                      <Bar dataKey="count" fill={CHART_COLORS.info} radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Trends Tab */}
        <TabsContent value="trends" className="space-y-6 mt-6">
          {/* Time Series Controls */}
          <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
              <CardTitle className="flex items-center gap-2 text-xl font-bold">
                <Filter className="h-5 w-5 text-primary" />
                Configuração do Gráfico
              </CardTitle>
              <CardDescription className="text-gray-600">Personalize a visualização dos dados temporais</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <label className="text-sm font-semibold mb-2 block text-gray-700">Métrica</label>
                  <Select value={timeSeriesMetric} onValueChange={(value: any) => setTimeSeriesMetric(value)}>
                    <SelectTrigger className="h-11 shadow-sm border-gray-300 hover:border-gray-400 transition-colors">
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
                  <label className="text-sm font-semibold mb-2 block text-gray-700">Granularidade</label>
                  <Select value={granularity} onValueChange={(value: any) => setGranularity(value)}>
                    <SelectTrigger className="h-11 shadow-sm border-gray-300 hover:border-gray-400 transition-colors">
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
            <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                <CardTitle className="flex items-center gap-2 text-xl font-bold">
                  <LineChartIcon className="h-5 w-5 text-primary" />
                  Tendência - {timeSeriesData?.metric_type ? timeSeriesData.metric_type.charAt(0).toUpperCase() + timeSeriesData.metric_type.slice(1) : 'Métrica'}
                </CardTitle>
                <CardDescription className="text-gray-600">
                  Evolução temporal da métrica selecionada
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={timeSeriesData?.data || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="timestamp" tick={{ fontSize: 12 }} />
                    <YAxis 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => 
                        timeSeriesMetric === 'revenue' ? formatCurrency(value) : formatNumber(value)
                      }
                    />
                    <Tooltip 
                      formatter={(value) => [
                        timeSeriesMetric === 'revenue' ? formatCurrency(value as number) : formatNumber(value as number),
                        timeSeriesData?.metric_type || 'Métrica'
                      ]}
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke={CHART_COLORS.primary} 
                      strokeWidth={3}
                      dot={{ fill: CHART_COLORS.primary, strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6, stroke: CHART_COLORS.primary, strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Export Tab */}
        <TabsContent value="export" className="space-y-6 mt-6">
          <ReportExportComponent />
        </TabsContent>
      </Tabs>
    </div>
  )
}