'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageCircle, Users, Calendar, MessageSquare } from "lucide-react"

interface KPIData {
  total_conversations: number;
  unique_users: number;
  total_appointments: number;
  total_messages: number;
  messages_today: number;
  conversations_today: number;
  appointments_today: number;
  growth_conversations: number;
  growth_messages: number;
  growth_appointments: number;
}

interface KPICardProps {
  title: string
  value: string | number
  subtitle: string
  icon: React.ReactNode
  gradient: string
  growth?: number
}

const KPICard = ({ title, value, subtitle, icon, gradient, growth }: KPICardProps) => {
  const growthColor = growth && growth > 0 ? 'text-green-600' : 'text-red-600';
  const growthIcon = growth && growth > 0 ? '↗' : '↘';
  
  return (
    <Card className="overflow-hidden animate-fadeInUp">
      <CardHeader className={`${gradient} text-white pb-2`}>
        <div className="flex items-center justify-between">
          <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
            {icon}
          </div>
          <div className="text-right">
            <CardTitle className="text-2xl font-bold text-white">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </CardTitle>
            <p className="text-white/90 text-sm font-medium">{title}</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4 bg-gray-50">
        <p className="text-center text-sm text-gray-600">
          {subtitle}
          {growth !== undefined && (
            <span className={`ml-2 ${growthColor} font-semibold`}>
              {growthIcon} {Math.abs(growth).toFixed(1)}%
            </span>
          )}
        </p>
      </CardContent>
    </Card>
  )
}

interface KPIGridProps {
  data?: KPIData;
}

export const KPIGrid = ({ data }: KPIGridProps) => {
  // Dados padrão/fallback (como no dashboard Dash original)
  const defaultData: KPIData = {
    total_conversations: 127,
    unique_users: 284,
    total_appointments: 31,
    total_messages: 3847,
    messages_today: 67,
    conversations_today: 8,
    appointments_today: 4,
    growth_conversations: 15.2,
    growth_messages: 23.8,
    growth_appointments: 8.7
  };

  const kpiData = data || defaultData;

  const kpis = [
    {
      title: "Conversas Ativas",
      value: kpiData.total_conversations,
      subtitle: `+${kpiData.conversations_today} hoje`,
      icon: <MessageCircle size={24} />,
      gradient: "bg-gradient-to-r from-blue-500 to-blue-600",
      growth: kpiData.growth_conversations
    },
    {
      title: "Clientes Únicos", 
      value: kpiData.unique_users,
      subtitle: "Base de clientes",
      icon: <Users size={24} />,
      gradient: "bg-gradient-to-r from-green-500 to-green-600"
    },
    {
      title: "Agendamentos",
      value: kpiData.total_appointments, 
      subtitle: `+${kpiData.appointments_today} hoje`,
      icon: <Calendar size={24} />,
      gradient: "bg-gradient-to-r from-orange-500 to-orange-600",
      growth: kpiData.growth_appointments
    },
    {
      title: "Mensagens",
      value: kpiData.total_messages,
      subtitle: `${kpiData.messages_today} hoje`,
      icon: <MessageSquare size={24} />,
      gradient: "bg-gradient-to-r from-purple-500 to-purple-600",
      growth: kpiData.growth_messages
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {kpis.map((kpi, index) => (
        <KPICard 
          key={index} 
          title={kpi.title}
          value={kpi.value}
          subtitle={kpi.subtitle}
          icon={kpi.icon}
          gradient={kpi.gradient}
          growth={kpi.growth}
        />
      ))}
    </div>
  )
}