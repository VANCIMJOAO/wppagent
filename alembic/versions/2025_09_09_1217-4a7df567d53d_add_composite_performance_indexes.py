"""add_composite_performance_indexes

Revision ID: 4a7df567d53d
Revises: 721a97f0b961
Create Date: 2025-09-09 12:17:33.544449-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a7df567d53d'
down_revision = '721a97f0b961'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar índices compostos para melhorar performance de consultas críticas
    
    # Índice composto para messages - consultas por usuário ordenadas por data
    op.create_index('idx_messages_user_created', 'messages', ['user_id', 'created_at'])
    
    # Índice composto para appointments - consultas por data e status juntos
    op.create_index('idx_appointments_datetime_status', 'appointments', ['date_time', 'status'])


def downgrade() -> None:
    # Remover índices compostos criados
    op.drop_index('idx_appointments_datetime_status', 'appointments')
    op.drop_index('idx_messages_user_created', 'messages')
