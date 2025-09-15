/**
 * 📊 Dashboard Real-Time com WebSocket
 * ====================================
 *
 * Dashboard em tempo real usando WebSocket:
 * - Estatísticas em tempo real
 * - Notificações automáticas
 * - Gráficos animados
 * - Status de conexão
 * - Auto-refresh inteligente
 */

import React, { useState, useEffect } from 'react'
import { useDashboardWebSocket } from '../hooks/useRealtimeWebSocket'
import { useQuery } from '@tanstack/react-query'

// ============= TYPES =============
interface DashboardStats {
    appointments_today: number
    unread_messages: number
    total_users: number
    messages_today: number
    last_updated: string
}

interface DashboardProps {
    token?: string
    className?: string
    refreshInterval?: number
}

// ============= API FUNCTIONS =============
const fetchDashboardStats = async (): Promise<DashboardStats> => {
    const response = await fetch('/api/dashboard/stats', {
        headers: {
            'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}`
        }
    })

    if (!response.ok) {
        throw new Error('Falha ao carregar estatísticas')
    }

    return response.json()
}

// ============= STAT CARD COMPONENT =============
interface StatCardProps {
    title: string
    value: number
    icon: string
    color: string
    trend?: number
    isAnimating?: boolean
}

function StatCard({ title, value, icon, color, trend, isAnimating }: StatCardProps) {
    const [displayValue, setDisplayValue] = useState(value)

    // Animate value changes
    useEffect(() => {
        if (value !== displayValue) {
            const increment = value > displayValue ? 1 : -1
            const timer = setInterval(() => {
                setDisplayValue(prev => {
                    const next = prev + increment
                    if ((increment > 0 && next >= value) || (increment < 0 && next <= value)) {
                        clearInterval(timer)
                        return value
                    }
                    return next
                })
            }, 50)

            return () => clearInterval(timer)
        }
    }, [value, displayValue])

    return (
        <div className={`bg-white rounded-xl p-6 shadow-sm border-l-4 ${color} ${
            isAnimating ? 'animate-pulse' : ''
        } transition-all duration-300 hover:shadow-md`}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-gray-600 text-sm font-medium">{title}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">
                        {displayValue.toLocaleString()}
                    </p>
                    {trend !== undefined && (
                        <p className={`text-sm mt-2 flex items-center ${
                            trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600'
                        }`}>
                            {trend > 0 && '↗️'}
                            {trend < 0 && '↘️'}
                            {trend === 0 && '→'}
                            <span className="ml-1">
                                {trend > 0 ? '+' : ''}{trend}%
                            </span>
                        </p>
                    )}
                </div>
                <div className="text-4xl opacity-80">
                    {icon}
                </div>
            </div>
        </div>
    )
}

// ============= CONNECTION STATUS =============
function ConnectionStatus({ isConnected, status, connectionId }: {
    isConnected: boolean
    status: string
    connectionId?: string | null
}) {
    return (
        <div className={`flex items-center space-x-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
            isConnected
                ? 'bg-green-100 text-green-700 border border-green-200'
                : 'bg-red-100 text-red-700 border border-red-200'
        }`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}>
                {isConnected && (
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-ping" />
                )}
            </div>
            <span>
                {isConnected ? 'Online' : 'Offline'} • {status}
            </span>
            {connectionId && (
                <span className="text-xs opacity-70">
                    ({connectionId.slice(-6)})
                </span>
            )}
        </div>
    )
}

