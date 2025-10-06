'use client';

import React, { Component, ReactNode, ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, Copy, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { debugLog } from '@/lib/debug';

export interface UniversalErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: 'global' | 'page' | 'component' | 'modal' | 'form' | 'table';
  name?: string;
  context?: string;
  enableRetry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  showDetails?: boolean;
  customActions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'ghost' | 'destructive';
  }>;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorId?: string;
  retryCount: number;
  isRetrying: boolean;
  isOnline: boolean;
}

export class UniversalErrorBoundary extends Component<UniversalErrorBoundaryProps, State> {
  private retryTimer: NodeJS.Timeout | null = null;

  constructor(props: UniversalErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      retryCount: 0,
      isRetrying: false,
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return {
      hasError: true,
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { level = 'component', name = 'Unknown', onError, context } = this.props;

    console.group(`🚨 Universal Error Boundary [${level}]${name ? ` - ${name}` : ''}`);
    debugLog.error('Error:', error);
    debugLog.error('Error Info:', errorInfo);
    debugLog.error('Context:', context);
    debugLog.error('Component Stack:', errorInfo.componentStack);
    console.groupEnd();

    this.setState({ errorInfo });

    // Report error to monitoring service
    this.reportError(error, errorInfo);

    // Custom error handler
    if (onError) {
      onError(error, errorInfo);
    }

    // Listen for online/offline status
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.handleOnline);
      window.addEventListener('offline', this.handleOffline);
    }
  }

  componentWillUnmount() {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleOnline);
      window.removeEventListener('offline', this.handleOffline);
    }
  }

  private handleOnline = () => {
    this.setState({ isOnline: true });
  };

  private handleOffline = () => {
    this.setState({ isOnline: false });
  };

  private reportError = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      const errorReport = {
        id: this.state.errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        level: this.props.level || 'component',
        name: this.props.name || 'Unknown',
        context: this.props.context,
        timestamp: new Date().toISOString(),
        userAgent: typeof window !== 'undefined' ? navigator.userAgent : 'SSR',
        url: typeof window !== 'undefined' ? window.location.href : 'SSR',
        userId: typeof window !== 'undefined' ? localStorage.getItem('userId') : null,
        sessionId: typeof window !== 'undefined' ? sessionStorage.getItem('sessionId') : null,
        retryCount: this.state.retryCount,
        isOnline: this.state.isOnline
      };

      // Send to error reporting API
      await fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorReport)
      });

      debugLog.info(`✅ Error reported with ID: ${errorReport.id}`);
    } catch (reportingError) {
      debugLog.error('Failed to report error:', reportingError);
    }
  };

  private handleRetry = () => {
    const { enableRetry = true, maxRetries = 3, retryDelay = 1000 } = this.props;
    
    if (!enableRetry || this.state.retryCount >= maxRetries) {
      debugLog.warn('Maximum retry attempts reached');
      return;
    }

    this.setState({ isRetrying: true });
    
    this.retryTimer = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: undefined,
        errorInfo: undefined,
        errorId: undefined,
        retryCount: prevState.retryCount + 1,
        isRetrying: false
      }));
    }, retryDelay);
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
Context: ${this.props.context || 'N/A'}
Level: ${this.props.level || 'component'}
    `.trim();

    try {
      await navigator.clipboard.writeText(errorDetails);
      debugLog.success('Error details copied to clipboard');
    } catch (err) {
      debugLog.error('Failed to copy error details:', err);
    }
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { level = 'component', name, showDetails = false } = this.props;
      const { error, errorId, retryCount, isRetrying, isOnline } = this.state;
      const maxRetries = this.props.maxRetries || 3;

      // Render based on error level
      switch (level) {
        case 'component':
          return <ComponentErrorFallback
            error={error!}
            errorId={errorId!}
            onRetry={this.handleRetry}
            retryCount={retryCount}
            maxRetries={maxRetries}
            isRetrying={isRetrying}
            name={name}
          />;

        case 'modal':
          return <ModalErrorFallback
            error={error!}
            errorId={errorId!}
            onRetry={this.handleRetry}
            name={name}
          />;

        case 'form':
          return <FormErrorFallback
            error={error!}
            errorId={errorId!}
            onRetry={this.handleRetry}
            name={name}
          />;

        case 'table':
          return <TableErrorFallback
            error={error!}
            errorId={errorId!}
            onRetry={this.handleRetry}
            name={name}
          />;

        case 'page':
          return <PageErrorFallback
            error={error!}
            errorId={errorId!}
            onRetry={this.handleRetry}
            onGoHome={this.handleGoHome}
            onCopyDetails={this.copyErrorDetails}
            retryCount={retryCount}
            maxRetries={maxRetries}
            isRetrying={isRetrying}
            name={name}
            customActions={this.props.customActions}
          />;

        case 'global':
        default:
          return <GlobalErrorFallback
            error={error!}
            errorInfo={this.state.errorInfo}
            errorId={errorId!}
            onRetry={this.handleRetry}
            onReload={this.handleReload}
            onCopyDetails={this.copyErrorDetails}
            retryCount={retryCount}
            maxRetries={maxRetries}
            isRetrying={isRetrying}
            isOnline={isOnline}
            showDetails={showDetails}
            name={name}
            customActions={this.props.customActions}
          />;
      }
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
  maxRetries,
  isRetrying,
  name
}: {
  error: Error;
  errorId: string;
  onRetry: () => void;
  retryCount: number;
  maxRetries: number;
  isRetrying: boolean;
  name?: string;
}) {
  return (
    <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
      <div className="flex items-start">
        <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-red-800">
            Erro no componente {name ? `"${name}"` : ''}
          </h3>
          <p className="text-sm text-red-700 mt-1">
            {error.message || 'Falha ao carregar este componente.'}
          </p>
          {retryCount < maxRetries && !isRetrying ? (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="mt-2 border-red-300 text-red-700 hover:bg-red-100"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Tentar novamente ({retryCount}/{maxRetries})
            </Button>
          ) : isRetrying ? (
            <div className="mt-2 text-xs text-red-600">
              <RefreshCw className="w-3 h-3 inline mr-1 animate-spin" />
              Tentando novamente...
            </div>
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

// Modal-level error fallback
function ModalErrorFallback({
  error,
  errorId,
  onRetry,
  name
}: {
  error: Error;
  errorId: string;
  onRetry: () => void;
  name?: string;
}) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded">
      <p className="text-red-700 text-sm mb-2">
        ⚠️ Erro ao carregar {name || 'modal'}. Tente fechar e abrir novamente.
      </p>
      <Button onClick={onRetry} variant="outline" size="sm">
        <RefreshCw className="w-3 h-3 mr-1" />
        Tentar novamente
      </Button>
    </div>
  );
}

// Form-level error fallback
function FormErrorFallback({
  error,
  errorId,
  onRetry,
  name
}: {
  error: Error;
  errorId: string;
  onRetry: () => void;
  name?: string;
}) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded">
      <p className="text-red-700 text-sm mb-2">
        ⚠️ Erro no {name?.toLowerCase() || 'formulário'}
      </p>
      <Button onClick={onRetry} variant="outline" size="sm">
        <RefreshCw className="w-3 h-3 mr-1" />
        Recarregar formulário
      </Button>
    </div>
  );
}

// Table-level error fallback
function TableErrorFallback({
  error,
  errorId,
  onRetry,
  name
}: {
  error: Error;
  errorId: string;
  onRetry: () => void;
  name?: string;
}) {
  return (
    <div className="p-8 text-center bg-red-50 border border-red-200 rounded-lg">
      <div className="text-red-600 text-4xl mb-3">📋</div>
      <h3 className="font-medium text-red-800 mb-2">
        Erro ao carregar {name?.toLowerCase() || 'dados'}
      </h3>
      <p className="text-sm text-red-700 mb-4">
        Falha na comunicação com o servidor
      </p>
      <Button onClick={onRetry} variant="outline" size="sm">
        <RefreshCw className="w-3 h-3 mr-1" />
        Tentar Novamente
      </Button>
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
  maxRetries,
  isRetrying,
  name,
  customActions
}: {
  error: Error;
  errorId: string;
  onRetry: () => void;
  onGoHome: () => void;
  onCopyDetails: () => void;
  retryCount: number;
  maxRetries: number;
  isRetrying: boolean;
  name?: string;
  customActions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'ghost' | 'destructive';
  }>;
}) {
  return (
    <div className="min-h-96 flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center border border-red-200">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Erro na página {name ? `"${name}"` : ''}
        </h2>
        <p className="text-gray-600 mb-4">
          {error.message || 'Esta página encontrou um problema inesperado.'}
        </p>

        <div className="flex flex-col gap-2">
          {retryCount < maxRetries && !isRetrying ? (
            <Button onClick={onRetry} className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              Tentar novamente ({retryCount}/{maxRetries})
            </Button>
          ) : isRetrying ? (
            <div className="w-full py-2 text-sm text-gray-600">
              <RefreshCw className="w-4 h-4 inline mr-2 animate-spin" />
              Tentando novamente...
            </div>
          ) : null}

          <Button onClick={onGoHome} variant="outline" className="w-full">
            <Home className="w-4 h-4 mr-2" />
            Voltar ao Dashboard
          </Button>

          <Button onClick={onCopyDetails} variant="ghost" size="sm">
            <Copy className="w-3 h-3 mr-1" />
            Copiar detalhes (ID: {errorId})
          </Button>

          {customActions?.map((action, index) => (
            <Button
              key={index}
              onClick={action.onClick}
              variant={action.variant || 'outline'}
              className="w-full"
            >
              {action.label}
            </Button>
          ))}
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
  maxRetries,
  isRetrying,
  isOnline,
  showDetails,
  name,
  customActions
}: {
  error: Error;
  errorInfo?: ErrorInfo;
  errorId: string;
  onRetry: () => void;
  onReload: () => void;
  onCopyDetails: () => void;
  retryCount: number;
  maxRetries: number;
  isRetrying: boolean;
  isOnline: boolean;
  showDetails: boolean;
  name?: string;
  customActions?: Array<{
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'ghost' | 'destructive';
  }>;
}) {
  const isDev = typeof window !== 'undefined' && window.location.hostname === 'localhost';

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

        {/* Network Status */}
        {!isOnline && (
          <Alert className="mb-6 border-orange-200 bg-orange-50">
            <WifiOff className="h-4 w-4 text-orange-600" />
            <AlertDescription className="text-orange-800">
              Você está offline. Verifique sua conexão com a internet.
            </AlertDescription>
          </Alert>
        )}

        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <p className="text-sm text-gray-700">
            <strong>ID do Erro:</strong> <code className="bg-gray-200 px-1 rounded">{errorId}</code>
          </p>
          {name && (
            <p className="text-sm text-gray-700 mt-1">
              <strong>Componente:</strong> {name}
            </p>
          )}
          <p className="text-xs text-gray-500 mt-2">
            Use este ID para reportar o problema ao suporte
          </p>
        </div>

        {(isDev || showDetails) && (
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
          {retryCount < maxRetries && !isRetrying ? (
            <Button onClick={onRetry} className="w-full">
              <RefreshCw className="w-4 h-4 mr-2" />
              Tentar Novamente ({retryCount}/{maxRetries})
            </Button>
          ) : isRetrying ? (
            <div className="w-full py-2 text-sm text-gray-600">
              <RefreshCw className="w-4 h-4 inline mr-2 animate-spin" />
              Tentando novamente...
            </div>
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

          {customActions?.map((action, index) => (
            <Button
              key={index}
              onClick={action.onClick}
              variant={action.variant || 'outline'}
              className="w-full"
            >
              {action.label}
            </Button>
          ))}

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

// Convenience components for common use cases
export const DashboardErrorBoundary = ({ children }: { children: ReactNode }) => (
  <UniversalErrorBoundary
    level="page"
    name="Dashboard"
    context="Dashboard principal"
    customActions={[
      { label: 'Recarregar Dashboard', onClick: () => window.location.reload() }
    ]}
  >
    {children}
  </UniversalErrorBoundary>
);

export const ConversasErrorBoundary = ({ children }: { children: ReactNode }) => (
  <UniversalErrorBoundary
    level="page"
    name="Conversas"
    context="Sistema de conversas WhatsApp"
    customActions={[
      { label: 'Verificar WhatsApp', onClick: () => window.location.href = '/configuracoes' }
    ]}
  >
    {children}
  </UniversalErrorBoundary>
);

export const ClientesErrorBoundary = ({ children }: { children: ReactNode }) => (
  <UniversalErrorBoundary
    level="page"
    name="Clientes"
    context="Base de dados de clientes"
  >
    {children}
  </UniversalErrorBoundary>
);

export const AgendamentosErrorBoundary = ({ children }: { children: ReactNode }) => (
  <UniversalErrorBoundary
    level="page"
    name="Agendamentos"
    context="Sistema de agendamentos"
  >
    {children}
  </UniversalErrorBoundary>
);

export const ModalErrorBoundary = ({ children }: { children: ReactNode }) => (
  <UniversalErrorBoundary level="modal" name="Modal">
    {children}
  </UniversalErrorBoundary>
);

export const FormErrorBoundary = ({ 
  children, 
  formName = 'Formulário' 
}: { 
  children: ReactNode; 
  formName?: string; 
}) => (
  <UniversalErrorBoundary level="form" name={formName}>
    {children}
  </UniversalErrorBoundary>
);

export const TableErrorBoundary = ({ 
  children, 
  dataType = 'dados' 
}: { 
  children: ReactNode; 
  dataType?: string; 
}) => (
  <UniversalErrorBoundary level="table" name={`Tabela-${dataType}`}>
    {children}
  </UniversalErrorBoundary>
);

export const ComponentErrorBoundary = ({ 
  children, 
  name = 'Component' 
}: { 
  children: ReactNode; 
  name?: string; 
}) => (
  <UniversalErrorBoundary level="component" name={name}>
    {children}
  </UniversalErrorBoundary>
);
