/**
 * 🚀 ERROR BOUNDARY MODULE - FASE 3 REFATORAÇÃO
 * ==============================================
 * 
 * Barrel file para exportar todos os componentes do error boundary refatorado.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

export { ErrorBoundaryCore } from './error-boundary-core';
export { ErrorFallback } from './error-fallback';
export { UniversalErrorBoundary } from './UniversalErrorBoundary';
export { ConsolidatedErrorProvider, useErrorHandler, ErrorDashboard } from './ConsolidatedErrorProvider';
export { Collapsible, CollapsibleTrigger, CollapsibleContent } from './collapsible';
export type { 
  ErrorBoundaryProps, 
  ErrorBoundaryState, 
  ErrorDetails, 
  ErrorActions, 
  ErrorFallbackProps 
} from './types';
export type { UniversalErrorBoundaryProps } from './UniversalErrorBoundary';
export type { AppError, ErrorContextType } from './ConsolidatedErrorProvider';
