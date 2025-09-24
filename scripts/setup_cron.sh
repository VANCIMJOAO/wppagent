#!/bin/bash

# Script para configurar cron job de limpeza automática
echo "⏰ Configurando limpeza automática de sessões..."

# Criar entradas no crontab
(crontab -l 2>/dev/null; echo "# Limpeza de sessões a cada 6 horas"; echo "0 */6 * * * cd /home/vancim/whats_agent && source setup_env.sh && python3 scripts/cleanup_sessions.py") | crontab -

# Adicionar rotação de logs diária às 2h da manhã
(crontab -l 2>/dev/null; echo "# Rotação de logs diária às 2h"; echo "0 2 * * * cd /home/vancim/whats_agent && source setup_env.sh && python3 scripts/log_rotation.py") | crontab -

echo "✅ Cron job configurado!"
echo "📅 Limpeza automática executará a cada 6 horas"
echo "📝 Logs serão salvos em: /home/vancim/whats_agent/logs/session_cleanup.log"

# Executar limpeza inicial
echo "🧹 Executando limpeza inicial..."
cd /home/vancim/whats_agent
source setup_env.sh
python3 scripts/cleanup_sessions.py
