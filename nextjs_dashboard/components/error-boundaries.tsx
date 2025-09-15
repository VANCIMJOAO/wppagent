'use client';

import React from 'react';
import ErrorBoundary from './error-boundary';

// Error Boundary específico para Dashboard
export function DashboardErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      level="page"
      name="Dashboard"
      onError={(error, errorInfo) => {
        // Analytics específicos do dashboard
        console.error('Dashboard Error:', {
          error: error.message,
          component: errorInfo.componentStack,
          timestamp: new Date().toISOString()
        });
      }}
      fallback={
        <div className="p-8 text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
            <div className="text-red-600 text-6xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-red-800 mb-2">
              Erro no Dashboard
            </h2>
            <p className="text-red-700 mb-4">
              O dashboard encontrou um problema. Dados podem estar temporariamente indisponíveis.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
            >
              Recarregar Dashboard
            </button>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// Error Boundary para Conversas
export function ConversasErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      level="page"
      name="Conversas"
      onError={(error, errorInfo) => {
        // Log específico para conversas
        console.error('Conversas Error:', error.message);
      }}
      fallback={
        <div className="p-8 text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
            <div className="text-red-600 text-6xl mb-4">💬</div>
            <h2 className="text-xl font-semibold text-red-800 mb-2">
              Erro nas Conversas
            </h2>
            <p className="text-red-700 mb-4">
              Não foi possível carregar as conversas. O WhatsApp pode estar temporariamente indisponível.
            </p>
            <div className="space-y-2">
              <button
                onClick={() => window.location.reload()}
                className="block w-full bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
              >
                Tentar Novamente
              </button>
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="block w-full bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 transition-colors"
              >
                Voltar ao Dashboard
              </button>
            </div>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// Error Boundary para Clientes
export function ClientesErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      level="page"
      name="Clientes"
      fallback={
        <div className="p-8 text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
            <div className="text-red-600 text-6xl mb-4">👥</div>
            <h2 className="text-xl font-semibold text-red-800 mb-2">
              Erro nos Clientes
            </h2>
            <p className="text-red-700 mb-4">
              Falha ao carregar informações de clientes.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
            >
              Recarregar Clientes
            </button>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// Error Boundary para Agendamentos
export function AgendamentosErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      level="page"
      name="Agendamentos"
      fallback={
        <div className="p-8 text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
            <div className="text-red-600 text-6xl mb-4">📅</div>
            <h2 className="text-xl font-semibold text-red-800 mb-2">
              Erro nos Agendamentos
            </h2>
            <p className="text-red-700 mb-4">
              Sistema de agendamento temporariamente indisponível.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
            >
              Recarregar Agendamentos
            </button>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// Error Boundary para Componentes pequenos
export function ComponentErrorBoundary({
  children,
  name = 'Component'
}: {
  children: React.ReactNode;
  name?: string;
}) {
  return (
    <ErrorBoundary
      level="component"
      name={name}
    >
      {children}
    </ErrorBoundary>
  );
}

// Error Boundary para Modais
export function ModalErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      level="component"
      name="Modal"
      fallback={
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-700 text-sm">
            ⚠️ Erro ao carregar modal. Tente fechar e abrir novamente.
          </p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// Error Boundary para Formulários
export function FormErrorBoundary({
  children,
  formName = 'Formulário'
}: {
  children: React.ReactNode;
  formName?: string;
}) {
  return (
    <ErrorBoundary
      level="component"
      name={`Form-${formName}`}
      fallback={
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <p className="text-red-700 text-sm mb-2">
            ⚠️ Erro no {formName.toLowerCase()}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="text-xs bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 transition-colors"
          >
            Recarregar página
          </button>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// Error Boundary para Tabelas/Listas
export function DataTableErrorBoundary({
  children,
  dataType = 'dados'
}: {
  children: React.ReactNode;
  dataType?: string;
}) {
  return (
    <ErrorBoundary
      level="component"
      name={`DataTable-${dataType}`}
      fallback={
        <div className="p-8 text-center bg-red-50 border border-red-200 rounded-lg">
          <div className="text-red-600 text-4xl mb-3">📋</div>
          <h3 className="font-medium text-red-800 mb-2">
            Erro ao carregar {dataType}
          </h3>
          <p className="text-sm text-red-700 mb-4">
            Falha na comunicação com o servidor
          </p>
          <button
            onClick={() => window.location.reload()}
            className="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700 transition-colors"
          >
            Tentar Novamente
          </button>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}

// Hook para relatar erros manualmente
export function useErrorReporter() {
  const reportError = React.useCallback(async (error: Error, context?: string) => {
    try {
      const errorReport = {
        id: `manual_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        message: error.message,
        stack: error.stack,
        level: 'component' as const,
        name: context || 'Manual Report',
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        userId: localStorage.getItem('userId'),
        sessionId: sessionStorage.getItem('sessionId'),
        retryCount: 0
      };

      await fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorReport)
      });

      console.log(`✅ Manual error reported: ${errorReport.id}`);
    } catch (reportingError) {
      console.error('❌ Failed to report manual error:', reportingError);
    }
  }, []);

  return { reportError };
}
