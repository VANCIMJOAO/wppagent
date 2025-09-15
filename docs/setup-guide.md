# 🚀 WhatsApp Agent - Guia Completo de Setup

> **Guia detalhado para instalação, configuração e deploy** do sistema WhatsApp Agent em ambiente de desenvolvimento e produção.

---

## 📋 **PRÉ-REQUISITOS**

### **Sistema Operacional**

- ✅ **Linux**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- ✅ **macOS**: 12.0+ (Monterey)
- ✅ **Windows**: 10+ com WSL2

### **Software Necessário**

#### **Core Requirements**

```bash
# Python 3.11+ (Required)
python --version  # 3.11.0+

# Node.js 18+ (Required)
node --version     # 18.0.0+

# PostgreSQL 16+ (Required)
psql --version     # 16.0+

# Redis 7+ (Required)
redis-server --version  # 7.0.0+

# Git (Required)
git --version     # 2.34.0+
```

#### **Development Tools**

```bash
# Docker & Docker Compose (Recommended)
docker --version         # 24.0.0+
docker-compose --version # 2.20.0+

# Package Managers
pip --version    # 23.0+
npm --version    # 9.0+
```

### **Meta Business API Requirements**

- ✅ **Meta Business Account** (verificado)
- ✅ **WhatsApp Business API Access** (aprovado)
- ✅ **Webhook endpoint** (HTTPS obrigatório)
- ✅ **Phone number** (verificado para WhatsApp Business)

---

## 🔧 **INSTALAÇÃO COMPLETA**

### **Método 1: Docker (Recomendado)**

#### **1.1 Clone e Setup Inicial**

```bash
# Clone do repositório
git clone https://github.com/VANCIMJOAO/wppagent.git
cd whats_agent

# Verificar estrutura
ls -la
# Deve mostrar: app/, nextjs_dashboard/, docker-compose.yml, etc.
```

#### **1.2 Configuração Environment**

```bash
# Copiar template de configuração
cp .env.example .env

# Editar configurações (ver seção Environment Variables)
nano .env
```

#### **1.3 Build e Start dos Serviços**

```bash
# Build das imagens
docker-compose build

# Start dos serviços em background
docker-compose up -d

# Verificar status dos containers
docker-compose ps
```

#### **1.4 Inicialização Database**

```bash
# Aplicar migrations
docker-compose exec app alembic upgrade head

# Verificar migrations aplicadas
docker-compose exec app alembic current
```

#### **1.5 Verificação da Instalação**

```bash
# Health check do sistema
curl -X GET http://localhost:8000/health

# Resposta esperada:
# {"status":"healthy","timestamp":"2025-01-16T21:30:00","version":"1.0.0"}

# Health check detalhado
curl -X GET http://localhost:8000/health/detailed

# Verificar frontend
curl -I http://localhost:3000
# Resposta esperada: HTTP/1.1 200 OK
```

### **Método 2: Instalação Manual**

#### **2.1 Setup Backend (FastAPI)**

```bash
# Criar ambiente virtual Python
python -m venv venv

# Ativar ambiente virtual
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt

# Verificar instalação
pip list | grep fastapi
# Deve mostrar: fastapi 0.104.0+
```

#### **2.2 Setup Database (PostgreSQL)**

```bash
# Instalar PostgreSQL (Ubuntu)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Iniciar serviço
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Criar usuário e database
sudo -u postgres psql
CREATE USER whatsapp_user WITH PASSWORD 'secure_password';
CREATE DATABASE whatsapp_agent OWNER whatsapp_user;
GRANT ALL PRIVILEGES ON DATABASE whatsapp_agent TO whatsapp_user;
\q

# Verificar conexão
psql -h localhost -U whatsapp_user -d whatsapp_agent -c "SELECT version();"
```

#### **2.3 Setup Redis**

```bash
# Instalar Redis (Ubuntu)
sudo apt install redis-server

# Configurar Redis
sudo nano /etc/redis/redis.conf
# Uncomment: requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis-server

# Verificar Redis
redis-cli ping
# Resposta esperada: PONG
```

