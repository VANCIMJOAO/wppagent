// components/dashboard/RealTimeStats.tsx
'use client'

import React, { useState, useEffect } from 'react'
import { useDashboardWebSocket } from '@/hooks/useWebSocket'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
// import { Separator } from '@/components/ui/separator'
import { Separator } from '../ui/separator'
import { 
  Activity, 
  Users, 
  MessageSquare, 
  Calendar,
  TrendingUp,
  TrendingDown,
  Minus,
  Wifi,
  WifiOff,
  RefreshCw
} from 'lucide-react'

interface StatsCardProps {
  title: string
  value: number
  previousValue?: number
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  isRealTime?: boolean
  isAnimating?: boolean
}

function StatsCard({ 
  title, 
  value, 
  previousValue, 
  icon, 
  trend, 
  isRealTime = false, 
  isAnimating = false 
}: StatsCardProps) {
  const [displayValue, setDisplayValue] = useState(value)

  // Smooth animation when value changes
  useEffect(() => {
    if (value !== displayValue && isRealTime) {
      const startValue = displayValue
      const endValue = value
      const duration = 800 // ms
      const startTime = Date.now()

      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / duration, 1)
        
        // Ease out animation
        const easedProgress = 1 - Math.pow(1 - progress, 3)
        const currentValue = Math.round(startValue + (endValue - startValue) * easedProgress)
        
        setDisplayValue(currentValue)

        if (progress < 1) {
          requestAnimationFrame(animate)
        }
      }

      requestAnimationFrame(animate)
    } else {
      setDisplayValue(value)
    }
  }, [value, displayValue, isRealTime])

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-3 h-3 text-green-600" />
      case 'down':
        return <TrendingDown className="w-3 h-3 text-red-600" />
      default:
        return <Minus className="w-3 h-3 text-gray-400" />
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      default:
        return 'text-gray-500'
    }
  }

  const calculateTrendPercentage = () => {
    if (!previousValue || previousValue === 0) return 0
    return Math.round(((displayValue - previousValue) / previousValue) * 100)
  }

  return (
    <Card className={`transition-all duration-300 ${
      isAnimating ? 'ring-2 ring-blue-300 scale-[1.02] shadow-lg' : 'hover:shadow-md'
    }`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">
          {title}
        </CardTitle>
        <div className="flex items-center space-x-2">
          {icon}
          {isRealTime && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" 
                   title="Dados em tempo real" />
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline space-x-2">
            <div className={`text-2xl font-bold transition-colors duration-300 ${
              isAnimating ? 'text-blue-600' : 'text-gray-900'
            }`}>
              {displayValue.toLocaleString()}
            </div>
            {previousValue !== undefined && (
              <div className={`flex items-center space-x-1 text-xs ${getTrendColor()}`}>
                {getTrendIcon()}
                <span>{Math.abs(calculateTrendPercentage())}%</span>
              </div>
            )}
          </div>
        </div>
        {previousValue !== undefined && (
          <p className={`text-xs mt-1 ${getTrendColor()}`}>
            {trend === 'up' ? '+' : trend === 'down' ? '-' : ''}
            {Math.abs(displayValue - previousValue)} desde ontem
          </p>
        )}
      </CardContent>
    </Card>
  )
}

interface SystemAlert {
  message: string
  timestamp: number
  alert_type?: 'info' | 'warning' | 'error'
}

function AlertItem({ alert }: { alert: SystemAlert }) {
  const getAlertColor = () => {
    switch (alert.alert_type) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800'
    }
  }

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className={`p-2 rounded border text-xs ${getAlertColor()}`}>
      <div className="flex items-center justify-between">
        <span className="font-medium">{alert.message}</span>
        <span className="text-xs opacity-75">
          {formatTime(alert.timestamp)}
        </span>
      </div>
    </div>
  )
}

