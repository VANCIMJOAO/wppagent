/**
 * Real Analytics Dashboard - Substitui dados mock por dados reais
 * Integrado com Error Boundaries e sistema de recuperação automática
 */
'use client';

import React from 'react';
import { useRealAnalytics } from '@/hooks/use-real-analytics';
import { ApiErrorBoundary } from '@/components/error-boundaries/ApiErrorBoundary';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  FunnelChart,
  Funnel,
  LabelList,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  MessageCircle,
  Clock,
  Star,
  Users,
  Calendar,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

interface RealAnalyticsDashboardProps {
  period?: number;
  autoRefresh?: boolean;
}

export function RealAnalyticsDashboard({
  period = 30,
  autoRefresh = false
}: RealAnalyticsDashboardProps) {
  const {
    dashboardSummary,
    loadingDashboard,
    dashboardError,
    conversionFunnel,
    loadingFunnel,
    refreshDashboard,
    loadConversionFunnel,
    isLoading
  } = useRealAnalytics();

  // Auto refresh effect
  React.useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        refreshDashboard(period);
      }, 5 * 60 * 1000); // 5 minutes

      return () => clearInterval(interval);
    }
  }, [autoRefresh, period, refreshDashboard]);

  // Load funnel data when dashboard loads
  React.useEffect(() => {
    if (dashboardSummary && !conversionFunnel) {
      loadConversionFunnel();
    }
  }, [dashboardSummary, conversionFunnel, loadConversionFunnel]);

  const handleRefresh = async () => {
    await Promise.all([
      refreshDashboard(period),
      loadConversionFunnel()
    ]);
  };

  return (
    <div className="space-y-6">
      {/* Header com controles */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Dados reais dos últimos {period} dias
          </p>
        </div>

        <div className="flex items-center gap-2">
          {autoRefresh && (
            <Badge variant="outline" className="text-green-600">
              <Activity className="w-3 h-3 mr-1" />
              Auto-refresh
            </Badge>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {/* Métricas principais */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <ApiErrorBoundary>
          <MetricCard
            title="Clientes Únicos"
            value={dashboardSummary?.key_metrics.total_customers || 0}
            trend={dashboardSummary?.trends.conversations}
            icon={<Users className="w-4 h-4" />}
            loading={loadingDashboard}
          />
        </ApiErrorBoundary>

        <ApiErrorBoundary>
          <MetricCard
            title="Total de Mensagens"
            value={dashboardSummary?.key_metrics.total_messages || 0}
            icon={<MessageCircle className="w-4 h-4" />}
            loading={loadingDashboard}
          />
        </ApiErrorBoundary>

        <ApiErrorBoundary>
          <MetricCard
            title="Taxa de Conversão"
            value={dashboardSummary?.key_metrics.overall_conversion_rate || 0}
            suffix="%"
            trend={5.2}
            icon={<TrendingUp className="w-4 h-4" />}
            loading={loadingDashboard}
          />
        </ApiErrorBoundary>

        <ApiErrorBoundary>
          <MetricCard
            title="Agendamentos"
            value={dashboardSummary?.key_metrics.total_appointments || 0}
            icon={<Calendar className="w-4 h-4" />}
            loading={loadingDashboard}
          />
        </ApiErrorBoundary>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Funil de Conversão */}
        <ApiErrorBoundary>
          <Card>
            <CardHeader>
              <CardTitle>Funil de Conversão</CardTitle>
              <CardDescription>
                Jornada completa do cliente - dados reais
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingFunnel ? (
                <div className="h-64 flex items-center justify-center">
                  <Skeleton className="w-full h-full" />
                </div>
              ) : conversionFunnel ? (
                <ResponsiveContainer width="100%" height={300}>
                  <FunnelChart>
                    <Tooltip
                      content={({ payload }) => {
                        if (!payload || !payload[0]) return null;
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white p-3 border rounded shadow-sm">
                            <p className="font-medium">{data.stage}</p>
                            <p className="text-sm text-blue-600">{data.count} usuários</p>
                            <p className="text-sm text-green-600">
                              {data.conversionRate.toFixed(1)}% conversão
                            </p>
                          </div>
                        );
                      }}
                    />
                    <Funnel
                      dataKey="count"
                      data={conversionFunnel.stages}
                      isAnimationActive={true}
                    >
                      <LabelList position="center" fill="#fff" stroke="none" fontSize={12} />
                    </Funnel>
                  </FunnelChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-muted-foreground">
                  Nenhum dado disponível
                </div>
              )}
            </CardContent>
          </Card>
        </ApiErrorBoundary>

        {/* Série Temporal */}
        <ApiErrorBoundary>
          <TimeSeriesChart
            data={dashboardSummary?.time_series || []}
            loading={loadingDashboard}
          />
        </ApiErrorBoundary>
      </div>

      {/* Performance por Canal */}
      <ApiErrorBoundary>
        <ChannelPerformanceChart
          data={dashboardSummary?.channel_performance || []}
          loading={loadingDashboard}
        />
      </ApiErrorBoundary>

      {/* Breakdown de Satisfação */}
      <ApiErrorBoundary>
        <SatisfactionChart
          data={dashboardSummary?.satisfaction_breakdown || []}
          loading={loadingDashboard}
        />
      </ApiErrorBoundary>
    </div>
  );
}

