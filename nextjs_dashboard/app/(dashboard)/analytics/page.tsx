"use client";

import { useState, useEffect } from 'react';
import {
  Card, CardHeader, CardTitle, CardContent
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { debugLog } from '@/lib/debug';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Calendar,
  MessageCircle,
  DollarSign,
  Clock,
  Target,
  Activity,
  PieChart,
  LineChart,
  RefreshCw
} from 'lucide-react';
import {
  LineChart as RechartsLineChart,
  Line,
  BarChart as RechartsBarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface AnalyticsData {
  overview: {
    totalRevenue: number;
    totalClients: number;
    totalAppointments: number;
    conversionRate: number;
    avgAppointmentValue: number;
    clientRetentionRate: number;
  };
  trends: {
    revenueChange: number;
    clientsChange: number;
    appointmentsChange: number;
    conversionChange: number;
    avgTicketChange: number;
    retentionChange: number;
  };
  revenue: {
    daily: { date: string; value: number }[];
    monthly: { month: string; value: number }[];
    yearly: { year: string; value: number }[];
  };
  appointments: {
    byStatus: { status: string; count: number }[];
    byService: { service: string; count: number }[];
    byTimeSlot: { time: string; count: number }[];
  };
  clients: {
    newClients: { date: string; count: number }[];
    retention: { period: string; rate: number }[];
    demographics: { ageGroup: string; count: number }[];
  };
}

// Cores para os gráficos
const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'];

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  const [selectedTab, setSelectedTab] = useState('overview');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const refreshData = async () => {
    setLastUpdate(new Date());
    // O useEffect será executado novamente devido à mudança no timeRange
  };

  // Buscar dados reais do Railway
  useEffect(() => {
    const fetchRealData = async () => {
      try {
        setLoading(true);
        debugLog.info('🔄 Buscando dados reais da API para Analytics...');
        
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // Buscar TODOS os dados em paralelo das APIs reais
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        const [
          revenueDaily,
          revenueMonthly,
          revenueYearly,
          appointmentsByStatus,
          appointmentsByService,
          appointmentsByTime,
          newClientsDaily,
          clientRetention,
          clientDemographics
        ] = await Promise.all([
          fetch('/api/analytics/revenue?period=daily&days=7', { credentials: 'include' }),
          fetch('/api/analytics/revenue?period=monthly&months=6', { credentials: 'include' }),
          fetch('/api/analytics/revenue?period=yearly&years=3', { credentials: 'include' }),
          fetch('/api/analytics/appointments/by-status?days=30', { credentials: 'include' }),
          fetch('/api/analytics/appointments/by-service?days=30', { credentials: 'include' }),
          fetch('/api/analytics/appointments/by-timeslot?days=30', { credentials: 'include' }),
          fetch('/api/analytics/clients/new-daily?days=7', { credentials: 'include' }),
          fetch('/api/analytics/clients/retention', { credentials: 'include' }),
          fetch('/api/analytics/clients/demographics', { credentials: 'include' })
        ]);
        
        // Parse respostas com tratamento de erro
        const parseResponse = async (response: Response) => {
          if (!response.ok) {
            debugLog.warn(`API retornou ${response.status}: ${response.statusText}`);
            return { success: false, data: [] };
          }
          try {
            return await response.json();
          } catch {
            return { success: false, data: [] };
          }
        };
        
        const [
          revenueDailyData,
          revenueMonthlyData,
          revenueYearlyData,
          appointmentsStatusData,
          appointmentsServiceData,
          appointmentsTimeData,
          newClientsData,
          retentionData,
          demographicsData
        ] = await Promise.all([
          parseResponse(revenueDaily),
          parseResponse(revenueMonthly),
          parseResponse(revenueYearly),
          parseResponse(appointmentsByStatus),
          parseResponse(appointmentsByService),
          parseResponse(appointmentsByTime),
          parseResponse(newClientsDaily),
          parseResponse(clientRetention),
          parseResponse(clientDemographics)
        ]);
        
        // Calcular totais a partir dos dados reais da API
        const totalRevenue = (revenueMonthlyData.total || 0);
        const totalAppointments = (appointmentsStatusData.total || 0);
        const totalClients = (newClientsData.total || 0);
        
        debugLog.info('📊 Dados reais recebidos das APIs:');
        debugLog.info(`  - Receita total: R$ ${totalRevenue}`);
        debugLog.info(`  - Total de agendamentos: ${totalAppointments}`);
        debugLog.info(`  - Total de clientes: ${totalClients}`);
        
        
        // Calcular métricas de overview
        const conversionRate = totalClients > 0 ? (totalAppointments / totalClients) * 100 : 0;
        const avgAppointmentValue = totalAppointments > 0 ? totalRevenue / totalAppointments : 0;
        const clientRetentionRate = retentionData.data?.[0]?.rate || 0;
        
        // Montar objeto de dados com APIs reais
        const analyticsData: AnalyticsData = {
          overview: {
            totalRevenue,
            totalClients,
            totalAppointments,
            conversionRate,
            avgAppointmentValue,
            clientRetentionRate
          },
          trends: {
            revenueChange: 0,       // TODO: Implementar comparação de períodos
            clientsChange: 0,       // TODO: Implementar comparação de períodos
            appointmentsChange: 0,  // TODO: Implementar comparação de períodos
            conversionChange: 0,
            avgTicketChange: 0,
            retentionChange: 0
          },
          revenue: {
            daily: revenueDailyData.data || [],
            monthly: revenueMonthlyData.data || [],
            yearly: revenueYearlyData.data || []
          },
          appointments: {
            byStatus: appointmentsStatusData.data || [],
            byService: appointmentsServiceData.data || [],
            byTimeSlot: appointmentsTimeData.data || []
          },
          clients: {
            newClients: newClientsData.data || [],
            retention: retentionData.data || [],
            demographics: demographicsData.data || []
          }
        };

        debugLog.success(`✅ Analytics carregado com dados REAIS das APIs:`, {
          receita: totalRevenue,
          agendamentos: totalAppointments,
          clientes: totalClients,
          taxaConversao: `${conversionRate.toFixed(1)}%`,
          pontosDadosReceita: revenueDailyData.data?.length || 0,
          statusAgendamentos: appointmentsStatusData.data?.length || 0
        });
        
        setData(analyticsData);
        
      } catch (error) {
        debugLog.error('Erro ao carregar dados reais:', error);
        
        // Fallback para dados básicos se houver erro
        const fallbackData: AnalyticsData = {
          overview: {
            totalRevenue: 0,
            totalClients: 0,
            totalAppointments: 0,
            conversionRate: 0,
            avgAppointmentValue: 0,
            clientRetentionRate: 0
          },
          trends: {
            revenueChange: 0,
            clientsChange: 0,
            appointmentsChange: 0,
            conversionChange: 0,
            avgTicketChange: 0,
            retentionChange: 0
          },
          revenue: { daily: [], monthly: [], yearly: [] },
          appointments: { byStatus: [], byService: [], byTimeSlot: [] },
          clients: { newClients: [], retention: [], demographics: [] }
        };
        setData(fallbackData);
      } finally {
        setLoading(false);
      }
    };

    fetchRealData();
  }, [timeRange, lastUpdate]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getTrendIcon = (value: number, threshold: number = 0) => {
    if (value > threshold) {
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    } else if (value < threshold) {
      return <TrendingDown className="h-4 w-4 text-red-600" />;
    }
    return <Activity className="h-4 w-4 text-gray-600" />;
  };

  const getTrendColor = (value: number, threshold: number = 0) => {
    if (value > threshold) return 'text-green-600';
    if (value < threshold) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-white min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Analytics</h1>
          <p className="text-gray-600 mt-2 text-lg">
            Dashboard avançado de métricas e insights
          </p>
          {data && (
            <div className="mt-3">
              <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200 shadow-sm">
                <Activity className="w-3.5 h-3.5 mr-1.5 animate-pulse" />
                Dados Reais do Railway
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-36 h-10 shadow-sm border-gray-300 hover:border-gray-400 transition-colors">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">7 dias</SelectItem>
              <SelectItem value="30d">30 dias</SelectItem>
              <SelectItem value="90d">90 dias</SelectItem>
              <SelectItem value="1y">1 ano</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            variant="outline" 
            onClick={refreshData}
            disabled={loading}
            className="h-10 shadow-sm hover:shadow-md transition-all hover:scale-105"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button 
            variant="outline"
            className="h-10 shadow-sm hover:shadow-md transition-all hover:scale-105"
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-green-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">Receita Total</p>
                {loading ? (
                  <Skeleton className="h-8 w-24 mt-2" />
                ) : (
                  <p className="text-3xl font-bold text-gray-900 mb-3">
                    {formatCurrency(data?.overview.totalRevenue || 0)}
                  </p>
                )}
                <div className="flex items-center gap-1.5">
                  {getTrendIcon(data?.trends?.revenueChange || 0)}
                  <span className={`text-xs font-medium ${getTrendColor(data?.trends?.revenueChange || 0)}`}>
                    {data?.trends?.revenueChange ? 
                      `${data.trends.revenueChange > 0 ? '+' : ''}${data.trends.revenueChange.toFixed(1)}% vs período anterior` :
                      'Sem dados anteriores'
                    }
                  </span>
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
                <p className="text-sm font-semibold text-gray-600 mb-2">Total de Clientes</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-2" />
                ) : (
                  <p className="text-3xl font-bold text-gray-900 mb-3">
                    {data?.overview.totalClients || 0}
                  </p>
                )}
                <div className="flex items-center gap-1.5">
                  {getTrendIcon(data?.trends?.clientsChange || 0)}
                  <span className={`text-xs font-medium ${getTrendColor(data?.trends?.clientsChange || 0)}`}>
                    {data?.trends?.clientsChange ? 
                      `${data.trends.clientsChange > 0 ? '+' : ''}${data.trends.clientsChange.toFixed(1)}% vs período anterior` :
                      'Sem dados anteriores'
                    }
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
                <Users className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-purple-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">Agendamentos</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-2" />
                ) : (
                  <p className="text-3xl font-bold text-gray-900 mb-3">
                    {data?.overview.totalAppointments || 0}
                  </p>
                )}
                <div className="flex items-center gap-1.5">
                  {getTrendIcon(data?.trends?.appointmentsChange || 0)}
                  <span className={`text-xs font-medium ${getTrendColor(data?.trends?.appointmentsChange || 0)}`}>
                    {data?.trends?.appointmentsChange ? 
                      `${data.trends.appointmentsChange > 0 ? '+' : ''}${data.trends.appointmentsChange.toFixed(1)}% vs período anterior` :
                      'Sem dados anteriores'
                    }
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg">
                <Calendar className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-orange-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">Taxa de Conversão</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-2" />
                ) : (
                  <p className="text-3xl font-bold text-gray-900 mb-3">
                    {formatPercentage(data?.overview.conversionRate || 0)}
                  </p>
                )}
                <div className="flex items-center gap-1.5">
                  {getTrendIcon(data?.trends?.conversionChange || 0)}
                  <span className={`text-xs font-medium ${getTrendColor(data?.trends?.conversionChange || 0)}`}>
                    {data?.trends?.conversionChange ? 
                      `${data.trends.conversionChange > 0 ? '+' : ''}${data.trends.conversionChange.toFixed(1)}% vs período anterior` :
                      'Estável'
                    }
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-orange-500 to-red-600 shadow-lg">
                <Target className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-indigo-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">Ticket Médio</p>
                {loading ? (
                  <Skeleton className="h-8 w-20 mt-2" />
                ) : (
                  <p className="text-3xl font-bold text-gray-900 mb-3">
                    {formatCurrency(data?.overview.avgAppointmentValue || 0)}
                  </p>
                )}
                <div className="flex items-center gap-1.5">
                  {getTrendIcon(data?.trends?.avgTicketChange || 0)}
                  <span className={`text-xs font-medium ${getTrendColor(data?.trends?.avgTicketChange || 0)}`}>
                    {data?.trends?.avgTicketChange ? 
                      `${data.trends.avgTicketChange > 0 ? '+' : ''}${data.trends.avgTicketChange.toFixed(1)}% vs período anterior` :
                      'Estável'
                    }
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
                <DollarSign className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-teal-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">Retenção de Clientes</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-2" />
                ) : (
                  <p className="text-3xl font-bold text-gray-900 mb-3">
                    {formatPercentage(data?.overview.clientRetentionRate || 0)}
                  </p>
                )}
                <div className="flex items-center gap-1.5">
                  {getTrendIcon(data?.trends?.retentionChange || 0)}
                  <span className={`text-xs font-medium ${getTrendColor(data?.trends?.retentionChange || 0)}`}>
                    {data?.trends?.retentionChange ? 
                      `${data.trends.retentionChange > 0 ? '+' : ''}${data.trends.retentionChange.toFixed(1)}% vs período anterior` :
                      'Estável'
                    }
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 shadow-lg">
                <Users className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs de Análises Detalhadas */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-white p-1.5 rounded-xl shadow-md">
          <TabsTrigger 
            value="overview"
            className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            Visão Geral
          </TabsTrigger>
          <TabsTrigger 
            value="revenue"
            className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            Receita
          </TabsTrigger>
          <TabsTrigger 
            value="appointments"
            className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            Agendamentos
          </TabsTrigger>
          <TabsTrigger 
            value="clients"
            className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-primary data-[state=active]:to-primary/90 data-[state=active]:text-white data-[state=active]:shadow-md transition-all duration-200 rounded-lg font-semibold"
          >
            Clientes
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                <CardTitle className="flex items-center gap-2 text-xl font-bold">
                  <LineChart className="h-5 w-5 text-primary" />
                  Receita por Período
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <RechartsLineChart data={data?.revenue.daily || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                      />
                      <YAxis 
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => `R$ ${value}`}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                        labelFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                        formatter={(value: number) => [`R$ ${value.toFixed(2)}`, 'Receita']}
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#3b82f6" 
                        strokeWidth={3}
                        dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6 }}
                        name="Receita Diária"
                      />
                    </RechartsLineChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                <CardTitle className="flex items-center gap-2 text-xl font-bold">
                  <PieChart className="h-5 w-5 text-primary" />
                  Distribuição de Serviços
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <RechartsPieChart>
                      <Pie
                        data={data?.appointments.byService || []}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ service, count, percent }) => 
                          `${service}: ${count} (${(percent * 100).toFixed(0)}%)`
                        }
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {data?.appointments.byService.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                      />
                      <Legend 
                        verticalAlign="bottom" 
                        height={36}
                        formatter={(value, entry: any) => entry.payload.service}
                      />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="revenue" className="space-y-6 mt-6">
          <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
            <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
              <CardTitle className="flex items-center gap-2 text-xl font-bold">
                <BarChart3 className="h-5 w-5 text-primary" />
                Análise de Receita
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              {loading ? (
                <Skeleton className="h-96 w-full" />
              ) : (
                <ResponsiveContainer width="100%" height={400}>
                  <RechartsBarChart data={data?.revenue.monthly || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="month" 
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => `R$ ${value}`}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'white', 
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                      }}
                      formatter={(value: number) => [`R$ ${value.toFixed(2)}`, 'Receita']}
                    />
                    <Legend />
                    <Bar 
                      dataKey="value" 
                      fill="#10b981"
                      name="Receita Mensal"
                      radius={[8, 8, 0, 0]}
                    />
                  </RechartsBarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appointments" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                <CardTitle className="flex items-center gap-2 text-xl font-bold">
                  <Activity className="h-5 w-5 text-primary" />
                  Agendamentos por Status
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <ResponsiveContainer width="100%" height={250}>
                    <RechartsBarChart data={data?.appointments.byStatus || []} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis type="number" tick={{ fontSize: 12 }} />
                      <YAxis dataKey="status" type="category" tick={{ fontSize: 12 }} width={100} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                      />
                      <Bar dataKey="count" fill="#8b5cf6" name="Quantidade" radius={[0, 8, 8, 0]} />
                    </RechartsBarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                <CardTitle className="flex items-center gap-2 text-xl font-bold">
                  <Clock className="h-5 w-5 text-primary" />
                  Agendamentos por Horário
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <ResponsiveContainer width="100%" height={250}>
                    <RechartsBarChart data={data?.appointments.byTimeSlot || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="time" 
                        tick={{ fontSize: 11 }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                      />
                      <Bar dataKey="count" fill="#ec4899" name="Agendamentos" radius={[8, 8, 0, 0]} />
                    </RechartsBarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="clients" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                <CardTitle className="flex items-center gap-2 text-xl font-bold">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Novos Clientes
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={data?.clients.newClients || []}>
                      <defs>
                        <linearGradient id="colorClients" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => new Date(value).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                      />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                        labelFormatter={(value) => new Date(value).toLocaleDateString('pt-BR')}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="count" 
                        stroke="#06b6d4" 
                        fillOpacity={1} 
                        fill="url(#colorClients)"
                        name="Novos Clientes"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <Card className="border-0 shadow-xl hover:shadow-2xl transition-all duration-300 bg-gradient-to-br from-white to-gray-50">
              <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
                <CardTitle className="flex items-center gap-2 text-xl font-bold">
                  <Users className="h-5 w-5 text-primary" />
                  Demografia por Idade
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <ResponsiveContainer width="100%" height={250}>
                    <RechartsBarChart data={data?.clients.demographics || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="ageGroup" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                      />
                      <Bar dataKey="count" fill="#f59e0b" name="Quantidade" radius={[8, 8, 0, 0]} />
                    </RechartsBarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}