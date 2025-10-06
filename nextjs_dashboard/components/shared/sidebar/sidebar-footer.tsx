/**
 * 🚀 SIDEBAR FOOTER - FASE 3 REFATORAÇÃO
 * ========================================
 * 
 * Rodapé do sidebar com ações do usuário.
 * Extraído do sidebar.tsx para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React from 'react';
import { LogOut, Bell, HelpCircle } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarFooterProps } from './types';

export function SidebarFooter({ user, onLogout }: SidebarFooterProps) {
  if (!user) {
    return (
      <div className="px-3 py-3 border-t">
        <div className="flex justify-center">
          <div className="w-8 h-8 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="px-3 py-3 border-t bg-gradient-to-br from-gray-50/50 to-white">
      <div className="flex items-center justify-between gap-1">
        {/* Notificações */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="ghost" 
              size="sm" 
              className="relative hover:bg-primary/10 hover:text-primary transition-all duration-200 hover:scale-110"
            >
              <Bell className="h-4 w-4" />
              <Badge 
                variant="destructive" 
                className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-xs font-bold shadow-lg animate-pulse"
              >
                3
              </Badge>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notificações</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">Nova mensagem</p>
                <p className="text-xs text-muted-foreground">
                  Você recebeu uma nova mensagem no WhatsApp
                </p>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">Agendamento confirmado</p>
                <p className="text-xs text-muted-foreground">
                  Cliente confirmou agendamento para amanhã
                </p>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">Sistema atualizado</p>
                <p className="text-xs text-muted-foreground">
                  Nova versão disponível
                </p>
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Ajuda */}
        <Button 
          variant="ghost" 
          size="sm"
          className="hover:bg-blue-50 hover:text-blue-600 transition-all duration-200 hover:scale-110"
        >
          <HelpCircle className="h-4 w-4" />
        </Button>

        {/* Menu do usuário */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="ghost" 
              size="sm"
              className="hover:bg-red-50 hover:text-red-600 transition-all duration-200 hover:scale-110"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Minha Conta</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              Perfil
            </DropdownMenuItem>
            <DropdownMenuItem>
              Configurações
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem 
              onClick={onLogout}
              className="text-red-600 focus:text-red-600"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sair
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
