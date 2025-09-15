# 🔧 Guia de Solução de Problemas - WhatsApp Agent

> **Manual completo de troubleshooting** com procedimentos detalhados, diagnósticos automatizados, e soluções para problemas comuns em ambientes de produção e desenvolvimento.

---

## 🎯 **VISÃO GERAL DE TROUBLESHOOTING**

### **Categorias de Problemas** 📋

#### **Classificação por Severidade**
- 🚨 **CRÍTICO**: Sistema totalmente indisponível
- ⚠️ **ALTO**: Funcionalidade principal comprometida  
- 📝 **MÉDIO**: Funcionalidade secundária afetada
- 💡 **BAIXO**: Performance degradada ou bugs menores

#### **Tipos de Problemas Comuns**
- 🌐 **API Issues**: Endpoints não responsivos, erros HTTP
- 🗄️ **Database Problems**: Conexões, queries lentas, locks
- 💾 **Cache Issues**: Redis indisponível, cache corruption
- 📱 **WhatsApp Integration**: API Meta, webhooks, autenticação
- 🔐 **Authentication**: JWT, sessões, permissões
- 📊 **Performance**: Latência alta, memory leaks, CPU

---

## 🚨 **PROBLEMAS CRÍTICOS**

### **🌐 API Totalmente Indisponível**

#### **Sintomas**
- ❌ Curl/Postman retorna erro de conexão
- ❌ Health check endpoint não responde
- ❌ Dashboard mostra API Down
- ❌ Usuários reportam erro 502/503/504

#### **Diagnóstico Rápido**
```bash
# 1. Verificar se container está rodando
docker ps | grep whatsapp-agent-api

# 2. Verificar logs recentes
docker logs whatsapp-agent-api --tail 50

# 3. Verificar saúde do container
docker inspect whatsapp-agent-api | grep -A5 -B5 "Health"

# 4. Verificar porta e binding
netstat -tulpn | grep :8000
lsof -i :8000

# 5. Teste de conectividade local
curl -v http://localhost:8000/health
```

#### **Soluções por Ordem de Prioridade**

**🔄 1. Restart Graceful (Primeira Tentativa)**
```bash
# Restart do container
docker restart whatsapp-agent-api

# Aguardar inicialização (30-60s)
sleep 30

# Verificar se voltou
curl -f http://localhost:8000/health
curl -f https://api.whatsappagent.com/health

# Monitorar logs durante startup
docker logs whatsapp-agent-api -f
```

**🔧 2. Verificar Configuração (Se restart não resolver)**
```bash
# Verificar variáveis de ambiente
docker inspect whatsapp-agent-api | grep -A20 "Env"

# Verificar se DATABASE_URL está correto
docker exec whatsapp-agent-api env | grep DATABASE_URL

# Verificar conectividade com dependências
docker exec whatsapp-agent-api pg_isready -h postgres -p 5432
docker exec whatsapp-agent-api redis-cli -h redis ping

# Verificar arquivos de configuração
docker exec whatsapp-agent-api ls -la /app/config/
docker exec whatsapp-agent-api cat /app/config/production.env
```

**🏗️ 3. Rebuild se Configuração OK**
```bash
# Parar serviço
docker-compose down api

# Rebuild da imagem (se deploy recente)
docker-compose build api --no-cache

# Subir novamente
docker-compose up -d api

# Monitorar logs de inicialização
docker-compose logs -f api
```

**🗄️ 4. Verificar Dependências Críticas**
```bash
# Database connectivity
docker exec postgres pg_isready
PGPASSWORD=$DB_PASSWORD psql -h localhost -U whatsapp_agent -d whatsapp_agent -c "SELECT 1;"

# Redis connectivity  
docker exec redis redis-cli ping
docker exec redis redis-cli info server

# Network connectivity entre containers
docker network ls
docker network inspect whats_agent_default
```

#### **Procedimento de Escalation**
```bash
# Se nada resolver em 10 minutos:
# 1. Notificar engineering lead
# 2. Ativar modo de manutenção
# 3. Investigar logs de sistema

# Ativar página de manutenção
nginx -s reload -c /etc/nginx/maintenance.conf

# Logs de sistema para debugging profundo
journalctl -u docker --since "30 minutes ago"
dmesg | tail -50
free -h && df -h
```

### **🗄️ Database Connection Failed**

#### **Sintomas**
- ❌ API retorna 500 com erro de database
- ❌ Logs mostram "connection refused" ou "timeout"
- ❌ Grafana mostra PostgreSQL down
- ❌ Connection pool esgotado

