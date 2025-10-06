/**
 * 🚀 TOAST PROVIDER CONSOLIDADO - FASE 3 REFATORAÇÃO
 * ===================================================
 * 
 * Provider consolidado que combina todos os componentes modulares de toast.
 * Substitui o AdvancedToastProvider (667 linhas) por uma implementação modular.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React, { ReactNode } from 'react';
import { ToastProvider } from './toast-context';
import { ToastContainer } from './toast-container';

interface ConsolidatedToastProviderProps {
  children: ReactNode;
}

export function ConsolidatedToastProvider({ children }: ConsolidatedToastProviderProps) {
  return (
    <ToastProvider>
      {children}
      <ToastContainer />
    </ToastProvider>
  );
}

// Re-export para compatibilidade
export { useToast } from './toast-context';
