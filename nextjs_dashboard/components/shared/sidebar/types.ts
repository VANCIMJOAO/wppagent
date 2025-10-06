/**
 * 🚀 SIDEBAR TYPES - FASE 3 REFATORAÇÃO
 * ======================================
 * 
 * Tipos para o sistema de sidebar refatorado.
 * Extraído do sidebar.tsx para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

import { LucideIcon } from 'lucide-react';

export interface User {
  id: number;
  email: string;
  name: string;
  role: string;
  avatar_url?: string;
}

export interface MenuItem {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  description: string;
  badge?: string;
  disabled?: boolean;
  adminOnly?: boolean;
}

export interface SidebarProps {
  children: React.ReactNode;
}

export interface SidebarHeaderProps {
  user: User | null;
  onLogout: () => void;
}

export interface SidebarMenuProps {
  items: MenuItem[];
  currentPath: string;
  onItemClick: (href: string) => void;
  isCollapsed: boolean;
}

export interface SidebarMenuItemProps {
  item: MenuItem;
  isActive: boolean;
  isCollapsed: boolean;
  onClick: () => void;
}

export interface SidebarFooterProps {
  user: User | null;
  onLogout: () => void;
}

export interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  menuItems: MenuItem[];
  currentPath: string;
  onItemClick: (href: string) => void;
  onLogout: () => void;
}
