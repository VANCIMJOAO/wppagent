/**
 * Componente de Gerenciamento RBAC
 * Interface completa para controle de usuários, roles e permissões
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Users, 
  Shield, 
  Key, 
  UserPlus,
  Settings,
  Eye,
  Edit3,
  Trash2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Lock,
  Unlock,
  UserCheck
} from 'lucide-react';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  requires_2fa: boolean;
  roles: string[];
  permissions: string[];
  created_at: string;
}

interface Role {
  id: number;
  name: string;
  description: string;
  role_type?: string;
  is_system_role: boolean;
  can_be_deleted: boolean;
  permissions_count: number;
  users_count: number;
  permissions: string[];
}

interface Permission {
  permission_type: string;
  name: string;
  description: string;
  category: string;
  risk_level: string;
  requires_2fa: boolean;
}

interface RBACStats {
  users: {
    total: number;
    active: number;
    inactive: number;
  };
  roles: {
    total: number;
    system_roles: number;
    custom_roles: number;
  };
  permissions: {
    total: number;
    categories: number;
  };
}

const RBACManagementComponent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'roles' | 'permissions' | 'stats'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [stats, setStats] = useState<RBACStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Estados para modais
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showCreateRole, setShowCreateRole] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  // Carregar dados
  const loadUsers = useCallback(async () => {
    try {
      const response = await fetch('/api/rbac/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (err) {
      setError('Erro ao carregar usuários');
    }
  }, []);

  const loadRoles = useCallback(async () => {
    try {
      const response = await fetch('/api/rbac/roles', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setRoles(data);
      }
    } catch (err) {
      setError('Erro ao carregar roles');
    }
  }, []);

  const loadPermissions = useCallback(async () => {
    try {
      const response = await fetch('/api/rbac/permissions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPermissions(data.permissions || []);
      }
    } catch (err) {
      setError('Erro ao carregar permissões');
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const response = await fetch('/api/rbac/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      setError('Erro ao carregar estatísticas');
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    
    Promise.all([
      activeTab === 'users' && loadUsers(),
      activeTab === 'roles' && loadRoles(),
      activeTab === 'permissions' && loadPermissions(),
      activeTab === 'stats' && loadStats()
    ]).finally(() => {
      setLoading(false);
    });
  }, [activeTab, loadUsers, loadRoles, loadPermissions, loadStats]);

  // Renderizar estatísticas
  const renderStats = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold">Estatísticas do Sistema RBAC</h3>
      
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Usuários */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Usuários</p>
                <p className="text-2xl font-bold text-gray-900">{stats.users.total}</p>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
            <div className="mt-4 flex justify-between text-sm">
              <span className="text-green-600">Ativos: {stats.users.active}</span>
              <span className="text-red-600">Inativos: {stats.users.inactive}</span>
            </div>
          </div>

          {/* Roles */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Roles</p>
                <p className="text-2xl font-bold text-gray-900">{stats.roles.total}</p>
              </div>
              <Shield className="h-8 w-8 text-green-600" />
            </div>
            <div className="mt-4 flex justify-between text-sm">
              <span className="text-blue-600">Sistema: {stats.roles.system_roles}</span>
              <span className="text-purple-600">Custom: {stats.roles.custom_roles}</span>
            </div>
          </div>

          {/* Permissões */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Permissões</p>
                <p className="text-2xl font-bold text-gray-900">{stats.permissions.total}</p>
              </div>
              <Key className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="mt-4">
              <span className="text-sm text-gray-600">
                {stats.permissions.categories} categorias
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Renderizar lista de usuários
  const renderUsers = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold">Gerenciar Usuários</h3>
        <button
          onClick={() => setShowCreateUser(true)}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <UserPlus className="w-4 h-4" />
          <span>Novo Usuário</span>
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {users.map((user) => (
            <li key={user.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                      <span className="text-sm font-medium text-gray-700">
                        {user.full_name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="flex items-center space-x-2">
                      <p className="text-sm font-medium text-gray-900">
                        {user.full_name}
                      </p>
                      {user.is_active ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                      {user.requires_2fa && (
                        <Lock className="h-4 w-4 text-orange-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-500">@{user.username} • {user.email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      {user.roles.map((role, index) => (
                        <span 
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {role}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setSelectedUser(user)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {/* Editar usuário */}}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <Edit3 className="h-4 w-4" />
                  </button>
                  {!user.is_active && (
                    <button
                      onClick={() => {/* Reativar usuário */}}
                      className="text-green-400 hover:text-green-600"
                    >
                      <UserCheck className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );

  // Renderizar lista de roles
  const renderRoles = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold">Gerenciar Roles</h3>
        <button
          onClick={() => setShowCreateRole(true)}
          className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
        >
          <Shield className="w-4 h-4" />
          <span>Novo Role</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {roles.map((role) => (
          <div key={role.id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h4 className="text-lg font-semibold text-gray-900">{role.name}</h4>
                  {role.is_system_role && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      Sistema
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{role.description}</p>
                
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Permissões:</span>
                    <span className="font-medium">{role.permissions_count}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Usuários:</span>
                    <span className="font-medium">{role.users_count}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={() => setSelectedRole(role)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <Eye className="h-4 w-4" />
                </button>
                {role.can_be_deleted && (
                  <button
                    onClick={() => {/* Deletar role */}}
                    className="text-red-400 hover:text-red-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Renderizar lista de permissões
  const renderPermissions = () => {
    const categorizedPermissions = permissions.reduce((acc, perm) => {
      if (!acc[perm.category]) {
        acc[perm.category] = [];
      }
      acc[perm.category].push(perm);
      return acc;
    }, {} as Record<string, Permission[]>);

    return (
      <div className="space-y-6">
        <h3 className="text-xl font-semibold">Permissões do Sistema</h3>
        
        {Object.entries(categorizedPermissions).map(([category, categoryPerms]) => (
          <div key={category} className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h4 className="text-lg font-medium text-gray-900">{category}</h4>
            </div>
            <div className="divide-y divide-gray-200">
              {categoryPerms.map((perm) => (
                <div key={perm.permission_type} className="px-6 py-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{perm.name}</p>
                    <p className="text-xs text-gray-500">{perm.permission_type}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      perm.risk_level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                      perm.risk_level === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                      perm.risk_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {perm.risk_level}
                    </span>
                    {perm.requires_2fa && (
                      <Lock className="h-4 w-4 text-orange-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Renderizar conteúdo da aba ativa
  const renderActiveTab = () => {
    if (loading) {
      return (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    switch (activeTab) {
      case 'users':
        return renderUsers();
      case 'roles':
        return renderRoles();
      case 'permissions':
        return renderPermissions();
      case 'stats':
        return renderStats();
      default:
        return null;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Sistema RBAC</h1>
        <p className="text-gray-600 mt-2">
          Controle granular de permissões e gerenciamento de acesso
        </p>
      </div>

      {/* Abas */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'users', label: 'Usuários', icon: Users },
            { id: 'roles', label: 'Roles', icon: Shield },
            { id: 'permissions', label: 'Permissões', icon: Key },
            { id: 'stats', label: 'Estatísticas', icon: Settings }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Mensagem de erro */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <p className="ml-2 text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Conteúdo da aba ativa */}
      {renderActiveTab()}
    </div>
  );
};

export default RBACManagementComponent;
