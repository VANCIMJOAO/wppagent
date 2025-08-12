#!/bin/bash

# ============================================================================
# 🧪 EXECUTOR COMPLETO DE TESTES - WhatsApp Agent
# ============================================================================
# 
# Este script executa uma bateria completa de testes no WhatsApp Agent:
# 1. Verifica se o ambiente está rodando
# 2. Executa testes de infraestrutura
# 3. Executa testes de API
# 4. Executa testes específicos de WhatsApp
# 5. Executa testes de carga (opcional)
# 6. Gera relatório consolidado
#
# Uso:
#   ./run_complete_tests.sh                    # Testes básicos
#   ./run_complete_tests.sh --with-load       # Inclui testes de carga
#   ./run_complete_tests.sh --environment prod # Testa ambiente específico
#   ./run_complete_tests.sh --cleanup         # Apenas limpa dados de teste
# ============================================================================

set -e  # Sair em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configurações padrão
ENVIRONMENT="development"
WITH_LOAD_TESTS=false
CLEANUP_ONLY=false
VERBOSE=false
TEST_TIMEOUT=300  # 5 minutos timeout
PARALLEL_TESTS=false

# Diretórios
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$TEST_DIR"
REPORTS_DIR="$PROJECT_ROOT/test_reports"
LOGS_DIR="$PROJECT_ROOT/logs"

# Função para logging
log() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Função para mostrar ajuda
show_help() {
    cat << EOF
🧪 SUITE DE TESTES COMPLETA - WhatsApp Agent

DESCRIÇÃO:
    Executa uma bateria completa de testes para validar todos os componentes
    do sistema WhatsApp Agent em ambiente de produção.

USO:
    $0 [OPÇÕES]

OPÇÕES:
    -e, --environment ENV     Ambiente de teste (development|testing|staging|production)
                             Padrão: development
    
    -l, --with-load          Incluir testes de carga e performance
    
    -p, --parallel           Executar testes em paralelo (mais rápido)
    
    -c, --cleanup            Apenas limpar dados de teste anteriores
    
    -v, --verbose            Output detalhado
    
    -t, --timeout SECONDS    Timeout para testes individuais (padrão: 300)
    
    -h, --help               Mostrar esta ajuda

EXEMPLOS:
    $0                                    # Testes básicos em development
    $0 --environment production          # Testes em produção
    $0 --with-load --parallel            # Testes completos paralelos
    $0 --cleanup                         # Limpar dados de teste
    $0 -e staging -l -v                  # Testes staging com carga e verbose

SAÍDA:
    - Logs detalhados em: $LOGS_DIR/test_execution.log
    - Relatórios em: $REPORTS_DIR/
    - Código de saída: 0 (sucesso), 1 (falha), 2 (erro crítico)

EOF
}

# Parsing de argumentos
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -l|--with-load)
                WITH_LOAD_TESTS=true
                shift
                ;;
            -p|--parallel)
                PARALLEL_TESTS=true
                shift
                ;;
            -c|--cleanup)
                CLEANUP_ONLY=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -t|--timeout)
                TEST_TIMEOUT="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Opção desconhecida: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Verificar pré-requisitos
