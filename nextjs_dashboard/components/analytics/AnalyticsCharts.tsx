/**
 * Componentes de Gráficos Analytics - Recharts Integration
 * Visualizações interativas com dados reais do backend
 */
'use client';

import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  FunnelChart,
  Funnel,
  LabelList,
} from 'recharts';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  MessageCircle,
  Clock,
  Star
} from 'lucide-react';

// Tipos para props dos componentes
interface ChartSkeletonProps {
  height?: number;
  lines?: number;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: number;
  icon?: React.ReactNode;
  formatValue?: (value: number) => string;
}

// Skeleton loading para gráficos
export const ChartSkeleton: React.FC<ChartSkeletonProps> = ({
  height = 300,
  lines = 3
}) => (
  <div className="animate-pulse" style={{ height }}>
    <div className="h-full bg-gray-200 rounded-lg flex flex-col justify-end p-4">
      {Array.from({ length: lines }, (_, i) => (
        <div
          key={i}
          className="bg-gray-300 rounded"
          style={{
            height: `${Math.random() * 60 + 20}%`,
            marginBottom: '8px',
            width: '100%'
          }}
        />
      ))}
    </div>
  </div>
);

// Card de métrica com tendência
export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  trend,
  icon,
  formatValue
}) => {
  const displayValue = typeof value === 'number' && formatValue
    ? formatValue(value)
    : value;

  const getTrendIcon = () => {
    if (!trend) return <Minus className="w-4 h-4 text-gray-400" />;
    if (trend > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    return <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  const getTrendColor = () => {
    if (!trend) return 'text-gray-500';
    return trend > 0 ? 'text-green-600' : 'text-red-600';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {icon}
          <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        </div>
        {getTrendIcon()}
      </div>
      <div className="flex items-baseline space-x-2">
        <p className="text-2xl font-bold text-gray-900">{displayValue}</p>
        {trend && (
          <span className={`text-sm font-medium ${getTrendColor()}`}>
            {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
};

// Gráfico de linha - Conversas ao longo do tempo
export const ConversationTrendsChart: React.FC<{
  data: Array<{ date: string; conversations: number; messages: number }>;
  loading?: boolean;
}> = ({ data, loading }) => {
  if (loading) return <ChartSkeleton height={300} />;
  if (!data?.length) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <Activity className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          <p>Nenhum dado disponível</p>
        </div>
      </div>
    );
  }

  const formattedData = data.map(item => ({
    ...item,
    date: format(new Date(item.date), 'dd/MM', { locale: ptBR }),
  }));

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formattedData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            stroke="#666"
            fontSize={12}
          />
          <YAxis stroke="#666" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="conversations"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
            name="Conversas"
          />
          <Line
            type="monotone"
            dataKey="messages"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', strokeWidth: 2, r: 3 }}
            name="Mensagens"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// Gráfico de área - Volume de mensagens
export const MessageVolumeChart: React.FC<{
  data: Array<{ date: string; messages: number; responses: number }>;
  loading?: boolean;
}> = ({ data, loading }) => {
  if (loading) return <ChartSkeleton height={300} />;
  if (!data?.length) return <div className="h-64 flex items-center justify-center text-gray-500">Nenhum dado disponível</div>;

  const formattedData = data.map(item => ({
    ...item,
    date: format(new Date(item.date), 'dd/MM'),
  }));

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorMessages" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="colorResponses" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" stroke="#666" fontSize={12} />
          <YAxis stroke="#666" fontSize={12} />
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Area
            type="monotone"
            dataKey="messages"
            stackId="1"
            stroke="#3b82f6"
            fill="url(#colorMessages)"
            name="Mensagens Recebidas"
          />
          <Area
            type="monotone"
            dataKey="responses"
            stackId="1"
            stroke="#10b981"
            fill="url(#colorResponses)"
            name="Respostas Enviadas"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// Gráfico de barras - Performance por canal
export const ChannelPerformanceChart: React.FC<{
  data: Array<{ channel: string; conversations: number; avgResponseTime: number; satisfaction: number }>;
  loading?: boolean;
}> = ({ data, loading }) => {
  if (loading) return <ChartSkeleton height={300} />;
  if (!data?.length) return <div className="h-64 flex items-center justify-center text-gray-500">Nenhum dado disponível</div>;

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="channel" stroke="#666" fontSize={12} />
          <YAxis stroke="#666" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Legend />
          <Bar
            dataKey="conversations"
            fill="#3b82f6"
            name="Conversas"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// Gráfico de pizza - Distribuição de satisfação
export const SatisfactionDistributionChart: React.FC<{
  data: Array<{ rating: number; count: number; percentage: number }>;
  loading?: boolean;
}> = ({ data, loading }) => {
  if (loading) return <ChartSkeleton height={300} />;
  if (!data?.length) return <div className="h-64 flex items-center justify-center text-gray-500">Nenhum dado disponível</div>;

  const COLORS = {
    5: '#10b981', // Verde - Excelente
    4: '#3b82f6', // Azul - Bom
    3: '#f59e0b', // Amarelo - Regular
    2: '#f97316', // Laranja - Ruim
    1: '#ef4444', // Vermelho - Péssimo
  };

  const formattedData = data.map(item => ({
    name: `${item.rating} ${item.rating === 1 ? 'estrela' : 'estrelas'}`,
    value: item.count,
    percentage: item.percentage,
    rating: item.rating,
  }));

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={formattedData}
            cx="50%"
            cy="50%"
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
          >
            {formattedData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.rating as keyof typeof COLORS] || '#94a3b8'}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value} avaliações`,
              name
            ]}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

// Gráfico de funil - Conversão
export const ConversionFunnelChart: React.FC<{
  data: Array<{ stage: string; count: number; conversionRate: number }>;
  loading?: boolean;
}> = ({ data, loading }) => {
  if (loading) return <ChartSkeleton height={300} />;
  if (!data?.length) return <div className="h-64 flex items-center justify-center text-gray-500">Nenhum dado disponível</div>;

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <FunnelChart>
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value} usuários`,
              name
            ]}
          />
          <Funnel
            dataKey="count"
            data={data}
            isAnimationActive
          >
            <LabelList position="center" fill="#fff" stroke="none" />
          </Funnel>
        </FunnelChart>
      </ResponsiveContainer>
    </div>
  );
};

// Componente de resumo com múltiplas métricas
export const MetricsOverview: React.FC<{
  totalConversations: number;
  totalMessages: number;
  avgResponseTime: number;
  overallSatisfaction: number;
  trends: {
    conversations: number;
    responseTime: number;
    satisfaction: number;
  };
  loading?: boolean;
}> = ({
  totalConversations,
  totalMessages,
  avgResponseTime,
  overallSatisfaction,
  trends,
  loading
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="animate-pulse bg-gray-200 h-32 rounded-lg" />
        ))}
      </div>
    );
  }

  const formatResponseTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    return `${(seconds / 60).toFixed(1)}min`;
  };

  const formatSatisfaction = (score: number): string => {
    return `${score.toFixed(1)}/5.0`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Total de Conversas"
        value={totalConversations.toLocaleString('pt-BR')}
        trend={trends.conversations}
        icon={<MessageCircle className="w-5 h-5 text-blue-500" />}
      />

      <MetricCard
        title="Total de Mensagens"
        value={totalMessages.toLocaleString('pt-BR')}
        icon={<Activity className="w-5 h-5 text-green-500" />}
      />

      <MetricCard
        title="Tempo Médio de Resposta"
        value={formatResponseTime(avgResponseTime)}
        trend={-trends.responseTime} // Negativo pois menor tempo é melhor
        icon={<Clock className="w-5 h-5 text-orange-500" />}
      />

      <MetricCard
        title="Satisfação Média"
        value={formatSatisfaction(overallSatisfaction)}
        trend={trends.satisfaction}
        icon={<Star className="w-5 h-5 text-yellow-500" />}
      />
    </div>
  );
};

export default {
  ConversationTrendsChart,
  MessageVolumeChart,
  ChannelPerformanceChart,
  SatisfactionDistributionChart,
  ConversionFunnelChart,
  MetricsOverview,
  MetricCard,
  ChartSkeleton,
};
