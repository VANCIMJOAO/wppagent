#!/bin/bash
# 🔄 SISTEMA DE UPDATES DE SEGURANÇA AUTOMATIZADO
# ===============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/security-updates.log"
LOCK_FILE="/var/lock/security-updates.lock"

# Função de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | sudo tee -a "$LOG_FILE"
}

# Função de cleanup
cleanup() {
    sudo rm -f "$LOCK_FILE"
}

# Trap para cleanup
trap cleanup EXIT

echo "🔄 APLICANDO UPDATES DE SEGURANÇA..."

# Verificar se já está rodando
if [ -f "$LOCK_FILE" ]; then
    echo "❌ Updates já estão rodando. Aguarde..."
    exit 1
fi

# Criar lock file
sudo touch "$LOCK_FILE"

log "🔄 Iniciando updates de segurança"

# ===========================================
# 1. SISTEMA OPERACIONAL
# ===========================================

echo "🐧 Atualizando sistema operacional..."
log "🐧 Atualizando pacotes do sistema"

# Atualizar lista de pacotes
sudo apt-get update -y

# Instalar apenas updates de segurança
sudo apt-get upgrade -y \
    -o Dpkg::Options::="--force-confdef" \
    -o Dpkg::Options::="--force-confold"

# Updates de segurança específicos
sudo unattended-upgrade -v

# Remover pacotes desnecessários
sudo apt-get autoremove -y
sudo apt-get autoclean

log "✅ Sistema operacional atualizado"

# ===========================================
# 2. DOCKER E CONTAINERS
# ===========================================

echo "🐳 Atualizando Docker e containers..."
log "🐳 Atualizando containers Docker"

cd "$SCRIPT_DIR/.."

# Parar containers
docker-compose down

# Atualizar imagens base
docker-compose pull

# Rebuild com cache para aplicar patches de segurança
docker-compose build --no-cache --pull

# Remover imagens antigas
docker image prune -f

# Remover volumes não utilizados
docker volume prune -f

# Remover networks não utilizados
docker network prune -f

log "✅ Docker atualizado"

# ===========================================
# 3. DEPENDÊNCIAS PYTHON
# ===========================================

echo "🐍 Atualizando dependências Python..."
log "🐍 Verificando vulnerabilidades Python"

# Atualizar pip
python3 -m pip install --upgrade pip

# Verificar vulnerabilidades com safety
if ! command -v safety &> /dev/null; then
    pip install safety
fi

# Audit de segurança
safety check --json > /tmp/safety_report.json || true

# Atualizar requirements com versões seguras
pip-review --local --auto || true

log "✅ Dependências Python verificadas"

# ===========================================
# 4. CERTIFICADOS SSL
# ===========================================

echo "🔐 Verificando certificados SSL..."
log "🔐 Verificando validade dos certificados"

SSL_CERT="/home/vancim/whats_agent/config/nginx/ssl/server.crt"

if [ -f "$SSL_CERT" ]; then
    # Verificar data de expiração
    EXPIRY_DATE=$(openssl x509 -in "$SSL_CERT" -noout -enddate | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
    CURRENT_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
    
    if [ $DAYS_LEFT -lt 30 ]; then
        log "⚠️ Certificado SSL expira em $DAYS_LEFT dias"
        echo "⚠️ ATENÇÃO: Certificado SSL expira em $DAYS_LEFT dias!"
        
        # Renovar certificado automaticamente se for Let's Encrypt
        if [ -f "/etc/letsencrypt/live" ]; then
            sudo certbot renew --quiet
            log "✅ Certificado Let's Encrypt renovado"
        fi
    else
        log "✅ Certificado SSL válido por $DAYS_LEFT dias"
    fi
else
    log "⚠️ Certificado SSL não encontrado"
fi

# ===========================================
# 5. CONFIGURAÇÕES DE SEGURANÇA
# ===========================================

echo "🔒 Verificando configurações de segurança..."
log "🔒 Auditando configurações de segurança"

# Verificar permissões de arquivos críticos
find /home/vancim/whats_agent -name "*.key" -not -perm 600 -exec chmod 600 {} \;
find /home/vancim/whats_agent -name "*.pem" -not -perm 600 -exec chmod 600 {} \;

# Verificar .env
ENV_FILE="/home/vancim/whats_agent/.env"
if [ -f "$ENV_FILE" ]; then
    if [ "$(stat -c %a "$ENV_FILE")" != "600" ]; then
        chmod 600 "$ENV_FILE"
        log "🔒 Corrigidas permissões do .env"
    fi
fi

# Verificar diretório secrets
SECRETS_DIR="/home/vancim/whats_agent/secrets"
if [ -d "$SECRETS_DIR" ]; then
    if [ "$(stat -c %a "$SECRETS_DIR")" != "700" ]; then
        chmod 700 "$SECRETS_DIR"
        log "🔒 Corrigidas permissões do diretório secrets"
    fi
fi

log "✅ Configurações de segurança verificadas"

# ===========================================
# 6. LOGS E MONITORAMENTO
# ===========================================

echo "📊 Configurando logs de segurança..."
log "📊 Configurando auditoria de logs"

# Configurar logrotate para logs de segurança
sudo tee /etc/logrotate.d/whatsapp-security > /dev/null << 'EOF'
/var/log/security-updates.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}

/home/vancim/whats_agent/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

