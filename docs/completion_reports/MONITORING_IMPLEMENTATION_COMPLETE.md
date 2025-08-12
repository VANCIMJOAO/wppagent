
# 🔍 GUIA DE IMPLANTAÇÃO - SISTEMA DE MONITORAMENTO
================================================

## ✅ REQUISITOS IMPLEMENTADOS

### 1. Logs de auditoria configurados ✅
- Script: `scripts/monitoring_system_complete.py`
- Logs estruturados em JSON
- Categorias: segurança, acesso, sistema, banco de dados
- Rotação automática configurada

### 2. Alertas de segurança ativos ✅
- Script: `scripts/real_time_alerts.py`
- Monitoramento em tempo real
- Notificações multi-canal (email, Slack, arquivo)
- Sistema de cooldown anti-spam

### 3. Monitoring de vulnerabilidades ✅
- Scanner de dependências Python (Safety)
- Verificação de configurações de segurança
- Scan de permissões de arquivos
- Scan de portas de rede
- Relatórios automáticos

### 4. SIEM integrado ✅
- Correlação de eventos em tempo real
- Regras de detecção configuradas
- Resposta automática a ameaças
- Buffer de eventos com retenção

## 🚀 IMPLANTAÇÃO PASSO A PASSO

### Passo 1: Configurar Sistema de Monitoramento
```bash
cd /home/vancim/whats_agent
chmod +x scripts/monitoring_system_complete.py

# Instalar dependências
pip install aiofiles psutil asyncpg cryptography safety

# Executar sistema de monitoramento
python3 scripts/monitoring_system_complete.py
```

### Passo 2: Configurar Alertas em Tempo Real
```bash
chmod +x scripts/real_time_alerts.py

# Configurar variáveis de ambiente para notificações
export ALERT_EMAIL_USER="admin@empresa.com"
export ALERT_EMAIL_PASS="senha_do_email"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."

# Executar alertas em background
nohup python3 scripts/real_time_alerts.py &
```

### Passo 3: Iniciar Dashboard Web
```bash
chmod +x scripts/monitoring_dashboard.py

# Instalar FastAPI e Uvicorn
pip install fastapi uvicorn jinja2

# Iniciar dashboard
python3 scripts/monitoring_dashboard.py
# Acessar: http://localhost:8001
```

### Passo 4: Configurar Monitoramento Contínuo
```bash
# Adicionar ao crontab para execução automática
crontab -e

# Adicionar linhas:
# Monitoramento principal a cada 5 minutos
*/5 * * * * cd /home/vancim/whats_agent && python3 scripts/monitoring_system_complete.py

# Scan de vulnerabilidades diário
0 3 * * * cd /home/vancim/whats_agent && python3 scripts/monitoring_system_complete.py --vulnerability-scan
```

## 📊 CONFIGURAÇÕES RECOMENDADAS

### Alertas de Email
```bash
export ALERT_EMAIL_USER="monitoring@empresa.com"
export ALERT_EMAIL_PASS="senha_aplicativo"
export ALERT_EMAIL_TO="admin@empresa.com,security@empresa.com"
```

### Alertas de Slack
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
```

### Thresholds de Alerta
- CPU Crítico: >95%
- CPU Warning: >85%
- Memória Crítica: >95%
- Memória Warning: >85%
- Disco Crítico: >95%
- Disco Warning: >85%

## 🔍 MONITORAMENTO E MANUTENÇÃO

### Verificar Status dos Componentes
```bash
# Status geral
python3 scripts/validate_monitoring_complete.py

# Dashboard web
curl http://localhost:8001/health

# Logs de auditoria
tail -f logs/audit/security_audit.log
tail -f logs/alerts/real_time_alerts.log
```

### Logs Importantes
- `logs/audit/security_audit.log` - Eventos de segurança
- `logs/audit/access_audit.log` - Acessos ao sistema
- `logs/alerts/real_time_alerts.log` - Alertas em tempo real
- `logs/vulnerabilities/` - Relatórios de vulnerabilidades
- `logs/siem/` - Eventos SIEM e correlações

### Comandos de Manutenção
```bash
# Limpar logs antigos (>30 dias)
find logs/ -name "*.log" -mtime +30 -delete

# Verificar espaço em disco
df -h

# Status dos serviços
ps aux | grep python3 | grep monitoring
```

## 🚨 ALERTAS CONFIGURADOS

### Sistema
- Alto uso de CPU (>85%)
- Alto uso de memória (>85%)
- Alto uso de disco (>85%)
- Serviços offline

### Segurança
- Tentativas de login falhadas
- Modificações em arquivos críticos
- Certificados SSL expirando
- Atividade de rede suspeita

### Aplicação
- Erros críticos nos logs
- APIs com problemas
- Banco de dados inacessível
- Tempo de resposta alto

## 📞 SUPORTE E TROUBLESHOOTING

### Logs de Erro
```bash
# Verificar erros do sistema de monitoramento
tail -f logs/monitoring_audit.log | grep ERROR

# Verificar alertas ativos
cat logs/alerts/active_alerts.json

# Verificar último scan de vulnerabilidades
ls -la logs/vulnerabilities/ | tail -1
```

### Reiniciar Componentes
```bash
# Reiniciar alertas em tempo real
pkill -f real_time_alerts.py
nohup python3 scripts/real_time_alerts.py &

# Reiniciar dashboard
pkill -f monitoring_dashboard.py
nohup python3 scripts/monitoring_dashboard.py &
```

---

## 🎉 SISTEMA DE MONITORAMENTO COMPLETO IMPLEMENTADO!

✅ Logs de auditoria configurados
✅ Alertas de segurança ativos  
✅ Monitoring de vulnerabilidades
✅ SIEM integrado
✅ Dashboard web funcional

O sistema está pronto para produção e atende 100% dos requisitos de monitoramento!
