'use client';

import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';

export interface AppError {
  id: string;
  type: 'api' | 'network' | 'validation' | 'auth' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details?: string;
  stack?: string;
  timestamp: string;
  endpoint?: string;
  status?: number;
  userAgent?: string;
  userId?: string;
  sessionId?: string;
  context?: Record<string, any>;
  resolved?: boolean;
  retryCount?: number;
  maxRetries?: number;
}

interface ErrorState {
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
}

type ErrorAction = 
  | { type: 'ADD_ERROR'; error: AppError }
  | { type: 'REMOVE_ERROR'; id: string }
  | { type: 'RESOLVE_ERROR'; id: string }
  | { type: 'CLEAR_ERRORS' }
  | { type: 'SET_GLOBAL_ERROR'; error: AppError | null }
  | { type: 'SET_NETWORK_STATUS'; status: 'online' | 'offline' | 'slow' }
  | { type: 'INCREMENT_RETRY'; id: string };

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
  }
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
        // Set as global error if critical
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
        globalError: state.globalError?.id === action.id ? null : state.globalError
      };
    }

    case 'RESOLVE_ERROR': {
      return {
        ...state,
        errors: state.errors.map(error =>
          error.id === action.id 
            ? { ...error, resolved: true }
            : error
        ),
        globalError: state.globalError?.id === action.id 
          ? { ...state.globalError, resolved: true }
          : state.globalError
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
        }
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
            ? { ...error, retryCount: (error.retryCount || 0) + 1 }
            : error
        ),
        globalError: state.globalError?.id === action.id 
          ? { ...state.globalError, retryCount: (state.globalError.retryCount || 0) + 1 }
          : state.globalError
      };
    }

    default:
      return state;
  }
}

interface ErrorContextType {
  // State
  errors: AppError[];
  globalError: AppError | null;
  networkStatus: 'online' | 'offline' | 'slow';
  errorCounts: ErrorState['errorCounts'];
  
  // Actions
  addError: (error: Omit<AppError, 'id' | 'timestamp'>) => string;
  removeError: (id: string) => void;
  resolveError: (id: string) => void;
  clearErrors: () => void;
  setGlobalError: (error: AppError | null) => void;
  incrementRetry: (id: string) => void;

  // Convenience methods
  addApiError: (message: string, details?: { endpoint?: string; status?: number; context?: any }) => string;
  addNetworkError: (message: string) => string;
  addValidationError: (message: string, context?: any) => string;
  addAuthError: (message: string) => string;
  
  // Helpers
  hasErrors: () => boolean;
  hasCriticalErrors: () => boolean;
  getErrorsByType: (type: AppError['type']) => AppError[];
  getRecentErrors: (minutes?: number) => AppError[];
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export function ErrorProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(errorReducer, initialState);

  // Monitor network status
  React.useEffect(() => {
    const handleOnline = () => {
      dispatch({ type: 'SET_NETWORK_STATUS', status: 'online' });
    };

    const handleOffline = () => {
      dispatch({ type: 'SET_NETWORK_STATUS', status: 'offline' });
    };

    // Detect slow connection
    const handleConnectionChange = () => {
      const connection = (navigator as any).connection;
      if (connection && connection.effectiveType) {
        if (['slow-2g', '2g'].includes(connection.effectiveType)) {
          dispatch({ type: 'SET_NETWORK_STATUS', status: 'slow' });
        } else {
          dispatch({ type: 'SET_NETWORK_STATUS', status: 'online' });
        }
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);
      
      // Check initial status
      if (!navigator.onLine) {
        dispatch({ type: 'SET_NETWORK_STATUS', status: 'offline' });
      }

      // Monitor connection quality if available
      const connection = (navigator as any).connection;
      if (connection) {
        connection.addEventListener('change', handleConnectionChange);
        handleConnectionChange(); // Check initial connection
      }

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
        if (connection) {
          connection.removeEventListener('change', handleConnectionChange);
        }
      };
    }
  }, []);

  const generateId = (): string => {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const addError = useCallback((error: Omit<AppError, 'id' | 'timestamp'>): string => {
    const id = generateId();
    const fullError: AppError = {
      id,
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'SSR',
      userId: typeof localStorage !== 'undefined' ? localStorage.getItem('userId') || undefined : undefined,
      sessionId: typeof sessionStorage !== 'undefined' ? sessionStorage.getItem('sessionId') || undefined : undefined,
      retryCount: 0,
      maxRetries: 3,
      ...error
    };

    dispatch({ type: 'ADD_ERROR', error: fullError });

    // Auto-report critical errors
    if (fullError.severity === 'critical') {
      reportErrorToServer(fullError);
    }

    return id;
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

  // Convenience methods
  const addApiError = useCallback((message: string, details?: { endpoint?: string; status?: number; context?: any }): string => {
    return addError({
      type: 'api',
      severity: details?.status && details.status >= 500 ? 'high' : 'medium',
      message,
      endpoint: details?.endpoint,
      status: details?.status,
      context: details?.context
    });
  }, [addError]);

  const addNetworkError = useCallback((message: string): string => {
    return addError({
      type: 'network',
      severity: 'high',
      message
    });
  }, [addError]);

  const addValidationError = useCallback((message: string, context?: any): string => {
    return addError({
      type: 'validation',
      severity: 'low',
      message,
      context
    });
  }, [addError]);

  const addAuthError = useCallback((message: string): string => {
    return addError({
      type: 'auth',
      severity: 'critical',
      message
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

  const contextValue: ErrorContextType = {
    // State
    errors: state.errors,
    globalError: state.globalError,
    networkStatus: state.networkStatus,
    errorCounts: state.errorCounts,
    
    // Actions
    addError,
    removeError,
    resolveError,
    clearErrors,
    setGlobalError,
    incrementRetry,
    
    // Convenience methods
    addApiError,
    addNetworkError,
    addValidationError,
    addAuthError,
    
    // Helpers
    hasErrors,
    hasCriticalErrors,
    getErrorsByType,
    getRecentErrors
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
    throw new Error('useErrorHandler must be used within an ErrorProvider');
  }
  return context;
}

// Helper function to report errors to server
async function reportErrorToServer(error: AppError) {
  try {
    await fetch('/api/errors/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...error,
        url: typeof window !== 'undefined' ? window.location.href : 'SSR'
      })
    });
  } catch (reportingError) {
    console.error('Failed to report error to server:', reportingError);
  }
}