#### **Diagnóstico Detalhado**
```bash
# 1. Verificar se PostgreSQL está rodando
docker ps | grep postgres
docker logs postgres --tail 30

# 2. Testar conexão direta
pg_isready -h localhost -p 5432
PGPASSWORD=$DB_PASSWORD psql -h localhost -U whatsapp_agent -d whatsapp_agent -c "\l"

# 3. Verificar conexões ativas
PGPASSWORD=$DB_PASSWORD psql -h localhost -U whatsapp_agent -d whatsapp_agent << EOF
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active_connections,
    count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity 
WHERE application_name = 'whatsapp_agent';

-- Verificar locks
SELECT * FROM pg_locks WHERE NOT granted;

-- Verificar queries longas
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
    AND state = 'active'
ORDER BY duration DESC;
EOF

# 4. Verificar configuração de connection pool
docker exec whatsapp-agent-api python -c "
from app.database import engine
print(f'Pool size: {engine.pool.size()}')
print(f'Checked out: {engine.pool.checkedout()}')
print(f'Overflow: {engine.pool.overflow()}')
print(f'Checked in: {engine.pool.checkedin()}')
"
```

#### **Soluções Escalonadas**

**🔄 1. Kill Conexões Problemáticas**
```sql
-- Conectar como superuser
sudo -u postgres psql

-- Identificar conexões problemáticas
SELECT 
    pid,
    application_name,
    state,
    query_start,
    query
FROM pg_stat_activity 
WHERE application_name = 'whatsapp_agent'
    AND state IN ('idle in transaction', 'active')
    AND (now() - query_start) > interval '2 minutes';

-- Kill conexões específicas (substituir PIDs)
SELECT pg_terminate_backend(12345);
SELECT pg_terminate_backend(12346);

-- Ou kill todas as conexões da aplicação (CUIDADO!)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity 
WHERE application_name = 'whatsapp_agent'
    AND pid <> pg_backend_pid();
```

**🔧 2. Restart PostgreSQL (Se necessário)**
```bash
# Restart graceful
docker restart postgres

# Aguardar inicialização
sleep 30

# Verificar logs
docker logs postgres --tail 20

# Testar conectividade
pg_isready -h localhost -p 5432
PGPASSWORD=$DB_PASSWORD psql -h localhost -U whatsapp_agent -d whatsapp_agent -c "SELECT now();"
```

**⚙️ 3. Ajustar Connection Pool**
```python
# Configuração emergencial no app/database.py
# Reduzir pool size temporariamente

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,        # Reduzido de 10
    max_overflow=10,    # Reduzido de 20
    pool_timeout=60,    # Aumentado de 30
    pool_recycle=1800,  # Reduzido de 3600
    pool_pre_ping=True
)

# Rebuild e restart da aplicação
docker-compose build api
docker-compose up -d api
```

### **💾 Redis Cache Indisponível**

#### **Sintomas**
- ⚠️ API lenta mas funcional
- ❌ Cache miss rate 100%
- ❌ Redis connection errors nos logs
- 📊 Performance degradada significativamente

#### **Diagnóstico e Solução**
```bash
# 1. Verificar Redis container
docker ps | grep redis
docker logs redis --tail 20

# 2. Testar conectividade
redis-cli -h localhost ping
redis-cli -h localhost info server

# 3. Verificar uso de memória
redis-cli -h localhost info memory | grep -E "(used_memory|maxmemory)"

# 4. Se Redis está rodando mas não responsivo
redis-cli -h localhost shutdown nosave
docker restart redis

# 5. Se Redis não está rodando
docker-compose up -d redis

# 6. Verificar configuração
docker exec redis cat /etc/redis/redis.conf | grep -E "(maxmemory|timeout)"

# 7. Flush cache se necessário (dados corrompidos)
redis-cli -h localhost flushdb
```

---

## ⚠️ **PROBLEMAS DE ALTA PRIORIDADE**

### **📱 WhatsApp Integration Broken**

#### **Sintomas**
- ❌ Mensagens não são enviadas
- ❌ Webhooks não funcionam
- ❌ API Meta retorna erros de autenticação
- ❌ Templates não carregam

#### **Diagnóstico Completo**
```bash
# 1. Verificar configuração WhatsApp
docker exec whatsapp-agent-api python -c "
from app.config import settings
print(f'WHATSAPP_TOKEN: {settings.WHATSAPP_TOKEN[:10]}...')
print(f'WHATSAPP_VERIFY_TOKEN: {settings.WHATSAPP_VERIFY_TOKEN[:10]}...')
print(f'WHATSAPP_PHONE_ID: {settings.WHATSAPP_PHONE_ID}')
"

# 2. Testar conectividade com Meta API
curl -H "Authorization: Bearer $WHATSAPP_TOKEN" \
     "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_ID"

# 3. Verificar webhook endpoint
curl -X GET "https://api.whatsappagent.com/webhooks/whatsapp?hub.verify_token=$WHATSAPP_VERIFY_TOKEN&hub.challenge=test123&hub.mode=subscribe"

# 4. Logs específicos do WhatsApp
docker logs whatsapp-agent-api | grep -i whatsapp | tail -20

# 5. Testar envio de mensagem simples
curl -X POST "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_ID/messages" \
     -H "Authorization: Bearer $WHATSAPP_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "messaging_product": "whatsapp",
       "to": "+5511999999999",
       "type": "text",
       "text": {"body": "Test message"}
     }'
```

