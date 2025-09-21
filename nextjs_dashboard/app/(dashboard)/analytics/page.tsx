"use client";

import { useState, useEffect } from 'react';
import {
  Card, CardHeader, CardTitle, CardContent
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  LineChart
} from 'lucide-react';

interface AnalyticsData {
  overview: {
    totalRevenue: number;
    totalClients: number;
    totalAppointments: number;
    conversionRate: number;
    avgAppointmentValue: number;
    clientRetentionRate: number;
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

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  const [selectedTab, setSelectedTab] = useState('overview');

  // Mock data para demonstração
  useEffect(() => {
    const mockData: AnalyticsData = {
      overview: {
        totalRevenue: 125000,
        totalClients: 245,
        totalAppointments: 892,
        conversionRate: 78.5,
        avgAppointmentValue: 140,
        clientRetentionRate: 85.2
      },
      revenue: {
        daily: [
          { date: '2024-01-01', value: 1200 },
          { date: '2024-01-02', value: 1500 },
          { date: '2024-01-03', value: 1800 },
          { date: '2024-01-04', value: 2100 },
          { date: '2024-01-05', value: 1900 },
          { date: '2024-01-06', value: 2200 },
          { date: '2024-01-07', value: 2500 }
        ],
        monthly: [
          { month: 'Jan', value: 45000 },
          { month: 'Fev', value: 52000 },
          { month: 'Mar', value: 48000 },
          { month: 'Abr', value: 55000 },
          { month: 'Mai', value: 60000 },
          { month: 'Jun', value: 58000 }
        ],
        yearly: [
          { year: '2022', value: 450000 },
          { year: '2023', value: 520000 },
          { year: '2024', value: 580000 }
        ]
      },
      appointments: {
        byStatus: [
          { status: 'Confirmado', count: 156 },
          { status: 'Pendente', count: 23 },
          { status: 'Cancelado', count: 12 },
          { status: 'Realizado', count: 134 }
        ],
        byService: [
          { service: 'Limpeza de Pele', count: 89 },
          { service: 'Hidrofacial', count: 67 },
          { service: 'Criolipólise', count: 45 },
          { service: 'Massagem', count: 78 },
          { service: 'Outros', count: 23 }
        ],
        byTimeSlot: [
          { time: '08:00-10:00', count: 45 },
          { time: '10:00-12:00', count: 78 },
          { time: '12:00-14:00', count: 23 },
          { time: '14:00-16:00', count: 89 },
          { time: '16:00-18:00', count: 67 },
          { time: '18:00-20:00', count: 34 }
        ]
      },
      clients: {
        newClients: [
          { date: '2024-01-01', count: 5 },
          { date: '2024-01-02', count: 8 },
          { date: '2024-01-03', count: 12 },
          { date: '2024-01-04', count: 6 },
          { date: '2024-01-05', count: 9 },
          { date: '2024-01-06', count: 15 },
          { date: '2024-01-07', count: 11 }
        ],
        retention: [
          { period: '1 mês', rate: 95.2 },
          { period: '3 meses', rate: 87.8 },
          { period: '6 meses', rate: 82.1 },
          { period: '1 ano', rate: 78.5 }
        ],
        demographics: [
          { ageGroup: '18-25', count: 45 },
          { ageGroup: '26-35', count: 89 },
          { ageGroup: '36-45', count: 67 },
          { ageGroup: '46-55', count: 34 },
          { ageGroup: '55+', count: 10 }
        ]
      }
    };

    setTimeout(() => {
      setData(mockData);
      setLoading(false);
    }, 1000);
  }, []);

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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">Dashboard avançado de métricas e insights</p>
        </div>
        <div className="flex items-center space-x-4">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">7 dias</SelectItem>
              <SelectItem value="30d">30 dias</SelectItem>
              <SelectItem value="90d">90 dias</SelectItem>
              <SelectItem value="1y">1 ano</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <BarChart3 className="h-4 w-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Receita Total</p>
                {loading ? (
                  <Skeleton className="h-8 w-24 mt-2" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(data?.overview.totalRevenue || 0)}
                  </p>
                )}
                <div className="flex items-center mt-2">
                  {getTrendIcon(12.5)}
                  <span className={`text-sm ml-1 ${getTrendColor(12.5)}`}>
                    +12.5% vs mês anterior
                  </span>
                </div>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total de Clientes</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-2" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">
                    {data?.overview.totalClients || 0}
                  </p>
                )}
                <div className="flex items-center mt-2">
                  {getTrendIcon(8.2)}
                  <span className={`text-sm ml-1 ${getTrendColor(8.2)}`}>
                    +8.2% vs mês anterior
                  </span>
                </div>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Agendamentos</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-2" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">
                    {data?.overview.totalAppointments || 0}
                  </p>
                )}
                <div className="flex items-center mt-2">
                  {getTrendIcon(15.3)}
                  <span className={`text-sm ml-1 ${getTrendColor(15.3)}`}>
                    +15.3% vs mês anterior
                  </span>
                </div>
              </div>
              <Calendar className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Taxa de Conversão</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-2" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">
                    {formatPercentage(data?.overview.conversionRate || 0)}
                  </p>
                )}
                <div className="flex items-center mt-2">
                  {getTrendIcon(2.1)}
                  <span className={`text-sm ml-1 ${getTrendColor(2.1)}`}>
                    +2.1% vs mês anterior
                  </span>
                </div>
              </div>
              <Target className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Ticket Médio</p>
                {loading ? (
                  <Skeleton className="h-8 w-20 mt-2" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(data?.overview.avgAppointmentValue || 0)}
                  </p>
                )}
                <div className="flex items-center mt-2">
                  {getTrendIcon(5.7)}
                  <span className={`text-sm ml-1 ${getTrendColor(5.7)}`}>
                    +5.7% vs mês anterior
                  </span>
                </div>
              </div>
              <DollarSign className="h-8 w-8 text-indigo-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Retenção de Clientes</p>
                {loading ? (
                  <Skeleton className="h-8 w-16 mt-2" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">
                    {formatPercentage(data?.overview.clientRetentionRate || 0)}
                  </p>
                )}
                <div className="flex items-center mt-2">
                  {getTrendIcon(3.2)}
                  <span className={`text-sm ml-1 ${getTrendColor(3.2)}`}>
                    +3.2% vs mês anterior
                  </span>
                </div>
              </div>
              <Users className="h-8 w-8 text-teal-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs de Análises Detalhadas */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="revenue">Receita</TabsTrigger>
          <TabsTrigger value="appointments">Agendamentos</TabsTrigger>
          <TabsTrigger value="clients">Clientes</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Receita por Período</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <LineChart className="h-12 w-12 mx-auto mb-2" />
                    <p>Gráfico de Receita</p>
                    <p className="text-sm">Implementar com biblioteca de gráficos</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Distribuição de Serviços</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <PieChart className="h-12 w-12 mx-auto mb-2" />
                    <p>Gráfico de Pizza</p>
                    <p className="text-sm">Implementar com biblioteca de gráficos</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="revenue" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Análise de Receita</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-96 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <BarChart3 className="h-16 w-16 mx-auto mb-4" />
                  <p className="text-lg">Gráficos de Receita</p>
                  <p className="text-sm">Implementar com biblioteca de gráficos</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appointments" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Agendamentos por Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data?.appointments.byStatus.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.status}</span>
                      <Badge variant="outline">{item.count}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Agendamentos por Serviço</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data?.appointments.byService.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.service}</span>
                      <Badge variant="outline">{item.count}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="clients" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Retenção de Clientes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data?.clients.retention.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.period}</span>
                      <Badge variant="outline">{formatPercentage(item.rate)}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Demografia por Idade</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data?.clients.demographics.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.ageGroup} anos</span>
                      <Badge variant="outline">{item.count}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}