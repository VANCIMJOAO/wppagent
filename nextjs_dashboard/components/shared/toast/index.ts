/**
 * 🚀 TOAST MODULE EXPORTS - FASE 3 REFATORAÇÃO
 * =============================================
 * 
 * Exports centralizados para o sistema de toast refatorado.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

export { ToastProvider, useToast } from './toast-context';
export { ToastContainer } from './toast-container';
export { ToastItem } from './toast-item';
export { toastReducer, initialState } from './toast-reducer';
export type { Toast, ToastState, ToastContextType, AppError } from './types';
