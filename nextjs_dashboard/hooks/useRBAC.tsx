/**
 * Hook React para integração com sistema RBAC
 * Gerencia permissões, autenticação e controle de acesso no frontend
 */
'use client';

import { useState, useEffect, useContext, createContext, ReactNode, useCallback } from 'react';

// Tipos
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

interface RBACContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  permissions: string[];
  roles: string[];
  login: (token: string) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  refreshUser: () => Promise<void>;
  checkTwoFactorRequired: (permission?: string) => boolean;
}

// Context
const RBACContext = createContext<RBACContextType | undefined>(undefined);

// Provider
interface RBACProviderProps {
  children: ReactNode;
}

export const RBACProvider: React.FC<RBACProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [roles, setRoles] = useState<string[]>([]);

  const isAuthenticated = !!user;

  // Verificar token no localStorage e carregar dados do usuário
  const checkAuthentication = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/rbac/user/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setPermissions(userData.permissions || []);
        setRoles(userData.roles || []);
      } else {
        // Token inválido, limpar localStorage
        localStorage.removeItem('auth_token');
      }
    } catch (error) {
      console.error('Erro ao verificar autenticação:', error);
      localStorage.removeItem('auth_token');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fazer login
  const login = async (token: string): Promise<void> => {
    localStorage.setItem('auth_token', token);
    await checkAuthentication();
  };

  // Fazer logout
  const logout = (): void => {
    localStorage.removeItem('auth_token');
    setUser(null);
    setPermissions([]);
    setRoles([]);
  };

  // Verificar se usuário tem uma permissão específica
  const hasPermission = (permission: string): boolean => {
    return permissions.includes(permission);
  };

  // Verificar se usuário tem um role específico
  const hasRole = (role: string): boolean => {
    return roles.includes(role);
  };

  // Verificar se usuário tem qualquer uma das permissões
  const hasAnyPermission = (permissionList: string[]): boolean => {
    return permissionList.some(permission => permissions.includes(permission));
  };

  // Verificar se usuário tem todas as permissões
  const hasAllPermissions = (permissionList: string[]): boolean => {
    return permissionList.every(permission => permissions.includes(permission));
  };

  // Verificar se usuário tem qualquer um dos roles
  const hasAnyRole = (roleList: string[]): boolean => {
    return roleList.some(role => roles.includes(role));
  };

  // Verificar se 2FA é obrigatório
  const checkTwoFactorRequired = (permission?: string): boolean => {
    if (!user) return false;
    
    // Se o usuário tem 2FA configurado, sempre requer
    if (user.requires_2fa) return true;
    
    // Se uma permissão específica foi fornecida, verificar se ela requer 2FA
    // Isso seria implementado baseado nas configurações de permissões
    return false;
  };

  // Atualizar dados do usuário
  const refreshUser = async (): Promise<void> => {
    if (!isAuthenticated) return;
    
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    try {
      const response = await fetch('/api/rbac/user/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setPermissions(userData.permissions || []);
        setRoles(userData.roles || []);
      }
    } catch (error) {
      console.error('Erro ao atualizar dados do usuário:', error);
    }
  };

  // Verificar autenticação na inicialização
  useEffect(() => {
    checkAuthentication();
  }, [checkAuthentication]);

  const contextValue: RBACContextType = {
    user,
    isAuthenticated,
    isLoading,
    permissions,
    roles,
    login,
    logout,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    hasAnyRole,
    refreshUser,
    checkTwoFactorRequired,
  };

  return (
    <RBACContext.Provider value={contextValue}>
      {children}
    </RBACContext.Provider>
  );
};

// Hook principal
export const useRBAC = (): RBACContextType => {
  const context = useContext(RBACContext);
  if (context === undefined) {
    throw new Error('useRBAC deve ser usado dentro de um RBACProvider');
  }
  return context;
};

// Hook para componentes protegidos por permissão
export const useRequirePermission = (permission: string) => {
  const { hasPermission, isLoading, isAuthenticated } = useRBAC();
  
  const canAccess = isAuthenticated && hasPermission(permission);
  const isCheckingAccess = isLoading;
  
  return { canAccess, isCheckingAccess };
};

// Hook para componentes protegidos por role
export const useRequireRole = (role: string) => {
  const { hasRole, isLoading, isAuthenticated } = useRBAC();
  
  const canAccess = isAuthenticated && hasRole(role);
  const isCheckingAccess = isLoading;
  
  return { canAccess, isCheckingAccess };
};

