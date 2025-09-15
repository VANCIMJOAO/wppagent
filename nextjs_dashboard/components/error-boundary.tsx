'use client';

import React, { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: 'global' | 'page' | 'component';
  name?: string;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId?: string;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  private retryCount = 0;
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return {
      hasError: true,
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { level = 'component', name = 'Unknown', onError } = this.props;

    console.group(`🚨 Error Boundary [${level}${name ? ` - ${name}` : ''}]`);
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Component Stack:', errorInfo.componentStack);
    console.groupEnd();

    this.setState({ errorInfo });

    // Report error to monitoring service
    this.reportError(error, errorInfo);

    // Custom error handler
    if (onError) {
      onError(error, errorInfo);
    }
  }

  private reportError = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      const errorReport = {
        id: this.state.errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        level: this.props.level || 'component',
        name: this.props.name || 'Unknown',
        timestamp: new Date().toISOString(),
        userAgent: typeof window !== 'undefined' ? navigator.userAgent : 'SSR',
        url: typeof window !== 'undefined' ? window.location.href : 'SSR',
        userId: typeof window !== 'undefined' ? localStorage.getItem('userId') : null,
        sessionId: typeof window !== 'undefined' ? sessionStorage.getItem('sessionId') : null,
        retryCount: this.retryCount
      };

      // Send to error reporting API
      await fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorReport)
      });

      console.log(`✅ Error reported with ID: ${errorReport.id}`);
    } catch (reportingError) {
      console.error('❌ Failed to report error:', reportingError);
    }
  };

  private handleRetry = () => {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      console.log(`🔄 Retry attempt ${this.retryCount}/${this.maxRetries}`);
      this.setState({
        hasError: false,
        error: undefined,
        errorInfo: undefined,
        errorId: undefined
      });
    } else {
      console.warn('⚠️ Maximum retry attempts reached');
      this.handleGoHome();
    }
  };

  private handleGoHome = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/dashboard';
    }
  };

  private handleReload = () => {
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  private copyErrorDetails = async () => {
    const errorDetails = `
Error ID: ${this.state.errorId}
Message: ${this.state.error?.message}
Stack: ${this.state.error?.stack}
Component Stack: ${this.state.errorInfo?.componentStack}
Timestamp: ${new Date().toISOString()}
URL: ${typeof window !== 'undefined' ? window.location.href : 'SSR'}
    `.trim();

    try {
      await navigator.clipboard.writeText(errorDetails);
      console.log('✅ Error details copied to clipboard');
    } catch (err) {
      console.error('❌ Failed to copy error details:', err);
    }
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { level = 'component' } = this.props;

      // Different UI based on error level
      if (level === 'component') {
        return <ComponentErrorFallback
          error={this.state.error!}
          errorId={this.state.errorId!}
          onRetry={this.handleRetry}
          retryCount={this.retryCount}
          maxRetries={this.maxRetries}
        />;
      }

      if (level === 'page') {
        return <PageErrorFallback
          error={this.state.error!}
          errorId={this.state.errorId!}
          onRetry={this.handleRetry}
          onGoHome={this.handleGoHome}
          onCopyDetails={this.copyErrorDetails}
          retryCount={this.retryCount}
          maxRetries={this.maxRetries}
        />;
      }

      // Global level
      return <GlobalErrorFallback
        error={this.state.error!}
        errorInfo={this.state.errorInfo}
        errorId={this.state.errorId!}
        onRetry={this.handleRetry}
        onReload={this.handleReload}
        onCopyDetails={this.copyErrorDetails}
        retryCount={this.retryCount}
        maxRetries={this.maxRetries}
      />;
    }

    return this.props.children;
  }
}

