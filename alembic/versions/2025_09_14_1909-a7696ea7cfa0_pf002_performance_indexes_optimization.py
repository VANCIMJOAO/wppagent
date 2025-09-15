"""pf002_performance_indexes_optimization

Revision ID: a7696ea7cfa0
Revises: hf001_simplified_cleanup
Create Date: 2025-09-14 19:09:37.513783-03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7696ea7cfa0'
down_revision = 'hf001_simplified_cleanup'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    PF-002: Índices de Performance
    Criar índices compostos otimizados para queries frequentes do sistema
    """
    
    # 1. Appointments - principal gargalo de performance
    # Índice otimizado para queries de agendamentos por usuário, data e status
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointments_user_date_status 
        ON appointments (user_id, date_time DESC, status)
        WHERE status IN ('agendado', 'confirmado', 'concluido')
    """)
    
    # 2. Messages - conversas em tempo real
    # Índice para listagem de mensagens por conversa ordenadas por data
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_created 
        ON messages (conversation_id, created_at DESC)
    """)
    
    # 3. Conversations - dashboard principal
    # Índice para listagem de conversas por usuário e status
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_user_status 
        ON conversations (user_id, status, last_message_at DESC)
    """)
    
    # 4. Admin auth - login frequente
    # Índice otimizado para autenticação de administradores ativos
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_admin_users_email_active 
        ON admin_users (email, is_active) 
        WHERE is_active = true
    """)
    
    # 5. Services lookup - consultas de serviços
    # Índice para busca de serviços ativos por business
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_services_business_active 
        ON services (business_id, is_active) 
        WHERE is_active = true
    """)
    
    # 6. Login sessions - cleanup e validação
    # Índice para limpeza de sessões expiradas
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_login_sessions_expires 
        ON login_sessions (expires_at, is_active) 
        WHERE is_active = true
    """)


def downgrade() -> None:
    """
    Remover índices criados pelo PF-002
    """
    op.drop_index('idx_appointments_user_date_status', table_name='appointments')
    op.drop_index('idx_messages_conversation_created', table_name='messages')
    op.drop_index('idx_conversations_user_status', table_name='conversations')
    op.drop_index('idx_admin_users_email_active', table_name='admin_users')
    op.drop_index('idx_services_business_active', table_name='services')
    op.drop_index('idx_login_sessions_expires', table_name='login_sessions')
