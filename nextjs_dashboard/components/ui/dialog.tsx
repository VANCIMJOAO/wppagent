'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DialogContextType {
  isOpen: boolean;
  setOpen: (open: boolean) => void;
}

const DialogContext = createContext<DialogContextType | null>(null);

interface DialogProps {
  children: ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function Dialog({ children, open: controlledOpen, onOpenChange }: DialogProps) {
  const [internalOpen, setInternalOpen] = useState(false);

  const isOpen = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const setOpen = (open: boolean) => {
    if (onOpenChange) {
      onOpenChange(open);
    } else {
      setInternalOpen(open);
    }
  };

  return (
    <DialogContext.Provider value={{ isOpen, setOpen }}>
      <div className="relative">
        {children}
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
              onClick={() => setOpen(false)}
            />
            {/* Modal */}
            <div className="relative bg-white rounded-lg shadow-lg max-w-lg w-full mx-4 max-h-[90vh] overflow-auto">
              {React.Children.map(children, child => {
                if (React.isValidElement(child) && child.type === DialogContent) {
                  return child;
                }
                return null;
              })}
            </div>
          </div>
        )}
      </div>
    </DialogContext.Provider>
  );
}

interface DialogTriggerProps {
  children: ReactNode;
  asChild?: boolean;
}

export function DialogTrigger({ children, asChild }: DialogTriggerProps) {
  const context = useContext(DialogContext);

  if (!context) {
    throw new Error('DialogTrigger must be used within Dialog');
  }

  const handleClick = () => {
    context.setOpen(true);
  };

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, { onClick: handleClick });
  }

  return (
    <button onClick={handleClick}>
      {children}
    </button>
  );
}

interface DialogContentProps {
  children: ReactNode;
  className?: string;
}

export function DialogContent({ children, className = '' }: DialogContentProps) {
  const context = useContext(DialogContext);

  if (!context) {
    throw new Error('DialogContent must be used within Dialog');
  }

  return (
    <div className={`p-6 ${className}`}>
      <Button
        onClick={() => context.setOpen(false)}
        className="absolute top-2 right-2 p-1 h-auto w-auto hover:bg-gray-100"
        variant="ghost"
      >
        <X className="h-4 w-4" />
      </Button>
      {children}
    </div>
  );
}

export function DialogHeader({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`mb-4 ${className}`}>{children}</div>;
}

export function DialogTitle({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <h2 className={`text-lg font-semibold ${className}`}>{children}</h2>;
}
