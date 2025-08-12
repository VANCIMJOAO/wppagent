#!/bin/bash

# =========================================================================
# WHATSAPP AGENT - SCRIPT DE INICIALIZAÇÃO COMPLETA
# =========================================================================
# Este script inicia todos os componentes da aplicação WhatsApp Agent
# Criado em: 11 de Agosto de 2025
# Versão: 1.0.0
# =========================================================================

set -e  # Sair em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Função para log com timestamp
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Banner de inicialização
print_banner() {
    echo -e "${PURPLE}"
    echo "==========================================================================="
    echo "                    🚀 WHATSAPP AGENT STARTUP SCRIPT 🚀"
    echo "==========================================================================="
    echo "               Inicializando todos os componentes da aplicação"
    echo "                        Versão: 1.0.0 | $(date '+%Y-%m-%d')"
    echo "==========================================================================="
    echo -e "${NC}"
}

# Verificar se está no diretório correto
check_directory() {
    log "🔍 Verificando diretório da aplicação..."
    
    if [[ ! -f "docker-compose.yml" ]] || [[ ! -f "requirements.txt" ]] || [[ ! -d "app" ]]; then
        log_error "❌ Não foi possível encontrar os arquivos da aplicação WhatsApp Agent!"
        log_error "   Execute este script a partir da raiz do projeto."
        exit 1
    fi
    
    log "✅ Diretório da aplicação confirmado: $(pwd)"
}

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

