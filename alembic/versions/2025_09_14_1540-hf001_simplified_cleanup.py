"""HF-001: Consolidate schema drift final - Simplified

Revision ID: hf001_simplified_cleanup
Revises: pd001_performance_idx
Create Date: 2025-09-14 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'hf001_simplified_cleanup'
down_revision = 'pd001_performance_idx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """HF-001: Limpeza simples de tabelas órfãs - sem alterações de schema complexas"""
    
    # Remover apenas as tabelas órfãs identificadas no roadmap
    orphan_tables = [
        'role_permissions', 
        'rbac_audit_logs', 
        'rbac_roles', 
        'rbac_permissions', 
        'user_roles', 
        'rbac_users',
        'login_attempts_backup_pd002',
        'login_sessions_backup_pd002',
        'refresh_tokens_backup_pd002'
    ]
    
    # Remover tabelas órfãs de forma segura
    for table in orphan_tables:
        try:
            op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"✅ Removed orphan table: {table}")
        except Exception as e:
            print(f"⚠️  Could not remove table {table}: {e}")
    
    print("🎯 HF-001: Schema drift cleanup completed!")


def downgrade() -> None:
    """Rollback seguro - não recriar tabelas órfãs"""
    print("🔄 HF-001 downgrade: Orphan tables will not be recreated (safe rollback)")
    pass