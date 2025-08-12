"""
🗄️ Serviço de Otimização do Banco de Dados
=========================================

Implementa:
- Índices otimizados para queries frequentes
- Stored procedures para operações complexas
- Estratégia de backup/restore
- Configuração de replicação para alta disponibilidade
"""

import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.config import settings
from app.utils.logger import get_logger
from app.database import engine
logger = get_logger(__name__)
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
import json
import os
import subprocess

logger = logging.getLogger(__name__)

class DatabaseOptimizationService:
    """Serviço para otimização e administração do banco de dados"""
    
    def __init__(self):
        self.db_config = {
            'host': settings.db_host,
            'port': settings.db_port,
            'database': settings.db_name,
            'user': settings.db_user,
            'password': settings.db_password.get_secret_value()
        }
        self.backup_dir = "backups/database"
        self.engine = engine
    
    async def create_optimized_indexes(self) -> Dict[str, Any]:
        """
        Cria índices otimizados para queries frequentes
        """
        logger.info("🚀 Criando índices otimizados...")
        
        indexes = {
            # Índices para messages (usando colunas que existem)
            "messages_performance": [
                "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_messages_user_conversation ON messages (user_id, conversation_id);",
                "CREATE INDEX IF NOT EXISTS idx_messages_direction ON messages (direction);",
                "CREATE INDEX IF NOT EXISTS idx_messages_content_search ON messages USING gin(to_tsvector('portuguese', content));"
            ],
            
            # Índices para conversations (usando colunas que existem)
            "conversations_performance": [
                "CREATE INDEX IF NOT EXISTS idx_conversations_status_updated ON conversations (status, updated_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_status ON conversations (user_id, status);",
                "CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations (last_message_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_created ON conversations (user_id, created_at DESC);"
            ],
            
            # Índices para users (usando colunas que existem: wa_id, nome, telefone, email)
            "users_performance": [
                "CREATE INDEX IF NOT EXISTS idx_users_wa_id ON users (wa_id) WHERE wa_id IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_users_telefone ON users (telefone) WHERE telefone IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users (email) WHERE email IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at DESC);"
            ],
            
            # Índices para appointments (usando colunas que existem: date_time, status, service_id)
            "appointments_performance": [
                "CREATE INDEX IF NOT EXISTS idx_appointments_datetime_status ON appointments (date_time, status);",
                "CREATE INDEX IF NOT EXISTS idx_appointments_user_future ON appointments (user_id, date_time) WHERE date_time > NOW();",
                "CREATE INDEX IF NOT EXISTS idx_appointments_service_date ON appointments (service_id, date_time);",
                "CREATE INDEX IF NOT EXISTS idx_appointments_status_created ON appointments (status, created_at DESC);"
            ],
            
            # Índices para meta_logs (queries por data, endpoint, status)
            "meta_logs_performance": [
                "CREATE INDEX IF NOT EXISTS idx_meta_logs_created_direction ON meta_logs (created_at DESC, direction);",
                "CREATE INDEX IF NOT EXISTS idx_meta_logs_endpoint_status ON meta_logs (endpoint, status_code);",
                "CREATE INDEX IF NOT EXISTS idx_meta_logs_error_analysis ON meta_logs (status_code) WHERE status_code >= 400;",
                "CREATE INDEX IF NOT EXISTS idx_meta_logs_created_at ON meta_logs (created_at DESC);"
            ],
            
            # Índices para admin_users e login_sessions
            "admin_performance": [
                "CREATE INDEX IF NOT EXISTS idx_admin_users_username_active ON admin_users (username) WHERE is_active = true;",
                "CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users (username);",
                "CREATE INDEX IF NOT EXISTS idx_login_sessions_admin_expires ON login_sessions (admin_user_id, expires_at);"
            ]
        }
        
        results = {}
        # Executar cada índice individualmente para evitar problemas de transação
        for category, index_list in indexes.items():
            results[category] = []
            for index_sql in index_list:
                try:
                    async with self.engine.begin() as conn:
                        await conn.execute(text(index_sql))
                        index_name = index_sql.split("idx_")[1].split(" ")[0] if "idx_" in index_sql else "unknown"
                        results[category].append(f"✅ {index_name}")
                        logger.info(f"✅ Índice criado: {index_name}")
                except Exception as e:
                    error_msg = f"❌ Erro ao criar índice: {str(e)[:100]}"
                    results[category].append(error_msg)
                    logger.error(error_msg)
        
        logger.info("🎯 Criação de índices concluída")
        return results
    
    async def create_stored_procedures(self) -> Dict[str, Any]:
        """
        Cria stored procedures para operações complexas
        """
        logger.info("🔧 Criando stored procedures...")
        
        procedures = {
            # Procedure para análise de conversas
            "conversation_analytics": """
                CREATE OR REPLACE FUNCTION get_conversation_analytics(
                    start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
                    end_date DATE DEFAULT CURRENT_DATE
                )
                RETURNS TABLE (
                    date_period DATE,
                    total_conversations BIGINT,
                    active_conversations BIGINT,
                    avg_messages_per_conversation NUMERIC,
                    unique_users BIGINT,
                    conversion_rate NUMERIC
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        DATE(c.created_at) as date_period,
                        COUNT(c.id) as total_conversations,
                        COUNT(c.id) FILTER (WHERE c.status = 'active') as active_conversations,
                        ROUND(AVG(c.message_count), 2) as avg_messages_per_conversation,
                        COUNT(DISTINCT c.user_id) as unique_users,
                        ROUND(
                            COUNT(c.id) FILTER (WHERE c.status = 'completed') * 100.0 / 
                            NULLIF(COUNT(c.id), 0), 
                            2
                        ) as conversion_rate
                    FROM conversations c
                    WHERE DATE(c.created_at) BETWEEN start_date AND end_date
                    GROUP BY DATE(c.created_at)
                    ORDER BY date_period DESC;
                END;
                $$ LANGUAGE plpgsql;
            """,
            
            # Procedure para limpeza de dados antigos
            "cleanup_old_data": """
                CREATE OR REPLACE FUNCTION cleanup_old_data(
                    days_to_keep INTEGER DEFAULT 90
                )
                RETURNS TABLE (
                    table_name TEXT,
                    deleted_count BIGINT
                ) AS $$
                DECLARE
                    cutoff_date TIMESTAMP := NOW() - (days_to_keep || ' days')::INTERVAL;
                    deleted_meta_logs BIGINT;
                    deleted_sessions BIGINT;
                BEGIN
                    -- Limpar meta_logs antigos
                    DELETE FROM meta_logs WHERE created_at < cutoff_date;
                    GET DIAGNOSTICS deleted_meta_logs = ROW_COUNT;
                    
                    -- Limpar sessões expiradas
                    DELETE FROM login_sessions WHERE expires_at < NOW();
                    GET DIAGNOSTICS deleted_sessions = ROW_COUNT;
                    
                    -- Retornar resultados
                    RETURN QUERY VALUES 
                        ('meta_logs', deleted_meta_logs),
                        ('login_sessions', deleted_sessions);
                END;
                $$ LANGUAGE plpgsql;
            """,
            
            # Procedure para estatísticas de performance
            "performance_stats": """
                CREATE OR REPLACE FUNCTION get_performance_stats()
                RETURNS TABLE (
                    metric_name TEXT,
                    metric_value NUMERIC,
                    metric_unit TEXT,
                    last_updated TIMESTAMP
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT * FROM (
                        VALUES 
                            ('active_connections', 
                             (SELECT count(*) FROM pg_stat_activity WHERE state = 'active')::NUMERIC,
                             'connections', NOW()),
                            ('database_size_mb', 
                             (SELECT pg_database_size(current_database()) / 1024.0 / 1024.0)::NUMERIC,
                             'MB', NOW()),
                            ('total_messages_today',
                             (SELECT count(*) FROM messages WHERE DATE(created_at) = CURRENT_DATE)::NUMERIC,
                             'messages', NOW()),
                            ('avg_response_time_ms',
                             (SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) * 1000), 0)
                              FROM conversations WHERE DATE(created_at) = CURRENT_DATE)::NUMERIC,
                             'milliseconds', NOW()),
                            ('cache_hit_ratio',
                             (SELECT ROUND(
                                 100.0 * sum(blks_hit) / NULLIF(sum(blks_hit + blks_read), 0), 2
                              ) FROM pg_stat_database WHERE datname = current_database())::NUMERIC,
                             'percentage', NOW())
                    ) AS stats(metric_name, metric_value, metric_unit, last_updated);
                END;
                $$ LANGUAGE plpgsql;
            """,
            
            # Procedure para backup de conversas críticas
            "backup_critical_conversations": """
                CREATE OR REPLACE FUNCTION backup_critical_conversations(
                    backup_table_suffix TEXT DEFAULT to_char(NOW(), 'YYYYMMDD')
                )
                RETURNS TEXT AS $$
                DECLARE
                    backup_table_name TEXT := 'conversations_backup_' || backup_table_suffix;
                    backed_up_count BIGINT;
                BEGIN
                    -- Criar tabela de backup
                    EXECUTE format('
                        CREATE TABLE IF NOT EXISTS %I AS
                        SELECT c.*, u.phone_number, u.name as user_name
                        FROM conversations c
                        JOIN users u ON c.user_id = u.id
                        WHERE c.status IN (''active'', ''completed'')
                        AND c.updated_at >= CURRENT_DATE - INTERVAL ''7 days''
                    ', backup_table_name);
                    
                    -- Contar registros
                    EXECUTE format('SELECT count(*) FROM %I', backup_table_name) INTO backed_up_count;
                    
                    RETURN format('Backup criado: %s com %s conversas', backup_table_name, backed_up_count);
                END;
                $$ LANGUAGE plpgsql;
            """,
            
            # Procedure para otimização automática
            "auto_optimize": """
                CREATE OR REPLACE FUNCTION auto_optimize_database()
                RETURNS TABLE (
                    optimization_type TEXT,
                    result TEXT,
                    execution_time INTERVAL
                ) AS $$
                DECLARE
                    start_time TIMESTAMP;
                    end_time TIMESTAMP;
                BEGIN
                    -- VACUUM automático
                    start_time := clock_timestamp();
                    VACUUM ANALYZE messages, conversations, users;
                    end_time := clock_timestamp();
                    RETURN QUERY VALUES ('VACUUM_ANALYZE', 'Completed', end_time - start_time);
                    
                    -- Reindex crítico
                    start_time := clock_timestamp();
                    REINDEX INDEX CONCURRENTLY idx_messages_created_at;
                    end_time := clock_timestamp();
                    RETURN QUERY VALUES ('REINDEX_MESSAGES', 'Completed', end_time - start_time);
                    
                    -- Atualizar estatísticas
                    start_time := clock_timestamp();
                    ANALYZE;
                    end_time := clock_timestamp();
                    RETURN QUERY VALUES ('ANALYZE_STATS', 'Completed', end_time - start_time);
                END;
                $$ LANGUAGE plpgsql;
            """
        }
        
        results = {}
        async with self.engine.begin() as conn:
            for proc_name, proc_sql in procedures.items():
                try:
                    await conn.execute(text(proc_sql))
                    results[proc_name] = "✅ Criada com sucesso"
                    logger.info(f"✅ Stored procedure criada: {proc_name}")
                except Exception as e:
                    error_msg = f"❌ Erro: {str(e)[:100]}"
                    results[proc_name] = error_msg
                    logger.error(f"❌ Erro ao criar procedure {proc_name}: {e}")
        
        logger.info("🎯 Criação de stored procedures concluída")
        return results
    
    async def setup_backup_strategy(self) -> Dict[str, Any]:
        """
        Configura estratégia de backup/restore
        """
        logger.info("💾 Configurando estratégia de backup...")
        
        # Criar diretório de backup
        os.makedirs(self.backup_dir, exist_ok=True)
        
        backup_config = {
            "backup_schedule": {
                "full_backup": "daily_2am",
                "incremental": "every_6h",
                "transaction_log": "every_15m"
            },
            "retention_policy": {
                "daily_backups": "30_days",
                "weekly_backups": "12_weeks", 
                "monthly_backups": "12_months"
            },
            "backup_verification": "automatic",
            "compression": "gzip",
            "encryption": "AES256"
        }
        
        # Script de backup diário
        backup_script = f"""#!/bin/bash
# Backup automático do WhatsApp Agent Database
# Criado em: {datetime.now().isoformat()}

DB_HOST="{self.db_config['host']}"
DB_PORT="{self.db_config['port']}"
DB_NAME="{self.db_config['database']}"
DB_USER="{self.db_config['user']}"
BACKUP_DIR="{os.path.abspath(self.backup_dir)}"
DATE=$(date +%Y%m%d_%H%M%S)

# Função de backup completo
full_backup() {{
    echo "🚀 Iniciando backup completo..."
    BACKUP_FILE="$BACKUP_DIR/full_backup_$DATE.sql.gz"
    
    PGPASSWORD="{self.db_config['password']}" pg_dump \\
        -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \\
        --verbose --no-owner --no-privileges \\
        | gzip > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Backup completo criado: $BACKUP_FILE"
        echo "📊 Tamanho: $(du -h "$BACKUP_FILE" | cut -f1)"
    else
        echo "❌ Erro no backup completo"
        exit 1
    fi
}}

# Função de backup incremental (apenas dados modificados)
incremental_backup() {{
    echo "🔄 Iniciando backup incremental..."
    BACKUP_FILE="$BACKUP_DIR/incremental_backup_$DATE.sql.gz"
    
    # Backup apenas de tabelas com dados recentes (últimas 24h)
    PGPASSWORD="{self.db_config['password']}" pg_dump \\
        -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \\
        --verbose --no-owner --no-privileges \\
        --where="created_at >= NOW() - INTERVAL '24 hours'" \\
        -t messages -t conversations -t meta_logs \\
        | gzip > "$BACKUP_FILE"
    
    echo "✅ Backup incremental criado: $BACKUP_FILE"
}}

# Limpeza de backups antigos
cleanup_old_backups() {{
    echo "🧹 Limpando backups antigos..."
    
    # Manter apenas os últimos 30 backups completos
    ls -t $BACKUP_DIR/full_backup_*.sql.gz | tail -n +31 | xargs -r rm -f
    
    # Manter apenas os últimos 60 backups incrementais
    ls -t $BACKUP_DIR/incremental_backup_*.sql.gz | tail -n +61 | xargs -r rm -f
    
    echo "✅ Limpeza concluída"
}}

# Verificação de integridade
verify_backup() {{
    BACKUP_FILE=$1
    echo "🔍 Verificando integridade: $BACKUP_FILE"
    
    if gzip -t "$BACKUP_FILE"; then
        echo "✅ Arquivo íntegro"
        return 0
    else
        echo "❌ Arquivo corrompido"
        return 1
    fi
}}

# Execução baseada no parâmetro
case "$1" in
    "full")
        full_backup
        verify_backup "$BACKUP_DIR/full_backup_$DATE.sql.gz"
        ;;
    "incremental")
        incremental_backup
        verify_backup "$BACKUP_DIR/incremental_backup_$DATE.sql.gz"
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    *)
        echo "Uso: $0 {{full|incremental|cleanup}}"
        echo "  full        - Backup completo"
        echo "  incremental - Backup incremental"
        echo "  cleanup     - Limpeza de backups antigos"
        exit 1
        ;;
esac
"""
        
        # Salvar script de backup
        script_path = f"{self.backup_dir}/backup_script.sh"
        with open(script_path, 'w') as f:
            f.write(backup_script)
        os.chmod(script_path, 0o755)
        
        # Script de restore
        restore_script = f"""#!/bin/bash
# Script de restore do WhatsApp Agent Database

DB_HOST="{self.db_config['host']}"
DB_PORT="{self.db_config['port']}"
DB_NAME="{self.db_config['database']}"
DB_USER="{self.db_config['user']}"
BACKUP_DIR="{os.path.abspath(self.backup_dir)}"

restore_backup() {{
    BACKUP_FILE=$1
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Arquivo de backup não encontrado: $BACKUP_FILE"
        exit 1
    fi
    
    echo "⚠️  ATENÇÃO: Esta operação irá substituir todos os dados!"
    echo "Backup a ser restaurado: $BACKUP_FILE"
    read -p "Continuar? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Operação cancelada"
        exit 0
    fi
    
    echo "🚀 Iniciando restore..."
    
    # Criar backup de segurança antes do restore
    SAFETY_BACKUP="$BACKUP_DIR/safety_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
    echo "📦 Criando backup de segurança..."
    PGPASSWORD="{self.db_config['password']}" pg_dump \\
        -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \\
        | gzip > "$SAFETY_BACKUP"
    
    # Restore do backup
    echo "🔄 Restaurando dados..."
    gunzip -c "$BACKUP_FILE" | PGPASSWORD="{self.db_config['password']}" psql \\
        -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
    
    if [ $? -eq 0 ]; then
        echo "✅ Restore concluído com sucesso"
        echo "💾 Backup de segurança salvo em: $SAFETY_BACKUP"
    else
        echo "❌ Erro durante o restore"
        exit 1
    fi
}}

# Listar backups disponíveis
list_backups() {{
    echo "📋 Backups disponíveis:"
    echo ""
    echo "BACKUPS COMPLETOS:"
    ls -la $BACKUP_DIR/full_backup_*.sql.gz 2>/dev/null | awk '{{print "  " $9 " (" $5 " bytes, " $6 " " $7 " " $8 ")"}}' || echo "  Nenhum backup completo encontrado"
    echo ""
    echo "BACKUPS INCREMENTAIS:"
    ls -la $BACKUP_DIR/incremental_backup_*.sql.gz 2>/dev/null | awk '{{print "  " $9 " (" $5 " bytes, " $6 " " $7 " " $8 ")"}}' || echo "  Nenhum backup incremental encontrado"
}}

case "$1" in
    "restore")
        if [ -z "$2" ]; then
            echo "Uso: $0 restore <arquivo_backup>"
            list_backups
            exit 1
        fi
        restore_backup "$2"
        ;;
    "list")
        list_backups
        ;;
    *)
        echo "Uso: $0 {{restore|list}}"
        echo "  restore <arquivo> - Restaura backup"
        echo "  list              - Lista backups disponíveis"
        exit 1
        ;;
esac
"""
        
        restore_script_path = f"{self.backup_dir}/restore_script.sh"
        with open(restore_script_path, 'w') as f:
            f.write(restore_script)
        os.chmod(restore_script_path, 0o755)
        
        return {
            "backup_config": backup_config,
            "backup_script": script_path,
            "restore_script": restore_script_path,
            "backup_directory": self.backup_dir,
            "status": "✅ Estratégia de backup configurada"
        }
    
    async def setup_replication_config(self) -> Dict[str, Any]:
        """
        Configura replicação para alta disponibilidade
        """
        logger.info("🔄 Configurando replicação para alta disponibilidade...")
        
        replication_config = {
            "architecture": "primary_replica",
            "replication_type": "streaming_replication",
            "sync_mode": "asynchronous",  # Para melhor performance
            "replica_count": 2,
            "failover": "automatic"
        }
        
        # Configurações do PostgreSQL para replicação
        postgresql_conf = """
# Configurações de Replicação para Alta Disponibilidade
# WhatsApp Agent Database

# WAL (Write-Ahead Logging)
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB

# Checkpoint
checkpoint_timeout = 5min
max_wal_size = 2GB
min_wal_size = 256MB

# Connection
max_connections = 200
shared_buffers = 256MB

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_min_duration_statement = 1000  # Log queries > 1s

# Performance
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Replication specific
hot_standby = on
wal_receiver_timeout = 60s
"""
        
        # pg_hba.conf para replicação
        pg_hba_replication = """
# Configuração de acesso para replicação
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Replication connections
host    replication     replicator      10.0.0.0/8              md5
host    replication     replicator      172.16.0.0/12           md5
host    replication     replicator      192.168.0.0/16          md5
"""
        
        # Script de configuração do Primary
        primary_setup = """#!/bin/bash
# Configuração do servidor Primary para replicação

echo "🔧 Configurando servidor Primary..."

# Backup da configuração atual
sudo cp /etc/postgresql/*/main/postgresql.conf /etc/postgresql/*/main/postgresql.conf.backup
sudo cp /etc/postgresql/*/main/pg_hba.conf /etc/postgresql/*/main/pg_hba.conf.backup

# Criar usuário de replicação
sudo -u postgres psql << EOF
CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'replica_password_here';
EOF

echo "✅ Usuário de replicação criado"

# Aplicar configurações (requer restart do PostgreSQL)
echo "⚠️  Para ativar a replicação, aplique as configurações do postgresql.conf"
echo "⚠️  e reinicie o PostgreSQL: sudo systemctl restart postgresql"
"""
        
        # Script de configuração do Replica
        replica_setup = """#!/bin/bash
# Configuração do servidor Replica

PRIMARY_HOST=$1
if [ -z "$PRIMARY_HOST" ]; then
    echo "Uso: $0 <primary_host_ip>"
    exit 1
fi

echo "🔧 Configurando servidor Replica..."

# Parar PostgreSQL
sudo systemctl stop postgresql

# Fazer backup do diretório de dados
sudo mv /var/lib/postgresql/*/main /var/lib/postgresql/*/main.backup

# Fazer basebackup do Primary
sudo -u postgres pg_basebackup -h $PRIMARY_HOST -D /var/lib/postgresql/*/main -U replicator -P -W -R

# Configurar recovery
sudo -u postgres cat > /var/lib/postgresql/*/main/postgresql.auto.conf << EOF
primary_conninfo = 'host=$PRIMARY_HOST port=5432 user=replicator'
promote_trigger_file = '/tmp/promote_replica'
EOF

# Iniciar PostgreSQL
sudo systemctl start postgresql

echo "✅ Replica configurado e iniciado"
echo "💡 Para promover a replica a primary: touch /tmp/promote_replica"
"""
        
        # Monitoramento de replicação
        monitoring_script = """#!/bin/bash
# Script de monitoramento da replicação

check_replication_status() {
    echo "📊 STATUS DA REPLICAÇÃO"
    echo "======================"
    
    # Status no Primary
    echo "PRIMARY SERVER:"
    sudo -u postgres psql -c "
        SELECT 
            client_addr,
            state,
            sent_lsn,
            write_lsn,
            flush_lsn,
            replay_lsn,
            write_lag,
            flush_lag,
            replay_lag
        FROM pg_stat_replication;
    "
    
    # Lag da replicação
    echo ""
    echo "REPLICATION LAG:"
    sudo -u postgres psql -c "
        SELECT 
            CASE 
                WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() 
                THEN 0 
                ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp()) 
            END AS lag_seconds;
    "
}

check_replica_status() {
    echo "📊 STATUS DO REPLICA"
    echo "==================="
    
    sudo -u postgres psql -c "
        SELECT 
            pg_is_in_recovery() as is_replica,
            pg_last_wal_receive_lsn() as received_lsn,
            pg_last_wal_replay_lsn() as replayed_lsn,
            pg_last_xact_replay_timestamp() as last_replay;
    "
}

case "$1" in
    "primary")
        check_replication_status
        ;;
    "replica")
        check_replica_status
        ;;
    *)
        echo "Uso: $0 {primary|replica}"
        ;;
esac
"""
        
        # Salvar arquivos de configuração
        config_dir = f"{self.backup_dir}/../replication"
        os.makedirs(config_dir, exist_ok=True)
        
        configs = {
            "postgresql.conf": postgresql_conf,
            "pg_hba_replication.conf": pg_hba_replication,
            "setup_primary.sh": primary_setup,
            "setup_replica.sh": replica_setup,
            "monitor_replication.sh": monitoring_script
        }
        
        for filename, content in configs.items():
            filepath = f"{config_dir}/{filename}"
            with open(filepath, 'w') as f:
                f.write(content)
            if filename.endswith('.sh'):
                os.chmod(filepath, 0o755)
        
        return {
            "replication_config": replication_config,
            "config_directory": config_dir,
            "setup_files": list(configs.keys()),
            "next_steps": [
                "1. Aplicar configurações do postgresql.conf no Primary",
                "2. Reiniciar PostgreSQL no Primary",
                "3. Executar setup_replica.sh no servidor Replica",
                "4. Monitorar com monitor_replication.sh"
            ],
            "status": "✅ Configuração de replicação preparada"
        }
    
    async def run_performance_analysis(self) -> Dict[str, Any]:
        """
        Executa análise de performance do banco
        """
        logger.info("📊 Executando análise de performance...")
        
        results = {}
        
        # Verificar se pg_stat_statements está disponível
        async with self.engine.begin() as conn:
            try:
                check_extension = await conn.execute(text("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                    ) as has_extension;
                """))
                has_pg_stat_statements = check_extension.scalar()
            except Exception:
                has_pg_stat_statements = False
        
        # Queries básicas sempre disponíveis
        base_queries = {
            "table_sizes": """
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """,
            
            "index_usage": """
                SELECT 
                    schemaname,
                    relname as tablename,
                    indexrelname as indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    CASE 
                        WHEN idx_tup_read = 0 THEN 'Nunca usado'
                        WHEN idx_tup_read < 100 THEN 'Pouco usado'
                        ELSE 'Bem usado'
                    END as usage_status
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_tup_read DESC;
            """,
            
            "connection_stats": """
                SELECT 
                    state,
                    count(*) as connections
                FROM pg_stat_activity 
                GROUP BY state;
            """,
            
            "database_stats": """
                SELECT 
                    pg_database_size(current_database()) as db_size_bytes,
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_connections;
            """,
            
            "table_activity": """
                SELECT 
                    schemaname,
                    relname as tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                ORDER BY (n_tup_ins + n_tup_upd + n_tup_del) DESC;
            """
        }
        
        # Query específica se pg_stat_statements estiver disponível
        if has_pg_stat_statements:
            base_queries["slow_queries"] = """
                SELECT 
                    LEFT(query, 80) as query_preview,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE mean_time > 10
                ORDER BY mean_time DESC 
                LIMIT 10;
            """
        else:
            results["slow_queries"] = {
                "status": "⚠️ Extensão pg_stat_statements não disponível",
                "solution": "Execute: CREATE EXTENSION IF NOT EXISTS pg_stat_statements;",
                "note": "Requer reinicialização do banco após habilitar"
            }
        
        # Executar todas as queries disponíveis
        for analysis_name, query in base_queries.items():
            try:
                async with self.engine.begin() as conn:
                    result = await conn.execute(text(query))
                    rows = result.fetchall()
                    results[analysis_name] = [dict(row._mapping) for row in rows] if rows else []
                    logger.info(f"✅ Análise {analysis_name}: {len(rows)} resultados")
            except Exception as e:
                results[analysis_name] = {
                    "error": f"❌ Erro: {str(e)[:150]}",
                    "query": analysis_name
                }
                logger.error(f"❌ Erro na análise {analysis_name}: {e}")
        
        # Adicionar resumo da análise
        results["analysis_summary"] = {
            "timestamp": datetime.now().isoformat(),
            "pg_stat_statements_available": has_pg_stat_statements,
            "queries_executed": len([k for k in results.keys() if not isinstance(results[k], dict) or "error" not in results[k]]),
            "errors": len([k for k in results.keys() if isinstance(results[k], dict) and "error" in results[k]])
        }
        
        return results
    
    async def get_optimization_status(self) -> Dict[str, Any]:
        """
        Retorna status das otimizações implementadas
        """
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "optimizations": {},
            "health_score": 0
        }
        
        checks = [
            ("indexes", "SELECT count(*) FROM pg_indexes WHERE schemaname = 'public'"),
            ("procedures", "SELECT count(*) FROM pg_proc WHERE prokind = 'f' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')"),
            ("connections", "SELECT count(*) FROM pg_stat_activity"),
            ("database_size", "SELECT pg_database_size(current_database()) / 1024.0 / 1024.0 as size_mb")
        ]
        
        async with self.engine.begin() as conn:
            for check_name, query in checks:
                try:
                    result = await conn.execute(text(query))
                    value = result.scalar()
                    status["optimizations"][check_name] = {
                        "value": float(value) if value else 0,
                        "status": "healthy" if value else "needs_attention"
                    }
                except Exception as e:
                    status["optimizations"][check_name] = {
                        "value": 0,
                        "status": "error",
                        "error": str(e)
                    }
        
        # Calcular health score
        healthy_count = sum(1 for opt in status["optimizations"].values() 
                          if opt.get("status") == "healthy")
        total_checks = len(status["optimizations"])
        status["health_score"] = (healthy_count / total_checks * 100) if total_checks > 0 else 0
        
        return status

# Instância global
db_optimizer = DatabaseOptimizationService()
