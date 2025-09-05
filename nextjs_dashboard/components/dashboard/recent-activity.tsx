'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge" 
import { MessageCircle, Calendar, UserPlus, CheckCircle } from "lucide-react"

interface ActivityItem {
  id: number;
  type: 'conversation' | 'appointment' | 'message';
  title: string;
  description: string;
  user_name?: string;
  created_at: string;
  status?: string;
}

interface RecentActivityProps {
  data?: ActivityItem[];
}

export const RecentActivity = ({ data }: RecentActivityProps) => {
  // Dados padrão/fallback
  const defaultActivities = [
    {
      id: 1,
      type: 'conversation' as const,
      title: "Nova conversa iniciada",
      description: "João Silva iniciou uma conversa",
      created_at: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    },
    {
      id: 2,
      type: 'appointment' as const,
      title: "Agendamento confirmado",
      description: "Maria Santos confirmou consulta",
      created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    },
    {
      id: 3,
      type: 'message' as const,
      title: "Nova mensagem",
      description: "Pedro Oliveira enviou uma mensagem",
      created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    }
  ];

  const activities = data || defaultActivities;

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'conversation':
        return <MessageCircle className="h-4 w-4" />;
      case 'appointment':
        return <Calendar className="h-4 w-4" />;
      case 'message':
        return <MessageCircle className="h-4 w-4" />;
      default:
        return <CheckCircle className="h-4 w-4" />;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'conversation':
        return 'bg-blue-500';
      case 'appointment':
        return 'bg-green-500';
      case 'message':
        return 'bg-orange-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 60) {
      return `${diffMins} min atrás`;
    } else if (diffHours < 24) {
      return `${diffHours} hora${diffHours > 1 ? 's' : ''} atrás`;
    } else {
      return `${diffDays} dia${diffDays > 1 ? 's' : ''} atrás`;
    }
  };

  return (
    <Card className="animate-fadeInUp">
      <CardHeader>
        <CardTitle className="text-lg font-semibold flex items-center">
          <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
          Atividade Recente
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-center space-x-3">
            <div className={`${getActivityColor(activity.type)} p-2 rounded-full text-white`}>
              {getActivityIcon(activity.type)}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                {activity.title}
              </p>
              <p className="text-xs text-gray-600">
                {activity.description}
              </p>
              <p className="text-xs text-gray-500">
                {formatTimeAgo(activity.created_at)}
              </p>
            </div>
          </div>
        ))}
        
        {activities.length === 0 && (
          <p className="text-center text-gray-500 py-4">
            Nenhuma atividade recente
          </p>
        )}
      </CardContent>
    </Card>
  )
}