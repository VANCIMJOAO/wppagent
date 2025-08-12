#!/bin/bash
# 🔄 SCRIPT DE RECOVERY AUTOMÁTICO
# Sistema inteligente de recuperação automática com múltiplos níveis

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
RECOVERY_LOG="$PROJECT_DIR/logs/recovery.log"
MAX_RETRY_ATTEMPTS=3
HEALTH_CHECK_URL="http://localhost:8000/health"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

# Criar log de recovery se não existir
mkdir -p "$(dirname "$RECOVERY_LOG")"
touch "$RECOVERY_LOG"

# Funções de log
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$RECOVERY_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log "INFO" "$1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log "SUCCESS" "$1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log "WARNING" "$1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log "ERROR" "$1"
}

# Função para notificar Slack
notify_slack() {
    local message="$1"
    local urgency="${2:-normal}"
    
    if [ -n "$SLACK_WEBHOOK" ]; then
        local emoji="🔄"
        if [ "$urgency" = "critical" ]; then
            emoji="🚨"
        elif [ "$urgency" = "success" ]; then
            emoji="✅"
        fi
        
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-type: application/json' \
            --data "{\"text\":\"$emoji WhatsApp Agent Recovery: $message\"}" \
            >/dev/null 2>&1 || true
    fi
}

# Função para verificar saúde do sistema
check_health() {
    log_info "Verificando saúde do sistema..."
    
    # Health check HTTP
    if curl -f "$HEALTH_CHECK_URL" >/dev/null 2>&1; then
        log_success "Health check passou"
        return 0
    else
        log_error "Health check falhou"
        return 1
    fi
}

