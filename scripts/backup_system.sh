#!/bin/bash
"""
Script de Backup Automático - WhatsApp Agent
Executa backup completo do sistema
"""

set -e

# Configurações
BACKUP_DIR="/home/whatsapp/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-whatsapp_agent}"
DB_USER="${DB_USER:-vancimj}"

echo "🔄 Iniciando backup automático - $DATE"

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR/database"
mkdir -p "$BACKUP_DIR/config"
mkdir -p "$BACKUP_DIR/logs"

# Backup do banco de dados PostgreSQL
echo "📊 Fazendo backup do banco de dados..."
pg_dump -h postgres -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_DIR/database/backup_$DATE.sql"

# Backup das configurações
echo "⚙️ Fazendo backup das configurações..."
cp -r /home/whatsapp/app/config/* "$BACKUP_DIR/config/" 2>/dev/null || true
cp /home/whatsapp/app/.env* "$BACKUP_DIR/config/" 2>/dev/null || true

# Backup dos logs importantes
echo "📝 Fazendo backup dos logs..."
find /home/whatsapp/app/logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/logs/" \; 2>/dev/null || true

# Limpeza de backups antigos (manter apenas 7 dias)
echo "🧹 Limpando backups antigos..."
find "$BACKUP_DIR" -name "backup_*.sql" -mtime +7 -delete 2>/dev/null || true

# Verificar tamanho do backup
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "✅ Backup concluído - Tamanho total: $BACKUP_SIZE"

# Criar marcador de sucesso
echo "$DATE - Backup realizado com sucesso" >> "$BACKUP_DIR/backup_history.log"

echo "🎉 Backup automático concluído com sucesso!"
