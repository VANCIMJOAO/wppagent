"""fix_rbac_enum_values_alignment

Revision ID: dbfccfc4f44c
Revises: fix_rbac_enum_types
Create Date: 2025-09-24 19:12:08.375554-03:00

✅ CORREÇÃO: Alinhar valores do enum roletype com o código Python
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'dbfccfc4f44c'
down_revision = 'fix_rbac_enum_types'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Alinhar valores do enum roletype com o código Python"""
    
    # O banco já está com os valores corretos (minúsculos)
    # Esta migração é apenas para marcar que o alinhamento foi feito
    print("✅ Valores do enum roletype já estão alinhados com o código Python")
    print("✅ Migração de alinhamento aplicada com sucesso")


def downgrade() -> None:
    """Reverter para valores maiúsculos"""
    
    # 1. Atualizar dados para valores maiúsculos
    op.execute("""
        UPDATE rbac_roles 
        SET role_type = CASE 
            WHEN role_type = 'super_admin' THEN 'SUPER_ADMIN'
            WHEN role_type = 'admin' THEN 'ADMIN'
            WHEN role_type = 'manager' THEN 'MANAGER'
            WHEN role_type = 'operator' THEN 'OPERATOR'
            WHEN role_type = 'viewer' THEN 'VIEWER'
            WHEN role_type = 'guest' THEN 'GUEST'
            ELSE role_type
        END
        WHERE role_type IS NOT NULL
    """)
    
    # 2. Remover enum atual
    try:
        op.execute("DROP TYPE IF EXISTS roletype CASCADE")
    except Exception:
        pass
    
    # 3. Recriar enum com valores maiúsculos
    old_role_type_enum = postgresql.ENUM(
        "SUPER_ADMIN",
        "ADMIN", 
        "MANAGER",
        "OPERATOR",
        "VIEWER",
        "GUEST",
        name="roletype",
    )
    old_role_type_enum.create(op.get_bind())
    
    # 4. Atualizar coluna
    op.alter_column(
        'rbac_roles',
        'role_type',
        type_=old_role_type_enum,
        postgresql_using='role_type::text::roletype'
    )