# Função para verificar containers
check_containers() {
    log_info "Verificando status dos containers..."
    
    local unhealthy_containers=()
    
    # Verificar cada serviço
    while IFS= read -r service; do
        if [ -n "$service" ]; then
            local status=$(docker-compose ps -q "$service" | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
            if [ "$status" != "running" ]; then
                unhealthy_containers+=("$service")
                log_warning "Container $service não está rodando (status: $status)"
            fi
        fi
    done < <(docker-compose config --services)
    
    if [ ${#unhealthy_containers[@]} -eq 0 ]; then
        log_success "Todos os containers estão rodando"
        return 0
    else
        log_error "Containers com problema: ${unhealthy_containers[*]}"
        return 1
    fi
}

# Função para verificar recursos do sistema
check_resources() {
    log_info "Verificando recursos do sistema..."
    
    # Verificar espaço em disco
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log_error "Espaço em disco crítico: $disk_usage%"
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "Espaço em disco alto: $disk_usage%"
    fi
    
    # Verificar memória
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$mem_usage" -gt 95 ]; then
        log_error "Uso de memória crítico: $mem_usage%"
        return 1
    elif [ "$mem_usage" -gt 85 ]; then
        log_warning "Uso de memória alto: $mem_usage%"
    fi
    
    log_success "Recursos do sistema OK (Disk: $disk_usage%, RAM: $mem_usage%)"
    return 0
}

# NÍVEL 1: Recovery Suave
level_1_soft_recovery() {
    log_info "=== NÍVEL 1: RECOVERY SUAVE ==="
    notify_slack "Iniciando recovery suave (Level 1)" "normal"
    
    # Restart apenas da aplicação
    log_info "Reiniciando aplicação..."
    docker-compose restart app
    
    # Aguardar inicialização
    sleep 30
    
    # Verificar se resolveu
    if check_health; then
        log_success "Recovery suave bem-sucedido!"
        notify_slack "Recovery Level 1 bem-sucedido" "success"
        return 0
    else
        log_warning "Recovery suave falhou"
        return 1
    fi
}

# NÍVEL 2: Recovery Médio
level_2_medium_recovery() {
    log_info "=== NÍVEL 2: RECOVERY MÉDIO ==="
    notify_slack "Iniciando recovery médio (Level 2)" "normal"
    
    # Restart de todos os serviços
    log_info "Reiniciando todos os serviços..."
    docker-compose restart
    
    # Aguardar inicialização
    sleep 60
    
    # Verificar containers
    if ! check_containers; then
        log_warning "Alguns containers ainda com problema, tentando start individual..."
        docker-compose up -d
        sleep 30
    fi
    
    # Verificar se resolveu
    if check_health; then
        log_success "Recovery médio bem-sucedido!"
        notify_slack "Recovery Level 2 bem-sucedido" "success"
        return 0
    else
        log_warning "Recovery médio falhou"
        return 1
    fi
}

# NÍVEL 3: Recovery Completo
level_3_full_recovery() {
    log_info "=== NÍVEL 3: RECOVERY COMPLETO ==="
    notify_slack "Iniciando recovery completo (Level 3)" "critical"
    
    # Parar tudo
    log_info "Parando todos os serviços..."
    docker-compose down
    
    # Limpeza de recursos
    log_info "Executando limpeza de recursos..."
    
    # Limpar containers órfãos
    docker container prune -f >/dev/null 2>&1 || true
    
    # Limpar redes órfãs
    docker network prune -f >/dev/null 2>&1 || true
    
    # Limpar volumes não utilizados (cuidado!)
    # docker volume prune -f >/dev/null 2>&1 || true
    
    # Verificar espaço em disco e limpar se necessário
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        log_info "Limpando logs antigos devido ao espaço em disco..."
        find "$PROJECT_DIR/logs" -name "*.log" -mtime +7 -delete 2>/dev/null || true
        find "$PROJECT_DIR/logs" -name "*.log.*" -mtime +3 -delete 2>/dev/null || true
    fi
    
    # Aguardar um pouco
    sleep 10
    
    # Subir serviços em ordem
    log_info "Iniciando serviços em ordem..."
    
    # 1. Banco de dados primeiro
    docker-compose up -d postgres redis
    sleep 30
    
    # 2. Aplicação
    docker-compose up -d app
    sleep 60
    
    # 3. Serviços auxiliares
    docker-compose up -d nginx dashboard 2>/dev/null || true
    
    # Verificar se resolveu
    if check_health && check_containers; then
        log_success "Recovery completo bem-sucedido!"
        notify_slack "Recovery Level 3 bem-sucedido" "success"
        return 0
    else
        log_error "Recovery completo falhou"
        return 1
    fi
}

# NÍVEL 4: Recovery de Emergência (Backup Restore)
level_4_emergency_recovery() {
    log_info "=== NÍVEL 4: RECOVERY DE EMERGÊNCIA ==="
    notify_slack "Iniciando recovery de emergência (Level 4) - BACKUP RESTORE" "critical"
    
    # Parar tudo
    docker-compose down
    
    # Backup da configuração atual (por segurança)
    local backup_dir="$PROJECT_DIR/emergency_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    cp -r "$PROJECT_DIR/logs" "$backup_dir/" 2>/dev/null || true
    cp "$PROJECT_DIR/.env" "$backup_dir/" 2>/dev/null || true
    cp "$PROJECT_DIR/docker-compose.yml" "$backup_dir/" 2>/dev/null || true
    
    log_info "Backup de emergência criado em: $backup_dir"
    
    # Verificar se existem backups automáticos
    local latest_backup=""
    if [ -d "$PROJECT_DIR/backups/automatic" ]; then
        latest_backup=$(ls -t "$PROJECT_DIR/backups/automatic/"*.sql.gz 2>/dev/null | head -1 || echo "")
    fi
    
    if [ -n "$latest_backup" ]; then
        log_info "Restaurando backup: $latest_backup"
        
        # Iniciar apenas PostgreSQL para restore
        docker-compose up -d postgres
        sleep 30
        
        # Restaurar backup
        gunzip -c "$latest_backup" | docker-compose exec -T postgres psql -U ${DB_USER:-whatsapp_user} ${DB_NAME:-whatsapp_db}
        
        if [ $? -eq 0 ]; then
            log_success "Backup restaurado com sucesso"
            
            # Iniciar outros serviços
            docker-compose up -d
            sleep 90
            
            if check_health; then
                log_success "Recovery de emergência bem-sucedido!"
                notify_slack "Recovery Level 4 (backup restore) bem-sucedido" "success"
                return 0
            fi
        else
            log_error "Falha ao restaurar backup"
        fi
    else
        log_error "Nenhum backup automático encontrado"
    fi
    
    log_error "Recovery de emergência falhou"
    return 1
}

# Função para validar recuperação
validate_recovery() {
    log_info "Validando recuperação..."
    
    local validation_score=0
    local total_checks=5
    
    # 1. Health check
    if check_health; then
        validation_score=$((validation_score + 1))
    fi
    
    # 2. Containers
    if check_containers; then
        validation_score=$((validation_score + 1))
    fi
    
    # 3. Recursos
    if check_resources; then
        validation_score=$((validation_score + 1))
    fi
    
    # 4. Webhook test
    if curl -f -X POST "$HEALTH_CHECK_URL/../webhook" \
           -H "Content-Type: application/json" \
           -d '{"object":"whatsapp_business_account","entry":[]}' >/dev/null 2>&1; then
        validation_score=$((validation_score + 1))
        log_success "Webhook test passou"
    else
        log_warning "Webhook test falhou"
    fi
    
    # 5. Database connectivity
    if docker-compose exec -T postgres pg_isready -U ${DB_USER:-whatsapp_user} >/dev/null 2>&1; then
        validation_score=$((validation_score + 1))
        log_success "Database connectivity OK"
    else
        log_warning "Database connectivity falhou"
    fi
    
    local success_rate=$((validation_score * 100 / total_checks))
    log_info "Score de validação: $validation_score/$total_checks ($success_rate%)"
    
    if [ $success_rate -ge 80 ]; then
        log_success "Validação passou! Sistema operacional."
        return 0
    else
        log_error "Validação falhou! Sistema ainda com problemas."
        return 1
    fi
}

# Função para monitoramento pós-recovery
post_recovery_monitoring() {
    log_info "Iniciando monitoramento pós-recovery..."
    
    local monitor_duration=300  # 5 minutos
    local check_interval=30     # 30 segundos
    local checks=0
    local failures=0
    
    notify_slack "Iniciando monitoramento pós-recovery (5 minutos)"
    
    for ((i=0; i<monitor_duration; i+=check_interval)); do
        checks=$((checks + 1))
        
        if ! check_health; then
            failures=$((failures + 1))
            log_warning "Health check falhou durante monitoramento (tentativa $checks)"
            
            # Se muitas falhas, alertar
            if [ $failures -gt 2 ]; then
                log_error "Muitas falhas durante monitoramento pós-recovery!"
                notify_slack "Sistema instável após recovery - $failures falhas em $checks tentativas" "critical"
                return 1
            fi
        else
            log_info "Health check OK (tentativa $checks)"
        fi
        
        sleep $check_interval
    done
    
    local success_rate=$((100 * (checks - failures) / checks))
    log_success "Monitoramento concluído: $success_rate% de sucesso ($failures falhas em $checks checks)"
    
    if [ $success_rate -ge 90 ]; then
        notify_slack "Sistema estável após recovery - $success_rate% uptime" "success"
        return 0
    else
        notify_slack "Sistema instável após recovery - apenas $success_rate% uptime" "critical"
        return 1
    fi
}

# Função principal de recovery
execute_recovery() {
    log_info "🔄 INICIANDO SISTEMA DE RECOVERY AUTOMÁTICO"
    log_info "Timestamp: $(date)"
    
    cd "$PROJECT_DIR"
    
    # Diagnóstico inicial
    log_info "Executando diagnóstico inicial..."
    local initial_health=$(check_health && echo "healthy" || echo "unhealthy")
    local initial_containers=$(check_containers && echo "healthy" || echo "unhealthy")
    local initial_resources=$(check_resources && echo "healthy" || echo "unhealthy")
    
    log_info "Status inicial - Health: $initial_health, Containers: $initial_containers, Resources: $initial_resources"
    
    # Se sistema está saudável, sair
    if [ "$initial_health" = "healthy" ] && [ "$initial_containers" = "healthy" ]; then
        log_success "Sistema já está saudável. Nenhum recovery necessário."
        return 0
    fi
    
    # Tentar recovery em níveis crescentes
    local recovery_level=1
    local max_levels=4
    
    for level in $(seq 1 $max_levels); do
        log_info "Tentando recovery nível $level..."
        
        case $level in
            1)
                if level_1_soft_recovery; then
                    break
                fi
                ;;
            2)
                if level_2_medium_recovery; then
                    break
                fi
                ;;
            3)
                if level_3_full_recovery; then
                    break
                fi
                ;;
            4)
                if level_4_emergency_recovery; then
                    break
                fi
                ;;
        esac
        
        recovery_level=$((level + 1))
        
        if [ $recovery_level -gt $max_levels ]; then
            log_error "Todos os níveis de recovery falharam!"
            notify_slack "FALHA CRÍTICA: Todos os níveis de recovery falharam. Intervenção manual necessária." "critical"
            return 1
        fi
        
        log_warning "Recovery nível $level falhou, tentando nível $recovery_level..."
        sleep 10
    done
    
    # Validar recuperação
    if validate_recovery; then
        log_success "Recovery concluído com sucesso no nível $recovery_level!"
        
        # Monitoramento pós-recovery
        if post_recovery_monitoring; then
            log_success "Sistema completamente estável após recovery!"
            notify_slack "Recovery completo bem-sucedido - sistema estável" "success"
            return 0
        else
            log_warning "Sistema instável após recovery"
            notify_slack "Recovery parcial - sistema instável" "critical"
            return 1
        fi
    else
        log_error "Recovery falhou na validação!"
        notify_slack "Recovery falhou na validação final" "critical"
        return 1
    fi
}

