/**
 * Dashboard Principal - Página de Overview
 * Combina métricas principais com navegação para analytics avançadas
 */
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useRealAnalytics } from '@/hooks/use-real-analytics';
import { AdvancedErrorBoundary } from '@/components/error-boundaries/AdvancedErrorBoundary';
import { 
  Users, 
  MessageSquare, 
  Clock,
  TrendingUp,
  Calendar,
  Activity,
  RefreshCw,
  ArrowRight,
  Database
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import Link from 'next/link';

export default function DashboardPage() {
  const {
    dashboardSummary,
    loadingDashboard,
    dashboardError,
    refreshDashboard
  } = useRealAnalytics();
  
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  if (loadingDashboard && !dashboardSummary) {
    return (
      <div className="space-y-6 p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-48 bg-gray-200 rounded"></div>
            <div className="h-48 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <AdvancedErrorBoundary>
      <div className="space-y-6 p-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">
              Visão geral do desempenho do WhatsApp Agent
            </p>
            {lastUpdated && (
              <p className="text-sm text-gray-500 mt-1">
                <Activity className="inline w-4 h-4 mr-1" />
                Última atualização: {format(lastUpdated, "dd 'de' MMMM 'às' HH:mm", { locale: ptBR })}
              </p>
            )}
          </div>
          
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                refreshDashboard(30);
                setLastUpdated(new Date());
              }}
              disabled={loadingDashboard}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loadingDashboard ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
            
            <Link href="/analytics">
              <Button size="sm">
                <TrendingUp className="w-4 h-4 mr-2" />
                Analytics Avançadas
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Métricas Principais */}
        {dashboardSummary?.key_metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total de Clientes</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardSummary.key_metrics.total_customers?.toLocaleString() || '0'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Clientes ativos na base
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Conversas</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardSummary.key_metrics.total_conversations?.toLocaleString() || '0'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Conversas iniciadas
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Agendamentos</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardSummary.key_metrics.total_appointments?.toLocaleString() || '0'}
                </div>
                <p className="text-xs text-muted-foreground">
                  Compromissos marcados
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Taxa de Conversão</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {dashboardSummary.key_metrics.overall_conversion_rate?.toFixed(1) || '0.0'}%
                </div>
                <p className="text-xs text-muted-foreground">
                  Conversões realizadas
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Performance e Qualidade */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Tempo de Resposta
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-2">
                {dashboardSummary?.key_metrics.avg_response_time_minutes?.toFixed(1) || '0.0'}
                <span className="text-lg text-gray-500 ml-1">min</span>
              </div>
              <p className="text-sm text-gray-600">
                Tempo médio para primeira resposta
              </p>
              
              {dashboardSummary?.trends && (
                <div className="mt-4 flex items-center gap-2">
                  <TrendingUp className={`h-4 w-4 ${
                    (dashboardSummary.trends.responseTime || 0) >= 0 
                      ? 'text-red-500' 
                      : 'text-green-500'
                  }`} />
                  <span className={`text-sm ${
                    (dashboardSummary.trends.responseTime || 0) >= 0 
                      ? 'text-red-600' 
                      : 'text-green-600'
                  }`}>
                    {Math.abs(dashboardSummary.trends.responseTime || 0).toFixed(1)}% vs período anterior
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Satisfação dos Clientes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold mb-2">
                {dashboardSummary?.key_metrics.satisfaction_score?.toFixed(1) || '0.0'}
                <span className="text-lg text-gray-500 ml-1">/5.0</span>
              </div>
              <p className="text-sm text-gray-600">
                Score médio de satisfação
              </p>
              
              {dashboardSummary?.trends && (
                <div className="mt-4 flex items-center gap-2">
                  <TrendingUp className={`h-4 w-4 ${
                    (dashboardSummary.trends.satisfaction || 0) >= 0 
                      ? 'text-green-500' 
                      : 'text-red-500'
                  }`} />
                  <span className={`text-sm ${
                    (dashboardSummary.trends.satisfaction || 0) >= 0 
                      ? 'text-green-600' 
                      : 'text-red-600'
                  }`}>
                    {Math.abs(dashboardSummary.trends.satisfaction || 0).toFixed(1)}% vs período anterior
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Status da Conexão com Database */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Status do Sistema
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${
                  dashboardSummary ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm">
                  {dashboardSummary ? 'Conectado ao backend' : 'Backend desconectado'}
                </span>
              </div>
              
              {dashboardError && (
                <div className="text-sm text-red-600 bg-red-50 px-3 py-1 rounded">
                  Erro: {dashboardError}
                </div>
              )}
            </div>
            
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Mensagens processadas:</strong> {dashboardSummary?.key_metrics.total_messages?.toLocaleString() || '0'}
              </div>
              <div>
                <strong>Última atualização:</strong> {format(lastUpdated, "HH:mm", { locale: ptBR })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Call to Action */}
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardContent className="p-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold text-blue-900 mb-2">
                  Explore Analytics Avançadas
                </h3>
                <p className="text-blue-700 mb-4">
                  Acesse relatórios detalhados, funis de conversão, performance de templates e muito mais.
                </p>
                <Link href="/analytics">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Ver Analytics Completas
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdvancedErrorBoundary>
  );
}
