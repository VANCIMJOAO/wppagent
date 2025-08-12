#!/bin/bash
# Rolling Update Strategy para WhatsApp Agent
# Deployment com zero downtime usando blue-green deployment

set -euo pipefail

# Configurações
COMPOSE_FILE="docker-compose.yml"
COMPOSE_OVERRIDE="docker-compose.override.yml"
BACKUP_DIR="backups/deployment"
LOG_FILE="logs/deployment.log"
HEALTH_CHECK_TIMEOUT=60
ROLLBACK_TIMEOUT=300

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Função para verificar health checks
check_health() {
    local service=$1
    local timeout=${2:-30}
    local count=0
    
    log_info "Verificando health check do serviço: $service"
    
    while [ $count -lt $timeout ]; do
        if docker-compose ps | grep "$service" | grep -q "healthy\|Up"; then
            log_success "Serviço $service está saudável"
            return 0
        fi
        
        sleep 2
        count=$((count + 1))
    done
    
    log_error "Health check falhou para o serviço: $service"
    return 1
}

# Função para backup do estado atual
backup_current_state() {
    log_info "Criando backup do estado atual..."
    
    mkdir -p "$BACKUP_DIR/$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$(date +%Y%m%d_%H%M%S)"
    
    # Backup da configuração
    cp docker-compose.yml "$backup_path/"
    [ -f "$COMPOSE_OVERRIDE" ] && cp "$COMPOSE_OVERRIDE" "$backup_path/"
    
    # Backup do banco de dados
    if docker-compose ps postgres | grep -q "Up"; then
        log_info "Fazendo backup do banco de dados..."
        docker-compose exec -T postgres pg_dump -U whatsapp_user whatsapp_db > "$backup_path/database_backup.sql"
    fi
    
    # Salvar imagens atuais
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}" | grep whatsapp > "$backup_path/current_images.txt"
    
    echo "$backup_path" > "$BACKUP_DIR/latest_backup.txt"
    log_success "Backup criado em: $backup_path"
}

# Função para rollback
rollback() {
    log_warning "Iniciando rollback..."
    
    if [ ! -f "$BACKUP_DIR/latest_backup.txt" ]; then
        log_error "Nenhum backup encontrado para rollback"
        return 1
    fi
    
    local backup_path=$(cat "$BACKUP_DIR/latest_backup.txt")
    
    if [ ! -d "$backup_path" ]; then
        log_error "Diretório de backup não encontrado: $backup_path"
        return 1
    fi
    
    # Restaurar configurações
    cp "$backup_path/docker-compose.yml" .
    [ -f "$backup_path/$COMPOSE_OVERRIDE" ] && cp "$backup_path/$COMPOSE_OVERRIDE" .
    
    # Parar serviços atuais
    docker-compose down --timeout 30
    
    # Restaurar banco de dados se necessário
    if [ -f "$backup_path/database_backup.sql" ]; then
        log_info "Restaurando banco de dados..."
        docker-compose up -d postgres
        sleep 10
        docker-compose exec -T postgres psql -U whatsapp_user -d whatsapp_db < "$backup_path/database_backup.sql"
    fi
    
    # Subir serviços
    docker-compose up -d
    
    # Verificar health checks
    if check_health "app" $HEALTH_CHECK_TIMEOUT; then
        log_success "Rollback completado com sucesso"
        return 0
    else
        log_error "Rollback falhou"
        return 1
    fi
}

# Função para deployment gradual
rolling_update() {
    local new_image_tag=${1:-latest}
    
    log_info "Iniciando rolling update com imagem: $new_image_tag"
    
    # 1. Backup do estado atual
    backup_current_state
    
    # 2. Build das novas imagens
    log_info "Fazendo build das novas imagens..."
    docker-compose build --parallel
    
    # 3. Tag das imagens com versão
    docker tag whatsapp-agent:latest "whatsapp-agent:$new_image_tag"
    docker tag whatsapp-dashboard:latest "whatsapp-dashboard:$new_image_tag"
    
    # 4. Atualizar serviços um por vez
    local services=("postgres" "redis" "app" "dashboard" "nginx")
    
    for service in "${services[@]}"; do
        log_info "Atualizando serviço: $service"
        
        # Parar o serviço antigo
        docker-compose stop "$service"
        
        # Remover container antigo
        docker-compose rm -f "$service"
        
        # Subir novo container
        docker-compose up -d "$service"
        
        # Verificar health check
        if ! check_health "$service" $HEALTH_CHECK_TIMEOUT; then
            log_error "Health check falhou para $service durante update"
            log_warning "Iniciando rollback automático..."
            rollback
            return 1
        fi
        
        log_success "Serviço $service atualizado com sucesso"
        sleep 5  # Pequena pausa entre atualizações
    done
    
    # 5. Verificação final
    log_info "Verificando estado final do sistema..."
    
    for service in "${services[@]}"; do
        if ! check_health "$service" 30; then
            log_error "Verificação final falhou para $service"
            rollback
            return 1
        fi
    done
    
    # 6. Cleanup de imagens antigas
    log_info "Limpando imagens antigas..."
    docker image prune -f --filter "label=maintainer=WhatsApp Agent Team"
    
    log_success "Rolling update completado com sucesso!"
    return 0
}

