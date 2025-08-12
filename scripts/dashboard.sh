#!/bin/bash

# 🎯 DASHBOARD DE MONITORAMENTO - WHATSAPP AGENT
# ==============================================

clear
echo "🚀 =============================================================="
echo "📊 DASHBOARD DE MONITORAMENTO - WHATSAPP AGENT"
echo "🚀 =============================================================="
echo ""

# Função para exibir status com cores
print_status() {
    if [[ "$2" == "healthy" ]] || [[ "$2" == "OK" ]]; then
        echo -e "✅ $1: \033[32m$2\033[0m"
    elif [[ "$2" == "unhealthy" ]] || [[ "$2" == "ERROR" ]]; then
        echo -e "❌ $1: \033[31m$2\033[0m"
    else
        echo -e "⚠️  $1: \033[33m$2\033[0m"
    fi
}

# Verificar se servidor está rodando
if curl -s http://localhost:8000/health > /dev/null; then
    echo "🌐 SERVIDOR PRINCIPAL"
    echo "--------------------------------------------------------------"
    print_status "Status do Servidor" "ONLINE"
    print_status "Porta" "8000"
    print_status "URL Dashboard" "http://localhost:8000/production/system/status"
    echo ""
    
    # Buscar dados do sistema
    echo "🔍 HEALTH CHECKS"
    echo "--------------------------------------------------------------"
    SYSTEM_DATA=$(curl -s http://localhost:8000/production/system/status)
    
    # Extrair health checks
    DB_STATUS=$(echo $SYSTEM_DATA | jq -r '.data.health_checks.database.status // "unknown"')
    WA_STATUS=$(echo $SYSTEM_DATA | jq -r '.data.health_checks.whatsapp_api.status // "unknown"')
    AI_STATUS=$(echo $SYSTEM_DATA | jq -r '.data.health_checks.openai_api.status // "unknown"')
    
    print_status "Banco de Dados" "$DB_STATUS"
    print_status "WhatsApp API" "$WA_STATUS"
    print_status "OpenAI API" "$AI_STATUS"
    echo ""
    
    # Performance do sistema
    echo "⚡ PERFORMANCE DO SISTEMA"
    echo "--------------------------------------------------------------"
    CPU=$(echo $SYSTEM_DATA | jq -r '.data.performance.cpu_usage.value // 0')
    MEMORY=$(echo $SYSTEM_DATA | jq -r '.data.performance.memory_usage.value // 0')
    DISK=$(echo $SYSTEM_DATA | jq -r '.data.performance.disk_usage.value // 0')
    
    echo "🖥️  CPU: ${CPU}%"
    echo "💾 Memória: ${MEMORY}%"
    echo "💿 Disco: ${DISK}%"
    echo ""
    
    # Métricas de negócio
    echo "📈 MÉTRICAS DE NEGÓCIO"
    echo "--------------------------------------------------------------"
    BUSINESS_DATA=$(curl -s http://localhost:8000/production/metrics/business)
    
    CONVERSATIONS=$(echo $BUSINESS_DATA | jq -r '.data.conversations.total // 0')
    ACTIVE_CONV=$(echo $BUSINESS_DATA | jq -r '.data.conversations.active // 0')
    AVG_RESPONSE=$(echo $BUSINESS_DATA | jq -r '.data.performance.avg_response_time // 0')
    REVENUE=$(echo $BUSINESS_DATA | jq -r '.data.business.total_revenue // 0')
    
    echo "💬 Conversações Totais: $CONVERSATIONS"
    echo "🔥 Conversações Ativas: $ACTIVE_CONV"
    echo "⚡ Tempo Médio Resposta: ${AVG_RESPONSE}ms"
    echo "💰 Receita Total: R$ $REVENUE"
    echo ""
    
    # Alertas
    echo "🚨 ALERTAS"
    echo "--------------------------------------------------------------"
    ALERTS_DATA=$(curl -s http://localhost:8000/production/alerts/active)
    ACTIVE_ALERTS=$(echo $ALERTS_DATA | jq -r '.data.total // 0')
    
    if [[ "$ACTIVE_ALERTS" == "0" ]]; then
        echo "✅ Nenhum alerta ativo"
    else
        echo "⚠️  $ACTIVE_ALERTS alertas ativos"
    fi
    echo ""
    
    # Logs recentes
    echo "📋 LOGS RECENTES"
    echo "--------------------------------------------------------------"
    if [[ -f "logs/app.log" ]]; then
        echo "📝 Últimas 5 entradas:"
        tail -n 5 logs/app.log | head -3
        echo "..."
    else
        echo "⚠️  Arquivo de log não encontrado"
    fi
    echo ""
    
    # Links úteis
    echo "🔗 LINKS ÚTEIS"
    echo "--------------------------------------------------------------"
    echo "📊 Dashboard Completo: http://localhost:8000/production/system/status"
    echo "📈 Métricas de Negócio: http://localhost:8000/production/metrics/business"
    echo "🚨 Alertas Ativos: http://localhost:8000/production/alerts/active"
    echo "⚡ Performance Atual: http://localhost:8000/production/performance/current"
    echo "💾 Status de Backup: http://localhost:8000/production/backup/status"
    echo ""
    
    echo "🔄 Última atualização: $(date '+%Y-%m-%d %H:%M:%S')"
    
else
    echo "❌ SERVIDOR OFFLINE"
    echo "--------------------------------------------------------------"
    echo "O servidor não está respondendo na porta 8000"
    echo ""
    echo "💡 Para iniciar o servidor:"
    echo "   ./scripts/start_production.sh"
    echo ""
    echo "🔍 Para verificar processos na porta 8000:"
    echo "   lsof -i :8000"
fi

echo ""
echo "🎯 =============================================================="
