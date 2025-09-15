'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import ErrorBoundary from '@/components/error-boundary';
import {
  ComponentErrorBoundary,
  DataTableErrorBoundary,
  useErrorReporter
} from '@/components/error-boundaries';
import {
  AlertTriangle,
  Bug,
  Zap,
  Shield,
  RefreshCw,
  CheckCircle
} from 'lucide-react';

// Component que simula erro
function ErrorComponent({ shouldError }: { shouldError: boolean }) {
  if (shouldError) {
    throw new Error('Erro simulado para demonstração do Error Boundary');
  }

  return (
    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
      <div className="flex items-center">
        <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
        <span className="text-green-700">Componente funcionando normalmente</span>
      </div>
    </div>
  );
}

// Component que simula erro assíncrono
function AsyncErrorComponent() {
  const [hasError, setHasError] = useState(false);

  const triggerAsyncError = () => {
    setTimeout(() => {
      setHasError(true);
    }, 1000);
  };

  if (hasError) {
    throw new Error('Erro assíncrono após timeout');
  }

  return (
    <div className="p-4 border rounded-lg">
      <p className="mb-4">Componente com erro assíncrono:</p>
      <Button onClick={triggerAsyncError} variant="destructive" size="sm">
        <Zap className="w-4 h-4 mr-2" />
        Trigger Erro Assíncrono (1s)
      </Button>
    </div>
  );
}

// Component que usa useErrorReporter
function ManualErrorReporter() {
  const { reportError } = useErrorReporter();

  const reportManualError = () => {
    const error = new Error('Erro reportado manualmente via hook');
    reportError(error, 'ManualErrorReporter');
  };

  return (
    <div className="p-4 border rounded-lg">
      <p className="mb-4">Reportar erro manualmente:</p>
      <Button onClick={reportManualError} variant="outline" size="sm">
        <Bug className="w-4 h-4 mr-2" />
        Reportar Erro Manual
      </Button>
    </div>
  );
}

// Component que simula erro de network/API
function NetworkErrorComponent() {
  const [shouldError, setShouldError] = useState(false);

  React.useEffect(() => {
    if (shouldError) {
      // Simula erro de network que quebra o componente
      fetch('/api/nonexistent').then(response => {
        if (!response.ok) {
          throw new Error('Network error simulation');
        }
      });
    }
  }, [shouldError]);

  if (shouldError) {
    throw new Error('Erro de rede simulado');
  }

  return (
    <div className="p-4 border rounded-lg">
      <p className="mb-4">Componente com erro de rede:</p>
      <Button onClick={() => setShouldError(true)} variant="destructive" size="sm">
        <AlertTriangle className="w-4 h-4 mr-2" />
        Simular Erro de Rede
      </Button>
    </div>
  );
}

