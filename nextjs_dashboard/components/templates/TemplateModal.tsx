'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  MessageSquare, 
  ShoppingCart, 
  AlertCircle, 
  Calendar, 
  Clock,
  FileText,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

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

interface TemplateModalProps {
  template?: Template | null;
  isEdit: boolean;
  onClose: () => void;
  onSave: (template: Template) => void;
}

const categoriaOptions = [
  { 
    value: 'marketing', 
    label: 'Marketing', 
    icon: MessageSquare, 
    description: 'Promoções, ofertas e campanhas' 
  },
  { 
    value: 'transacional', 
    label: 'Transacional', 
    icon: ShoppingCart, 
    description: 'Confirmações, cancelamentos e atualizações' 
  },
  { 
    value: 'autenticacao', 
    label: 'Autenticação', 
    icon: AlertCircle, 
    description: 'Códigos de verificação e segurança' 
  },
  { 
    value: 'agendamento', 
    label: 'Agendamento', 
    icon: Calendar, 
    description: 'Confirmações e lembretes de consultas' 
  },
  { 
    value: 'lembrete', 
    label: 'Lembrete', 
    icon: Clock, 
    description: 'Lembretes e notificações' 
  }
];

const linguagemOptions = [
  { value: 'pt-BR', label: 'Português (Brasil)' },
  { value: 'en-US', label: 'English (United States)' },
  { value: 'es-ES', label: 'Español (España)' }
];

