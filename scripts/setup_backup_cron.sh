#!/bin/bash
"""
⏰ CONFIGURAÇÃO DE BACKUP AUTOMÁTICO
==================================

Configura agendamento automático de backup no crontab
"""

echo "⏰ CONFIGURANDO BACKUP AUTOMÁTICO NO CRONTAB"
echo "============================================="
echo

# Verificar se o script de backup existe
BACKUP_SCRIPT="/home/vancim/whats_agent/scripts/backup_database_secure.sh"

if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ Script de backup não encontrado: $BACKUP_SCRIPT"
    exit 1
fi

# Verificar se o script é executável
if [ ! -x "$BACKUP_SCRIPT" ]; then
    echo "🔧 Tornando script executável..."
    chmod +x "$BACKUP_SCRIPT"
fi

echo "✅ Script de backup encontrado: $BACKUP_SCRIPT"

# Definir horários de backup
DAILY_TIME="0 2"    # 02:00 diariamente
WEEKLY_TIME="0 3"   # 03:00 aos domingos
MONTHLY_TIME="0 4"  # 04:00 no primeiro dia do mês

# Criar entrada do crontab
CRON_ENTRY_DAILY="$DAILY_TIME * * * $BACKUP_SCRIPT daily"
CRON_ENTRY_WEEKLY="$WEEKLY_TIME * * 0 $BACKUP_SCRIPT weekly" 
CRON_ENTRY_MONTHLY="$MONTHLY_TIME 1 * * $BACKUP_SCRIPT monthly"

echo "📅 Configurando agendamentos:"
echo "   Backup diário: $CRON_ENTRY_DAILY"
echo "   Backup semanal: $CRON_ENTRY_WEEKLY"
echo "   Backup mensal: $CRON_ENTRY_MONTHLY"
echo

# Backup do crontab atual
echo "💾 Fazendo backup do crontab atual..."
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "# Novo crontab" > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S)

# Remover entradas antigas do backup (se existirem)
echo "🧹 Removendo agendamentos antigos de backup..."
crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT" > /tmp/new_crontab

# Adicionar novos agendamentos
echo "➕ Adicionando novos agendamentos..."
cat >> /tmp/new_crontab << EOF

# 🔄 BACKUP AUTOMÁTICO DO BANCO DE DADOS
# Gerado automaticamente em $(date)
$CRON_ENTRY_DAILY
$CRON_ENTRY_WEEKLY
$CRON_ENTRY_MONTHLY

EOF

# Aplicar novo crontab
crontab /tmp/new_crontab

# Verificar se foi aplicado
echo "✅ Verificando agendamentos configurados:"
crontab -l | grep "$BACKUP_SCRIPT"

# Limpar arquivo temporário
rm -f /tmp/new_crontab

echo
echo "🎉 BACKUP AUTOMÁTICO CONFIGURADO COM SUCESSO!"
echo "============================================="
echo "📋 Agendamentos ativos:"
echo "   - Backup diário às 02:00"
echo "   - Backup semanal aos domingos às 03:00"
echo "   - Backup mensal no dia 1º às 04:00"
echo
echo "🔍 Para verificar agendamentos: crontab -l"
echo "📝 Para editar agendamentos: crontab -e"
echo "📊 Para verificar logs: tail -f /var/log/cron"
