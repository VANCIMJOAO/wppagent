/**
 * 🚀 TOAST CONTAINER - FASE 3 REFATORAÇÃO
 * ========================================
 * 
 * Container que renderiza todos os toasts.
 * Extraído do AdvancedToastProvider para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { useToast } from './toast-context';
import { ToastItem } from './toast-item';

export function ToastContainer() {
  const { toasts } = useToast();

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
}
