/**
 * Componentes de Proteção RBAC
 * Wrappers para controle de acesso baseado em permissões e roles
 */
'use client';

import React, { ReactNode } from 'react';
import { useRBAC, useRequirePermission, useRequireRole, useRequireAnyPermission } from '../hooks/useRBAC';
import { Shield, Lock, AlertTriangle, Eye } from 'lucide-react';

interface ProtectedComponentProps {
  children: ReactNode;
  fallback?: ReactNode;
  showFallback?: boolean;
}

interface RequirePermissionProps extends ProtectedComponentProps {
  permission: string;
}

interface RequireRoleProps extends ProtectedComponentProps {
  role: string;
}

interface RequireAnyPermissionProps extends ProtectedComponentProps {
  permissions: string[];
}

interface RequireAuthProps extends ProtectedComponentProps {}

// Componente base para exibir fallback de acesso negado
const AccessDeniedFallback: React.FC<{
  type: 'permission' | 'role' | 'auth';
  requirement?: string;
  icon?: ReactNode;
}> = ({ type, requirement, icon }) => {
  const messages = {
    permission: 'Você não tem permissão para acessar este conteúdo',
    role: 'Seu nível de acesso não permite visualizar este conteúdo',
    auth: 'Faça login para acessar este conteúdo'
  };

  const icons = {
    permission: <Shield className="w-8 h-8 text-red-400" />,
    role: <Lock className="w-8 h-8 text-orange-400" />,
    auth: <AlertTriangle className="w-8 h-8 text-yellow-400" />
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
      {icon || icons[type]}
      <h3 className="mt-4 text-lg font-medium text-gray-900">Acesso Restrito</h3>
      <p className="mt-2 text-sm text-gray-600 text-center">
        {messages[type]}
        {requirement && (
          <span className="block mt-1 text-xs text-gray-500">
            Requerido: {requirement}
          </span>
        )}
      </p>
    </div>
  );
};

// Componente para exibir loading durante verificação de permissões
const AccessCheckLoading: React.FC = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span className="ml-3 text-sm text-gray-600">Verificando permissões...</span>
  </div>
);

// Proteção por permissão específica
export const RequirePermission: React.FC<RequirePermissionProps> = ({
  permission,
  children,
  fallback,
  showFallback = true
}) => {
  const { canAccess, isCheckingAccess } = useRequirePermission(permission);

  if (isCheckingAccess) {
    return <AccessCheckLoading />;
  }

  if (!canAccess) {
    if (fallback) {
      return <>{fallback}</>;
    }

    if (showFallback) {
      return <AccessDeniedFallback type="permission" requirement={permission} />;
    }

    return null;
  }

  return <>{children}</>;
};

// Proteção por role específico
export const RequireRole: React.FC<RequireRoleProps> = ({
  role,
  children,
  fallback,
  showFallback = true
}) => {
  const { canAccess, isCheckingAccess } = useRequireRole(role);

  if (isCheckingAccess) {
    return <AccessCheckLoading />;
  }

  if (!canAccess) {
    if (fallback) {
      return <>{fallback}</>;
    }

    if (showFallback) {
      return <AccessDeniedFallback type="role" requirement={role} />;
    }

    return null;
  }

  return <>{children}</>;
};

// Proteção por qualquer uma das permissões
export const RequireAnyPermission: React.FC<RequireAnyPermissionProps> = ({
  permissions,
  children,
  fallback,
  showFallback = true
}) => {
  const { canAccess, isCheckingAccess } = useRequireAnyPermission(permissions);

  if (isCheckingAccess) {
    return <AccessCheckLoading />;
  }

  if (!canAccess) {
    if (fallback) {
      return <>{fallback}</>;
    }

    if (showFallback) {
      return <AccessDeniedFallback type="permission" requirement={permissions.join(' ou ')} />;
    }

    return null;
  }

  return <>{children}</>;
};

// Proteção por autenticação
export const RequireAuth: React.FC<RequireAuthProps> = ({
  children,
  fallback,
  showFallback = true
}) => {
  const { isAuthenticated, isLoading } = useRBAC();

  if (isLoading) {
    return <AccessCheckLoading />;
  }

  if (!isAuthenticated) {
    if (fallback) {
      return <>{fallback}</>;
    }

    if (showFallback) {
      return <AccessDeniedFallback type="auth" />;
    }

    return null;
  }

  return <>{children}</>;
};

