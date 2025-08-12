#!/bin/bash

# =========================================================================
# WHATSAPP AGENT - SCRIPT DE PARADA COMPLETA
# =========================================================================
# Este script para todos os componentes da aplicação WhatsApp Agent
# Criado em: 11 de Agosto de 2025
# Versão: 1.0.0
# =========================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
WHITE='\033[1;37m'
NC='\033[0m'

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

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Banner
print_banner() {
    echo -e "${RED}"
    echo "==========================================================================="
    echo "                    🛑 WHATSAPP AGENT STOP SCRIPT 🛑"
    echo "==========================================================================="
    echo "                  Parando todos os componentes da aplicação"
    echo "==========================================================================="
    echo -e "${NC}"
}

# Função principal de parada
stop_application() {
    local force_mode=false
    local preserve_data=true
    
    # Detectar Docker Compose
    if ! detect_docker_compose; then
        log_error "❌ Docker Compose não encontrado!"
        exit 1
    fi
    
    log_info "   Docker Compose: $DOCKER_COMPOSE_CMD"
    
    # Processar argumentos
    for arg in "$@"; do
        case $arg in
            --force|-f)
                force_mode=true
                shift
                ;;
            --clean|-c)
                preserve_data=false
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
        esac
    done
    
    log "🛑 Iniciando parada da aplicação WhatsApp Agent..."
    
    # Parar containers Docker Compose
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up" 2>/dev/null; then
        log_info "   Parando containers Docker Compose..."
        
        if [[ "$force_mode" == true ]]; then
            $DOCKER_COMPOSE_CMD kill
            log_info "   Containers forçadamente terminados"
        else
            $DOCKER_COMPOSE_CMD stop
            log_info "   Containers parados graciosamente"
        fi
        
        $DOCKER_COMPOSE_CMD down
        log_info "   Containers removidos"
        
        if [[ "$preserve_data" == false ]]; then
            log_warning "   Removendo volumes de dados..."
            $DOCKER_COMPOSE_CMD down -v --remove-orphans
            log_warning "   ⚠️  DADOS REMOVIDOS PERMANENTEMENTE!"
        fi
    else
        log_info "   Nenhum container Docker Compose rodando"
    fi
    
    # Parar processos Python relacionados
    local python_pids=$(pgrep -f "app.main\|streamlit\|uvicorn\|whatsapp" 2>/dev/null || true)
    if [[ -n "$python_pids" ]]; then
        log_info "   Parando processos Python relacionados..."
        
        if [[ "$force_mode" == true ]]; then
            echo "$python_pids" | xargs kill -KILL 2>/dev/null || true
            log_info "   Processos Python forçadamente terminados"
        else
            echo "$python_pids" | xargs kill -TERM 2>/dev/null || true
            sleep 3
            # Verificar se ainda há processos rodando
            local remaining_pids=$(pgrep -f "app.main\|streamlit\|uvicorn\|whatsapp" 2>/dev/null || true)
            if [[ -n "$remaining_pids" ]]; then
                echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
                log_info "   Processos restantes forçadamente terminados"
            fi
        fi
    else
        log_info "   Nenhum processo Python relacionado encontrado"
    fi
    
    # Limpar recursos de rede
    log_info "   Limpando recursos de rede Docker..."
    docker network prune -f 2>/dev/null || true
    
    # Limpar imagens órfãs se solicitado
    if [[ "$preserve_data" == false ]]; then
        log_info "   Removendo imagens órfãs..."
        docker image prune -f 2>/dev/null || true
    fi
    
    log "✅ Aplicação WhatsApp Agent parada com sucesso!"
    
    # Mostrar status final
    show_final_status
}

# Mostrar status final
show_final_status() {
    echo ""
    echo -e "${WHITE}=========================================================================${NC}"
    echo -e "${GREEN}                      🎯 STATUS FINAL DA PARADA${NC}"
    echo -e "${WHITE}=========================================================================${NC}"
    echo ""
    
    # Verificar containers
    local running_containers=$($DOCKER_COMPOSE_CMD ps --services --filter "status=running" 2>/dev/null || true)
    if [[ -n "$running_containers" ]]; then
        echo -e "${YELLOW}⚠️  Containers ainda rodando:${NC}"
        echo "$running_containers" | sed 's/^/   - /'
    else
        echo -e "${GREEN}✅ Nenhum container rodando${NC}"
    fi
    
    # Verificar processos Python
    local python_procs=$(pgrep -f "app.main\|streamlit\|uvicorn\|whatsapp" 2>/dev/null || true)
    if [[ -n "$python_procs" ]]; then
        echo -e "${YELLOW}⚠️  Processos Python ainda rodando:${NC}"
        ps -p $python_procs -o pid,cmd --no-headers | sed 's/^/   - /'
    else
        echo -e "${GREEN}✅ Nenhum processo Python relacionado rodando${NC}"
    fi
    
    # Verificar portas
    local used_ports=$(netstat -tlnp 2>/dev/null | grep -E ":8000|:8501|:5432|:6379" || true)
    if [[ -n "$used_ports" ]]; then
        echo -e "${YELLOW}⚠️  Portas da aplicação ainda em uso:${NC}"
        echo "$used_ports" | sed 's/^/   /'
    else
        echo -e "${GREEN}✅ Todas as portas liberadas${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🔧 Para reiniciar a aplicação:${NC}"
    echo -e "   ./scripts/start_complete_application.sh"
    echo ""
    echo -e "${WHITE}=========================================================================${NC}"
}

# Mostrar ajuda
show_help() {
    echo "WHATSAPP AGENT - Script de Parada"
    echo ""
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --force, -f      Parada forçada (kill -9)"
    echo "  --clean, -c      Remove volumes e dados (CUIDADO!)"
    echo "  --help, -h       Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0                    # Parada normal"
    echo "  $0 --force            # Parada forçada"
    echo "  $0 --clean            # Parada com limpeza de dados"
    echo "  $0 --force --clean    # Parada forçada com limpeza"
}

# Verificar diretório
check_directory() {
    if [[ ! -f "docker-compose.yml" ]]; then
        echo -e "${RED}❌ Execute este script a partir da raiz do projeto WhatsApp Agent${NC}"
        exit 1
    fi
}

# Função principal
main() {
    print_banner
    check_directory
    stop_application "$@"
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