#### **Soluções por Problema Específico**

**🔑 1. Token Expirado/Inválido**
```bash
# Verificar validade do token
curl -H "Authorization: Bearer $WHATSAPP_TOKEN" \
     "https://graph.facebook.com/v18.0/me"

# Se token inválido:
# 1. Gerar novo token no Meta Business
# 2. Atualizar variável de ambiente
# 3. Restart da aplicação

# Atualizar token
export WHATSAPP_TOKEN="novo_token_aqui"
docker-compose restart api

# Verificar se funcionou
curl -H "Authorization: Bearer $WHATSAPP_TOKEN" \
     "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_ID"
```

**📞 2. Phone Number Verification Issues**
```bash
# Verificar status do número
curl -H "Authorization: Bearer $WHATSAPP_TOKEN" \
     "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_ID" | jq .

# Verificar se número está ativo no Business Manager
# Se não: reativar no Meta Business Manager

# Verificar webhook subscription
curl -H "Authorization: Bearer $WHATSAPP_TOKEN" \
     "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_ID/subscribed_apps"
```

**🌐 3. Webhook Problems**
```bash
# Testar webhook localmente
curl -X POST "https://api.whatsappagent.com/webhooks/whatsapp" \
     -H "Content-Type: application/json" \
     -d '{
       "object": "whatsapp_business_account",
       "entry": [{
         "id": "test",
         "changes": [{
           "value": {
             "messaging_product": "whatsapp",
             "metadata": {
               "display_phone_number": "15550123456",
               "phone_number_id": "'$WHATSAPP_PHONE_ID'"
             },
             "messages": [{
               "from": "5511999999999",
               "id": "test_message_id",
               "text": {"body": "test"},
               "timestamp": "'$(date +%s)'",
               "type": "text"
             }]
           },
           "field": "messages"
         }]
       }]
     }'

# Verificar se webhook está registrado corretamente
curl -H "Authorization: Bearer $WHATSAPP_TOKEN" \
     "https://graph.facebook.com/v18.0/$WHATSAPP_BUSINESS_ACCOUNT_ID/subscribed_apps"

# Re-registrar webhook se necessário
curl -X POST "https://graph.facebook.com/v18.0/$WHATSAPP_BUSINESS_ACCOUNT_ID/subscribed_apps" \
     -H "Authorization: Bearer $WHATSAPP_TOKEN" \
     -d "subscribed_fields=messages"
```

### **🔐 Authentication Problems**

#### **Sintomas**
- ❌ Login retorna 401 Unauthorized
- ❌ JWT tokens inválidos
- ❌ Sessões expiram rapidamente
- ❌ CORS errors no frontend

#### **Diagnóstico JWT**
```bash
# 1. Verificar configuração JWT
docker exec whatsapp-agent-api python -c "
from app.config import settings
print(f'JWT_SECRET_KEY length: {len(settings.JWT_SECRET_KEY)}')
print(f'JWT_ALGORITHM: {settings.JWT_ALGORITHM}')
print(f'JWT_EXPIRATION_HOURS: {settings.JWT_EXPIRATION_HOURS}')
"

# 2. Testar geração de token
docker exec whatsapp-agent-api python -c "
from app.auth.jwt_handler import create_access_token
token = create_access_token({'user_id': 1, 'email': 'test@test.com'})
print(f'Generated token: {token[:50]}...')
"

# 3. Verificar decodificação de token
# Usar token real capturado dos logs ou rede
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

docker exec whatsapp-agent-api python -c "
from app.auth.jwt_handler import verify_token
try:
    payload = verify_token('$TOKEN')
    print(f'Token valid: {payload}')
except Exception as e:
    print(f'Token invalid: {e}')
"

# 4. Verificar tempo de expiração
docker exec whatsapp-agent-api python -c "
import jwt
from app.config import settings
token = '$TOKEN'
try:
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    import datetime
    exp_time = datetime.datetime.fromtimestamp(decoded['exp'])
    now = datetime.datetime.utcnow()
    print(f'Token expires at: {exp_time}')
    print(f'Current time: {now}')
    print(f'Valid for: {exp_time - now}')
except Exception as e:
    print(f'Error: {e}')
"
```

#### **Soluções de Autenticação**

**🔑 1. JWT Secret Key Problems**
```bash
# Verificar se JWT_SECRET_KEY está definida e forte
if [ ${#JWT_SECRET_KEY} -lt 32 ]; then
    echo "❌ JWT_SECRET_KEY too short (min 32 chars)"
    # Gerar nova chave segura
    export JWT_SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')
    echo "✅ New JWT_SECRET_KEY generated"
fi

# Restart aplicação com nova chave
docker-compose restart api
```

**⏰ 2. Token Expiration Issues**
```python
# Ajustar configuração em app/config.py se tokens expirando muito rápido
JWT_EXPIRATION_HOURS = 24  # Aumentar de 1 para 24 horas

# Ou implementar refresh token mechanism
# app/auth/jwt_handler.py
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)  # 30 dias
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
```