// Componente para Super Admin apenas
export const RequireSuperAdmin: React.FC<ProtectedComponentProps> = ({
  children,
  fallback,
  showFallback = true
}) => {
  return (
    <RequireRole role="super_admin" fallback={fallback} showFallback={showFallback}>
      {children}
    </RequireRole>
  );
};

// Componente para Admin ou superior
export const RequireAdmin: React.FC<ProtectedComponentProps> = ({
  children,
  fallback,
  showFallback = true
}) => {
  return (
    <RequireAnyPermission
      permissions={['SYSTEM_ADMIN', 'SYSTEM_MANAGE']}
      fallback={fallback}
      showFallback={showFallback}
    >
      {children}
    </RequireAnyPermission>
  );
};

// Componente para visualização de dados do usuário atual
export const UserProfileDisplay: React.FC<{
  showRoles?: boolean;
  showPermissions?: boolean;
  className?: string;
}> = ({
  showRoles = true,
  showPermissions = false,
  className = ''
}) => {
  const { user, roles, permissions, isAuthenticated } = useRBAC();

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
      <div className="flex items-center space-x-3">
        <div className="h-12 w-12 rounded-full bg-blue-500 flex items-center justify-center">
          <span className="text-white font-medium">
            {user.full_name.split(' ').map(n => n[0]).join('')}
          </span>
        </div>
        <div>
          <h3 className="text-lg font-medium text-gray-900">{user.full_name}</h3>
          <p className="text-sm text-gray-600">@{user.username}</p>
        </div>
      </div>

      {showRoles && roles.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Roles:</h4>
          <div className="flex flex-wrap gap-2">
            {roles.map((role) => (
              <span
                key={role}
                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
              >
                {role}
              </span>
            ))}
          </div>
        </div>
      )}

      {showPermissions && permissions.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Permissões ({permissions.length}):
          </h4>
          <div className="max-h-32 overflow-y-auto">
            <div className="flex flex-wrap gap-1">
              {permissions.map((permission) => (
                <span
                  key={permission}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
                >
                  {permission}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Componente para mostrar status de permissão (útil para debugging)
export const PermissionDebugger: React.FC<{
  permission: string;
  className?: string;
}> = ({ permission, className = '' }) => {
  const { hasPermission, isAuthenticated } = useRBAC();

  if (!isAuthenticated) {
    return null;
  }

  const hasAccess = hasPermission(permission);

  return (
    <div className={`inline-flex items-center space-x-2 text-xs ${className}`}>
      <Eye className="w-3 h-3" />
      <span className="font-mono">{permission}</span>
      <span className={`px-2 py-1 rounded-full font-medium ${
        hasAccess
          ? 'bg-green-100 text-green-800'
          : 'bg-red-100 text-red-800'
      }`}>
        {hasAccess ? 'ALLOW' : 'DENY'}
      </span>
    </div>
  );
};

// Componente condicional baseado em permissões (mais flexível)
export const ConditionalRender: React.FC<{
  condition: 'permission' | 'role' | 'auth';
  requirement?: string | string[];
  children: ReactNode;
  fallback?: ReactNode;
}> = ({ condition, requirement, children, fallback }) => {
  const { hasPermission, hasRole, hasAnyPermission, isAuthenticated } = useRBAC();

  let shouldRender = false;

  switch (condition) {
    case 'auth':
      shouldRender = isAuthenticated;
      break;
    case 'permission':
      if (typeof requirement === 'string') {
        shouldRender = hasPermission(requirement);
      } else if (Array.isArray(requirement)) {
        shouldRender = hasAnyPermission(requirement);
      }
      break;
    case 'role':
      if (typeof requirement === 'string') {
        shouldRender = hasRole(requirement);
      }
      break;
  }

  return shouldRender ? <>{children}</> : <>{fallback}</>;
};

export default {
  RequirePermission,
  RequireRole,
  RequireAnyPermission,
  RequireAuth,
  RequireSuperAdmin,
  RequireAdmin,
  UserProfileDisplay,
  PermissionDebugger,
  ConditionalRender
};