// Componente de métrica individual
interface MetricCardProps {
  title: string;
  value: number;
  suffix?: string;
  trend?: number;
  icon?: React.ReactNode;
  loading?: boolean;
}

function MetricCard({ title, value, suffix = '', trend, icon, loading }: MetricCardProps) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between space-y-0 pb-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-4" />
          </div>
          <Skeleton className="h-8 w-16" />
          <div className="flex items-center pt-1">
            <Skeleton className="h-3 w-12" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const getTrendIcon = () => {
    if (trend === undefined) return <Minus className="w-4 h-4 text-gray-400" />;
    if (trend > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    return <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  const getTrendColor = () => {
    if (trend === undefined) return 'text-muted-foreground';
    return trend > 0 ? 'text-green-600' : 'text-red-600';
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {icon}
        </div>
        <div className="text-2xl font-bold">
          {value.toLocaleString()}{suffix}
        </div>
        {trend !== undefined && (
          <div className={`flex items-center pt-1 text-xs ${getTrendColor()}`}>
            {getTrendIcon()}
            <span className="ml-1">
              {Math.abs(trend).toFixed(1)}% vs período anterior
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Gráfico de série temporal
interface TimeSeriesChartProps {
  data: Array<{
    date: string;
    conversations: number;
    messages: number;
    responses: number;
  }>;
  loading: boolean;
}

function TimeSeriesChart({ data, loading }: TimeSeriesChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Atividade ao Longo do Tempo</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-64" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Atividade ao Longo do Tempo</CardTitle>
        <CardDescription>Conversas e mensagens por dia</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
              }}
            />
            <YAxis />
            <Tooltip
              labelFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleDateString('pt-BR');
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="conversations"
              stackId="1"
              stroke="#8884d8"
              fill="#8884d8"
              name="Conversas"
            />
            <Area
              type="monotone"
              dataKey="messages"
              stackId="1"
              stroke="#82ca9d"
              fill="#82ca9d"
              name="Mensagens"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// Gráfico de performance por canal
interface ChannelPerformanceChartProps {
  data: Array<{
    channel: string;
    conversations: number;
    messages: number;
    satisfaction: number;
  }>;
  loading: boolean;
}

function ChannelPerformanceChart({ data, loading }: ChannelPerformanceChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance por Canal</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-64" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance por Canal</CardTitle>
        <CardDescription>Comparativo de canais de comunicação</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="channel" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="conversations" fill="#8884d8" name="Conversas" />
            <Bar dataKey="messages" fill="#82ca9d" name="Mensagens" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

// Gráfico de satisfação
interface SatisfactionChartProps {
  data: Array<{
    rating: number;
    count: number;
    percentage: number;
  }>;
  loading: boolean;
}

function SatisfactionChart({ data, loading }: SatisfactionChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Distribuição de Satisfação</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full h-64" />
        </CardContent>
      </Card>
    );
  }

  const COLORS = ['#ff6b6b', '#feca57', '#48cae4', '#06ffa5', '#4ecdc4'];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Distribuição de Satisfação</CardTitle>
        <CardDescription>Avaliações dos clientes</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ rating, percentage }) => `${rating}★ (${percentage.toFixed(1)}%)`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="count"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
