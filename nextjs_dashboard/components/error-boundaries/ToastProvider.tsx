'use client';

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { X, AlertCircle, CheckCircle, AlertTriangle, Info, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info' | 'loading';
  title: string;
  description?: string;
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  errorId?: string;
  metadata?: {
    endpoint?: string;
    status?: number;
    retryCount?: number;
  };
}

interface ToastState {
  toasts: Toast[];
  isOnline: boolean;
}

type ToastAction = 
  | { type: 'ADD_TOAST'; toast: Toast }
  | { type: 'REMOVE_TOAST'; id: string }
  | { type: 'CLEAR_ALL' }
  | { type: 'SET_ONLINE'; isOnline: boolean }
  | { type: 'UPDATE_TOAST'; id: string; updates: Partial<Toast> };

const initialState: ToastState = {
  toasts: [],
  isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true
};

function toastReducer(state: ToastState, action: ToastAction): ToastState {
  switch (action.type) {
    case 'ADD_TOAST':
      return {
        ...state,
        toasts: [...state.toasts, action.toast]
      };
    
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.id !== action.id)
      };
    
    case 'CLEAR_ALL':
      return {
        ...state,
        toasts: []
      };
    
    case 'SET_ONLINE':
      return {
        ...state,
        isOnline: action.isOnline
      };
    
    case 'UPDATE_TOAST':
      return {
        ...state,
        toasts: state.toasts.map(toast => 
          toast.id === action.id 
            ? { ...toast, ...action.updates }
            : toast
        )
      };
    
    default:
      return state;
  }
}

interface ToastContextType {
  toasts: Toast[];
  isOnline: boolean;
  addToast: (toast: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
  clearAll: () => void;
  updateToast: (id: string, updates: Partial<Toast>) => void;
  
  // Convenience methods
  showSuccess: (title: string, description?: string, options?: Partial<Toast>) => string;
  showError: (title: string, description?: string, options?: Partial<Toast>) => string;
  showWarning: (title: string, description?: string, options?: Partial<Toast>) => string;
  showInfo: (title: string, description?: string, options?: Partial<Toast>) => string;
  showLoading: (title: string, description?: string) => string;
  
  // API-specific methods
  showApiError: (error: Error, options?: { endpoint?: string; retryAction?: () => void }) => string;
  showNetworkError: (retryAction?: () => void) => string;
  showOfflineNotification: () => string;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(toastReducer, initialState);

  // Monitor online/offline status
  useEffect(() => {
    function handleOnline() {
      dispatch({ type: 'SET_ONLINE', isOnline: true });
      // Show reconnection toast
      addToast({
        type: 'success',
        title: 'Conexão Restaurada',
        description: 'Você está online novamente',
        duration: 3000
      });
    }

    function handleOffline() {
      dispatch({ type: 'SET_ONLINE', isOnline: false });
      showOfflineNotification();
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);
      
      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }
  }, []);

  // Auto-remove toasts after duration
  useEffect(() => {
    const timers: Record<string, NodeJS.Timeout> = {};

    state.toasts.forEach(toast => {
      if (!toast.persistent && toast.duration && toast.duration > 0) {
        if (timers[toast.id]) {
          clearTimeout(timers[toast.id]);
        }
        
        timers[toast.id] = setTimeout(() => {
          removeToast(toast.id);
        }, toast.duration);
      }
    });

    return () => {
      Object.values(timers).forEach(timer => clearTimeout(timer));
    };
  }, [state.toasts]);

