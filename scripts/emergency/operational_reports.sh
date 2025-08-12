#!/bin/bash
# 📊 GERADOR DE RELATÓRIOS OPERACIONAIS
# Gera relatórios detalhados de operação e performance do sistema

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
REPORTS_DIR="$PROJECT_DIR/reports"
LOGS_DIR="$PROJECT_DIR/logs"

# Funções de log
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

# Criar diretório de relatórios
mkdir -p "$REPORTS_DIR"

# Função para gerar cabeçalho
generate_header() {
    local title="$1"
    local date_str=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat << EOF
# $title

**Data de Geração**: $date_str  
**Sistema**: WhatsApp Agent  
**Ambiente**: ${ENVIRONMENT:-development}  
**Servidor**: $(hostname)  
**Gerado por**: $(whoami)

---

EOF
}

# Função para obter métricas do sistema
get_system_metrics() {
    local output_file="$1"
    
    {
        echo "## 📊 MÉTRICAS DO SISTEMA"
        echo
        
        # CPU e Load
        echo "### CPU e Load Average"
        echo '```'
        echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
        echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')% user"
        echo '```'
        echo
        
        # Memória
        echo "### Uso de Memória"
        echo '```'
        free -h
        echo '```'
        echo
        
        # Disco
        echo "### Uso de Disco"
        echo '```'
        df -h | grep -E "(Filesystem|/dev/)"
        echo '```'
        echo
        
        # Processos top
        echo "### Top Processos (CPU)"
        echo '```'
        ps aux --sort=-%cpu | head -10
        echo '```'
        echo
        
        # Processos top (Memória)
        echo "### Top Processos (Memória)"
        echo '```'
        ps aux --sort=-%mem | head -10
        echo '```'
        echo
        
    } > "$output_file"
}

# Função para obter métricas de Docker
get_docker_metrics() {
    local output_file="$1"
    
    {
        echo "## 🐳 MÉTRICAS DO DOCKER"
        echo
        
        # Status dos containers
        echo "### Status dos Containers"
        echo '```'
        docker-compose ps
        echo '```'
        echo
        
        # Stats dos containers
        echo "### Estatísticas dos Containers"
        echo '```'
        docker stats --no-stream
        echo '```'
        echo
        
        # Imagens
        echo "### Imagens Docker"
        echo '```'
        docker images | head -10
        echo '```'
        echo
        
        # Volumes
        echo "### Volumes Docker"
        echo '```'
        docker volume ls
        echo '```'
        echo
        
        # Networks
        echo "### Networks Docker"
        echo '```'
        docker network ls
        echo '```'
        echo
        
    } > "$output_file"
}

