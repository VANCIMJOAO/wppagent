"use client";

import { useState, useEffect } from 'react';
import {
  Card, CardHeader, CardTitle, CardContent
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Users,
  Search,
  Plus,
  Edit,
  Trash2,
  Phone,
  Mail,
  Calendar,
  Filter,
  MoreVertical,
  Eye,
  UserCheck,
  UserX,
  RefreshCw,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight
} from 'lucide-react';
import { useClients } from '@/hooks/useClients';
import type { Client } from '@/types/api';
import { NewClientForm } from '@/components/NewClientForm';
import EditClientModal from '@/components/clients/EditClientModal';
import DeleteClientModal from '@/components/clients/DeleteClientModal';
import ClientHistoryModal from '@/components/clients/ClientHistoryModal';
import { toast } from 'sonner';
import { debugLog } from '@/lib/debug';

export default function ClientesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('name');
  const [showNewClientForm, setShowNewClientForm] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  // Estados para modais
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Usar o hook personalizado para gerenciar dados dos clientes
  const {
    clients,
    loading,
    error,
    pagination,
    refetch,
    createClient,
    updateFilters
  } = useClients({
    search: searchTerm,
    status: statusFilter,
    sortBy: sortBy,
    limit: itemsPerPage,
    offset: (currentPage - 1) * itemsPerPage
  });

  // Atualizar filtros quando os valores mudarem
  useEffect(() => {
    updateFilters({
      search: searchTerm,
      status: statusFilter,
      sortBy: sortBy,
      limit: itemsPerPage,
      offset: (currentPage - 1) * itemsPerPage
    });
  }, [searchTerm, statusFilter, sortBy, currentPage, itemsPerPage, updateFilters]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter, sortBy]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'vip':
        return <Badge className="bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-md font-semibold">VIP</Badge>;
      case 'active':
        return <Badge className="bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-md font-semibold">Ativo</Badge>;
      case 'inactive':
        return <Badge className="bg-gradient-to-r from-gray-400 to-gray-600 text-white shadow-md font-semibold">Inativo</Badge>;
      default:
        return <Badge className="bg-gradient-to-r from-gray-400 to-gray-600 text-white shadow-md font-semibold">Desconhecido</Badge>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'vip':
        return (
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-md border-2 border-white">
            <UserCheck className="h-3.5 w-3.5 text-white" />
          </div>
        );
      case 'active':
        return (
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-md border-2 border-white">
            <UserCheck className="h-3.5 w-3.5 text-white" />
          </div>
        );
      case 'inactive':
        return (
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center shadow-md border-2 border-white">
            <UserX className="h-3.5 w-3.5 text-white" />
          </div>
        );
      default:
        return (
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center shadow-md border-2 border-white">
            <Users className="h-3.5 w-3.5 text-white" />
          </div>
        );
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const handleRefresh = () => {
    refetch();
  };

  const handleNewClient = async (clientData: { name: string; email?: string; phone: string }) => {
    const newClient = await createClient({
      name: clientData.name,
      email: clientData.email || '',
      phone: clientData.phone
    });
    if (newClient) {
      setShowNewClientForm(false);
    }
  };

  // Funções para modais
  const handleOpenEditModal = (client: Client) => {
    setSelectedClient(client);
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
    setSelectedClient(null);
  };

  const handleOpenDeleteModal = (client: Client) => {
    setSelectedClient(client);
    setIsDeleteModalOpen(true);
  };

  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setSelectedClient(null);
  };

  const handleOpenHistoryModal = (client: Client) => {
    setSelectedClient(client);
    setIsHistoryModalOpen(true);
  };

  const handleCloseHistoryModal = () => {
    setIsHistoryModalOpen(false);
    setSelectedClient(null);
  };

  const handleDeleteClient = async () => {
    if (!selectedClient) return;

    setIsDeleting(true);
    try {
      const response = await fetch(`/api/clients/${selectedClient.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erro ao excluir cliente');
      }

      toast.success('Cliente excluído com sucesso!');
      await refetch(); // Recarregar dados
      handleCloseDeleteModal();
    } catch (error) {
      debugLog.error('Erro ao excluir cliente:', error);
      toast.error(
        error instanceof Error 
          ? error.message 
          : 'Erro ao excluir cliente'
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const handleEditSuccess = async () => {
    await refetch(); // Recarregar dados após editar
  };

  // Calcular informações de paginação
  const totalPages = pagination?.total ? Math.ceil(pagination.total / itemsPerPage) : 0;
  const startItem = pagination?.total ? (currentPage - 1) * itemsPerPage + 1 : 0;
  const endItem = pagination?.total ? Math.min(currentPage * itemsPerPage, pagination.total) : 0;

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="space-y-8 p-6 bg-gradient-to-br from-gray-50 to-white min-h-screen" data-testid="clients-page">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 tracking-tight">Clientes</h1>
          <p className="text-gray-600 mt-2 text-lg">
            Gestão da base de clientes
            {pagination && (
              <span className="ml-2 inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 border border-blue-200 shadow-sm">
                {pagination.total} {pagination.total === 1 ? 'cliente' : 'clientes'}
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            onClick={handleRefresh} 
            disabled={loading}
            className="h-10 shadow-sm hover:shadow-md transition-all hover:scale-105"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button 
            onClick={() => setShowNewClientForm(true)}
            className="h-10 shadow-sm hover:shadow-md transition-all hover:scale-105 bg-gradient-to-r from-primary to-primary/90"
          >
            <Plus className="h-4 w-4 mr-2" />
            Novo Cliente
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-red-800">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">Erro ao carregar clientes:</span>
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-blue-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">Total</p>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-3xl font-bold text-gray-900">
                    {pagination?.total || clients.length}
                  </p>
                )}
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg">
                <Users className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-green-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">Ativos</p>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-3xl font-bold text-green-600">
                    {clients.filter(c => c.status === 'active').length}
                  </p>
                )}
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg">
                <UserCheck className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-purple-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">VIP</p>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-3xl font-bold text-purple-600">
                    {clients.filter(c => c.status === 'vip').length}
                  </p>
                )}
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg">
                <UserCheck className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] bg-gradient-to-br from-white to-gray-50/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-2">Inativos</p>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-3xl font-bold text-gray-600">
                    {clients.filter(c => c.status === 'inactive').length}
                  </p>
                )}
              </div>
              <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 shadow-lg">
                <UserX className="h-7 w-7 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3.5 text-gray-400" />
                <Input
                  placeholder="Buscar clientes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 h-11 border-gray-300 focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48 h-11 shadow-sm border-gray-300 hover:border-gray-400 transition-colors">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos os Status</SelectItem>
                <SelectItem value="active">Ativo</SelectItem>
                <SelectItem value="vip">VIP</SelectItem>
                <SelectItem value="inactive">Inativo</SelectItem>
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-48 h-11 shadow-sm border-gray-300 hover:border-gray-400 transition-colors">
                <SelectValue placeholder="Ordenar por" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Nome</SelectItem>
                <SelectItem value="registrationDate">Data de Cadastro</SelectItem>
                <SelectItem value="lastVisit">Última Visita</SelectItem>
                <SelectItem value="appointments">Número de Consultas</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Clientes */}
      <Card className="border-0 shadow-xl bg-gradient-to-br from-white to-gray-50">
        <CardHeader className="border-b bg-gradient-to-r from-gray-50 to-transparent pb-4">
          <CardTitle className="flex items-center gap-2 text-xl font-bold">
            <Users className="h-5 w-5 text-primary" />
            Lista de Clientes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {loading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center space-x-4 p-4 border rounded-lg">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-1/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                    <Skeleton className="h-8 w-20" />
                  </div>
                ))}
              </div>
            ) : clients.length === 0 ? (
              <div className="text-center py-12">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum cliente encontrado</h3>
                <p className="text-gray-600 mb-4">
                  {searchTerm || statusFilter !== 'all' 
                    ? 'Tente ajustar os filtros de busca'
                    : 'Comece adicionando seu primeiro cliente'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && (
                  <Button onClick={() => setShowNewClientForm(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Adicionar Cliente
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {clients.map((client) => (
                  <div
                    key={client.id}
                    className="flex items-center justify-between p-5 border-0 rounded-xl hover:shadow-lg transition-all duration-300 bg-white shadow-md hover:scale-[1.01]"
                  >
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="relative">
                        <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
                          <Users className="h-7 w-7 text-white" />
                        </div>
                        <div className="absolute -bottom-1 -right-1">
                          {getStatusIcon(client.status)}
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-bold text-gray-900 truncate">{client.nome}</h3>
                          {getStatusBadge(client.status)}
                        </div>
                        <div className="flex items-center flex-wrap gap-4 text-sm text-gray-600 mb-2">
                          {client.email && (
                            <span className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded-md">
                              <Mail className="h-3.5 w-3.5 flex-shrink-0" />
                              <span className="truncate">{client.email}</span>
                            </span>
                          )}
                          <span className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded-md">
                            <Phone className="h-3.5 w-3.5 flex-shrink-0" />
                            {client.telefone}
                          </span>
                          <span className="flex items-center gap-1.5 bg-gray-50 px-2 py-1 rounded-md">
                            <Calendar className="h-3.5 w-3.5 flex-shrink-0" />
                            {client.wa_id}
                          </span>
                        </div>
                        <div className="flex items-center flex-wrap gap-3 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <span className="font-semibold">Cadastrado:</span> {formatDate(client.created_at)}
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="font-semibold">Última visita:</span> {formatDate(client.last_interaction || null)}
                          </span>
                          <Badge variant="outline" className="font-semibold">
                            {client.total_appointments} consultas
                          </Badge>
                          <Badge variant="outline" className="font-semibold">
                            {client.total_conversations} conversas
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        title="Ver histórico"
                        onClick={() => handleOpenHistoryModal(client)}
                        className="hover:bg-green-50 hover:text-green-600 transition-all duration-200 hover:scale-110"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        title="Editar cliente"
                        onClick={() => handleOpenEditModal(client)}
                        className="hover:bg-blue-50 hover:text-blue-600 transition-all duration-200 hover:scale-110"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        title="Excluir cliente"
                        onClick={() => handleOpenDeleteModal(client)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 transition-all duration-200 hover:scale-110"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>

        {/* Paginação */}
        {!loading && clients.length > 0 && pagination && totalPages > 1 && (
          <div className="border-t bg-gradient-to-r from-gray-50 to-transparent p-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              {/* Info de itens */}
              <div className="text-sm text-gray-600 font-medium">
                Mostrando <span className="font-bold text-gray-900">{startItem}</span> até{' '}
                <span className="font-bold text-gray-900">{endItem}</span> de{' '}
                <span className="font-bold text-gray-900">{pagination.total}</span> clientes
              </div>

              {/* Controles de paginação */}
              <div className="flex items-center gap-2">
                {/* Primeira página */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(1)}
                  disabled={currentPage === 1}
                  className="h-9 w-9 p-0 hover:bg-primary/10 hover:text-primary transition-all disabled:opacity-50"
                  title="Primeira página"
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>

                {/* Página anterior */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="h-9 w-9 p-0 hover:bg-primary/10 hover:text-primary transition-all disabled:opacity-50"
                  title="Página anterior"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>

                {/* Números de páginas */}
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNumber;
                    if (totalPages <= 5) {
                      pageNumber = i + 1;
                    } else if (currentPage <= 3) {
                      pageNumber = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNumber = totalPages - 4 + i;
                    } else {
                      pageNumber = currentPage - 2 + i;
                    }

                    return (
                      <Button
                        key={pageNumber}
                        variant={currentPage === pageNumber ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handlePageChange(pageNumber)}
                        className={`h-9 w-9 p-0 transition-all ${
                          currentPage === pageNumber
                            ? 'bg-gradient-to-r from-primary to-primary/90 shadow-md'
                            : 'hover:bg-primary/10 hover:text-primary'
                        }`}
                      >
                        {pageNumber}
                      </Button>
                    );
                  })}
                </div>

                {/* Próxima página */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="h-9 w-9 p-0 hover:bg-primary/10 hover:text-primary transition-all disabled:opacity-50"
                  title="Próxima página"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>

                {/* Última página */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(totalPages)}
                  disabled={currentPage === totalPages}
                  className="h-9 w-9 p-0 hover:bg-primary/10 hover:text-primary transition-all disabled:opacity-50"
                  title="Última página"
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>

              {/* Selector de itens por página (opcional) */}
              <div className="hidden lg:flex items-center gap-2 text-sm text-gray-600">
                <span className="font-medium">Página</span>
                <span className="font-bold text-gray-900">{currentPage}</span>
                <span className="font-medium">de</span>
                <span className="font-bold text-gray-900">{totalPages}</span>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Formulário de Novo Cliente */}
      {showNewClientForm && (
        <NewClientForm
          onClose={() => setShowNewClientForm(false)}
          onSuccess={(client) => {
            debugLog.info('Cliente criado:', client);
            setShowNewClientForm(false);
          }}
        />
      )}

      {/* Modais */}
      <EditClientModal
        isOpen={isEditModalOpen}
        onClose={handleCloseEditModal}
        onSuccess={handleEditSuccess}
        client={selectedClient}
      />

      <DeleteClientModal
        isOpen={isDeleteModalOpen}
        onClose={handleCloseDeleteModal}
        onConfirm={handleDeleteClient}
        client={selectedClient}
        isLoading={isDeleting}
      />

      <ClientHistoryModal
        isOpen={isHistoryModalOpen}
        onClose={handleCloseHistoryModal}
        client={selectedClient}
      />
    </div>
  );
}