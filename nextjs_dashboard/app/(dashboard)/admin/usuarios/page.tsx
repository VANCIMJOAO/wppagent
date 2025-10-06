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
  UserCheck, 
  UserX,
  Shield,
  Eye,
  User
} from 'lucide-react';
import { UserModal } from '@/components/admin/UserModal';
import { DeleteUserModal } from '@/components/admin/DeleteUserModal';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { useToast } from '@/hooks/use-toast';
import { debugLog } from '@/lib/debug';

// Tipos
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

interface UserFilters {
  search: string;
  role: string;
  status: string;
}

const roleLabels = {
  admin: 'Administrador',
  atendente: 'Atendente',
  visualizador: 'Visualizador'
};

const statusLabels = {
  ativo: 'Ativo',
  inativo: 'Inativo'
};

const statusColors = {
  ativo: 'bg-green-100 text-green-800',
  inativo: 'bg-red-100 text-red-800'
};

const roleColors = {
  admin: 'bg-purple-100 text-purple-800',
  atendente: 'bg-blue-100 text-blue-800',
  visualizador: 'bg-gray-100 text-gray-800'
};

export default function UsuariosPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<UserFilters>({
    search: '',
    role: 'all',
    status: 'all'
  });
  const [showUserModal, setShowUserModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isEdit, setIsEdit] = useState(false);
  const { toast } = useToast();

  // Carregar usuários do backend (PostgreSQL)
  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/users', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Erro ao carregar usuários: ${response.status}`);
      }

      const data = await response.json();
      debugLog.success('Usuários carregados:', data);
      debugLog.info('🔍 Estrutura dos dados:', JSON.stringify(data, null, 2));
      
      if (data.success && data.data) {
        debugLog.info('👤 Primeiro usuário:', data.data[0]);
        // Mapear dados para o formato esperado
        const mappedUsers = data.data.map((user: any) => ({
          id: user.id,
          nome: user.name || user.nome,
          email: user.email,
          role: user.role,
          status: user.status,
          created_at: user.created_at,
          ultima_atividade: user.last_login || user.ultima_atividade
        }));
        debugLog.info('👤 Usuários mapeados:', mappedUsers);
        setUsers(mappedUsers);
      } else {
        throw new Error('Dados de usuários não encontrados');
      }
    } catch (error) {
      debugLog.error('Erro ao carregar usuários:', error);
      toast({
        title: 'Erro',
        description: 'Falha ao carregar usuários',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  // Filtrar usuários
  const filteredUsers = users.filter(user => {
    const matchesSearch = !filters.search || 
      user.nome.toLowerCase().includes(filters.search.toLowerCase()) ||
      user.email.toLowerCase().includes(filters.search.toLowerCase());
    
    const matchesRole = filters.role === 'all' || user.role === filters.role;
    const matchesStatus = filters.status === 'all' || user.status === filters.status;
    
    return matchesSearch && matchesRole && matchesStatus;
  });

  // Handlers
  const handleCreateUser = () => {
    setSelectedUser(null);
    setIsEdit(false);
    setShowUserModal(true);
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setIsEdit(true);
    setShowUserModal(true);
  };

  const handleDeleteUser = (user: User) => {
    setSelectedUser(user);
    setShowDeleteModal(true);
  };

  const handleToggleStatus = async (user: User) => {
    try {
      const newStatus = user.status === 'ativo' ? 'inativo' : 'ativo';
      
      // Simular chamada da API
      await new Promise(resolve => setTimeout(resolve, 300));
      
      setUsers(prev => prev.map(u => 
        u.id === user.id ? { ...u, status: newStatus } : u
      ));
      
      toast({
        title: 'Sucesso',
        description: `Usuário ${newStatus === 'ativo' ? 'ativado' : 'desativado'} com sucesso`
      });
    } catch (error) {
      debugLog.error('Erro ao alterar status:', error);
      toast({
        title: 'Erro',
        description: 'Falha ao alterar status do usuário',
        variant: 'destructive'
      });
    }
  };

  const handleUserSaved = (savedUser: User) => {
    if (isEdit) {
      setUsers(prev => prev.map(u => u.id === savedUser.id ? savedUser : u));
      toast({
        title: 'Sucesso',
        description: 'Usuário atualizado com sucesso'
      });
    } else {
      setUsers(prev => [...prev, { ...savedUser, id: Date.now() }]);
      toast({
        title: 'Sucesso',
        description: 'Usuário criado com sucesso'
      });
    }
    setShowUserModal(false);
  };

  const handleUserDeleted = (userId: number) => {
    setUsers(prev => prev.filter(u => u.id !== userId));
    setShowDeleteModal(false);
    toast({
      title: 'Sucesso',
      description: 'Usuário removido com sucesso'
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin': return <Shield className="h-4 w-4" />;
      case 'atendente': return <User className="h-4 w-4" />;
      case 'visualizador': return <Eye className="h-4 w-4" />;
      default: return <User className="h-4 w-4" />;
    }
  };

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  return (
    <RoleGuard requiredRole="admin">
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
        <div className="max-w-7xl mx-auto p-6 lg:p-8 space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
                Gestão de Usuários
              </h1>
              <p className="text-gray-600 text-lg">
                Gerencie usuários, permissões e acessos do sistema
              </p>
            </div>
            <Button 
              onClick={handleCreateUser}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all h-12 px-6 text-base font-medium"
            >
              <Plus className="h-5 w-5 mr-2" />
              Novo Usuário
            </Button>
          </div>

          {/* Filtros */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 pb-5">
              <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
                <Search className="w-6 h-6 mr-3 text-blue-600" />
                Filtros
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <Input
                    placeholder="Buscar por nome ou email..."
                    value={filters.search}
                    onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                    className="pl-12 h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                
                <Select
                  value={filters.role}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, role: value }))}
                >
                  <SelectTrigger className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500">
                    <SelectValue placeholder="Filtrar por role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as roles</SelectItem>
                    <SelectItem value="admin">Administrador</SelectItem>
                    <SelectItem value="atendente">Atendente</SelectItem>
                    <SelectItem value="visualizador">Visualizador</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={filters.status}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
                >
                  <SelectTrigger className="h-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500">
                    <SelectValue placeholder="Filtrar por status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os status</SelectItem>
                    <SelectItem value="ativo">Ativo</SelectItem>
                    <SelectItem value="inativo">Inativo</SelectItem>
                  </SelectContent>
                </Select>

                <Button
                  variant="outline"
                  onClick={() => setFilters({ search: '', role: 'all', status: 'all' })}
                  className="h-12 text-base border-2 hover:bg-gray-50 font-medium"
                >
                  Limpar Filtros
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Tabela de Usuários */}
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 pb-5">
              <CardTitle className="text-xl font-bold text-gray-900 flex items-center">
                <User className="w-6 h-6 mr-3 text-blue-600" />
                Usuários ({filteredUsers.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
                </div>
              ) : (
                <div className="rounded-lg border border-gray-200 overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gradient-to-r from-gray-50 to-slate-50 hover:from-gray-50 hover:to-slate-50">
                        <TableHead className="font-bold text-gray-900 text-base h-14">Nome</TableHead>
                        <TableHead className="font-bold text-gray-900 text-base h-14">Email</TableHead>
                        <TableHead className="font-bold text-gray-900 text-base h-14">Role</TableHead>
                        <TableHead className="font-bold text-gray-900 text-base h-14">Status</TableHead>
                        <TableHead className="font-bold text-gray-900 text-base h-14">Última Atividade</TableHead>
                        <TableHead className="w-[70px] h-14"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredUsers.map((user) => (
                        <TableRow key={user.id} className="hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-purple-50/50 transition-colors">
                          <TableCell className="font-medium text-base py-5">
                            <div className="flex items-center gap-3">
                              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white font-bold shadow-md">
                                {user.nome.charAt(0).toUpperCase()}
                              </div>
                              <span className="font-semibold">{user.nome}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-gray-600 text-base py-5">{user.email}</TableCell>
                          <TableCell className="py-5">
                            <Badge className={`${roleColors[user.role]} px-3 py-1.5 text-sm font-medium`}>
                              <span className="mr-2">{getRoleIcon(user.role)}</span>
                              {roleLabels[user.role]}
                            </Badge>
                          </TableCell>
                          <TableCell className="py-5">
                            <Badge className={`${statusColors[user.status]} px-3 py-1.5 text-sm font-medium`}>
                              {statusLabels[user.status]}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-gray-600 text-sm py-5">
                            {formatDate(user.ultima_atividade)}
                          </TableCell>
                          <TableCell className="py-5">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm" className="h-9 w-9 p-0 hover:bg-gray-100">
                                  <MoreHorizontal className="h-5 w-5" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-48">
                                <DropdownMenuItem onClick={() => handleEditUser(user)} className="cursor-pointer">
                                  <Edit className="h-4 w-4 mr-3" />
                                  Editar
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleToggleStatus(user)} className="cursor-pointer">
                                  {user.status === 'ativo' ? (
                                    <>
                                      <UserX className="h-4 w-4 mr-3" />
                                      Desativar
                                    </>
                                  ) : (
                                    <>
                                      <UserCheck className="h-4 w-4 mr-3" />
                                      Ativar
                                    </>
                                  )}
                                </DropdownMenuItem>
                                <DropdownMenuItem 
                                  onClick={() => handleDeleteUser(user)}
                                  className="text-red-600 cursor-pointer focus:text-red-600"
                                >
                                  <Trash2 className="h-4 w-4 mr-3" />
                                  Excluir
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Modais */}
          {showUserModal && (
            <UserModal
              user={selectedUser}
              isEdit={isEdit}
              onClose={() => setShowUserModal(false)}
              onSave={handleUserSaved}
            />
          )}

          {showDeleteModal && selectedUser && (
            <DeleteUserModal
              user={selectedUser}
              onClose={() => setShowDeleteModal(false)}
              onConfirm={handleUserDeleted}
            />
          )}
        </div>
      </div>
    </RoleGuard>
  );
}
