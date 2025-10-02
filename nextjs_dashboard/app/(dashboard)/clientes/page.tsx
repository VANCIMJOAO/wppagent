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
  AlertCircle
} from 'lucide-react';
import { useClients } from '@/hooks/useClients';
import type { Client } from '@/types/api';
import { NewClientForm } from '@/components/NewClientForm';
import EditClientModal from '@/components/clients/EditClientModal';
import DeleteClientModal from '@/components/clients/DeleteClientModal';
import { toast } from 'sonner';

export default function ClientesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('name');
  const [showNewClientForm, setShowNewClientForm] = useState(false);

  // Estados para modais
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
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
    limit: 50,
    offset: 0
  });

  // Atualizar filtros quando os valores mudarem
  useEffect(() => {
    updateFilters({
      search: searchTerm,
      status: statusFilter,
      sortBy: sortBy
    });
  }, [searchTerm, statusFilter, sortBy, updateFilters]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'vip':
        return <Badge className="bg-purple-100 text-purple-800">VIP</Badge>;
      case 'active':
        return <Badge className="bg-green-100 text-green-800">Ativo</Badge>;
      case 'inactive':
        return <Badge className="bg-gray-100 text-gray-800">Inativo</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Desconhecido</Badge>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'vip':
        return <UserCheck className="h-4 w-4 text-purple-600" />;
      case 'active':
        return <UserCheck className="h-4 w-4 text-green-600" />;
      case 'inactive':
        return <UserX className="h-4 w-4 text-gray-400" />;
      default:
        return <Users className="h-4 w-4 text-gray-400" />;
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
      console.error('Erro ao excluir cliente:', error);
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

  return (
    <div className="space-y-6" data-testid="clients-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Clientes</h1>
          <p className="text-gray-600 mt-1">
            Gestão da base de clientes
            {pagination && (
              <span className="ml-2 text-sm">
                ({pagination.total} {pagination.total === 1 ? 'cliente' : 'clientes'})
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button onClick={() => setShowNewClientForm(true)}>
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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">
                    {pagination?.total || clients.length}
                  </p>
                )}
              </div>
              <Users className="h-6 w-6 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Ativos</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-green-600">
                    {clients.filter(c => c.status === 'active').length}
                  </p>
                )}
              </div>
              <UserCheck className="h-6 w-6 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">VIP</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-purple-600">
                    {clients.filter(c => c.status === 'vip').length}
                  </p>
                )}
              </div>
              <UserCheck className="h-6 w-6 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Inativos</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-gray-600">
                    {clients.filter(c => c.status === 'inactive').length}
                  </p>
                )}
              </div>
              <UserX className="h-6 w-6 text-gray-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Buscar clientes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
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
              <SelectTrigger className="w-48">
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
      <Card>
        <CardHeader>
          <CardTitle>Lista de Clientes</CardTitle>
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
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <Users className="h-6 w-6 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className="font-medium text-gray-900">{client.nome}</h3>
                          {getStatusBadge(client.status)}
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                          {client.email && (
                            <span className="flex items-center">
                              <Mail className="h-3 w-3 mr-1" />
                              {client.email}
                            </span>
                          )}
                          <span className="flex items-center">
                            <Phone className="h-3 w-3 mr-1" />
                            {client.telefone}
                          </span>
                          <span className="flex items-center">
                            <Calendar className="h-3 w-3 mr-1" />
                            {client.wa_id}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                          <span>Cadastrado: {formatDate(client.created_at)}</span>
                          <span>Última visita: {formatDate(client.last_interaction || null)}</span>
                          <span>Consultas: {client.total_appointments}</span>
                          <span>Conversas: {client.total_conversations}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        title="Editar cliente"
                        onClick={() => handleOpenEditModal(client)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        title="Excluir cliente"
                        onClick={() => handleOpenDeleteModal(client)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
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
      </Card>

      {/* Formulário de Novo Cliente */}
      {showNewClientForm && (
        <NewClientForm
          onClose={() => setShowNewClientForm(false)}
          onSuccess={(client) => {
            console.log('Cliente criado:', client);
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
    </div>
  );
}