// Component-level error fallback
function ComponentErrorFallback({
  error,
  errorId,
  onRetry,
  retryCount,
  maxRetries
}: {
  error: Error;
  errorId: string;
  onRetry: () => void;
  retryCount: number;
  maxRetries: number;
}) {
  return (
    <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
      <div className="flex items-start">
        <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-red-800">
            Erro no componente
          </h3>
          <p className="text-sm text-red-700 mt-1">
            {error.message || 'Falha ao carregar este componente.'}
          </p>
          {retryCount < maxRetries ? (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="mt-2 border-red-300 text-red-700 hover:bg-red-100"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Tentar novamente ({retryCount}/{maxRetries})
            </Button>
          ) : (
            <p className="text-xs text-red-600 mt-2">
              Máximo de tentativas atingido. ID: {errorId}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// Page-level error fallback
function PageErrorFallback({
  error,
  errorId,
  onRetry,
  onGoHome,
  onCopyDetails,
  retryCount,
  maxRetries
}: {
  error: Error;
  errorId: string;
  onRetry: () => void;
  onGoHome: () => void;
  onCopyDetails: () => void;
  retryCount: number;
  maxRetries: number;
}) {
  return (
    <div className="min-h-96 flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center border border-red-200">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Erro na página
        </h2>
        <p className="text-gray-600 mb-4">
          {error.message || 'Esta página encontrou um problema inesperado.'}
        </p>

        <div className="flex flex-col gap-2">
          {retryCount < maxRetries ? (
            <Button onClick={onRetry} className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              Tentar novamente ({retryCount}/{maxRetries})
            </Button>
          ) : null}

          <Button onClick={onGoHome} variant="outline" className="w-full">
            <Home className="w-4 h-4 mr-2" />
            Voltar ao Dashboard
          </Button>

          <Button onClick={onCopyDetails} variant="ghost" size="sm">
            <Copy className="w-3 h-3 mr-1" />
            Copiar detalhes (ID: {errorId})
          </Button>
        </div>
      </div>
    </div>
  );
}

// Global-level error fallback
function GlobalErrorFallback({
  error,
  errorInfo,
  errorId,
  onRetry,
  onReload,
  onCopyDetails,
  retryCount,
  maxRetries
}: {
  error: Error;
  errorInfo?: ErrorInfo;
  errorId: string;
  onRetry: () => void;
  onReload: () => void;
  onCopyDetails: () => void;
  retryCount: number;
  maxRetries: number;
}) {
  const isDev = process.env.NODE_ENV === 'development';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="max-w-lg w-full bg-white rounded-lg shadow-xl p-8 text-center">
        <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-6" />
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          Ops! Algo deu errado
        </h1>
        <p className="text-gray-600 mb-6">
          Ocorreu um erro inesperado na aplicação. Nossa equipe foi notificada automaticamente.
        </p>

        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <p className="text-sm text-gray-700">
            <strong>ID do Erro:</strong> <code className="bg-gray-200 px-1 rounded">{errorId}</code>
          </p>
          <p className="text-xs text-gray-500 mt-2">
            Use este ID para reportar o problema ao suporte
          </p>
        </div>

        {isDev && (
          <details className="text-left bg-gray-100 p-4 rounded mb-6 text-sm">
            <summary className="font-medium cursor-pointer mb-2">Detalhes técnicos</summary>
            <div className="space-y-2">
              <div>
                <strong>Mensagem:</strong>
                <pre className="mt-1 text-xs bg-white p-2 rounded overflow-auto">
                  {error.message}
                </pre>
              </div>
              {error.stack && (
                <div>
                  <strong>Stack Trace:</strong>
                  <pre className="mt-1 text-xs bg-white p-2 rounded overflow-auto max-h-32">
                    {error.stack}
                  </pre>
                </div>
              )}
              {errorInfo?.componentStack && (
                <div>
                  <strong>Component Stack:</strong>
                  <pre className="mt-1 text-xs bg-white p-2 rounded overflow-auto max-h-32">
                    {errorInfo.componentStack}
                  </pre>
                </div>
              )}
            </div>
          </details>
        )}

        <div className="flex flex-col gap-3">
          {retryCount < maxRetries ? (
            <Button onClick={onRetry} className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              Tentar Novamente ({retryCount}/{maxRetries})
            </Button>
          ) : (
            <Button onClick={onReload} className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              Recarregar Página
            </Button>
          )}

          <Button onClick={onCopyDetails} variant="outline" className="w-full">
            <Copy className="w-4 h-4 mr-2" />
            Copiar Detalhes do Erro
          </Button>

          <div className="flex gap-2">
            <Button
              onClick={() => window.location.href = '/dashboard'}
              variant="ghost"
              className="flex-1"
            >
              <Home className="w-4 h-4 mr-2" />
              Dashboard
            </Button>
            <Button
              onClick={() => window.location.href = '/suporte'}
              variant="ghost"
              className="flex-1"
            >
              <Bug className="w-4 h-4 mr-2" />
              Suporte
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
