/**
 * 🚀 TOAST REDUCER - FASE 3 REFATORAÇÃO
 * =====================================
 * 
 * Reducer para gerenciar estado do sistema de toast.
 * Extraído do AdvancedToastProvider para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

import { Toast, ToastState } from './types';

export const initialState: ToastState = {
  toasts: [],
  maxToasts: 5,
  globalPause: false,
  defaultDuration: 5000
};

export type ToastAction =
  | { type: 'ADD_TOAST'; toast: Toast }
  | { type: 'REMOVE_TOAST'; id: string }
  | { type: 'UPDATE_TOAST'; id: string; updates: Partial<Toast> }
  | { type: 'CLEAR_ALL' }
  | { type: 'CLEAR_BY_TYPE'; toastType: Toast['type'] }
  | { type: 'CLEAR_BY_CATEGORY'; category: string }
  | { type: 'SET_GLOBAL_PAUSE'; paused: boolean }
  | { type: 'SET_MAX_TOASTS'; maxToasts: number }
  | { type: 'SET_DEFAULT_DURATION'; duration: number };

export function toastReducer(state: ToastState, action: ToastAction): ToastState {
  switch (action.type) {
    case 'ADD_TOAST':
      const newToasts = [...state.toasts, action.toast];
      // Manter apenas os últimos maxToasts
      const trimmedToasts = newToasts.slice(-state.maxToasts);
      return {
        ...state,
        toasts: trimmedToasts
      };

    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.id !== action.id)
      };

    case 'UPDATE_TOAST':
      return {
        ...state,
        toasts: state.toasts.map(toast =>
          toast.id === action.id ? { ...toast, ...action.updates } : toast
        )
      };

    case 'CLEAR_ALL':
      return {
        ...state,
        toasts: []
      };

    case 'CLEAR_BY_TYPE':
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.type !== action.toastType)
      };

    case 'CLEAR_BY_CATEGORY':
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.category !== action.category)
      };

    case 'SET_GLOBAL_PAUSE':
      return {
        ...state,
        globalPause: action.paused
      };

    case 'SET_MAX_TOASTS':
      return {
        ...state,
        maxToasts: action.maxToasts
      };

    case 'SET_DEFAULT_DURATION':
      return {
        ...state,
        defaultDuration: action.duration
      };

    default:
      return state;
  }
}