// Hook para componentes protegidos por múltiplas permissões
export const useRequireAnyPermission = (permissions: string[]) => {
  const { hasAnyPermission, isLoading, isAuthenticated } = useRBAC();
  
  const canAccess = isAuthenticated && hasAnyPermission(permissions);
  const isCheckingAccess = isLoading;
  
  return { canAccess, isCheckingAccess };
};

// Hook para componentes protegidos por múltiplas permissões (todas obrigatórias)
export const useRequireAllPermissions = (permissions: string[]) => {
  const { hasAllPermissions, isLoading, isAuthenticated } = useRBAC();
  
  const canAccess = isAuthenticated && hasAllPermissions(permissions);
  const isCheckingAccess = isLoading;
  
  return { canAccess, isCheckingAccess };
};

// Hook para operações RBAC (admin)
export const useRBACAdmin = () => {
  const { hasPermission } = useRBAC();
  
  const canManageUsers = hasPermission('USERS_MANAGE');
  const canManageRoles = hasPermission('SYSTEM_RBAC_MANAGE');
  const canViewUsers = hasPermission('USERS_VIEW');
  const canViewSystem = hasPermission('SYSTEM_VIEW');
  
  // Funções para operações administrativas
  const createUser = async (userData: {
    username: string;
    email: string;
    full_name: string;
    password: string;
    roles?: string[];
  }) => {
    if (!canManageUsers) {
      throw new Error('Sem permissão para criar usuários');
    }

    const token = localStorage.getItem('auth_token');
    const response = await fetch('/api/rbac/users', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      throw new Error('Erro ao criar usuário');
    }

    return response.json();
  };

  const updateUser = async (userId: number, updates: {
    full_name?: string;
    email?: string;
    is_active?: boolean;
    requires_2fa?: boolean;
  }) => {
    if (!canManageUsers) {
      throw new Error('Sem permissão para atualizar usuários');
    }

    const token = localStorage.getItem('auth_token');
    const response = await fetch(`/api/rbac/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      throw new Error('Erro ao atualizar usuário');
    }

    return response.json();
  };

  const assignRole = async (userId: number, roleName: string) => {
    if (!canManageUsers) {
      throw new Error('Sem permissão para gerenciar roles de usuário');
    }

    const token = localStorage.getItem('auth_token');
    const response = await fetch(`/api/rbac/users/${userId}/roles/${roleName}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Erro ao atribuir role');
    }

    return response.json();
  };

  const removeRole = async (userId: number, roleName: string) => {
    if (!canManageUsers) {
      throw new Error('Sem permissão para gerenciar roles de usuário');
    }

    const token = localStorage.getItem('auth_token');
    const response = await fetch(`/api/rbac/users/${userId}/roles/${roleName}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Erro ao remover role');
    }

    return response.json();
  };

  const createRole = async (roleData: {
    name: string;
    description: string;
    permissions?: string[];
  }) => {
    if (!canManageRoles) {
      throw new Error('Sem permissão para criar roles');
    }

    const token = localStorage.getItem('auth_token');
    const response = await fetch('/api/rbac/roles', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(roleData),
    });

    if (!response.ok) {
      throw new Error('Erro ao criar role');
    }

    return response.json();
  };

  const fetchUsers = async () => {
    if (!canViewUsers) {
      throw new Error('Sem permissão para visualizar usuários');
    }

    const token = localStorage.getItem('auth_token');
    const response = await fetch('/api/rbac/users', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Erro ao carregar usuários');
    }

    return response.json();
  };

  const fetchRoles = async () => {
    if (!canViewSystem) {
      throw new Error('Sem permissão para visualizar roles');
    }

    const token = localStorage.getItem('auth_token');
    const response = await fetch('/api/rbac/roles', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Erro ao carregar roles');
    }

    return response.json();
  };

  const fetchStats = async () => {
    if (!canViewSystem) {
      throw new Error('Sem permissão para visualizar estatísticas');
    }

    const token = localStorage.getItem('auth_token');
    const response = await fetch('/api/rbac/stats', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Erro ao carregar estatísticas');
    }

    return response.json();
  };

  return {
    canManageUsers,
    canManageRoles,
    canViewUsers,
    canViewSystem,
    createUser,
    updateUser,
    assignRole,
    removeRole,
    createRole,
    fetchUsers,
    fetchRoles,
    fetchStats,
  };
};

export default useRBAC;
