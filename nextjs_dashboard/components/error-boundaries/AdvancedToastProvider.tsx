'use client';

import React, { createContext, useContext, useReducer, useCallback, ReactNode, useEffect } from 'react';
import { X, AlertCircle, CheckCircle, AlertTriangle, Info, Wifi, WifiOff, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info' | 'loading' | 'network';
  title: string;
  description?: string;
  duration?: number;
  persistent?: boolean;
  dismissible?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  retry?: {
    onRetry: () => void;
    retryCount: number;
    maxRetries: number;
  };
  timestamp: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  priority?: 'low' | 'medium' | 'high' | 'critical';
  category?: string;
  metadata?: Record<string, any>;
}

interface ToastState {
  toasts: Toast[];
  maxToasts: number;
  defaultDuration: number;
  globalPause: boolean;
}

type ToastAction =
  | { type: 'ADD_TOAST'; toast: Toast }
  | { type: 'REMOVE_TOAST'; id: string }
  | { type: 'UPDATE_TOAST'; id: string; updates: Partial<Toast> }
  | { type: 'CLEAR_ALL' }
  | { type: 'CLEAR_BY_TYPE'; toastType: Toast['type'] }
  | { type: 'CLEAR_BY_CATEGORY'; category: string }
  | { type: 'SET_GLOBAL_PAUSE'; paused: boolean }
  | { type: 'INCREMENT_RETRY'; id: string };

const initialState: ToastState = {
  toasts: [],
  maxToasts: 5,
  defaultDuration: 5000,
  globalPause: false
};

function toastReducer(state: ToastState, action: ToastAction): ToastState {
  switch (action.type) {
    case 'ADD_TOAST': {
      const newToast = action.toast;

      // Remove oldest toast if at max capacity
      let toasts = [...state.toasts];
      if (toasts.length >= state.maxToasts) {
        // Remove non-persistent toasts first, then oldest
        const nonPersistent = toasts.filter(t => !t.persistent);
        if (nonPersistent.length > 0) {
          const oldestNonPersistent = nonPersistent.reduce((oldest, current) =>
            oldest.timestamp < current.timestamp ? oldest : current
          );
          toasts = toasts.filter(t => t.id !== oldestNonPersistent.id);
        } else {
          toasts = toasts.slice(1); // Remove oldest
        }
      }

      // Insert toast in priority order
      const insertIndex = toasts.findIndex(toast => {
        const priorities = { low: 0, medium: 1, high: 2, critical: 3 };
        const newPriority = priorities[newToast.priority || 'medium'];
        const existingPriority = priorities[toast.priority || 'medium'];
        return newPriority > existingPriority;
      });

      if (insertIndex === -1) {
        toasts.push(newToast);
      } else {
        toasts.splice(insertIndex, 0, newToast);
      }

      return { ...state, toasts };
    }

    case 'REMOVE_TOAST': {
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.id !== action.id)
      };
    }

    case 'UPDATE_TOAST': {
      return {
        ...state,
        toasts: state.toasts.map(toast =>
          toast.id === action.id ? { ...toast, ...action.updates } : toast
        )
      };
    }

    case 'CLEAR_ALL': {
      return { ...state, toasts: [] };
    }

    case 'CLEAR_BY_TYPE': {
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.type !== action.toastType)
      };
    }

    case 'CLEAR_BY_CATEGORY': {
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.category !== action.category)
      };
    }

    case 'SET_GLOBAL_PAUSE': {
      return { ...state, globalPause: action.paused };
    }

    case 'INCREMENT_RETRY': {
      return {
        ...state,
        toasts: state.toasts.map(toast =>
          toast.id === action.id && toast.retry
            ? {
                ...toast,
                retry: {
                  ...toast.retry,
                  retryCount: toast.retry.retryCount + 1
                }
              }
            : toast
        )
      };
    }

    default:
      return state;
  }
}

interface ToastContextType {
  // State
  toasts: Toast[];

