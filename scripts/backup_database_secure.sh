#!/bin/bash
# 💾 SISTEMA DE BACKUP AUTOMÁTICO SEGURO - VERSÃO COMPLETA
# =======================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_BASE_DIR="/home/vancim/whats_agent/backups"
RETENTION_DAYS=30
MAX_BACKUP_SIZE="10GB"

# Função de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_BASE_DIR/backup.log"
}

# Função de cleanup
cleanup() {
    if [ -n "${TEMP_DIR:-}" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

trap cleanup EXIT

echo "💾 SISTEMA DE BACKUP AUTOMÁTICO COMPLETO"
echo "========================================"

# Carregar configurações
if [ -f "/home/vancim/whats_agent/secrets/database_credentials.env" ]; then
    source "/home/vancim/whats_agent/secrets/database_credentials.env"
elif [ -f "/home/vancim/whats_agent/.env" ]; then
    source "/home/vancim/whats_agent/.env"
else
    echo "❌ Arquivo de configuração não encontrado"
    exit 1
fi

# Configurações de backup
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_DIR="$BACKUP_BASE_DIR/database/$TIMESTAMP"
TEMP_DIR=$(mktemp -d)

# Usar usuário de backup se disponível
if [ -n "${DB_BACKUP_USER:-}" ]; then
    BACKUP_USER="$DB_BACKUP_USER"
    BACKUP_PASSWORD="$DB_BACKUP_PASSWORD"
else
    BACKUP_USER="${DB_USER:-vancimj}"
    BACKUP_PASSWORD="${DB_PASSWORD:-os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")}"
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-whatsapp_agent}"

log "💾 Iniciando backup do banco de dados"

# ===========================================
# 1. VALIDAÇÕES PRÉ-BACKUP
# ===========================================

echo "🔍 Validando pré-requisitos..."

# Verificar se os comandos necessários existem
for cmd in pg_dump pg_isready psql gzip; do
    if ! command -v "$cmd" &> /dev/null; then
        log "❌ Comando $cmd não encontrado"
        exit 1
    fi
done

# Verificar espaço em disco
AVAILABLE_SPACE=$(df "$BACKUP_BASE_DIR" | awk 'NR==2 {print $4}')
REQUIRED_SPACE=1048576  # 1GB em KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    log "❌ Espaço em disco insuficiente"
    echo "❌ Espaço disponível: $(($AVAILABLE_SPACE / 1024))MB, necessário: 1GB"
    exit 1
fi

# Verificar conectividade com o banco
if ! PGPASSWORD="$BACKUP_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$BACKUP_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    log "❌ Não foi possível conectar ao banco de dados"
    echo "❌ Erro: Banco de dados não acessível"
    exit 1
fi

log "✅ Validações concluídas"

# ===========================================
# 2. CRIAR ESTRUTURA DE BACKUP
# ===========================================

echo "📁 Criando estrutura de backup..."

mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_BASE_DIR/logs"

# Metadados do backup
cat > "$BACKUP_DIR/backup_info.txt" << EOF
BACKUP WHATSAPP AGENT
====================

Data: $(date)
Servidor: $(hostname)
Usuário: $(whoami)
Banco: $DB_NAME
Host: $DB_HOST:$DB_PORT
Usuário DB: $BACKUP_USER

EOF

log "📁 Estrutura de backup criada"

# ===========================================
# 3. BACKUP COMPLETO DO BANCO
# ===========================================

echo "🗃️ Executando backup completo..."

DUMP_FILE="$BACKUP_DIR/database_full.sql"
DUMP_FILE_COMPRESSED="$BACKUP_DIR/database_full.sql.gz"

# Backup com pg_dump
PGPASSWORD="$BACKUP_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$BACKUP_USER" \
    -d "$DB_NAME" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=plain \
    --no-password \
    --file="$DUMP_FILE" 2>&1 | tee "$BACKUP_DIR/backup_log.txt"

if [ $? -eq 0 ]; then
    log "✅ Backup SQL completo criado"
else
    log "❌ Erro no backup SQL"
    exit 1
