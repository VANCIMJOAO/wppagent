'use client';

import { AdvancedErrorBoundary } from '@/components/error-boundaries/AdvancedErrorBoundary';
import { ApiErrorBoundary } from '@/components/error-boundaries/ApiErrorBoundary';
import { ErrorDashboard } from '@/components/error-boundaries/ErrorDashboard';
import {
  DashboardKpisErrorFallback,
  ChartsErrorFallback,
  RecentActivityErrorFallback,
  NetworkErrorFallback,
  FormErrorFallback
} from '@/components/error-boundaries/ErrorFallbacks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useState } from 'react';
import {
  Activity,
  Users,
  MessageSquare,
  TrendingUp,
  BarChart3,
  Settings,
  AlertTriangle,
  Wifi
} from 'lucide-react';

// Mock components que podem falhar para demonstrar Error Boundaries
function FailingKPIComponent() {
  const [shouldFail, setShouldFail] = useState(false);

  if (shouldFail) {
    throw new Error('KPI data fetch failed - Network timeout');
  }

  const kpis = [
    { title: 'Mensagens Enviadas', value: '2,847', change: '+12%', icon: MessageSquare },
    { title: 'Usuários Ativos', value: '1,234', change: '+8%', icon: Users },
    { title: 'Taxa de Resposta', value: '94%', change: '+3%', icon: Activity },
    { title: 'Engajamento', value: '87%', change: '+5%', icon: TrendingUp }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi, index) => (
        <Card key={index}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {kpi.title}
            </CardTitle>
            <kpi.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpi.value}</div>
            <p className="text-xs text-muted-foreground">
              <Badge variant="secondary" className="text-green-600">
                {kpi.change}
              </Badge>
              {' '}desde o último mês
            </p>
          </CardContent>
        </Card>
      ))}

      <div className="col-span-full mt-4">
        <Button
          onClick={() => setShouldFail(true)}
          variant="destructive"
          size="sm"
        >
          <AlertTriangle className="w-4 h-4 mr-2" />
          Simular Erro de KPI
        </Button>
      </div>
    </div>
  );
}

function FailingChartComponent() {
  const [shouldFail, setShouldFail] = useState(false);

  if (shouldFail) {
    throw new Error('Chart API failed - 503 Service Unavailable');
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Analytics Dashboard
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <BarChart3 className="w-16 h-16 text-blue-400 mx-auto mb-4" />
            <p className="text-gray-600">Chart carregado com sucesso!</p>
            <Button
              onClick={() => setShouldFail(true)}
              variant="outline"
              size="sm"
              className="mt-4"
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              Simular Erro de API
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function FailingNetworkComponent() {
  const [shouldFail, setShouldFail] = useState(false);

  if (shouldFail) {
    const error = new Error('Network request failed');
    (error as any).isNetworkError = true;
    throw error;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wifi className="w-5 h-5" />
          Status de Rede
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span>Conexão com API</span>
            <Badge variant="default" className="bg-green-100 text-green-800">
              Online
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span>Latência</span>
            <span className="text-sm text-muted-foreground">45ms</span>
          </div>
          <Button
            onClick={() => setShouldFail(true)}
            variant="outline"
            size="sm"
            className="w-full"
          >
            <AlertTriangle className="w-4 h-4 mr-2" />
            Simular Erro de Rede
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ErrorBoundaryDemoPage() {
  const [showErrorDashboard, setShowErrorDashboard] = useState(false);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Dashboard com Error Boundaries
          </h1>
          <p className="text-gray-600 mt-2">
            Demonstração de Error Boundaries robustos com recovery automático
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            onClick={() => setShowErrorDashboard(!showErrorDashboard)}
            variant={showErrorDashboard ? "default" : "outline"}
            className="flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            {showErrorDashboard ? 'Ocultar' : 'Mostrar'} Error Dashboard
          </Button>
        </div>
      </div>

      {/* Error Dashboard (se ativado) */}
      {showErrorDashboard && (
        <AdvancedErrorBoundary
          level="section"
          context="Error Dashboard"
        >
          <ErrorDashboard />
        </AdvancedErrorBoundary>
      )}

      {/* KPI Section com Error Boundary */}
      <section>
        <h2 className="text-xl font-semibold mb-4">KPIs Principais</h2>
        <AdvancedErrorBoundary
          level="section"
          context="KPI Dashboard"
          retryAttempts={3}
          fallback={<DashboardKpisErrorFallback onRetry={() => window.location.reload()} />}
        >
          <FailingKPIComponent />
        </AdvancedErrorBoundary>
      </section>

      {/* Charts Section com API Error Boundary */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Analytics</h2>
        <ApiErrorBoundary
          level="important"
          endpoint="/api/analytics"
          method="GET"
          enableRetry={true}
          maxRetries={5}
          showToast={true}
          fallback={
            <ChartsErrorFallback
              onRetry={() => console.log('Retrying chart load...')}
              loading={false}
            />
          }
        >
          <FailingChartComponent />
        </ApiErrorBoundary>
      </section>

      {/* Network Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section>
          <h2 className="text-xl font-semibold mb-4">Status de Rede</h2>
          <AdvancedErrorBoundary
            level="component"
            context="Network Monitor"
            fallback={
              <NetworkErrorFallback
                onRetry={() => console.log('Retrying network check...')}
                onReset={() => console.log('Resetting network state...')}
                error={null}
              />
            }
          >
            <FailingNetworkComponent />
          </AdvancedErrorBoundary>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-4">Atividade Recente</h2>
          <AdvancedErrorBoundary
            level="component"
            context="Activity Feed"
            fallback={
              <RecentActivityErrorFallback
                onRetry={() => console.log('Retrying activity load...')}
                loading={false}
              />
            }
          >
            <Card>
              <CardHeader>
                <CardTitle>Feed de Atividades</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 text-center py-8">
                  Esta seção carrega atividades recentes.
                  <br />
                  <span className="text-sm text-muted-foreground">
                    (Sem erros simulados aqui)
                  </span>
                </p>
              </CardContent>
            </Card>
          </AdvancedErrorBoundary>
        </section>
      </div>

      {/* Instructions */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <h3 className="font-medium text-blue-900 mb-2">
                Como testar os Error Boundaries:
              </h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Clique nos botões "Simular Erro" para ver os fallbacks em ação</li>
                <li>• Observe como cada seção falha independentemente</li>
                <li>• Teste os botões de retry para ver a recuperação automática</li>
                <li>• Ative o "Error Dashboard" para monitoramento em tempo real</li>
                <li>• Verifique as notificações toast para feedback imediato</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
