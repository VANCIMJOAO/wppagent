#!/bin/bash
# Monitor de Health Checks Avançado
# Monitoramento em tempo real do status dos serviços Docker

set -euo pipefail

# Configurações
UPDATE_INTERVAL=5
LOG_FILE="logs/health_monitor.log"
ALERT_THRESHOLD=3

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores de falhas
declare -A failure_counts

log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Função para verificar status de um container
check_container_health() {
    local container_name=$1
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "not_found")
    
    case $health_status in
        "healthy")
            echo -e "${GREEN}✓${NC}"
            failure_counts[$container_name]=0
            ;;
        "unhealthy")
            echo -e "${RED}✗${NC}"
            failure_counts[$container_name]=$((${failure_counts[$container_name]:-0} + 1))
            ;;
        "starting")
            echo -e "${YELLOW}◐${NC}"
            ;;
        "none"|"not_found")
            echo -e "${BLUE}?${NC}"
            ;;
        *)
            echo -e "${YELLOW}◐${NC}"
            ;;
    esac
    
    echo "$health_status"
}

# Função para exibir status simples
display_simple_status() {
    echo "🔍 Verificando saúde do sistema..."
    
    # Verificar se o servidor está rodando
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Servidor principal: OK"
    else
        echo "❌ Servidor principal: FALHA"
        exit 1
    fi
    
    # Verificar métricas
    if curl -s http://localhost:8000/production/system/status > /dev/null 2>/dev/null; then
        echo "✅ Sistema de monitoramento: OK"
    else
        echo "⚠️ Sistema de monitoramento: FALHA"
    fi
    
    # Verificar logs
    if [ -f "logs/app.log" ]; then
        echo "✅ Sistema de logs: OK"
    else
        echo "⚠️ Sistema de logs: Arquivo não encontrado"
    fi
}

# Função para exibir status detalhado dos containers
display_container_status() {
    echo -e "${BLUE}=== Status dos Containers Docker ===${NC}"
    echo
    
    local containers=("whatsapp_postgres" "whatsapp_redis" "whatsapp_app" "whatsapp_dashboard" "whatsapp_nginx")
    
    for container in "${containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^$container$"; then
            local status_info=$(check_container_health "$container")
            local status_icon=$(echo "$status_info" | head -n1)
            local status_text=$(echo "$status_info" | tail -n1)
            echo "Container $container: $status_icon $status_text"
        else
            echo "Container $container: ${RED}✗ Parado${NC}"
        fi
    done
}

# Função principal
main() {
    local mode=${1:-simple}
    
    mkdir -p logs
    
    case $mode in
        "simple"|"")
            display_simple_status
            ;;
        "containers"|"c")
            display_container_status
            ;;
        "all"|"a")
            display_simple_status
            echo
            display_container_status
            ;;
        "help"|*)
            echo "Uso: $0 {simple|containers|all}"
            echo ""
            echo "Modos:"
            echo "  simple      - Verificação simples de APIs (padrão)"
            echo "  containers  - Status dos containers Docker"
            echo "  all         - Verificação completa"
            echo "  help        - Mostrar esta ajuda"
            ;;
    esac
}

# Executar função principal
main "$@"