export default function ErrorBoundaryDemo() {
  const [globalError, setGlobalError] = useState(false);
  const [pageError, setPageError] = useState(false);
  const [componentError, setComponentError] = useState(false);
  const [dataTableError, setDataTableError] = useState(false);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          <Shield className="w-8 h-8 inline mr-2 text-blue-500" />
          Error Boundaries - Sistema Completo de Tratamento de Erros
        </h1>
        <p className="text-gray-600">
          Demonstração interativa do sistema robusto de Error Boundaries implementado.
        </p>

        <div className="flex justify-center gap-2 mt-4">
          <Badge variant="secondary">✅ Global Error Boundary</Badge>
          <Badge variant="secondary">✅ Page Error Boundary</Badge>
          <Badge variant="secondary">✅ Component Error Boundary</Badge>
          <Badge variant="secondary">✅ Error Reporting API</Badge>
        </div>
      </div>

      {/* Controles de Reset */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <RefreshCw className="w-5 h-5 mr-2" />
            Controles de Reset
          </CardTitle>
          <CardDescription>
            Use estes botões para resetar os estados de erro
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={() => setGlobalError(false)}
              variant="outline"
              size="sm"
            >
              Reset Global
            </Button>
            <Button
              onClick={() => setPageError(false)}
              variant="outline"
              size="sm"
            >
              Reset Page
            </Button>
            <Button
              onClick={() => setComponentError(false)}
              variant="outline"
              size="sm"
            >
              Reset Component
            </Button>
            <Button
              onClick={() => setDataTableError(false)}
              variant="outline"
              size="sm"
            >
              Reset Data Table
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Global Error Boundary Demo */}
      <ErrorBoundary
        level="global"
        name="DemoGlobal"
        onError={(error, errorInfo) => {
          console.log('🚨 Global Error Demo:', { error, errorInfo });
        }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-red-600">
              🌍 Global Error Boundary
            </CardTitle>
            <CardDescription>
              Captura erros em nível de aplicação com UI completa de fallback
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <ErrorComponent shouldError={globalError} />
              <Button
                onClick={() => setGlobalError(true)}
                variant="destructive"
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                Trigger Global Error
              </Button>
            </div>
          </CardContent>
        </Card>
      </ErrorBoundary>

      {/* Page Error Boundary Demo */}
      <ErrorBoundary
        level="page"
        name="DemoPage"
        onError={(error, errorInfo) => {
          console.log('📄 Page Error Demo:', { error, errorInfo });
        }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="text-orange-600">
              📄 Page Error Boundary
            </CardTitle>
            <CardDescription>
              Captura erros em nível de página com opções de navegação
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <ErrorComponent shouldError={pageError} />
              <Button
                onClick={() => setPageError(true)}
                variant="destructive"
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                Trigger Page Error
              </Button>
            </div>
          </CardContent>
        </Card>
      </ErrorBoundary>

      {/* Component Error Boundary Demo */}
      <Card>
        <CardHeader>
          <CardTitle className="text-yellow-600">
            🧩 Component Error Boundary
          </CardTitle>
          <CardDescription>
            Captura erros em componentes específicos com UI compacta
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <ComponentErrorBoundary name="DemoComponent">
              <ErrorComponent shouldError={componentError} />
            </ComponentErrorBoundary>
            <Button
              onClick={() => setComponentError(true)}
              variant="destructive"
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              Trigger Component Error
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Data Table Error Boundary Demo */}
      <Card>
        <CardHeader>
          <CardTitle className="text-purple-600">
            📊 Data Table Error Boundary
          </CardTitle>
          <CardDescription>
            Especializado para erros em tabelas e listas de dados
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <DataTableErrorBoundary dataType="demonstração">
              <ErrorComponent shouldError={dataTableError} />
            </DataTableErrorBoundary>
            <Button
              onClick={() => setDataTableError(true)}
              variant="destructive"
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              Trigger Data Table Error
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Error Scenarios */}
      <Card>
        <CardHeader>
          <CardTitle className="text-blue-600">
            🔬 Cenários Avançados
          </CardTitle>
          <CardDescription>
            Diferentes tipos de erros e situações reais
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ComponentErrorBoundary name="AsyncError">
              <AsyncErrorComponent />
            </ComponentErrorBoundary>

            <ComponentErrorBoundary name="NetworkError">
              <NetworkErrorComponent />
            </ComponentErrorBoundary>

            <div className="md:col-span-2">
              <ManualErrorReporter />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Reporting Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-green-600">
            📈 Sistema de Monitoramento
          </CardTitle>
          <CardDescription>
            Recursos implementados para tracking e resolução de erros
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-medium text-green-800">API de Erros</h3>
              <p className="text-sm text-green-600">
                <code>/api/errors</code> para centralizar relatórios
              </p>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-800">Error IDs</h3>
              <p className="text-sm text-blue-600">
                IDs únicos para rastreamento e suporte
              </p>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <h3 className="font-medium text-purple-800">Context Stack</h3>
              <p className="text-sm text-purple-600">
                Stack trace de componentes React
              </p>
            </div>

            <div className="bg-orange-50 p-4 rounded-lg">
              <h3 className="font-medium text-orange-800">User Context</h3>
              <p className="text-sm text-orange-600">
                URL, User-Agent, Session ID incluídos
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Implementation Stats */}
      <Card>
        <CardHeader>
          <CardTitle>📊 Estatísticas da Implementação</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">4</div>
              <div className="text-sm text-gray-600">Tipos de Error Boundary</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">3</div>
              <div className="text-sm text-gray-600">Níveis de Captura</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">1</div>
              <div className="text-sm text-gray-600">API de Relatórios</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">15+</div>
              <div className="text-sm text-gray-600">Testes Automatizados</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="text-center text-gray-500 text-sm">
        <p>
          ✨ Sistema completo implementado com sucesso!
          Abra o console do navegador para ver os logs detalhados dos erros.
        </p>
      </div>
    </div>
  );
}