// ============= ACTIVITY FEED =============
function ActivityFeed({ messages }: { messages: any[] }) {
    return (
        <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Atividade em Tempo Real
            </h3>

            <div className="space-y-3 max-h-64 overflow-y-auto">
                {messages.length === 0 ? (
                    <p className="text-gray-500 text-sm">Nenhuma atividade recente</p>
                ) : (
                    messages.slice(-10).reverse().map((message, index) => (
                        <div key={index} className="flex items-start space-x-3 p-2 hover:bg-gray-50 rounded-lg transition-colors">
                            <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2" />
                            <div className="flex-1 min-w-0">
                                <p className="text-sm text-gray-900 break-words">
                                    {message.type.replace('_', ' ').toUpperCase()}
                                </p>
                                <p className="text-xs text-gray-500">
                                    {new Date(message.timestamp).toLocaleTimeString()}
                                </p>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}

// ============= MAIN DASHBOARD COMPONENT =============
export default function RealtimeDashboard({
    token,
    className = '',
    refreshInterval = 30000
}: DashboardProps) {
    const [activityMessages, setActivityMessages] = useState<any[]>([])
    const [animatingCards, setAnimatingCards] = useState<Set<string>>(new Set())

    // WebSocket connection
    const {
        isConnected,
        status,
        connectionId,
        lastMessage,
        refreshDashboard
    } = useDashboardWebSocket(token)

    // Query for dashboard stats
    const { data: stats, isLoading, error, refetch } = useQuery({
        queryKey: ['dashboard', 'stats'],
        queryFn: fetchDashboardStats,
        enabled: !!token,
        refetchInterval: refreshInterval,
        refetchOnWindowFocus: true
    })

    // Handle real-time messages
    useEffect(() => {
        if (lastMessage) {
            // Add to activity feed
            setActivityMessages(prev => [...prev, lastMessage].slice(-50))

            // Animate relevant cards
            if (lastMessage.type.includes('appointment')) {
                setAnimatingCards(prev => new Set(prev).add('appointments'))
                setTimeout(() => {
                    setAnimatingCards(prev => {
                        const newSet = new Set(prev)
                        newSet.delete('appointments')
                        return newSet
                    })
                }, 1000)
            }

            if (lastMessage.type.includes('message')) {
                setAnimatingCards(prev => new Set(prev).add('messages'))
                setTimeout(() => {
                    setAnimatingCards(prev => {
                        const newSet = new Set(prev)
                        newSet.delete('messages')
                        return newSet
                    })
                }, 1000)
            }
        }
    }, [lastMessage])

    // Manual refresh
    const handleRefresh = async () => {
        refreshDashboard()
        await refetch()
    }

    if (!token) {
        return (
            <div className={`flex items-center justify-center p-8 ${className}`}>
                <div className="text-gray-500">Por favor, faça login para acessar o dashboard</div>
            </div>
        )
    }

    if (error) {
        return (
            <div className={`flex items-center justify-center p-8 ${className}`}>
                <div className="text-red-500">Erro ao carregar dados do dashboard</div>
                <button
                    onClick={handleRefresh}
                    className="ml-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                    Tentar Novamente
                </button>
            </div>
        )
    }

    return (
        <div className={`space-y-6 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Dashboard em Tempo Real</h1>
                    <p className="text-gray-600">
                        Última atualização: {stats?.last_updated ?
                            new Date(stats.last_updated).toLocaleString() :
                            'Carregando...'
                        }
                    </p>
                </div>

                <div className="flex items-center space-x-4">
                    <ConnectionStatus
                        isConnected={isConnected}
                        status={status}
                        connectionId={connectionId}
                    />

                    <button
                        onClick={handleRefresh}
                        disabled={isLoading}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <span>🔄</span>
                        <span>{isLoading ? 'Atualizando...' : 'Atualizar'}</span>
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="bg-white rounded-xl p-6 shadow-sm animate-pulse">
                            <div className="h-4 bg-gray-200 rounded mb-4" />
                            <div className="h-8 bg-gray-200 rounded mb-2" />
                            <div className="h-3 bg-gray-200 rounded w-1/2" />
                        </div>
                    ))}
                </div>
            ) : stats ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard
                        title="Agendamentos Hoje"
                        value={stats.appointments_today}
                        icon="📅"
                        color="border-blue-500"
                        isAnimating={animatingCards.has('appointments')}
                    />

                    <StatCard
                        title="Mensagens Não Lidas"
                        value={stats.unread_messages}
                        icon="💬"
                        color="border-orange-500"
                        isAnimating={animatingCards.has('messages')}
                    />

                    <StatCard
                        title="Total de Usuários"
                        value={stats.total_users}
                        icon="👥"
                        color="border-green-500"
                    />

                    <StatCard
                        title="Mensagens Hoje"
                        value={stats.messages_today}
                        icon="📨"
                        color="border-purple-500"
                        isAnimating={animatingCards.has('messages')}
                    />
                </div>
            ) : (
                <div className="text-center py-8 text-gray-500">
                    Nenhum dado disponível
                </div>
            )}

            {/* Activity Feed */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <ActivityFeed messages={activityMessages} />
                </div>

                <div className="bg-white rounded-xl p-6 shadow-sm">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Status do Sistema
                    </h3>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-gray-600">WebSocket</span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                            }`}>
                                {isConnected ? 'Online' : 'Offline'}
                            </span>
                        </div>

                        <div className="flex items-center justify-between">
                            <span className="text-gray-600">Status</span>
                            <span className="text-sm text-gray-900">{status}</span>
                        </div>

                        <div className="flex items-center justify-between">
                            <span className="text-gray-600">Mensagens Recebidas</span>
                            <span className="text-sm font-medium text-gray-900">
                                {activityMessages.length}
                            </span>
                        </div>

                        {connectionId && (
                            <div className="flex items-center justify-between">
                                <span className="text-gray-600">Conexão</span>
                                <span className="text-xs font-mono text-gray-500">
                                    {connectionId.slice(-12)}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

// ============= MINI DASHBOARD WIDGET =============
export function MiniDashboard({ token }: { token?: string }) {
    const { data: stats } = useQuery({
        queryKey: ['dashboard', 'stats'],
        queryFn: fetchDashboardStats,
        enabled: !!token,
        refetchInterval: 30000
    })

    const { isConnected } = useDashboardWebSocket(token)

    if (!stats) return null

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow-sm border">
                <div className="text-2xl font-bold text-blue-600">{stats.appointments_today}</div>
                <div className="text-sm text-gray-600">Agendamentos</div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm border">
                <div className="text-2xl font-bold text-orange-600">{stats.unread_messages}</div>
                <div className="text-sm text-gray-600">Não Lidas</div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm border">
                <div className="text-2xl font-bold text-green-600">{stats.total_users}</div>
                <div className="text-sm text-gray-600">Usuários</div>
            </div>

            <div className="bg-white p-4 rounded-lg shadow-sm border">
                <div className={`text-2xl font-bold ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                    {isConnected ? '🟢' : '🔴'}
                </div>
                <div className="text-sm text-gray-600">Status</div>
            </div>
        </div>
    )
}
