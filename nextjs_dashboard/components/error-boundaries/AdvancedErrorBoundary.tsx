'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AppError, useErrorHandler } from './ErrorProvider';
import { AlertTriangle, RefreshCw, Bug, Home, ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

// Simple Collapsible component
interface CollapsibleProps {
  children: ReactNode;
}

function Collapsible({ children }: CollapsibleProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          if (child.type === CollapsibleTrigger) {
            return React.cloneElement(child, { onClick: () => setIsOpen(!isOpen) });
          }
          if (child.type === CollapsibleContent) {
            return isOpen ? child : null;
          }
        }
        return child;
      })}
    </div>
  );
}

function CollapsibleTrigger({ children, className, onClick }: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <button className={className} onClick={onClick}>
      {children}
    </button>
  );
}

function CollapsibleContent({ children, className }: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={className}>{children}</div>;
}

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  level?: 'page' | 'section' | 'component';
  context?: string;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  retryAttempts?: number;
  isolateErrors?: boolean;
  showErrorDetails?: boolean;
  allowReset?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
  retryCount: number;
  isRetrying: boolean;
  errorHistory: Array<{
    error: Error;
    timestamp: number;
    stack?: string;
  }>;
}

class AdvancedErrorBoundaryClass extends Component<Props, State> {
  private retryTimer: NodeJS.Timeout | null = null;
  private errorReportingQueue: Array<AppError> = [];

  constructor(props: Props) {
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

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
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
      type: this.classifyError(error),
      severity: this.calculateSeverity(error),
      message: error.message,
      details: this.formatErrorDetails(error, errorInfo),
      stack: error.stack,
      timestamp: new Date().toISOString(),
      context: {
        level: this.props.level || 'component',
        context: this.props.context,
        retryCount: this.state.retryCount,
        componentStack: errorInfo.componentStack,
        errorBoundary: 'AdvancedErrorBoundary',
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
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Props:', this.props);
      console.error('State:', this.state);
      console.groupEnd();
    }
  }