# Função para analisar logs de aplicação
analyze_application_logs() {
    local output_file="$1"
    local days_back="${2:-1}"
    
    {
        echo "## 📋 ANÁLISE DE LOGS DE APLICAÇÃO"
        echo
        echo "**Período**: Últimos $days_back dia(s)"
        echo
        
        # Estatísticas gerais
        echo "### Estatísticas Gerais"
        echo '```'
        echo "Total de linhas de log:"
        find "$LOGS_DIR" -name "*.log" -mtime -$days_back -exec wc -l {} + 2>/dev/null | tail -1 || echo "0 total"
        echo
        
        # Contar por nível de log
        echo "Logs por nível:"
        for level in DEBUG INFO WARNING ERROR CRITICAL; do
            count=$(find "$LOGS_DIR" -name "*.log" -mtime -$days_back -exec grep -c "$level" {} + 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
            echo "$level: $count"
        done
        echo '```'
        echo
        
        # Erros mais comuns
        echo "### Erros Mais Comuns"
        echo '```'
        find "$LOGS_DIR" -name "*.log" -mtime -$days_back -exec grep -h "ERROR\|CRITICAL" {} \; 2>/dev/null | \
            sed 's/.*ERROR\|.*CRITICAL//' | \
            sort | uniq -c | sort -nr | head -10 || echo "Nenhum erro encontrado"
        echo '```'
        echo
        
        # Atividade por hora
        echo "### Atividade por Hora (últimas 24h)"
        echo '```'
        if [ -f "$LOGS_DIR/app.log" ]; then
            grep "$(date '+%Y-%m-%d')" "$LOGS_DIR/app.log" 2>/dev/null | \
                awk '{print $2}' | cut -d':' -f1 | sort | uniq -c | \
                awk '{printf "%02d:00 - %s logs\n", $2, $1}' || echo "Sem dados de hoje"
        else
            echo "Log de aplicação não encontrado"
        fi
        echo '```'
        echo
        
        # Últimos erros críticos
        echo "### Últimos Erros Críticos (20 mais recentes)"
        echo '```'
        find "$LOGS_DIR" -name "*.log" -mtime -$days_back -exec grep -h "CRITICAL\|FATAL" {} \; 2>/dev/null | \
            tail -20 || echo "Nenhum erro crítico encontrado"
        echo '```'
        echo
        
    } > "$output_file"
}

# Função para obter métricas de performance
get_performance_metrics() {
    local output_file="$1"
    
    {
        echo "## ⚡ MÉTRICAS DE PERFORMANCE"
        echo
        
        # Métricas do endpoint
        echo "### Métricas do Sistema de Monitoramento"
        echo '```'
        if curl -s http://localhost:8000/production/metrics/performance 2>/dev/null; then
            echo "✅ Endpoint de métricas acessível"
        else
            echo "❌ Endpoint de métricas inacessível"
        fi
        echo '```'
        echo
        
        # SLA Metrics
        echo "### SLA Metrics Atuais"
        echo '```'
        if curl -s http://localhost:8000/production/metrics/performance 2>/dev/null | jq -r '.sla_metrics // empty' 2>/dev/null; then
            echo "Dados SLA obtidos via API"
        else
            echo "SLA metrics não disponíveis via API"
        fi
        echo '```'
        echo
        
        # Response times dos logs
        echo "### Response Times dos Logs"
        echo '```'
        if [ -f "$LOGS_DIR/performance.log" ]; then
            echo "Response times (ms) - estatísticas:"
            grep "response_time" "$LOGS_DIR/performance.log" 2>/dev/null | \
                tail -100 | \
                awk -F'response_time["\:]*' '{print $2}' | \
                awk -F'[^0-9.]*' '{print $1}' | \
                sort -n | \
                awk '
                {
                    a[NR] = $1
                    sum += $1
                }
                END {
                    if (NR > 0) {
                        print "Count: " NR
                        print "Min: " a[1] "ms"
                        print "Max: " a[NR] "ms"
                        print "Avg: " sum/NR "ms"
                        print "P50: " a[int(NR*0.5)] "ms"
                        print "P95: " a[int(NR*0.95)] "ms"
                        print "P99: " a[int(NR*0.99)] "ms"
                    } else {
                        print "Sem dados de response time"
                    }
                }'
        else
            echo "Log de performance não encontrado"
        fi
        echo '```'
        echo
        
        # Throughput
        echo "### Throughput (Requisições por Minuto)"
        echo '```'
        if [ -f "$LOGS_DIR/app.log" ]; then
            echo "Últimas 60 minutos:"
            for i in {0..5}; do
                minute=$(date -d "$i minutes ago" '+%Y-%m-%d %H:%M')
                count=$(grep "$minute" "$LOGS_DIR/app.log" 2>/dev/null | wc -l)
                echo "$minute: $count requisições"
            done
        else
            echo "Log de aplicação não encontrado"
        fi
        echo '```'
        echo
        
    } > "$output_file"
}

# Função para obter métricas de negócio
get_business_metrics() {
    local output_file="$1"
    
    {
        echo "## 💼 MÉTRICAS DE NEGÓCIO"
        echo
        
        # Métricas via API
        echo "### Métricas Atuais via API"
        echo '```'
        if curl -s http://localhost:8000/production/metrics/business 2>/dev/null | jq -r '.business_metrics // empty' 2>/dev/null; then
            echo "Dados de negócio obtidos via API"
        else
            echo "Métricas de negócio não disponíveis via API"
        fi
        echo '```'
        echo
        
        # Análise de logs de negócio
        echo "### Análise dos Logs de Negócio"
        echo '```'
        if [ -d "$LOGS_DIR/business_metrics" ]; then
            echo "Arquivos de métricas encontrados:"
            ls -la "$LOGS_DIR/business_metrics/" | head -10
            echo
            
            # Últimas métricas
            echo "Últimas métricas registradas:"
            find "$LOGS_DIR/business_metrics" -name "*.json" -mtime -1 | head -5 | while read file; do
                echo "=== $(basename "$file") ==="
                tail -3 "$file" 2>/dev/null || echo "Erro ao ler arquivo"
            done
        else
            echo "Diretório de métricas de negócio não encontrado"
        fi
        echo '```'
        echo
        
        # Conversas por dia
        echo "### Atividade de Conversas (Últimos 7 dias)"
        echo '```'
        for i in {0..6}; do
            day=$(date -d "$i days ago" '+%Y-%m-%d')
            count=$(grep -r "conversation" "$LOGS_DIR" 2>/dev/null | grep "$day" | wc -l)
            echo "$day: $count eventos de conversa"
        done
        echo '```'
        echo
        
        # Mensagens processadas
        echo "### Mensagens Processadas (Últimas 24h)"
        echo '```'
        today=$(date '+%Y-%m-%d')
        message_count=$(grep -r "message.*processed\|webhook.*message" "$LOGS_DIR" 2>/dev/null | grep "$today" | wc -l)
        echo "Mensagens processadas hoje: $message_count"
        
        # Por hora
        echo "Por hora:"
        for hour in {00..23}; do
            count=$(grep -r "message.*processed\|webhook.*message" "$LOGS_DIR" 2>/dev/null | grep "$today $hour:" | wc -l)
            if [ $count -gt 0 ]; then
                echo "$hour:00 - $count mensagens"
            fi
        done
        echo '```'
        echo
        
    } > "$output_file"
}

# Função para analisar alertas
analyze_alerts() {
    local output_file="$1"
    
    {
        echo "## 🚨 ANÁLISE DE ALERTAS"
        echo
        
        # Alertas ativos
        echo "### Alertas Ativos"
        echo '```'
        if curl -s http://localhost:8000/production/alerts/active 2>/dev/null; then
            echo "Alertas obtidos via API"
        else
            echo "Endpoint de alertas não acessível"
        fi
        echo '```'
        echo
        
        # Histórico de alertas
        echo "### Histórico de Alertas (Últimos 7 dias)"
        echo '```'
        if [ -d "$LOGS_DIR/alerts" ]; then
            echo "Alertas por dia:"
            for i in {0..6}; do
                day=$(date -d "$i days ago" '+%Y-%m-%d')
                count=$(find "$LOGS_DIR/alerts" -name "*$day*" 2>/dev/null | wc -l)
                echo "$day: $count arquivos de alerta"
            done
            echo
            
            echo "Últimos 10 alertas:"
            find "$LOGS_DIR/alerts" -type f -mtime -7 | head -10 | while read file; do
                echo "=== $(basename "$file") ==="
                head -3 "$file" 2>/dev/null || echo "Erro ao ler arquivo"
            done
        else
            echo "Diretório de alertas não encontrado"
        fi
        echo '```'
        echo
        
        # Alertas por severidade
        echo "### Alertas por Severidade (Últimos 7 dias)"
        echo '```'
        for severity in CRITICAL HIGH MEDIUM LOW; do
            count=$(grep -r "$severity" "$LOGS_DIR" 2>/dev/null | grep -E "alert|alerta" | wc -l)
            echo "$severity: $count"
        done
        echo '```'
        echo
        
    } > "$output_file"
}

# Função para verificar saúde do sistema
check_system_health() {
    local output_file="$1"
    
    {
        echo "## 🏥 SAÚDE DO SISTEMA"
        echo
        
        # Health checks
        echo "### Health Checks"
        echo '```'
        echo "Sistema Principal:"
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo "✅ Health check principal: OK"
        else
            echo "❌ Health check principal: FALHA"
        fi
        
        echo
        echo "Banco de Dados:"
        if docker-compose exec -T postgres pg_isready -U ${DB_USER:-whatsapp_user} >/dev/null 2>&1; then
            echo "✅ PostgreSQL: OK"
        else
            echo "❌ PostgreSQL: FALHA"
        fi
        
        echo
        echo "Redis:"
        if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
            echo "✅ Redis: OK"
        else
            echo "❌ Redis: FALHA"
        fi
        
        echo
        echo "Webhook:"
        if curl -f -X POST http://localhost:8000/webhook -H "Content-Type: application/json" -d '{}' >/dev/null 2>&1; then
            echo "✅ Webhook: OK"
        else
            echo "❌ Webhook: FALHA"
        fi
        echo '```'
        echo
        
        # Status dos serviços
        echo "### Status dos Serviços"
        echo '```'
        docker-compose ps
        echo '```'
        echo
        
        # Uptime
        echo "### Uptime do Sistema"
        echo '```'
        echo "Sistema operacional:"
        uptime
        echo
        echo "Containers:"
        docker-compose ps | grep "Up" | awk '{print $1, $4, $5, $6}'
        echo '```'
        echo
        
        # Últimos restarts
        echo "### Últimos Restarts/Problemas"
        echo '```'
        echo "Logs de restart (últimas 48h):"
        grep -r "restart\|reboot\|down\|crash" "$LOGS_DIR" 2>/dev/null | grep -E "$(date '+%Y-%m-%d'|date -d 'yesterday' '+%Y-%m-%d')" | tail -10 || echo "Nenhum restart detectado"
        echo '```'
        echo
        
    } > "$output_file"
}

# Função para gerar recomendações
generate_recommendations() {
    local output_file="$1"
    
    {
        echo "## 🎯 RECOMENDAÇÕES E AÇÕES"
        echo
        
        # Verificar uso de recursos
        local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
        local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
        
        echo "### Recomendações de Infraestrutura"
        echo
        
        if [ "$disk_usage" -gt 85 ]; then
            echo "🔴 **URGENTE**: Espaço em disco crítico ($disk_usage%)"
            echo "- Executar limpeza de logs: \`find logs/ -name '*.log' -mtime +7 -delete\`"
            echo "- Executar limpeza do Docker: \`docker system prune -f\`"
            echo "- Considerar aumentar capacidade de disco"
            echo
        elif [ "$disk_usage" -gt 70 ]; then
            echo "🟡 **ATENÇÃO**: Espaço em disco alto ($disk_usage%)"
            echo "- Agendar limpeza de logs antigos"
            echo "- Monitorar crescimento"
            echo
        fi
        
        if [ "$mem_usage" -gt 90 ]; then
            echo "🔴 **URGENTE**: Uso de memória crítico ($mem_usage%)"
            echo "- Investigar vazamentos de memória"
            echo "- Considerar restart dos serviços"
            echo "- Avaliar upgrade de RAM"
            echo
        elif [ "$mem_usage" -gt 80 ]; then
            echo "🟡 **ATENÇÃO**: Uso de memória alto ($mem_usage%)"
            echo "- Monitorar processos que consomem mais memória"
            echo "- Considerar otimizações"
            echo
        fi
        
        # Verificar logs de erro
        local error_count=$(grep -c "ERROR\|CRITICAL" "$LOGS_DIR"/*.log 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
        
        echo "### Recomendações de Aplicação"
        echo
        
        if [ "$error_count" -gt 100 ]; then
            echo "🔴 **URGENTE**: Muitos erros detectados ($error_count)"
            echo "- Investigar causas raiz dos erros"
            echo "- Verificar logs detalhados"
            echo "- Considerar rollback se deploy recente"
            echo
        elif [ "$error_count" -gt 50 ]; then
            echo "🟡 **ATENÇÃO**: Quantidade elevada de erros ($error_count)"
            echo "- Monitorar tendência de erros"
            echo "- Investigar padrões"
            echo
        fi
        
        # Verificar health checks
        if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo "🔴 **CRÍTICO**: Sistema não responde a health checks"
            echo "- Executar diagnóstico: \`./scripts/emergency/emergency_diagnosis.sh\`"
            echo "- Considerar restart: \`./scripts/emergency/auto_recovery.sh\`"
            echo "- Escalar para equipe técnica se necessário"
            echo
        fi
        
        echo "### Recomendações de Manutenção"
        echo
        echo "📅 **Manutenção Preventiva Recomendada**:"
        echo "- Backup manual: \`./scripts/backup_manual.sh\`"
        echo "- Atualização de dependências (verificar vulnerabilidades)"
        echo "- Revisão de logs de segurança"
        echo "- Teste de procedures de recovery"
        echo
        
        echo "📊 **Monitoramento Contínuo**:"
        echo "- Configurar alertas proativos se não configurados"
        echo "- Implementar monitoramento de SLA se necessário"
        echo "- Revisar thresholds de alerta baseados no histórico"
        echo
        
    } > "$output_file"
}

# Função para gerar relatório diário
generate_daily_report() {
    local date_str=$(date '+%Y-%m-%d')
    local report_file="$REPORTS_DIR/daily_report_$date_str.md"
    
    log_info "Gerando relatório diário: $report_file"
    
    # Cabeçalho
    generate_header "RELATÓRIO OPERACIONAL DIÁRIO" > "$report_file"
    
    # Seções do relatório
    local temp_dir="/tmp/report_$$"
    mkdir -p "$temp_dir"
    
    # Gerar cada seção em paralelo
    check_system_health "$temp_dir/health.md" &
    get_system_metrics "$temp_dir/system.md" &
    get_docker_metrics "$temp_dir/docker.md" &
    analyze_application_logs "$temp_dir/logs.md" 1 &
    get_performance_metrics "$temp_dir/performance.md" &
    get_business_metrics "$temp_dir/business.md" &
    analyze_alerts "$temp_dir/alerts.md" &
    generate_recommendations "$temp_dir/recommendations.md" &
    
    # Aguardar conclusão
    wait
    
    # Combinar seções
    cat "$temp_dir/health.md" >> "$report_file"
    cat "$temp_dir/system.md" >> "$report_file"
    cat "$temp_dir/docker.md" >> "$report_file"
    cat "$temp_dir/performance.md" >> "$report_file"
    cat "$temp_dir/business.md" >> "$report_file"
    cat "$temp_dir/logs.md" >> "$report_file"
    cat "$temp_dir/alerts.md" >> "$report_file"
    cat "$temp_dir/recommendations.md" >> "$report_file"
    
    # Rodapé
    {
        echo
        echo "---"
        echo
        echo "**Relatório gerado automaticamente**  "
        echo "**Próximo relatório**: $(date -d 'tomorrow' '+%Y-%m-%d')"
        echo "**Para mais informações**: \`./scripts/emergency/operational_reports.sh --help\`"
        echo
    } >> "$report_file"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    log_success "Relatório diário gerado: $report_file"
}

# Função para gerar relatório semanal
generate_weekly_report() {
    local date_str=$(date '+%Y-W%U')
    local report_file="$REPORTS_DIR/weekly_report_$date_str.md"
    
    log_info "Gerando relatório semanal: $report_file"
    
    # Cabeçalho
    generate_header "RELATÓRIO OPERACIONAL SEMANAL" > "$report_file"
    
    # Análise da semana
    {
        echo "**Período**: $(date -d '7 days ago' '+%Y-%m-%d') a $(date '+%Y-%m-%d')"
        echo
        
    } >> "$report_file"
    
    # Seções específicas para relatório semanal
    local temp_dir="/tmp/weekly_report_$$"
    mkdir -p "$temp_dir"
    
    check_system_health "$temp_dir/health.md" &
    analyze_application_logs "$temp_dir/logs.md" 7 &
    get_performance_metrics "$temp_dir/performance.md" &
    get_business_metrics "$temp_dir/business.md" &
    analyze_alerts "$temp_dir/alerts.md" &
    
    wait
    
    # Adicionar análise de tendências
    {
        echo "## 📈 ANÁLISE DE TENDÊNCIAS (7 dias)"
        echo
        echo "### Atividade Diária"
        echo '```'
        for i in {6..0}; do
            day=$(date -d "$i days ago" '+%Y-%m-%d')
            log_count=$(find "$LOGS_DIR" -name "*.log" -exec grep -l "$day" {} \; 2>/dev/null | wc -l)
            echo "$day: $log_count arquivos com atividade"
        done
        echo '```'
        echo
        
        echo "### Comparação com Semana Anterior"
        echo '```'
        current_errors=$(find "$LOGS_DIR" -name "*.log" -mtime -7 -exec grep -c "ERROR" {} + 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
        previous_errors=$(find "$LOGS_DIR" -name "*.log" -mtime -14 -not -mtime -7 -exec grep -c "ERROR" {} + 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
        
        echo "Erros esta semana: $current_errors"
        echo "Erros semana anterior: $previous_errors"
        
        if [ "$current_errors" -gt "$previous_errors" ]; then
            echo "Tendência: ⬆️ Aumento de $(($current_errors - $previous_errors)) erros"
        elif [ "$current_errors" -lt "$previous_errors" ]; then
            echo "Tendência: ⬇️ Redução de $(($previous_errors - $current_errors)) erros"
        else
            echo "Tendência: ➡️ Estável"
        fi
        echo '```'
        echo
        
    } >> "$report_file"
    
    # Combinar seções
    cat "$temp_dir/health.md" >> "$report_file"
    cat "$temp_dir/performance.md" >> "$report_file"
    cat "$temp_dir/business.md" >> "$report_file"
    cat "$temp_dir/logs.md" >> "$report_file"
    cat "$temp_dir/alerts.md" >> "$report_file"
    
    # Recomendações específicas para semana
    {
        echo "## 🎯 PLANO PARA PRÓXIMA SEMANA"
        echo
        echo "### Ações Prioritárias"
        echo "- [ ] Revisar e aplicar patches de segurança"
        echo "- [ ] Executar backup completo"
        echo "- [ ] Analisar tendências de performance"
        echo "- [ ] Otimizar consultas lentas (se identificadas)"
        echo
        echo "### Monitoramento Intensificado"
        echo "- [ ] Acompanhar métricas de error rate"
        echo "- [ ] Verificar crescimento de logs"
        echo "- [ ] Monitorar uso de recursos"
        echo
        
    } >> "$report_file"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    log_success "Relatório semanal gerado: $report_file"
}

# Função para gerar relatório de emergência
generate_emergency_report() {
    local incident_id="${1:-emergency_$(date +%Y%m%d_%H%M%S)}"
    local report_file="$REPORTS_DIR/emergency_report_$incident_id.md"
    
    log_info "Gerando relatório de emergência: $report_file"
    
    # Cabeçalho
    generate_header "RELATÓRIO DE EMERGÊNCIA - $incident_id" > "$report_file"
    
    # Informações críticas
    {
        echo "🚨 **SITUAÇÃO DE EMERGÊNCIA DETECTADA**"
        echo
        echo "**Incident ID**: $incident_id"
        echo "**Timestamp**: $(date)"
        echo "**Severidade**: CRÍTICA"
        echo
        
    } >> "$report_file"
    
    # Executar diagnóstico completo
    local temp_dir="/tmp/emergency_report_$$"
    mkdir -p "$temp_dir"
    
    # Diagnóstico rápido
    check_system_health "$temp_dir/health.md"
    get_system_metrics "$temp_dir/system.md"
    get_docker_metrics "$temp_dir/docker.md"
    analyze_application_logs "$temp_dir/logs.md" 1
    
    # Combinar
    cat "$temp_dir/health.md" >> "$report_file"
    cat "$temp_dir/system.md" >> "$report_file"
    cat "$temp_dir/docker.md" >> "$report_file"
    cat "$temp_dir/logs.md" >> "$report_file"
    
    # Ações recomendadas de emergência
    {
        echo "## 🆘 AÇÕES IMEDIATAS RECOMENDADAS"
        echo
        echo "### Verificações Prioritárias"
        echo "1. Executar diagnóstico completo: \`./scripts/emergency/emergency_diagnosis.sh\`"
        echo "2. Tentar recovery automático: \`./scripts/emergency/auto_recovery.sh\`"
        echo "3. Verificar logs de erro: \`tail -100 logs/errors.log\`"
        echo
        echo "### Escalação"
        echo "- **Imediato**: Notificar equipe de plantão"
        echo "- **5 min**: Acionar DevOps Engineer"
        echo "- **15 min**: Acionar Tech Lead"
        echo "- **30 min**: Acionar CTO"
        echo
        echo "### Contatos de Emergência"
        echo "- Slack: #emergency-incidents"
        echo "- DevOps: +55 11 99999-0002"
        echo "- Tech Lead: +55 11 99999-0003"
        echo
        
    } >> "$report_file"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    log_success "Relatório de emergência gerado: $report_file"
    
    # Notificar geração do relatório
    log_warning "⚠️ RELATÓRIO DE EMERGÊNCIA DISPONÍVEL EM: $report_file"
}

# Função para exibir ajuda
show_help() {
    echo "📊 GERADOR DE RELATÓRIOS OPERACIONAIS - WhatsApp Agent"
    echo
    echo "Uso: $0 [comando] [opções]"
    echo
    echo "Comandos:"
    echo "  daily       - Gera relatório operacional diário (padrão)"
    echo "  weekly      - Gera relatório operacional semanal"
    echo "  emergency   - Gera relatório de emergência"
    echo "  custom      - Gera relatório customizado"
    echo "  list        - Lista relatórios existentes"
    echo "  cleanup     - Remove relatórios antigos"
    echo "  help        - Exibe esta ajuda"
    echo
    echo "Opções:"
    echo "  --incident-id ID    - ID do incidente (para emergency)"
    echo "  --days N           - Número de dias para análise"
    echo "  --output FILE      - Arquivo de saída específico"
    echo
    echo "Exemplos:"
    echo "  $0 daily                           # Relatório diário"
    echo "  $0 weekly                          # Relatório semanal"
    echo "  $0 emergency --incident-id INC-001 # Relatório de emergência"
    echo "  $0 list                            # Listar relatórios"
    echo
    echo "Localização dos relatórios: $REPORTS_DIR"
}

# Função para listar relatórios
list_reports() {
    log_info "Relatórios disponíveis em: $REPORTS_DIR"
    
    if [ -d "$REPORTS_DIR" ] && [ "$(ls -A "$REPORTS_DIR")" ]; then
        echo
        echo "📋 Relatórios existentes:"
        ls -la "$REPORTS_DIR"/*.md 2>/dev/null | while read line; do
            echo "  $line"
        done
        
        echo
        echo "📊 Estatísticas:"
        echo "  Total de relatórios: $(find "$REPORTS_DIR" -name "*.md" 2>/dev/null | wc -l)"
        echo "  Espaço utilizado: $(du -sh "$REPORTS_DIR" 2>/dev/null | cut -f1)"
        echo "  Último relatório: $(ls -t "$REPORTS_DIR"/*.md 2>/dev/null | head -1 | xargs basename)"
    else
        log_warning "Nenhum relatório encontrado"
    fi
}

# Função para limpeza de relatórios antigos
cleanup_reports() {
    local days_to_keep="${1:-30}"
    
    log_info "Removendo relatórios mais antigos que $days_to_keep dias..."
    
    local removed_count=0
    find "$REPORTS_DIR" -name "*.md" -mtime +$days_to_keep | while read file; do
        rm -f "$file"
        removed_count=$((removed_count + 1))
        log_info "Removido: $(basename "$file")"
    done
    
    if [ $removed_count -gt 0 ]; then
        log_success "Removidos $removed_count relatórios antigos"
    else
        log_info "Nenhum relatório antigo para remover"
    fi
}

# Função principal
main() {
    local command="${1:-daily}"
    shift || true
    
    # Criar diretório de relatórios
    mkdir -p "$REPORTS_DIR"
    
    # Ir para diretório do projeto
    cd "$PROJECT_DIR"
    
    # Processar comando
    case "$command" in
        "daily")
            generate_daily_report
            ;;
        "weekly")
            generate_weekly_report
            ;;
        "emergency")
            local incident_id=""
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --incident-id)
                        incident_id="$2"
                        shift 2
                        ;;
                    *)
                        shift
                        ;;
                esac
            done
            generate_emergency_report "$incident_id"
            ;;
        "list")
            list_reports
            ;;
        "cleanup")
            cleanup_reports "$@"
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
