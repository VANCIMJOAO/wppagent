/**
 * Componente de Cards de Estatísticas
 * Exibe KPIs do Dashboard com dados reais do backend
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
// import type { DashboardStats } from '@/hooks/useDashboardStats'
// Define the DashboardStats type here if not exported from the hook
interface DashboardStats {
  total_clients: number;
  growth_rate?: number;
  conversations_today: number;
  total_conversations: number;
  appointments_today: number;
  total_appointments: number;
  conversion_rate?: number;
  messages_today: number;
  total_messages: number;
  new_clients_today: number;
}
import { 
  Users, 
  MessageCircle, 
  Calendar, 
  MessageSquare,
  TrendingUp,
  TrendingDown,
  UserPlus
} from 'lucide-react'

interface StatsCardsProps {
  stats?: DashboardStats | null;
  period?: 'daily' | 'weekly' | 'monthly' | 'yearly';
}

export function StatsCards({ stats, period = 'daily' }: StatsCardsProps) {
  if (!stats) {
    return null;
  }
  
  const cards = [
    {
      title: 'Total de Clientes',
      value: stats.total_clients,
      icon: Users,
      description: 'clientes cadastrados',
      trend: stats.growth_rate ? {
        value: stats.growth_rate,
        isPositive: stats.growth_rate > 0
      } : null
    },
    {
      title: 'Conversas Hoje',
      value: stats.conversations_today,
      icon: MessageCircle,
      description: `${stats.total_conversations} total`,
      trend: null
    },
    {
      title: 'Agendamentos Hoje',
      value: stats.appointments_today,
      icon: Calendar,
      description: `${stats.total_appointments} total`,
      trend: stats.conversion_rate ? {
        value: stats.conversion_rate,
        isPositive: stats.conversion_rate > 5
      } : null
    },
    {
      title: 'Mensagens Hoje',
      value: stats.messages_today,
      icon: MessageSquare,
      description: `${stats.total_messages} total`,
      trend: null
    },
    {
      title: 'Novos Clientes',
      value: stats.new_clients_today,
      icon: UserPlus,
      description: 'novos hoje',
      trend: null
    }
  ];
  
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {card.title}
            </CardTitle>
            <card.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {card.value.toLocaleString('pt-BR')}
            </div>
            <div className="flex items-center justify-between mt-1">
              <p className="text-xs text-muted-foreground">
                {card.description}
              </p>
              {card.trend && (
                <div className={`flex items-center text-xs ${
                  card.trend.isPositive ? 'text-green-600' : 'text-red-600'
                }`}>
                  {card.trend.isPositive ? 
                    <TrendingUp className="h-3 w-3 mr-1" /> : 
                    <TrendingDown className="h-3 w-3 mr-1" />
                  }
                  {Math.abs(card.trend.value)}%
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Versão compacta para uso em outras páginas
export function CompactStatsCards({ stats }: { stats?: DashboardStats | null }) {
  if (!stats) {
    return null;
  }
  
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
      <div className="bg-white p-3 rounded-lg border text-center">
        <div className="text-lg font-semibold">{stats.total_clients}</div>
        <div className="text-xs text-gray-500">Clientes</div>
      </div>
      <div className="bg-white p-3 rounded-lg border text-center">
        <div className="text-lg font-semibold">{stats.conversations_today}</div>
        <div className="text-xs text-gray-500">Conversas</div>
      </div>
      <div className="bg-white p-3 rounded-lg border text-center">
        <div className="text-lg font-semibold">{stats.appointments_today}</div>
        <div className="text-xs text-gray-500">Agendamentos</div>
      </div>
      <div className="bg-white p-3 rounded-lg border text-center">
        <div className="text-lg font-semibold">{stats.messages_today}</div>
        <div className="text-xs text-gray-500">Mensagens</div>
      </div>
    </div>
  )
}
