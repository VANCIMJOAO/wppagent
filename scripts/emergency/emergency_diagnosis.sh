#!/bin/bash
# 🚨 SCRIPT DE DIAGNÓSTICO COMPLETO DE EMERGÊNCIA
# Executa diagnóstico completo do sistema em caso de problemas

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOGS_DIR="$PROJECT_DIR/logs"
EMERGENCY_DIR="$PROJECT_DIR/emergency_$(date +%Y%m%d_%H%M%S)"

# Funções de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo
    echo "🚨 ==============================================="
    echo "🔍 DIAGNÓSTICO DE EMERGÊNCIA - WhatsApp Agent"
    echo "🚨 ==============================================="
    echo "Timestamp: $(date)"
    echo "Executado por: $(whoami)"
    echo "Diretório: $PROJECT_DIR"
    echo
}

# Função para salvar output
save_output() {
    local output_file="$EMERGENCY_DIR/$1"
    mkdir -p "$(dirname "$output_file")"
    cat > "$output_file"
}

# 1. Verificação rápida do sistema
quick_system_check() {
    log_info "VERIFICAÇÃO RÁPIDA DO SISTEMA"
    echo "----------------------------------------"
    
    # Health check básico
    echo "🏥 HEALTH CHECK:"
    if curl -f http://localhost:8000/health 2>/dev/null; then
        log_success "Sistema respondendo"
    else
        log_error "Sistema NÃO está respondendo"
    fi
    
    # Status dos containers
    echo -e "\n🐳 STATUS DOS CONTAINERS:"
    docker-compose ps | save_output "docker_status.txt"
    docker-compose ps
    
    # Recursos do sistema
    echo -e "\n💻 RECURSOS DO SISTEMA:"
    {
        echo "CPU Usage:"
        top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'
        
        echo -e "\nMemory Usage:"
        free -h
        
        echo -e "\nDisk Usage:"
        df -h
        
        echo -e "\nLoad Average:"
        uptime
    } | tee >(save_output "system_resources.txt")
    
    echo
}

# 2. Análise de logs críticos
analyze_logs() {
    log_info "ANÁLISE DE LOGS CRÍTICOS"
    echo "----------------------------------------"
    
    # Últimos erros
    echo "❌ ÚLTIMOS ERROS (50 linhas):"
    if [ -f "$LOGS_DIR/errors.log" ]; then
        tail -50 "$LOGS_DIR/errors.log" | tee >(save_output "latest_errors.txt")
    else
        log_warning "Arquivo de erros não encontrado"
    fi
    
    echo -e "\n🔥 ERROS CRÍTICOS (últimas 24h):"
    find "$LOGS_DIR" -name "*.log" -mtime -1 -exec grep -l "CRITICAL\|FATAL" {} \; | while read logfile; do
        echo "=== $logfile ==="
        grep "CRITICAL\|FATAL" "$logfile" | tail -10
    done | tee >(save_output "critical_errors.txt")
    
    echo -e "\n⚠️ WARNINGS RECENTES:"
    find "$LOGS_DIR" -name "*.log" -mtime -1 -exec grep -l "WARNING\|WARN" {} \; | while read logfile; do
        echo "=== $logfile ==="
        grep "WARNING\|WARN" "$logfile" | tail -5
    done | tee >(save_output "recent_warnings.txt")
    
    echo
}

# 3. Verificação de conectividade
check_connectivity() {
    log_info "VERIFICAÇÃO DE CONECTIVIDADE"
    echo "----------------------------------------"
    
    {
        echo "🌐 CONECTIVIDADE EXTERNA:"
        
        # Teste Meta/WhatsApp API
        echo "Meta WhatsApp API:"
        if curl -s --max-time 10 "https://graph.facebook.com/v17.0/me" -H "Authorization: Bearer $META_ACCESS_TOKEN" >/dev/null 2>&1; then
            echo "✅ Meta API: OK"
        else
            echo "❌ Meta API: FALHA"
        fi
        
        # Teste OpenAI API
        echo "OpenAI API:"
        if curl -s --max-time 10 "https://api.openai.com/v1/models" -H "Authorization: Bearer $OPENAI_API_KEY" >/dev/null 2>&1; then
            echo "✅ OpenAI API: OK"
        else
            echo "❌ OpenAI API: FALHA"
        fi
        
        # Teste conectividade geral
        echo -e "\n🔌 CONECTIVIDADE GERAL:"
        echo "Google DNS:"
        if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
            echo "✅ Internet: OK"
        else
            echo "❌ Internet: FALHA"
        fi
        
        echo -e "\n🔗 PORTAS LOCAIS:"
        netstat -tulpn | grep LISTEN | head -10
        
    } | tee >(save_output "connectivity_check.txt")
    
    echo
}

