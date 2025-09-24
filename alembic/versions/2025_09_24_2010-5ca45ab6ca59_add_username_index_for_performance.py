"""add_username_index_for_performance

Revision ID: 5ca45ab6ca59
Revises: dbfccfc4f44c
Create Date: 2025-09-24 20:10:47.218022-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ca45ab6ca59'
down_revision = 'dbfccfc4f44c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adicionar índice na coluna username para otimizar performance de login"""
    
    # Criar índice na coluna username da tabela admin_users
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_users_username 
        ON admin_users(username);
    """)
    
    # Criar índice composto para otimizar queries de autenticação
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_users_username_active 
        ON admin_users(username) 
        WHERE is_active = true;
    """)


def downgrade() -> None:
    """Remover índices criados"""
    
    # Remover índices
    op.execute("DROP INDEX IF EXISTS idx_admin_users_username_active;")
    op.execute("DROP INDEX IF EXISTS idx_admin_users_username;")