# Verificar dependências do sistema
check_dependencies() {
    log "🔧 Verificando dependências do sistema..."
    
    local missing_deps=()
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # Verificar Docker Compose
    if ! detect_docker_compose; then
        missing_deps+=("docker-compose")
    fi
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Verificar Git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    if [[ ${#missing_deps[@]} -ne 0 ]]; then
        log_error "❌ Dependências não encontradas: ${missing_deps[*]}"
        log_info "   Instale as dependências antes de continuar."
        exit 1
    fi
    
    log "✅ Todas as dependências encontradas"
    log_info "   Docker Compose: $DOCKER_COMPOSE_CMD"
}

# Verificar arquivo .env
check_env_file() {
    log "🔐 Verificando configurações de ambiente..."
    
    if [[ ! -f ".env" ]]; then
        log_warning "⚠️  Arquivo .env não encontrado!"
        
        if [[ -f ".env.example" ]]; then
            log_info "📋 Copiando .env.example para .env..."
            cp .env.example .env
            log_warning "⚠️  IMPORTANTE: Configure as variáveis no arquivo .env antes de usar em produção!"
        else
            log_error "❌ Nem .env nem .env.example encontrados!"
            exit 1
        fi
    fi
    
    # Verificar variáveis críticas
    local critical_vars=("OPENAI_API_KEY" "WHATSAPP_ACCESS_TOKEN" "DB_PASSWORD" "JWT_SECRET_KEY")
    local missing_vars=()
    
    for var in "${critical_vars[@]}"; do
        if ! grep -q "^${var}=" .env || grep -q "^${var}=$" .env || grep -q "^${var}=your_" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -ne 0 ]]; then
        log_warning "⚠️  Variáveis não configuradas: ${missing_vars[*]}"
        log_warning "   Configure essas variáveis no arquivo .env para funcionamento completo."
    else
        log "✅ Configurações de ambiente verificadas"
    fi
}

# Parar serviços existentes
stop_existing_services() {
    log "🛑 Parando serviços existentes..."
    
    # Parar Docker Compose se estiver rodando
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up" 2>/dev/null; then
        log_info "   Parando containers Docker..."
        $DOCKER_COMPOSE_CMD down 2>/dev/null || true
    fi
    
    # Parar processos Python relacionados
    local python_pids=$(pgrep -f "app.main\|streamlit\|uvicorn" || true)
    if [[ -n "$python_pids" ]]; then
        log_info "   Parando processos Python relacionados..."
        echo "$python_pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
    fi
    
    log "✅ Serviços existentes parados"
}

# Limpar caches e arquivos temporários
cleanup_temp_files() {
    log "🧹 Limpando arquivos temporários..."
    
    # Limpar cache Python
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Limpar logs antigos
    if [[ -d "logs" ]]; then
        find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    fi
    
    # Limpar arquivos temporários
    rm -rf tmp/* 2>/dev/null || true
    
    log "✅ Limpeza concluída"
}

build_docker_images() {
    log "🐳 Construindo imagens Docker..."
    
    # Verificar se há mudanças que requerem rebuild
    if [[ -f ".docker-build-timestamp" ]]; then
        local last_build=$(cat .docker-build-timestamp)
        local dockerfile_modified=0
        local requirements_modified=0
        
        # Verificar modificação do Dockerfile de forma segura
        if [[ -f "Dockerfile" ]]; then
            dockerfile_modified=$(stat -c %Y Dockerfile 2>/dev/null || stat -f %m Dockerfile 2>/dev/null || echo 0)
        fi
        
        # Verificar modificação do requirements.txt de forma segura
        if [[ -f "requirements.txt" ]]; then
            requirements_modified=$(stat -c %Y requirements.txt 2>/dev/null || stat -f %m requirements.txt 2>/dev/null || echo 0)
        fi
        
        if [[ $dockerfile_modified -gt $last_build ]] || [[ $requirements_modified -gt $last_build ]]; then
            log_info "   Detectadas mudanças, reconstruindo imagens..."
            $DOCKER_COMPOSE_CMD build --no-cache
        else
            log_info "   Imagens atualizadas, usando cache..."
            $DOCKER_COMPOSE_CMD build
        fi
    else
        log_info "   Primeira execução, construindo todas as imagens..."
        $DOCKER_COMPOSE_CMD build
    fi
    
    # Salvar timestamp do build
    date +%s > .docker-build-timestamp
    
    log "✅ Imagens Docker prontas"
}

# Inicializar banco de dados
initialize_database() {
    log "🗄️  Inicializando banco de dados..."
    
    # Tentar limpar redes problemáticas primeiro
    log_info "   Limpando redes Docker conflitantes..."
    docker network prune -f &>/dev/null || true
    
    # Iniciar apenas os serviços de banco
    log_info "   Iniciando PostgreSQL e Redis..."
    
    # Tentar iniciar com retry em caso de erro de rede
    local max_network_attempts=3
    local network_attempt=1
    
    while [[ $network_attempt -le $max_network_attempts ]]; do
        if $DOCKER_COMPOSE_CMD up -d postgres redis 2>/dev/null; then
            break
        fi
        
        log_warning "   Tentativa $network_attempt/$max_network_attempts - erro de rede, limpando e tentando novamente..."
        $DOCKER_COMPOSE_CMD down &>/dev/null || true
        docker network prune -f &>/dev/null || true
        sleep 3
        ((network_attempt++))
    done
    
    if [[ $network_attempt -gt $max_network_attempts ]]; then
        log_error "❌ Falha ao criar redes Docker após $max_network_attempts tentativas"
        log_error "   Execute 'docker system prune -f' e tente novamente"
        exit 1
    fi
    
    # Aguardar banco ficar disponível
    log_info "   Aguardando PostgreSQL ficar disponível..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if $DOCKER_COMPOSE_CMD exec -T postgres pg_isready -U ${DB_USER:-vancimj} &>/dev/null; then
            break
        fi
        
        log_info "   Tentativa $attempt/$max_attempts - aguardando PostgreSQL..."
        sleep 2
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "❌ PostgreSQL não ficou disponível após $max_attempts tentativas"
        log_error "   Verifique os logs: $DOCKER_COMPOSE_CMD logs postgres"
        exit 1
    fi
    
    # Executar migrações
    log_info "   Executando migrações do banco..."
    if ! $DOCKER_COMPOSE_CMD run --rm app python -m alembic upgrade head; then
        log_warning "   ⚠️  Migrações falharam, continuando sem elas..."
    fi
    
    log "✅ Banco de dados inicializado"
}

# Iniciar serviços principais
start_main_services() {
    log "🚀 Iniciando serviços principais..."
    
    # Iniciar todos os serviços
    log_info "   Iniciando todos os containers..."
    $DOCKER_COMPOSE_CMD up -d
    
    # Aguardar serviços ficarem prontos
    log_info "   Aguardando serviços ficarem prontos..."
    sleep 10
    
    # Verificar saúde dos serviços
    local services=("app" "dashboard" "nginx")
    for service in "${services[@]}"; do
        if $DOCKER_COMPOSE_CMD ps | grep -q "${service}.*Up"; then
            log_info "   ✅ $service está rodando"
        else
            log_warning "   ⚠️  $service pode estar com problemas"
        fi
    done
    
    log "✅ Serviços principais iniciados"
}

# Executar testes de saúde
run_health_checks() {
    log "🏥 Executando verificações de saúde..."
    
    local base_url="http://localhost:8000"
    local dashboard_url="http://localhost:8501"
    local max_attempts=20
    
    # Testar API principal
    log_info "   Testando API principal ($base_url)..."
    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -o /dev/null -w "%{http_code}" "$base_url/health" | grep -q "200"; then
            log_info "   ✅ API principal respondendo"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_warning "   ⚠️  API principal não respondeu após $max_attempts tentativas"
        else
            log_info "   Tentativa $attempt/$max_attempts - aguardando API..."
            sleep 3
        fi
        ((attempt++))
    done
    
    # Testar Dashboard
    log_info "   Testando Dashboard ($dashboard_url)..."
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -o /dev/null -w "%{http_code}" "$dashboard_url" | grep -q "200"; then
            log_info "   ✅ Dashboard respondendo"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_warning "   ⚠️  Dashboard não respondeu após $max_attempts tentativas"
        else
            log_info "   Tentativa $attempt/$max_attempts - aguardando Dashboard..."
            sleep 3
        fi
        ((attempt++))
    done
    
    log "✅ Verificações de saúde concluídas"
}

# Configurar monitoramento
setup_monitoring() {
    log "📊 Configurando monitoramento..."
    
    # Verificar se Prometheus está configurado
    if [[ -f "prometheus/prometheus.yml" ]]; then
        log_info "   Iniciando Prometheus..."
        $DOCKER_COMPOSE_CMD up -d prometheus 2>/dev/null || log_warning "   ⚠️  Prometheus não configurado"
    fi
    
    # Verificar se Grafana está configurado
    if [[ -f "grafana/grafana.ini" ]]; then
        log_info "   Iniciando Grafana..."
        $DOCKER_COMPOSE_CMD up -d grafana 2>/dev/null || log_warning "   ⚠️  Grafana não configurado"
    fi
    
    log "✅ Monitoramento configurado"
}

# Exibir informações de acesso
show_access_info() {
    local local_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
    
    echo ""
    echo -e "${WHITE}=========================================================================${NC}"
    echo -e "${GREEN}                    🎉 WHATSAPP AGENT INICIADO COM SUCESSO! 🎉${NC}"
    echo -e "${WHITE}=========================================================================${NC}"
    echo ""
    echo -e "${CYAN}📱 SERVIÇOS DISPONÍVEIS:${NC}"
    echo ""
    echo -e "   🔗 ${YELLOW}API Principal:${NC}     http://localhost:8000"
    echo -e "   🔗 ${YELLOW}API Principal (Rede):${NC} http://$local_ip:8000"
    echo -e "   📊 ${YELLOW}Dashboard Admin:${NC}   http://localhost:8501"
    echo -e "   📊 ${YELLOW}Dashboard (Rede):${NC}  http://$local_ip:8501"
    echo -e "   📚 ${YELLOW}Documentação API:${NC}  http://localhost:8000/docs"
    echo -e "   🔐 ${YELLOW}Webhook WhatsApp:${NC}  http://localhost:8000/webhook"
    echo ""
    echo -e "${CYAN}📊 MONITORAMENTO (se configurado):${NC}"
    echo -e "   📈 ${YELLOW}Prometheus:${NC}        http://localhost:9090"
    echo -e "   📉 ${YELLOW}Grafana:${NC}           http://localhost:3000"
    echo ""
    echo -e "${CYAN}🔧 COMANDOS ÚTEIS:${NC}"
    echo -e "   📋 ${YELLOW}Ver logs:${NC}          $DOCKER_COMPOSE_CMD logs -f"
    echo -e "   🔄 ${YELLOW}Reiniciar:${NC}         $DOCKER_COMPOSE_CMD restart"
    echo -e "   🛑 ${YELLOW}Parar tudo:${NC}        $DOCKER_COMPOSE_CMD down"
    echo -e "   🧹 ${YELLOW}Limpar tudo:${NC}       $DOCKER_COMPOSE_CMD down -v --remove-orphans"
    echo ""
    echo -e "${CYAN}📁 ARQUIVOS IMPORTANTES:${NC}"
    echo -e "   ⚙️  ${YELLOW}Configuração:${NC}      .env"
    echo -e "   📊 ${YELLOW}Dashboard:${NC}         dashboard_whatsapp_complete.py"
    echo -e "   📚 ${YELLOW}Documentação:${NC}      docs/DOCUMENTACAO_COMPLETA.html"
    echo -e "   🔐 ${YELLOW}Logs:${NC}              logs/"
    echo ""
    echo -e "${WHITE}=========================================================================${NC}"
    echo -e "${GREEN}                       Sistema pronto para uso! 🚀${NC}"
    echo -e "${WHITE}=========================================================================${NC}"
    echo ""
}

# Função para tratamento de sinais
cleanup_on_exit() {
    log_info "📝 Script interrompido, mantendo serviços rodando..."
    log_info "   Use '$DOCKER_COMPOSE_CMD down' para parar os serviços."
    exit 0
}

# Configurar tratamento de sinais
trap cleanup_on_exit SIGINT SIGTERM

# Função principal
main() {
    print_banner
    
    # Verificações iniciais
    check_directory
    check_dependencies
    check_env_file
    
    # Preparação
    stop_existing_services
    cleanup_temp_files
    
    # Construção e inicialização
    build_docker_images
    initialize_database
    start_main_services
    
    # Verificações finais
    run_health_checks
    setup_monitoring
    
    # Informações de acesso
    show_access_info
    
    # Manter script rodando para mostrar logs
    log "📋 Monitorando logs dos serviços (Ctrl+C para sair)..."
    $DOCKER_COMPOSE_CMD logs -f --tail=50
}

# Verificar se está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