# 4. Verificação de performance
check_performance() {
    log_info "VERIFICAÇÃO DE PERFORMANCE"
    echo "----------------------------------------"
    
    {
        echo "⚡ MÉTRICAS DE PERFORMANCE:"
        
        # Response times atuais
        echo "Response Times:"
        if curl -s http://localhost:8000/production/metrics/performance 2>/dev/null | jq -r '.sla_metrics.response_time.current_value // "N/A"'; then
            echo "✅ Métricas acessíveis"
        else
            echo "❌ Métricas inacessíveis"
        fi
        
        # Docker stats
        echo -e "\nDocker Stats:"
        docker stats --no-stream
        
        # Processos top
        echo -e "\nTop Processos:"
        ps aux --sort=-%cpu | head -10
        
        # I/O stats se disponível
        if command -v iostat >/dev/null 2>&1; then
            echo -e "\nI/O Stats:"
            iostat -x 1 1
        fi
        
    } | tee >(save_output "performance_check.txt")
    
    echo
}

# 5. Verificação de banco de dados
check_database() {
    log_info "VERIFICAÇÃO DE BANCO DE DADOS"
    echo "----------------------------------------"
    
    {
        echo "💾 STATUS DO BANCO DE DADOS:"
        
        # Conectividade PostgreSQL
        if docker-compose exec -T postgres pg_isready -U ${DB_USER:-whatsapp_user} >/dev/null 2>&1; then
            echo "✅ PostgreSQL: Conectável"
            
            # Informações do banco
            echo -e "\nInformações do Banco:"
            docker-compose exec -T postgres psql -U ${DB_USER:-whatsapp_user} ${DB_NAME:-whatsapp_db} -c "
                SELECT 
                    version() as version,
                    current_database() as database,
                    current_user as user,
                    inet_server_addr() as server_ip,
                    inet_server_port() as server_port;
            " 2>/dev/null || echo "Erro ao obter informações do banco"
            
            # Estatísticas das tabelas
            echo -e "\nEstatísticas das Tabelas:"
            docker-compose exec -T postgres psql -U ${DB_USER:-whatsapp_user} ${DB_NAME:-whatsapp_db} -c "
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes
                FROM pg_stat_user_tables 
                ORDER BY n_tup_ins DESC 
                LIMIT 10;
            " 2>/dev/null || echo "Erro ao obter estatísticas"
            
        else
            echo "❌ PostgreSQL: Não conectável"
        fi
        
        # Redis
        echo -e "\n🔄 REDIS:"
        if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
            echo "✅ Redis: OK"
            echo "Informações do Redis:"
            docker-compose exec -T redis redis-cli INFO server | grep redis_version
            docker-compose exec -T redis redis-cli INFO memory | grep used_memory_human
        else
            echo "❌ Redis: Não conectável"
        fi
        
    } | tee >(save_output "database_check.txt")
    
    echo
}

# 6. Verificação de configuração
check_configuration() {
    log_info "VERIFICAÇÃO DE CONFIGURAÇÃO"
    echo "----------------------------------------"
    
    {
        echo "⚙️ CONFIGURAÇÃO DO SISTEMA:"
        
        # Variáveis de ambiente críticas
        echo "Variáveis de Ambiente:"
        echo "DB_USER: ${DB_USER:-NOT_SET}"
        echo "DB_NAME: ${DB_NAME:-NOT_SET}"
        echo "ENVIRONMENT: ${ENVIRONMENT:-NOT_SET}"
        echo "DEBUG: ${DEBUG:-NOT_SET}"
        echo "META_ACCESS_TOKEN: ${META_ACCESS_TOKEN:+SET}"
        echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
        
        # Arquivos de configuração
        echo -e "\nArquivos de Configuração:"
        for file in .env docker-compose.yml; do
            if [ -f "$PROJECT_DIR/$file" ]; then
                echo "✅ $file: Existe"
                stat "$PROJECT_DIR/$file" | grep "Modify:"
            else
                echo "❌ $file: NÃO existe"
            fi
        done
        
        # Validação de configuração
        echo -e "\nValidação de Configuração:"
        if [ -f "$PROJECT_DIR/validate_configuration.py" ]; then
            cd "$PROJECT_DIR"
            python validate_configuration.py 2>&1 | head -20
        else
            echo "Script de validação não encontrado"
        fi
        
    } | tee >(save_output "configuration_check.txt")
    
    echo
}

