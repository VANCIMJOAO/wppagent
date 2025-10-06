/**
 * Página de Analytics com Dados Reais - Versão Simplificada
 * Foca na implementação de dados reais com Error Boundaries
 */
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RealAnalyticsDashboard } from '@/components/analytics/RealAnalyticsDashboard';
import { UniversalErrorBoundary } from '@/components/shared/error-boundary/UniversalErrorBoundary';
import { useRealAnalytics } from '@/hooks/use-real-analytics';
import {
  BarChart3,
  Database,
  RefreshCw,
  Users,
  MessageSquare,
  TrendingUp,
  Clock
} from 'lucide-react';

export default function RealAnalyticsPage() {
  const {
    dashboardSummary,
    loadingDashboard,
    dashboardError,
    refreshDashboard,
    isLoading
  } = useRealAnalytics();

  const handleRefresh = async () => {
    await refreshDashboard(30);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <BarChart3 className="w-8 h-8 mr-3 text-blue-600" />
            Analytics - Dados Reais
          </h1>
          <p className="text-gray-600 mt-2">
            Dashboard integrado com backend FastAPI e PostgreSQL
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Badge variant="default" className="flex items-center bg-green-600">
            <Database className="w-3 h-3 mr-1" />
            Dados Reais PostgreSQL
          </Badge>

          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </div>

      {/* Status Cards */}
      {dashboardSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-600">Clientes Únicos</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {dashboardSummary.key_metrics.total_customers.toLocaleString()}
                  </p>
                </div>
                <Users className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-600">Total Mensagens</p>
                  <p className="text-2xl font-bold text-green-900">
                    {dashboardSummary.key_metrics.total_messages.toLocaleString()}
                  </p>
                </div>
                <MessageSquare className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-purple-50 border-purple-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-purple-600">Taxa de Conversão</p>
                  <p className="text-2xl font-bold text-purple-900">
                    {dashboardSummary.key_metrics.overall_conversion_rate.toFixed(1)}%
                  </p>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-orange-50 border-orange-200">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-orange-600">Agendamentos</p>
                  <p className="text-2xl font-bold text-orange-900">
                    {dashboardSummary.key_metrics.total_appointments.toLocaleString()}
                  </p>
                </div>
                <Clock className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Dashboard */}
      <UniversalErrorBoundary level="component" name="Analytics Dashboard">
        {useRealData ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="w-5 h-5 mr-2 text-green-600" />
                Dashboard com Dados Reais do Backend
              </CardTitle>
            </CardHeader>
            <CardContent>
              <RealAnalyticsDashboard
                period={30}
                autoRefresh={true}
              />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="w-5 h-5 mr-2 text-gray-600" />
                Dashboard com Dados Simulados (Fallback)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <Database className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">Modo Simulação</h3>
                <p>Clique em "Usar Real" para ver dados reais do backend</p>
              </div>
            </CardContent>
          </Card>
        )}
      </UniversalErrorBoundary>

      {/* Error Display */}
      {dashboardError && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium text-red-800">Erro no Backend</h4>
                <p className="text-sm text-red-600">{dashboardError}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setUseRealData(false)}
                className="text-red-600 border-red-300"
              >
                Usar Fallback
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
