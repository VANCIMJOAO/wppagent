'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  AlertTriangle, 
  Shield, 
  User, 
  Eye as EyeIcon,
  Trash2
} from 'lucide-react';

interface User {
  id: number;
  nome: string;
  email: string;
  role: 'admin' | 'atendente' | 'visualizador';
  status: 'ativo' | 'inativo';
  ultima_atividade: string;
  created_at: string;
  updated_at?: string;
}

interface DeleteUserModalProps {
  user: User;
  onClose: () => void;
  onConfirm: (userId: number) => void;
}

const roleLabels = {
  admin: 'Administrador',
  atendente: 'Atendente',
  visualizador: 'Visualizador'
};

const roleIcons = {
  admin: Shield,
  atendente: User,
  visualizador: EyeIcon
};

export function DeleteUserModal({ user, onClose, onConfirm }: DeleteUserModalProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    
    try {
      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 1000));
      onConfirm(user.id);
    } catch (error) {
      console.error('Erro ao deletar usuário:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const RoleIcon = roleIcons[user.role];

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <Trash2 className="h-5 w-5" />
            Excluir Usuário
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Aviso de perigo */}
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              <strong>Atenção:</strong> Esta ação não pode ser desfeita. O usuário será 
              permanentemente removido do sistema.
            </AlertDescription>
          </Alert>

          {/* Informações do usuário */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-200 rounded-full">
                <RoleIcon className="h-5 w-5 text-gray-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{user.nome}</h3>
                <p className="text-sm text-gray-600">{user.email}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                    {roleLabels[user.role]}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    user.status === 'ativo' 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {user.status === 'ativo' ? 'Ativo' : 'Inativo'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Avisos específicos */}
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">Consequências da exclusão:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• O usuário não poderá mais fazer login</li>
              <li>• Todos os dados associados serão removidos</li>
              <li>• Histórico de atividades será perdido</li>
              {user.role === 'admin' && (
                <li className="text-red-600 font-medium">
                  • ⚠️ Este é um usuário administrador
                </li>
              )}
            </ul>
          </div>

          {/* Confirmação de segurança */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <p className="text-sm text-yellow-800">
              <strong>Confirmação necessária:</strong> Digite <code className="bg-yellow-100 px-1 rounded">EXCLUIR</code> para confirmar a exclusão.
            </p>
          </div>
        </div>

        {/* Botões */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="outline" onClick={onClose} disabled={isDeleting}>
            Cancelar
          </Button>
          <Button 
            variant="destructive" 
            onClick={handleConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Excluindo...
              </>
            ) : (
              <>
                <Trash2 className="h-4 w-4 mr-2" />
                Excluir Usuário
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
