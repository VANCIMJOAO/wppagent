"""add_performance_indexes

Revision ID: d08ef6b15ecb
Revises: 6897816d7333
Create Date: 2025-08-06 21:34:26.997470-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd08ef6b15ecb'
down_revision = '6897816d7333'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar índices para melhorar performance de consultas
    
    # Índices na tabela conversations
    op.create_index('ix_conversations_status', 'conversations', ['status'])
    op.create_index('ix_conversations_last_message_at', 'conversations', ['last_message_at'])
    
    # Índices na tabela appointments
    op.create_index('ix_appointments_date_time', 'appointments', ['date_time'])
    op.create_index('ix_appointments_status', 'appointments', ['status'])
    
    # Índices na tabela messages
    op.create_index('ix_messages_direction', 'messages', ['direction'])
    op.create_index('ix_messages_message_id', 'messages', ['message_id'])
    op.create_index('ix_messages_message_type', 'messages', ['message_type'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])


def downgrade() -> None:
    # Remover índices criados
    
    # Remover índices da tabela messages
    op.drop_index('ix_messages_created_at', 'messages')
    op.drop_index('ix_messages_message_type', 'messages')
    op.drop_index('ix_messages_message_id', 'messages')
    op.drop_index('ix_messages_direction', 'messages')
    
    # Remover índices da tabela appointments
    op.drop_index('ix_appointments_status', 'appointments')
    op.drop_index('ix_appointments_date_time', 'appointments')
    
    # Remover índices da tabela conversations
    op.drop_index('ix_conversations_last_message_at', 'conversations')
    op.drop_index('ix_conversations_status', 'conversations')
