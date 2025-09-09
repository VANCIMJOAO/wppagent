'use client';

import { useState, useCallback } from 'react';

export interface Toast {
  id: string;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  duration?: number;
  variant?: 'default' | 'destructive' | 'success' | 'warning';
}

interface ToastContextType {
  toasts: Toast[];
  toast: (toast: Omit<Toast, 'id'>) => void;
  dismiss: (toastId: string) => void;
  dismissAll: () => void;
}

const toasts: Toast[] = [];
const listeners: Array<(toasts: Toast[]) => void> = [];

let toastCount = 0;

function genId() {
  toastCount = (toastCount + 1) % Number.MAX_VALUE;
  return toastCount.toString();
}

const addToast = (toast: Omit<Toast, 'id'>) => {
  const id = genId();
  const newToast: Toast = {
    ...toast,
    id,
    duration: toast.duration ?? 5000,
    variant: toast.variant ?? 'default'
  };
  
  toasts.push(newToast);
  listeners.forEach((listener) => listener([...toasts]));
  
  // Auto dismiss after duration
  if (newToast.duration && newToast.duration > 0) {
    setTimeout(() => {
      dismissToast(id);
    }, newToast.duration);
  }
  
  return id;
};

const dismissToast = (toastId: string) => {
  const index = toasts.findIndex((t) => t.id === toastId);
  if (index > -1) {
    toasts.splice(index, 1);
    listeners.forEach((listener) => listener([...toasts]));
  }
};

const dismissAllToasts = () => {
  toasts.splice(0, toasts.length);
  listeners.forEach((listener) => listener([...toasts]));
};

export function useToast() {
  const [localToasts, setLocalToasts] = useState<Toast[]>([...toasts]);

  useState(() => {
    listeners.push(setLocalToasts);
    return () => {
      const index = listeners.indexOf(setLocalToasts);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  });

  const toast = useCallback((toast: Omit<Toast, 'id'>) => {
    return addToast(toast);
  }, []);

  const dismiss = useCallback((toastId: string) => {
    dismissToast(toastId);
  }, []);

  const dismissAll = useCallback(() => {
    dismissAllToasts();
  }, []);

  return {
    toasts: localToasts,
    toast,
    dismiss,
    dismissAll,
  };
}
