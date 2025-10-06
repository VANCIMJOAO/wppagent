"""dashboard_fields_add_first_response_and_feedback

Adiciona campos e tabelas necessários para o Dashboard:
- Campo first_response_at na tabela conversations
- Tabela customer_feedback para scores de satisfação
- Índices de performance para queries do dashboard

Revision ID: dc92f4f1d77f
Revises: 5ca45ab6ca59
Create Date: 2025-10-03 14:54:13.614239-03:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dc92f4f1d77f'
down_revision = '5ca45ab6ca59'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. ADICIONAR CAMPO first_response_at em conversations
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    op.add_column('conversations',
        sa.Column('first_response_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Criar índice para performance
    op.create_index(
        'idx_conversations_first_response',
        'conversations',
        ['first_response_at']
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. CRIAR TABELA customer_feedback
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    op.create_table('customer_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('feedback_type', sa.String(50), nullable=True),  # nps, csat, ces, etc
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range')
    )
    
    # Índices para customer_feedback
    op.create_index('idx_feedback_created_at', 'customer_feedback', ['created_at'])
    op.create_index('idx_feedback_rating', 'customer_feedback', ['rating'])
    op.create_index('idx_feedback_conversation', 'customer_feedback', ['conversation_id'])
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. CRIAR ÍNDICES ADICIONAIS PARA PERFORMANCE DO DASHBOARD
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Índice composto para queries de conversão por período
    op.create_index(
        'idx_conversations_created_status',
        'conversations',
        ['created_at', 'status']
    )


def downgrade() -> None:
    # Remover índices
    op.drop_index('idx_conversations_created_status', table_name='conversations')
    op.drop_index('idx_feedback_conversation', table_name='customer_feedback')
    op.drop_index('idx_feedback_rating', table_name='customer_feedback')
    op.drop_index('idx_feedback_created_at', table_name='customer_feedback')
    
    # Remover tabela customer_feedback
    op.drop_table('customer_feedback')
    
    # Remover índice de first_response_at
    op.drop_index('idx_conversations_first_response', table_name='conversations')
    
    # Remover campo first_response_at
    op.drop_column('conversations', 'first_response_at')