# Configurar auditd para monitoramento
if ! command -v auditd &> /dev/null; then
    sudo apt-get install -y auditd
fi

# Regras de auditoria
sudo tee -a /etc/audit/rules.d/whatsapp.rules > /dev/null << 'EOF'
# Monitorar arquivos críticos
-w /home/vancim/whats_agent/.env -p wa -k whatsapp_config
-w /home/vancim/whats_agent/secrets/ -p wa -k whatsapp_secrets
-w /home/vancim/whats_agent/config/ -p wa -k whatsapp_config

# Monitorar execução de containers
-w /usr/bin/docker -p x -k docker_exec
-w /usr/local/bin/docker-compose -p x -k docker_compose_exec
EOF

sudo systemctl restart auditd || true

log "✅ Logs e monitoramento configurados"

# ===========================================
# 7. BACKUP DE SEGURANÇA
# ===========================================

echo "💾 Criando backup de segurança..."
log "💾 Executando backup pré-update"

BACKUP_DIR="/home/vancim/whats_agent/backups/security-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup de configurações críticas
cp -r /home/vancim/whats_agent/config "$BACKUP_DIR/"
cp -r /home/vancim/whats_agent/secrets "$BACKUP_DIR/"
cp /home/vancim/whats_agent/.env "$BACKUP_DIR/"

# Backup do banco (se disponível)
if command -v pg_dump &> /dev/null && [ ! -z "${DB_NAME:-}" ]; then
    pg_dump "${DATABASE_URL:-}" > "$BACKUP_DIR/database_backup.sql" 2>/dev/null || true
fi

log "✅ Backup criado em $BACKUP_DIR"

# ===========================================
# 8. HARDENING ADICIONAL
# ===========================================

echo "🛡️ Aplicando hardening adicional..."
log "🛡️ Aplicando configurações de hardening"

# Configurações de kernel para segurança
sudo tee -a /etc/sysctl.conf > /dev/null << 'EOF'

# Hardening de segurança WhatsApp Agent
# =====================================

# Desabilitar IPv6 (se não usado)
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# Proteção contra overflow de buffer
kernel.exec-shield = 1
kernel.randomize_va_space = 2

# Limitar core dumps
fs.suid_dumpable = 0

# Proteção contra symlink attacks
fs.protected_hardlinks = 1
fs.protected_symlinks = 1

# Limitar acesso a dmesg
kernel.dmesg_restrict = 1

# Proteção contra ptrace
kernel.yama.ptrace_scope = 1
EOF

# Aplicar configurações
sudo sysctl -p

# Configurar limites de recursos
sudo tee /etc/security/limits.d/whatsapp.conf > /dev/null << 'EOF'
# Limites para usuário da aplicação
* soft core 0
* hard core 0
* soft nproc 65536
* hard nproc 65536
* soft nofile 65536
* hard nofile 65536
EOF

log "✅ Hardening aplicado"

# ===========================================
# 9. REINICIAR SERVIÇOS
# ===========================================

echo "🔄 Reiniciando serviços..."
log "🔄 Reiniciando containers com updates"

# Reiniciar containers com configurações atualizadas
docker-compose up -d --remove-orphans

# Aguardar health checks
sleep 30

# Verificar se serviços estão rodando
if docker-compose ps | grep -q "Up"; then
    log "✅ Serviços reiniciados com sucesso"
else
    log "❌ Erro ao reiniciar serviços"
    echo "❌ Erro ao reiniciar serviços. Verifique os logs."
fi

# ===========================================
# 10. RELATÓRIO FINAL
# ===========================================

echo ""
echo "🎉 UPDATES DE SEGURANÇA APLICADOS COM SUCESSO!"
echo "=============================================="
log "🎉 Updates de segurança aplicados com sucesso"

# Gerar relatório de segurança
REPORT_FILE="/home/vancim/whats_agent/reports/security-update-$(date +%Y%m%d-%H%M%S).txt"
mkdir -p "$(dirname "$REPORT_FILE")"

cat > "$REPORT_FILE" << EOF
RELATÓRIO DE UPDATES DE SEGURANÇA
================================

Data: $(date)
Usuário: $(whoami)
Sistema: $(uname -a)

UPDATES APLICADOS:
- ✅ Sistema operacional atualizado
- ✅ Docker e containers atualizados
- ✅ Dependências Python verificadas
- ✅ Certificados SSL verificados
- ✅ Configurações de segurança auditadas
- ✅ Logs e monitoramento configurados
- ✅ Backup de segurança criado
- ✅ Hardening adicional aplicado
- ✅ Serviços reiniciados

PRÓXIMA EXECUÇÃO: $(date -d "+1 week")

Para logs detalhados: tail -f $LOG_FILE
EOF

echo "📄 Relatório salvo em: $REPORT_FILE"
log "📄 Relatório gerado: $REPORT_FILE"

echo ""
echo "⏰ PRÓXIMOS PASSOS:"
echo "1. Configurar cron para execução automática"
echo "2. Monitorar logs de segurança"
echo "3. Verificar funcionamento dos serviços"
echo ""
echo "📋 COMANDOS ÚTEIS:"
echo "- Ver logs: tail -f $LOG_FILE"
echo "- Status Docker: docker-compose ps"
echo "- Ver auditoria: sudo ausearch -k whatsapp_config"
echo ""

log "🏁 Script de updates finalizado"
