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

  // Dados mock para demonstração
  const mockUsers: User[] = [
    {
      id: 1,
      nome: 'João Silva',
      email: 'joao@empresa.com',
      role: 'admin',
      status: 'ativo',
      ultima_atividade: '2025-10-01T15:30:00Z',
      created_at: '2025-01-15T10:00:00Z'
    },
    {
      id: 2,
      nome: 'Maria Santos',
      email: 'maria@empresa.com',
      role: 'atendente',
      status: 'ativo',
      ultima_atividade: '2025-10-01T14:20:00Z',
      created_at: '2025-02-20T09:30:00Z'
    },
    {
      id: 3,
      nome: 'Pedro Costa',
      email: 'pedro@empresa.com',
      role: 'visualizador',
      status: 'inativo',
      ultima_atividade: '2025-09-28T16:45:00Z',
      created_at: '2025-03-10T14:15:00Z'
    },
    {
      id: 4,
      nome: 'Ana Oliveira',
      email: 'ana@empresa.com',
      role: 'atendente',
      status: 'ativo',
      ultima_atividade: '2025-10-01T12:10:00Z',
      created_at: '2025-04-05T11:20:00Z'
    },
    {
      id: 5,
      nome: 'Carlos Ferreira',
      email: 'carlos@empresa.com',
      role: 'admin',
      status: 'ativo',
      ultima_atividade: '2025-10-01T18:00:00Z',
      created_at: '2025-05-12T08:45:00Z'
    }
  ];

  // Carregar usuários
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
      console.log('✅ Usuários carregados:', data);
      console.log('🔍 Estrutura dos dados:', JSON.stringify(data, null, 2));
      
      if (data.success && data.data) {
        console.log('👤 Primeiro usuário:', data.data[0]);
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
        console.log('👤 Usuários mapeados:', mappedUsers);
        setUsers(mappedUsers);
      } else {
        throw new Error('Dados de usuários não encontrados');
      }
    } catch (error) {
      console.error('Erro ao carregar usuários:', error);
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
      console.error('Erro ao alterar status:', error);
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
      <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Gestão de Usuários</h1>
          <p className="text-muted-foreground">
            Gerencie usuários, permissões e acessos do sistema
          </p>
        </div>
        <Button onClick={handleCreateUser}>
          <Plus className="h-4 w-4 mr-2" />
          Novo Usuário
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nome ou email..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="pl-10"
              />
            </div>
            
            <Select
              value={filters.role}
              onValueChange={(value) => setFilters(prev => ({ ...prev, role: value }))}
            >
              <SelectTrigger>
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
              <SelectTrigger>
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
            >
              Limpar Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Usuários */}
      <Card>
        <CardHeader>
          <CardTitle>
            Usuários ({filteredUsers.length})
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
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Última Atividade</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {getRoleIcon(user.role)}
                        {user.nome}
                      </div>
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge className={roleColors[user.role]}>
                        {roleLabels[user.role]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[user.status]}>
                        {statusLabels[user.status]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(user.ultima_atividade)}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEditUser(user)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Editar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleToggleStatus(user)}>
                            {user.status === 'ativo' ? (
                              <>
                                <UserX className="h-4 w-4 mr-2" />
                                Desativar
                              </>
                            ) : (
                              <>
                                <UserCheck className="h-4 w-4 mr-2" />
                                Ativar
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteUser(user)}
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
    </RoleGuard>
  );
}
