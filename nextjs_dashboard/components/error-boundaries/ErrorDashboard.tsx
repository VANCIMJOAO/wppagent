'use client';

import React, { useState } from 'react';
import { AlertTriangle, RefreshCw, Trash2, CheckCircle, Clock, Wifi, WifiOff, Signal } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useErrorHandler, AppError } from './ErrorProvider';

export function ErrorDashboard() {
  const {
    errors,
    globalError,
    networkStatus,
    errorCounts,
    clearErrors,
    removeError,
    resolveError,
    hasErrors,
    hasCriticalErrors,
    getRecentErrors
  } = useErrorHandler();

  const [selectedError, setSelectedError] = useState<AppError | null>(null);

  const recentErrors = getRecentErrors(30); // Last 30 minutes
  const totalErrors = errors.length;

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
        return <Wifi className="w-4 h-4 text-green-500" />;
      case 'offline':
        return <WifiOff className="w-4 h-4 text-red-500" />;
      case 'slow':
        return <Signal className="w-4 h-4 text-yellow-500" />;
    }
  };

  // Don't show dashboard if no errors and no critical state
  if (!hasErrors() && !globalError && networkStatus === 'online') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm">
      {/* Global Critical Error */}
      {globalError && (
        <Alert className="mb-4 border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-500" />
          <AlertDescription className="text-red-800">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-medium">Erro Crítico</p>
                <p className="text-sm">{globalError.message}</p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => resolveError(globalError.id)}
                className="text-red-600 hover:text-red-800"
              >
                <CheckCircle className="h-3 w-3" />
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Error Summary Card */}
      <Card className="shadow-lg">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className={`w-4 h-4 ${hasCriticalErrors() ? 'text-red-500' : 'text-yellow-500'}`} />
              Monitor de Erros
            </div>
            <div className="flex items-center gap-2">
              {getNetworkStatusIcon()}
              <Badge variant="outline" className="text-xs">
                {totalErrors}
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-3">
          {/* Network Status */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Rede:</span>
            <span className={`capitalize ${
              networkStatus === 'online' ? 'text-green-600' :
              networkStatus === 'offline' ? 'text-red-600' : 'text-yellow-600'
            }`}>
              {networkStatus === 'online' ? 'Online' :
               networkStatus === 'offline' ? 'Offline' : 'Lenta'}
            </span>
          </div>

          {/* Error Counts by Type */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(errorCounts).map(([type, count]) => (
              count > 0 && (
                <div key={type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="flex items-center gap-1">
                    <span>{getTypeIcon(type as AppError['type'])}</span>
                    {type}
                  </span>
                  <Badge variant="secondary" className="h-5 text-xs">
                    {count}
                  </Badge>
                </div>
              )
            ))}
          </div>

          {/* Recent Errors */}
          {recentErrors.length > 0 && (
            <div>
              <div className="text-xs text-gray-600 mb-2 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Últimos 30min ({recentErrors.length})
              </div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {recentErrors.slice(0, 3).map((error) => (
                  <Dialog key={error.id}>
                    <DialogTrigger asChild>
                      <button
                        className="w-full text-left p-2 text-xs bg-gray-50 hover:bg-gray-100 rounded border text-gray-700 transition-colors"
                        onClick={() => setSelectedError(error)}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-1 flex-1 min-w-0">
                            <span>{getTypeIcon(error.type)}</span>
                            <div className="min-w-0 flex-1">
                              <p className="truncate">{error.message}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge className={`h-4 text-xs ${getSeverityColor(error.severity)}`}>
                                  {error.severity}
                                </Badge>
                                <span className="text-gray-500">
                                  {new Date(error.timestamp).toLocaleTimeString()}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </button>
                    </DialogTrigger>

                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                          <span>{getTypeIcon(error.type)}</span>
                          Detalhes do Erro
                        </DialogTitle>
                      </DialogHeader>

                      {selectedError && (
                        <ErrorDetails
                          error={selectedError}
                          onResolve={() => resolveError(selectedError.id)}
                          onRemove={() => removeError(selectedError.id)}
                        />
                      )}
                    </DialogContent>
                  </Dialog>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-2 border-t">
            <Button
              size="sm"
              variant="outline"
              onClick={clearErrors}
              className="flex-1 text-xs h-8"
            >
              <Trash2 className="w-3 h-3 mr-1" />
              Limpar
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => window.location.reload()}
              className="flex-1 text-xs h-8"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Recarregar
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ErrorDetails({
  error,
  onResolve,
  onRemove
}: {
  error: AppError;
  onResolve: () => void;
  onRemove: () => void;
}) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <strong>Tipo:</strong> {error.type}
        </div>
        <div>
          <strong>Severidade:</strong>
          <Badge className={`ml-2 ${getSeverityColor(error.severity)}`}>
            {error.severity}
          </Badge>
        </div>
        <div>
          <strong>Timestamp:</strong> {new Date(error.timestamp).toLocaleString()}
        </div>
        <div>
          <strong>ID:</strong> <code className="text-xs">{error.id}</code>
        </div>
        {error.endpoint && (
          <div className="col-span-2">
            <strong>Endpoint:</strong> <code className="text-xs">{error.endpoint}</code>
          </div>
        )}
        {error.status && (
          <div>
            <strong>Status:</strong> {error.status}
          </div>
        )}
        {error.retryCount !== undefined && (
          <div>
            <strong>Tentativas:</strong> {error.retryCount}/{error.maxRetries}
          </div>
        )}
      </div>

      <div>
        <strong>Mensagem:</strong>
        <p className="mt-1 p-2 bg-gray-50 rounded text-sm">{error.message}</p>
      </div>

      {error.details && (
        <div>
          <strong>Detalhes:</strong>
          <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-auto max-h-32">
            {error.details}
          </pre>
        </div>
      )}

      {error.context && (
        <div>
          <strong>Contexto:</strong>
          <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-auto max-h-32">
            {JSON.stringify(error.context, null, 2)}
          </pre>
        </div>
      )}

      {error.stack && (
        <details>
          <summary className="cursor-pointer text-sm font-medium">Stack Trace</summary>
          <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-auto max-h-40">
            {error.stack}
          </pre>
        </details>
      )}

      <div className="flex gap-2 pt-4 border-t">
        <Button onClick={onResolve} className="flex-1">
          <CheckCircle className="w-4 h-4 mr-2" />
          Marcar como Resolvido
        </Button>
        <Button onClick={onRemove} variant="outline" className="flex-1">
          <Trash2 className="w-4 h-4 mr-2" />
          Remover
        </Button>
      </div>
    </div>
  );
}

function getSeverityColor(severity: AppError['severity']) {
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
}
