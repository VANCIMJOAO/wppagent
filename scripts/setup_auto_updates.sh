#!/bin/bash
# 📅 CONFIGURAÇÃO DE CRON PARA UPDATES AUTOMÁTICOS
# ===============================================

set -euo pipefail

echo "📅 Configurando updates automáticos de segurança..."

# Criar cron job para updates automáticos
CRON_JOB="0 2 * * 0 /home/vancim/whats_agent/scripts/apply_security_updates.sh >> /var/log/security-updates-cron.log 2>&1"

# Verificar se o cron job já existe
if ! crontab -l 2>/dev/null | grep -q "apply_security_updates.sh"; then
    # Adicionar cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job adicionado: Updates semanais aos domingos às 2h"
else
    echo "ℹ️ Cron job já existe"
fi

# Criar cron job para verificação diária de certificados
CERT_CRON="0 6 * * * /home/vancim/whats_agent/scripts/check_certificates.sh >> /var/log/cert-check.log 2>&1"

if ! crontab -l 2>/dev/null | grep -q "check_certificates.sh"; then
    (crontab -l 2>/dev/null; echo "$CERT_CRON") | crontab -
    echo "✅ Cron job adicionado: Verificação diária de certificados às 6h"
fi

# Mostrar crontab atual
echo ""
echo "📋 CRON JOBS CONFIGURADOS:"
crontab -l

echo ""
echo "✅ Updates automáticos configurados!"
echo "- Updates de segurança: Domingos às 2:00"
echo "- Verificação de certificados: Diariamente às 6:00"