#### **2.4 Aplicar Migrations**

```bash
# Na pasta raiz do projeto
alembic upgrade head

# Verificar status
alembic current
alembic heads
# Deve mostrar: 6897816d7333 (head)
```

#### **2.5 Setup Frontend (Next.js)**

```bash
# Navegar para o diretório frontend
cd nextjs_dashboard

# Instalar dependências
npm install

# Verificar instalação
npm ls react
# Deve mostrar: react@18.2.0

# Build para produção (opcional)
npm run build

# Verificar build
ls -la .next/
```

---

## ⚙️ **CONFIGURAÇÃO DETALHADA**

### **Environment Variables (.env)**

#### **Database Configuration**

```env
# PostgreSQL Configuration
DATABASE_URL=postgresql://whatsapp_user:secure_password@localhost:5432/whatsapp_agent
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

#### **Redis Configuration**

```env
# Redis Configuration
REDIS_URL=redis://default:your_redis_password@localhost:6379
REDIS_TTL=3600
REDIS_MAX_CONNECTIONS=100
```

#### **Security Configuration**

```env
# JWT Security
JWT_SECRET_KEY=your-super-secure-secret-key-minimum-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Cookie Security
COOKIE_SECURE=true
COOKIE_SAMESITE=strict
COOKIE_HTTPONLY=true
COOKIE_MAX_AGE=1800

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
RATE_LIMIT_BURST=20
```

#### **WhatsApp Meta API**

```env
# Meta Business API
META_ACCESS_TOKEN=your_permanent_access_token
META_PHONE_NUMBER_ID=your_phone_number_id
META_BUSINESS_ACCOUNT_ID=your_business_account_id
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret

# Webhook Configuration
WEBHOOK_SECRET=your_webhook_verification_secret
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
WEBHOOK_URL=https://yourdomain.com/webhook
```

#### **Application Configuration**

```env
# Application Settings
APP_NAME=WhatsApp Agent
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=jpg,jpeg,png,pdf,doc,docx

# Timezone
TZ=America/Sao_Paulo
```

### **Meta Business API Setup**

#### **3.1 Criar App no Meta for Developers**

1. Acesse [developers.facebook.com](https://developers.facebook.com)
2. Clique em "Create App" → "Business"
3. Nome: "WhatsApp Agent - [Sua Empresa]"
4. Adicione o produto "WhatsApp Business API"

#### **3.2 Configurar Webhook**

```bash
# No painel do Meta for Developers:
# 1. WhatsApp → Configuration → Webhook
# 2. Callback URL: https://yourdomain.com/webhook
# 3. Verify Token: [mesmo valor do WEBHOOK_VERIFY_TOKEN]
# 4. Subscribe to: messages, message_status
```

#### **3.3 Obter Tokens de Acesso**

```bash
# Temporary Access Token (desenvolvimento)
# Disponível em: WhatsApp → API Setup → Temporary access token

# Permanent Access Token (produção)
# Processo via System User do Business Manager
```

#### **3.4 Configurar Phone Number**

```bash
# No painel do Meta for Developers:
# 1. WhatsApp → API Setup → Phone numbers
# 2. Add phone number ou use test number
# 3. Verify phone number
# 4. Copy Phone Number ID
```

### **Database Configuration (Avançada)**

#### **4.1 Otimizações PostgreSQL**

```sql
-- Configurações de performance (/etc/postgresql/16/main/postgresql.conf)
shared_buffers = '256MB'
effective_cache_size = '1GB'
work_mem = '4MB'
maintenance_work_mem = '64MB'
max_connections = 100
random_page_cost = 1.1

-- Restart PostgreSQL
sudo systemctl restart postgresql
```

#### **4.2 Índices Compostos (Já aplicados via Alembic)**

```sql
-- Verificar índices existentes
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Índices de performance implementados:
-- idx_appointments_business_status_date
-- idx_conversations_phone_date
-- idx_messages_conversation_timestamp
-- idx_users_email_active
-- idx_businesses_active_created
-- idx_webhooks_status_timestamp
```

#### **4.3 Backup Strategy**

```bash
# Backup automático (crontab)
0 2 * * * pg_dump $DATABASE_URL > /backup/whatsapp_agent_$(date +\%Y\%m\%d).sql

