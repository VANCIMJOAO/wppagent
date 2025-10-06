/**
 * 🚀 SIDEBAR HEADER - FASE 3 REFATORAÇÃO
 * ========================================
 * 
 * Cabeçalho do sidebar com informações do usuário.
 * Extraído do sidebar.tsx para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { SidebarHeaderProps } from './types';

export function SidebarHeader({ user, onLogout }: SidebarHeaderProps) {
  if (!user) {
    return (
      <div className="px-4 py-5 border-b">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse" />
          <div className="space-y-2 flex-1">
            <div className="h-4 bg-gray-200 rounded animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-2/3 animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role.toLowerCase()) {
      case 'admin':
        return 'default' as const;
      case 'manager':
        return 'secondary' as const;
      case 'user':
        return 'outline' as const;
      default:
        return 'outline' as const;
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role.toLowerCase()) {
      case 'admin':
        return 'Administrador';
      case 'manager':
        return 'Gerente';
      case 'user':
        return 'Usuário';
      default:
        return role;
    }
  };

  return (
    <div className="px-4 py-5 border-b bg-gradient-to-br from-white to-gray-50/50">
      <div className="flex items-center gap-3 group">
        <div className="relative">
          <Avatar className="h-11 w-11 ring-2 ring-primary/10 transition-all duration-300 group-hover:ring-primary/30 group-hover:scale-105">
            <AvatarImage src={user.avatar_url} alt={user.name} />
            <AvatarFallback className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground text-sm font-bold">
              {getInitials(user.name)}
            </AvatarFallback>
          </Avatar>
          <div className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 bg-green-500 rounded-full border-2 border-white shadow-sm" />
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-gray-900 truncate mb-1 tracking-tight">
            {user.name}
          </p>
          <p className="text-xs text-gray-500 truncate mb-2 font-medium">
            {user.email}
          </p>
          <Badge 
            variant={getRoleBadgeVariant(user.role)}
            className="text-xs px-2.5 py-0.5 font-semibold shadow-sm"
          >
            {getRoleLabel(user.role)}
          </Badge>
        </div>
      </div>
    </div>
  );
}
