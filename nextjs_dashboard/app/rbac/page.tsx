/**
 * Página de Gerenciamento RBAC
 * Interface administrativa para controle de usuários, roles e permissões
 */
'use client';

import React from 'react';
import RBACManagementComponent from '../../components/RBACManagementComponent';
import { RequirePermission } from '../../components/RBACProtection';
import { RBACProvider } from '../../hooks/useRBAC';

const RBACManagementPage: React.FC = () => {
  return (
    <RBACProvider>
      <RequirePermission permission="SYSTEM_RBAC_MANAGE">
        <div className="min-h-screen bg-gray-50">
          <RBACManagementComponent />
        </div>
      </RequirePermission>
    </RBACProvider>
  );
};

export default RBACManagementPage;
