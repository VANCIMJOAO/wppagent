from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
🚀 Database Performance Optimizer - Otimizações de Índices e Queries
Cria índices otimizados e implementa queries com melhor performance
"""

# SQL para criar índices otimizados
OPTIMIZED_INDEXES = """
-- Índices para tabela users (operações mais frequentes)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_wa_id_hash 
ON users USING hash(wa_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at_btree
ON users USING btree(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_nome_gin
ON users USING gin(to_tsvector('portuguese', nome));

-- Índices para tabela conversations (queries por usuário e status)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_status
ON conversations USING btree(user_id, status, last_message_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_active_recent
ON conversations USING btree(last_message_at DESC)
WHERE status = 'active';

-- Índices para tabela messages (queries por conversa e timestamp)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_conversation_timestamp
ON messages USING btree(conversation_id, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_user_timestamp
ON messages USING btree(user_id, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_content_gin
ON messages USING gin(to_tsvector('portuguese', content));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_type_timestamp
ON messages USING btree(message_type, timestamp DESC);

-- Índices para tabela appointments (queries por data e status)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_user_date
ON appointments USING btree(user_id, appointment_date DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_date_status
ON appointments USING btree(appointment_date, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_pending_recent
ON appointments USING btree(appointment_date DESC)
WHERE status = 'pending';

-- Índices para tabela available_slots (queries por data)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_available_slots_date_available
ON available_slots USING btree(date, slot_time)
WHERE is_available = true;

-- Índices para login_sessions (segurança e limpeza)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_login_sessions_token_hash
ON login_sessions USING hash(session_token);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_login_sessions_expires_at
ON login_sessions USING btree(expires_at)
WHERE is_active = true;

-- Índices para meta_logs (monitoramento)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_meta_logs_created_at
ON meta_logs USING btree(created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_meta_logs_level_created
ON meta_logs USING btree(level, created_at DESC);

-- Índices compostos para queries complexas
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_conversation_message
ON messages USING btree(user_id, conversation_id, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_business_service_active
ON services USING btree(business_id, is_active, created_at DESC);
"""

# Queries otimizadas mais comuns
OPTIMIZED_QUERIES = {
    "get_user_by_wa_id": """
        SELECT id, wa_id, nome, telefone, email, created_at, updated_at
        FROM users 
        WHERE wa_id = %(wa_id)s
        LIMIT 1
    """,
    
    "get_recent_conversations": """
        SELECT c.id, c.status, c.last_message_at, c.created_at,
               u.wa_id, u.nome
        FROM conversations c
        JOIN users u ON c.user_id = u.id
        WHERE c.last_message_at >= NOW() - INTERVAL '7 days'
          AND c.status = 'active'
        ORDER BY c.last_message_at DESC
        LIMIT %(limit)s
    """,
    
    "get_conversation_history": """
        SELECT m.id, m.content, m.message_type, m.timestamp,
               m.metadata, c.status
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = %(user_id)s
          AND m.timestamp >= NOW() - INTERVAL '30 days'
        ORDER BY m.timestamp DESC
        LIMIT %(limit)s
    """,
    
    "get_available_slots_optimized": """
        SELECT slot_time, business_id
        FROM available_slots
        WHERE date = %(date)s 
          AND is_available = true
          AND business_id = %(business_id)s
        ORDER BY slot_time
    """,
    
    "get_user_stats": """
        WITH user_stats AS (
            SELECT 
                COUNT(DISTINCT c.id) as total_conversations,
                COUNT(DISTINCT m.id) as total_messages,
                COUNT(DISTINCT a.id) as total_appointments,
                MAX(m.timestamp) as last_activity
            FROM users u
            LEFT JOIN conversations c ON u.id = c.user_id
            LEFT JOIN messages m ON u.id = m.user_id
            LEFT JOIN appointments a ON u.id = a.user_id
            WHERE u.wa_id = %(wa_id)s
        )
        SELECT * FROM user_stats
    """,
    
    "search_users": """
        SELECT id, wa_id, nome, telefone, email, created_at,
               ts_rank(to_tsvector('portuguese', nome), query) as rank
        FROM users, to_tsquery('portuguese', %(search_term)s) query
        WHERE to_tsvector('portuguese', nome) @@ query
        ORDER BY rank DESC, created_at DESC
        LIMIT %(limit)s
    """,
    
    "get_business_metrics": """
        WITH daily_stats AS (
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as new_users,
                COUNT(DISTINCT CASE WHEN conversations.id IS NOT NULL THEN users.id END) as active_users,
                COUNT(DISTINCT conversations.id) as conversations,
                COUNT(DISTINCT messages.id) as messages
            FROM users
            LEFT JOIN conversations ON users.id = conversations.user_id
            LEFT JOIN messages ON users.id = messages.user_id
            WHERE users.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(users.created_at)
        )
        SELECT 
            date,
            new_users,
            active_users,
            conversations,
            messages,
            SUM(new_users) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) as cumulative_users
        FROM daily_stats
        ORDER BY date DESC
    """,
    
    "cleanup_old_sessions": """
        DELETE FROM login_sessions 
        WHERE expires_at < NOW() 
           OR (created_at < NOW() - INTERVAL '30 days' AND is_active = false)
    """,
    
    "cleanup_old_messages": """
        DELETE FROM messages 
        WHERE timestamp < NOW() - INTERVAL '%(days)s days'
          AND conversation_id IN (
              SELECT id FROM conversations WHERE status = 'closed'
          )
    """,
    
    "get_popular_intents": """
        SELECT 
            metadata->>'intent' as intent,
            COUNT(*) as frequency,
            AVG(CASE WHEN metadata->>'confidence' IS NOT NULL 
                THEN (metadata->>'confidence')::float ELSE NULL END) as avg_confidence
        FROM messages
        WHERE message_type = 'received'
          AND metadata->>'intent' IS NOT NULL
          AND timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY metadata->>'intent'
        ORDER BY frequency DESC
        LIMIT 20
    """
}

# Configurações de performance por tabela
TABLE_OPTIMIZATIONS = """
-- Configurar autovacuum mais agressivo para tabelas com alta rotatividade
ALTER TABLE messages SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05,
    autovacuum_vacuum_cost_limit = 1000
);

ALTER TABLE login_sessions SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

ALTER TABLE meta_logs SET (
    autovacuum_vacuum_scale_factor = 0.2,
    autovacuum_analyze_scale_factor = 0.1
);

-- Configurar fill factor para tabelas com muitas atualizações
ALTER TABLE conversations SET (fillfactor = 90);
ALTER TABLE appointments SET (fillfactor = 90);
ALTER TABLE available_slots SET (fillfactor = 85);

-- Configurar toast para campos grandes
ALTER TABLE messages ALTER COLUMN content SET STORAGE EXTENDED;
ALTER TABLE messages ALTER COLUMN metadata SET STORAGE EXTENDED;
"""

# Views materializadas para relatórios
MATERIALIZED_VIEWS = """
-- View materializada para métricas diárias
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_metrics AS
SELECT 
    DATE(created_at) as metric_date,
    'users' as metric_type,
    COUNT(*) as metric_value,
    MAX(created_at) as last_updated
FROM users
WHERE created_at >= CURRENT_DATE - INTERVAL '365 days'
GROUP BY DATE(created_at)

UNION ALL

SELECT 
    DATE(timestamp) as metric_date,
    'messages' as metric_type,
    COUNT(*) as metric_value,
    MAX(timestamp) as last_updated
FROM messages
WHERE timestamp >= CURRENT_DATE - INTERVAL '365 days'
GROUP BY DATE(timestamp)

UNION ALL

SELECT 
    DATE(created_at) as metric_date,
    'conversations' as metric_type,
    COUNT(*) as metric_value,
    MAX(created_at) as last_updated
FROM conversations
WHERE created_at >= CURRENT_DATE - INTERVAL '365 days'
GROUP BY DATE(created_at);

-- Índice na view materializada
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_metrics_date_type
ON daily_metrics (metric_date, metric_type);

-- View materializada para estatísticas de usuários ativos
CREATE MATERIALIZED VIEW IF NOT EXISTS user_activity_stats AS
SELECT 
    u.id,
    u.wa_id,
    u.nome,
    COUNT(DISTINCT c.id) as total_conversations,
    COUNT(DISTINCT m.id) as total_messages,
    COUNT(DISTINCT a.id) as total_appointments,
    MAX(m.timestamp) as last_message_at,
    MAX(c.last_message_at) as last_conversation_at,
    CASE 
        WHEN MAX(m.timestamp) >= NOW() - INTERVAL '24 hours' THEN 'highly_active'
        WHEN MAX(m.timestamp) >= NOW() - INTERVAL '7 days' THEN 'active'
        WHEN MAX(m.timestamp) >= NOW() - INTERVAL '30 days' THEN 'moderate'
        ELSE 'inactive'
    END as activity_level
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id
LEFT JOIN messages m ON u.id = m.user_id
LEFT JOIN appointments a ON u.id = a.user_id
GROUP BY u.id, u.wa_id, u.nome;

-- Índices na view de atividade
CREATE INDEX IF NOT EXISTS idx_user_activity_level
ON user_activity_stats (activity_level, last_message_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_activity_wa_id
ON user_activity_stats USING hash(wa_id);
"""

# Função para refresh das views materializadas
REFRESH_MATERIALIZED_VIEWS = """
-- Função para refresh automático das views
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_metrics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_activity_stats;
    
    -- Log do refresh
    INSERT INTO meta_logs (level, message, metadata, created_at)
    VALUES ('INFO', 'Materialized views refreshed', 
            '{"views": ["daily_metrics", "user_activity_stats"]}', NOW());
END;
$$ LANGUAGE plpgsql;

-- Trigger para refresh automático (pode ser chamado via cron)
-- SELECT refresh_materialized_views();
"""