# Restore
psql $DATABASE_URL < backup_file.sql

# Verificar integridade
psql $DATABASE_URL -c "SELECT count(*) FROM appointments;"
```

---

## 🚀 **DEPLOYMENT EM PRODUÇÃO**

### **Railway Deploy (Recomendado)**

#### **5.1 Preparação**

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Criar projeto
railway init whatsapp-agent
```

#### **5.2 Configuração dos Serviços**

```bash
# Adicionar PostgreSQL
railway add postgresql

# Adicionar Redis
railway add redis

# Deploy do código
railway up
```

#### **5.3 Environment Variables (Railway)**

```bash
# Via Railway CLI
railway variables set JWT_SECRET_KEY=your-secret
railway variables set META_ACCESS_TOKEN=your-token
railway variables set WEBHOOK_SECRET=your-webhook-secret

# Via Dashboard Railway:
# Settings → Environment → Add Variable
```

#### **5.4 Custom Domain Setup**

```bash
# No Railway Dashboard:
# Settings → Domains → Custom Domain
# Add: yourdomain.com
# Configure DNS CNAME: www → railway-domain
```

### **VPS Deploy Manual**

#### **6.1 Server Setup (Ubuntu)**

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql redis-server nginx certbot python3-certbot-nginx

# Criar usuário para aplicação
sudo adduser whatsapp
sudo usermod -aG sudo whatsapp
```

#### **6.2 Aplicação Setup**

```bash
# Login como usuário da aplicação
sudo su - whatsapp

# Clone e setup
git clone https://github.com/VANCIMJOAO/wppagent.git
cd whats_agent

# Environment virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env (produção)
cp .env.example .env
nano .env
```

#### **6.3 Nginx Configuration**

```nginx
# /etc/nginx/sites-available/whatsapp-agent
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Webhook
    location /webhook {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        access_log off;
    }

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### **6.4 SSL Certificate**

```bash
# Instalar certificado SSL
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Verificar auto-renewal
sudo certbot renew --dry-run
```

#### **6.5 Systemd Services**

**Backend Service:**

```ini
# /etc/systemd/system/whatsapp-backend.service
[Unit]
Description=WhatsApp Agent Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=whatsapp
WorkingDirectory=/home/whatsapp/whats_agent
Environment=PATH=/home/whatsapp/whats_agent/venv/bin
ExecStart=/home/whatsapp/whats_agent/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Frontend Service:**

```ini
# /etc/systemd/system/whatsapp-frontend.service
[Unit]
Description=WhatsApp Agent Frontend
After=network.target

[Service]
Type=simple
User=whatsapp
WorkingDirectory=/home/whatsapp/whats_agent/nextjs_dashboard
Environment=PATH=/usr/bin:/bin
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Enable Services:**

```bash
sudo systemctl enable whatsapp-backend
sudo systemctl enable whatsapp-frontend
sudo systemctl start whatsapp-backend
sudo systemctl start whatsapp-frontend

# Verificar status
sudo systemctl status whatsapp-backend
sudo systemctl status whatsapp-frontend
```

---

## 🧪 **VERIFICAÇÃO E TESTES**

### **Health Checks**

```bash
# Backend health
curl https://yourdomain.com/health
# Expected: {"status":"healthy","timestamp":"...","version":"1.0.0"}

# Detailed health
curl https://yourdomain.com/health/detailed
# Verifica: database, redis, webhook, meta_api

# Frontend health
curl -I https://yourdomain.com/
# Expected: HTTP/2 200
```

### **Database Tests**

```bash
# Test database connection
python -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT version()'))
    print('✅ Database:', result.fetchone()[0])
"

# Test migrations
alembic current
alembic heads
# Should show single head: 6897816d7333
```

### **Redis Tests**

