/**
 * 🚀 ERROR BOUNDARY TYPES - FASE 3 REFATORAÇÃO
 * ============================================
 * 
 * Tipos para o sistema de error boundary refatorado.
 * Extraído do AdvancedErrorBoundary para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  level?: 'page' | 'section' | 'component';
  context?: string;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  retryAttempts?: number;
  isolateErrors?: boolean;
  showErrorDetails?: boolean;
  allowReset?: boolean;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRetrying: boolean;
  errorHistory: Array<{
    error: Error;
    timestamp: number;
    stack?: string;
  }>;
}

export interface ErrorDetails {
  message: string;
  stack?: string;
  componentStack?: string;
  errorId: string;
  timestamp: string;
  context: string;
  level: string;
  retryCount: number;
}

export interface ErrorActions {
  onRetry: () => void;
  onReset: () => void;
  onReport: () => void;
  onGoHome: () => void;
  onGoBack: () => void;
}

export interface ErrorFallbackProps {
  error: Error;
  errorInfo?: React.ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRetrying: boolean;
  showErrorDetails: boolean;
  actions: ErrorActions;
  level: 'page' | 'section' | 'component';
  context?: string;
}
