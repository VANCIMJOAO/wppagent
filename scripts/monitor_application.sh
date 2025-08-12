#!/bin/bash

# =========================================================================
# WHATSAPP AGENT - SCRIPT DE MONITORAMENTO
# =========================================================================
# Este script monitora todos os componentes da aplicação em tempo real
# Criado em: 11 de Agosto de 2025
# Versão: 1.0.0
# =========================================================================

set -e

# Detectar comando Docker Compose
detect_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        return 1
    fi
    return 0
}

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Configurações
REFRESH_INTERVAL=5
MAX_LOG_LINES=10

# Função para limpar tela
clear_screen() {
    clear
    echo -e "${PURPLE}"
    echo "==========================================================================="
    echo "           🔍 WHATSAPP AGENT - MONITOR EM TEMPO REAL 🔍"
    echo "==========================================================================="
    echo -e "${NC}"
    echo -e "${BLUE}Atualizado em: $(date '+%Y-%m-%d %H:%M:%S')${NC} | Intervalo: ${REFRESH_INTERVAL}s | Ctrl+C para sair"
    echo ""
}

# Verificar status dos containers
check_container_status() {
    echo -e "${CYAN}📦 STATUS DOS CONTAINERS:${NC}"
    echo "============================================"
    
    if detect_docker_compose; then
        local containers=$($DOCKER_COMPOSE_CMD ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Nenhum container encontrado")
        
        if [[ "$containers" == "Nenhum container encontrado" ]]; then
            echo -e "${YELLOW}⚠️  Nenhum container Docker Compose rodando${NC}"
        else
            echo "$containers" | while IFS= read -r line; do
                if echo "$line" | grep -q "Up"; then
                    echo -e "${GREEN}✅ $line${NC}"
                elif echo "$line" | grep -q "Exit"; then
                    echo -e "${RED}❌ $line${NC}"
                else
                    echo -e "${YELLOW}⚠️  $line${NC}"
                fi
            done
        fi
    else
        echo -e "${RED}❌ Docker Compose não encontrado${NC}"
    fi
    echo ""
}

# Verificar uso de recursos
check_resource_usage() {
    echo -e "${CYAN}📊 USO DE RECURSOS:${NC}"
    echo "============================================"
    
    # CPU e Memória geral
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 2>/dev/null || echo "N/A")
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' 2>/dev/null || echo "N/A")
    local disk_usage=$(df -h . | awk 'NR==2 {print $5}' 2>/dev/null || echo "N/A")
    
    echo -e "🖥️  CPU: ${cpu_usage}% | 💾 RAM: ${mem_usage}% | 💿 Disco: ${disk_usage}"
    
    # Recursos dos containers Docker
    if docker ps --format "table {{.Names}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -q whats; then
        echo ""
        echo -e "${BLUE}Containers WhatsApp Agent:${NC}"
        docker ps --format "table {{.Names}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -E "(NAME|whats)" || echo "Nenhum container encontrado"
    fi
    echo ""
}

# Verificar conectividade de serviços
check_service_connectivity() {
    echo -e "${CYAN}🌐 CONECTIVIDADE DOS SERVIÇOS:${NC}"
    echo "============================================"
    
    local services=(
        "API Principal:http://localhost:8000/health"
        "Dashboard:http://localhost:8501"
        "PostgreSQL:localhost:5432"
        "Redis:localhost:6379"
        "Prometheus:http://localhost:9090"
        "Grafana:http://localhost:3000"
    )
    
    for service_info in "${services[@]}"; do
        local name=$(echo "$service_info" | cut -d':' -f1)
        local url=$(echo "$service_info" | cut -d':' -f2-)
        
        if echo "$url" | grep -q "^http"; then
            # Teste HTTP
            local status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url" 2>/dev/null || echo "000")
            if [[ "$status_code" =~ ^[23] ]]; then
                echo -e "${GREEN}✅ $name${NC} ($status_code)"
            else
                echo -e "${RED}❌ $name${NC} ($status_code)"
            fi
        else
            # Teste de porta TCP
            local host=$(echo "$url" | cut -d':' -f1)
            local port=$(echo "$url" | cut -d':' -f2)
            if timeout 3 bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null; then
                echo -e "${GREEN}✅ $name${NC} ($host:$port)"
            else
                echo -e "${RED}❌ $name${NC} ($host:$port)"
            fi
        fi
    done
    echo ""
}

# Mostrar logs recentes
show_recent_logs() {
    echo -e "${CYAN}📋 LOGS RECENTES:${NC}"
    echo "============================================"
    
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up" 2>/dev/null; then
        # Logs dos principais serviços
        local services=("app" "dashboard" "postgres" "redis")
        
        for service in "${services[@]}"; do
            if $DOCKER_COMPOSE_CMD ps | grep -q "$service.*Up" 2>/dev/null; then
                echo -e "${BLUE}📄 $service:${NC}"
                $DOCKER_COMPOSE_CMD logs --tail=$MAX_LOG_LINES "$service" 2>/dev/null | tail -n 3 | sed 's/^/   /'
                echo ""
            fi
        done
    else
        echo -e "${YELLOW}⚠️  Nenhum container rodando para mostrar logs${NC}"
        echo ""
    fi
}

