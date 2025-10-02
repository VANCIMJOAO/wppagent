"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Trash2, Users, MessageSquare, Calendar, Database } from 'lucide-react';
import { toast } from 'sonner';
import type { Client } from '@/types/api';

interface DeleteClientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  client: Client | null;
  isLoading?: boolean;
}

export default function DeleteClientModal({
  isOpen,
  onClose,
  onConfirm,
  client,
  isLoading = false
}: DeleteClientModalProps) {
  const handleConfirm = async () => {
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      console.error('Erro ao excluir cliente:', error);
      toast.error('Erro ao excluir cliente');
    }
  };

  if (!client) {
    return null;
  }

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            Confirmar Exclusão de Cliente
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-3">
            <p>
              Tem certeza que deseja excluir o cliente <strong>{client.nome}</strong>?
            </p>
            
            {/* Informações do cliente */}
            <div className="bg-gray-50 p-3 rounded-md space-y-2">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium">Cliente:</span>
                <span className="text-sm">{client.nome}</span>
              </div>
              {client.telefone && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">Telefone:</span>
                  <span className="text-sm">{client.telefone}</span>
                </div>
              )}
              {client.email && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">Email:</span>
                  <span className="text-sm">{client.email}</span>
                </div>
              )}
            </div>

            {/* Aviso sobre dados relacionados */}
            <div className="bg-red-50 border border-red-200 p-3 rounded-md">
              <div className="flex items-start gap-2">
                <Database className="h-4 w-4 text-red-600 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-red-800">
                    ⚠️ Dados Relacionados Serão Afetados
                  </p>
                  <div className="text-xs text-red-700 space-y-1">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-3 w-3" />
                      <span>Conversas: {client.total_conversations || 0}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-3 w-3" />
                      <span>Mensagens: {client.total_messages || 0}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-3 w-3" />
                      <span>Agendamentos: {client.total_appointments || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="text-sm text-red-600 font-medium">
              ⚠️ Esta ação não pode ser desfeita e pode afetar o histórico de atendimento.
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={isLoading}
            className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Excluindo...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Trash2 className="h-4 w-4" />
                Excluir Cliente
              </div>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}



