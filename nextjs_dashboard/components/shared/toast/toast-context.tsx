/**
 * 🚀 TOAST CONTEXT - FASE 3 REFATORAÇÃO
 * =====================================
 * 
 * Context e Provider para o sistema de toast refatorado.
 * Extraído do AdvancedToastProvider para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React, { createContext, useContext, useReducer, useCallback, ReactNode, useEffect } from 'react';
import { ToastContextType, Toast } from './types';
import { toastReducer, initialState } from './toast-reducer';

const ToastContext = createContext<ToastContextType | undefined>(undefined);

interface ToastProviderProps {
  children: ReactNode;
}

export function ToastProvider({ children }: ToastProviderProps) {
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
  const apiError = useCallback((message: string, options?: Partial<Toast>): string => {
    return addToast({
      type: 'error',
      title: 'API Error',
      description: message,
      priority: 'high',
      duration: 8000,
      category: 'api',
      ...options
    });
  }, [addToast]);

  const networkError = useCallback((message?: string): string => {
    return addToast({
      type: 'network',
      title: 'Network Error',
      description: message || 'Connection failed. Please check your internet connection.',
      priority: 'high',
      duration: 8000,
      category: 'network',
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
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextType {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