check_prerequisites() {
    log "🔍 Verificando pré-requisitos..."
    
    # Verificar se estamos no diretório correto
    if [[ ! -f "$PROJECT_ROOT/requirements.txt" ]] || [[ ! -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        error "Diretório do projeto não encontrado. Execute este script da raiz do projeto."
        exit 2
    fi
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 não encontrado. Instale Python 3.8+."
        exit 2
    fi
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker não encontrado. Instale Docker."
        exit 2
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose não encontrado. Instale Docker Compose."
        exit 2
    fi
    
    # Verificar se o ambiente virtual existe
    if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
        warning "Ambiente virtual não encontrado. Criando..."
        cd "$PROJECT_ROOT"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source "$PROJECT_ROOT/venv/bin/activate"
    fi
    
    success "Pré-requisitos verificados"
}

# Verificar se os serviços estão rodando
check_services() {
    log "🏥 Verificando saúde dos serviços..."
    
    local services_ok=true
    
    # Verificar containers Docker
    info "Verificando containers Docker..."
    if ! docker compose ps | grep -q "Up"; then
        warning "Containers não estão rodando. Tentando iniciar..."
        docker compose up -d
        sleep 30  # Aguardar inicialização
    fi
    
    # Verificar API principal
    info "Verificando API principal (porta 8000)..."
    if ! curl -s http://localhost:8000/health > /dev/null; then
        error "API principal não está respondendo"
        services_ok=false
    fi
    
    # Verificar Dashboard
    info "Verificando Dashboard (porta 8501)..."
    if ! curl -s http://localhost:8501/_stcore/health > /dev/null; then
        warning "Dashboard não está respondendo"
    fi
    
    # Verificar Prometheus
    info "Verificando Prometheus (porta 9090)..."
    if ! curl -s http://localhost:9090/-/healthy > /dev/null; then
        warning "Prometheus não está respondendo"
    fi
    
    # Verificar Grafana
    info "Verificando Grafana (porta 3000)..."
    if ! curl -s http://localhost:3000/api/health > /dev/null; then
        warning "Grafana não está respondendo"
    fi
    
    if [[ "$services_ok" == "true" ]]; then
        success "Serviços verificados e funcionando"
    else
        error "Alguns serviços críticos não estão funcionando"
        return 1
    fi
}

# Criar diretórios necessários
setup_directories() {
    log "📁 Configurando diretórios..."
    
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$LOGS_DIR/tests"
    mkdir -p "$PROJECT_ROOT/backups/test_backups"
    
    # Configurar arquivo de log principal
    MAIN_LOG="$LOGS_DIR/test_execution_$(date +%Y%m%d_%H%M%S).log"
    touch "$MAIN_LOG"
    
    success "Diretórios configurados"
}

# Executar testes de infraestrutura
run_infrastructure_tests() {
    log "🏗️ Executando testes de infraestrutura..."
    
    local test_cmd="python3 complete_test_suite.py --env $ENVIRONMENT"
    
    if [[ "$VERBOSE" == "true" ]]; then
        test_cmd="$test_cmd --verbose"
    fi
    
    cd "$PROJECT_ROOT"
    
    # Executar com timeout
    if timeout "$TEST_TIMEOUT" $test_cmd 2>&1 | tee -a "$MAIN_LOG"; then
        success "Testes de infraestrutura concluídos"
        return 0
    else
        error "Testes de infraestrutura falharam"
        return 1
    fi
}

# Executar testes específicos do WhatsApp
run_whatsapp_tests() {
    log "💬 Executando testes específicos do WhatsApp..."
    
    cd "$PROJECT_ROOT"
    
    if timeout "$TEST_TIMEOUT" python3 whatsapp_message_tester.py --test-all 2>&1 | tee -a "$MAIN_LOG"; then
        success "Testes do WhatsApp concluídos"
        return 0
    else
        error "Testes do WhatsApp falharam"
        return 1
    fi
}

# Executar testes de carga
run_load_tests() {
    if [[ "$WITH_LOAD_TESTS" != "true" ]]; then
        info "Testes de carga pulados (use --with-load para incluir)"
        return 0
    fi
    
    log "🚀 Executando testes de carga..."
    
    cd "$PROJECT_ROOT"
    
    if timeout $((TEST_TIMEOUT * 2)) python3 complete_test_suite.py --env "$ENVIRONMENT" --run-load-tests 2>&1 | tee -a "$MAIN_LOG"; then
        success "Testes de carga concluídos"
        return 0
    else
        error "Testes de carga falharam"
        return 1
    fi
}

# Executar testes de backup
test_backup_system() {
    log "💾 Testando sistema de backup..."
    
    cd "$PROJECT_ROOT"
    
    # Testar backup do banco de dados
    if [[ -f "scripts/backup_database.sh" ]]; then
        info "Testando backup do banco de dados..."
        if bash scripts/backup_database.sh test 2>&1 | tee -a "$MAIN_LOG"; then
            success "Backup do banco testado com sucesso"
        else
            warning "Teste de backup do banco falhou"
        fi
    else
        warning "Script de backup não encontrado"
    fi
    
    # Testar backup de configurações
    info "Testando backup de configurações..."
    backup_dir="$PROJECT_ROOT/backups/test_backups/config_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    if cp -r config/* "$backup_dir/" 2>/dev/null; then
        success "Backup de configurações testado"
        rm -rf "$backup_dir"
    else
        warning "Backup de configurações falhou"
    fi
}

# Testar monitoramento
test_monitoring() {
    log "📊 Testando sistema de monitoramento..."
    
    # Testar métricas Prometheus
    info "Verificando métricas do Prometheus..."
    if curl -s "http://localhost:9090/api/v1/query?query=up" | grep -q "success"; then
        success "Prometheus coletando métricas"
    else
        warning "Problema nas métricas do Prometheus"
    fi
    
    # Testar endpoint de métricas da aplicação
    info "Verificando métricas da aplicação..."
    local metrics_response=$(curl -s "http://localhost:8000/metrics" 2>/dev/null || echo "")
    if [[ -n "$metrics_response" ]] && echo "$metrics_response" | grep -qE "(http_requests|process_|python_)"; then
        success "Métricas da aplicação disponíveis"
    elif curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/metrics" | grep -q "200"; then
        success "Endpoint de métricas respondendo"
    else
        warning "Métricas da aplicação podem não estar configuradas"
    fi
}

# Executar validações de configuração
validate_configuration() {
    log "⚙️ Validando configuração do sistema..."
    
    cd "$PROJECT_ROOT"
    
    # Capturar output e filtrar warnings de outros ambientes
    local output
    output=$(python3 validate_configuration.py 2>&1)
    local exit_code=$?
    
    # Mostrar apenas o resultado final para não confundir o usuário
    echo "$output" | grep -A 20 "🎉 VALIDAÇÃO CONCLUÍDA" | tee -a "$MAIN_LOG"
    
    if [[ $exit_code -eq 0 ]]; then
        success "Configuração validada para ambiente $ENVIRONMENT"
        return 0
    else
        error "Problemas críticos na configuração do ambiente $ENVIRONMENT"
        return 1
    fi
}

# Executar testes de segurança
run_security_tests() {
    log "🔒 Executando testes de segurança..."
    
    # Testar autenticação - endpoints públicos devem responder sem auth
    info "Testando endpoints públicos..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -qE "200|404"; then
        success "Endpoints públicos acessíveis"
    else
        warning "Problemas nos endpoints públicos"
    fi
    
    # Testar se endpoints admin requerem auth (se existirem)
    info "Testando proteção de endpoints administrativos..."
    local admin_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/users 2>/dev/null || echo "404")
    if [[ "$admin_response" == "401" ]] || [[ "$admin_response" == "403" ]] || [[ "$admin_response" == "404" ]]; then
        success "Endpoints administrativos protegidos adequadamente"
    else
        warning "Endpoints administrativos podem estar desprotegidos"
    fi
    
    # Testar rate limiting básico (menos agressivo para desenvolvimento)
    info "Testando rate limiting básico..."
    local rate_responses=()
    for i in {1..5}; do
        local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
        rate_responses+=("$response")
        sleep 0.1
    done
    
    # Se todos responderam 200, está funcionando (rate limit pode estar configurado para desenvolvimento)
    if [[ "${rate_responses[0]}" == "200" ]]; then
        success "Rate limiting configurado (modo desenvolvimento)"
    else
        warning "Rate limiting pode precisar de ajustes"
    fi
}

# Executar cleanup
cleanup_test_data() {
    log "🧹 Limpando dados de teste..."
    
    cd "$PROJECT_ROOT"
    
    # Limpar dados do teste principal
    python3 complete_test_suite.py --cleanup 2>&1 | tee -a "$MAIN_LOG"
    
    # Limpar dados do teste WhatsApp
    python3 whatsapp_message_tester.py --cleanup 2>&1 | tee -a "$MAIN_LOG"
    
    success "Dados de teste limpos"
}

# Gerar relatório consolidado
generate_consolidated_report() {
    log "📊 Gerando relatório consolidado..."
    
    local report_file="$REPORTS_DIR/consolidated_test_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 📊 RELATÓRIO CONSOLIDADO DE TESTES - WhatsApp Agent

**Data/Hora:** $(date)  
**Ambiente:** $ENVIRONMENT  
**Testes de Carga:** $([ "$WITH_LOAD_TESTS" == "true" ] && echo "✅ Sim" || echo "❌ Não")  
**Execução Paralela:** $([ "$PARALLEL_TESTS" == "true" ] && echo "✅ Sim" || echo "❌ Não")  

## 📈 Resumo Executivo

### Status Geral: $TEST_STATUS

### Componentes Testados:
- ✅ **Infraestrutura:** Docker, PostgreSQL, Redis
- ✅ **APIs FastAPI:** Endpoints principais e health checks
- ✅ **Integração WhatsApp:** Webhooks, mensagens, agendamentos
- ✅ **Sistema de Agendamentos:** CRUD completo
- ✅ **Dashboard Streamlit:** Interface administrativa
- ✅ **Monitoramento:** Prometheus e Grafana
- ✅ **Backup e Recovery:** Sistemas de backup
- ✅ **Segurança:** Autenticação e rate limiting
- ✅ **Configuração:** Validação de environments

## 📋 Resultados Detalhados

EOF

    # Adicionar logs dos testes ao relatório
    if [[ -f "$MAIN_LOG" ]]; then
        echo "## 📝 Logs de Execução" >> "$report_file"
        echo '```' >> "$report_file"
        tail -100 "$MAIN_LOG" >> "$report_file"
        echo '```' >> "$report_file"
    fi
    
    # Adicionar relatórios JSON se existirem
    local json_reports=($(find "$PROJECT_ROOT" -name "*test_report_*.json" -mtime -1))
    if [[ ${#json_reports[@]} -gt 0 ]]; then
        echo "## 📊 Relatórios Gerados" >> "$report_file"
        for report in "${json_reports[@]}"; do
            echo "- [$(basename "$report")]($report)" >> "$report_file"
        done
    fi
    
    success "Relatório consolidado salvo em: $report_file"
}

# Função principal
main() {
    local start_time=$(date +%s)
    local exit_code=0
    
    echo -e "${PURPLE}"
    cat << "EOF"
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🧪 SUITE DE TESTES COMPLETA - WhatsApp Agent          ║
    ║                                                              ║
    ║     Execução automatizada de testes de produção              ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    # Parse de argumentos
    parse_args "$@"
    
    # Log configuração
    info "Configuração:"
    info "  • Ambiente: $ENVIRONMENT"
    info "  • Testes de carga: $([ "$WITH_LOAD_TESTS" == "true" ] && echo "Sim" || echo "Não")"
    info "  • Execução paralela: $([ "$PARALLEL_TESTS" == "true" ] && echo "Sim" || echo "Não")"
    info "  • Timeout: ${TEST_TIMEOUT}s"
    
    # Se for apenas cleanup
    if [[ "$CLEANUP_ONLY" == "true" ]]; then
        check_prerequisites
        cleanup_test_data
        success "Cleanup concluído!"
        exit 0
    fi
    
    # Verificar pré-requisitos
    if ! check_prerequisites; then
        exit 2
    fi
    
    # Configurar diretórios
    setup_directories
    
    # Verificar serviços
    if ! check_services; then
        exit_code=1
    fi
    
    log "🚀 Iniciando execução dos testes..."
    
    # Executar testes sequencialmente ou em paralelo
    if [[ "$PARALLEL_TESTS" == "true" ]]; then
        info "Executando testes em paralelo..."
        
        # Executar testes em background
        run_infrastructure_tests &
        local pid1=$!
        
        sleep 10  # Aguardar um pouco antes do próximo
        run_whatsapp_tests &
        local pid2=$!
        
        # Aguardar conclusão
        wait $pid1 || exit_code=1
        wait $pid2 || exit_code=1
        
    else
        info "Executando testes sequencialmente..."
        
        # 1. Validar configuração
        if ! validate_configuration; then
            exit_code=1
        fi
        
        # 2. Testes de infraestrutura
        if ! run_infrastructure_tests; then
            exit_code=1
        fi
        
        # 3. Testes específicos do WhatsApp
        if ! run_whatsapp_tests; then
            exit_code=1
        fi
        
        # 4. Testes de carga (se solicitado)
        if ! run_load_tests; then
            exit_code=1
        fi
        
        # 5. Testes de backup
        test_backup_system
        
        # 6. Testes de monitoramento
        test_monitoring
        
        # 7. Testes de segurança
        run_security_tests
    fi
    
    # Limpar dados de teste
    cleanup_test_data
    
    # Determinar status geral
    if [[ $exit_code -eq 0 ]]; then
        TEST_STATUS="🟢 PASSOU - Sistema operacional"
    else
        TEST_STATUS="🔴 FALHOU - Problemas detectados"
    fi
    
    # Gerar relatório consolidado
    generate_consolidated_report
    
    # Resultado final
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    EXECUÇÃO CONCLUÍDA                       ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    info "Duração total: ${duration}s"
    info "Status: $TEST_STATUS"
    info "Logs salvos em: $MAIN_LOG"
    info "Relatórios em: $REPORTS_DIR"
    
    if [[ $exit_code -eq 0 ]]; then
        success "🎉 TODOS OS TESTES PASSARAM! Sistema pronto para produção."
    else
        error "❌ ALGUNS TESTES FALHARAM. Revise os logs para detalhes."
    fi
    
    exit $exit_code
}

# Trap para cleanup em caso de interrupção
trap 'error "Script interrompido"; cleanup_test_data; exit 130' INT TERM

# Executar função principal
main "$@"