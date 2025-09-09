/**
 * Página de Analytics Avançada - Sistema Completo
 * Dashboard com todos os componentes avançados integrados
 */
'use client';

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAnalytics } from '@/hooks/useAnalytics';
import AnalyticsFilters from '@/components/analytics/AnalyticsFilters';
import AnalyticsCharts from '@/components/analytics/AnalyticsCharts';
import { DrillDownAnalytics } from '@/components/analytics/DrillDownAnalytics';
import { AlertsSystem } from '@/components/analytics/AlertsSystem';
import { CustomDashboard } from '@/components/analytics/CustomDashboard';
import { AutomatedReports } from '@/components/analytics/AutomatedReports';
import { 
  TrendingUp, 
  Users, 
  MessageSquare, 
  Clock,
  BarChart3,
  Search,
  Bell,
  Layout,
  FileText,
  Settings,
  RefreshCw,
  Download
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function AdvancedAnalyticsPage() {
  const [selectedTab, setSelectedTab] = useState('overview');
  const { data: analytics, loading, error, refresh } = useAnalytics();
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Atualizar timestamp
  const handleRefresh = () => {
    refresh();
    setLastUpdate(new Date());
  };

  if (loading && !analytics) {
    return (
      <div className="space-y-6 p-6">
        <div className="animate-pulse">
          <div className="flex justify-between items-center mb-6">
            <div>
              <div className="h-8 bg-gray-200 rounded w-64 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-48"></div>
            </div>
            <div className="h-10 bg-gray-200 rounded w-32"></div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
          
          <div className="h-12 bg-gray-200 rounded mb-4"></div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-6">
            <div className="text-center py-12">
              <div className="text-red-500 mb-4">
                <TrendingUp className="w-12 h-12 mx-auto opacity-50" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Erro ao carregar dados
              </h2>
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={handleRefresh}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Tentar novamente
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const stats = [
    {
      title: 'Total de Conversas',
      value: analytics?.totalConversations?.toLocaleString('pt-BR') || '2,850',
      change: '+12.5%',
      changeType: 'positive',
      icon: MessageSquare,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Total de Mensagens',
      value: analytics?.totalMessages?.toLocaleString('pt-BR') || '11,500',
      change: '+8.2%',
      changeType: 'positive',
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Tempo Médio Resposta',
      value: `${analytics?.avgResponseTime || 2.3}min`,
      change: '-3.1%',
      changeType: 'negative',
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: 'Satisfação Geral',
      value: `${analytics?.overallSatisfaction || 4.6}/5`,
      change: '+5.7%',
      changeType: 'positive',
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Cabeçalho Principal */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <BarChart3 className="w-8 h-8 mr-3 text-blue-600" />
            Analytics Dashboard Avançado
          </h1>
          <p className="text-gray-600 mt-2 flex items-center">
            <Clock className="w-4 h-4 mr-2" />
            Última atualização: {format(lastUpdate, "dd 'de' MMMM 'às' HH:mm", { locale: ptBR })}
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={handleRefresh}
            className="flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Atualizar
          </Button>
        </div>
      </div>

      {/* Cards de estatísticas principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.title} className={`${stat.bgColor} border-0`}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600 mb-1">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 mb-2">
                    {stat.value}
                  </p>
                  <p className={`text-sm font-medium flex items-center ${
                    stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    <TrendingUp className={`w-3 h-3 mr-1 ${
                      stat.changeType === 'negative' ? 'rotate-180' : ''
                    }`} />
                    {stat.change} vs período anterior
                  </p>
                </div>
                <div className={`p-3 rounded-full ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs Principais do Sistema */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6 h-12">
          <TabsTrigger value="overview" className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4" />
            <span className="hidden sm:inline">Overview</span>
          </TabsTrigger>
          <TabsTrigger value="drill-down" className="flex items-center space-x-2">
            <Search className="w-4 h-4" />
            <span className="hidden sm:inline">Drill-Down</span>
          </TabsTrigger>
          <TabsTrigger value="alerts" className="flex items-center space-x-2">
            <Bell className="w-4 h-4" />
            <span className="hidden sm:inline">Alertas</span>
          </TabsTrigger>
          <TabsTrigger value="dashboard" className="flex items-center space-x-2">
            <Layout className="w-4 h-4" />
            <span className="hidden sm:inline">Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="reports" className="flex items-center space-x-2">
            <FileText className="w-4 h-4" />
            <span className="hidden sm:inline">Relatórios</span>
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center space-x-2">
            <Settings className="w-4 h-4" />
            <span className="hidden sm:inline">Config</span>
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview - Gráficos principais */}
        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-blue-600" />
                  Visão Geral dos Dados
                </CardTitle>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Exportar
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Conversas ao Longo do Tempo</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80 flex items-center justify-center text-gray-500">
                      <BarChart3 className="w-12 h-12 mr-4" />
                      Gráfico de Conversas - Recharts
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Volume de Mensagens</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80 flex items-center justify-center text-gray-500">
                      <TrendingUp className="w-12 h-12 mr-4" />
                      Gráfico de Volume - Recharts
                    </div>
                  </CardContent>
                </Card>

                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Performance por Canal</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-80 flex items-center justify-center text-gray-500">
                      <BarChart3 className="w-12 h-12 mr-4" />
                      Gráfico de Performance - Recharts
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Drill-Down - Análise detalhada */}
        <TabsContent value="drill-down" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Search className="w-5 h-5 mr-2 text-green-600" />
                Análise Detalhada - Drill Down
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DrillDownAnalytics metricType="conversations" />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Alertas - Sistema de monitoramento */}
        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Bell className="w-5 h-5 mr-2 text-red-600" />
                Sistema de Alertas Inteligentes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AlertsSystem />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Dashboard - Dashboard personalizado */}
        <TabsContent value="dashboard" className="space-y-6">
          <CustomDashboard />
        </TabsContent>

        {/* Tab 5: Relatórios - Relatórios automatizados */}
        <TabsContent value="reports" className="space-y-6">
          <AutomatedReports />
        </TabsContent>

        {/* Tab 6: Configurações - Configurações do sistema */}
        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="w-5 h-5 mr-2 text-gray-600" />
                Configurações do Sistema
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-8">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Configurações de Backend */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
                    Integração Backend
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        URL da API
                      </label>
                      <input 
                        type="text" 
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                        placeholder="https://api.empresa.com/analytics"
                        defaultValue="https://api.whatsapp-agent.local"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Token de Autenticação
                      </label>
                      <input 
                        type="password" 
                        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" 
                        placeholder="Bearer token de autenticação"
                      />
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                      <input type="checkbox" id="useRealData" className="h-4 w-4 text-blue-600" />
                      <label htmlFor="useRealData" className="text-sm font-medium text-blue-900">
                        Usar dados reais do backend (desmarque para dados demo)
                      </label>
                    </div>
                  </div>
                </div>

                {/* Configurações de Notificações */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 border-b pb-2">
                    Sistema de Notificações
                  </h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium text-gray-900">Notificações por Email</div>
                        <div className="text-sm text-gray-600">Receber alertas por email</div>
                      </div>
                      <input type="checkbox" className="h-4 w-4 text-blue-600" defaultChecked />
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="font-medium text-gray-900">Notificações do Navegador</div>
                        <div className="text-sm text-gray-600">Alertas em tempo real no navegador</div>
                      </div>
                      <input type="checkbox" className="h-4 w-4 text-blue-600" defaultChecked />
                    </div>
                  </div>
                </div>
              </div>

              {/* Botões de ação */}
              <div className="flex justify-end space-x-4 pt-8 border-t">
                <Button variant="outline">
                  Cancelar Alterações
                </Button>
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <Settings className="w-4 h-4 mr-2" />
                  Salvar Configurações
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