fi

# Comprimir backup
gzip "$DUMP_FILE"
log "✅ Backup comprimido"

# ===========================================
# 4. BACKUP DE CONFIGURAÇÕES
# ===========================================

echo "⚙️ Backup de configurações..."

CONFIG_BACKUP_DIR="$BACKUP_DIR/config"
mkdir -p "$CONFIG_BACKUP_DIR"

# Copiar configurações importantes (sem credenciais)
if [ -d "/home/vancim/whats_agent/config" ]; then
    cp -r "/home/vancim/whats_agent/config" "$CONFIG_BACKUP_DIR/"
    log "✅ Configurações da aplicação salvas"
fi

# Schema do banco
PGPASSWORD="$BACKUP_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$BACKUP_USER" \
    -d "$DB_NAME" \
    --schema-only \
    --no-password \
    --file="$CONFIG_BACKUP_DIR/schema.sql" 2>/dev/null

log "✅ Schema do banco salvo"

# ===========================================
# 5. VERIFICAÇÃO DE INTEGRIDADE
# ===========================================

echo "🔍 Verificando integridade do backup..."

# Verificar se o arquivo existe e não está vazio
if [ -f "$DUMP_FILE_COMPRESSED" ] && [ -s "$DUMP_FILE_COMPRESSED" ]; then
    BACKUP_SIZE=$(du -h "$DUMP_FILE_COMPRESSED" | cut -f1)
    log "✅ Backup válido: $BACKUP_SIZE"
else
    log "❌ Backup inválido ou vazio"
    exit 1
fi

# ===========================================
# 6. CHECKSUM E METADADOS FINAIS
# ===========================================

echo "🔐 Gerando checksums..."

# Gerar checksums
cd "$BACKUP_DIR"
find . -type f -name "*.sql.gz" -o -name "*.sql" | xargs sha256sum > checksums.sha256
log "✅ Checksums gerados"

# Metadados finais
BACKUP_END_TIME=$(date)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

cat >> "$BACKUP_DIR/backup_info.txt" << EOF

FINALIZAÇÃO
===========

Fim do backup: $BACKUP_END_TIME
Tamanho total: $TOTAL_SIZE
Arquivos criados:
$(find "$BACKUP_DIR" -type f -exec basename {} \; | sort)

STATUS: SUCESSO
EOF

log "💾 Backup concluído: $TOTAL_SIZE"

# ===========================================
# 7. LIMPEZA DE BACKUPS ANTIGOS
# ===========================================

echo "🧹 Limpando backups antigos..."

# Remover backups mais antigos que RETENTION_DAYS
find "$BACKUP_BASE_DIR/database" -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

# Contar backups restantes
BACKUP_COUNT=$(find "$BACKUP_BASE_DIR/database" -type d -name "20*" | wc -l)
log "🗃️ $BACKUP_COUNT backups mantidos (retenção: $RETENTION_DAYS dias)"

# ===========================================
# 8. RELATÓRIO FINAL
# ===========================================

echo ""
echo "🎉 BACKUP CONCLUÍDO COM SUCESSO!"
echo "================================"
echo "📁 Local: $BACKUP_DIR"
echo "📊 Tamanho: $TOTAL_SIZE"
echo "⏰ Concluído às $(date '+%H:%M:%S')"
echo ""

# Criar link simbólico para último backup
ln -sfn "$BACKUP_DIR" "$BACKUP_BASE_DIR/latest"
log "🔗 Link simbólico 'latest' atualizado"

# Notificação de sucesso
echo "✅ Backup automático executado com sucesso" >> "$BACKUP_BASE_DIR/backup_status.log"

log "🏁 Sistema de backup finalizado"

echo ""
echo "💡 COMANDOS ÚTEIS:"
echo "  Ver logs: tail -f $BACKUP_BASE_DIR/backup.log"
echo "  Listar backups: ls -la $BACKUP_BASE_DIR/database/"
echo "  Último backup: ls -la $BACKUP_BASE_DIR/latest/"
echo ""
