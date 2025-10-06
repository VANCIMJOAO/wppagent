'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  Search, 
  Plus, 
  MoreHorizontal, 
  Edit, 
  Trash2, 
  Eye,
  CheckCircle,
  Clock,
  XCircle,
  FileText,
  MessageSquare,
  Calendar,
  ShoppingCart,
  AlertCircle
} from 'lucide-react';
import { TemplateModal } from '@/components/templates/TemplateModal';
import { DeleteTemplateModal } from '@/components/templates/DeleteTemplateModal';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { useToast } from '@/hooks/use-toast';
import { debugLog } from '@/lib/debug';

// Tipos
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

interface TemplateFilters {
  search: string;
  categoria: string;
  status: string;
  linguagem: string;
}

const categoriaLabels = {
  marketing: 'Marketing',
  transacional: 'Transacional',
  autenticacao: 'Autenticação',
  agendamento: 'Agendamento',
  lembrete: 'Lembrete',
  // Mapear categorias da API
  welcome: 'Boas-vindas',
  appointment: 'Agendamento',
  reminder: 'Lembrete',
  cancellation: 'Cancelamento'
};

const categoriaIcons = {
  marketing: MessageSquare,
  transacional: ShoppingCart,
  autenticacao: AlertCircle,
  agendamento: Calendar,
  lembrete: Clock,
  // Mapear categorias da API
  welcome: MessageSquare,
  appointment: Calendar,
  reminder: Clock,
  cancellation: XCircle
};

const statusLabels = {
  aprovado: 'Aprovado',
  pendente: 'Pendente',
  rejeitado: 'Rejeitado',
  // Mapear status da API
  approved: 'Aprovado',
  pending: 'Pendente',
  rejected: 'Rejeitado'
};

const statusColors = {
  aprovado: 'bg-green-100 text-green-800',
  pendente: 'bg-yellow-100 text-yellow-800',
  rejeitado: 'bg-red-100 text-red-800',
  // Mapear status da API
  approved: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  rejected: 'bg-red-100 text-red-800'
};

