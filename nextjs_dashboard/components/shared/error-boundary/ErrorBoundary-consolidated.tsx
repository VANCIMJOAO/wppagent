/**
 * 🚀 ERROR BOUNDARY CONSOLIDADO - FASE 3 REFATORAÇÃO
 * ===================================================
 * 
 * Error boundary consolidado que usa componentes modulares.
 * Substitui o AdvancedErrorBoundary (616 linhas) por uma implementação modular.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React, { ReactNode } from 'react';
import { ErrorBoundaryCore } from './error-boundary-core';
import { ErrorBoundaryProps } from './types';
import { debugLog } from '@/lib/debug';

// HOC Wrapper to provide error context
export function ConsolidatedErrorBoundary(props: ErrorBoundaryProps) {
  return <ErrorBoundaryCore {...props} />;
}

// Hook for programmatic error boundary control
export function useErrorBoundary() {
  // This would typically integrate with a global error handler
  // For now, we'll provide a simple interface
  return {
    reportError: (error: Error, context?: string) => {
      debugLog.error('Error reported:', { error, context });
      // In a real implementation, this would send to an error tracking service
    },
    clearErrors: () => {
      debugLog.info('Errors cleared');
    }
  };
}

// Convenience exports with different levels
export const PageErrorBoundary = (props: Omit<ErrorBoundaryProps, 'level'>) => (
  <ConsolidatedErrorBoundary {...props} level="page" />
);

export const SectionErrorBoundary = (props: Omit<ErrorBoundaryProps, 'level'>) => (
  <ConsolidatedErrorBoundary {...props} level="section" />
);

export const ComponentErrorBoundary = (props: Omit<ErrorBoundaryProps, 'level'>) => (
  <ConsolidatedErrorBoundary {...props} level="component" />
);

// Default export for backward compatibility
export default ConsolidatedErrorBoundary;
