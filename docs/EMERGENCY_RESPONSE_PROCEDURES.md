# 🚨 EMERGENCY RESPONSE PROCEDURES - WhatsApp Agent

**Data de Atualização**: 09 de agosto de 2025  
**Versão**: 1.0  
**Responsabilidade**: Equipe de Operações, DevOps e Gerência

---

## 📋 ÍNDICE

- [🔥 Classificação de Emergências](#-classificação-de-emergências)
- [⚡ Ações Imediatas por Tipo](#-ações-imediatas-por-tipo)
- [📞 Plano de Comunicação](#-plano-de-comunicação)
- [🛡️ Procedures de Containment](#️-procedures-de-containment)
- [🔄 Recovery Procedures](#-recovery-procedures)
- [📋 Checklists de Emergência](#-checklists-de-emergência)
- [📊 Post-Incident Analysis](#-post-incident-analysis)

---

## 🔥 CLASSIFICAÇÃO DE EMERGÊNCIAS

### SEV-1 (CRÍTICO) - Resposta Imediata (< 5 min)

**Critérios**:
- Sistema completamente indisponível (>95% usuários afetados)
- Perda de dados críticos
- Violação de segurança confirmada
- Incidente de compliance (LGPD/GDPR)

**Ações Automáticas**:
- Alertas para toda equipe técnica
- Ativação do war room
- Comunicação executiva em 15 min

### SEV-2 (URGENTE) - Resposta Rápida (< 15 min)

**Critérios**:
- Funcionalidade crítica afetada (50-95% usuários)
- Performance severamente degradada
- Erro de integração com WhatsApp/Meta
- Falha parcial do sistema

**Ações Automáticas**:
- Alertas para equipe de plantão
- Escalação automática em 30 min se não resolvido

### SEV-3 (MODERADO) - Resposta Normal (< 1 hora)

**Critérios**:
- Funcionalidade menor afetada (<50% usuários)
- Performance degradada mas utilizável
- Problemas de monitoramento
- Issues não-críticos

**Ações Automáticas**:
- Notificação para operador de plantão
- Criação de ticket para acompanhamento

### SEV-4 (BAIXO) - Resposta Planejada (< 24 horas)

**Critérios**:
- Problemas menores ou cosméticos
- Melhorias de performance
- Manutenção preventiva
- Documentação

---

## ⚡ AÇÕES IMEDIATAS POR TIPO

### 🔥 SISTEMA COMPLETAMENTE DOWN (SEV-1)

**PRIMEIRA RESPOSTA (0-5 minutos)**:

```bash
# PASSO 1: Verificação Rápida (1 min)
cd /home/vancim/whats_agent
curl -f http://localhost:8000/health || echo "CONFIRMADO: Sistema DOWN"
docker-compose ps | grep -v "Up" | head -5

# PASSO 2: Restart de Emergência (2 min)
docker-compose restart app
sleep 30
curl -f http://localhost:8000/health

# PASSO 3: Se não resolver - Restart Completo (2 min)
if ! curl -f http://localhost:8000/health; then
    docker-compose down
    docker-compose up -d
    echo "RESTART COMPLETO EXECUTADO $(date)"
fi
```

**COMUNICAÇÃO IMEDIATA**:
```bash
# Notificar Slack
curl -X POST $SLACK_EMERGENCY_WEBHOOK -d '{
  "text": "🚨 SEV-1: Sistema WhatsApp Agent DOWN\nIniciando procedures de emergência\nETA: 5-10 minutos"
}'

# Notificar Status Page (se existir)
# curl -X POST $STATUS_PAGE_API -d '{"status":"major_outage","message":"Sistema em manutenção de emergência"}'
```

**ESCALAÇÃO AUTOMÁTICA (5 min)**:
- Se sistema não voltar em 5 min → Acionar DevOps Engineer
- Se não resolver em 15 min → Acionar Tech Lead
- Se não resolver em 30 min → Acionar Gerência

---

### 🔒 INCIDENTE DE SEGURANÇA (SEV-1)

**CONTAINMENT IMEDIATO (0-3 minutos)**:

```bash
# PASSO 1: Isolar Sistema Imediatamente
docker-compose down
echo "SISTEMA ISOLADO POR SEGURANÇA $(date)" >> security_incident.log

# PASSO 2: Preservar Evidências
cp -r logs/ security_incident_$(date +%Y%m%d_%H%M%S)/
docker-compose logs > security_incident_docker_$(date +%Y%m%d_%H%M%S).log

# PASSO 3: Verificar Comprometimento
find . -name "*.py" -newer logs/app.log -exec ls -la {} \;  # Arquivos modificados recentemente
netstat -tulpn | grep LISTEN  # Portas em listening
```

**COMUNICAÇÃO DE SEGURANÇA**:
```bash
# Notificar Equipe de Segurança
curl -X POST $SECURITY_TEAM_WEBHOOK -d '{
  "text": "🚨 SECURITY INCIDENT: WhatsApp Agent\nSistema ISOLADO preventivamente\nEquipe de segurança favor verificar imediatamente"
}'

# Notificar Compliance (se aplicável)
# Email automático para compliance@company.com
```

**ANÁLISE FORENSE INICIAL**:
```bash
# Verificar tentativas de acesso
grep -i "401\|403\|unauthorized" logs/security.log | tail -50

# Verificar mudanças de configuração
git diff HEAD~5 .env docker-compose.yml

# Verificar processos suspeitos
ps aux | grep -v -E "(docker|python|postgres|redis|nginx)"
```

---

### 💾 PERDA DE DADOS (SEV-1)

**IMMEDIATE DAMAGE ASSESSMENT (0-2 minutos)**:

```bash
# PASSO 1: Parar Escritas Imediatamente
docker-compose stop app  # Para prevenir mais corrupção

# PASSO 2: Verificar Integridade do Banco
docker-compose exec postgres psql -U $DB_USER $DB_NAME -c "
SELECT 
  schemaname, 
  tablename, 
  n_tup_ins, 
  n_tup_upd, 
  n_tup_del,
  last_autoanalyze
FROM pg_stat_user_tables 
ORDER BY n_tup_ins DESC;"

# PASSO 3: Verificar Backups Disponíveis
ls -la backups/automatic/ | tail -10
ls -la backups/manual/ | tail -5
```

**RECOVERY IMEDIATO**:
```bash
# OPÇÃO 1: Se dados parcialmente corrompidos
./scripts/restore_partial_backup.sh critical_tables_only

# OPÇÃO 2: Se perda completa
./scripts/restore_full_backup.sh latest

# OPÇÃO 3: Point-in-time recovery (se configurado)
./scripts/restore_pitr.sh "2025-08-09 14:30:00"
```

---

### 🌐 FALHA DE INTEGRAÇÃO WHATSAPP (SEV-2)

**DIAGNOSTIC RÁPIDO (0-3 minutos)**:

```bash
# PASSO 1: Testar Conectividade Meta API
curl -H "Authorization: Bearer $META_ACCESS_TOKEN" \
     "https://graph.facebook.com/v17.0/$PHONE_NUMBER_ID"

# PASSO 2: Verificar Webhook Status
curl -X POST http://localhost:8000/webhook \
     -H "Content-Type: application/json" \
     -d '{"object":"whatsapp_business_account","entry":[]}'

# PASSO 3: Verificar Logs de Webhook
grep -i "webhook\|whatsapp" logs/app.log | tail -20
```

**WORKAROUNDS IMEDIATOS**:
```bash
# OPÇÃO 1: Switch para Token de Backup (se configurado)
export META_ACCESS_TOKEN=$META_BACKUP_TOKEN
docker-compose restart app

# OPÇÃO 2: Ativar Modo Degradado
# Configurar sistema para aceitar mensagens sem processar IA
export FALLBACK_MODE=true
docker-compose restart app

# OPÇÃO 3: Redirecionar para Sistema de Backup
# (Se configurado) Alterar webhook URL temporariamente
```

---

### ⚡ SOBRECARGA DO SISTEMA (SEV-2)

**IMMEDIATE LOAD REDUCTION (0-2 minutos)**:

```bash
# PASSO 1: Ativar Rate Limiting Agressivo
# Editar configuração temporariamente
export RATE_LIMIT_PER_MINUTE=10  # Reduzir drasticamente
docker-compose restart app

# PASSO 2: Scale Horizontal (se possível)
docker-compose up -d --scale app=3

# PASSO 3: Ativar Circuit Breaker
export CIRCUIT_BREAKER_ENABLED=true
export CIRCUIT_BREAKER_THRESHOLD=50
docker-compose restart app
```

**MONITORING INTENSIVO**:
```bash
# Monitor CPU e Memory em tempo real
watch -n 5 'docker stats --no-stream'

# Monitor response times
watch -n 10 'curl -s http://localhost:8000/production/metrics/performance | jq .sla_metrics.response_time'

# Monitor error rate
watch -n 30 'tail -100 logs/app.log | grep ERROR | wc -l'
```

---

## 📞 PLANO DE COMUNICAÇÃO

### Canais de Emergência

**SLACK CHANNELS**:
- `#emergency-incidents` - Coordenação de incidentes
- `#whatsapp-agent-alerts` - Alertas específicos do sistema
- `#ops-team` - Equipe operacional
- `#dev-team` - Equipe de desenvolvimento

**TELEFONES DE EMERGÊNCIA**:
- **Operador de Plantão**: `+55 11 99999-0001`
- **DevOps Engineer**: `+55 11 99999-0002`
- **Tech Lead**: `+55 11 99999-0003`
- **CTO**: `+55 11 99999-0004`

**EMAIL GROUPS**:
- `emergency@company.com` - Toda equipe técnica
- `incidents@company.com` - Equipe de resposta a incidentes
- `executives@company.com` - Liderança (apenas SEV-1)

### Templates de Comunicação

**TEMPLATE: INITIAL INCIDENT NOTIFICATION**
```
🚨 INCIDENT ALERT - SEV-[1/2/3]

SYSTEM: WhatsApp Agent
STATUS: [INVESTIGATING/IDENTIFIED/MONITORING/RESOLVED]
IMPACT: [Descrever impacto nos usuários]
START TIME: [YYYY-MM-DD HH:MM UTC]
ETA: [Estimativa de resolução]

INITIAL ACTIONS TAKEN:
- [Ação 1]
- [Ação 2]

NEXT STEPS:
- [Próximo passo 1]
- [Próximo passo 2]

RESPONSIBLE: [Nome do responsável]
INCIDENT COMMANDER: [Nome]

Updates will be provided every [15/30/60] minutes.
```

**TEMPLATE: STATUS UPDATE**
```
📋 INCIDENT UPDATE - SEV-[1/2/3]

SYSTEM: WhatsApp Agent
STATUS: [UPDATE FROM PREVIOUS]
TIME: [Current timestamp]

PROGRESS UPDATE:
- [Progresso desde último update]
- [Ações completadas]
- [Resultados observados]

CURRENT ACTIONS:
- [O que está sendo feito agora]

NEXT UPDATE: [Timestamp do próximo update]
ETA: [Updated ETA if changed]
```

**TEMPLATE: INCIDENT RESOLVED**
```
✅ INCIDENT RESOLVED - SEV-[1/2/3]

SYSTEM: WhatsApp Agent
STATUS: RESOLVED
RESOLUTION TIME: [YYYY-MM-DD HH:MM UTC]
TOTAL DURATION: [X hours Y minutes]

FINAL RESOLUTION:
- [Como foi resolvido]
- [Verificações realizadas]

IMPACT SUMMARY:
- [Resumo do impacto nos usuários]
- [Número de usuários afetados]
- [Funcionalidades afetadas]

POST-MORTEM:
- Scheduled for [Date]
- Action items will be tracked in [Tool/Location]

MONITORING:
System will be monitored closely for the next [timeframe].
```

### Escalação Automática

**TEMPO 0 min**: Incidente detectado
- Alertas automáticos para equipe de plantão
- Criação de canal #incident-YYYYMMDD-HHMM

**TEMPO 5 min** (SEV-1) / **15 min** (SEV-2):
- Se não acknowledgment → Escalação para DevOps
- Notificação para Tech Lead

**TEMPO 15 min** (SEV-1) / **30 min** (SEV-2):
- Se não resolvido → Escalação para CTO
- Ativação de equipe adicional

**TEMPO 30 min** (SEV-1):
- Se não resolvido → Notificação executiva
- Consideração de acionamento de vendor support

---

## 🛡️ PROCEDURES DE CONTAINMENT

### Isolamento de Sistema

**FULL SYSTEM ISOLATION**:
```bash
#!/bin/bash
# emergency_isolation.sh

echo "🚨 INICIANDO ISOLAMENTO DE EMERGÊNCIA"
echo "Timestamp: $(date)"

# 1. Parar toda aplicação
docker-compose down

# 2. Bloquear tráfego externo (se aplicável)
# iptables -A INPUT -p tcp --dport 80 -j DROP
# iptables -A INPUT -p tcp --dport 443 -j DROP

# 3. Preservar estado atual
mkdir -p emergency_$(date +%Y%m%d_%H%M%S)
cp -r logs/ emergency_$(date +%Y%m%d_%H%M%S)/logs/
docker-compose logs > emergency_$(date +%Y%m%d_%H%M%S)/docker_logs.txt

# 4. Notificar isolamento
curl -X POST $SLACK_EMERGENCY_WEBHOOK -d '{
  "text": "🚨 SISTEMA ISOLADO - WhatsApp Agent\nTodos os serviços parados preventivamente"
}'

echo "✅ ISOLAMENTO CONCLUÍDO"
```

### Containment por Componente

**ISOLAR APENAS APLICAÇÃO**:
```bash
# Manter DB e Redis rodando, parar apenas app
docker-compose stop app nginx
# Manter infraestrutura para análise
```

**ISOLAR APENAS BANCO**:
```bash
# Se suspeita de corrupção de dados
docker-compose stop postgres
# Preservar dados para análise forense
```

**MODO SEGURO**:
```bash
# Iniciar sistema em modo somente leitura
export READ_ONLY_MODE=true
export DISABLE_WEBHOOKS=true
docker-compose up -d app
```

---

## 🔄 RECOVERY PROCEDURES

### Recovery Escalonado

**NÍVEL 1 - QUICK RECOVERY**:
```bash
#!/bin/bash
# quick_recovery.sh

echo "⚡ QUICK RECOVERY PROCEDURE"

# 1. Restart simples
docker-compose restart
sleep 60

# 2. Verificação imediata
if curl -f http://localhost:8000/health; then
    echo "✅ QUICK RECOVERY SUCCESSFUL"
    exit 0
fi

echo "❌ QUICK RECOVERY FAILED - Escalando para LEVEL 2"
exit 1
```

**NÍVEL 2 - FULL RESTART**:
```bash
#!/bin/bash
# full_restart_recovery.sh

echo "🔄 FULL RESTART RECOVERY PROCEDURE"

# 1. Parar tudo
docker-compose down

# 2. Limpeza básica
docker system prune -f

# 3. Reiniciar serviços em ordem
docker-compose up -d postgres redis
sleep 30

docker-compose up -d app
sleep 60

docker-compose up -d nginx dashboard

# 4. Verificação
if curl -f http://localhost:8000/health; then
    echo "✅ FULL RESTART RECOVERY SUCCESSFUL"
    exit 0
fi

echo "❌ FULL RESTART FAILED - Escalando para LEVEL 3"
exit 1
```

**NÍVEL 3 - BACKUP RESTORE**:
```bash
#!/bin/bash
# backup_restore_recovery.sh

echo "💾 BACKUP RESTORE RECOVERY PROCEDURE"

# 1. Parar tudo
docker-compose down

# 2. Restaurar configurações
cp backups/automatic/config_$(date +%Y%m%d)*.tar.gz .
tar -xzf config_*.tar.gz

# 3. Restaurar banco de dados
./scripts/restore_backup.sh latest

# 4. Verificar integridade
docker-compose up -d postgres
sleep 30
docker-compose exec postgres psql -U $DB_USER $DB_NAME -c "SELECT count(*) FROM conversations;"

# 5. Reiniciar aplicação
docker-compose up -d

# 6. Verificação final
sleep 120
if curl -f http://localhost:8000/health; then
    echo "✅ BACKUP RESTORE RECOVERY SUCCESSFUL"
    exit 0
fi

echo "❌ BACKUP RESTORE FAILED - ESCALAÇÃO PARA DISASTER RECOVERY"
exit 1
```

### Disaster Recovery

**FULL DISASTER RECOVERY**:
```bash
#!/bin/bash
# disaster_recovery.sh

echo "🆘 DISASTER RECOVERY PROCEDURE"
echo "Iniciando recovery completo em novo ambiente"

# Este script seria executado em uma nova máquina/ambiente

# 1. Setup inicial
git clone <repository> whats_agent_recovery
cd whats_agent_recovery

# 2. Restaurar configurações críticas
# (De backup externo ou repositório seguro)
aws s3 cp s3://backup-bucket/configs/ . --recursive

# 3. Restaurar dados
aws s3 cp s3://backup-bucket/database/latest.sql.gz .
gunzip latest.sql.gz

# 4. Setup completo
docker-compose up -d postgres redis
sleep 60
docker-compose exec -T postgres psql -U $DB_USER $DB_NAME < latest.sql

# 5. Iniciar aplicação
docker-compose up -d

# 6. Verificação e switchover
# (Atualizar DNS, load balancer, etc.)

echo "🆘 DISASTER RECOVERY COMPLETED"
echo "Verificar funcionamento antes de direcionar tráfego"
```

---

## 📋 CHECKLISTS DE EMERGÊNCIA

### ✅ CHECKLIST: INCIDENT RESPONSE (SEV-1)

**IMMEDIATE (0-5 minutes)**:
- [ ] Confirm incident severity
- [ ] Start incident war room
- [ ] Execute immediate containment
- [ ] Send initial notification
- [ ] Assign incident commander

**SHORT TERM (5-30 minutes)**:
- [ ] Complete impact assessment
- [ ] Execute recovery procedures
- [ ] Provide regular status updates
- [ ] Escalate if not resolving
- [ ] Document all actions taken

**RESOLUTION**:
- [ ] Confirm system fully operational
- [ ] Run validation tests
- [ ] Send resolution notification
- [ ] Schedule post-mortem
- [ ] Update documentation

### ✅ CHECKLIST: SECURITY INCIDENT

**IMMEDIATE**:
- [ ] Isolate affected systems
- [ ] Preserve evidence
- [ ] Notify security team
- [ ] Document initial findings
- [ ] Assess breach scope

**INVESTIGATION**:
- [ ] Perform forensic analysis
- [ ] Identify attack vectors
- [ ] Assess data compromise
- [ ] Coordinate with authorities (if needed)
- [ ] Prepare legal notifications

**RECOVERY**:
- [ ] Patch vulnerabilities
- [ ] Rotate compromised credentials
- [ ] Restore from clean backups
- [ ] Implement additional controls
- [ ] Monitor for reoccurrence

### ✅ CHECKLIST: DATA LOSS INCIDENT

**IMMEDIATE**:
- [ ] Stop all write operations
- [ ] Assess extent of data loss
- [ ] Identify last good backup
- [ ] Notify stakeholders
- [ ] Preserve corrupted data for analysis

**RECOVERY**:
- [ ] Execute backup restore
- [ ] Validate data integrity
- [ ] Test application functionality
- [ ] Communicate data recovery status
- [ ] Implement additional backup measures

---

## 📊 POST-INCIDENT ANALYSIS

### Immediate Post-Incident (Within 24 hours)

**INCIDENT SUMMARY TEMPLATE**:
```markdown
# INCIDENT POST-MORTEM: [INCIDENT-ID]

## Incident Summary
- **Date**: [YYYY-MM-DD]
- **Duration**: [Start] - [End] ([X hours Y minutes])
- **Severity**: SEV-[1/2/3]
- **Impact**: [Description of user impact]
- **Root Cause**: [Brief description]

## Timeline
| Time | Event | Action Taken | Result |
|------|-------|--------------|--------|
| HH:MM | Incident started | - | System down |
| HH:MM | Detection | Automatic alert | Team notified |
| HH:MM | Response started | [Action] | [Result] |
| HH:MM | Resolution | [Final action] | System restored |

## Root Cause Analysis
**What happened**: [Detailed description]
**Why it happened**: [Technical root cause]
**Why it wasn't detected earlier**: [Detection gaps]

## What Went Well
- [Positive aspect 1]
- [Positive aspect 2]

## What Could Be Improved
- [Improvement area 1]
- [Improvement area 2]

## Action Items
| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| [Action 1] | [Name] | [Date] | High |
| [Action 2] | [Name] | [Date] | Medium |

## Lessons Learned
- [Lesson 1]
- [Lesson 2]
```

### Follow-up Actions

**IMMEDIATE (24-48 hours)**:
- [ ] Complete post-mortem document
- [ ] Share with stakeholders
- [ ] Create action item tickets
- [ ] Update emergency procedures

**SHORT TERM (1-2 weeks)**:
- [ ] Implement high-priority fixes
- [ ] Update monitoring/alerting
- [ ] Conduct tabletop exercises
- [ ] Train team on lessons learned

**LONG TERM (1 month+)**:
- [ ] Complete all action items
- [ ] Review incident trends
- [ ] Update architecture (if needed)
- [ ] Conduct emergency drill

### Incident Metrics Tracking

**KPIs to Track**:
- **MTTD** (Mean Time To Detection)
- **MTTR** (Mean Time To Resolution)
- **MTBF** (Mean Time Between Failures)
- **Incident Count** (by severity)
- **Customer Impact** (users affected, revenue impact)

**Monthly Incident Review**:
```bash
# Generate incident report
./scripts/generate_incident_report.sh $(date +%Y-%m)

# Analyze trends
grep "SEV-" incident_log.txt | awk '{print $1}' | sort | uniq -c

# Review action item completion
./scripts/review_action_items.sh
```

---

## 🎯 EMERGENCY CONTACT MATRIX

| Role | Primary | Secondary | Escalation Time |
|------|---------|-----------|-----------------|
| **Incident Commander** | DevOps Lead | Tech Lead | Immediate |
| **Technical SME** | Senior Developer | Platform Engineer | 15 min |
| **Communications** | Engineering Manager | Product Manager | 30 min |
| **Executive** | CTO | CEO | 60 min (SEV-1 only) |
| **Legal/Compliance** | Legal Counsel | Compliance Officer | 2 hours (if needed) |

## 📱 EMERGENCY AUTOMATION

### Automated Emergency Scripts

**AUTO-RESTART ON CRITICAL FAILURE**:
```bash
#!/bin/bash
# auto_emergency_restart.sh
# Triggered by monitoring system

FAILURE_COUNT_FILE="/tmp/failure_count"
MAX_FAILURES=3

# Increment failure count
if [ -f "$FAILURE_COUNT_FILE" ]; then
    count=$(cat "$FAILURE_COUNT_FILE")
    count=$((count + 1))
else
    count=1
fi

echo $count > "$FAILURE_COUNT_FILE"

if [ $count -le $MAX_FAILURES ]; then
    echo "Auto-restart attempt $count/$MAX_FAILURES"
    docker-compose restart app
    
    # Reset count if successful
    sleep 60
    if curl -f http://localhost:8000/health; then
        rm -f "$FAILURE_COUNT_FILE"
        echo "Auto-restart successful"
    fi
else
    echo "Max auto-restart attempts reached. Manual intervention required."
    curl -X POST $SLACK_EMERGENCY_WEBHOOK -d '{
        "text": "🚨 AUTO-RESTART FAILED: Max attempts reached. Manual intervention required."
    }'
fi
```

**MONITORING HEALTH CHECK**:
```bash
#!/bin/bash
# continuous_health_monitor.sh
# Run as cron job every minute

HEALTH_URL="http://localhost:8000/health"
FAILURE_THRESHOLD=3
FAILURE_FILE="/tmp/health_failures"

if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
    # Health check passed, reset failure count
    rm -f "$FAILURE_FILE"
else
    # Health check failed
    if [ -f "$FAILURE_FILE" ]; then
        failures=$(cat "$FAILURE_FILE")
        failures=$((failures + 1))
    else
        failures=1
    fi
    
    echo $failures > "$FAILURE_FILE"
    
    if [ $failures -ge $FAILURE_THRESHOLD ]; then
        # Trigger emergency response
        ./emergency_response.sh "health_check_failure"
        rm -f "$FAILURE_FILE"
    fi
fi
```

---

**Última Atualização**: 09/08/2025  
**Próxima Revisão**: 09/09/2025  
**Versão**: 1.0

---

**IMPORTANTE**: Este documento deve ser revisado mensalmente e atualizado após cada incidente significativo. Todos os membros da equipe devem estar familiarizados com estes procedimentos.
