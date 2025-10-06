/**
 * 🚀 SIDEBAR CONSOLIDADO - FASE 3 REFATORAÇÃO
 * ==============================================
 * 
 * Sidebar consolidado que usa componentes modulares.
 * Substitui o sidebar.tsx (557 linhas) por uma implementação modular.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { cn } from '@/lib/utils';
import { 
  SidebarHeader, 
  SidebarMenu, 
  SidebarFooter, 
  MobileMenu,
  getMenuItemsForUser
} from './index';
import type { SidebarProps, User } from './types';
import { debugLog } from '@/lib/debug';

export default function ConsolidatedSidebar({ children }: SidebarProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const router = useRouter();
  const pathname = usePathname();

  // Carregar dados reais do usuário
  useEffect(() => {
    const loadUser = async () => {
      try {
        const response = await fetch('/api/users/me', {
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Erro ao carregar dados do usuário');
        }
        
        const data = await response.json();
        
        if (data.success && data.user) {
          setUser(data.user);
        }
      } catch (error) {
        debugLog.error('Erro ao carregar usuário:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  // Verificar se é mobile
  useEffect(() => {
    const checkMobile = () => {
      if (window.innerWidth < 1024) {
        setIsCollapsed(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleLogout = async () => {
    try {
      // Simular logout
      setUser(null);
      router.push('/login');
    } catch (error) {
      debugLog.error('Erro ao fazer logout:', error);
    }
  };

  const handleMenuItemClick = (href: string) => {
    router.push(href);
    setIsMobileMenuOpen(false); // Fechar menu mobile ao navegar
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  // Obter itens do menu baseado no usuário
  const menuItems = getMenuItemsForUser(user);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Desktop Sidebar */}
      <div className={cn(
        'hidden lg:flex lg:flex-col lg:bg-white lg:border-r lg:shadow-xl lg:h-screen',
        'lg:transition-all lg:duration-300 lg:ease-in-out',
        isCollapsed ? 'lg:w-16' : 'lg:w-64'
      )}>
        {/* Header - Fixo no topo */}
        <div className="flex-shrink-0">
          <SidebarHeader user={user} onLogout={handleLogout} />
        </div>

        {/* Menu - Com scroll */}
        <div className="flex-1 min-h-0">
          <SidebarMenu
            items={menuItems}
            currentPath={pathname}
            onItemClick={handleMenuItemClick}
            isCollapsed={isCollapsed}
          />
        </div>

        {/* Footer - Fixo no fundo */}
        <div className="flex-shrink-0">
          <SidebarFooter user={user} onLogout={handleLogout} />
          
          {/* Toggle Button */}
          <div className="px-3 py-3 border-t bg-gradient-to-br from-gray-50/50 to-white">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSidebar}
              className="w-full justify-center h-9 hover:bg-primary/10 hover:text-primary transition-all duration-200 hover:scale-105 font-medium"
            >
              {isCollapsed ? (
                <Menu className="h-4 w-4" />
              ) : (
                <>
                  <X className="h-4 w-4 mr-2" />
                  {!isCollapsed && <span className="text-xs">Recolher</span>}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 bg-white border-b w-full">
        <h1 className="text-lg font-semibold">Dashboard</h1>
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleMobileMenu}
        >
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      {/* Mobile Menu */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        user={user}
        menuItems={menuItems}
        currentPath={pathname}
        onItemClick={handleMenuItemClick}
        onLogout={handleLogout}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

// Export para compatibilidade
export { ConsolidatedSidebar as Sidebar };
