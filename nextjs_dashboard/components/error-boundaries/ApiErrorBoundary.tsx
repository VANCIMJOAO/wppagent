'use client';

import React, { ReactNode, ErrorInfo } from 'react';
import { AlertCircle, RefreshCw, Wifi, WifiOff, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ApiError extends Error {
  status?: number;
  statusText?: string;
  endpoint?: string;
  method?: string;
  requestId?: string;
  isNetworkError?: boolean;
  isTimeoutError?: boolean;
  retryAfter?: number;
}

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  endpoint?: string;
  method?: string;
  level?: 'critical' | 'important' | 'optional';
  onError?: (error: ApiError, errorInfo: ErrorInfo) => void;
  enableRetry?: boolean;
  retryDelay?: number;
  maxRetries?: number;
  showToast?: boolean;
  enableOfflineMode?: boolean;
}

interface State {
  hasError: boolean;
  error?: ApiError;
  errorInfo?: ErrorInfo;
  isRetrying: boolean;
  retryCount: number;
  isOnline: boolean;
}

export class ApiErrorBoundary extends React.Component<Props, State> {
  private retryTimeout: NodeJS.Timeout | null = null;
  private errorId: string = '';

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      isRetrying: false,
      retryCount: 0,
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true
    };

    this.errorId = `api_err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    const apiError = error as ApiError;

    // Categorize API errors
    if (error.message.includes('fetch')) {
      apiError.isNetworkError = true;
    }

    if (error.message.includes('timeout')) {
      apiError.isTimeoutError = true;
    }

    return {
      hasError: true,
      error: apiError,
      isRetrying: false
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const apiError = error as ApiError;

    // Enrich error with API context
    if (this.props.endpoint) {
      apiError.endpoint = this.props.endpoint;
    }

    if (this.props.method) {
      apiError.method = this.props.method;
    }

    console.group(`🚨 API Error Boundary [${this.props.level || 'important'}]`);
    console.error('API Error:', apiError);
    console.error('Endpoint:', this.props.endpoint);
    console.error('Method:', this.props.method);
    console.error('Error Info:', errorInfo);
    console.groupEnd();

    this.setState({ errorInfo });

    // Report error to monitoring
    this.reportApiError(apiError, errorInfo);

    // Show toast notification if enabled
    if (this.props.showToast) {
      this.showErrorToast(apiError);
    }

    // Auto-retry for network errors if enabled
    if (this.props.enableRetry && this.isRetryableError(apiError)) {
      this.scheduleRetry();
    }

    // Custom error handler
    if (this.props.onError) {
      this.props.onError(apiError, errorInfo);
    }
  }

  componentDidMount() {
    // Listen for online/offline events
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.handleOnline);
      window.addEventListener('offline', this.handleOffline);
    }
  }

  componentWillUnmount() {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }

    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleOnline);
      window.removeEventListener('offline', this.handleOffline);
    }
  }

  private handleOnline = () => {
    this.setState({ isOnline: true });

    // Auto-retry when coming back online
    if (this.state.hasError && this.state.error?.isNetworkError) {
      this.handleRetry();
    }
  };

  private handleOffline = () => {
    this.setState({ isOnline: false });
  };

  private isRetryableError = (error: ApiError): boolean => {
    // Retry network errors
    if (error.isNetworkError || error.isTimeoutError) {
      return true;
    }

    // Retry 5xx server errors
    if (error.status && error.status >= 500) {
      return true;
    }

    // Retry specific status codes
    if (error.status && [408, 429, 503, 504].includes(error.status)) {
      return true;
    }

    return false;
  };

  private scheduleRetry = () => {
    const { retryDelay = 1000, maxRetries = 3 } = this.props;

    if (this.state.retryCount >= maxRetries) {
      return;
    }

    const delay = this.calculateRetryDelay();

    this.retryTimeout = setTimeout(() => {
      this.handleRetry();
    }, delay);
  };

  private calculateRetryDelay = (): number => {
    const { retryDelay = 1000 } = this.props;
    const { retryCount, error } = this.state;

    // Check for Retry-After header
    if (error?.retryAfter) {
      return error.retryAfter * 1000;
    }

    // Exponential backoff
    return retryDelay * Math.pow(2, retryCount) + Math.random() * 1000;
  };

  private reportApiError = async (error: ApiError, errorInfo: ErrorInfo) => {
    try {
      const errorReport = {
        id: this.errorId,
        type: 'api_error',
        message: error.message,
        stack: error.stack,
        endpoint: error.endpoint || this.props.endpoint,
        method: error.method || this.props.method,
        status: error.status,
        statusText: error.statusText,
        isNetworkError: error.isNetworkError,
        isTimeoutError: error.isTimeoutError,
        level: this.props.level || 'important',
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
        isOnline: this.state.isOnline,
        retryCount: this.state.retryCount,
        // ✅ SEGURO: sessionId para debugging (não-sensível)
        sessionId: typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('sessionId') : null
      };

      await fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorReport)
      });

    } catch (reportingError) {
      console.error('Failed to report API error:', reportingError);
    }
  };

  private showErrorToast = (error: ApiError) => {
    // This would be called via a toast hook in a real implementation
    console.log('Toast:', {
      title: 'Erro na API',
      description: this.getErrorMessage(error),
      variant: 'destructive'
    });
  };

  private getErrorMessage = (error: ApiError): string => {
    if (!this.state.isOnline) {
      return 'Sem conexão com a internet. Verifique sua rede.';
    }

    if (error.isNetworkError) {
      return 'Problema de conexão. Tentando novamente...';
    }

    if (error.isTimeoutError) {
      return 'Tempo limite esgotado. Tentando novamente...';
    }

    if (error.status) {
      switch (error.status) {
        case 400:
          return 'Dados inválidos enviados ao servidor.';
        case 401:
          return 'Sessão expirada. Faça login novamente.';
        case 403:
          return 'Você não tem permissão para esta ação.';
        case 404:
          return 'Recurso não encontrado.';
        case 429:
          return 'Muitas tentativas. Aguarde um momento.';
        case 500:
          return 'Erro interno do servidor. Tentando novamente...';
        case 502:
        case 503:
        case 504:
          return 'Servidor temporariamente indisponível.';
        default:
          return `Erro do servidor (${error.status}): ${error.statusText || 'Erro desconhecido'}`;
      }
    }

    return error.message || 'Erro desconhecido na API.';
  };

  private handleRetry = () => {
    const { maxRetries = 3 } = this.props;

    if (this.state.retryCount >= maxRetries) {
      return;
    }

    this.setState(prevState => ({
      isRetrying: true,
      retryCount: prevState.retryCount + 1
    }));

    // Clear error state to trigger re-render
    setTimeout(() => {
      this.setState({
        hasError: false,
        error: undefined,
        errorInfo: undefined,
        isRetrying: false
      });
    }, 100);
  };

  private handleForceRefresh = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { level = 'important', enableRetry = true, maxRetries = 3, enableOfflineMode = false } = this.props;
      const { error, retryCount, isRetrying, isOnline } = this.state;

      // Custom fallback
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Different UI based on error level
      if (level === 'critical') {
        return <CriticalApiErrorFallback
          error={error!}
          errorId={this.errorId}
          isRetrying={isRetrying}
          retryCount={retryCount}
          maxRetries={maxRetries}
          isOnline={isOnline}
          onRetry={enableRetry ? this.handleRetry : undefined}
          onRefresh={this.handleForceRefresh}
        />;
      }

      if (level === 'optional') {
        return <OptionalApiErrorFallback
          error={error!}
          errorId={this.errorId}
          isRetrying={isRetrying}
          retryCount={retryCount}
          maxRetries={maxRetries}
          isOnline={isOnline}
          onRetry={enableRetry ? this.handleRetry : undefined}
          enableOfflineMode={enableOfflineMode}
        />;
      }

      // Important level (default)
      return <ImportantApiErrorFallback
        error={error!}
        errorId={this.errorId}
        isRetrying={isRetrying}
        retryCount={retryCount}
        maxRetries={maxRetries}
        isOnline={isOnline}
        onRetry={enableRetry ? this.handleRetry : undefined}
        endpoint={this.props.endpoint}
      />;
    }

    return this.props.children;
  }
}

// Critical API Error - Blocks entire section
function CriticalApiErrorFallback({
  error,
  errorId,
  isRetrying,
  retryCount,
  maxRetries,
  isOnline,
  onRetry,
  onRefresh
}: {
  error: ApiError;
  errorId: string;
  isRetrying: boolean;
  retryCount: number;
  maxRetries: number;
  isOnline: boolean;
  onRetry?: () => void;
  onRefresh: () => void;
}) {
  return (
    <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
      <div className="flex items-start">
        <AlertTriangle className="w-6 h-6 text-red-500 mt-1 mr-4 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            Serviço Indisponível
          </h3>
          <p className="text-red-700 mb-4">
            Um serviço crítico está temporariamente indisponível.
            {!isOnline && ' Verifique sua conexão com a internet.'}
          </p>

          <div className="flex items-center gap-2 mb-4">
            {!isOnline ? (
              <WifiOff className="w-4 h-4 text-red-500" />
            ) : (
              <Wifi className="w-4 h-4 text-green-500" />
            )}
            <span className="text-sm text-red-600">
              Status: {isOnline ? 'Online' : 'Offline'}
            </span>
          </div>

          <div className="flex gap-2">
            {onRetry && retryCount < maxRetries && (
              <Button
                onClick={onRetry}
                disabled={isRetrying}
                variant="outline"
                className="border-red-300 text-red-700 hover:bg-red-100"
              >
                {isRetrying ? (
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

            <Button
              onClick={onRefresh}
              variant="outline"
              className="border-red-300 text-red-700 hover:bg-red-100"
            >
              Recarregar Página
            </Button>
          </div>

          <p className="text-xs text-red-600 mt-3">
            ID do Erro: {errorId}
          </p>
        </div>
      </div>
    </div>
  );
}

// Important API Error - Shows error but allows partial functionality
function ImportantApiErrorFallback({
  error,
  errorId,
  isRetrying,
  retryCount,
  maxRetries,
  isOnline,
  onRetry,
  endpoint
}: {
  error: ApiError;
  errorId: string;
  isRetrying: boolean;
  retryCount: number;
  maxRetries: number;
  isOnline: boolean;
  onRetry?: () => void;
  endpoint?: string;
}) {
  return (
    <Alert className="border-amber-200 bg-amber-50">
      <AlertCircle className="h-4 w-4 text-amber-500" />
      <AlertDescription className="text-amber-800">
        <div className="flex justify-between items-start">
          <div>
            <p className="font-medium mb-1">
              Falha ao carregar dados{endpoint && ` de ${endpoint}`}
            </p>
            <p className="text-sm mb-2">
              {!isOnline ? 'Sem conexão com a internet.' : 'Problema temporário no servidor.'}
            </p>
            {onRetry && retryCount < maxRetries && (
              <Button
                onClick={onRetry}
                disabled={isRetrying}
                size="sm"
                variant="outline"
                className="border-amber-300 text-amber-700 hover:bg-amber-100"
              >
                {isRetrying ? (
                  <>
                    <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                    Tentando...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Tentar Novamente
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
        <p className="text-xs text-amber-600 mt-2">
          ID: {errorId}
        </p>
      </AlertDescription>
    </Alert>
  );
}

// Optional API Error - Minimal error display, doesn't block UI
function OptionalApiErrorFallback({
  error,
  errorId,
  isRetrying,
  retryCount,
  maxRetries,
  isOnline,
  onRetry,
  enableOfflineMode
}: {
  error: ApiError;
  errorId: string;
  isRetrying: boolean;
  retryCount: number;
  maxRetries: number;
  isOnline: boolean;
  onRetry?: () => void;
  enableOfflineMode?: boolean;
}) {
  // For optional features, show minimal error or hide completely
  if (enableOfflineMode && !isOnline) {
    return (
      <div className="p-2 bg-gray-100 rounded text-center text-sm text-gray-600">
        <WifiOff className="w-4 h-4 inline mr-1" />
        Modo offline - alguns recursos não estão disponíveis
      </div>
    );
  }

  return (
    <div className="p-2 bg-blue-50 border border-blue-200 rounded text-center">
      <p className="text-sm text-blue-700">
        {isRetrying ? (
          <>
            <RefreshCw className="w-3 h-3 inline mr-1 animate-spin" />
            Recarregando...
          </>
        ) : (
          'Conteúdo indisponível no momento'
        )}
      </p>
      {onRetry && retryCount < maxRetries && !isRetrying && (
        <button
          onClick={onRetry}
          className="text-xs text-blue-600 hover:text-blue-800 mt-1 underline"
        >
          Tentar novamente
        </button>
      )}
    </div>
  );
}

export default ApiErrorBoundary;