# Função para blue-green deployment
blue_green_deployment() {
    local new_image_tag=${1:-latest}
    
    log_info "Iniciando blue-green deployment com imagem: $new_image_tag"
    
    # 1. Backup do estado atual (Blue environment)
    backup_current_state
    
    # 2. Criar compose file para green environment
    cp docker-compose.yml docker-compose.green.yml
    sed -i 's/8000:8000/8001:8000/' docker-compose.green.yml
    sed -i 's/8501:8501/8502:8501/' docker-compose.green.yml
    sed -i 's/whatsapp-/whatsapp-green-/g' docker-compose.green.yml
    
    # 3. Build e iniciar green environment
    log_info "Iniciando Green environment..."
    docker-compose -f docker-compose.green.yml up -d --build
    
    # 4. Verificar health checks do green environment
    sleep 30  # Aguardar inicialização
    
    if ! check_health "whatsapp-green-app" $HEALTH_CHECK_TIMEOUT; then
        log_error "Health check falhou no Green environment"
        docker-compose -f docker-compose.green.yml down
        rm docker-compose.green.yml
        return 1
    fi
    
    # 5. Teste de fumaça no green environment
    log_info "Executando testes de fumaça no Green environment..."
    if ! curl -f http://localhost:8001/health; then
        log_error "Teste de fumaça falhou no Green environment"
        docker-compose -f docker-compose.green.yml down
        rm docker-compose.green.yml
        return 1
    fi
    
    # 6. Redirecionar tráfego (atualizar nginx ou load balancer)
    log_info "Redirecionando tráfego para Green environment..."
    
    # Atualizar configuração do nginx
    sed -i 's/app:8000/app:8001/' config/nginx/nginx.conf
    sed -i 's/dashboard:8501/dashboard:8502/' config/nginx/nginx.conf
    
    # Recarregar nginx
    docker-compose exec nginx nginx -s reload
    
    # 7. Verificar se tráfego está funcionando
    sleep 10
    if ! curl -f http://localhost/health; then
        log_error "Falha após redirecionamento de tráfego"
        # Reverter nginx
        sed -i 's/app:8001/app:8000/' config/nginx/nginx.conf
        sed -i 's/dashboard:8502/dashboard:8501/' config/nginx/nginx.conf
        docker-compose exec nginx nginx -s reload
        docker-compose -f docker-compose.green.yml down
        rm docker-compose.green.yml
        return 1
    fi
    
    # 8. Parar blue environment
    log_info "Parando Blue environment..."
    docker-compose down
    
    # 9. Promover green para production
    log_info "Promovendo Green environment para produção..."
    mv docker-compose.yml docker-compose.blue.yml
    mv docker-compose.green.yml docker-compose.yml
    
    # Reverter configuração do nginx para portas padrão
    sed -i 's/app:8001/app:8000/' config/nginx/nginx.conf
    sed -i 's/dashboard:8502/dashboard:8501/' config/nginx/nginx.conf
    
    # Recriar serviços com configuração padrão
    docker-compose down
    docker-compose up -d
    
    # Recarregar nginx
    docker-compose exec nginx nginx -s reload
    
    # 10. Cleanup
    log_info "Limpando ambiente Blue antigo..."
    docker-compose -f docker-compose.blue.yml down --rmi all --volumes --remove-orphans
    rm docker-compose.blue.yml
    
    log_success "Blue-green deployment completado com sucesso!"
    return 0
}

# Função principal
main() {
    local command=${1:-help}
    local image_tag=${2:-latest}
    
    # Criar diretórios necessários
    mkdir -p "$BACKUP_DIR" logs
    
    case $command in
        "rolling")
            rolling_update "$image_tag"
            ;;
        "blue-green")
            blue_green_deployment "$image_tag"
            ;;
        "rollback")
            rollback
            ;;
        "health-check")
            local service=${2:-app}
            check_health "$service"
            ;;
        "backup")
            backup_current_state
            ;;
        "help"|*)
            echo "Uso: $0 {rolling|blue-green|rollback|health-check|backup} [image_tag|service]"
            echo ""
            echo "Comandos:"
            echo "  rolling [tag]        - Rolling update com zero downtime"
            echo "  blue-green [tag]     - Blue-green deployment"
            echo "  rollback             - Rollback para versão anterior"
            echo "  health-check [service] - Verificar health check de um serviço"
            echo "  backup               - Fazer backup do estado atual"
            echo "  help                 - Mostrar esta ajuda"
            ;;
    esac
}

# Trap para cleanup em caso de erro
trap 'log_error "Script interrompido"; exit 1' INT TERM

# Executar função principal
main "$@"
