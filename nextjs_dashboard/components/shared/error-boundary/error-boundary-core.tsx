/**
 * 🚀 ERROR BOUNDARY CORE - FASE 3 REFATORAÇÃO
 * ============================================
 * 
 * Lógica principal do error boundary extraída do AdvancedErrorBoundary.
 * Gerencia captura de erros, retry, e reporte.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React, { Component, ReactNode } from 'react';
import { AppError, useErrorHandler } from './ConsolidatedErrorProvider';
import { ErrorBoundaryProps, ErrorBoundaryState } from './types';
import { ErrorFallback } from './error-fallback';
import { debugLog } from '@/lib/debug';

export class ErrorBoundaryCore extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimer: NodeJS.Timeout | null = null;
  private errorReportingQueue: Array<AppError> = [];

  constructor(props: ErrorBoundaryProps) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRetrying: false,
      errorHistory: []
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const errorId = this.generateErrorId();
    const timestamp = Date.now();

    // Update state with error information
    this.setState(prevState => ({
      errorInfo,
      errorId,
      errorHistory: [
        ...prevState.errorHistory,
        {
          error,
          timestamp,
          stack: error.stack
        }
      ].slice(-10) // Keep only last 10 errors
    }));

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Create structured error for reporting
    const appError: AppError = {
      id: errorId,
      type: this.classifyError(error) as AppError['type'],
      severity: this.calculateSeverity(error),
      message: error.message,
      details: JSON.stringify(this.formatErrorDetails(error, errorInfo)),
      stack: error.stack,
      timestamp: new Date().toISOString(),
      context: {
        level: this.props.level || 'component',
        context: this.props.context,
        retryCount: this.state.retryCount,
        componentStack: errorInfo.componentStack || undefined,
        errorBoundary: 'ErrorBoundaryCore',
        url: typeof window !== 'undefined' ? window.location.href : 'SSR'
      },
      retryCount: 0,
      maxRetries: this.props.retryAttempts || 3
    };

    // Queue error for reporting
    this.queueErrorForReporting(appError);

    // Auto-retry for certain error types
    if (this.shouldAutoRetry(error) && this.state.retryCount < (this.props.retryAttempts || 3)) {
      this.scheduleRetry();
    }

    // Log error for development
    if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
      console.group('🚨 Error Boundary Caught Error');
      debugLog.error('Error:', error);
      debugLog.error('Error Info:', errorInfo);
      debugLog.error('Props:', this.props);
      debugLog.error('State:', this.state);
      console.groupEnd();
    }
  }

  componentWillUnmount() {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
    }
  }

  private generateErrorId(): string {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private classifyError(error: Error): AppError['type'] {
    if (error.name === 'ChunkLoadError') return 'network';
    if (error.message.includes('Network')) return 'network';
    if (error.message.includes('Timeout')) return 'network';
    if (error.message.includes('Permission')) return 'auth';
    if (error.message.includes('Not Found')) return 'api';
    if (error.message.includes('Validation')) return 'validation';
    return 'unknown';
  }

  private calculateSeverity(error: Error): 'low' | 'medium' | 'high' | 'critical' {
    const errorType = this.classifyError(error);
    
    switch (errorType) {
      case 'network':
        return 'medium';
      case 'auth':
      case 'api':
        return 'high';
      case 'validation':
        return 'low';
      default:
        return 'medium';
    }
  }

  private formatErrorDetails(error: Error, errorInfo: React.ErrorInfo): Record<string, any> {
    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      props: this.props,
      timestamp: new Date().toISOString()
    };
  }

  private shouldAutoRetry(error: Error): boolean {
    const errorType = this.classifyError(error);
    return ['network'].includes(errorType);
  }

  private scheduleRetry() {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
    }

    const delay = Math.min(1000 * Math.pow(2, this.state.retryCount), 10000);
    
    this.retryTimer = setTimeout(() => {
      this.setState(prevState => ({
        isRetrying: true,
        retryCount: prevState.retryCount + 1
      }));

      setTimeout(() => {
        this.setState({
          hasError: false,
          error: null,
          errorInfo: null,
          errorId: null,
          isRetrying: false
        });
      }, 100);
    }, delay);
  }

  private queueErrorForReporting(appError: AppError) {
    this.errorReportingQueue.push(appError);
    
    // Process queue
    this.processErrorReportingQueue();
  }

  private async processErrorReportingQueue() {
    if (this.errorReportingQueue.length === 0) return;

    const errors = [...this.errorReportingQueue];
    this.errorReportingQueue = [];

    for (const error of errors) {
      try {
        // Report error using error handler
        const errorHandler = useErrorHandler();
        errorHandler.addError(error);
      } catch (reportError) {
        debugLog.error('Failed to report error:', reportError);
      }
    }
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: this.state.retryCount + 1
    });
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0,
      isRetrying: false,
      errorHistory: []
    });
  };

  private handleReport = () => {
    if (this.state.error) {
      const appError: AppError = {
        id: this.state.errorId || this.generateErrorId(),
        type: this.classifyError(this.state.error),
        severity: this.calculateSeverity(this.state.error),
        message: this.state.error.message,
        details: JSON.stringify(this.formatErrorDetails(this.state.error, this.state.errorInfo!)),
        stack: this.state.error.stack,
        timestamp: new Date().toISOString(),
        context: {
          level: this.props.level || 'component',
          context: this.props.context,
          retryCount: this.state.retryCount,
          componentStack: this.state.errorInfo?.componentStack || undefined,
          errorBoundary: 'ErrorBoundaryCore',
          url: typeof window !== 'undefined' ? window.location.href : 'SSR'
        },
        retryCount: this.state.retryCount,
        maxRetries: this.props.retryAttempts || 3
      };

      this.queueErrorForReporting(appError);
    }
  };

  private handleGoHome = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  };

  private handleGoBack = () => {
    if (typeof window !== 'undefined') {
      window.history.back();
    }
  };

  render() {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const actions = {
        onRetry: this.handleRetry,
        onReset: this.handleReset,
        onReport: this.handleReport,
        onGoHome: this.handleGoHome,
        onGoBack: this.handleGoBack
      };

      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          errorId={this.state.errorId}
          retryCount={this.state.retryCount}
          isRetrying={this.state.isRetrying}
          showErrorDetails={this.props.showErrorDetails || false}
          actions={actions}
          level={this.props.level || 'component'}
          context={this.props.context}
        />
      );
    }

    return this.props.children;
  }
}
