"""
Fix RBAC Enum Types - Corrigir tipos de enum RBAC

Revision ID: fix_rbac_enum_types
Revises: hf001_consolidate_schema_drift_final
Create Date: 2025-01-15 12:00:00.000000

✅ CORREÇÃO: Corrigir tipos de enum RBAC para resolver erro SQL
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers
revision = "fix_rbac_enum_types"
down_revision = "a8ae5130c43c"
branch_labels = None
depends_on = None


def upgrade():
    """Corrigir tipos de enum RBAC"""
    
    # 1. Primeiro, atualizar dados existentes para valores compatíveis
    op.execute("""
        UPDATE rbac_roles 
        SET role_type = CASE 
            WHEN role_type = 'SUPER_ADMIN' THEN 'super_admin'
            WHEN role_type = 'ADMIN' THEN 'admin'
            WHEN role_type = 'MANAGER' THEN 'manager'
            WHEN role_type = 'OPERATOR' THEN 'operator'
            WHEN role_type = 'VIEWER' THEN 'viewer'
            WHEN role_type = 'GUEST' THEN 'guest'
            WHEN role_type = 'USER' THEN 'viewer'
            WHEN role_type = 'CUSTOM' THEN 'viewer'
            WHEN role_type = 'SYSTEM' THEN 'admin'
            ELSE 'viewer'
        END
        WHERE role_type IS NOT NULL
    """)
    
    # 2. Remover enum antigo se existir
    try:
        op.execute("DROP TYPE IF EXISTS roletype CASCADE")
    except Exception:
        pass
    
    # 3. Criar enum RoleType corrigido
    role_type_enum = postgresql.ENUM(
        "super_admin",
        "admin", 
        "manager",
        "operator",
        "viewer",
        "guest",
        name="roletype",
    )
    role_type_enum.create(op.get_bind())
    
    # 4. Atualizar coluna role_type na tabela rbac_roles
    op.alter_column(
        'rbac_roles',
        'role_type',
        type_=role_type_enum,
        postgresql_using='role_type::text::roletype'
    )
    
    # 5. Atualizar dados de permissões existentes
    op.execute("""
        UPDATE rbac_permissions 
        SET permission_type = CASE 
            WHEN permission_type = 'read' THEN 'dashboard:view'
            WHEN permission_type = 'write' THEN 'dashboard:admin'
            WHEN permission_type = 'delete' THEN 'system:admin'
            WHEN permission_type = 'admin' THEN 'system:admin'
            ELSE permission_type
        END
        WHERE permission_type IS NOT NULL
    """)
    
    # 6. Remover enum antigo PermissionType se existir
    try:
        op.execute("DROP TYPE IF EXISTS permissiontype CASCADE")
    except Exception:
        pass
    
    # 7. Criar enum PermissionType corrigido
    permission_type_enum = postgresql.ENUM(
        "dashboard:view",
        "dashboard:admin",
        "appointments:view",
        "appointments:create",
        "appointments:update",
        "appointments:delete",
        "appointments:admin",
        "conversations:view",
        "conversations:respond",
        "conversations:delete",
        "conversations:admin",
        "clients:view",
        "clients:create",
        "clients:update",
        "clients:delete",
        "clients:admin",
        "reports:view",
        "reports:export",
        "reports:admin",
        "system:admin",
        "users:manage",
        "roles:manage",
        "permissions:manage",
        "monitoring:view",
        "monitoring:admin",
        "backup:create",
        "backup:restore",
        "backup:admin",
        name="permissiontype",
    )
    permission_type_enum.create(op.get_bind())
    
    # 8. Atualizar coluna permission_type na tabela rbac_permissions
    op.alter_column(
        'rbac_permissions',
        'permission_type',
        type_=permission_type_enum,
        postgresql_using='permission_type::text::permissiontype'
    )


def downgrade():
    """Reverter correções"""
    
    # Reverter para tipos antigos
    try:
        op.execute("DROP TYPE IF EXISTS roletype CASCADE")
        op.execute("DROP TYPE IF EXISTS permissiontype CASCADE")
    except Exception:
        pass
    
    # Recriar enums antigos
    old_role_type_enum = postgresql.ENUM(
        "SYSTEM",
        "CUSTOM", 
        "SUPER_ADMIN",
        "ADMIN",
        "MANAGER",
        "USER",
        "GUEST",
        "OPERATOR",
        "VIEWER",
        name="roletype",
    )
    old_role_type_enum.create(op.get_bind())
    
    old_permission_type_enum = postgresql.ENUM(
        "dashboard:view",
        "dashboard:admin",
        "appointments:view",
        "appointments:create",
        "appointments:update",
        "appointments:delete",
        "appointments:admin",
        "conversations:view",
        "conversations:respond",
        "conversations:delete",
        "conversations:admin",
        "clients:view",
        "clients:create",
        "clients:update",
        "clients:delete",
        "clients:admin",
        "reports:view",
        "reports:export",
        "reports:admin",
        "system:admin",
        "users:manage",
        "roles:manage",
        "permissions:manage",
        "monitoring:view",
        "monitoring:admin",
        "backup:create",
        "backup:restore",
        "backup:admin",
        name="permissiontype",
    )
    old_permission_type_enum.create(op.get_bind())
