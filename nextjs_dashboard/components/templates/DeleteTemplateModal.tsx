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
import { Badge } from '@/components/ui/badge';
import { 
  AlertTriangle, 
  Trash2,
  FileText,
  MessageSquare,
  ShoppingCart,
  AlertCircle,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  Clock as ClockIcon
} from 'lucide-react';

interface Template {
  id: number;
  nome: string;
  categoria: 'marketing' | 'transacional' | 'autenticacao' | 'agendamento' | 'lembrete';
  linguagem: 'pt-BR' | 'en-US' | 'es-ES';
  conteudo: string;
  status: 'aprovado' | 'pendente' | 'rejeitado';
  variaveis: string[];
  created_at: string;
  updated_at?: string;
  aprovado_em?: string;
  rejeitado_em?: string;
  motivo_rejeicao?: string;
}

interface DeleteTemplateModalProps {
  template: Template;
  onClose: () => void;
  onConfirm: (templateId: number) => void;
}

const categoriaLabels = {
  marketing: 'Marketing',
  transacional: 'Transacional',
  autenticacao: 'Autenticação',
  agendamento: 'Agendamento',
  lembrete: 'Lembrete'
};

const categoriaIcons = {
  marketing: MessageSquare,
  transacional: ShoppingCart,
  autenticacao: AlertCircle,
  agendamento: Calendar,
  lembrete: Clock
};

const statusLabels = {
  aprovado: 'Aprovado',
  pendente: 'Pendente',
  rejeitado: 'Rejeitado'
};

const statusColors = {
  aprovado: 'bg-green-100 text-green-800',
  pendente: 'bg-yellow-100 text-yellow-800',
  rejeitado: 'bg-red-100 text-red-800'
};

const linguagemLabels = {
  'pt-BR': 'Português (BR)',
  'en-US': 'English (US)',
  'es-ES': 'Español (ES)'
};

export function DeleteTemplateModal({ template, onClose, onConfirm }: DeleteTemplateModalProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    
    try {
      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 1000));
      onConfirm(template.id);
    } catch (error) {
      console.error('Erro ao deletar template:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const CategoriaIcon = categoriaIcons[template.categoria];
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'aprovado': return <CheckCircle className="h-4 w-4" />;
      case 'pendente': return <ClockIcon className="h-4 w-4" />;
      case 'rejeitado': return <XCircle className="h-4 w-4" />;
      default: return <ClockIcon className="h-4 w-4" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-600">
            <Trash2 className="h-5 w-5" />
            Excluir Template
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Aviso de perigo */}
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              <strong>Atenção:</strong> Esta ação não pode ser desfeita. O template será 
              permanentemente removido do sistema.
            </AlertDescription>
          </Alert>

          {/* Informações do template */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-gray-200 rounded-full">
                <CategoriaIcon className="h-5 w-5 text-gray-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{template.nome}</h3>
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {template.conteudo}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {categoriaLabels[template.categoria]}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {linguagemLabels[template.linguagem]}
                  </Badge>
                  <div className="flex items-center gap-1">
                    {getStatusIcon(template.status)}
                    <Badge className={`text-xs ${statusColors[template.status]}`}>
                      {statusLabels[template.status]}
                    </Badge>
                  </div>
                </div>
                {template.variaveis.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-500 mb-1">Variáveis:</p>
                    <div className="flex flex-wrap gap-1">
                      {template.variaveis.map((variavel, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {variavel}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Avisos específicos */}
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">Consequências da exclusão:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• O template não poderá mais ser usado em mensagens</li>
              <li>• Mensagens agendadas com este template serão canceladas</li>
              <li>• Histórico de uso será perdido</li>
              {template.status === 'aprovado' && (
                <li className="text-orange-600 font-medium">
                  • ⚠️ Este template está aprovado pelo WhatsApp
                </li>
              )}
              {template.status === 'pendente' && (
                <li className="text-yellow-600 font-medium">
                  • ⚠️ Este template está aguardando aprovação
                </li>
              )}
            </ul>
          </div>

          {/* Informações adicionais */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-sm text-blue-800">
              <p><strong>Criado em:</strong> {formatDate(template.created_at)}</p>
              {template.aprovado_em && (
                <p><strong>Aprovado em:</strong> {formatDate(template.aprovado_em)}</p>
              )}
              {template.rejeitado_em && (
                <p><strong>Rejeitado em:</strong> {formatDate(template.rejeitado_em)}</p>
              )}
              {template.motivo_rejeicao && (
                <p><strong>Motivo da rejeição:</strong> {template.motivo_rejeicao}</p>
              )}
            </div>
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
                Excluir Template
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
