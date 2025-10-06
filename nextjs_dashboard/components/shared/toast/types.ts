/**
 * 🚀 TOAST TYPES - FASE 3 REFATORAÇÃO
 * ===================================
 * 
 * Tipos centralizados para o sistema de toast refatorado.
 * Extraído do AdvancedToastProvider para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

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

export interface ToastState {
  toasts: Toast[];
  maxToasts: number;
  globalPause: boolean;
  defaultDuration: number;
}

export interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id' | 'timestamp'>) => string;
  removeToast: (id: string) => void;
  updateToast: (id: string, updates: Partial<Toast>) => void;
  clearAll: () => void;
  clearByType: (type: Toast['type']) => void;
  clearByCategory: (category: string) => void;
  success: (title: string, description?: string, options?: Partial<Toast>) => string;
  error: (title: string, description?: string, options?: Partial<Toast>) => string;
  warning: (title: string, description?: string, options?: Partial<Toast>) => string;
  info: (title: string, description?: string, options?: Partial<Toast>) => string;
  loading: (title: string, description?: string, options?: Partial<Toast>) => string;
  apiError: (message: string, options?: Partial<Toast>) => string;
  networkError: (message?: string) => string;
  retryableError: (title: string, onRetry: () => void, maxRetries?: number) => string;
  progressToast: (title: string, initialProgress: number) => string;
  updateProgress: (id: string, progress: number) => void;
  pauseAll: () => void;
  resumeAll: () => void;
}

export interface AppError {
  id: string;
  type: 'network' | 'api' | 'validation' | 'auth' | 'permission' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details: string;
  stack?: string;
  timestamp: string;
  context: {
    level: 'component' | 'page' | 'app';
    context?: string;
    retryCount: number;
    componentStack?: string;
    errorBoundary?: string;
    url: string;
  };
  retryCount: number;
  maxRetries: number;
}
