# 📚 RUNBOOKS OPERACIONAIS - WhatsApp Agent

**Data de Atualização**: 09 de agosto de 2025  
**Versão**: 1.0  
**Responsabilidade**: Equipe de Operações

---

## 📋 ÍNDICE

- [🚀 Inicialização do Sistema](#-inicialização-do-sistema)
- [🔄 Operações Diárias](#-operações-diárias)
- [📊 Monitoramento](#-monitoramento)
- [🔧 Manutenção](#-manutenção)
- [🎯 Procedures de Backup](#-procedures-de-backup)
- [⚡ Rolling Updates](#-rolling-updates)
- [📈 Análise de Performance](#-análise-de-performance)
- [🔒 Procedimentos de Segurança](#-procedimentos-de-segurança)

---

## 🚀 INICIALIZAÇÃO DO SISTEMA

### Startup Completo (Cold Start)

**Objetivo**: Inicializar sistema completo a partir do zero

**Tempo Estimado**: 5-10 minutos

**Pré-requisitos**:
- Docker e Docker Compose instalados
- Arquivos de configuração no lugar
- Certificados SSL válidos (se aplicável)

**Procedimento**:

```bash
# 1. Navegar para diretório do projeto
cd /home/vancim/whats_agent

# 2. Verificar configurações
./validate_configuration.py

# 3. Verificar saúde do sistema antes de iniciar
docker system df  # Verificar espaço em disco
docker-compose config  # Validar docker-compose.yml

# 4. Inicializar banco de dados (se necessário)
docker-compose up -d postgres redis
sleep 30  # Aguardar inicialização do DB

# 5. Executar migrações
docker-compose exec postgres psql -U $DB_USER -c "SELECT version();"
# Se necessário: alembic upgrade head

# 6. Inicializar aplicação principal
docker-compose up -d app

# 7. Verificar health checks
sleep 60
curl -f http://localhost:8000/health || echo "FALHA: App não inicializou"

# 8. Inicializar dashboard (se configurado)
docker-compose up -d dashboard

# 9. Inicializar nginx (se configurado)
docker-compose up -d nginx

# 10. Verificação final
docker-compose ps
./scripts/monitor_health.sh
```

**Verificações Pós-Startup**:
- [ ] Todos os containers estão "Up"
- [ ] Health checks retornando 200
- [ ] Logs sem erros críticos
- [ ] Webhook respondendo a testes
- [ ] Métricas sendo coletadas

**Rollback em Caso de Falha**:
```bash
docker-compose down
docker-compose up -d postgres redis  # Apenas serviços essenciais
# Investigar logs antes de tentar novamente
```

---

### Startup Rápido (Warm Start)

**Objetivo**: Restart rápido de sistema já configurado

**Tempo Estimado**: 2-3 minutos

```bash
# 1. Restart suave
docker-compose restart

# 2. Verificação rápida
sleep 30
curl http://localhost:8000/health
./scripts/monitor_health.sh
```

---

## 🔄 OPERAÇÕES DIÁRIAS

### Checklist Matinal (9:00)

**Responsabilidade**: Operador de plantão

```bash
# 1. Status geral do sistema
cd /home/vancim/whats_agent
./scripts/monitor_health.sh

# 2. Verificar logs da noite
tail -n 100 logs/app.log | grep -i error
tail -n 50 logs/errors.log

# 3. Verificar métricas de negócio
curl -s http://localhost:8000/production/metrics/business | jq '.business_metrics'

# 4. Verificar alertas ativos
curl -s http://localhost:8000/production/alerts/active

# 5. Verificar uso de recursos
docker stats --no-stream

# 6. Verificar espaço em disco
df -h
du -sh logs/ backups/

# 7. Verificar backup automático (se falhou)
ls -la backups/automatic/ | tail -5
```

**Ações se Problemas Detectados**:
- ❌ **Health check falha**: Investigar logs → Restart se necessário
- ⚠️ **Alertas ativos**: Analisar e resolver conforme severidade
- 💾 **Espaço baixo**: Limpar logs antigos ou alertar administrador
- 🔄 **Backup falhou**: Executar backup manual

---

### Checklist Vespertino (17:00)

```bash
# 1. Relatório de métricas do dia
curl -s http://localhost:8000/production/metrics/business > daily_metrics_$(date +%Y%m%d).json

# 2. Verificar performance do dia
curl -s http://localhost:8000/production/metrics/performance

# 3. Preparar sistema para período noturno
# (Se aplicável - menor carga, manutenções programadas)

# 4. Verificar atualizações de segurança
apt list --upgradable 2>/dev/null | grep -i security || echo "Sem atualizações de segurança"
```

---

## 📊 MONITORAMENTO

### Dashboard Principal

**URL**: `http://localhost:8000/production/system/status`

**Métricas Críticas a Monitorar**:

1. **SLA Metrics**:
   - Response Time < 500ms
   - Error Rate < 1%
   - Uptime > 99.9%
   - Throughput adequado

2. **Business Metrics**:
   - Conversas iniciadas/hora
   - Taxa de resposta
   - Qualidade das respostas
   - Conversões geradas

3. **System Health**:
   - CPU < 80%
   - Memória < 85%
   - Disco < 90%
   - Network I/O

### Alertas Automáticos

**Configuração**: `app/config/environment_config.py`

**Níveis de Severidade**:
- 🔴 **CRITICAL**: Requer ação imediata (< 5 min)
- 🟡 **HIGH**: Requer ação urgente (< 30 min)
- 🟢 **LOW**: Monitorar e planejar ação

**Canais de Notificação**:
- Slack: `#whatsapp-alerts`
- Email: `ops-team@company.com`
- SMS: Para alertas críticos (opcional)

### Comandos de Monitoramento

```bash
# Status em tempo real
watch -n 30 'curl -s http://localhost:8000/health'

# Métricas contínuas
watch -n 60 'curl -s http://localhost:8000/production/metrics/business | jq ".business_metrics.conversations_started.current_period"'

# Logs em tempo real
tail -f logs/app.log | grep -E "(ERROR|WARN|CRITICAL)"

# Performance do sistema
watch -n 10 'docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
```

---

## 🔧 MANUTENÇÃO

### Manutenção Semanal

**Agendamento**: Domingos às 02:00

```bash
#!/bin/bash
# weekly_maintenance.sh

echo "🔧 Iniciando manutenção semanal $(date)"

# 1. Backup completo
./scripts/backup_full.sh

# 2. Limpeza de logs antigos
find logs/ -name "*.log" -mtime +30 -delete
find logs/ -name "*.log.*" -mtime +7 -delete

# 3. Limpeza de métricas antigas
find logs/business_metrics/ -name "*.json" -mtime +90 -delete

# 4. Limpeza de Docker
docker system prune -f
docker volume prune -f

# 5. Atualização de dependências (se habilitado)
# pip-tools compile requirements.in

# 6. Verificação de segurança
bandit -r app/ -f json -o security_check_$(date +%Y%m%d).json

# 7. Teste de health checks
./validate_monitoring.py

# 8. Relatório de manutenção
curl -s http://localhost:8000/production/system/status > maintenance_report_$(date +%Y%m%d).json

echo "✅ Manutenção semanal concluída $(date)"
```

### Manutenção Mensal

**Agendamento**: Primeiro domingo do mês às 01:00

```bash
#!/bin/bash
# monthly_maintenance.sh

echo "🗓️ Iniciando manutenção mensal $(date)"

# 1. Backup arquival (retenção longa)
./scripts/backup_archival.sh

# 2. Análise de performance
python scripts/run_optimizations.py

# 3. Atualização do sistema operacional
apt update && apt upgrade -y

# 4. Rotação de logs
logrotate /etc/logrotate.conf

# 5. Verificação de certificados SSL
openssl x509 -in /path/to/cert.pem -dates -noout

# 6. Teste de recuperação de desastre
# ./scripts/disaster_recovery_test.sh

# 7. Relatório mensal
./scripts/generate_monthly_report.sh

echo "✅ Manutenção mensal concluída $(date)"
```

---

## 🎯 PROCEDURES DE BACKUP

### Backup Automático (Diário)

**Agendamento**: Todo dia às 03:00 via cron

```bash
# Adicionar ao crontab
0 3 * * * cd /home/vancim/whats_agent && ./scripts/backup_daily.sh

# Conteúdo do backup_daily.sh
#!/bin/bash
BACKUP_DIR="/home/vancim/whats_agent/backups/automatic"
DATE=$(date +%Y%m%d_%H%M%S)

# 1. Backup do banco de dados
docker-compose exec -T postgres pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# 2. Backup de configurações
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" config/ .env docker-compose.yml

# 3. Backup de logs críticos
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/errors.log logs/security.log

# 4. Verificar integridade
gzip -t "$BACKUP_DIR/db_$DATE.sql.gz" || echo "ERRO: Backup corrompido"

# 5. Limpeza de backups antigos (manter 30 dias)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

# 6. Notificar resultado
curl -X POST "$SLACK_WEBHOOK" -d "{\"text\":\"✅ Backup diário concluído: $DATE\"}"
```

### Backup Manual

```bash
# Backup completo imediato
./scripts/backup_manual.sh

# Backup específico de dados críticos
docker-compose exec -T postgres pg_dump -U $DB_USER -t conversations -t bookings $DB_NAME > critical_data_$(date +%Y%m%d).sql
```

### Restore de Backup

```bash
# Listar backups disponíveis
ls -la backups/automatic/ | tail -10

# Restore de banco de dados
docker-compose exec -T postgres psql -U $DB_USER $DB_NAME < backup_file.sql

# Restore completo com parada de serviço
docker-compose down
# Restore DB + configs
docker-compose up -d
```

---

## ⚡ ROLLING UPDATES

### Update de Aplicação (Zero Downtime)

**Objetivo**: Atualizar código sem interrupção de serviço

```bash
# 1. Preparação
cd /home/vancim/whats_agent
git pull origin main

# 2. Verificações pré-deploy
./validate_configuration.py
docker-compose config

# 3. Rolling update
./scripts/rolling_update.sh rolling latest

# 4. Verificação pós-deploy
sleep 60
curl -f http://localhost:8000/health
./scripts/monitor_health.sh
```

### Blue-Green Deployment

**Objetivo**: Deploy com capacidade de rollback instantâneo

```bash
# 1. Deploy para ambiente green
./scripts/rolling_update.sh blue-green v1.2.0

# 2. Teste em ambiente green
curl -f http://localhost:8001/health

# 3. Switch de tráfego (automático no script)
# 4. Monitorar pós-switch
watch -n 10 'curl -s http://localhost/health'
```

### Rollback Rápido

```bash
# Em caso de problemas após deploy
./scripts/rolling_update.sh rollback

# Verificar se rollback foi bem-sucedido
curl -f http://localhost:8000/health
```

---

## 📈 ANÁLISE DE PERFORMANCE

### Coleta de Métricas

```bash
# Métricas de sistema
./scripts/performance_analysis.sh

# Métricas de aplicação
curl -s http://localhost:8000/production/metrics/performance

# Análise de logs de performance
grep "slow" logs/performance.log | tail -20
```

### Identificação de Gargalos

```bash
# Top processos por CPU
docker stats --no-stream | sort -k3 -hr

# Top consultas lentas (se PostgreSQL)
docker-compose exec postgres psql -U $DB_USER -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Análise de memória
free -h
cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable|Cached)"
```

### Otimizações Automáticas

```bash
# Executar otimizações do banco
python scripts/run_optimizations.py

# Limpeza de cache
docker-compose exec redis redis-cli FLUSHDB

# Restart otimizado (se necessário)
docker-compose restart app
```

---

## 🔒 PROCEDIMENTOS DE SEGURANÇA

### Verificações de Segurança Diárias

```bash
# 1. Verificar tentativas de acesso não autorizadas
grep -i "unauthorized\|forbidden\|401\|403" logs/security.log | tail -20

# 2. Verificar logs de autenticação
grep -i "auth\|login\|token" logs/app.log | tail -10

# 3. Verificar atualizações de segurança
apt list --upgradable | grep -i security
```

### Resposta a Incidentes de Segurança

```bash
# 1. Isolar sistema (se necessário)
# docker-compose down

# 2. Coletar evidências
cp logs/security.log incident_$(date +%Y%m%d_%H%M%S).log
docker-compose logs > docker_logs_$(date +%Y%m%d_%H%M%S).log

# 3. Notificar equipe de segurança
curl -X POST "$SECURITY_WEBHOOK" -d "{\"text\":\"🚨 Incidente de segurança detectado\"}"

# 4. Análise forense (se necessário)
# Preservar logs e dados para investigação
```

### Auditoria de Configurações

```bash
# 1. Verificar permissões de arquivos
find . -name "*.env" -exec ls -la {} \;
find . -name "*.key" -exec ls -la {} \;

# 2. Verificar configurações de segurança
./validate_secrets.py

# 3. Scan de vulnerabilidades
bandit -r app/
safety check

# 4. Verificar exposição de portas
netstat -tulpn | grep LISTEN
```

---

## 📋 CHECKLIST DE RESPONSABILIDADES

### Operador de Plantão (24/7)
- [ ] Monitorar alertas críticos
- [ ] Responder a incidentes em <5 min
- [ ] Executar procedimentos de emergência
- [ ] Documentar todas as ações

### Administrador de Sistema (Horário Comercial)
- [ ] Manutenção preventiva
- [ ] Atualizações de sistema
- [ ] Configuração de novos recursos
- [ ] Análise de performance

### Engenheiro DevOps (Sob Demanda)
- [ ] Deployments complexos
- [ ] Mudanças de infraestrutura
- [ ] Otimizações arquiteturais
- [ ] Automação de processos

---

## 📞 CONTATOS DE EMERGÊNCIA

**Escalação**:
1. Operador de Plantão: `+55 11 99999-0001`
2. Administrador de Sistema: `+55 11 99999-0002`
3. Engenheiro DevOps: `+55 11 99999-0003`
4. Gerente de TI: `+55 11 99999-0004`

**Canais de Comunicação**:
- Slack: `#ops-emergency`
- Email: `ops-team@company.com`
- WhatsApp: Grupo "Ops WhatsApp Agent"

---

**Última Atualização**: 09/08/2025  
**Próxima Revisão**: 09/09/2025  
**Versão**: 1.0
