# 🧪 SUITE DE TESTES COMPLETA - WhatsApp Agent

> **Sistema abrangente de testes automatizados para validação completa do WhatsApp Agent em produção**

## 📋 Visão Geral

Esta suite de testes foi projetada para validar **TODOS** os aspectos críticos do WhatsApp Agent:

- ✅ **Infraestrutura**: Docker, PostgreSQL, Redis, Nginx
- ✅ **APIs FastAPI**: Todos os endpoints e health checks  
- ✅ **Integração WhatsApp**: Webhooks, mensagens, processamento LLM
- ✅ **Sistema de Agendamentos**: CRUD completo, cancelamentos
- ✅ **Dashboard Streamlit**: Interface administrativa
- ✅ **Monitoramento**: Prometheus, Grafana, métricas
- ✅ **Segurança**: Autenticação, rate limiting, validações
- ✅ **Backup & Recovery**: Sistemas de backup
- ✅ **Performance**: Testes de carga e stress
- ✅ **Configuração**: Validação de environments

## 🚀 Quick Start

### 1. Instalação Rápida

```bash
# Clone e configure o ambiente
git clone <seu-repositorio>
cd whatsapp-agent

# Torne os scripts executáveis
chmod +x run_complete_tests.sh
chmod +x whatsapp_message_tester.py
chmod +x complete_test_suite.py

# Configure ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuração Básica

```bash
# Copie o arquivo de configuração
cp .env.example .env.development

# Configure suas variáveis (IMPORTANTE!)
vim .env.development
```

**Variáveis essenciais para testes:**
```env
# Base de dados
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/whatsapp_agent

# WhatsApp (configure tokens reais para testes completos)
META_ACCESS_TOKEN=your_real_token_here
PHONE_NUMBER_ID=your_phone_number_id
WEBHOOK_VERIFY_TOKEN=your_webhook_token

# OpenAI
OPENAI_API_KEY=your_openai_key_here
```

### 3. Execução Básica

```bash
# Iniciar serviços
docker-compose up -d

# Aguardar inicialização (2-3 minutos)
sleep 180

# Executar testes básicos
./run_complete_tests.sh
```

## 🎯 Tipos de Teste

### 🔧 Testes de Infraestrutura
```bash
# Testa apenas a infraestrutura
python3 complete_test_suite.py --env development
```

**O que testa:**
- Containers Docker rodando
- Conectividade PostgreSQL
- Conectividade Redis  
- Health checks dos serviços
- Estrutura do banco de dados

### 💬 Testes de WhatsApp
```bash
# Testa integração WhatsApp completa
python3 whatsapp_message_tester.py --test-all
```

**O que testa:**
- Recebimento de webhooks
- Processamento de mensagens
- Respostas da LLM
- Agendamentos via WhatsApp
- Cancelamentos via WhatsApp
- Coleta de dados do usuário
- Diferentes tipos de mensagem

### 🚀 Testes de Performance
```bash
# Inclui testes de carga
./run_complete_tests.sh --with-load
```

**O que testa:**
- 50+ usuários simultâneos
- 1000+ operações de banco/segundo
- 500+ requisições API/segundo
- Tempo de resposta sob carga
- Estabilidade do sistema

### 🔒 Testes de Segurança
```bash
# Foco em segurança
./run_complete_tests.sh --environment production
```

**O que testa:**
- Autenticação de endpoints
- Rate limiting
- Validação de tokens
- Proteção contra ataques
- Logs de segurança

## 📊 Cenários de Teste Detalhados

### 1. Fluxo Completo de Agendamento

```
👤 Usuário: "Olá!"
🤖 Bot: "Olá! Como posso ajudar?"

👤 Usuário: "Quero agendar um horário"
🤖 Bot: "Claro! Qual seu nome?"

👤 Usuário: "João Silva"  
🤖 Bot: "Obrigado, João! Qual seu email?"

👤 Usuário: "joao@email.com"
🤖 Bot: "E seu telefone?"

👤 Usuário: "11987654321"
🤖 Bot: "Perfeito! Qual serviço deseja?"

👤 Usuário: "Corte de cabelo"
🤖 Bot: "Qual horário prefere?"

👤 Usuário: "Amanhã às 14h"
🤖 Bot: "Agendamento confirmado!"