export default function RealTimeStats() {
  const { 
    dashboardStats, 
    systemAlerts, 
    analyticsUpdates,
    isConnected, 
    connectionStats, 
    requestStats 
  } = useDashboardWebSocket()

  const [previousStats, setPreviousStats] = useState<any>(null)
  const [animatingStats, setAnimatingStats] = useState<Set<string>>(new Set())

  // Track stats changes for animations
  useEffect(() => {
    if (dashboardStats && previousStats) {
      const newAnimating = new Set<string>()
      
      Object.keys(dashboardStats).forEach(key => {
        if (dashboardStats[key] !== previousStats[key]) {
          newAnimating.add(key)
        }
      })
      
      if (newAnimating.size > 0) {
        setAnimatingStats(newAnimating)
        
        // Clear animations after duration
        setTimeout(() => {
          setAnimatingStats(new Set())
        }, 1000)
      }
    }
    
    if (dashboardStats) {
      setPreviousStats({ ...dashboardStats })
    }
  }, [dashboardStats, previousStats])

  const stats = dashboardStats || {
    messages_today: 0,
    conversations_today: 0,
    appointments_today: 0,
    new_clients_today: 0
  }

  const getTrend = (current: number, previous: number | undefined): 'up' | 'down' | 'neutral' => {
    if (!previous) return 'neutral'
    if (current > previous) return 'up'
    if (current < previous) return 'down'
    return 'neutral'
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard em Tempo Real</h2>
        <div className="flex items-center space-x-3">
          <Button
            onClick={requestStats}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
            disabled={!isConnected}
          >
            <RefreshCw className="w-4 h-4" />
            <span>Atualizar</span>
          </Button>
          
          <Badge 
            variant={isConnected ? "default" : "destructive"}
            className={`flex items-center space-x-2 ${
              isConnected ? "bg-green-600 hover:bg-green-700" : ""
            }`}
          >
            {isConnected ? (
              <>
                <Wifi className="w-3 h-3" />
                <span>Tempo Real</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                <span>Offline</span>
              </>
            )}
          </Badge>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Mensagens Hoje"
          value={stats.messages_today}
          previousValue={previousStats?.messages_today}
          trend={getTrend(stats.messages_today, previousStats?.messages_today)}
          icon={<MessageSquare className="w-4 h-4 text-blue-600" />}
          isRealTime={isConnected}
          isAnimating={animatingStats.has('messages_today')}
        />
        
        <StatsCard
          title="Conversas Ativas"
          value={stats.conversations_today}
          previousValue={previousStats?.conversations_today}
          trend={getTrend(stats.conversations_today, previousStats?.conversations_today)}
          icon={<Users className="w-4 h-4 text-green-600" />}
          isRealTime={isConnected}
          isAnimating={animatingStats.has('conversations_today')}
        />
        
        <StatsCard
          title="Agendamentos"
          value={stats.appointments_today}
          previousValue={previousStats?.appointments_today}
          trend={getTrend(stats.appointments_today, previousStats?.appointments_today)}
          icon={<Calendar className="w-4 h-4 text-purple-600" />}
          isRealTime={isConnected}
          isAnimating={animatingStats.has('appointments_today')}
        />
        
        <StatsCard
          title="Novos Clientes"
          value={stats.new_clients_today}
          previousValue={previousStats?.new_clients_today}
          trend={getTrend(stats.new_clients_today, previousStats?.new_clients_today)}
          icon={<Activity className="w-4 h-4 text-orange-600" />}
          isRealTime={isConnected}
          isAnimating={animatingStats.has('new_clients_today')}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Connection Details */}
        <Card>
          <CardHeader>
            <CardTitle>Status da Conexão</CardTitle>
            <CardDescription>
              Detalhes da conexão WebSocket em tempo real
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-gray-600">Status</span>
              <Badge 
                variant={isConnected ? "default" : "destructive"}
                className={isConnected ? "bg-green-600 hover:bg-green-700" : ""}
              >
                {isConnected ? 'Conectado' : 'Desconectado'}
              </Badge>
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-gray-600">Inscrições</span>
              <div className="flex flex-wrap gap-1">
                {connectionStats.subscriptions.map((sub) => (
                  <Badge key={sub} variant="outline" className="text-xs">
                    {sub}
                  </Badge>
                ))}
              </div>
            </div>
            
            {connectionStats.connectionTime && (
              <>
                <Separator />
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-gray-600">Conectado há</span>
                  <span className="text-sm font-medium">
                    {Math.round((Date.now() - connectionStats.connectionTime.getTime()) / 1000)}s
                  </span>
                </div>
              </>
            )}
            
            {connectionStats.reconnectCount > 0 && (
              <>
                <Separator />
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-gray-600">Reconexões</span>
                  <Badge variant="secondary">
                    {connectionStats.reconnectCount}
                  </Badge>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* System Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Alertas do Sistema</CardTitle>
            <CardDescription>
              Últimas notificações e alertas
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {systemAlerts.length > 0 ? (
              systemAlerts.slice(0, 5).map((alert, index) => (
                <AlertItem key={index} alert={alert} />
              ))
            ) : (
              <div className="text-center py-4 text-gray-500 text-sm">
                Nenhum alerta recente
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Analytics Updates */}
      {analyticsUpdates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Atualizações de Analytics</CardTitle>
            <CardDescription>
              Últimas atualizações dos relatórios analíticos
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analyticsUpdates.slice(0, 3).map((update, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm">{update.report_type || 'Relatório'}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(update.timestamp).toLocaleTimeString('pt-BR')}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
