'use client';

import React from 'react';
import { AlertCircle, RefreshCw, Home, TrendingUp, Users, MessageCircle, Calendar, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ErrorFallbackProps {
  error?: Error | null;
  onRetry?: () => void;
  onReset?: () => void;
  loading?: boolean;
  retryCount?: number;
  maxRetries?: number;
}

// Dashboard KPIs Error Fallback
export function DashboardKpisErrorFallback({
  error,
  onRetry,
  loading = false,
  retryCount = 0,
  maxRetries = 3
}: ErrorFallbackProps) {
  const mockKpis = [
    { title: 'Total Clientes', value: '---', icon: Users },
    { title: 'Conversas Ativas', value: '---', icon: MessageCircle },
    { title: 'Agendamentos', value: '---', icon: Calendar },
    { title: 'Taxa Conversão', value: '---', icon: TrendingUp },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {mockKpis.map((kpi, index) => (
        <Card key={index} className="border-red-200 bg-red-50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-800">
              {kpi.title}
            </CardTitle>
            <kpi.icon className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-700">
              {loading ? '...' : kpi.value}
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-red-600">
                Erro ao carregar
              </p>
              {onRetry && retryCount < maxRetries && (
                <Button
                  onClick={onRetry}
                  disabled={loading}
                  size="sm"
                  variant="ghost"
                  className="h-6 text-xs text-red-600 hover:text-red-800"
                >
                  {loading ? (
                    <RefreshCw className="h-3 w-3 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3 w-3" />
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Charts Error Fallback
export function ChartsErrorFallback({
  error,
  onRetry,
  loading = false,
  retryCount = 0,
  maxRetries = 3
}: ErrorFallbackProps) {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <CardHeader>
        <CardTitle className="text-amber-800 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          Erro ao Carregar Gráficos
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-full h-32 bg-amber-100 rounded-lg flex items-center justify-center mb-4">
            <div className="text-amber-600 text-sm">Dados indisponíveis</div>
          </div>

          <p className="text-amber-700 text-sm text-center mb-4">
            {error?.message || 'Não foi possível carregar os gráficos no momento.'}
          </p>

          {onRetry && retryCount < maxRetries && (
            <Button
              onClick={onRetry}
              disabled={loading}
              variant="outline"
              className="border-amber-300 text-amber-700 hover:bg-amber-100"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Tentando...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Tentar Novamente ({retryCount}/{maxRetries})
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Recent Activity Error Fallback
export function RecentActivityErrorFallback({
  error,
  onRetry,
  loading = false,
  retryCount = 0,
  maxRetries = 3
}: ErrorFallbackProps) {
  return (
    <Card className="border-blue-200 bg-blue-50">
      <CardHeader>
        <CardTitle className="text-blue-800">Atividade Recente</CardTitle>
      </CardHeader>
      <CardContent>
        <Alert className="border-blue-200 bg-blue-100">
          <AlertCircle className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium mb-1">Erro ao carregar atividades</p>
                <p className="text-sm">
                  {error?.message || 'Atividades recentes não estão disponíveis no momento.'}
                </p>
              </div>
              {onRetry && retryCount < maxRetries && (
                <Button
                  onClick={onRetry}
                  disabled={loading}
                  size="sm"
                  variant="outline"
                  className="ml-2 border-blue-300 text-blue-700 hover:bg-blue-100"
                >
                  {loading ? (
                    <RefreshCw className="h-3 w-3 animate-spin" />
                  ) : (
                    <RefreshCw className="h-3 w-3" />
                  )}
                </Button>
              )}
            </div>
          </AlertDescription>
        </Alert>

        {/* Mock recent activity items to maintain layout */}
        <div className="space-y-3 mt-4 opacity-50">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start space-x-3 p-2 border border-blue-200 rounded-lg bg-blue-100">
              <div className="w-8 h-8 bg-blue-200 rounded-full flex items-center justify-center">
                <MessageCircle className="w-4 h-4 text-blue-500" />
              </div>
              <div className="flex-1">
                <div className="h-4 bg-blue-200 rounded w-3/4 mb-1"></div>
                <div className="h-3 bg-blue-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Network Status Error Fallback
export function NetworkErrorFallback({
  error,
  onRetry,
  onReset,
  loading = false
}: ErrorFallbackProps) {
  const isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;

  return (
    <div className="flex flex-col items-center justify-center min-h-96 p-8 bg-gray-50 rounded-lg border border-gray-200">
      {isOnline ? (
        <Wifi className="w-16 h-16 text-gray-400 mb-4" />
      ) : (
        <WifiOff className="w-16 h-16 text-red-500 mb-4" />
      )}

      <h2 className="text-xl font-semibold text-gray-800 mb-2">
        {isOnline ? 'Problema de Conexão' : 'Sem Internet'}
      </h2>

      <p className="text-gray-600 text-center mb-6 max-w-md">
        {isOnline
          ? 'Não foi possível conectar com o servidor. Verifique se os serviços estão funcionando.'
          : 'Verifique sua conexão com a internet e tente novamente.'
        }
      </p>

      <div className="flex gap-3">
        {onRetry && (
          <Button
            onClick={onRetry}
            disabled={loading}
            className="min-w-32"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Tentando...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Tentar Novamente
              </>
            )}
          </Button>
        )}

        {onReset && (
          <Button
            onClick={onReset}
            variant="outline"
          >
            <Home className="w-4 h-4 mr-2" />
            Início
          </Button>
        )}
      </div>

      {error?.message && (
        <details className="mt-4 text-sm text-gray-500">
          <summary className="cursor-pointer hover:text-gray-700">
            Detalhes técnicos
          </summary>
          <pre className="mt-2 p-2 bg-gray-100 rounded text-xs max-w-md overflow-auto">
            {error.message}
          </pre>
        </details>
      )}
    </div>
  );
}

// Generic Table Error Fallback
export function TableErrorFallback({
  error,
  onRetry,
  loading = false,
  retryCount = 0,
  maxRetries = 3,
  tableName = 'dados'
}: ErrorFallbackProps & { tableName?: string }) {
  return (
    <div className="border border-gray-200 rounded-lg">
      <div className="p-6 text-center">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Erro ao Carregar {tableName}
        </h3>
        <p className="text-gray-600 mb-4">
          {error?.message || `Não foi possível carregar os ${tableName} no momento.`}
        </p>

        {onRetry && retryCount < maxRetries && (
          <Button
            onClick={onRetry}
            disabled={loading}
            variant="outline"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Carregando...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Tentar Novamente ({retryCount}/{maxRetries})
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

// Form Error Fallback
export function FormErrorFallback({
  error,
  onRetry,
  onReset,
  loading = false
}: ErrorFallbackProps) {
  return (
    <Alert className="border-red-200 bg-red-50">
      <AlertCircle className="h-4 w-4 text-red-500" />
      <AlertDescription className="text-red-800">
        <div className="flex justify-between items-start">
          <div>
            <p className="font-medium mb-1">Erro no Formulário</p>
            <p className="text-sm mb-3">
              {error?.message || 'Ocorreu um erro ao processar sua solicitação.'}
            </p>
            <div className="flex gap-2">
              {onRetry && (
                <Button
                  onClick={onRetry}
                  disabled={loading}
                  size="sm"
                  variant="outline"
                  className="border-red-300 text-red-700 hover:bg-red-100"
                >
                  {loading ? (
                    <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                  ) : (
                    <RefreshCw className="w-3 h-3 mr-1" />
                  )}
                  Tentar Novamente
                </Button>
              )}
              {onReset && (
                <Button
                  onClick={onReset}
                  size="sm"
                  variant="ghost"
                  className="text-red-700 hover:bg-red-100"
                >
                  Limpar Formulário
                </Button>
              )}
            </div>
          </div>
        </div>
      </AlertDescription>
    </Alert>
  );
}

// Minimal Error Fallback for optional features
export function MinimalErrorFallback({
  error,
  onRetry,
  loading = false
}: ErrorFallbackProps) {
  return (
    <div className="p-3 bg-gray-100 rounded text-center text-sm text-gray-600">
      <p className="mb-2">Conteúdo indisponível</p>
      {onRetry && (
        <button
          onClick={onRetry}
          disabled={loading}
          className="text-blue-600 hover:text-blue-800 underline text-xs"
        >
          {loading ? 'Carregando...' : 'Tentar novamente'}
        </button>
      )}
    </div>
  );
}
