#!/bin/bash
# 🔐 VERIFICAÇÃO DIÁRIA DE CERTIFICADOS
# ====================================

set -euo pipefail

LOG_FILE="/var/log/cert-check.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

echo "🔐 Verificando certificados SSL..."
log "🔐 Iniciando verificação de certificados"

SSL_CERT="/home/vancim/whats_agent/config/nginx/ssl/server.crt"

if [ -f "$SSL_CERT" ]; then
    # Verificar data de expiração
    EXPIRY_DATE=$(openssl x509 -in "$SSL_CERT" -noout -enddate | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
    CURRENT_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
    
    log "Certificado expira em $DAYS_LEFT dias"
    
    if [ $DAYS_LEFT -lt 7 ]; then
        log "🚨 CRÍTICO: Certificado expira em $DAYS_LEFT dias!"
        # Enviar alerta (implementar notificação)
        echo "🚨 ATENÇÃO: Certificado SSL expira em $DAYS_LEFT dias!"
    elif [ $DAYS_LEFT -lt 30 ]; then
        log "⚠️ AVISO: Certificado expira em $DAYS_LEFT dias"
        echo "⚠️ Certificado SSL expira em $DAYS_LEFT dias"
    else
        log "✅ Certificado válido por $DAYS_LEFT dias"
    fi
    
    # Verificar integridade do certificado
    if openssl x509 -in "$SSL_CERT" -noout -checkend 0 >/dev/null 2>&1; then
        log "✅ Certificado válido e íntegro"
    else
        log "❌ Certificado inválido ou corrompido!"
        echo "❌ ERRO: Certificado SSL inválido!"
    fi
else
    log "❌ Certificado SSL não encontrado"
    echo "❌ ERRO: Certificado SSL não encontrado!"
fi

log "🏁 Verificação de certificados finalizada"
