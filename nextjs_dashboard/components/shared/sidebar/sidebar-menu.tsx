/**
 * 🚀 SIDEBAR MENU - FASE 3 REFATORAÇÃO
 * ======================================
 * 
 * Menu principal do sidebar.
 * Extraído do sidebar.tsx para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { SidebarMenuProps } from './types';
import { SidebarMenuItem } from './sidebar-menu-item';

export function SidebarMenu({
  items,
  currentPath,
  onItemClick,
  isCollapsed
}: SidebarMenuProps) {
  return (
    <nav className="h-full overflow-y-auto overflow-x-hidden space-y-2 px-3 py-4 scrollbar-thin">
      {items.map((item) => {
        const isActive = currentPath === item.href;
        
        return (
          <div key={item.id} className="relative">
            <SidebarMenuItem
              item={item}
              isActive={isActive}
              isCollapsed={isCollapsed}
              onClick={() => onItemClick(item.href)}
            />
          </div>
        );
      })}
    </nav>
  );
}