  // Core actions
  addToast: (toast: Omit<Toast, 'id' | 'timestamp'>) => string;
  removeToast: (id: string) => void;
  updateToast: (id: string, updates: Partial<Toast>) => void;
  clearAll: () => void;
  clearByType: (type: Toast['type']) => void;
  clearByCategory: (category: string) => void;

  // Convenience methods
  success: (title: string, description?: string, options?: Partial<Toast>) => string;
  error: (title: string, description?: string, options?: Partial<Toast>) => string;
  warning: (title: string, description?: string, options?: Partial<Toast>) => string;
  info: (title: string, description?: string, options?: Partial<Toast>) => string;
  loading: (title: string, description?: string, options?: Partial<Toast>) => string;

  // API-specific methods
  apiError: (endpoint: string, status?: number, message?: string) => string;
  networkError: (message?: string) => string;

  // Advanced features
  retryableError: (title: string, onRetry: () => void, maxRetries?: number) => string;
  progressToast: (title: string, initialProgress: number) => string;
  updateProgress: (id: string, progress: number) => void;

  // Control
  pauseAll: () => void;
  resumeAll: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function AdvancedToastProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(toastReducer, initialState);

  // Auto-remove toasts after their duration
  useEffect(() => {
    const timers: { [id: string]: NodeJS.Timeout } = {};

    state.toasts.forEach(toast => {
      if (!toast.persistent && !state.globalPause && toast.duration !== 0) {
        const duration = toast.duration || state.defaultDuration;

        timers[toast.id] = setTimeout(() => {
          dispatch({ type: 'REMOVE_TOAST', id: toast.id });
        }, duration);
      }
    });

    return () => {
      Object.values(timers).forEach(timer => clearTimeout(timer));
    };
  }, [state.toasts, state.globalPause, state.defaultDuration]);

