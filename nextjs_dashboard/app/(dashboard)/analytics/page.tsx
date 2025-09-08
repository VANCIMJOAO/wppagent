"use client"

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  BarChart, Bar, PieChart, Pie, Cell, FunnelChart, Funnel, LabelList,
  ResponsiveContainer, AreaChart, Area
} from 'recharts'
import { 
  TrendingUp, Users, Target, Calendar, DollarSign, 
  Clock, Download, RefreshCw, AlertCircle
} from 'lucide-react'
import { ExportButtons } from '@/components/export-buttons'

interface ConversionFunnel {
  funnel_stages: {
    first_contact: number
    bot_response: number
    scheduled: number
    confirmed: number
    completed: number
  }
  conversion_rates: {
    contact_to_schedule: number
    schedule_to_confirm: number
    confirm_to_complete: number
    overall_conversion: number
  }
  recommendations: string[]
}

interface TimeAnalytics {
  hourly_patterns: Array<{
    hour: number
    hour_formatted: string
    messages: number
    unique_users: number
    response_rate: number
    efficiency_score: number
  }>
  weekly_patterns: Array<{
    day_of_week: number
    day_name: string
    messages: number
    unique_users: number
    engagement_ratio: number
  }>
  daily_trends: Array<{
    date: string
    date_formatted: string
    messages: number
    unique_users: number
    messages_ma7: number
  }>
  insights: {
    peak_hours: Array<{hour: number, messages: number}>
    busiest_days: Array<{day_name: string, messages: number}>
    activity_score: number
    consistency_score: number
  }
}

interface CustomerInsights {
  vip_customers: Array<{
    user_id: number
    name: string
    total_spent: number
    appointments: number
    loyalty_score: number
    avg_order_value: number
  }>
  high_value_prospects: Array<{
    user_id: number
    name: string
    engagement_score: number
    conversion_potential: string
  }>
  customer_summary: {
    total_vip: number
    total_churned: number
    total_prospects: number
    avg_customer_value: number
    churn_rate: number
  }
}

interface BusinessMetrics {
  revenue_metrics: {
    total_revenue: number
    total_appointments: number
    avg_order_value: number
    unique_customers: number
  }
  customer_metrics: {
    customer_acquisition_cost: number
    customer_lifetime_value: number
    ltv_to_cac_ratio: number
  }
  growth_metrics: {
    revenue_growth_percent: number
    customer_growth_percent: number
    growth_trend: string
  }
  efficiency_metrics: {
    roi_percentage: number
    cost_per_appointment: number
  }
}

