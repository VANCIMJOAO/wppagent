/**
 * 🚀 SIDEBAR MENU ITEM - FASE 3 REFATORAÇÃO
 * ============================================
 * 
 * Item individual do menu sidebar.
 * Extraído do sidebar.tsx para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from '@/lib/utils';
import { SidebarMenuItemProps } from './types';

export function SidebarMenuItem({
  item,
  isActive,
  isCollapsed,
  onClick
}: SidebarMenuItemProps) {
  const Icon = item.icon;

  return (
    <Button
      variant={isActive ? 'default' : 'ghost'}
      className={cn(
        'w-full justify-start h-[3.5rem] py-0 px-3 group',
        'transition-all duration-200 ease-in-out',
        'hover:shadow-sm hover:scale-[1.01]',
        isActive && 'shadow-md bg-gradient-to-r from-primary to-primary/90',
        !isActive && 'hover:bg-gray-50 hover:border-gray-200',
        isCollapsed ? 'justify-center px-2 h-[2.5rem]' : 'rounded-lg',
        item.disabled && 'opacity-50 cursor-not-allowed hover:scale-100'
      )}
      onClick={onClick}
      disabled={item.disabled}
    >
      <div className="flex items-center w-full h-full">
        <div className="flex items-center justify-center w-5 h-5 flex-shrink-0 mr-3">
          <Icon className={cn(
            'h-5 w-5 transition-transform duration-200',
            'group-hover:scale-110',
            isActive && 'text-white',
            !isActive && 'text-gray-600',
            isCollapsed && 'h-4 w-4'
          )} />
        </div>
        
        {!isCollapsed && (
          <div className="flex-1 min-w-0 flex items-center gap-2">
            <span className={cn(
              'text-sm font-semibold truncate transition-colors flex-1 text-left leading-none',
              isActive && 'text-white',
              !isActive && 'text-gray-900 group-hover:text-gray-950'
            )}>
              {item.label}
            </span>
            
            {item.badge && (
              <Badge 
                variant={item.badge === 'NEW' ? 'default' : 'secondary'}
                className={cn(
                  'text-xs px-2 py-0.5 font-medium flex-shrink-0',
                  'shadow-sm transition-transform duration-200',
                  'group-hover:scale-105',
                  item.badge === 'NEW' && 'bg-green-500 hover:bg-green-600 animate-pulse'
                )}
              >
                {item.badge}
              </Badge>
            )}
          </div>
        )}
        
        {isCollapsed && item.badge && (
          <Badge 
            variant={item.badge === 'NEW' ? 'default' : 'secondary'}
            className={cn(
              'absolute -top-1 -right-1 h-5 w-5 p-0',
              'flex items-center justify-center text-xs font-bold',
              'shadow-lg border-2 border-white',
              item.badge === 'NEW' && 'bg-green-500 animate-pulse'
            )}
          >
            {item.badge === 'NEW' ? 'N' : item.badge}
          </Badge>
        )}
      </div>
    </Button>
  );
}
