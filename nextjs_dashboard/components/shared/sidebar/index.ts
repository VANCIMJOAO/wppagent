/**
 * 🚀 SIDEBAR MODULE - FASE 3 REFATORAÇÃO
 * ========================================
 * 
 * Barrel file para exportar todos os componentes do sidebar refatorado.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

export { SidebarHeader } from './sidebar-header';
export { SidebarMenu } from './sidebar-menu';
export { SidebarMenuItem } from './sidebar-menu-item';
export { SidebarFooter } from './sidebar-footer';
export { MobileMenu } from './mobile-menu';
export { MENU_ITEMS, ADMIN_MENU_ITEMS, getMenuItemsForUser } from './menu-items';
export type { 
  User, 
  MenuItem, 
  SidebarProps, 
  SidebarHeaderProps, 
  SidebarMenuProps,
  SidebarMenuItemProps,
  SidebarFooterProps,
  MobileMenuProps
} from './types';