const linguagemLabels = {
  'pt-BR': 'Português (BR)',
  'en-US': 'English (US)',
  'es-ES': 'Español (ES)'
};

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<TemplateFilters>({
    search: '',
    categoria: 'all',
    status: 'all',
    linguagem: 'all'
  });
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [isEdit, setIsEdit] = useState(false);
  const { toast } = useToast();

  // Carregar templates do backend (PostgreSQL)
  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/templates', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Erro ao carregar templates: ${response.status}`);
      }

      const data = await response.json();
      debugLog.success('Templates carregados:', data);
      debugLog.info('🔍 Estrutura dos dados:', JSON.stringify(data, null, 2));
      
      if (data.success && data.data) {
        debugLog.info('📝 Primeiro template:', data.data[0]);
        // Mapear dados para o formato esperado
        const mappedTemplates = data.data.map((template: any) => ({
          id: template.id,
          nome: template.name || template.nome,
          categoria: template.category || template.categoria,
          linguagem: template.language || template.linguagem,
          conteudo: template.content || template.conteudo,
          status: template.status,
          variaveis: template.variables || template.variaveis || [],
          created_at: template.created_at,
          aprovado_em: template.approved_at || template.aprovado_em
        }));
        debugLog.info('📝 Templates mapeados:', mappedTemplates);
        setTemplates(mappedTemplates);
      } else {
        throw new Error('Dados de templates não encontrados');
      }
    } catch (error) {
      debugLog.error('Erro ao carregar templates:', error);
      toast({
        title: 'Erro',
        description: 'Falha ao carregar templates',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Filtrar templates
  const filteredTemplates = templates.filter(template => {
    const matchesSearch = !filters.search || 
      template.nome.toLowerCase().includes(filters.search.toLowerCase()) ||
      template.conteudo.toLowerCase().includes(filters.search.toLowerCase());
    
    const matchesCategoria = filters.categoria === 'all' || template.categoria === filters.categoria;
    const matchesStatus = filters.status === 'all' || template.status === filters.status;
    const matchesLinguagem = filters.linguagem === 'all' || template.linguagem === filters.linguagem;
    
    return matchesSearch && matchesCategoria && matchesStatus && matchesLinguagem;
  });

  // Handlers
  const handleCreateTemplate = () => {
    setSelectedTemplate(null);
    setIsEdit(false);
    setShowTemplateModal(true);
  };

  const handleEditTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setIsEdit(true);
    setShowTemplateModal(true);
  };

  const handleDeleteTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setShowDeleteModal(true);
  };

  const handleViewTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setIsEdit(false);
    setShowTemplateModal(true);
  };

  const handleTemplateSaved = (savedTemplate: Template) => {
    if (isEdit) {
      setTemplates(prev => prev.map(t => t.id === savedTemplate.id ? savedTemplate : t));
      toast({
        title: 'Sucesso',
        description: 'Template atualizado com sucesso'
      });
    } else {
      setTemplates(prev => [...prev, { ...savedTemplate, id: Date.now() }]);
      toast({
        title: 'Sucesso',
        description: 'Template criado com sucesso'
      });
    }
    setShowTemplateModal(false);
  };

  const handleTemplateDeleted = (templateId: number) => {
    setTemplates(prev => prev.filter(t => t.id !== templateId));
    setShowDeleteModal(false);
    toast({
      title: 'Sucesso',
      description: 'Template removido com sucesso'
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'aprovado':
      case 'approved': return <CheckCircle className="h-4 w-4" />;
      case 'pendente':
      case 'pending': return <Clock className="h-4 w-4" />;
      case 'rejeitado':
      case 'rejected': return <XCircle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const getCategoriaIcon = (categoria: string) => {
    const Icon = categoriaIcons[categoria as keyof typeof categoriaIcons];
    if (!Icon) {
      return <MessageSquare className="h-4 w-4" />; // Ícone padrão
    }
    return <Icon className="h-4 w-4" />;
  };

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  return (
    <RoleGuard requiredRole="admin">
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Templates WhatsApp</h1>
          <p className="text-muted-foreground">
            Gerencie templates de mensagens para WhatsApp Business
          </p>
        </div>
        <Button onClick={handleCreateTemplate}>
          <Plus className="h-4 w-4 mr-2" />
          Novo Template
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nome ou conteúdo..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="pl-10"
              />
            </div>
            
            <Select
              value={filters.categoria}
              onValueChange={(value) => setFilters(prev => ({ ...prev, categoria: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Categoria" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas as categorias</SelectItem>
                <SelectItem value="marketing">Marketing</SelectItem>
                <SelectItem value="transacional">Transacional</SelectItem>
                <SelectItem value="autenticacao">Autenticação</SelectItem>
                <SelectItem value="agendamento">Agendamento</SelectItem>
                <SelectItem value="lembrete">Lembrete</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.status}
              onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os status</SelectItem>
                <SelectItem value="aprovado">Aprovado</SelectItem>
                <SelectItem value="pendente">Pendente</SelectItem>
                <SelectItem value="rejeitado">Rejeitado</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.linguagem}
              onValueChange={(value) => setFilters(prev => ({ ...prev, linguagem: value }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Linguagem" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas as linguagens</SelectItem>
                <SelectItem value="pt-BR">Português (BR)</SelectItem>
                <SelectItem value="en-US">English (US)</SelectItem>
                <SelectItem value="es-ES">Español (ES)</SelectItem>
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              onClick={() => setFilters({ search: '', categoria: 'all', status: 'all', linguagem: 'all' })}
            >
              Limpar Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Templates */}
      <Card>
        <CardHeader>
          <CardTitle>
            Templates ({filteredTemplates.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Categoria</TableHead>
                  <TableHead>Linguagem</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Variáveis</TableHead>
                  <TableHead>Criado em</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTemplates.map((template) => (
                  <TableRow key={template.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        {template.nome}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getCategoriaIcon(template.categoria)}
                        <span>{categoriaLabels[template.categoria]}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {linguagemLabels[template.linguagem]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(template.status)}
                        <Badge className={statusColors[template.status]}>
                          {statusLabels[template.status]}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {template.variaveis?.map((variavel, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {variavel}
                          </Badge>
                        )) || <span className="text-gray-400 text-xs">Nenhuma variável</span>}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(template.created_at)}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewTemplate(template)}>
                            <Eye className="h-4 w-4 mr-2" />
                            Visualizar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleEditTemplate(template)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Editar
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteTemplate(template)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Excluir
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Modais */}
      {showTemplateModal && (
        <TemplateModal
          template={selectedTemplate}
          isEdit={isEdit}
          onClose={() => setShowTemplateModal(false)}
          onSave={handleTemplateSaved}
        />
      )}

      {showDeleteModal && selectedTemplate && (
        <DeleteTemplateModal
          template={selectedTemplate}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={handleTemplateDeleted}
        />
      )}
      </div>
    </RoleGuard>
  );
}
