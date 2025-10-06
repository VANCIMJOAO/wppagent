'use client';

import React, { createContext, useContext, useReducer, useCallback, ReactNode, useEffect } from 'react';
import { AlertTriangle, RefreshCw, Trash2, CheckCircle, Clock, Wifi, WifiOff, Signal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

// Types
export interface AppError {
  id: string;
  type: 'api' | 'network' | 'validation' | 'auth' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details?: string;
  stack?: string;
  timestamp: string;
  context?: {
    level?: string;
    context?: string;
    retryCount?: number;
    componentStack?: string;
    errorBoundary?: string;
    url?: string;
    userId?: string | null;
    sessionId?: string | null;
  };
  retryCount: number;
  maxRetries: number;
  resolved?: boolean;
}

export interface ErrorState {
  errors: AppError[];
  globalError: AppError | null;
  networkStatus: 'online' | 'offline' | 'slow';
  errorCounts: {
    api: number;
    network: number;
    validation: number;
    auth: number;
    unknown: number;
  };
  recentErrors: AppError[];
  errorHistory: AppError[];
}

type ErrorAction =
  | { type: 'ADD_ERROR'; error: AppError }
  | { type: 'REMOVE_ERROR'; id: string }
  | { type: 'RESOLVE_ERROR'; id: string }
  | { type: 'CLEAR_ERRORS' }
  | { type: 'SET_GLOBAL_ERROR'; error: AppError | null }
  | { type: 'SET_NETWORK_STATUS'; status: 'online' | 'offline' | 'slow' }
  | { type: 'INCREMENT_RETRY'; id: string }
  | { type: 'ADD_TO_HISTORY'; error: AppError }
  | { type: 'CLEAR_HISTORY' };

const initialState: ErrorState = {
  errors: [],
  globalError: null,
  networkStatus: 'online',
  errorCounts: {
    api: 0,
    network: 0,
    validation: 0,
    auth: 0,
    unknown: 0
  },
  recentErrors: [],
  errorHistory: []
};

function errorReducer(state: ErrorState, action: ErrorAction): ErrorState {
  switch (action.type) {
    case 'ADD_ERROR': {
      const newError = action.error;
      const updatedCounts = {
        ...state.errorCounts,
        [newError.type]: state.errorCounts[newError.type] + 1
      };

      return {
        ...state,
        errors: [...state.errors, newError],
        errorCounts: updatedCounts,
        recentErrors: [newError, ...state.recentErrors].slice(0, 10),
        globalError: newError.severity === 'critical' ? newError : state.globalError
      };
    }

    case 'REMOVE_ERROR': {
      const errorToRemove = state.errors.find(e => e.id === action.id);
      const filteredErrors = state.errors.filter(e => e.id !== action.id);

      let updatedCounts = state.errorCounts;
      if (errorToRemove) {
        updatedCounts = {
          ...state.errorCounts,
          [errorToRemove.type]: Math.max(0, state.errorCounts[errorToRemove.type] - 1)
        };
      }

      return {
        ...state,
        errors: filteredErrors,
        errorCounts: updatedCounts,
        recentErrors: state.recentErrors.filter(e => e.id !== action.id),
        globalError: state.globalError?.id === action.id ? null : state.globalError
      };
    }

    case 'RESOLVE_ERROR': {
      const resolvedErrors = state.errors.map(error =>
        error.id === action.id
          ? { ...error, resolved: true }
          : error
      );

      return {
        ...state,
        errors: resolvedErrors,
        globalError: state.globalError?.id === action.id
          ? { ...state.globalError, resolved: true }
          : state.globalError,
        recentErrors: state.recentErrors.map(error =>
          error.id === action.id
            ? { ...error, resolved: true }
            : error
        )
      };
    }

    case 'CLEAR_ERRORS': {
      return {
        ...state,
        errors: [],
        globalError: null,
        errorCounts: {
          api: 0,
          network: 0,
          validation: 0,
          auth: 0,
          unknown: 0
        },
        recentErrors: []
      };
    }

    case 'SET_GLOBAL_ERROR': {
      return {
        ...state,
        globalError: action.error
      };
    }

    case 'SET_NETWORK_STATUS': {
      return {
        ...state,
        networkStatus: action.status
      };
    }

    case 'INCREMENT_RETRY': {
      return {
        ...state,
        errors: state.errors.map(error =>
          error.id === action.id
            ? { ...error, retryCount: error.retryCount + 1 }
            : error
        )
      };
    }

    case 'ADD_TO_HISTORY': {
      return {
        ...state,
        errorHistory: [action.error, ...state.errorHistory].slice(0, 100)
      };
    }

    case 'CLEAR_HISTORY': {
      return {
        ...state,
        errorHistory: []
      };
    }

    default:
      return state;
  }
}

export interface ErrorContextType {
  // State
  errors: AppError[];
  globalError: AppError | null;
  networkStatus: 'online' | 'offline' | 'slow';
  errorCounts: {
    api: number;
    network: number;
    validation: number;
    auth: number;
    unknown: number;
  };
  recentErrors: AppError[];
  errorHistory: AppError[];

  // Actions
  addError: (error: Omit<AppError, 'id' | 'timestamp'>) => string;
  removeError: (id: string) => void;
  resolveError: (id: string) => void;
  clearErrors: () => void;
  setGlobalError: (error: AppError | null) => void;
  incrementRetry: (id: string) => void;
  addToHistory: (error: AppError) => void;
  clearHistory: () => void;

  // Convenience methods
  addApiError: (message: string, context?: any) => string;
  addNetworkError: (message: string) => string;
  addValidationError: (message: string, context?: any) => string;
  addAuthError: (message: string) => string;

  // Helpers
  hasErrors: () => boolean;
  hasCriticalErrors: () => boolean;
  getErrorsByType: (type: AppError['type']) => AppError[];
  getRecentErrors: (minutes?: number) => AppError[];
  getErrorsBySeverity: (severity: AppError['severity']) => AppError[];
  getErrorStats: () => {
    total: number;
    byType: Record<string, number>;
    bySeverity: Record<string, number>;
    criticalCount: number;
    unresolvedCount: number;
  };
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export function ConsolidatedErrorProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(errorReducer, initialState);

  // Network status monitoring
  useEffect(() => {
    const handleOnline = () => {
      dispatch({ type: 'SET_NETWORK_STATUS', status: 'online' });
    };

    const handleOffline = () => {
      dispatch({ type: 'SET_NETWORK_STATUS', status: 'offline' });
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }
  }, []);

  const addError = useCallback((errorData: Omit<AppError, 'id' | 'timestamp'>): string => {
    const error: AppError = {
      ...errorData,
      id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString()
    };

    dispatch({ type: 'ADD_ERROR', error });
    dispatch({ type: 'ADD_TO_HISTORY', error });

    return error.id;
  }, []);

  const removeError = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_ERROR', id });
  }, []);

  const resolveError = useCallback((id: string) => {
    dispatch({ type: 'RESOLVE_ERROR', id });
  }, []);

  const clearErrors = useCallback(() => {
    dispatch({ type: 'CLEAR_ERRORS' });
  }, []);

  const setGlobalError = useCallback((error: AppError | null) => {
    dispatch({ type: 'SET_GLOBAL_ERROR', error });
  }, []);

  const incrementRetry = useCallback((id: string) => {
    dispatch({ type: 'INCREMENT_RETRY', id });
  }, []);

  const addToHistory = useCallback((error: AppError) => {
    dispatch({ type: 'ADD_TO_HISTORY', error });
  }, []);

  const clearHistory = useCallback(() => {
    dispatch({ type: 'CLEAR_HISTORY' });
  }, []);

  // Convenience methods
  const addApiError = useCallback((message: string, context?: any): string => {
    return addError({
      type: 'api',
      severity: 'medium',
      message,
      context,
      retryCount: 0,
      maxRetries: 3
    });
  }, [addError]);

  const addNetworkError = useCallback((message: string): string => {
    return addError({
      type: 'network',
      severity: 'high',
      message,
      retryCount: 0,
      maxRetries: 3
    });
  }, [addError]);

  const addValidationError = useCallback((message: string, context?: any): string => {
    return addError({
      type: 'validation',
      severity: 'low',
      message,
      context,
      retryCount: 0,
      maxRetries: 1
    });
  }, [addError]);

  const addAuthError = useCallback((message: string): string => {
    return addError({
      type: 'auth',
      severity: 'critical',
      message,
      retryCount: 0,
      maxRetries: 1
    });
  }, [addError]);

  // Helper methods
  const hasErrors = useCallback((): boolean => {
    return state.errors.length > 0;
  }, [state.errors.length]);

  const hasCriticalErrors = useCallback((): boolean => {
    return state.errors.some(error => error.severity === 'critical');
  }, [state.errors]);

  const getErrorsByType = useCallback((type: AppError['type']): AppError[] => {
    return state.errors.filter(error => error.type === type);
  }, [state.errors]);

  const getRecentErrors = useCallback((minutes: number = 5): AppError[] => {
    const cutoff = new Date(Date.now() - minutes * 60 * 1000);
    return state.errors.filter(error => new Date(error.timestamp) > cutoff);
  }, [state.errors]);

  const getErrorsBySeverity = useCallback((severity: AppError['severity']): AppError[] => {
    return state.errors.filter(error => error.severity === severity);
  }, [state.errors]);

  const getErrorStats = useCallback(() => {
    const total = state.errors.length;
    const byType = state.errorCounts;
    const bySeverity = state.errors.reduce((acc, error) => {
      acc[error.severity] = (acc[error.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    const criticalCount = state.errors.filter(error => error.severity === 'critical').length;
    const unresolvedCount = state.errors.filter(error => !error.resolved).length;

    return {
      total,
      byType,
      bySeverity,
      criticalCount,
      unresolvedCount
    };
  }, [state.errors, state.errorCounts]);

  const contextValue: ErrorContextType = {
    // State
    errors: state.errors,
    globalError: state.globalError,
    networkStatus: state.networkStatus,
    errorCounts: state.errorCounts,
    recentErrors: state.recentErrors,
    errorHistory: state.errorHistory,

    // Actions
    addError,
    removeError,
    resolveError,
    clearErrors,
    setGlobalError,
    incrementRetry,
    addToHistory,
    clearHistory,

    // Convenience methods
    addApiError,
    addNetworkError,
    addValidationError,
    addAuthError,

    // Helpers
    hasErrors,
    hasCriticalErrors,
    getErrorsByType,
    getRecentErrors,
    getErrorsBySeverity,
    getErrorStats
  };

  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
    </ErrorContext.Provider>
  );
}

export function useErrorHandler() {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useErrorHandler must be used within a ConsolidatedErrorProvider');
  }
  return context;
}

// Error Dashboard Component (integrated into the provider)
export function ErrorDashboard() {
  const {
    errors,
    globalError,
    networkStatus,
    errorCounts,
    recentErrors,
    errorHistory,
    clearErrors,
    removeError,
    resolveError,
    hasErrors,
    hasCriticalErrors,
    getRecentErrors,
    getErrorStats
  } = useErrorHandler();

  const [selectedError, setSelectedError] = React.useState<AppError | null>(null);
  const [showHistory, setShowHistory] = React.useState(false);

  const stats = getErrorStats();
  const recentErrors30min = getRecentErrors(30);

  const getSeverityColor = (severity: AppError['severity']) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTypeIcon = (type: AppError['type']) => {
    switch (type) {
      case 'api':
        return '🔌';
      case 'network':
        return '🌐';
      case 'validation':
        return '✏️';
      case 'auth':
        return '🔐';
      default:
        return '❓';
    }
  };

  const getNetworkStatusIcon = () => {
    switch (networkStatus) {
      case 'online':
        return <Wifi className="w-4 h-4 text-green-600" />;
      case 'offline':
        return <WifiOff className="w-4 h-4 text-red-600" />;
      case 'slow':
        return <Signal className="w-4 h-4 text-yellow-600" />;
      default:
        return <Wifi className="w-4 h-4 text-gray-600" />;
    }
  };

  if (!hasErrors()) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Sistema de Erros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Nenhum erro detectado
            </h3>
            <p className="text-gray-600">
              O sistema está funcionando normalmente.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Network Status */}
      <Alert className={networkStatus === 'online' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
        {getNetworkStatusIcon()}
        <AlertDescription className={networkStatus === 'online' ? 'text-green-800' : 'text-red-800'}>
          Status da rede: {networkStatus === 'online' ? 'Conectado' : networkStatus === 'offline' ? 'Desconectado' : 'Lento'}
        </AlertDescription>
      </Alert>

      {/* Error Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total de Erros</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Críticos</p>
                <p className="text-2xl font-bold text-red-600">{stats.criticalCount}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Não Resolvidos</p>
                <p className="text-2xl font-bold text-orange-600">{stats.unresolvedCount}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Últimos 30min</p>
                <p className="text-2xl font-bold text-blue-600">{recentErrors30min.length}</p>
              </div>
              <Clock className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Erros Ativos ({errors.length})
            </CardTitle>
            <div className="flex gap-2">
              <Button
                onClick={() => setShowHistory(!showHistory)}
                variant="outline"
                size="sm"
              >
                {showHistory ? 'Ocultar' : 'Ver'} Histórico
              </Button>
              <Button
                onClick={clearErrors}
                variant="outline"
                size="sm"
                className="text-red-600 hover:text-red-700"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Limpar Todos
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {errors.map((error) => (
              <div
                key={error.id}
                className={`p-4 rounded-lg border ${getSeverityColor(error.severity)} ${
                  error.resolved ? 'opacity-50' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <span className="text-lg">{getTypeIcon(error.type)}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium">{error.message}</h4>
                        <Badge variant="outline" className="text-xs">
                          {error.severity}
                        </Badge>
                        {error.resolved && (
                          <Badge variant="outline" className="text-xs bg-green-100 text-green-800">
                            Resolvido
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm opacity-75">
                        {new Date(error.timestamp).toLocaleString('pt-BR')}
                      </p>
                      {error.context?.url && (
                        <p className="text-xs opacity-60 mt-1">
                          URL: {error.context.url}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedError(error)}
                        >
                          Detalhes
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>Detalhes do Erro</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-medium mb-2">Informações Básicas</h4>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <span className="font-medium">ID:</span> {error.id}
                              </div>
                              <div>
                                <span className="font-medium">Tipo:</span> {error.type}
                              </div>
                              <div>
                                <span className="font-medium">Severidade:</span> {error.severity}
                              </div>
                              <div>
                                <span className="font-medium">Tentativas:</span> {error.retryCount}/{error.maxRetries}
                              </div>
                            </div>
                          </div>
                          <div>
                            <h4 className="font-medium mb-2">Mensagem</h4>
                            <p className="text-sm bg-gray-100 p-3 rounded">{error.message}</p>
                          </div>
                          {error.details && (
                            <div>
                              <h4 className="font-medium mb-2">Detalhes</h4>
                              <pre className="text-sm bg-gray-100 p-3 rounded overflow-auto">
                                {error.details}
                              </pre>
                            </div>
                          )}
                          {error.stack && (
                            <div>
                              <h4 className="font-medium mb-2">Stack Trace</h4>
                              <pre className="text-sm bg-gray-100 p-3 rounded overflow-auto max-h-40">
                                {error.stack}
                              </pre>
                            </div>
                          )}
                        </div>
                      </DialogContent>
                    </Dialog>
                    {!error.resolved && (
                      <Button
                        onClick={() => resolveError(error.id)}
                        variant="outline"
                        size="sm"
                        className="text-green-600 hover:text-green-700"
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Resolver
                      </Button>
                    )}
                    <Button
                      onClick={() => removeError(error.id)}
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Error History */}
      {showHistory && errorHistory.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Histórico de Erros ({errorHistory.length})</CardTitle>
              <Button
                onClick={() => setShowHistory(false)}
                variant="ghost"
                size="sm"
              >
                Ocultar
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-60 overflow-auto">
              {errorHistory.slice(0, 20).map((error) => (
                <div
                  key={error.id}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span>{getTypeIcon(error.type)}</span>
                    <span className="font-medium">{error.message}</span>
                    <Badge variant="outline" className="text-xs">
                      {error.severity}
                    </Badge>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(error.timestamp).toLocaleString('pt-BR')}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
