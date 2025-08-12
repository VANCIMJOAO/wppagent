#!/bin/bash
# Script de Deployment Simplificado
# Wrapper para estratégias de deployment com validações

set -euo pipefail

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROLLING_SCRIPT="$SCRIPT_DIR/rolling_update.sh"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função para verificar pré-requisitos
check_prerequisites() {
    log_info "Verificando pré-requisitos..."
    
    # Verificar se o Docker está rodando
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker não está rodando"
        return 1
    fi
    
    # Verificar se docker-compose está disponível
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "docker-compose não está instalado"
        return 1
    fi
    
    # Verificar se estamos no diretório correto
    if [ ! -f "$PROJECT_DIR/docker-compose.yml" ]; then
        log_error "docker-compose.yml não encontrado no diretório do projeto"
        return 1
    fi
    
    # Verificar espaço em disco
    local available_space=$(df "$PROJECT_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # 1GB em KB
        log_warning "Pouco espaço em disco disponível: $(($available_space / 1024))MB"
    fi
    
    log_success "Pré-requisitos verificados"
    return 0
}

# Função para verificar se há mudanças não commitadas
check_git_status() {
    if [ -d "$PROJECT_DIR/.git" ]; then
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            log_warning "Há mudanças não commitadas no repositório"
            read -p "Continuar mesmo assim? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Deployment cancelado pelo usuário"
                return 1
            fi
        fi
    fi
    return 0
}

# Função para escolher estratégia de deployment
choose_deployment_strategy() {
    echo
    echo "Escolha a estratégia de deployment:"
    echo "1) Rolling Update (recomendado para atualizações menores)"
    echo "2) Blue-Green Deployment (recomendado para atualizações maiores)"
    echo "3) Cancelar"
    echo
    read -p "Opção [1]: " -n 1 -r
    echo
    
    case $REPLY in
        2)
            echo "blue-green"
            ;;
        3)
            echo "cancel"
            ;;
        *)
            echo "rolling"
            ;;
    esac
}

# Função para confirmar deployment
confirm_deployment() {
    local strategy=$1
    local tag=$2
    
    echo
    echo "=== CONFIRMAÇÃO DE DEPLOYMENT ==="
    echo "Estratégia: $strategy"
    echo "Tag da imagem: $tag"
    echo "Projeto: $PROJECT_DIR"
    echo "================================"
    echo
    read -p "Confirma o deployment? [y/N] " -n 1 -r
    echo
    
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Função para deployment com monitoramento
deploy_with_monitoring() {
    local strategy=$1
    local tag=$2
    
    log_info "Iniciando deployment ($strategy) com tag: $tag"
    
    # Executar deployment em background e capturar PID
    $ROLLING_SCRIPT "$strategy" "$tag" &
    local deploy_pid=$!
    
    # Monitorar progresso
    while kill -0 $deploy_pid 2>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo
    
    # Verificar resultado
    wait $deploy_pid
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "Deployment completado com sucesso!"
        
        # Verificar health checks finais
        log_info "Verificando health checks finais..."
        if $ROLLING_SCRIPT health-check app; then
            log_success "Sistema está operacional!"
        else
            log_warning "Health checks apresentaram problemas"
        fi
        
        return 0
    else
        log_error "Deployment falhou com código: $exit_code"
        return $exit_code
    fi
}

# Função para listar deployments recentes
list_recent_deployments() {
    log_info "Deployments recentes:"
    
    if [ -d "$PROJECT_DIR/backups/deployment" ]; then
        ls -la "$PROJECT_DIR/backups/deployment" | tail -10
    else
        log_info "Nenhum deployment encontrado"
    fi
}

# Função para status do sistema
system_status() {
    log_info "Status do sistema:"
    
    echo
    echo "=== CONTAINERS ==="
    docker-compose ps
    
    echo
    echo "=== HEALTH CHECKS ==="
    $ROLLING_SCRIPT health-check app
    $ROLLING_SCRIPT health-check dashboard
    
    echo
    echo "=== RECURSOS ==="
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Função principal
main() {
    local command=${1:-deploy}
    local tag=${2:-$(date +%Y%m%d_%H%M%S)}
    
    cd "$PROJECT_DIR"
    
    case $command in
        "deploy")
            # Verificar pré-requisitos
            if ! check_prerequisites; then
                exit 1
            fi
            
            # Verificar status do git
            if ! check_git_status; then
                exit 1
            fi
            
            # Escolher estratégia
            local strategy=$(choose_deployment_strategy)
            
            if [ "$strategy" = "cancel" ]; then
                log_info "Deployment cancelado"
                exit 0
            fi
            
            # Confirmar deployment
            if ! confirm_deployment "$strategy" "$tag"; then
                log_info "Deployment cancelado"
                exit 0
            fi
            
            # Executar deployment
            deploy_with_monitoring "$strategy" "$tag"
            ;;
            
        "rollback")
            log_warning "Iniciando rollback..."
            if confirm_deployment "rollback" "previous"; then
                $ROLLING_SCRIPT rollback
            else
                log_info "Rollback cancelado"
            fi
            ;;
            
        "status")
            system_status
            ;;
            
        "history")
            list_recent_deployments
            ;;
            
        "backup")
            log_info "Criando backup manual..."
            $ROLLING_SCRIPT backup
            ;;
            
        "help"|*)
            echo "Uso: $0 {deploy|rollback|status|history|backup} [tag]"
            echo ""
            echo "Comandos:"
            echo "  deploy [tag]    - Fazer deployment (interativo)"
            echo "  rollback        - Rollback para versão anterior"
            echo "  status          - Mostrar status do sistema"
            echo "  history         - Listar deployments recentes"
            echo "  backup          - Criar backup manual"
            echo "  help            - Mostrar esta ajuda"
            echo ""
            echo "Exemplos:"
            echo "  $0 deploy                    # Deployment interativo"
            echo "  $0 deploy v1.2.3            # Deployment com tag específica"
            echo "  $0 rollback                  # Rollback"
            echo "  $0 status                    # Status do sistema"
            ;;
    esac
}

# Executar função principal
main "$@"
