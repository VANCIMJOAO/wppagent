"""PD001: Índices de performance críticos

Revision ID: pd001_performance_idx
Revises: hf003_consolidate_auth
Create Date: 2025-09-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pd001_performance_idx'
down_revision = 'hf003_consolidate_auth'
branch_labels = None
depends_on = None


def upgrade():
    """PD001 - Criar índices compostos críticos para eliminar N+1 e otimizar performance"""
    
    # 1. Índice composto para conversas por usuário e data
    # Otimiza: ORDER BY last_message_at + filtro por user_id
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_user_last_message
        ON conversations(user_id, last_message_at DESC)
    """)
    
    # 2. Índice composto para mensagens por conversa e data  
    # Otimiza: busca de mensagens por conversa ordenadas por data
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
        ON messages(conversation_id, created_at DESC)
    """)
    
    # 3. Índice composto para appointments por business e data
    # Otimiza: listagem de appointments por empresa ordenados por data
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointments_business_datetime
        ON appointments(business_id, date_time DESC)
    """)
    
    # 4. Índice composto para appointments por usuário e status
    # Otimiza: filtros de appointments por usuário e status
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_appointments_user_status_date
        ON appointments(user_id, status, date_time DESC)
    """)
    
    # 5. Índice para contagem de mensagens por conversa (otimização crítica)
    # Otimiza: COUNT(messages) por conversation_id + filtro direction
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_count
        ON messages(conversation_id) WHERE direction = 'in'
    """)
    
    # 6. Índice para filtros de status com data
    # Otimiza: conversas ativas/pendentes ordenadas por última mensagem
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_status_last_message
        ON conversations(status, last_message_at DESC) WHERE status IN ('active', 'pending')
    """)
    
    # 7. Índice para user lookups por telefone (WhatsApp integration)
    # Otimiza: busca de usuários por telefone (comum em webhooks)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_telefone
        ON users(telefone)
    """)
    
    # 8. Índice composto para services por business
    # Otimiza: listagem de serviços por empresa
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_services_business_active
        ON services(business_id, is_active) WHERE is_active = true
    """)


def downgrade():
    """PD001 - Remover índices se necessário"""
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_conversations_user_last_message")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_messages_conversation_created")  
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_appointments_business_datetime")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_appointments_user_status_date")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_messages_conversation_count")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_conversations_status_last_message")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_users_telefone")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_services_business_active")
