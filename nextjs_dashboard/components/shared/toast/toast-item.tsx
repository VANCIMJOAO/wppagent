/**
 * 🚀 TOAST ITEM - FASE 3 REFATORAÇÃO
 * ===================================
 * 
 * Componente individual de toast.
 * Extraído do AdvancedToastProvider para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { X, AlertCircle, CheckCircle, AlertTriangle, Info, Wifi, WifiOff, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Toast } from './types';
import { useToast } from './toast-context';

interface ToastItemProps {
  toast: Toast;
}

const iconMap = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
  loading: Loader2,
  network: WifiOff
};

const colorMap = {
  success: 'border-green-200 bg-green-50 text-green-800',
  error: 'border-red-200 bg-red-50 text-red-800',
  warning: 'border-yellow-200 bg-yellow-50 text-yellow-800',
  info: 'border-blue-200 bg-blue-50 text-blue-800',
  loading: 'border-gray-200 bg-gray-50 text-gray-800',
  network: 'border-orange-200 bg-orange-50 text-orange-800'
};

export function ToastItem({ toast }: ToastItemProps) {
  const { removeToast, updateToast } = useToast();
  const Icon = iconMap[toast.type];
  const colorClass = colorMap[toast.type];

  const handleRetry = () => {
    if (toast.retry && toast.retry.retryCount < toast.retry.maxRetries) {
      toast.retry.onRetry();
      updateToast(toast.id, {
        retry: {
          ...toast.retry,
          retryCount: toast.retry.retryCount + 1
        }
      });
    }
  };

  const canRetry = toast.retry && toast.retry.retryCount < toast.retry.maxRetries;

  return (
    <Alert className={`mb-3 w-full max-w-md shadow-lg transition-all duration-300 ${colorClass}`}>
      <Icon className="h-4 w-4" />
      <AlertTitle className="flex items-center justify-between">
        <span>{toast.title}</span>
        <div className="flex items-center gap-2">
          {toast.priority && (
            <Badge variant="secondary" className="text-xs">
              {toast.priority}
            </Badge>
          )}
          {toast.dismissible && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => removeToast(toast.id)}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </AlertTitle>
      
      {toast.description && (
        <AlertDescription className="mt-2">
          {toast.description}
        </AlertDescription>
      )}

      {/* Progress bar */}
      {toast.type === 'loading' && toast.metadata?.progress !== undefined && (
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${toast.metadata.progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-600 mt-1">
            {toast.metadata.progress}%
          </p>
        </div>
      )}

      {/* Retry button */}
      {canRetry && (
        <div className="mt-3 flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleRetry}
            className="text-xs"
          >
            Retry ({toast.retry!.retryCount}/{toast.retry!.maxRetries})
          </Button>
        </div>
      )}

      {/* Action button */}
      {toast.action && (
        <div className="mt-3">
          <Button
            size="sm"
            variant="outline"
            onClick={toast.action.onClick}
            className="text-xs"
          >
            {toast.action.label}
          </Button>
        </div>
      )}

      {/* Network status indicator */}
      {toast.type === 'network' && (
        <div className="mt-2 flex items-center gap-1 text-xs">
          <Wifi className="h-3 w-3" />
          <span>Check your connection</span>
        </div>
      )}
    </Alert>
  );
}