  const generateId = (): string => {
    return `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const addToast = useCallback((toast: Omit<Toast, 'id' | 'timestamp'>): string => {
    const id = generateId();
    const fullToast: Toast = {
      id,
      timestamp: Date.now(),
      position: 'top-right',
      priority: 'medium',
      dismissible: true,
      duration: state.defaultDuration,
      ...toast
    };

    dispatch({ type: 'ADD_TOAST', toast: fullToast });
    return id;
  }, [state.defaultDuration]);

  const removeToast = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_TOAST', id });
  }, []);

  const updateToast = useCallback((id: string, updates: Partial<Toast>) => {
    dispatch({ type: 'UPDATE_TOAST', id, updates });
  }, []);

  const clearAll = useCallback(() => {
    dispatch({ type: 'CLEAR_ALL' });
  }, []);

  const clearByType = useCallback((type: Toast['type']) => {
    dispatch({ type: 'CLEAR_BY_TYPE', toastType: type });
  }, []);

  const clearByCategory = useCallback((category: string) => {
    dispatch({ type: 'CLEAR_BY_CATEGORY', category });
  }, []);

  const pauseAll = useCallback(() => {
    dispatch({ type: 'SET_GLOBAL_PAUSE', paused: true });
  }, []);

  const resumeAll = useCallback(() => {
    dispatch({ type: 'SET_GLOBAL_PAUSE', paused: false });
  }, []);

  // Convenience methods
  const success = useCallback((title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'success',
      title,
      description,
      duration: 4000,
      ...options
    });
  }, [addToast]);

  const error = useCallback((title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'error',
      title,
      description,
      priority: 'high',
      duration: 8000,
      ...options
    });
  }, [addToast]);

  const warning = useCallback((title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'warning',
      title,
      description,
      priority: 'medium',
      duration: 6000,
      ...options
    });
  }, [addToast]);

  const info = useCallback((title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'info',
      title,
      description,
      duration: 5000,
      ...options
    });
  }, [addToast]);

  const loading = useCallback((title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'loading',
      title,
      description,
      persistent: true,
      dismissible: false,
      ...options
    });
  }, [addToast]);

  // API-specific methods
  const apiError = useCallback((endpoint: string, status?: number, message?: string): string => {
    let title = 'Erro na API';
    let description = `Falha ao acessar ${endpoint}`;
    let priority: Toast['priority'] = 'medium';

    if (status) {
      if (status >= 500) {
        title = 'Erro do Servidor';
        description = `Servidor indisponível (${status}). Tente novamente em alguns instantes.`;
        priority = 'high';
      } else if (status === 401) {
        title = 'Não Autorizado';
        description = 'Sua sessão pode ter expirado. Faça login novamente.';
        priority = 'critical';
      } else if (status === 403) {
        title = 'Acesso Negado';
        description = 'Você não tem permissão para esta operação.';
        priority = 'high';
      } else if (status === 404) {
        title = 'Recurso Não Encontrado';
        description = `O recurso ${endpoint} não foi encontrado.`;
        priority = 'medium';
      } else if (status >= 400) {
        title = 'Erro na Solicitação';
        description = message || `Erro ${status}: Verifique os dados enviados.`;
        priority = 'medium';
      }
    }

    if (message) {
      description = `${description} - ${message}`;
    }

    return addToast({
      type: 'error',
      title,
      description,
      priority,
      category: 'api',
      metadata: { endpoint, status },
      duration: 8000
    });
  }, [addToast]);

  const networkError = useCallback((message?: string): string => {
    return addToast({
      type: 'network',
      title: 'Problema de Conexão',
      description: message || 'Verifique sua conexão com a internet e tente novamente.',
      priority: 'high',
      category: 'network',
      duration: 10000,
      retry: {
        onRetry: () => window.location.reload(),
        retryCount: 0,
        maxRetries: 3
      }
    });
  }, [addToast]);

  // Advanced features
  const retryableError = useCallback((title: string, onRetry: () => void, maxRetries = 3): string => {
    return addToast({
      type: 'error',
      title,
      priority: 'medium',
      persistent: true,
      retry: {
        onRetry,
        retryCount: 0,
        maxRetries
      }
    });
  }, [addToast]);

  const progressToast = useCallback((title: string, initialProgress: number): string => {
    return addToast({
      type: 'loading',
      title,
      persistent: true,
      dismissible: false,
      metadata: { progress: initialProgress }
    });
  }, [addToast]);

  const updateProgress = useCallback((id: string, progress: number) => {
    updateToast(id, {
      metadata: { progress },
      ...(progress >= 100 && {
        type: 'success',
        persistent: false,
        dismissible: true,
        duration: 3000
      })
    });
  }, [updateToast]);

  const contextValue: ToastContextType = {
    toasts: state.toasts,
    addToast,
    removeToast,
    updateToast,
    clearAll,
    clearByType,
    clearByCategory,
    success,
    error,
    warning,
    info,
    loading,
    apiError,
    networkError,
    retryableError,
    progressToast,
    updateProgress,
    pauseAll,
    resumeAll
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
}

// Toast Container Component
function ToastContainer() {
  const { toasts } = useToast();

  // Group toasts by position
  const toastsByPosition = toasts.reduce((acc, toast) => {
    const position = toast.position || 'top-right';
    if (!acc[position]) acc[position] = [];
    acc[position].push(toast);
    return acc;
  }, {} as Record<string, Toast[]>);

  return (
    <>
      {Object.entries(toastsByPosition).map(([position, positionToasts]) => (
        <div
          key={position}
          className={`fixed z-50 p-4 space-y-2 max-w-sm ${getPositionClasses(position)}`}
        >
          {positionToasts.map(toast => (
            <ToastComponent key={toast.id} toast={toast} />
          ))}
        </div>
      ))}
    </>
  );
}

// Individual Toast Component
function ToastComponent({ toast }: { toast: Toast }) {
  const { removeToast, updateToast } = useToast();
  const [isVisible, setIsVisible] = React.useState(false);
  const [progress, setProgress] = React.useState(0);

  // Entrance animation
  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 50);
    return () => clearTimeout(timer);
  }, []);

  // Progress bar for loading toasts
  useEffect(() => {
    if (toast.type === 'loading' && toast.metadata?.progress !== undefined) {
      setProgress(toast.metadata.progress);
    }
  }, [toast.metadata?.progress, toast.type]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => removeToast(toast.id), 200);
  };

  const handleRetry = () => {
    if (toast.retry) {
      updateToast(toast.id, {
        retry: {
          ...toast.retry,
          retryCount: toast.retry.retryCount + 1
        }
      });
      toast.retry.onRetry();
    }
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
      case 'loading':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'network':
        return navigator.onLine ?
          <Wifi className="h-5 w-5 text-orange-500" /> :
          <WifiOff className="h-5 w-5 text-red-500" />;
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getBorderColor = () => {
    switch (toast.type) {
      case 'success': return 'border-green-200';
      case 'error': return 'border-red-200';
      case 'warning': return 'border-yellow-200';
      case 'info': return 'border-blue-200';
      case 'loading': return 'border-blue-200';
      case 'network': return 'border-orange-200';
      default: return 'border-gray-200';
    }
  };

  return (
    <div
      className={`
        toast-container transition-all duration-200 transform
        ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
      `}
    >
      <Alert className={`relative shadow-lg border-l-4 ${getBorderColor()}`}>
        {/* Progress bar for loading toasts */}
        {toast.type === 'loading' && toast.metadata?.progress !== undefined && (
          <div className="absolute top-0 left-0 right-0 h-1 bg-muted rounded-t overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <div className="flex items-start space-x-3">
          {getIcon()}

          <div className="flex-1 space-y-1">
            <div className="flex items-center justify-between">
              <AlertTitle className="text-sm font-medium">
                {toast.title}
                {toast.priority && toast.priority !== 'medium' && (
                  <Badge
                    variant={toast.priority === 'critical' ? 'destructive' : 'secondary'}
                    className="ml-2 text-xs"
                  >
                    {toast.priority}
                  </Badge>
                )}
              </AlertTitle>

              {toast.dismissible && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={handleClose}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>

            {toast.description && (
              <AlertDescription className="text-sm">
                {toast.description}
              </AlertDescription>
            )}

            {/* Progress text for loading toasts */}
            {toast.type === 'loading' && toast.metadata?.progress !== undefined && (
              <div className="text-xs text-muted-foreground">
                Progresso: {Math.round(progress)}%
              </div>
            )}

            {/* Actions */}
            {(toast.action || toast.retry) && (
              <div className="flex space-x-2 mt-2">
                {toast.action && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      toast.action!.onClick();
                      handleClose();
                    }}
                  >
                    {toast.action.label}
                  </Button>
                )}

                {toast.retry && toast.retry.retryCount < toast.retry.maxRetries && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleRetry}
                  >
                    Tentar Novamente ({toast.retry.retryCount + 1}/{toast.retry.maxRetries})
                  </Button>
                )}
              </div>
            )}

            {/* Timestamp for development */}
            {typeof window !== 'undefined' && window.location.hostname === 'localhost' && (
              <div className="text-xs text-muted-foreground">
                {new Date(toast.timestamp).toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      </Alert>
    </div>
  );
}

// Position utility
function getPositionClasses(position: string): string {
  switch (position) {
    case 'top-left':
      return 'top-4 left-4';
    case 'top-right':
      return 'top-4 right-4';
    case 'top-center':
      return 'top-4 left-1/2 transform -translate-x-1/2';
    case 'bottom-left':
      return 'bottom-4 left-4';
    case 'bottom-right':
      return 'bottom-4 right-4';
    case 'bottom-center':
      return 'bottom-4 left-1/2 transform -translate-x-1/2';
    default:
      return 'top-4 right-4';
  }
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within an AdvancedToastProvider');
  }
  return context;
}

export default AdvancedToastProvider;
