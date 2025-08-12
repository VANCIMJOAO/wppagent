#!/bin/bash
"""
Script de Restore - WhatsApp Agent
Restaura backup do sistema
"""

set -e

# Configurações
BACKUP_DIR="/home/whatsapp/app/backups"
DB_NAME="${DB_NAME:-whatsapp_agent}"
DB_USER="${DB_USER:-vancimj}"

if [ -z "$1" ]; then
    echo "❌ Uso: $0 <arquivo_backup.sql>"
    echo "📋 Backups disponíveis:"
    ls -la "$BACKUP_DIR/database/"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Arquivo de backup não encontrado: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Iniciando restore do backup: $BACKUP_FILE"

# Confirmar operação
read -p "⚠️ Isso irá substituir o banco atual. Continuar? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operação cancelada"
    exit 1
fi

# Fazer backup do estado atual antes do restore
DATE=$(date +%Y%m%d_%H%M%S)
echo "💾 Fazendo backup de segurança do estado atual..."
pg_dump -h postgres -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/database/pre_restore_backup_$DATE.sql"

# Restaurar banco de dados
echo "📊 Restaurando banco de dados..."
psql -h postgres -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"

echo "✅ Restore concluído com sucesso!"
echo "📝 Backup de segurança salvo em: pre_restore_backup_$DATE.sql"
