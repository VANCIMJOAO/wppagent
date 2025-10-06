/**
 * 🚀 SIDEBAR MENU ITEMS - FASE 3 REFATORAÇÃO
 * ============================================
 * 
 * Configuração dos itens do menu sidebar.
 * Extraído do sidebar.tsx para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

import {
  LayoutDashboard,
  MessageCircle,
  Users,
  Calendar,
  FileText,
  Settings,
  UserX,
  HelpCircle,
  Shield,
  MessageSquare,
  Database,
  User as UserIcon
} from 'lucide-react';
import { MenuItem, User } from './types';

export const MENU_ITEMS: MenuItem[] = [
  // Visão Geral
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    href: '/dashboard',
    description: 'Visão geral'
  },
  
  // Operações Principais
  {
    id: 'conversas',
    label: 'Conversas',
    icon: MessageCircle,
    href: '/conversas',
    description: 'WhatsApp',
    badge: '12'
  },
  {
    id: 'clientes',
    label: 'Clientes',
    icon: Users,
    href: '/clientes',
    description: 'Base de dados'
  },
  {
    id: 'agendamentos',
    label: 'Agendamentos',
    icon: Calendar,
    href: '/agendamentos',
    description: 'Agenda',
    badge: '3'
  },
  {
    id: 'bloqueados',
    label: 'Bloqueados',
    icon: UserX,
    href: '/bloqueados',
    description: 'Horários'
  },
  
  // Análise
  {
    id: 'relatorios',
    label: 'Relatórios',
    icon: FileText,
    href: '/relatorios',
    description: 'Analytics'
  },
  
  // Configurações e Suporte
  {
    id: 'configuracoes',
    label: 'Configurações',
    icon: Settings,
    href: '/configuracoes',
    description: 'Sistema'
  },
  {
    id: 'suporte',
    label: 'Suporte',
    icon: HelpCircle,
    href: '/suporte',
    description: 'Ajuda & FAQ'
  },
  
  // Perfil do Usuário
  {
    id: 'perfil',
    label: 'Perfil',
    icon: UserIcon,
    href: '/perfil',
    description: 'Meu perfil'
  }
];

export const ADMIN_MENU_ITEMS: MenuItem[] = [
  {
    id: 'admin',
    label: 'Administração',
    icon: Shield,
    href: '/admin',
    description: 'Painel admin',
    adminOnly: true
  },
  {
    id: 'admin-users',
    label: 'Usuários',
    icon: Users,
    href: '/admin/usuarios',
    description: 'Gestão de usuários',
    adminOnly: true
  },
  {
    id: 'admin-backup',
    label: 'Backup',
    icon: Database,
    href: '/admin/backup',
    description: 'Sistema de backup',
    adminOnly: true
  }
];

export function getMenuItemsForUser(user: User | null): MenuItem[] {
  const baseItems = [...MENU_ITEMS];
  
  if (user?.role === 'admin') {
    baseItems.push(...ADMIN_MENU_ITEMS);
  }
  
  return baseItems;
}
