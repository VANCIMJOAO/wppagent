#!/bin/bash
# Backup automático do WhatsApp Agent Database
# Criado em: 2025-08-08T20:22:09.328223

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="whats_agent"
DB_USER="vancimj"
BACKUP_DIR="/home/vancim/whats_agent/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)

# Função de backup completo
full_backup() {
    echo "🚀 Iniciando backup completo..."
    BACKUP_FILE="$BACKUP_DIR/full_backup_$DATE.sql.gz"
    
    PGPASSWORD="os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")" pg_dump \
        -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        --verbose --no-owner --no-privileges \
        | gzip > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Backup completo criado: $BACKUP_FILE"
        echo "📊 Tamanho: $(du -h "$BACKUP_FILE" | cut -f1)"
    else
        echo "❌ Erro no backup completo"
        exit 1
    fi
}

# Função de backup incremental (apenas dados modificados)
incremental_backup() {
    echo "🔄 Iniciando backup incremental..."
    BACKUP_FILE="$BACKUP_DIR/incremental_backup_$DATE.sql.gz"
    
    # Backup apenas de tabelas com dados recentes (últimas 24h)
    PGPASSWORD="os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")" pg_dump \
        -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        --verbose --no-owner --no-privileges \
        --where="created_at >= NOW() - INTERVAL '24 hours'" \
        -t messages -t conversations -t meta_logs \
        | gzip > "$BACKUP_FILE"
    
    echo "✅ Backup incremental criado: $BACKUP_FILE"
}

# Limpeza de backups antigos
cleanup_old_backups() {
    echo "🧹 Limpando backups antigos..."
    
    # Manter apenas os últimos 30 backups completos
    ls -t $BACKUP_DIR/full_backup_*.sql.gz | tail -n +31 | xargs -r rm -f
    
    # Manter apenas os últimos 60 backups incrementais
    ls -t $BACKUP_DIR/incremental_backup_*.sql.gz | tail -n +61 | xargs -r rm -f
    
    echo "✅ Limpeza concluída"
}

# Verificação de integridade
verify_backup() {
    BACKUP_FILE=$1
    echo "🔍 Verificando integridade: $BACKUP_FILE"
    
    if gzip -t "$BACKUP_FILE"; then
        echo "✅ Arquivo íntegro"
        return 0
    else
        echo "❌ Arquivo corrompido"
        return 1
    fi
}

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
        echo "Uso: $0 {full|incremental|cleanup}"
        echo "  full        - Backup completo"
        echo "  incremental - Backup incremental"
        echo "  cleanup     - Limpeza de backups antigos"
        exit 1
        ;;
esac