# 7. Verificação de segurança
check_security() {
    log_info "VERIFICAÇÃO DE SEGURANÇA"
    echo "----------------------------------------"
    
    {
        echo "🔒 VERIFICAÇÕES DE SEGURANÇA:"
        
        # Logs de segurança
        echo "Eventos de Segurança Recentes:"
        if [ -f "$LOGS_DIR/security.log" ]; then
            tail -20 "$LOGS_DIR/security.log" | grep -E "(WARN|ERROR|CRITICAL)" || echo "Nenhum evento crítico"
        else
            echo "Log de segurança não encontrado"
        fi
        
        # Tentativas de acesso suspeitas
        echo -e "\nTentativas de Acesso (últimas 100 entradas):"
        if [ -f "$LOGS_DIR/access.log" ]; then
            tail -100 "$LOGS_DIR/access.log" | awk '$9 >= 400 {print $1, $7, $9}' | sort | uniq -c | sort -nr | head -10
        elif [ -f "$LOGS_DIR/app.log" ]; then
            grep -i "401\|403\|unauthorized" "$LOGS_DIR/app.log" | tail -10
        else
            echo "Logs de acesso não encontrados"
        fi
        
        # Verificar permissões de arquivos críticos
        echo -e "\nPermissões de Arquivos Críticos:"
        for file in .env docker-compose.yml; do
            if [ -f "$PROJECT_DIR/$file" ]; then
                ls -la "$PROJECT_DIR/$file"
            fi
        done
        
    } | tee >(save_output "security_check.txt")
    
    echo
}

# 8. Coleta de informações para suporte
collect_support_info() {
    log_info "COLETANDO INFORMAÇÕES PARA SUPORTE"
    echo "----------------------------------------"
    
    # Criar diretório de emergência
    mkdir -p "$EMERGENCY_DIR"
    
    # Logs completos
    echo "📋 Copiando logs..."
    cp -r "$LOGS_DIR" "$EMERGENCY_DIR/logs_backup" 2>/dev/null || true
    
    # Configurações (sem senhas)
    echo "⚙️ Copiando configurações..."
    cp "$PROJECT_DIR/docker-compose.yml" "$EMERGENCY_DIR/" 2>/dev/null || true
    
    # Informações do sistema
    {
        echo "=== INFORMAÇÕES DO SISTEMA ==="
        echo "Data: $(date)"
        echo "Hostname: $(hostname)"
        echo "User: $(whoami)"
        echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"
        echo "Kernel: $(uname -r)"
        echo "Docker: $(docker --version)"
        echo "Docker Compose: $(docker-compose --version)"
        echo "Python: $(python3 --version)"
        echo
        echo "=== PROCESSOS DOCKER ==="
        docker ps -a
        echo
        echo "=== LOGS DO DOCKER ==="
        docker-compose logs --tail=100
        
    } > "$EMERGENCY_DIR/system_info.txt"
    
    # Criar arquivo de resumo
    {
        echo "🚨 RESUMO DE EMERGÊNCIA"
        echo "======================"
        echo "Timestamp: $(date)"
        echo "Diretório de logs: $EMERGENCY_DIR"
        echo
        echo "PROBLEMAS IDENTIFICADOS:"
        
        # Verificar health check
        if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo "❌ Sistema não responde ao health check"
        fi
        
        # Verificar containers parados
        stopped_containers=$(docker-compose ps | grep -c "Exit\|Down" || echo "0")
        if [ "$stopped_containers" -gt 0 ]; then
            echo "❌ $stopped_containers container(s) parado(s)"
        fi
        
        # Verificar erros recentes
        if [ -f "$LOGS_DIR/errors.log" ]; then
            recent_errors=$(grep -c "$(date '+%Y-%m-%d')" "$LOGS_DIR/errors.log" 2>/dev/null || echo "0")
            if [ "$recent_errors" -gt 10 ]; then
                echo "⚠️ $recent_errors erros registrados hoje"
            fi
        fi
        
        # Verificar espaço em disco
        disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
        if [ "$disk_usage" -gt 85 ]; then
            echo "⚠️ Espaço em disco: $disk_usage%"
        fi
        
        echo
        echo "PRÓXIMOS PASSOS RECOMENDADOS:"
        echo "1. Revisar logs de erro em: $EMERGENCY_DIR/latest_errors.txt"
        echo "2. Verificar recursos do sistema em: $EMERGENCY_DIR/system_resources.txt"
        echo "3. Considerar restart se necessário"
        echo "4. Escalar para DevOps se problema persistir"
        echo
        echo "CONTATOS DE EMERGÊNCIA:"
        echo "- Slack: #emergency-incidents"
        echo "- DevOps: +55 11 99999-0002"
        echo "- Tech Lead: +55 11 99999-0003"
        
    } > "$EMERGENCY_DIR/EMERGENCY_SUMMARY.txt"
    
    log_success "Informações coletadas em: $EMERGENCY_DIR"
    echo
}