**🌐 3. CORS Configuration**
```python
# Verificar configuração CORS em app/cors_config.py
ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Next.js dev
    "https://dashboard.whatsappagent.com",
    "https://api.whatsappagent.com"
]

# Adicionar middleware CORS se não existir
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

### **📊 Performance Degradation**

#### **Sintomas**
- ⏱️ Response times > 1 segundo
- 📈 CPU usage > 80%
- 💾 Memory usage crescendo
- 🗄️ Database queries lentas

#### **Diagnóstico Performance**
```bash
# 1. Monitoramento em tempo real
htop
iotop
docker stats

# 2. Profiling da aplicação
docker exec whatsapp-agent-api python -c "
import psutil
import os

process = psutil.Process(os.getpid())
print(f'CPU: {process.cpu_percent()}%')
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
print(f'Threads: {process.num_threads()}')
print(f'Open files: {process.num_fds()}')
"

# 3. Database performance
PGPASSWORD=$DB_PASSWORD psql -h localhost -U whatsapp_agent -d whatsapp_agent << EOF
-- Top queries lentas
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Índices não utilizados
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;

-- Tamanho das tabelas
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF

# 4. Cache performance
redis-cli info stats | grep -E "(hit|miss|ops|memory)"

# 5. Network latency
curl -w "@curl-format.txt" -s -o /dev/null https://api.whatsappagent.com/health
```

#### **Otimizações Rápidas**

**🗄️ 1. Database Quick Fixes**
```sql
-- Atualizar estatísticas
ANALYZE;

-- Reindex tabelas principais se necessário
REINDEX TABLE appointments;
REINDEX TABLE users;

-- Vacuum para liberar espaço
VACUUM (ANALYZE, VERBOSE) appointments;

-- Kill queries muito longas
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '30 seconds'
    AND state = 'active' 
    AND application_name = 'whatsapp_agent';
```

**💾 2. Cache Optimization**
```bash
# Limpar cache corrompido
redis-cli flushdb

# Restart Redis se memory usage alto
docker restart redis

# Verificar configuração de memória
redis-cli config get maxmemory
redis-cli config set maxmemory 2gb
redis-cli config set maxmemory-policy allkeys-lru
```

**🚀 3. Application Scaling**
```bash
# Scale horizontal temporário
docker-compose up -d --scale api=3

# Verificar load balancing
for i in {1..10}; do
    curl -s https://api.whatsappagent.com/health | jq .hostname
done

# Se necessário, aumentar recursos
docker update --memory=2g --cpus=2 whatsapp-agent-api
```

---

## 📝 **PROBLEMAS MÉDIOS**

### **📧 Email Notifications Failed**

#### **Diagnóstico**
```bash
# 1. Verificar configuração SMTP
docker exec whatsapp-agent-api python -c "
from app.config import settings
print(f'SMTP_HOST: {settings.SMTP_HOST}')
print(f'SMTP_PORT: {settings.SMTP_PORT}')
print(f'SMTP_USER: {settings.SMTP_USER}')
print(f'SMTP_USE_TLS: {settings.SMTP_USE_TLS}')
"

# 2. Testar conexão SMTP
docker exec whatsapp-agent-api python -c "
import smtplib
from app.config import settings

try:
    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
    server.starttls()
    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    print('✅ SMTP connection successful')
    server.quit()
except Exception as e:
    print(f'❌ SMTP connection failed: {e}')
"