✅ VALIDAÇÕES:
- Usuário criado no banco
- Agendamento salvo com status 'scheduled'
- Dados coletados corretamente
- Respostas da LLM adequadas
```

### 2. Teste de Cancelamento

```
👤 Usuário: "Preciso cancelar meu agendamento"
🤖 Bot: "Posso ajudar com isso. Confirma o cancelamento?"

👤 Usuário: "Sim, confirmo"
🤖 Bot: "Agendamento cancelado com sucesso!"

✅ VALIDAÇÕES:
- Status atualizado para 'cancelled'
- Data de cancelamento registrada
- Motivo do cancelamento salvo
```

### 3. Teste de Diferentes Tipos de Mensagem

```
📱 Texto simples: "Olá"
📱 Com emojis: "Quero agendar 💇‍♀️"
📱 Mensagem longa: "Olá! Gostaria de saber sobre seus serviços..."
📱 Múltiplas perguntas: "Vocês fazem corte? Quanto custa? Quando posso ir?"

✅ VALIDAÇÕES:
- Todas as mensagens processadas
- Respostas apropriadas geradas
- Emojis preservados
- Context mantido entre mensagens
```

## 📈 Métricas e Monitoramento

### Métricas Coletadas

```
🔍 Performance:
- Tempo de resposta da API (< 2s)
- Tempo de processamento LLM (< 10s) 
- Throughput de mensagens (> 100/min)
- Uso de CPU (< 80%)
- Uso de memória (< 4GB)

📊 Business:
- Taxa de criação de agendamentos (> 85%)
- Taxa de coleta de dados (> 80%)
- Taxa de respostas da LLM (> 90%)
- Mensagens processadas com sucesso (> 95%)

🛡️ Segurança:
- Tentativas de acesso não autorizado (0)
- Rate limiting funcionando (✅)
- Logs de segurança (monitorados)
```

### Dashboard de Monitoramento

Durante os testes, você pode monitorar em tempo real:

- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090  
- **API Health**: http://localhost:8000/health
- **Dashboard**: http://localhost:8501

## 🔧 Comandos Avançados

### Execução Personalizada

```bash
# Teste apenas conversas
python3 whatsapp_message_tester.py --test-conversations

# Teste apenas agendamentos  
python3 whatsapp_message_tester.py --test-appointments

# Teste ambiente específico
./run_complete_tests.sh --environment staging

# Execução paralela (mais rápido)
./run_complete_tests.sh --parallel

# Com timeout customizado
./run_complete_tests.sh --timeout 600

# Modo verbose (logs detalhados)
./run_complete_tests.sh --verbose

# Apenas limpeza
./run_complete_tests.sh --cleanup
```

### Validações Específicas

```bash
# Validar apenas configuração
python3 validate_configuration.py

# Validar apenas Docker
./validate_docker.sh

# Validar sistema de secrets
python3 validate_secrets.py

# Validar logs
python3 validate_logging.py

# Validar monitoramento
python3 validate_monitoring.py
```

## 📊 Interpretando Resultados

### Status de Saída

```bash
# Código 0: Todos os testes passaram ✅
echo $?  # Output: 0

# Código 1: Alguns testes falharam ⚠️  
echo $?  # Output: 1

# Código 2: Erro crítico ❌
echo $?  # Output: 2
```

### Relatórios Gerados

```
📁 test_reports/
├── consolidated_test_report_20240109_143022.md  # Relatório principal
├── test_report_1704813022.json                 # Dados completos JSON
├── whatsapp_test_report_1704813022.json        # Específico WhatsApp
└── performance_metrics_1704813022.csv          # Métricas de performance

📁 logs/
├── test_execution_20240109_143022.log          # Log de execução
├── app/                                        # Logs da aplicação
├── security/                                   # Logs de segurança  
└── business/                                   # Logs de negócio
```

### Interpretação de Métricas

```
🟢 95-100%: Excelente - Sistema pronto para produção
🟡 85-94%:  Bom - Pequenos ajustes necessários  
🟠 70-84%:  Atenção - Problemas identificados
🔴 < 70%:   Crítico - Correções urgentes necessárias
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. "Containers não iniciam"
```bash
# Verificar portas em uso
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :5432

# Limpar Docker
docker-compose down
docker system prune -f
docker-compose up -d --force-recreate
```