  const generateId = (): string => {
    return `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const addToast = (toast: Omit<Toast, 'id'>): string => {
    const id = generateId();
    const newToast: Toast = {
      id,
      duration: 5000, // Default 5 seconds
      ...toast
    };

    dispatch({ type: 'ADD_TOAST', toast: newToast });
    return id;
  };

  const removeToast = (id: string) => {
    dispatch({ type: 'REMOVE_TOAST', id });
  };

  const clearAll = () => {
    dispatch({ type: 'CLEAR_ALL' });
  };

  const updateToast = (id: string, updates: Partial<Toast>) => {
    dispatch({ type: 'UPDATE_TOAST', id, updates });
  };

  // Convenience methods
  const showSuccess = (title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'success',
      title,
      description,
      duration: 4000,
      ...options
    });
  };

  const showError = (title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'error',
      title,
      description,
      duration: 6000,
      persistent: true, // Errors should be manually dismissed
      ...options
    });
  };

  const showWarning = (title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'warning',
      title,
      description,
      duration: 5000,
      ...options
    });
  };

  const showInfo = (title: string, description?: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'info',
      title,
      description,
      duration: 4000,
      ...options
    });
  };

  const showLoading = (title: string, description?: string): string => {
    return addToast({
      type: 'loading',
      title,
      description,
      persistent: true // Loading toasts should be manually removed
    });
  };

  // API-specific methods
  const showApiError = (error: Error, options?: { endpoint?: string; retryAction?: () => void }): string => {
    const { endpoint, retryAction } = options || {};
    
    return addToast({
      type: 'error',
      title: 'Erro na API',
      description: getApiErrorMessage(error, endpoint),
      persistent: true,
      action: retryAction ? {
        label: 'Tentar Novamente',
        onClick: retryAction
      } : undefined,
      metadata: {
        endpoint,
        status: (error as any).status
      }
    });
  };

  const showNetworkError = (retryAction?: () => void): string => {
    return addToast({
      type: 'error',
      title: 'Erro de Conexão',
      description: 'Verifique sua conexão com a internet',
      persistent: true,
      action: retryAction ? {
        label: 'Tentar Novamente',
        onClick: retryAction
      } : undefined
    });
  };

  const showOfflineNotification = (): string => {
    return addToast({
      type: 'warning',
      title: 'Modo Offline',
      description: 'Algumas funcionalidades podem não estar disponíveis',
      persistent: true
    });
  };

  const contextValue: ToastContextType = {
    toasts: state.toasts,
    isOnline: state.isOnline,
    addToast,
    removeToast,
    clearAll,
    updateToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading,
    showApiError,
    showNetworkError,
    showOfflineNotification
  };

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

function ToastContainer() {
  const { toasts, removeToast, isOnline } = useToast();

  return (
    <div className="fixed top-0 right-0 z-50 p-4 space-y-4 pointer-events-none max-w-sm w-full">
      {/* Online/Offline Indicator */}
      <div className="flex justify-end">
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium pointer-events-auto ${
          isOnline 
            ? 'bg-green-100 text-green-800 border border-green-200' 
            : 'bg-red-100 text-red-800 border border-red-200'
        }`}>
          {isOnline ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          {isOnline ? 'Online' : 'Offline'}
        </div>
      </div>

      {/* Toast Messages */}
      {toasts.map(toast => (
        <ToastItem 
          key={toast.id} 
          toast={toast} 
          onRemove={() => removeToast(toast.id)} 
        />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />;
      case 'loading':
        return <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStyles = () => {
    switch (toast.type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-amber-50 border-amber-200 text-amber-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'loading':
        return 'bg-gray-50 border-gray-200 text-gray-800';
      default:
        return 'bg-white border-gray-200 text-gray-800';
    }
  };

  return (
    <div className={`
      pointer-events-auto
      max-w-sm w-full
      border rounded-lg shadow-lg
      p-4
      transform transition-all duration-300 ease-in-out
      animate-in slide-in-from-right-full
      ${getStyles()}
    `}>
      <div className="flex items-start">
        <div className="flex-shrink-0 mr-3">
          {getIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm">
            {toast.title}
          </p>
          {toast.description && (
            <p className="text-sm opacity-90 mt-1">
              {toast.description}
            </p>
          )}
          
          {/* Error ID for debugging */}
          {toast.errorId && (
            <p className="text-xs opacity-75 mt-2 font-mono">
              ID: {toast.errorId}
            </p>
          )}
          
          {/* Metadata */}
          {toast.metadata && (
            <div className="text-xs opacity-75 mt-2 space-y-1">
              {toast.metadata.endpoint && (
                <div>Endpoint: {toast.metadata.endpoint}</div>
              )}
              {toast.metadata.status && (
                <div>Status: {toast.metadata.status}</div>
              )}
              {toast.metadata.retryCount !== undefined && (
                <div>Tentativas: {toast.metadata.retryCount}</div>
              )}
            </div>
          )}
          
          {/* Action Button */}
          {toast.action && (
            <Button
              size="sm"
              variant="outline"
              className="mt-2 h-7 text-xs"
              onClick={toast.action.onClick}
            >
              {toast.action.label}
            </Button>
          )}
        </div>

        <Button
          size="sm"
          variant="ghost"
          className="ml-2 h-6 w-6 p-0 opacity-70 hover:opacity-100"
          onClick={onRemove}
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
    </div>
  );
}

// Helper function to get user-friendly API error messages
function getApiErrorMessage(error: Error, endpoint?: string): string {
  const apiError = error as any;
  
  if (apiError.status) {
    switch (apiError.status) {
      case 400:
        return 'Dados inválidos enviados ao servidor.';
      case 401:
        return 'Sessão expirada. Faça login novamente.';
      case 403:
        return 'Você não tem permissão para esta ação.';
      case 404:
        return `Recurso não encontrado${endpoint ? ` em ${endpoint}` : ''}.`;
      case 429:
        return 'Muitas tentativas. Aguarde um momento.';
      case 500:
        return 'Erro interno do servidor.';
      case 502:
      case 503:
      case 504:
        return 'Servidor temporariamente indisponível.';
      default:
        return `Erro ${apiError.status}: ${apiError.statusText || 'Erro desconhecido'}`;
    }
  }
  
  if (error.message.includes('fetch')) {
    return 'Problema de conexão com o servidor.';
  }
  
  if (error.message.includes('timeout')) {
    return 'Tempo limite esgotado.';
  }
  
  return error.message || 'Erro desconhecido na API.';
}