# 3. Verificar fila de emails
docker exec whatsapp-agent-api python -c "
from app.services.email_service import get_email_queue_status
print(get_email_queue_status())
"
```

#### **Soluções**
```python
# 1. Configurar retry mechanism
# app/services/email_service.py
async def send_email_with_retry(to: str, subject: str, body: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            await send_email(to, subject, body)
            return True
        except Exception as e:
            logger.warning(f"Email send attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error(f"Email send failed after {max_retries} attempts")
                # Store in dead letter queue
                await store_failed_email(to, subject, body, str(e))
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return False

# 2. Verificar credenciais Gmail/Outlook
# Para Gmail: App Password necessário
# Para Outlook: Modern auth configurado
```

### **📊 Dashboard Data Issues**

#### **Sintomas**
- 📈 Gráficos não carregam
- 📊 Dados inconsistentes
- ⏰ Data lag excessivo
- 🔢 Métricas incorretas

#### **Diagnóstico e Solução**
```bash
# 1. Verificar cache de analytics
redis-cli keys "analytics:*"
redis-cli get "analytics:dashboard:1:30d"

# 2. Verificar geração de relatórios
docker exec whatsapp-agent-api python -c "
from app.services.analytics_service import generate_dashboard_data
import asyncio

async def test_analytics():
    try:
        data = await generate_dashboard_data(business_id=1, period='7d')
        print(f'Analytics data: {data}')
    except Exception as e:
        print(f'Analytics error: {e}')

asyncio.run(test_analytics())
"

# 3. Reprocessar dados se necessário
docker exec whatsapp-agent-api python -c "
from app.services.analytics_service import recalculate_all_metrics
import asyncio
asyncio.run(recalculate_all_metrics())
"

# 4. Limpar cache corrompido
redis-cli del "analytics:dashboard:*"
redis-cli del "analytics:monthly:*"
```

---

## 💡 **PROBLEMAS DE BAIXA PRIORIDADE**

### **🎨 Frontend/UI Issues**

#### **Sintomas Comuns**
- 🖼️ Imagens não carregam
- 🎨 CSS quebrado
- ⚡ JavaScript errors
- 📱 Mobile layout issues

#### **Soluções Rápidas**
```bash
# 1. Verificar arquivos estáticos
ls -la app/static/
curl -I https://api.whatsappagent.com/static/css/main.css

# 2. Rebuild assets se necessário
cd nextjs_dashboard
npm run build
npm run export

# 3. Verificar NGINX serving static files
nginx -t
nginx -s reload

# 4. Browser cache issues
# Instruir usuários para:
# Ctrl+F5 (hard refresh)
# Clear browser cache
# Private/incognito mode
```

### **📝 Logging Issues**

#### **Problemas**
- 📝 Logs não aparecem
- 💾 Log files muito grandes
- 🔍 Formatação incorreta

#### **Soluções**
```bash
# 1. Verificar configuração de logging
docker exec whatsapp-agent-api python -c "
import logging
logger = logging.getLogger()
print(f'Log level: {logger.level}')
print(f'Handlers: {logger.handlers}')
"

# 2. Rotacionar logs grandes
logrotate -f /etc/logrotate.d/whatsapp-agent

# 3. Ajustar log level temporariamente
docker exec whatsapp-agent-api python -c "
import logging
logging.getLogger().setLevel(logging.DEBUG)
print('Log level set to DEBUG')
"

# 4. Verificar disk space para logs
df -h /var/log/
```

---

## 🛠️ **FERRAMENTAS DE DIAGNÓSTICO**

### **Script de Diagnóstico Automático**

#### **Diagnostic Tool - diagnostic.py**
```python
#!/usr/bin/env python3
# scripts/diagnostic.py

import asyncio
import subprocess
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

class SystemDiagnostic:
    """
    Ferramenta de diagnóstico automático
    """
    
    def __init__(self):
        self.results = {}
        self.issues = []
        
    async def run_full_diagnostic(self):
        """
        Executar diagnóstico completo do sistema
        """
        print("🔍 Starting WhatsApp Agent System Diagnostic")
        print("=" * 50)
        
        # Executar todos os checks
        await self._check_containers()
        await self._check_api_health()
        await self._check_database()
        await self._check_redis()
        await self._check_whatsapp_integration()
        await self._check_performance()
        await self._check_disk_space()
        await self._check_logs()
        
        # Gerar relatório
        self._generate_report()
        
    async def _check_containers(self):
        """
        Verificar status dos containers Docker
        """
        print("\n🐳 Checking Docker Containers...")
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True, text=True
            )
            
            containers = {}
            expected_containers = [
                "whatsapp-agent-api",
                "postgres", 
                "redis",
                "nginx"
            ]
            
            running_containers = []
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        name, status = line.split('\t')
                        containers[name] = status
                        running_containers.append(name)
            
            # Verificar containers obrigatórios
            missing_containers = []
            for container in expected_containers:
                if container not in running_containers:
                    missing_containers.append(container)
                    self.issues.append(f"❌ Container {container} not running")
                else:
                    print(f"  ✅ {container}: {containers[container]}")
            
            self.results['containers'] = {
                'running': running_containers,
                'missing': missing_containers,
                'status': 'healthy' if not missing_containers else 'unhealthy'
            }
            
        except Exception as e:
            self.results['containers'] = {'status': 'error', 'error': str(e)}
            self.issues.append(f"❌ Docker check failed: {e}")
    
    async def _check_api_health(self):
        """
        Verificar saúde da API
        """
        print("\n🌐 Checking API Health...")
        
        import aiohttp
        import time
        
        endpoints = [
            "/health",
            "/health/deep",
            "/auth/health"
        ]
        
        api_results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    async with session.get(f"http://localhost:8000{endpoint}") as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            print(f"  ✅ {endpoint}: {response.status} ({response_time:.3f}s)")
                            api_results[endpoint] = {
                                'status': 'healthy',
                                'response_time': response_time,
                                'status_code': response.status
                            }
                        else:
                            print(f"  ❌ {endpoint}: {response.status}")
                            api_results[endpoint] = {
                                'status': 'unhealthy',
                                'status_code': response.status
                            }
                            self.issues.append(f"❌ API endpoint {endpoint} returned {response.status}")
                            
                except Exception as e:
                    print(f"  ❌ {endpoint}: Connection failed - {e}")
                    api_results[endpoint] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    self.issues.append(f"❌ API endpoint {endpoint} connection failed: {e}")
        
        self.results['api'] = api_results
    
    async def _check_database(self):
        """
        Verificar conexão e performance do banco
        """
        print("\n🗄️ Checking Database...")
        
        try:
            # Testar conexão básica
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("  ✅ PostgreSQL connection: OK")
                
                # Testar query simples
                db_test = subprocess.run([
                    "docker", "exec", "postgres", "psql", 
                    "-U", "whatsapp_agent", "-d", "whatsapp_agent",
                    "-c", "SELECT COUNT(*) FROM appointments;"
                ], capture_output=True, text=True)
                
                if db_test.returncode == 0:
                    print("  ✅ Database query: OK")
                    self.results['database'] = {'status': 'healthy'}
                else:
                    print(f"  ❌ Database query failed: {db_test.stderr}")
                    self.results['database'] = {'status': 'query_failed', 'error': db_test.stderr}
                    self.issues.append("❌ Database query test failed")
            else:
                print(f"  ❌ PostgreSQL connection failed: {result.stderr}")
                self.results['database'] = {'status': 'connection_failed', 'error': result.stderr}
                self.issues.append("❌ Database connection failed")
                
        except Exception as e:
            self.results['database'] = {'status': 'error', 'error': str(e)}
            self.issues.append(f"❌ Database check error: {e}")
    
    async def _check_redis(self):
        """
        Verificar Redis cache
        """
        print("\n💾 Checking Redis Cache...")
        
        try:
            result = subprocess.run(
                ["redis-cli", "-h", "localhost", "ping"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0 and "PONG" in result.stdout:
                print("  ✅ Redis connection: OK")
                
                # Verificar memória
                mem_info = subprocess.run(
                    ["redis-cli", "-h", "localhost", "info", "memory"],
                    capture_output=True, text=True
                )
                
                if mem_info.returncode == 0:
                    # Parse memory usage
                    for line in mem_info.stdout.split('\n'):
                        if 'used_memory_human:' in line:
                            memory_used = line.split(':')[1].strip()
                            print(f"  📊 Memory used: {memory_used}")
                            break
                
                self.results['redis'] = {'status': 'healthy'}
            else:
                print(f"  ❌ Redis connection failed: {result.stderr}")
                self.results['redis'] = {'status': 'connection_failed', 'error': result.stderr}
                self.issues.append("❌ Redis connection failed")
                
        except Exception as e:
            self.results['redis'] = {'status': 'error', 'error': str(e)}
            self.issues.append(f"❌ Redis check error: {e}")
    
    async def _check_whatsapp_integration(self):
        """
        Verificar integração WhatsApp
        """
        print("\n📱 Checking WhatsApp Integration...")
        
        try:
            # Verificar configuração básica
            config_check = subprocess.run([
                "docker", "exec", "whatsapp-agent-api", "python", "-c",
                "from app.config import settings; print(f'Phone ID: {settings.WHATSAPP_PHONE_ID}')"
            ], capture_output=True, text=True)
            
            if config_check.returncode == 0:
                print("  ✅ WhatsApp configuration: OK")
                self.results['whatsapp'] = {'status': 'healthy'}
            else:
                print(f"  ❌ WhatsApp configuration error: {config_check.stderr}")
                self.results['whatsapp'] = {'status': 'config_error', 'error': config_check.stderr}
                self.issues.append("❌ WhatsApp configuration error")
                
        except Exception as e:
            self.results['whatsapp'] = {'status': 'error', 'error': str(e)}
            self.issues.append(f"❌ WhatsApp check error: {e}")
    
    async def _check_performance(self):
        """
        Verificar métricas de performance
        """
        print("\n📊 Checking Performance Metrics...")
        
        try:
            # CPU e Memory usage
            stats = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", 
                 "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
                capture_output=True, text=True
            )
            
            if stats.returncode == 0:
                performance = {}
                for line in stats.stdout.strip().split('\n'):
                    if line and 'whatsapp-agent' in line:
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            name = parts[0]
                            cpu = parts[1].replace('%', '')
                            memory = parts[2].split('/')[0].strip()
                            
                            performance[name] = {
                                'cpu_percent': cpu,
                                'memory_usage': memory
                            }
                            
                            # Check thresholds
                            try:
                                cpu_val = float(cpu)
                                if cpu_val > 80:
                                    self.issues.append(f"⚠️ High CPU usage: {name} at {cpu}%")
                                    print(f"  ⚠️ {name} CPU: {cpu}% (HIGH)")
                                else:
                                    print(f"  ✅ {name} CPU: {cpu}%")
                            except ValueError:
                                pass
                
                self.results['performance'] = performance
            
        except Exception as e:
            self.results['performance'] = {'status': 'error', 'error': str(e)}
    
    async def _check_disk_space(self):
        """
        Verificar espaço em disco
        """
        print("\n💽 Checking Disk Space...")
        
        try:
            df_result = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True, text=True
            )
            
            if df_result.returncode == 0:
                lines = df_result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        usage_percent = parts[4].replace('%', '')
                        
                        try:
                            usage_val = int(usage_percent)
                            if usage_val > 90:
                                self.issues.append(f"🚨 Critical disk usage: {usage_percent}%")
                                print(f"  🚨 Disk usage: {usage_percent}% (CRITICAL)")
                            elif usage_val > 80:
                                self.issues.append(f"⚠️ High disk usage: {usage_percent}%")
                                print(f"  ⚠️ Disk usage: {usage_percent}% (HIGH)")
                            else:
                                print(f"  ✅ Disk usage: {usage_percent}%")
                            
                            self.results['disk'] = {
                                'usage_percent': usage_percent,
                                'status': 'critical' if usage_val > 90 else 'warning' if usage_val > 80 else 'healthy'
                            }
                        except ValueError:
                            pass
                        
        except Exception as e:
            self.results['disk'] = {'status': 'error', 'error': str(e)}
    
    async def _check_logs(self):
        """
        Verificar logs para erros recentes
        """
        print("\n📝 Checking Recent Logs...")
        
        try:
            # Verificar logs dos últimos 10 minutos
            logs = subprocess.run([
                "docker", "logs", "whatsapp-agent-api", "--since", "10m"
            ], capture_output=True, text=True)
            
            if logs.returncode == 0:
                error_count = logs.stderr.lower().count('error')
                critical_count = logs.stderr.lower().count('critical')
                
                print(f"  📊 Errors in last 10min: {error_count}")
                print(f"  📊 Critical in last 10min: {critical_count}")
                
                if critical_count > 0:
                    self.issues.append(f"🚨 {critical_count} critical errors in recent logs")
                elif error_count > 10:
                    self.issues.append(f"⚠️ {error_count} errors in recent logs")
                else:
                    print("  ✅ Log health: OK")
                
                self.results['logs'] = {
                    'error_count': error_count,
                    'critical_count': critical_count,
                    'status': 'critical' if critical_count > 0 else 'warning' if error_count > 10 else 'healthy'
                }
                
        except Exception as e:
            self.results['logs'] = {'status': 'error', 'error': str(e)}
    
    def _generate_report(self):
        """
        Gerar relatório final
        """
        print("\n" + "=" * 50)
        print("📋 DIAGNOSTIC REPORT")
        print("=" * 50)
        
        # Status geral
        total_checks = len(self.results)
        healthy_checks = sum(1 for r in self.results.values() 
                           if isinstance(r, dict) and r.get('status') == 'healthy')
        
        print(f"🔍 Total checks: {total_checks}")
        print(f"✅ Healthy: {healthy_checks}")
        print(f"❌ Issues found: {len(self.issues)}")
        
        # Listar problemas
        if self.issues:
            print(f"\n🚨 ISSUES FOUND:")
            for issue in self.issues:
                print(f"  {issue}")
        else:
            print(f"\n🎉 All systems healthy!")
        
        # Salvar relatório JSON
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'issues': self.issues,
            'summary': {
                'total_checks': total_checks,
                'healthy_checks': healthy_checks,
                'issues_count': len(self.issues)
            }
        }
        
        with open('/tmp/diagnostic_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Full report saved to: /tmp/diagnostic_report.json")

async def main():
    diagnostic = SystemDiagnostic()
    await diagnostic.run_full_diagnostic()

if __name__ == "__main__":
    asyncio.run(main())
```

### **Quick Fix Script**

#### **quick_fix.sh**
```bash
#!/bin/bash
# scripts/quick_fix.sh

set -e

echo "🚀 WhatsApp Agent Quick Fix Tool"
echo "==============================="

# Função para executar com status
run_with_status() {
    local description="$1"
    local command="$2"
    
    echo -n "🔧 $description... "
    
    if eval "$command" &>/dev/null; then
        echo "✅ Done"
        return 0
    else
        echo "❌ Failed"
        return 1
    fi
}

# Menu de opções
echo "Select fix option:"
echo "1. Restart all services"
echo "2. Fix database connections" 
echo "3. Clear Redis cache"
echo "4. Fix permissions"
echo "5. Update containers"
echo "6. Full system reset"
echo "0. Exit"

read -p "Choose option [0-6]: " option

case $option in
    1)
        echo "🔄 Restarting all services..."
        run_with_status "Stop services" "docker-compose down"
        run_with_status "Start services" "docker-compose up -d"
        run_with_status "Wait for startup" "sleep 30"
        run_with_status "Verify API" "curl -f http://localhost:8000/health"
        ;;
    
    2)
        echo "🗄️ Fixing database connections..."
        run_with_status "Kill long queries" "docker exec postgres psql -U whatsapp_agent -d whatsapp_agent -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '30 seconds' AND state = 'active' AND application_name = 'whatsapp_agent';\""
        run_with_status "Restart database" "docker restart postgres"
        run_with_status "Restart API" "docker restart whatsapp-agent-api"
        ;;
    
    3)
        echo "💾 Clearing Redis cache..."
        run_with_status "Flush cache" "redis-cli flushdb"
        run_with_status "Restart Redis" "docker restart redis"
        ;;
    
    4)
        echo "🔐 Fixing permissions..."
        run_with_status "Fix log permissions" "sudo chown -R $USER:$USER /var/log/whatsapp-agent/"
        run_with_status "Fix config permissions" "sudo chown -R $USER:$USER ./config/"
        run_with_status "Fix data permissions" "sudo chown -R 999:999 ./data/postgres"
        ;;
    
    5)
        echo "📦 Updating containers..."
        run_with_status "Pull latest images" "docker-compose pull"
        run_with_status "Rebuild services" "docker-compose build --no-cache"
        run_with_status "Restart with new images" "docker-compose up -d"
        ;;
    
    6)
        echo "🔄 Full system reset..."
        echo "⚠️  WARNING: This will reset all data!"
        read -p "Are you sure? [y/N]: " confirm
        
        if [[ $confirm == [yY] ]]; then
            run_with_status "Stop all services" "docker-compose down -v"
            run_with_status "Remove containers" "docker-compose rm -f"
            run_with_status "Clear volumes" "docker volume prune -f"
            run_with_status "Rebuild everything" "docker-compose build --no-cache"
            run_with_status "Start fresh" "docker-compose up -d"
            run_with_status "Wait for initialization" "sleep 60"
            run_with_status "Run migrations" "docker exec whatsapp-agent-api alembic upgrade head"
        else
            echo "❌ Reset cancelled"
        fi
        ;;
    
    0)
        echo "👋 Exiting..."
        exit 0
        ;;
    
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "✅ Quick fix completed!"
echo "🔍 Run health check: ./scripts/health_check.sh"
echo "📊 Check status: docker-compose ps"
```

---

## 📚 **KNOWLEDGE BASE**

### **Códigos de Erro Comuns**

#### **HTTP Error Codes**
```
🔴 500 Internal Server Error
├── Causa: Database connection failed
├── Solução: Verificar PostgreSQL e connection pool
└── Comando: docker restart postgres && docker restart whatsapp-agent-api

