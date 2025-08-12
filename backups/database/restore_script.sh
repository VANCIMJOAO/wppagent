#!/bin/bash
# Script de restore do WhatsApp Agent Database

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="whats_agent"
DB_USER="vancimj"
BACKUP_DIR="/home/vancim/whats_agent/backups/database"

restore_backup() {
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
    PGPASSWORD="os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")" pg_dump \
        -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        | gzip > "$SAFETY_BACKUP"
    
    # Restore do backup
    echo "🔄 Restaurando dados..."
    gunzip -c "$BACKUP_FILE" | PGPASSWORD="os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")" psql \
        -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
    
    if [ $? -eq 0 ]; then
        echo "✅ Restore concluído com sucesso"
        echo "💾 Backup de segurança salvo em: $SAFETY_BACKUP"
    else
        echo "❌ Erro durante o restore"
        exit 1
    fi
}

# Listar backups disponíveis
list_backups() {
    echo "📋 Backups disponíveis:"
    echo ""
    echo "BACKUPS COMPLETOS:"
    ls -la $BACKUP_DIR/full_backup_*.sql.gz 2>/dev/null | awk '{print "  " $9 " (" $5 " bytes, " $6 " " $7 " " $8 ")"}' || echo "  Nenhum backup completo encontrado"
    echo ""
    echo "BACKUPS INCREMENTAIS:"
    ls -la $BACKUP_DIR/incremental_backup_*.sql.gz 2>/dev/null | awk '{print "  " $9 " (" $5 " bytes, " $6 " " $7 " " $8 ")"}' || echo "  Nenhum backup incremental encontrado"
}

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
        echo "Uso: $0 {restore|list}"
        echo "  restore <arquivo> - Restaura backup"
        echo "  list              - Lista backups disponíveis"
        exit 1
        ;;
esac
