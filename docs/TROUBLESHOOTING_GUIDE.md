# 🔧 TROUBLESHOOTING GUIDE - WhatsApp Agent

**Data de Atualização**: 09 de agosto de 2025  
**Versão**: 1.0  
**Responsabilidade**: Equipe de Operações e Desenvolvimento

---

## 📋 ÍNDICE

- [🚨 Problemas Críticos (P0)](#-problemas-críticos-p0)
- [⚠️ Problemas Urgentes (P1)](#️-problemas-urgentes-p1)
- [🔍 Problemas Comuns (P2)](#-problemas-comuns-p2)
- [🛠️ Ferramentas de Diagnóstico](#️-ferramentas-de-diagnóstico)
- [📊 Análise de Logs](#-análise-de-logs)
- [🔄 Procedimentos de Recovery](#-procedimentos-de-recovery)
- [🎯 Testes de Validação](#-testes-de-validação)

---

## 🚨 PROBLEMAS CRÍTICOS (P0)

### Sistema Completamente Indisponível

**Sintomas**:
- Health check retorna erro 500/503
- Aplicação não responde
- Todos os containers parados

**Diagnóstico Rápido**:
```bash
# 1. Verificar status dos containers
docker-compose ps

# 2. Verificar logs imediatos
docker-compose logs --tail=50 app

# 3. Verificar recursos do sistema
df -h  # Espaço em disco
free -h  # Memória
ps aux | head -20  # Processos top
```

**Resolução**:
```bash
# OPÇÃO 1: Restart completo
docker-compose down
docker-compose up -d

# OPÇÃO 2: Se problema persistir
docker system prune -f  # Limpar recursos
docker-compose build --no-cache  # Rebuild
docker-compose up -d

# OPÇÃO 3: Rollback de emergência
./scripts/rolling_update.sh rollback
```

**Verificação Pós-Resolução**:
```bash
# Aguardar 2 minutos e testar
sleep 120
curl -f http://localhost:8000/health
./scripts/monitor_health.sh
```

**Escalação**: Se não resolver em 10 minutos, acionar Engenheiro DevOps

---

### Banco de Dados Inacessível

**Sintomas**:
- Erro "connection refused" nos logs
- Aplicação retorna 500 para operações que usam DB
- Container postgres parado ou reiniciando

**Diagnóstico**:
```bash
# 1. Status do container PostgreSQL
docker-compose ps postgres

# 2. Logs do PostgreSQL
docker-compose logs postgres --tail=100

# 3. Conectividade
docker-compose exec postgres pg_isready -U $DB_USER

# 4. Espaço em disco (causa comum)
df -h
docker system df
```

**Resolução**:
```bash
# CASO 1: Container parado
docker-compose up -d postgres
sleep 30
docker-compose exec postgres pg_isready -U $DB_USER

# CASO 2: Falta de espaço
docker system prune -f
find logs/ -name "*.log" -mtime +7 -delete
# Se ainda não há espaço, limpar backups antigos

# CASO 3: Corrupção de dados
docker-compose down postgres
docker volume ls | grep postgres
# Último recurso: restore de backup
./scripts/restore_backup.sh latest

# CASO 4: Reset do container PostgreSQL
docker-compose down postgres
docker volume rm whatsapp_postgres_data  # CUIDADO!
docker-compose up -d postgres
# Executar migrações: alembic upgrade head
```

**Verificação**:
```bash
# Testar conectividade
docker-compose exec postgres psql -U $DB_USER -c "SELECT version();"

# Testar aplicação
curl -f http://localhost:8000/health
```

---

### Webhook do WhatsApp Falhando

**Sintomas**:
- Meta reporta webhook como "failed"
- Mensagens não chegam na aplicação
- Status 500/503 no endpoint /webhook

**Diagnóstico**:
```bash
# 1. Testar endpoint webhook localmente
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[]}'

# 2. Verificar logs de webhook
grep -i webhook logs/app.log | tail -20
grep -i "POST /webhook" logs/app.log | tail -20

# 3. Verificar certificado SSL (se HTTPS)
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# 4. Testar desde externa (se possível)
curl -X POST https://yourdomain.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[]}'
```

**Resolução**:
```bash
# CASO 1: Problema de certificado SSL
# Renovar certificado Let's Encrypt
certbot renew --force-renewal
docker-compose restart nginx

# CASO 2: Aplicação com problema
docker-compose restart app
sleep 30

# CASO 3: Configuração de firewall/proxy
# Verificar se porta 80/443 está acessível
# Verificar configuração do nginx
docker-compose exec nginx nginx -t

# CASO 4: Rate limiting excessivo
# Verificar e ajustar rate limits
grep -i "rate.limit" app/config/environment_config.py
```

**Verificação**:
```bash
# Teste local
curl -f http://localhost:8000/webhook -X POST -H "Content-Type: application/json" -d '{}'

# Teste externo
# Usar ferramenta de webhook online para testar
```

---

## ⚠️ PROBLEMAS URGENTES (P1)

### Performance Degradada (Response Time > 2s)

**Sintomas**:
- SLA de response time violado
- Aplicação lenta para responder
- Alertas de performance acionados

**Diagnóstico**:
```bash
# 1. Métricas de performance atual
curl -s http://localhost:8000/production/metrics/performance

# 2. Recursos do sistema
top -bn1 | head -20
iostat 1 5  # I/O disk
netstat -i  # Network

# 3. Performance do banco
docker-compose exec postgres psql -U $DB_USER -c "
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;"

# 4. Logs de performance
grep -i "slow\|timeout\|took" logs/performance.log | tail -20
```

**Resolução**:
```bash
# AÇÃO 1: Reiniciar aplicação (quick fix)
docker-compose restart app

# AÇÃO 2: Limpar cache Redis
docker-compose exec redis redis-cli FLUSHALL

# AÇÃO 3: Otimizar banco de dados
python scripts/run_optimizations.py

# AÇÃO 4: Aumentar recursos (se necessário)
# Editar docker-compose.yml para aumentar memory/cpu limits
docker-compose up -d --scale app=2  # Scale horizontal

# AÇÃO 5: Identificar consultas lentas
docker-compose exec postgres psql -U $DB_USER -c "
SELECT pg_stat_reset();"  # Reset estatísticas para nova medição
```

**Monitoramento Contínuo**:
```bash
# Monitorar response times
watch -n 30 'curl -s http://localhost:8000/production/metrics/performance | jq .sla_metrics.response_time'

# Monitorar recursos
watch -n 10 'docker stats --no-stream'
```

---

### Error Rate Elevada (> 5%)

**Sintomas**:
- Muitos erros 500 nos logs
- SLA de error rate violado
- Usuários reportando falhas

**Diagnóstico**:
```bash
# 1. Contagem de erros por tipo
grep -E "(ERROR|500|CRITICAL)" logs/app.log | tail -50
awk '$9 >= 500' logs/access.log | wc -l  # Nginx access log

# 2. Erros mais comuns
grep "ERROR" logs/app.log | awk '{print $NF}' | sort | uniq -c | sort -nr | head -10

# 3. Verificar dependências externas
curl -f https://api.openai.com/v1/models
curl -f https://graph.facebook.com/v17.0/me/messages

# 4. Verificar integridade da aplicação
curl -f http://localhost:8000/health
```

**Resolução**:
```bash
# CASO 1: Erro de dependência externa (OpenAI, Meta)
# Verificar se há fallbacks configurados
grep -r "fallback\|retry" app/services/

# CASO 2: Problema de código
# Verificar últimas mudanças
git log --oneline -10
# Se deploy recente, considerar rollback
./scripts/rolling_update.sh rollback

# CASO 3: Problema de configuração
./validate_configuration.py
./validate_secrets.py

# CASO 4: Sobrecarga do sistema
# Implementar circuit breaker ou rate limiting
docker-compose restart app
```

---

### Alertas de Segurança

**Sintomas**:
- Tentativas de acesso não autorizado
- Padrões suspeitos nos logs
- Alertas do sistema de monitoramento

**Diagnóstico**:
```bash
# 1. Verificar logs de segurança
grep -i "unauthorized\|forbidden\|attack\|suspicious" logs/security.log

# 2. Verificar tentativas de login
grep -i "auth\|login\|token" logs/app.log | grep -i "fail\|error"

# 3. Verificar IPs suspeitos
awk '{print $1}' logs/access.log | sort | uniq -c | sort -nr | head -20

# 4. Verificar integridade do sistema
find app/ -name "*.py" -exec md5sum {} \; > current_checksums.txt
# Comparar com checksums conhecidos
```

**Resolução Imediata**:
```bash
# 1. Bloquear IPs suspeitos (se identificados)
iptables -A INPUT -s SUSPICIOUS_IP -j DROP

# 2. Regenerar tokens/senhas se comprometidos
# Atualizar variáveis de ambiente
# Restart aplicação

# 3. Isolar sistema (último recurso)
docker-compose down  # Para tudo
# Investigar antes de religar

# 4. Notificar equipe de segurança
curl -X POST "$SECURITY_WEBHOOK" -d '{"text":"🚨 Incident detected"}'
```

---

## 🔍 PROBLEMAS COMUNS (P2)

### Logs Excessivos Enchendo Disco

**Diagnóstico**:
```bash
# Verificar uso de disco
df -h
du -sh logs/*

# Identificar logs grandes
find logs/ -size +100M -exec ls -lh {} \;
```

**Resolução**:
```bash
# Limpeza imediata
find logs/ -name "*.log" -mtime +7 -delete
find logs/ -name "*.log.*" -mtime +3 -delete

# Configurar rotação de logs
logrotate -f /etc/logrotate.conf

# Ajustar nível de log (se necessário)
# Editar LOG_LEVEL no .env para WARNING ou ERROR
```

---

### Cache Redis Cheio

**Sintomas**:
- Erros de memória no Redis
- Performance degradada

**Diagnóstico e Resolução**:
```bash
# Verificar uso de memória do Redis
docker-compose exec redis redis-cli INFO memory

# Limpar cache se necessário
docker-compose exec redis redis-cli FLUSHDB

# Configurar TTL para chaves (se não configurado)
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

### Dependências Externas Indisponíveis

**OpenAI API Indisponível**:
```bash
# Testar conectividade
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Verificar logs de erro
grep -i "openai\|ai.*error" logs/app.log

# Implementar fallback manual (se necessário)
# Configurar resposta padrão
```

**Meta WhatsApp API com Problemas**:
```bash
# Testar API
curl -H "Authorization: Bearer $META_ACCESS_TOKEN" \
     "https://graph.facebook.com/v17.0/$PHONE_NUMBER_ID"

# Verificar status oficial
# https://developers.facebook.com/status/
```

---

## 🛠️ FERRAMENTAS DE DIAGNÓSTICO

### Scripts de Diagnóstico Personalizados

**Diagnóstico Completo**:
```bash
#!/bin/bash
# diagnose_system.sh

echo "🔍 DIAGNÓSTICO COMPLETO DO SISTEMA"
echo "================================="

echo "📊 STATUS DOS CONTAINERS:"
docker-compose ps

echo "🏥 HEALTH CHECKS:"
curl -s http://localhost:8000/health | jq .

echo "📈 MÉTRICAS ATUAIS:"
curl -s http://localhost:8000/production/metrics/performance | jq .

echo "💾 RECURSOS DO SISTEMA:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')"
echo "RAM: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "DISK: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"

echo "🔥 TOP PROCESSOS:"
ps aux --sort=-%cpu | head -10

echo "📋 ÚLTIMOS ERROS:"
tail -20 logs/errors.log 2>/dev/null || echo "Sem logs de erro"

echo "🚨 ALERTAS ATIVOS:"
curl -s http://localhost:8000/production/alerts/active | jq .
```

### Performance Profiling

**Script de Análise de Performance**:
```bash
#!/bin/bash
# performance_analysis.sh

echo "⚡ ANÁLISE DE PERFORMANCE"
echo "========================"

# 1. Response times
echo "📊 RESPONSE TIMES (últimas 100 requisições):"
tail -100 logs/access.log | awk '{print $10}' | sort -n | awk '
  {
    a[NR] = $1
  }
  END {
    print "Min: " a[1] "ms"
    print "Avg: " (a[1] + a[NR]) / 2 "ms"
    print "Max: " a[NR] "ms"
    print "P95: " a[int(NR * 0.95)] "ms"
  }'

# 2. Endpoint mais lentos
echo "🐌 ENDPOINTS MAIS LENTOS:"
awk '$10 > 1000 {print $7, $10 "ms"}' logs/access.log | sort | uniq -c | sort -nr | head -10

# 3. Padrões de erro
echo "❌ PADRÕES DE ERRO:"
grep "ERROR" logs/app.log | awk '{print $5}' | sort | uniq -c | sort -nr | head -10
```

---

## 📊 ANÁLISE DE LOGS

### Estrutura de Logs

**Localização**: `/home/vancim/whats_agent/logs/`

```
logs/
├── app.log              # Log principal da aplicação
├── errors.log           # Apenas erros críticos
├── security.log         # Eventos de segurança
├── performance.log      # Métricas de performance
├── access.log           # Logs de acesso (nginx)
├── business_metrics/    # Métricas de negócio
└── alerts/             # Histórico de alertas
```

### Comandos Úteis para Análise

**Erros por Severidade**:
```bash
# Contar erros por tipo
grep -c "ERROR" logs/app.log
grep -c "CRITICAL" logs/app.log
grep -c "WARNING" logs/app.log

# Últimos erros críticos
grep "CRITICAL" logs/app.log | tail -10
```

**Performance Analysis**:
```bash
# Response times acima de 1s
grep "took.*[1-9][0-9]\{3\}ms" logs/performance.log

# Endpoints mais chamados
awk '{print $7}' logs/access.log | sort | uniq -c | sort -nr | head -20

# Erros por endpoint
awk '$9 >= 400 {print $7, $9}' logs/access.log | sort | uniq -c | sort -nr
```

**Análise de Padrões**:
```bash
# Atividade por hora
awk '{print $4}' logs/access.log | cut -d':' -f2 | sort | uniq -c

# IPs mais ativos
awk '{print $1}' logs/access.log | sort | uniq -c | sort -nr | head -20

# User agents suspeitos
awk -F'"' '{print $6}' logs/access.log | sort | uniq -c | sort -nr | head -10
```

### Alertas em Logs

**Palavras-chave para Monitorar**:
- `CRITICAL`, `ERROR`, `FATAL`
- `timeout`, `connection refused`, `out of memory`
- `unauthorized`, `forbidden`, `attack`
- `slow query`, `deadlock`, `corruption`

**Comando de Monitoramento Contínuo**:
```bash
# Monitor de logs em tempo real
tail -f logs/app.log | grep --color -E "(ERROR|CRITICAL|WARN)"

# Alertas automáticos
tail -f logs/app.log | while read line; do
  if echo "$line" | grep -q "CRITICAL"; then
    echo "🚨 ALERTA CRÍTICO: $line"
    # Enviar notificação
  fi
done
```

---

## 🔄 PROCEDIMENTOS DE RECOVERY

### Recovery de Aplicação

**Cenário**: Aplicação travada mas containers rodando

```bash
# 1. Soft restart
docker-compose restart app
sleep 30

# 2. Verificar se voltou
curl -f http://localhost:8000/health

# 3. Se não funcionou, hard restart
docker-compose stop app
docker-compose rm -f app
docker-compose up -d app
```

### Recovery de Banco de Dados

**Cenário**: Dados corrompidos ou perdidos

```bash
# 1. Parar aplicação
docker-compose stop app

# 2. Backup atual (por precaução)
docker-compose exec postgres pg_dump -U $DB_USER $DB_NAME > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Restaurar último backup conhecido
./scripts/restore_backup.sh latest

# 4. Verificar integridade
docker-compose exec postgres psql -U $DB_USER $DB_NAME -c "SELECT count(*) FROM conversations;"

# 5. Reiniciar aplicação
docker-compose up -d app
```

### Recovery de Configuração

**Cenário**: Configurações corrompidas

```bash
# 1. Restaurar configurações do git
git checkout -- .env docker-compose.yml

# 2. Ou restaurar de backup
cp backups/automatic/config_$(date +%Y%m%d)*.tar.gz .
tar -xzf config_*.tar.gz

# 3. Validar configuração
./validate_configuration.py

# 4. Restart completo
docker-compose down
docker-compose up -d
```

### Disaster Recovery Completo

**Cenário**: Servidor completamente comprometido

```bash
# Em novo servidor:
# 1. Clonar repositório
git clone <repository> whats_agent
cd whats_agent

# 2. Restaurar configurações
# Copiar arquivos .env, certificados, etc.

# 3. Restaurar backup de dados
./scripts/restore_full_backup.sh <backup_path>

# 4. Verificar e iniciar
./validate_configuration.py
docker-compose up -d

# 5. Verificar funcionamento
./scripts/monitor_health.sh

# 6. Atualizar DNS/balanceador (se necessário)
```

---

## 🎯 TESTES DE VALIDAÇÃO

### Teste Funcional Básico

```bash
#!/bin/bash
# basic_functional_test.sh

echo "🧪 TESTE FUNCIONAL BÁSICO"
echo "========================="

# 1. Health check
echo "1. Health Check..."
if curl -f http://localhost:8000/health; then
    echo "✅ Health check OK"
else
    echo "❌ Health check FALHOU"
    exit 1
fi

# 2. Webhook test
echo "2. Webhook Test..."
if curl -f -X POST http://localhost:8000/webhook \
   -H "Content-Type: application/json" \
   -d '{"object":"whatsapp_business_account","entry":[]}'; then
    echo "✅ Webhook OK"
else
    echo "❌ Webhook FALHOU"
fi

# 3. Database connectivity
echo "3. Database Test..."
if docker-compose exec postgres pg_isready -U $DB_USER; then
    echo "✅ Database OK"
else
    echo "❌ Database FALHOU"
fi

# 4. Metrics endpoint
echo "4. Metrics Test..."
if curl -f http://localhost:8000/production/metrics/business; then
    echo "✅ Metrics OK"
else
    echo "❌ Metrics FALHOU"
fi

echo "🎉 Teste funcional concluído"
```

### Teste de Carga Simples

```bash
#!/bin/bash
# simple_load_test.sh

echo "⚡ TESTE DE CARGA SIMPLES"
echo "========================"

# Enviar 50 requisições em 10 segundos
for i in {1..50}; do
    curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" \
         http://localhost:8000/health &
    
    if [ $((i % 10)) -eq 0 ]; then
        sleep 1  # Pausa a cada 10 requisições
    fi
done

wait  # Aguardar todas as requisições

echo "✅ Teste de carga concluído"
echo "Verificar logs para analisar performance"
```

### Teste de Integração Completo

```bash
# Executar suite completa de testes
python -m pytest tests/ -v --tb=short

# Executar testes de integração específicos
python -m pytest tests/integration/ -v

# Executar validação completa do sistema
./validate_monitoring.py
```

---

## 📋 CHECKLIST DE TROUBLESHOOTING

### Quando um Problema é Reportado

- [ ] **1. Coletar Informações (2 min)**
  - [ ] Quais sintomas específicos?
  - [ ] Quando começou?
  - [ ] Usuários afetados?
  - [ ] Mudanças recentes?

- [ ] **2. Triagem Inicial (3 min)**
  - [ ] Verificar health checks
  - [ ] Verificar alertas ativos
  - [ ] Verificar recursos (CPU, RAM, Disk)
  - [ ] Verificar logs de erro

- [ ] **3. Classificar Severidade**
  - [ ] P0: Sistema completamente down
  - [ ] P1: Funcionalidade crítica afetada
  - [ ] P2: Problema menor ou intermitente

- [ ] **4. Aplicar Resolução**
  - [ ] Seguir procedimentos específicos
  - [ ] Documentar ações tomadas
  - [ ] Monitorar resultado

- [ ] **5. Verificação Pós-Resolução**
  - [ ] Confirmar que problema foi resolvido
  - [ ] Executar testes funcionais
  - [ ] Comunicar resolução

- [ ] **6. Post-Mortem (Para P0/P1)**
  - [ ] Documentar causa raiz
  - [ ] Identificar melhorias
  - [ ] Atualizar procedimentos

---

## 📞 ESCALAÇÃO

**Tempos de Resposta**:
- **P0 (Crítico)**: 5 minutos
- **P1 (Urgente)**: 30 minutos  
- **P2 (Normal)**: 4 horas

**Contatos**:
1. **Operador de Plantão**: `+55 11 99999-0001`
2. **DevOps Engineer**: `+55 11 99999-0002`
3. **Tech Lead**: `+55 11 99999-0003`

**Comunicação**:
- Slack: `#ops-incidents`
- Email: `incidents@company.com`

---

**Última Atualização**: 09/08/2025  
**Próxima Revisão**: 09/09/2025  
**Versão**: 1.0
