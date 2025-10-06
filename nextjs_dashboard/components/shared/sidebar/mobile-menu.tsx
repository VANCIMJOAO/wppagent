/**
 * 🚀 MOBILE MENU - FASE 3 REFATORAÇÃO
 * ======================================
 * 
 * Menu mobile do sidebar.
 * Extraído do sidebar.tsx para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { X, LogOut } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { MobileMenuProps } from './types';
import { SidebarMenuItem } from './sidebar-menu-item';

export function MobileMenu({
  isOpen,
  onClose,
  user,
  menuItems,
  currentPath,
  onItemClick,
  onLogout
}: MobileMenuProps) {
  if (!isOpen) return null;

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />
      
      {/* Menu */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-2xl animate-in slide-in-from-left duration-300">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-5 border-b bg-gradient-to-br from-primary/5 to-transparent">
          <h2 className="text-lg font-bold text-gray-900">Menu</h2>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="hover:bg-red-50 hover:text-red-600 transition-all duration-200"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* User Info */}
        {user && (
          <div className="px-4 py-5 border-b bg-gradient-to-br from-white to-gray-50/50">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Avatar className="h-11 w-11 ring-2 ring-primary/10">
                  <AvatarImage src={user.avatar_url} alt={user.name} />
                  <AvatarFallback className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground text-sm font-bold">
                    {getInitials(user.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 bg-green-500 rounded-full border-2 border-white shadow-sm" />
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-gray-900 truncate mb-1">
                  {user.name}
                </p>
                <p className="text-xs text-gray-500 truncate mb-2 font-medium">
                  {user.email}
                </p>
                <Badge variant="outline" className="text-xs font-semibold shadow-sm">
                  {user.role}
                </Badge>
              </div>
            </div>
          </div>
        )}

        {/* Menu Items */}
        <nav className="flex-1 space-y-2 px-3 py-4 overflow-y-auto">
          {menuItems.map((item) => {
            const isActive = currentPath === item.href;
            
            return (
              <div key={item.id}>
                <SidebarMenuItem
                  item={item}
                  isActive={isActive}
                  isCollapsed={false}
                  onClick={() => {
                    onItemClick(item.href);
                    onClose();
                  }}
                />
              </div>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t bg-gradient-to-br from-gray-50/50 to-white">
          <Button 
            variant="ghost" 
            className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50 font-semibold transition-all duration-200 hover:scale-105 h-11"
            onClick={onLogout}
          >
            <LogOut className="h-5 w-5 mr-3" />
            Sair
          </Button>
        </div>
      </div>
    </div>
  );
}