#### 2. "Testes de banco falham"
```bash
# Verificar conectividade
psql -h localhost -U vancimj -d whatsapp_agent -c "SELECT 1;"

# Verificar logs do PostgreSQL
docker-compose logs postgres

# Recriar banco se necessário
docker-compose exec postgres psql -U vancimj -c "DROP DATABASE IF EXISTS whatsapp_agent;"
docker-compose exec postgres psql -U vancimj -c "CREATE DATABASE whatsapp_agent;"
```

#### 3. "WhatsApp webhook não responde"
```bash
# Testar webhook manualmente
curl -X GET "http://localhost:8000/webhook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=test"

# Verificar logs
tail -f logs/app/webhook.log

# Verificar ngrok (se usando)
curl https://your-ngrok-url.ngrok.io/webhook
```

#### 4. "Testes de carga falham"
```bash
# Reduzir carga nos testes
# Editar test_config.json:
{
  "load_tests": {
    "concurrent_users": 10,  # Reduzir de 50
    "messages_per_user": 5   # Reduzir de 10
  }
}

# Monitorar recursos
htop
docker stats
```

#### 5. "LLM não responde"
```bash
# Verificar chave OpenAI
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Verificar logs da aplicação
tail -f logs/app/llm.log

# Testar endpoint diretamente
curl -X POST http://localhost:8000/test-llm -d '{"message": "test"}'
```

### Logs Importantes

```bash
# Logs principais para debug
tail -f logs/test_execution_*.log           # Execução dos testes
tail -f logs/app/main.log                   # Aplicação principal  
tail -f logs/app/webhook.log                # Webhooks WhatsApp
tail -f logs/security/auth.log              # Autenticação
tail -f logs/business/appointments.log      # Agendamentos

# Logs do Docker
docker-compose logs app --tail=50          # Aplicação
docker-compose logs postgres --tail=20     # Banco de dados
docker-compose logs redis --tail=20        # Redis
docker-compose logs nginx --tail=20        # Nginx
```

## 🔒 Considerações de Segurança

### Desenvolvimento
```bash
# Usar tokens de teste
META_ACCESS_TOKEN=test_token_development
OPENAI_API_KEY=test_key_development

# Banco local
DATABASE_URL=postgresql://localhost:5432/whatsapp_agent_test
```

### Staging
```bash
# Tokens de staging (não produção)
META_ACCESS_TOKEN=staging_token
OPENAI_API_KEY=staging_key

# Banco de staging
DATABASE_URL=postgresql://staging-db:5432/whatsapp_agent_staging
```

### Produção ⚠️
```bash
# CUIDADO: Use apenas em horários de baixo tráfego
# Faça backup antes:
pg_dump whatsapp_agent > backup_before_tests.sql

# Execute com cuidado:
./run_complete_tests.sh --environment production

# Monitore durante execução:
watch -n 5 'curl -s http://localhost:8000/health | jq'
```

## 📞 Suporte

### Para problemas com os testes:
1. Verifique os logs em `logs/test_execution_*.log`
2. Execute com `--verbose` para mais detalhes
3. Teste componentes individualmente
4. Consulte a seção de troubleshooting

### Para problemas com o sistema:
1. Verifique health checks: `curl http://localhost:8000/health`
2. Verifique containers: `docker-compose ps`
3. Verifique logs: `docker-compose logs app`
4. Reinicie serviços se necessário: `docker-compose restart`

---

## 🎉 Resultado Esperado

Ao final da execução completa, você deve ver:

```
╔══════════════════════════════════════════════════════════════╗
║                    EXECUÇÃO CONCLUÍDA                       ║
╚══════════════════════════════════════════════════════════════╝

ℹ️ Duração total: 180s
ℹ️ Status: 🟢 PASSOU - Sistema operacional  
ℹ️ Logs salvos em: logs/test_execution_20240109_143022.log
ℹ️ Relatórios em: test_reports/

✅ 🎉 TODOS OS TESTES PASSARAM! Sistema pronto para produção.
```

**Isso significa que seu WhatsApp Agent está 100% funcional e pronto para uso em produção! 🚀**