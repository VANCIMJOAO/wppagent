#!/bin/bash

# Script de Backup Automatizado para WppAgent
# Executa backup completo e envia notificações

set -euo pipefail

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/app/logs/backup.log"
LOCK_FILE="/tmp/backup.lock"
PYTHON_CMD="${PYTHON_CMD:-python}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funções de logging
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${RED}ERROR${NC}: $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${GREEN}SUCCESS${NC}: $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - ${YELLOW}WARNING${NC}: $1" | tee -a "$LOG_FILE"
}

# Função para limpeza
cleanup() {
    if [[ -f "$LOCK_FILE" ]]; then
        rm -f "$LOCK_FILE"
        log "Lock file removed"
    fi
}

# Trap para limpeza em caso de erro
trap cleanup EXIT

# Verificar se já está rodando
if [[ -f "$LOCK_FILE" ]]; then
    log_error "Backup script is already running (lock file exists)"
    exit 1
fi

# Criar lock file
echo $$ > "$LOCK_FILE"

# Verificar dependências
check_dependencies() {
    log "Checking dependencies..."
    
    local missing=0
    
    # Verificar PostgreSQL
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found - PostgreSQL client tools required"
        missing=1
    fi
    
    # Verificar Redis (opcional)
    if ! command -v redis-cli &> /dev/null; then
        log_warning "redis-cli not found - Redis backup will be skipped"
    fi
    
    # Verificar Python
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        log_error "Python not found"
        missing=1
    fi
    
    # Verificar espaço em disco
    local available_space
    available_space=$(df /app | tail -1 | awk '{print $4}')
    local min_space=1048576  # 1GB em KB
    
    if [[ $available_space -lt $min_space ]]; then
        log_error "Insufficient disk space: ${available_space}KB available, ${min_space}KB required"
        missing=1
    fi
    
    if [[ $missing -eq 1 ]]; then
        log_error "Dependency check failed"
        exit 1
    fi
    
    log_success "All dependencies checked"
}

# Função principal de backup
run_backup() {
    log "Starting backup routine..."
    
    cd "$PROJECT_DIR"
    
    # Executar backup via Python
    local python_script='
import asyncio
import sys
import os
import json
from datetime import datetime

# Adicionar o diretório do projeto ao path
sys.path.insert(0, "/app")

from app.services.backup_service import BackupService
from app.utils.logger import get_logger

async def main():
    try:
        backup_service = BackupService()
        result = await backup_service.full_backup_routine()
        
        # Output JSON para parsing pelo shell script
        print("BACKUP_RESULT_JSON:" + json.dumps(result))
        
        # Exit code baseado no sucesso
        sys.exit(0 if result["success"] else 1)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        print("BACKUP_RESULT_JSON:" + json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
'
    
    # Executar script Python
    local backup_output
    if backup_output=$($PYTHON_CMD -c "$python_script" 2>&1); then
        log_success "Backup routine completed successfully"
        
        # Extrair resultado JSON
        local json_result
        json_result=$(echo "$backup_output" | grep "BACKUP_RESULT_JSON:" | sed 's/BACKUP_RESULT_JSON://')
        
        if [[ -n "$json_result" ]]; then
            # Salvar resultado detalhado
            echo "$json_result" > "/app/logs/last_backup_result.json"
            
            # Parse básico para logging
            local backup_count
            backup_count=$(echo "$json_result" | $PYTHON_CMD -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('backups_created', [])))" 2>/dev/null || echo "0")
            
            log_success "Created $backup_count backup files"
        fi
        
        return 0
    else
        log_error "Backup routine failed"
        log_error "Output: $backup_output"
        
        # Tentar extrair resultado mesmo em caso de erro
        local json_result
        json_result=$(echo "$backup_output" | grep "BACKUP_RESULT_JSON:" | sed 's/BACKUP_RESULT_JSON://' || echo '{}')
        echo "$json_result" > "/app/logs/last_backup_result.json"
        
        return 1
    fi
}

# Função para enviar notificação
send_notification() {
    local status="$1"
    local message="$2"
    
    # Webhook para notificações (se configurado)
    local webhook_url="${BACKUP_WEBHOOK_URL:-}"
    
    if [[ -n "$webhook_url" ]]; then
        local payload
        payload=$(cat <<EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "service": "whatsapp-agent",
    "component": "backup-system", 
    "status": "$status",
    "message": "$message",
    "server": "${HOSTNAME:-unknown}",
    "environment": "${RAILWAY_ENVIRONMENT_NAME:-production}"
}
EOF
)
        
        if curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$webhook_url" > /dev/null; then
            log "Notification sent successfully"
        else
            log_warning "Failed to send notification"
        fi
    fi
    
    # Log local sempre
    echo "[$(date)] $status: $message" >> "/app/logs/backup_notifications.log"
}

# Função para verificar saúde dos backups
check_backup_health() {
    log "Checking backup health..."
    
    local backup_dir="/app/backups"
    local max_age_hours=25  # Alertar se último backup tem mais de 25h
    
    if [[ ! -d "$backup_dir" ]]; then
        log_error "Backup directory does not exist: $backup_dir"
        return 1
    fi
    
    # Encontrar backup mais recente
    local latest_backup
    latest_backup=$(find "$backup_dir" -name "*.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -z "$latest_backup" ]]; then
        log_error "No backup files found"
        return 1
    fi
    
    # Verificar idade do último backup
    local file_age_seconds
    file_age_seconds=$(( $(date +%s) - $(stat -c %Y "$latest_backup") ))
    local file_age_hours=$((file_age_seconds / 3600))
    
    if [[ $file_age_hours -gt $max_age_hours ]]; then
        log_error "Latest backup is too old: $file_age_hours hours (max: $max_age_hours)"
        return 1
    fi
    
    log_success "Latest backup is $file_age_hours hours old (within acceptable range)"
    return 0
}

# Função para relatório de status
generate_status_report() {
    local status_file="/app/logs/backup_status.json"
    
    cat > "$status_file" <<EOF
{
    "last_check": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "backup_directory": "/app/backups",
    "log_file": "$LOG_FILE",
    "script_version": "1.0",
    "disk_usage": {
        "available_mb": $(df /app --output=avail | tail -1 | awk '{print int($1/1024)}'),
        "backup_size_mb": $(du -sm /app/backups 2>/dev/null | cut -f1 || echo "0")
    },
    "recent_backups": [
        $(find /app/backups -name "*.gz" -type f -printf '{"filename": "%f", "size_mb": %k, "modified": %TY-%Tm-%TdT%TH:%TM:%TSZ}' -printf ',\n' 2>/dev/null | head -5 | sed '$ s/,$//')
    ]
}
EOF
    
    log "Status report generated: $status_file"
}

# Função principal
main() {
    local start_time
    start_time=$(date +%s)
    
    log "=== Backup Script Started ==="
    log "PID: $$, User: $(whoami), PWD: $(pwd)"
    
    # Verificar dependências
    check_dependencies
    
    # Executar backup
    if run_backup; then
        log_success "Backup completed successfully"
        send_notification "SUCCESS" "Backup routine completed successfully"
        
        # Verificar saúde dos backups
        if check_backup_health; then
            log_success "Backup health check passed"
        else
            log_warning "Backup health check failed"
            send_notification "WARNING" "Backup health check failed"
        fi
    else
        log_error "Backup failed"
        send_notification "ERROR" "Backup routine failed - check logs for details"
        exit 1
    fi
    
    # Gerar relatório de status
    generate_status_report
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "=== Backup Script Completed in ${duration}s ==="
}

# Executar função principal
main "$@"