export function TemplateModal({ template, isEdit, onClose, onSave }: TemplateModalProps) {
  const [formData, setFormData] = useState({
    nome: '',
    categoria: 'marketing' as 'marketing' | 'transacional' | 'autenticacao' | 'agendamento' | 'lembrete',
    linguagem: 'pt-BR' as 'pt-BR' | 'en-US' | 'es-ES',
    conteudo: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [variaveis, setVariaveis] = useState<string[]>([]);
  const [previewMode, setPreviewMode] = useState(false);
  const { toast } = useToast();

  // Carregar dados do template se estiver editando
  useEffect(() => {
    if (isEdit && template) {
      setFormData({
        nome: template.nome,
        categoria: template.categoria,
        linguagem: template.linguagem,
        conteudo: template.conteudo
      });
      setVariaveis(template.variaveis);
    }
  }, [isEdit, template]);

  // Extrair variáveis do conteúdo
  const extractVariables = (content: string) => {
    const regex = /\{\{(\d+)\}\}/g;
    const matches = content.match(regex);
    return matches ? [...new Set(matches)].sort() : [];
  };

  // Atualizar variáveis quando o conteúdo mudar
  useEffect(() => {
    const extractedVars = extractVariables(formData.conteudo);
    setVariaveis(extractedVars);
  }, [formData.conteudo]);

  // Validar formulário
  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.nome.trim()) {
      newErrors.nome = 'Nome é obrigatório';
    }

    if (!formData.conteudo.trim()) {
      newErrors.conteudo = 'Conteúdo é obrigatório';
    } else if (formData.conteudo.length < 10) {
      newErrors.conteudo = 'Conteúdo deve ter pelo menos 10 caracteres';
    } else if (formData.conteudo.length > 1024) {
      newErrors.conteudo = 'Conteúdo deve ter no máximo 1024 caracteres';
    }

    // Verificar se as variáveis estão em sequência
    const extractedVars = extractVariables(formData.conteudo);
    const expectedVars = Array.from({ length: extractedVars.length }, (_, i) => `{{${i + 1}}}`);
    const hasSequentialVars = extractedVars.every((_, i) => extractedVars[i] === expectedVars[i]);
    
    if (extractedVars.length > 0 && !hasSequentialVars) {
      newErrors.conteudo = 'Variáveis devem estar em sequência: {{1}}, {{2}}, {{3}}, etc.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Salvar template
  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    const templateData: Template = {
      id: template?.id || Date.now(), // Gerar ID temporário para novos templates
      nome: formData.nome.trim(),
      categoria: formData.categoria,
      linguagem: formData.linguagem,
      conteudo: formData.conteudo.trim(),
      status: isEdit ? template?.status || 'pendente' : 'pendente',
      variaveis: variaveis,
      created_at: template?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
      aprovado_em: template?.aprovado_em,
      rejeitado_em: template?.rejeitado_em,
      motivo_rejeicao: template?.motivo_rejeicao
    };

    onSave(templateData);
  };

  // Gerar preview do template
  const generatePreview = () => {
    let preview = formData.conteudo;
    
    // Substituir variáveis por exemplos
    const examples = ['João', 'Limpeza de Pele', '15/10/2025', '14:30', 'R$ 150,00', 'Código: 123456'];
    variaveis.forEach((variavel, index) => {
      const example = examples[index] || `Exemplo${index + 1}`;
      preview = preview.replace(new RegExp(variavel.replace(/[{}]/g, '\\$&'), 'g'), example);
    });

    return preview;
  };

  const getCategoriaIcon = (categoria: string) => {
    const option = categoriaOptions.find(opt => opt.value === categoria);
    return option ? option.icon : FileText;
  };

  const getCategoriaDescription = (categoria: string) => {
    const option = categoriaOptions.find(opt => opt.value === categoria);
    return option ? option.description : '';
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? 'Editar Template' : 'Novo Template'}
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Formulário */}
          <div className="space-y-6">
            {/* Nome */}
            <div className="space-y-2">
              <Label htmlFor="nome">Nome do Template *</Label>
              <Input
                id="nome"
                value={formData.nome}
                onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                placeholder="Ex: Confirmação de Agendamento"
                className={errors.nome ? 'border-red-500' : ''}
              />
              {errors.nome && (
                <p className="text-sm text-red-500">{errors.nome}</p>
              )}
            </div>

            {/* Categoria */}
            <div className="space-y-2">
              <Label>Categoria *</Label>
              <Select
                value={formData.categoria}
                onValueChange={(value: any) => setFormData(prev => ({ ...prev, categoria: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categoriaOptions.map((option) => {
                    const Icon = option.icon;
                    return (
                      <SelectItem key={option.value} value={option.value}>
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4" />
                          <div>
                            <div className="font-medium">{option.label}</div>
                            <div className="text-sm text-muted-foreground">
                              {option.description}
                            </div>
                          </div>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                {getCategoriaDescription(formData.categoria)}
              </p>
            </div>

            {/* Linguagem */}
            <div className="space-y-2">
              <Label>Linguagem *</Label>
              <Select
                value={formData.linguagem}
                onValueChange={(value: any) => setFormData(prev => ({ ...prev, linguagem: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {linguagemOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Conteúdo */}
            <div className="space-y-2">
              <Label htmlFor="conteudo">Conteúdo da Mensagem *</Label>
              <Textarea
                id="conteudo"
                value={formData.conteudo}
                onChange={(e) => setFormData(prev => ({ ...prev, conteudo: e.target.value }))}
                placeholder="Digite o conteúdo do template usando {{1}}, {{2}}, etc. para variáveis"
                className={`min-h-[120px] ${errors.conteudo ? 'border-red-500' : ''}`}
              />
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>{formData.conteudo.length}/1024 caracteres</span>
                <span>{variaveis.length} variável{variaveis.length !== 1 ? 'is' : ''}</span>
              </div>
              {errors.conteudo && (
                <p className="text-sm text-red-500">{errors.conteudo}</p>
              )}
            </div>

            {/* Variáveis detectadas */}
            {variaveis.length > 0 && (
              <div className="space-y-2">
                <Label>Variáveis Detectadas</Label>
                <div className="flex flex-wrap gap-2">
                  {variaveis.map((variavel, index) => (
                    <Badge key={index} variant="secondary">
                      {variavel}
                    </Badge>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground">
                  As variáveis serão substituídas por dados reais quando o template for usado.
                </p>
              </div>
            )}

            {/* Avisos */}
            {isEdit && template?.status === 'aprovado' && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="flex items-center gap-2 text-yellow-800">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="font-medium">Template Aprovado</span>
                </div>
                <p className="text-sm text-yellow-700 mt-1">
                  Este template já foi aprovado pelo WhatsApp. Qualquer alteração 
                  precisará ser re-aprovada.
                </p>
              </div>
            )}
          </div>

          {/* Preview */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Preview</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setPreviewMode(!previewMode)}
              >
                {previewMode ? (
                  <>
                    <Eye className="h-4 w-4 mr-2" />
                    Ver Código
                  </>
                ) : (
                  <>
                    <Eye className="h-4 w-4 mr-2" />
                    Ver Preview
                  </>
                )}
              </Button>
            </div>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  {getCategoriaIcon(formData.categoria) && (
                    <div className="p-1 bg-gray-100 rounded">
                      {(() => {
                        const Icon = getCategoriaIcon(formData.categoria);
                        return <Icon className="h-4 w-4" />;
                      })()}
                    </div>
                  )}
                  {formData.nome || 'Nome do Template'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {previewMode ? (
                  <div className="space-y-2">
                    <div className="bg-gray-50 p-3 rounded text-sm font-mono">
                      {formData.conteudo || 'Conteúdo do template aparecerá aqui...'}
                    </div>
                    {variaveis.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-2">Variáveis:</p>
                        <div className="flex flex-wrap gap-1">
                          {variaveis.map((variavel, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {variavel}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                          W
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-medium text-green-800 mb-1">
                            WhatsApp Business
                          </div>
                          <div className="text-sm text-green-700 whitespace-pre-wrap">
                            {generatePreview() || 'Preview do template aparecerá aqui...'}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-xs text-muted-foreground">
                      <p>• Linguagem: {linguagemOptions.find(opt => opt.value === formData.linguagem)?.label}</p>
                      <p>• Categoria: {categoriaOptions.find(opt => opt.value === formData.categoria)?.label}</p>
                      <p>• Status: {isEdit ? (template?.status || 'Pendente') : 'Pendente'}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Botões */}
        <div className="flex justify-end gap-3 pt-6 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handleSave}>
            {isEdit ? 'Salvar Alterações' : 'Criar Template'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