🔴 502 Bad Gateway  
├── Causa: API container não responsivo
├── Solução: Restart do container API
└── Comando: docker restart whatsapp-agent-api

🟡 429 Too Many Requests
├── Causa: Rate limiting ativo
├── Solução: Verificar rate limit config ou aguardar
└── Comando: redis-cli del "rate_limit:*"

🔴 401 Unauthorized
├── Causa: JWT token inválido/expirado
├── Solução: Relogin ou verificar JWT config
└── Comando: Verificar JWT_SECRET_KEY

🟡 404 Not Found
├── Causa: Endpoint incorreto ou recurso deletado
├── Solução: Verificar URL e dados
└── Comando: Verificar logs de request
```

#### **WhatsApp API Errors**
```
🔴 Error 131000: Generic user error
├── Causa: Token inválido ou expirado
├── Solução: Renovar token no Meta Business
└── Verificação: curl -H "Authorization: Bearer $TOKEN" "https://graph.facebook.com/v18.0/me"

🔴 Error 131005: Message undeliverable  
├── Causa: Número inválido ou bloqueado
├── Solução: Verificar formato do número
└── Formato: +55DDNNNNNNNNN (Brasil)

🔴 Error 131021: Recipient not available
├── Causa: WhatsApp não instalado ou número inexistente
├── Solução: Verificar número com cliente
└── Teste: Enviar mensagem manual pelo WhatsApp