# Função para modo de monitoramento contínuo
continuous_monitoring() {
    log_info "Iniciando modo de monitoramento contínuo..."
    
    local check_interval=60  # 1 minuto
    local failure_threshold=3
    local consecutive_failures=0
    
    while true; do
        if check_health; then
            consecutive_failures=0
            log_info "Sistema saudável ($(date))"
        else
            consecutive_failures=$((consecutive_failures + 1))
            log_warning "Health check falhou (falha $consecutive_failures/$failure_threshold)"
            
            if [ $consecutive_failures -ge $failure_threshold ]; then
                log_error "Threshold de falhas atingido! Iniciando recovery automático..."
                execute_recovery
                consecutive_failures=0
            fi
        fi
        
        sleep $check_interval
    done
}

# Função para exibir ajuda
show_help() {
    echo "🔄 SISTEMA DE RECOVERY AUTOMÁTICO - WhatsApp Agent"
    echo
    echo "Uso: $0 [comando] [opções]"
    echo
    echo "Comandos:"
    echo "  auto       - Executa recovery automático (padrão)"
    echo "  level1     - Executa apenas recovery nível 1 (suave)"
    echo "  level2     - Executa apenas recovery nível 2 (médio)"
    echo "  level3     - Executa apenas recovery nível 3 (completo)"
    echo "  level4     - Executa apenas recovery nível 4 (emergência)"
    echo "  monitor    - Modo de monitoramento contínuo"
    echo "  check      - Apenas verifica saúde do sistema"
    echo "  validate   - Executa validação completa"
    echo "  help       - Exibe esta ajuda"
    echo
    echo "Variáveis de ambiente:"
    echo "  SLACK_WEBHOOK - Webhook do Slack para notificações"
    echo
    echo "Exemplos:"
    echo "  $0 auto                    # Recovery automático"
    echo "  $0 monitor                 # Monitoramento contínuo"
    echo "  SLACK_WEBHOOK=<url> $0 auto  # Com notificações Slack"
}

# Função principal
main() {
    local command="${1:-auto}"
    
    case "$command" in
        "auto")
            execute_recovery
            ;;
        "level1")
            level_1_soft_recovery
            ;;
        "level2")
            level_2_medium_recovery
            ;;
        "level3")
            level_3_full_recovery
            ;;
        "level4")
            level_4_emergency_recovery
            ;;
        "monitor")
            continuous_monitoring
            ;;
        "check")
            if check_health && check_containers && check_resources; then
                log_success "Todos os checks passaram!"
                exit 0
            else
                log_error "Alguns checks falharam!"
                exit 1
            fi
            ;;
        "validate")
            validate_recovery
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Comando desconhecido: $command"
            show_help
            exit 1
            ;;
    esac
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
