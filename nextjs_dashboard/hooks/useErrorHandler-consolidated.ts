/**
 * 🚀 HOOK ERROR HANDLER CONSOLIDADO - FASE 2 REFATORAÇÃO
 * ======================================================
 * 
 * Hook unificado que consolida diferentes padrões de error handling:
 * - useAdvancedApi.ts (error handling complexo com retry)
 * - use-async-state.ts (error states simples)
 * - useFormValidation.ts (validação de erros)
 * - use-real-analytics.ts (error handling com toast)
 * - useWebSocketRobust.ts (error handling WebSocket)
 * - useAppointmentOperations.ts (error handling mutations)
 * - useAuth.ts (error handling autenticação)
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { toast } from 'sonner';

// Tipos para diferentes tipos de erro
export interface ApiError extends Error {
  status?: number;
  endpoint?: string;
  data?: any;
  isRetryable?: boolean;
  isNetworkError?: boolean;
  isTimeoutError?: boolean;
}

export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

export interface NetworkError extends Error {
  isOffline?: boolean;
  isSlowConnection?: boolean;
  retryCount?: number;
}

// Estados de erro consolidados
export interface ErrorState {
  // Estados básicos
  error: Error | null;
  hasError: boolean;
  isLoading: boolean;
  
  // Estados específicos
  apiError: ApiError | null;
  validationErrors: ValidationError[];
  networkError: NetworkError | null;
  
  // Estados de retry
  retryCount: number;
  maxRetries: number;
  canRetry: boolean;
  
  // Estados de UI
  showToast: boolean;
  showErrorBoundary: boolean;
  isRecovering: boolean;
}

// Opções para error handling
export interface ErrorHandlerOptions {
  // Configurações básicas
  showToast?: boolean;
  showErrorBoundary?: boolean;
  autoRetry?: boolean;
  maxRetries?: number;
  retryDelay?: number;
  
  // Callbacks
  onError?: (error: Error) => void;
  onRetry?: (error: Error, attempt: number) => void;
  onRecovery?: () => void;
  
  // Configurações de toast
  toastDuration?: number;
  toastPosition?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  
  // Configurações de validação
  validateImmediately?: boolean;
  debounceValidation?: number;
}

// Hook principal consolidado
export function useErrorHandler(options: ErrorHandlerOptions = {}) {
  const {
    showToast = true,
    showErrorBoundary = false,
    autoRetry = false,
    maxRetries = 3,
    retryDelay = 1000,
    onError,
    onRetry,
    onRecovery,
    toastDuration = 5000,
    toastPosition = 'top-right',
    validateImmediately = false,
    debounceValidation = 300
  } = options;

  const [errorState, setErrorState] = useState<ErrorState>({
    error: null,
    hasError: false,
    isLoading: false,
    apiError: null,
    validationErrors: [],
    networkError: null,
    retryCount: 0,
    maxRetries,
    canRetry: false,
    showToast,
    showErrorBoundary,
    isRecovering: false
  });

  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const validationTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }
    };
  }, []);

  // Função para criar diferentes tipos de erro
  const createError = useCallback((error: any, type: 'api' | 'validation' | 'network' = 'api'): Error => {
    if (type === 'api') {
      const apiError: ApiError = error instanceof Error ? error : new Error(error?.message || 'API Error');
      apiError.status = error?.status || error?.response?.status;
      apiError.endpoint = error?.endpoint || error?.config?.url;
      apiError.data = error?.data || error?.response?.data;
      apiError.isRetryable = !apiError.status || apiError.status >= 500 || apiError.status === 408 || apiError.status === 429;
      apiError.isNetworkError = error?.code === 'NETWORK_ERROR' || error?.message === 'Network Error';
      apiError.isTimeoutError = error?.code === 'TIMEOUT' || error?.message === 'Request timed out';
      return apiError;
    }

    if (type === 'validation') {
      const validationError = error instanceof Error ? error : new Error(error?.message || 'Validation Error');
      return validationError;
    }

    if (type === 'network') {
      const networkError: NetworkError = error instanceof Error ? error : new Error(error?.message || 'Network Error');
      networkError.isOffline = !navigator.onLine;
      networkError.isSlowConnection = false; // TODO: Implementar detecção de conexão lenta
      networkError.retryCount = 0;
      return networkError;
    }

    return error instanceof Error ? error : new Error(String(error));
  }, []);

  // Função para processar erros
  const handleError = useCallback((error: any, context?: string) => {
    const processedError = createError(error);
    const canRetry = autoRetry && errorState.retryCount < maxRetries;

    setErrorState(prev => ({
      ...prev,
      error: processedError,
      hasError: true,
      isLoading: false,
      canRetry,
      isRecovering: false,
      // Determinar tipo de erro específico
      apiError: processedError instanceof Error && 'status' in processedError ? processedError as ApiError : null,
      networkError: processedError instanceof Error && 'isOffline' in processedError ? processedError as NetworkError : null
    }));

    // Mostrar toast se habilitado
    if (showToast) {
      const message = context ? `Erro em ${context}: ${processedError.message}` : processedError.message;
      toast.error(message, {
        duration: toastDuration,
        position: toastPosition
      });
    }

    // Chamar callback de erro
    if (onError) {
      onError(processedError);
    }

    // Lançar erro para error boundary se habilitado
    if (showErrorBoundary) {
      throw processedError;
    }

    return processedError;
  }, [createError, autoRetry, errorState.retryCount, maxRetries, showToast, toastDuration, toastPosition, onError, showErrorBoundary]);

  // Função para processar erros de validação
  const handleValidationErrors = useCallback((errors: ValidationError[] | Record<string, string>) => {
    const validationErrors: ValidationError[] = Array.isArray(errors) 
      ? errors 
      : Object.entries(errors).map(([field, message]) => ({ field, message }));

    setErrorState(prev => ({
      ...prev,
      validationErrors,
      hasError: validationErrors.length > 0
    }));

    // Mostrar toast para erros de validação
    if (showToast && validationErrors.length > 0) {
      toast.error(`Erro de validação: ${validationErrors[0].message}`, {
        duration: toastDuration,
        position: toastPosition
      });
    }
  }, [showToast, toastDuration, toastPosition]);

  // Função para retry
  const retry = useCallback(async (retryFn: () => Promise<any>) => {
    if (!errorState.canRetry || errorState.retryCount >= maxRetries) {
      return false;
    }

    setErrorState(prev => ({
      ...prev,
      isRecovering: true,
      retryCount: prev.retryCount + 1
    }));

    // Delay antes do retry
    await new Promise(resolve => {
      retryTimeoutRef.current = setTimeout(resolve, retryDelay * Math.pow(2, errorState.retryCount));
    });

    try {
      await retryFn();
      
      // Sucesso - limpar erros
      clearError();
      
      if (onRecovery) {
        onRecovery();
      }
      
      return true;
    } catch (error) {
      // Falha no retry
      handleError(error, `Retry ${errorState.retryCount + 1}`);
      
      if (onRetry) {
        onRetry(error instanceof Error ? error : new Error(String(error)), errorState.retryCount + 1);
      }
      
      return false;
    }
  }, [errorState.canRetry, errorState.retryCount, maxRetries, retryDelay, onRecovery, onRetry, handleError]);

  // Função para limpar erros
  const clearError = useCallback(() => {
    setErrorState(prev => ({
      ...prev,
      error: null,
      hasError: false,
      apiError: null,
      validationErrors: [],
      networkError: null,
      retryCount: 0,
      canRetry: false,
      isRecovering: false
    }));
  }, []);

  // Função para definir loading state
  const setLoading = useCallback((loading: boolean) => {
    setErrorState(prev => ({
      ...prev,
      isLoading: loading,
      error: loading ? null : prev.error // Limpar erro ao começar loading
    }));
  }, []);

  // Função para executar operação com error handling automático
  const executeWithErrorHandling = useCallback(async <T>(
    operation: () => Promise<T>,
    context?: string
  ): Promise<T | null> => {
    setLoading(true);
    
    try {
      const result = await operation();
      clearError();
      return result;
    } catch (error) {
      handleError(error, context);
      return null;
    } finally {
      setLoading(false);
    }
  }, [setLoading, clearError, handleError]);

  // Função para validação com debounce
  const validateWithDebounce = useCallback((
    validateFn: () => ValidationError[] | Record<string, string>,
    debounceMs: number = debounceValidation
  ) => {
    if (validationTimeoutRef.current) {
      clearTimeout(validationTimeoutRef.current);
    }

    validationTimeoutRef.current = setTimeout(() => {
      const errors = validateFn();
      handleValidationErrors(errors);
    }, debounceMs);
  }, [debounceValidation, handleValidationErrors]);

  return {
    // Estados
    ...errorState,
    
    // Ações
    handleError,
    handleValidationErrors,
    retry,
    clearError,
    setLoading,
    executeWithErrorHandling,
    validateWithDebounce,
    
    // Utilitários
    hasValidationErrors: errorState.validationErrors.length > 0,
    hasApiError: !!errorState.apiError,
    hasNetworkError: !!errorState.networkError,
    isRetryable: errorState.canRetry && errorState.retryCount < maxRetries,
    
    // Helpers para tipos específicos
    getApiError: () => errorState.apiError,
    getValidationError: (field: string) => errorState.validationErrors.find(e => e.field === field),
    getAllValidationErrors: () => errorState.validationErrors,
    getNetworkError: () => errorState.networkError
  };
}

// Hook simplificado para casos básicos
export function useSimpleErrorHandler() {
  return useErrorHandler({
    showToast: true,
    autoRetry: false,
    showErrorBoundary: false
  });
}

// Hook para validação de formulários
export function useFormErrorHandler() {
  const errorHandler = useErrorHandler({
    showToast: false, // Formulários geralmente mostram erros inline
    autoRetry: false,
    showErrorBoundary: false,
    validateImmediately: true,
    debounceValidation: 300
  });

  return {
    ...errorHandler,
    // Métodos específicos para formulários
    validateField: (field: string, value: any, validator: (value: any) => string | null) => {
      const error = validator(value);
      if (error) {
        errorHandler.handleValidationErrors([{ field, message: error }]);
        return false;
      }
      return true;
    },
    clearFieldError: (field: string) => {
      const remainingErrors = errorHandler.validationErrors.filter((e: ValidationError) => e.field !== field);
      errorHandler.handleValidationErrors(remainingErrors);
    }
  };
}

// Hook para operações de API
export function useApiErrorHandler() {
  return useErrorHandler({
    showToast: true,
    autoRetry: true,
    maxRetries: 3,
    retryDelay: 1000,
    showErrorBoundary: false
  });
}