export default function AdvancedAnalyticsPage() {
  const [conversionData, setConversionData] = useState<ConversionFunnel | null>(null)
  const [timeData, setTimeData] = useState<TimeAnalytics | null>(null)
  const [customerData, setCustomerData] = useState<CustomerInsights | null>(null)
  const [businessData, setBusinessData] = useState<BusinessMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState(30)
  
  const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    if (type === 'error') {
      alert(`❌ ${message}`)
    } else {
      alert(`✅ ${message}`)
    }
  }

  useEffect(() => {
    loadAnalyticsData()
  }, [selectedPeriod])

  const loadAnalyticsData = async () => {
    setLoading(true)
    setRefreshing(true)
    try {
      const [funnelRes, timeRes, customerRes, businessRes] = await Promise.all([
        fetch(`/api/analytics/funnel?days=${selectedPeriod}`),
        fetch(`/api/analytics/time-analysis?days=${selectedPeriod}`),
        fetch(`/api/analytics/customer-insights?days=${selectedPeriod}`),
        fetch(`/api/analytics/business-metrics?days=${selectedPeriod}`)
      ])

      if (!funnelRes.ok || !timeRes.ok || !customerRes.ok || !businessRes.ok) {
        throw new Error('Erro ao carregar dados')
      }

      const [funnelData, timeAnalytics, customerInsights, businessMetrics] = await Promise.all([
        funnelRes.json(),
        timeRes.json(),
        customerRes.json(),
        businessRes.json()
      ])

      setConversionData(funnelData.data)
      setTimeData(timeAnalytics.data)
      setCustomerData(customerInsights.data)
      setBusinessData(businessMetrics.data)

      showNotification(`Dados atualizados - Analytics carregadas para ${selectedPeriod} dias`)

    } catch (error) {
      console.error('Erro ao carregar analytics:', error)
      showNotification("Falha ao carregar dados de analytics", 'error')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const prepareFunnelData = () => {
    if (!conversionData) return []
    
    return [
      { 
        name: 'Primeiro Contato', 
        value: conversionData.funnel_stages.first_contact, 
        fill: '#8884d8',
        percentage: 100
      },
      { 
        name: 'Bot Response', 
        value: conversionData.funnel_stages.bot_response, 
        fill: '#82ca9d',
        percentage: (conversionData.funnel_stages.bot_response / conversionData.funnel_stages.first_contact * 100)
      },
      { 
        name: 'Agendado', 
        value: conversionData.funnel_stages.scheduled, 
        fill: '#ffc658',
        percentage: conversionData.conversion_rates.contact_to_schedule
      },
      { 
        name: 'Confirmado', 
        value: conversionData.funnel_stages.confirmed, 
        fill: '#ff7300',
        percentage: conversionData.conversion_rates.schedule_to_confirm
      },
      { 
        name: 'Realizado', 
        value: conversionData.funnel_stages.completed, 
        fill: '#00C49F',
        percentage: conversionData.conversion_rates.confirm_to_complete
      }
    ]
  }

  const exportData = async (analysisType: string, format: 'json' | 'csv' = 'json') => {
    try {
      const response = await fetch(`/api/analytics/export/${analysisType}?format=${format}&days=${selectedPeriod}`)
      
      if (format === 'csv') {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${analysisType}_${selectedPeriod}days.csv`
        a.click()
        window.URL.revokeObjectURL(url)
      } else {
        const data = await response.json()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${analysisType}_${selectedPeriod}days.json`
        a.click()
        window.URL.revokeObjectURL(url)
      }

      showNotification(`Exportação concluída - Dados exportados em formato ${format.toUpperCase()}`)
    } catch (error) {
      showNotification("Falha ao exportar dados", 'error')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 space-x-4">
        <RefreshCw className="h-6 w-6 animate-spin" />
        <span>Carregando analytics avançadas...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            📊 Analytics Avançadas
          </h1>
          <p className="text-gray-600 mt-2">Business Intelligence e Insights de Performance</p>
        </div>
        <div className="flex items-center space-x-4">
          <select 
            value={selectedPeriod} 
            onChange={(e) => setSelectedPeriod(Number(e.target.value))}
            className="border rounded-lg px-3 py-2 bg-white shadow-sm"
          >
            <option value={7}>Últimos 7 dias</option>
            <option value={30}>Últimos 30 dias</option>
            <option value={90}>Últimos 90 dias</option>
            <option value={365}>Último ano</option>
          </select>
          
          <ExportButtons 
            periodDays={selectedPeriod}
            className="bg-gradient-to-r from-green-500 to-blue-500 text-white hover:from-green-600 hover:to-blue-600"
          />
          
          <Button 
            onClick={loadAnalyticsData} 
            disabled={refreshing}
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">📈 Overview</TabsTrigger>
          <TabsTrigger value="funnel">🎯 Funil</TabsTrigger>
          <TabsTrigger value="time">🕐 Temporal</TabsTrigger>
          <TabsTrigger value="customers">👥 Clientes</TabsTrigger>
          <TabsTrigger value="business">💰 Negócio</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-r from-blue-50 to-blue-100 border-blue-200">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Target className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-blue-600">Taxa Conversão Geral</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {conversionData?.conversion_rates.overall_conversion.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-green-50 to-green-100 border-green-200">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <DollarSign className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-green-600">Receita Total</p>
                    <p className="text-2xl font-bold text-green-900">
                      R$ {businessData?.revenue_metrics.total_revenue.toFixed(2) || '0.00'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-purple-50 to-purple-100 border-purple-200">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-purple-600">Clientes VIP</p>
                    <p className="text-2xl font-bold text-purple-900">
                      {customerData?.customer_summary.total_vip || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-orange-50 to-orange-100 border-orange-200">
              <CardContent className="p-6">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-orange-600">ROI</p>
                    <p className="text-2xl font-bold text-orange-900">
                      {businessData?.efficiency_metrics.roi_percentage.toFixed(1)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Gráfico de Tendência Geral */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 mr-2" />
                Tendência de Atividade ({selectedPeriod} dias)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timeData?.daily_trends || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date_formatted" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="messages" 
                      stroke="#8884d8" 
                      fill="#8884d8" 
                      fillOpacity={0.3}
                      name="Mensagens" 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="unique_users" 
                      stroke="#82ca9d" 
                      fill="#82ca9d" 
                      fillOpacity={0.3}
                      name="Usuários Únicos" 
                    />
                    <Line 
                      type="monotone" 
                      dataKey="messages_ma7" 
                      stroke="#ff7300" 
                      strokeWidth={2}
                      name="Média Móvel 7 dias"
                      dot={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Funnel Tab */}
        <TabsContent value="funnel" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>🎯 Funil de Conversão</span>
                  <Button
                    onClick={() => exportData('funnel', 'csv')}
                    variant="outline"
                    size="sm"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Exportar
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-96 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={prepareFunnelData()} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="name" type="category" width={120} />
                      <Tooltip 
                        formatter={(value, name) => [
                          `${value} usuários (${name === 'value' ? prepareFunnelData().find(d => d.value === value)?.percentage?.toFixed(1) : 0}%)`,
                          'Quantidade'
                        ]}
                      />
                      <Bar dataKey="value" fill="#8884d8" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>📈 Taxas de Conversão</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {conversionData && Object.entries(conversionData.conversion_rates).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center">
                      <span className="text-sm font-medium capitalize">
                        {key.replace(/_/g, ' ').replace('to', '→')}
                      </span>
                      <div className="flex items-center space-x-2">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{width: `${Math.min(100, value)}%`}}
                          ></div>
                        </div>
                        <span className="text-sm font-bold text-blue-600 w-12 text-right">
                          {value.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recomendações */}
          {conversionData?.recommendations && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2" />
                  Recomendações de Otimização
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {conversionData.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-blue-500 mr-2">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Time Analysis Tab */}
        <TabsContent value="time" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Clock className="h-5 w-5 mr-2" />
                  Atividade por Hora do Dia
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={timeData?.hourly_patterns || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="hour_formatted" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="messages" fill="#8884d8" name="Mensagens" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>📅 Atividade por Dia da Semana</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={timeData?.weekly_patterns || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day_name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="messages" fill="#82ca9d" name="Mensagens" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Insights Temporais */}
          <Card>
            <CardHeader>
              <CardTitle>💡 Insights Temporais</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-blue-900">Horários de Pico</h4>
                  <ul className="mt-2 space-y-1">
                    {timeData?.insights.peak_hours.map((hour, index) => (
                      <li key={index} className="text-sm text-blue-700">
                        {hour.hour}:00 - {hour.messages} mensagens
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-green-900">Dias Mais Ativos</h4>
                  <ul className="mt-2 space-y-1">
                    {timeData?.insights.busiest_days.map((day, index) => (
                      <li key={index} className="text-sm text-green-700">
                        {day.day_name} - {day.messages} mensagens
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-purple-900">Scores</h4>
                  <div className="mt-2 space-y-2">
                    <div className="text-sm">
                      <span className="text-purple-700">Atividade: </span>
                      <span className="font-bold">{timeData?.insights.activity_score.toFixed(1)}</span>
                    </div>
                    <div className="text-sm">
                      <span className="text-purple-700">Consistência: </span>
                      <span className="font-bold">{timeData?.insights.consistency_score.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Customers Tab */}
        <TabsContent value="customers" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Clientes VIP */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <DollarSign className="h-5 w-5 mr-2 text-yellow-600" />
                  Clientes VIP ({customerData?.customer_summary.total_vip})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {customerData?.vip_customers.slice(0, 8).map((customer) => (
                    <div key={customer.user_id} className="flex justify-between items-center p-2 bg-yellow-50 rounded">
                      <div>
                        <p className="font-medium text-sm">{customer.name}</p>
                        <p className="text-xs text-gray-600">
                          {customer.appointments} agendamentos • Score: {customer.loyalty_score}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-green-600 text-sm">
                          R$ {customer.total_spent.toFixed(2)}
                        </p>
                        <p className="text-xs text-gray-500">
                          AOV: R$ {customer.avg_order_value.toFixed(2)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Prospects Alto Valor */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Target className="h-5 w-5 mr-2 text-blue-600" />
                  Prospects Alto Valor
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {customerData?.high_value_prospects.slice(0, 8).map((prospect) => (
                    <div key={prospect.user_id} className="flex justify-between items-center p-2 bg-blue-50 rounded">
                      <div>
                        <p className="font-medium text-sm">{prospect.name}</p>
                        <p className="text-xs text-gray-600">
                          Potencial: {prospect.conversion_potential}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-blue-600 text-sm">
                          {prospect.engagement_score}
                        </p>
                        <p className="text-xs text-gray-500">Score</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Resumo Geral */}
            <Card>
              <CardHeader>
                <CardTitle>📊 Resumo Clientes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-green-50 p-3 rounded">
                    <p className="text-sm text-green-600 font-medium">Valor Médio Cliente</p>
                    <p className="text-xl font-bold text-green-800">
                      R$ {customerData?.customer_summary.avg_customer_value.toFixed(2)}
                    </p>
                  </div>
                  <div className="bg-red-50 p-3 rounded">
                    <p className="text-sm text-red-600 font-medium">Taxa de Churn</p>
                    <p className="text-xl font-bold text-red-800">
                      {customerData?.customer_summary.churn_rate.toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-purple-50 p-3 rounded">
                    <p className="text-sm text-purple-600 font-medium">Prospects Ativos</p>
                    <p className="text-xl font-bold text-purple-800">
                      {customerData?.customer_summary.total_prospects}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Business Metrics Tab */}
        <TabsContent value="business" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-r from-green-50 to-green-100 border-green-200">
              <CardContent className="p-4">
                <div className="text-center">
                  <DollarSign className="h-8 w-8 text-green-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-green-600">Receita Total</p>
                  <p className="text-xl font-bold text-green-900">
                    R$ {businessData?.revenue_metrics.total_revenue.toFixed(2)}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-blue-50 to-blue-100 border-blue-200">
              <CardContent className="p-4">
                <div className="text-center">
                  <Target className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-blue-600">AOV</p>
                  <p className="text-xl font-bold text-blue-900">
                    R$ {businessData?.revenue_metrics.avg_order_value.toFixed(2)}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-purple-50 to-purple-100 border-purple-200">
              <CardContent className="p-4">
                <div className="text-center">
                  <Users className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-purple-600">LTV/CAC</p>
                  <p className="text-xl font-bold text-purple-900">
                    {businessData?.customer_metrics.ltv_to_cac_ratio.toFixed(1)}x
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-r from-orange-50 to-orange-100 border-orange-200">
              <CardContent className="p-4">
                <div className="text-center">
                  <TrendingUp className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-orange-600">ROI</p>
                  <p className="text-xl font-bold text-orange-900">
                    {businessData?.efficiency_metrics.roi_percentage.toFixed(1)}%
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Métricas Detalhadas */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>💰 Métricas de Revenue</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Total de Agendamentos:</span>
                    <span className="font-bold">{businessData?.revenue_metrics.total_appointments}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Clientes Únicos:</span>
                    <span className="font-bold">{businessData?.revenue_metrics.unique_customers}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Receita por Cliente:</span>
                    <span className="font-bold">
                      R$ {businessData ? (businessData.revenue_metrics.total_revenue / businessData.revenue_metrics.unique_customers).toFixed(2) : '0.00'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>📈 Métricas de Crescimento</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Crescimento de Receita:</span>
                    <span className={`font-bold ${businessData && businessData.growth_metrics.revenue_growth_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {businessData ? (businessData.growth_metrics.revenue_growth_percent >= 0 ? '+' : '') : ''}
                      {businessData?.growth_metrics.revenue_growth_percent.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Crescimento de Clientes:</span>
                    <span className={`font-bold ${businessData && businessData.growth_metrics.customer_growth_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {businessData ? (businessData.growth_metrics.customer_growth_percent >= 0 ? '+' : '') : ''}
                      {businessData?.growth_metrics.customer_growth_percent.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tendência:</span>
                    <span className={`font-bold ${
                      businessData?.growth_metrics.growth_trend === 'Positive' ? 'text-green-600' : 
                      businessData?.growth_metrics.growth_trend === 'Negative' ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {businessData?.growth_metrics.growth_trend === 'Positive' ? '📈 Positiva' :
                       businessData?.growth_metrics.growth_trend === 'Negative' ? '📉 Negativa' : '➡️ Estável'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Ações Rápidas */}
          <Card>
            <CardHeader>
              <CardTitle>🚀 Ações Rápidas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button 
                  onClick={() => exportData('business-metrics', 'json')}
                  variant="outline" 
                  className="flex items-center"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Exportar Métricas
                </Button>
                <Button 
                  onClick={() => exportData('customer-insights', 'csv')}
                  variant="outline"
                  className="flex items-center"
                >
                  <Users className="h-4 w-4 mr-2" />
                  Exportar Clientes
                </Button>
                <Button 
                  onClick={() => exportData('funnel', 'json')}
                  variant="outline"
                  className="flex items-center"
                >
                  <Target className="h-4 w-4 mr-2" />
                  Exportar Funil
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