```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping
# Expected: PONG

# Test cache operations
python -c "
import redis
r = redis.from_url('$REDIS_URL')
r.set('test', 'value')
print('✅ Cache test:', r.get('test').decode())
r.delete('test')
"
```

### **WhatsApp Integration Tests**

```bash
# Test webhook endpoint
curl -X POST https://yourdomain.com/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"object":"whatsapp_business_account","entry":[{"id":"test","changes":[]}]}'

# Expected: Webhook signature validation (will fail with test signature, but endpoint should respond)
```

### **Frontend Tests**

```bash
# Test frontend pages
curl -s https://yourdomain.com/ | grep -q "WhatsApp Agent"
echo "✅ Frontend title found"

# Test API integration
curl -s https://yourdomain.com/api/health | jq .
# Should return health status in JSON
```

---

## 🔍 **TROUBLESHOOTING**

### **Common Issues**

#### **Database Connection Issues**

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# Test connection manually
psql $DATABASE_URL -c "SELECT 1"
```

#### **Redis Connection Issues**

```bash
# Check Redis status
sudo systemctl status redis-server

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Test connection
redis-cli -u $REDIS_URL ping
```

#### **Migration Issues**

```bash
# Check current migration
alembic current

# Check for multiple heads
alembic heads

# If multiple heads, merge them:
alembic merge heads -m "merge heads"
alembic upgrade head
```

#### **Meta API Issues**

```bash
# Test access token
curl -X GET "https://graph.facebook.com/v18.0/me?access_token=$META_ACCESS_TOKEN"

# Test phone number
curl -X GET "https://graph.facebook.com/v18.0/$META_PHONE_NUMBER_ID?access_token=$META_ACCESS_TOKEN"

# Check webhook subscription
curl -X GET "https://graph.facebook.com/v18.0/$META_APP_ID/subscriptions?access_token=$META_ACCESS_TOKEN"
```

### **Performance Monitoring**

```bash
# Backend performance
curl -w "%{time_total}s\n" -o /dev/null -s https://yourdomain.com/health

# Database performance
psql $DATABASE_URL -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"

# Redis performance
redis-cli -u $REDIS_URL --latency-history -i 1
```

---

## 📞 **SUPORTE**

### **Logs e Debugging**

```bash
# Application logs
tail -f logs/security_audit.log

# System logs
sudo journalctl -u whatsapp-backend -f
sudo journalctl -u whatsapp-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Contato**

- 📧 **Email**: <setup-support@whatsappagent.com>
- 🐛 **Issues**: [GitHub Issues](https://github.com/VANCIMJOAO/wppagent/issues)
- 📚 **Docs**: [Documentação Completa](../README.md)

---

## ✅ **CHECKLIST FINAL**

### **Development Setup**

- [ ] ✅ Python 3.11+ instalado
- [ ] ✅ Node.js 18+ instalado
- [ ] ✅ PostgreSQL 16+ configurado
- [ ] ✅ Redis 7+ configurado
- [ ] ✅ Dependencies instaladas (pip install -r requirements.txt)
- [ ] ✅ Dependencies instaladas (npm install)
- [ ] ✅ .env configurado
- [ ] ✅ Migrations aplicadas (alembic upgrade head)
- [ ] ✅ Health checks passando
- [ ] ✅ Frontend acessível
- [ ] ✅ API endpoints funcionando

### **Production Setup**

- [ ] ✅ Server configurado (Railway/VPS)
- [ ] ✅ Domain/SSL configurado
- [ ] ✅ Environment variables configuradas
- [ ] ✅ Database production configurado
- [ ] ✅ Redis production configurado
- [ ] ✅ Meta Business API configurada
- [ ] ✅ Webhook funcionando
- [ ] ✅ Nginx/Reverse proxy configurado
- [ ] ✅ SSL certificate ativo
- [ ] ✅ Systemd services configurados
- [ ] ✅ Monitoring ativo
- [ ] ✅ Backup strategy implementada

---

<div align="center">

**🚀 SETUP COMPLETO - SISTEMA PRONTO PARA PRODUÇÃO**

*Guia criado com ❤️ para garantir deploy perfeito*

</div>