# Verificar APIs e endpoints
check_api_endpoints() {
    echo -e "${CYAN}🔗 STATUS DAS APIs:${NC}"
    echo "============================================"
    
    local endpoints=(
        "Health Check:/health"
        "Webhook WhatsApp:/webhook"
        "Documentação:/docs"
        "Métricas:/metrics"
        "Admin API:/admin"
    )
    
    local base_url="http://localhost:8000"
    
    for endpoint_info in "${endpoints[@]}"; do
        local name=$(echo "$endpoint_info" | cut -d':' -f1)
        local path=$(echo "$endpoint_info" | cut -d':' -f2)
        local url="$base_url$path"
        
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url" 2>/dev/null || echo "000")
        local response_time=$(curl -s -o /dev/null -w "%{time_total}" --max-time 3 "$url" 2>/dev/null || echo "N/A")
        
        if [[ "$status_code" =~ ^[23] ]]; then
            echo -e "${GREEN}✅ $name${NC} ($status_code) - ${response_time}s"
        elif [[ "$status_code" == "404" ]]; then
            echo -e "${YELLOW}⚠️  $name${NC} ($status_code) - Não encontrado"
        else
            echo -e "${RED}❌ $name${NC} ($status_code)"
        fi
    done
    echo ""
}

# Verificar estatísticas de banco
check_database_stats() {
    echo -e "${CYAN}🗄️  ESTATÍSTICAS DO BANCO:${NC}"
    echo "============================================"
    
    if $DOCKER_COMPOSE_CMD ps | grep -q "postgres.*Up" 2>/dev/null; then
        # Conectar ao PostgreSQL e obter estatísticas
        local db_stats=$($DOCKER_COMPOSE_CMD exec -T postgres psql -U whatsapp_user -d whatsapp_db -c "
            SELECT 
                schemaname,
                tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes
            FROM pg_stat_user_tables 
            ORDER BY n_tup_ins DESC 
            LIMIT 5;
        " 2>/dev/null || echo "Erro ao conectar")
        
        if [[ "$db_stats" != "Erro ao conectar" ]]; then
            echo -e "${BLUE}Top 5 tabelas por atividade:${NC}"
            echo "$db_stats" | head -n 10 | tail -n +3 | sed 's/^/   /'
        else
            echo -e "${YELLOW}⚠️  Não foi possível conectar ao PostgreSQL${NC}"
        fi
        
        # Tamanho do banco
        local db_size=$($DOCKER_COMPOSE_CMD exec -T postgres psql -U whatsapp_user -d whatsapp_db -c "
            SELECT pg_size_pretty(pg_database_size('whatsapp_db'));
        " 2>/dev/null | head -n 3 | tail -n 1 | xargs || echo "N/A")
        
        echo -e "${BLUE}Tamanho do banco:${NC} $db_size"
    else
        echo -e "${RED}❌ PostgreSQL não está rodando${NC}"
    fi
    echo ""
}

# Monitoramento principal
main_monitor() {
    local mode="${1:-full}"
    
    while true; do
        clear_screen
        
        case $mode in
            "containers"|"c")
                check_container_status
                ;;
            "resources"|"r")
                check_resource_usage
                ;;
            "services"|"s")
                check_service_connectivity
                ;;
            "logs"|"l")
                show_recent_logs
                ;;
            "api"|"a")
                check_api_endpoints
                ;;
            "database"|"db")
                check_database_stats
                ;;
            "full"|*)
                check_container_status
                check_service_connectivity
                check_resource_usage
                check_api_endpoints
                show_recent_logs
                ;;
        esac
        
        echo -e "${WHITE}=========================================================================${NC}"
        echo -e "${BLUE}Pressione Ctrl+C para sair | Próxima atualização em ${REFRESH_INTERVAL}s${NC}"
        
        sleep $REFRESH_INTERVAL
    done
}

# Mostrar ajuda
show_help() {
    echo "WHATSAPP AGENT - Monitor de Sistema"
    echo ""
    echo "Uso: $0 [modo] [opções]"
    echo ""
    echo "Modos:"
    echo "  full, f          Monitor completo (padrão)"
    echo "  containers, c    Apenas containers"
    echo "  resources, r     Apenas recursos"
    echo "  services, s      Apenas conectividade"
    echo "  logs, l          Apenas logs"
    echo "  api, a           Apenas APIs"
    echo "  database, db     Apenas banco de dados"
    echo ""
    echo "Opções:"
    echo "  --interval N     Intervalo de atualização (padrão: 5s)"
    echo "  --help, -h       Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0                    # Monitor completo"
    echo "  $0 containers         # Apenas containers"
    echo "  $0 --interval 10      # Atualizar a cada 10s"
}

# Processar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        containers|c|resources|r|services|s|logs|l|api|a|database|db|full|f)
            MODE="$1"
            shift
            ;;
        *)
            echo "Argumento desconhecido: $1"
            show_help
            exit 1
            ;;
    esac
done

# Verificar diretório e inicializar Docker Compose
if [[ ! -f "docker-compose.yml" ]]; then
    echo -e "${RED}❌ Execute este script a partir da raiz do projeto WhatsApp Agent${NC}"
    exit 1
fi

# Detectar e inicializar Docker Compose
if ! detect_docker_compose; then
    echo -e "${RED}❌ Docker Compose não encontrado!${NC}"
    echo -e "${YELLOW}Instale o Docker Compose para usar este script.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Usando: $DOCKER_COMPOSE_CMD${NC}"

# Configurar tratamento de sinais
trap 'echo -e "\n${GREEN}Monitor finalizado.${NC}"; exit 0' SIGINT SIGTERM

# Executar monitor
main_monitor "${MODE:-full}"
