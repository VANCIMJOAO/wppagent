'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MessageCircle, CalendarPlus, UserPlus, BarChart3 } from "lucide-react"
import { debugLog } from '@/lib/debug';

export const QuickActions = () => {
  const actions = [
    {
      icon: <MessageCircle className="h-6 w-6" />,
      label: "Nova Conversa",
      color: "bg-green-500 hover:bg-green-600",
      onClick: () => debugLog.info("Nova conversa")
    },
    {
      icon: <CalendarPlus className="h-6 w-6" />,
      label: "Novo Agendamento",
      color: "bg-blue-500 hover:bg-blue-600",
      onClick: () => debugLog.info("Novo agendamento")
    },
    {
      icon: <UserPlus className="h-6 w-6" />,
      label: "Adicionar Cliente",
      color: "bg-purple-500 hover:bg-purple-600",
      onClick: () => debugLog.info("Novo cliente")
    },
    {
      icon: <BarChart3 className="h-6 w-6" />,
      label: "Ver Relatórios",
      color: "bg-orange-500 hover:bg-orange-600",
      onClick: () => debugLog.info("Ver relatórios")
    }
  ]

  return (
    <Card className="animate-fadeInUp">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">Ações Rápidas</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {actions.map((action, index) => (
            <Button
              key={index}
              onClick={action.onClick}
              className={`${action.color} text-white h-24 flex flex-col items-center justify-center space-y-2 hover-lift transition-all duration-200`}
              variant="default"
            >
              {action.icon}
              <span className="text-sm font-medium">{action.label}</span>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