  componentWillUnmount() {
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
    }
  }

  private generateErrorId(): string {
    return `eb_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private classifyError(error: Error): AppError['type'] {
    const message = error.message.toLowerCase();
    const stack = error.stack?.toLowerCase() || '';

    if (message.includes('network') || message.includes('fetch') || message.includes('connection')) {
      return 'network';
    }
    if (message.includes('unauthorized') || message.includes('forbidden') || message.includes('auth')) {
      return 'auth';
    }
    if (message.includes('validation') || message.includes('invalid') || message.includes('required')) {
      return 'validation';
    }
    if (stack.includes('api') || stack.includes('axios') || stack.includes('fetch')) {
      return 'api';
    }

    return 'unknown';
  }

  private calculateSeverity(error: Error): AppError['severity'] {
    const message = error.message.toLowerCase();
    const level = (this.props.level || 'component') as 'page' | 'section' | 'component';

    // Page level errors are more critical
    if (level === 'page') {
      return 'critical';
    }

    // Auth errors are always high priority
    if (message.includes('auth') || message.includes('unauthorized')) {
      return 'critical';
    }

    // Network errors vary by context
    if (message.includes('network') || message.includes('fetch')) {
      return level === 'section' ? 'high' : 'medium';
    }

    // Default based on component level
    if (level === 'section') {
      return 'high';
    }
    return 'medium';
  }

  private formatErrorDetails(error: Error, errorInfo: ErrorInfo): string {
    return JSON.stringify({
      name: error.name,
      message: error.message,
      stack: error.stack?.split('\n').slice(0, 10), // First 10 lines of stack
      componentStack: errorInfo.componentStack?.split('\n').slice(0, 5), // First 5 components
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'SSR',
      url: typeof window !== 'undefined' ? window.location.href : 'SSR'
    }, null, 2);
  }

  private queueErrorForReporting(error: AppError) {
    this.errorReportingQueue.push(error);

    // Process queue asynchronously
    setTimeout(() => this.processErrorQueue(), 100);
  }

  private async processErrorQueue() {
    if (this.errorReportingQueue.length === 0) return;

    const errorsToReport = [...this.errorReportingQueue];
    this.errorReportingQueue = [];

    try {
      // Try to report to error tracking service
      await this.reportErrors(errorsToReport);
    } catch (reportingError) {
      console.error('Failed to report errors:', reportingError);
      // Re-queue for later retry
      this.errorReportingQueue.unshift(...errorsToReport);
    }
  }

  private async reportErrors(errors: AppError[]) {
    const batchReportUrl = '/api/errors/batch-report';

    await fetch(batchReportUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Error-Boundary': 'AdvancedErrorBoundary'
      },
      body: JSON.stringify({
        errors,
        metadata: {
          timestamp: new Date().toISOString(),
          userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'SSR',
          url: typeof window !== 'undefined' ? window.location.href : 'SSR',
          viewport: typeof window !== 'undefined' ? {
            width: window.innerWidth,
            height: window.innerHeight
          } : null
        }
      })
    });
  }

  private shouldAutoRetry(error: Error): boolean {
    const message = error.message.toLowerCase();

    // Auto-retry for network and temporary errors
    return (
      message.includes('network') ||
      message.includes('timeout') ||
      message.includes('connection') ||
      message.includes('503') ||
      message.includes('502') ||
      message.includes('504')
    );
  }

  private scheduleRetry() {
    const retryDelay = Math.min(1000 * Math.pow(2, this.state.retryCount), 10000); // Exponential backoff, max 10s

    this.setState({ isRetrying: true });

    this.retryTimer = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: null,
        retryCount: prevState.retryCount + 1,
        isRetrying: false
      }));
    }, retryDelay);
  }

  private handleManualRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: prevState.retryCount + 1,
      isRetrying: false
    }));
  };

  private handleResetState = () => {
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

  private handleReportIssue = () => {
    const error = this.state.error;
    const errorInfo = this.state.errorInfo;

    if (!error) return;

    const issueData = {
      title: `Error in ${this.props.context || 'Component'}: ${error.message}`,
      body: this.formatErrorDetails(error, errorInfo || {} as ErrorInfo),
      labels: ['bug', 'error-boundary', `severity-${this.calculateSeverity(error)}`]
    };

    // Open GitHub issue creation or internal reporting system
    const reportUrl = `/report-issue?data=${encodeURIComponent(JSON.stringify(issueData))}`;
    window.open(reportUrl, '_blank');
  };

  render() {
    if (this.state.hasError) {
      // Show custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Show retry loading state
      if (this.state.isRetrying) {
        return (
          <Card className="m-4">
            <CardContent className="flex items-center justify-center p-8">
              <div className="text-center space-y-4">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-500" />
                <p className="text-muted-foreground">
                  Tentando recuperar automaticamente...
                </p>
                <p className="text-sm text-muted-foreground">
                  Tentativa {this.state.retryCount + 1} de {this.props.retryAttempts || 3}
                </p>
              </div>
            </CardContent>
          </Card>
        );
      }

      // Render error UI
      return this.renderErrorUI();
    }

    return this.props.children;
  }

  private renderErrorUI() {
    const { error, errorInfo, errorId, retryCount, errorHistory } = this.state;
    const { level = 'component', context, retryAttempts = 3, showErrorDetails = true, allowReset = true } = this.props;

    const canRetry = retryCount < retryAttempts;
    const severity = error ? this.calculateSeverity(error) : 'medium';

    return (
      <div className="error-boundary-container">
        <Card className={`m-4 border-destructive ${severity === 'critical' ? 'bg-destructive/5' : ''}`}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertTriangle className={`h-5 w-5 ${
                  severity === 'critical' ? 'text-destructive' :
                  severity === 'high' ? 'text-orange-500' : 'text-yellow-500'
                }`} />
                <CardTitle className="text-lg">
                  {level === 'page' ? 'Erro na Página' :
                   level === 'section' ? 'Erro na Seção' : 'Erro no Componente'}
                </CardTitle>
                <Badge variant={severity === 'critical' ? 'destructive' : 'secondary'}>
                  {severity}
                </Badge>
              </div>

              {errorId && (
                <Badge variant="outline" className="font-mono text-xs">
                  {errorId}
                </Badge>
              )}
            </div>

            <CardDescription>
              {context && (
                <span className="font-medium">{context}: </span>
              )}
              {error?.message || 'Ocorreu um erro inesperado'}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Error Actions */}
            <div className="flex flex-wrap gap-2">
              {canRetry && (
                <Button
                  onClick={this.handleManualRetry}
                  variant="default"
                  size="sm"
                  className="flex items-center space-x-1"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Tentar Novamente</span>
                  {retryCount > 0 && (
                    <span className="text-xs opacity-75">({retryCount}/{retryAttempts})</span>
                  )}
                </Button>
              )}

              {allowReset && (
                <Button
                  onClick={this.handleResetState}
                  variant="outline"
                  size="sm"
                  className="flex items-center space-x-1"
                >
                  <Home className="h-4 w-4" />
                  <span>Resetar</span>
                </Button>
              )}

              <Button
                onClick={() => window.location.reload()}
                variant="outline"
                size="sm"
                className="flex items-center space-x-1"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Recarregar Página</span>
              </Button>

              <Button
                onClick={this.handleReportIssue}
                variant="outline"
                size="sm"
                className="flex items-center space-x-1"
              >
                <Bug className="h-4 w-4" />
                <span>Reportar Problema</span>
              </Button>

              <Button
                onClick={() => window.history.back()}
                variant="ghost"
                size="sm"
                className="flex items-center space-x-1"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Voltar</span>
              </Button>
            </div>

            {/* Retry Information */}
            {retryCount > 0 && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Tentativas de Recuperação</AlertTitle>
                <AlertDescription>
                  Esta operação foi tentada {retryCount} vez{retryCount > 1 ? 'es' : ''}.
                  {canRetry ? ' Você pode tentar novamente.' : ' Limite de tentativas atingido.'}
                </AlertDescription>
              </Alert>
            )}

            {/* Error Details */}
            {showErrorDetails && error && (
              <Collapsible>
                <CollapsibleTrigger className="flex items-center space-x-2 text-sm font-medium text-muted-foreground hover:text-foreground">
                  <ChevronDown className="h-4 w-4" />
                  <span>Detalhes Técnicos</span>
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-2">
                  <div className="space-y-2">
                    <div className="bg-muted p-3 rounded-md">
                      <h4 className="font-medium text-sm mb-1">Mensagem de Erro:</h4>
                      <code className="text-sm text-red-600 dark:text-red-400">
                        {error.name}: {error.message}
                      </code>
                    </div>

                    {error.stack && (
                      <div className="bg-muted p-3 rounded-md">
                        <h4 className="font-medium text-sm mb-1">Stack Trace:</h4>
                        <pre className="text-xs overflow-auto max-h-32 text-muted-foreground">
                          {error.stack}
                        </pre>
                      </div>
                    )}

                    {errorInfo?.componentStack && (
                      <div className="bg-muted p-3 rounded-md">
                        <h4 className="font-medium text-sm mb-1">Component Stack:</h4>
                        <pre className="text-xs overflow-auto max-h-32 text-muted-foreground">
                          {errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            )}

            {/* Error History */}
            {errorHistory.length > 1 && (
              <Collapsible>
                <CollapsibleTrigger className="flex items-center space-x-2 text-sm font-medium text-muted-foreground hover:text-foreground">
                  <ChevronDown className="h-4 w-4" />
                  <span>Histórico de Erros ({errorHistory.length})</span>
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-2">
                  <div className="space-y-2">
                    {errorHistory.slice(-5).map((historyItem, index) => (
                      <div key={index} className="bg-muted p-2 rounded text-xs">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-medium">{historyItem.error.name}</span>
                          <span className="text-muted-foreground">
                            {new Date(historyItem.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="text-muted-foreground">
                          {historyItem.error.message}
                        </div>
                      </div>
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            )}

            {/* Help Text */}
            <div className="text-xs text-muted-foreground border-t pt-2">
              <p>
                Se o problema persistir, tente recarregar a página ou entre em contato com o suporte.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
}

// HOC Wrapper to provide error context
export function AdvancedErrorBoundary(props: Props) {
  return <AdvancedErrorBoundaryClass {...props} />;
}

// Hook for programmatic error boundary control
export function useErrorBoundary() {
  return {
    reportError: (error: Error, context?: string) => {
      // This will trigger the error boundary
      throw new Error(`${context ? `${context}: ` : ''}${error.message}`);
    },

    captureError: (error: Error, context?: any) => {
      // Report error without triggering boundary
      console.error('Captured Error:', error, context);

      // Could send to error reporting service
      fetch('/api/errors/capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: {
            message: error.message,
            stack: error.stack,
            name: error.name
          },
          context,
          timestamp: new Date().toISOString(),
          url: typeof window !== 'undefined' ? window.location.href : 'SSR'
        })
      }).catch(console.error);
    }
  };
}

export default AdvancedErrorBoundary;