# 9. Sugestões de ação
suggest_actions() {
    log_info "SUGESTÕES DE AÇÃO"
    echo "----------------------------------------"
    
    echo "🎯 AÇÕES RECOMENDADAS BASEADAS NO DIAGNÓSTICO:"
    echo
    
    # Verificar se sistema está down
    if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "🚨 SISTEMA DOWN - AÇÕES IMEDIATAS:"
        echo "1. Tentar restart rápido: docker-compose restart"
        echo "2. Se não resolver: docker-compose down && docker-compose up -d"
        echo "3. Verificar logs em: $EMERGENCY_DIR"
        echo "4. Escalar se não resolver em 10 minutos"
        echo
    fi
    
    # Verificar containers parados
    stopped_containers=$(docker-compose ps | grep -v "Up" | wc -l)
    if [ "$stopped_containers" -gt 1 ]; then  # Cabeçalho conta como 1
        echo "🐳 CONTAINERS PARADOS DETECTADOS:"
        echo "1. Verificar logs: docker-compose logs [service_name]"
        echo "2. Reiniciar serviços: docker-compose up -d"
        echo
    fi
    
    # Verificar uso de recursos
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        echo "💾 ESPAÇO EM DISCO BAIXO ($disk_usage%):"
        echo "1. Limpar logs antigos: find logs/ -name '*.log' -mtime +7 -delete"
        echo "2. Limpar docker: docker system prune -f"
        echo "3. Limpar backups antigos se necessário"
        echo
    fi
    
    # Verificar erros recentes
    if [ -f "$LOGS_DIR/errors.log" ]; then
        recent_errors=$(tail -50 "$LOGS_DIR/errors.log" | grep -c "ERROR\|CRITICAL" || echo "0")
        if [ "$recent_errors" -gt 5 ]; then
            echo "❌ MUITOS ERROS RECENTES ($recent_errors):"
            echo "1. Analisar padrões em: $EMERGENCY_DIR/latest_errors.txt"
            echo "2. Verificar últimas mudanças: git log --oneline -10"
            echo "3. Considerar rollback se deploy recente"
            echo
        fi
    fi
    
    echo "📞 ESCALAÇÃO:"
    echo "- 0-5 min: Tentativas de auto-recovery"
    echo "- 5-15 min: Acionar DevOps Engineer"
    echo "- 15-30 min: Acionar Tech Lead"
    echo "- 30+ min: Acionar CTO"
    echo
}

# Função principal
main() {
    print_header
    
    cd "$PROJECT_DIR"
    
    # Executar todas as verificações
    quick_system_check
    analyze_logs
    check_connectivity
    check_performance
    check_database
    check_configuration
    check_security
    collect_support_info
    suggest_actions
    
    # Resumo final
    echo "🎉 DIAGNÓSTICO COMPLETO"
    echo "======================="
    echo "Todas as informações foram coletadas em:"
    echo "📁 $EMERGENCY_DIR"
    echo
    echo "📋 Arquivo de resumo:"
    echo "📄 $EMERGENCY_DIR/EMERGENCY_SUMMARY.txt"
    echo
    echo "Para mais ajuda, consulte:"
    echo "📖 docs/TROUBLESHOOTING_GUIDE.md"
    echo "📖 docs/EMERGENCY_RESPONSE_PROCEDURES.md"
    echo
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
