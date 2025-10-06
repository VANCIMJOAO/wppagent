/**
 * 🚀 COLLAPSIBLE COMPONENT - FASE 3 REFATORAÇÃO
 * ==============================================
 * 
 * Componente Collapsible extraído do AdvancedErrorBoundary.
 * Permite expandir/recolher seções de conteúdo.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React, { ReactNode, useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface CollapsibleProps {
  children: ReactNode;
}

interface CollapsibleTriggerProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

interface CollapsibleContentProps {
  children: ReactNode;
  className?: string;
}

function Collapsible({ children }: CollapsibleProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          if (child.type === CollapsibleTrigger) {
            return React.cloneElement(child, { 
              onClick: () => setIsOpen(!isOpen),
              isOpen 
            });
          }
          if (child.type === CollapsibleContent) {
            return isOpen ? child : null;
          }
        }
        return child;
      })}
    </div>
  );
}

function CollapsibleTrigger({ children, className, onClick, isOpen }: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  isOpen?: boolean;
}) {
  return (
    <button 
      className={`flex items-center gap-2 w-full ${className}`} 
      onClick={onClick}
      type="button"
    >
      {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      {children}
    </button>
  );
}

function CollapsibleContent({ children, className }: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={className}>{children}</div>;
}

export { Collapsible, CollapsibleTrigger, CollapsibleContent };