🟡 Error 131047: Re-engagement message
├── Causa: Cliente não interage há mais de 24h
├── Solução: Usar template message
└── Comando: Verificar templates aprovados
```

### **Performance Thresholds**

#### **Métricas Aceitáveis**
```
📊 API Response Time:
├── ✅ Excellent: < 100ms
├── ✅ Good: 100-300ms  
├── ⚠️ Warning: 300-1000ms
└── 🚨 Critical: > 1000ms

📊 Database Query Time:
├── ✅ Excellent: < 10ms
├── ✅ Good: 10-50ms
├── ⚠️ Warning: 50-200ms  
└── 🚨 Critical: > 200ms

📊 Memory Usage:
├── ✅ Excellent: < 50%
├── ✅ Good: 50-70%
├── ⚠️ Warning: 70-85%
└── 🚨 Critical: > 85%

📊 CPU Usage:
├── ✅ Excellent: < 30%
├── ✅ Good: 30-50%
├── ⚠️ Warning: 50-80%
└── 🚨 Critical: > 80%

📊 Cache Hit Rate:
├── ✅ Excellent: > 95%
├── ✅ Good: 90-95%
├── ⚠️ Warning: 80-90%
└── 🚨 Critical: < 80%
```

---

<div align="center">

**🔧 TROUBLESHOOTING ENTERPRISE COMPLETO**

*Sistema de diagnóstico e resolução automatizada*

**Diagnóstico Automático** ✅ | **Quick Fix Tools** ✅ | **Knowledge Base** ✅

</div>