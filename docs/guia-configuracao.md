# 🚀 Guia de Configuração - WhatsApp Agent

> **Guia completo de instalação e configuração** com instruções detalhadas para desenvolvimento, staging e produção usando Docker, configuração manual e deploy em cloud.

---

## 🎯 **VISÃO GERAL**

### **Pré-requisitos do Sistema** 📋

#### **Requisitos Mínimos**
- **Sistema Operacional**: Ubuntu 20.04+ / CentOS 8+ / macOS 12+ / Windows 11 WSL2
- **Docker**: 20.10+ com Docker Compose 2.0+
- **Python**: 3.11+ (se instalação manual)
- **Node.js**: 18+ (para dashboard)
- **Memória RAM**: 4GB (desenvolvimento) / 8GB+ (produção)
- **Armazenamento**: 20GB disponível
- **Rede**: HTTPS obrigatório em produção

#### **Contas e APIs Necessárias**
- ✅ **Meta for Developers** - Conta verificada para WhatsApp Business API
- ✅ **PostgreSQL** - Banco de dados (local ou cloud)
- ✅ **Redis** - Cache (local ou cloud)
- ✅ **Domínio com SSL** - Para webhook e produção

---

## 🐳 **INSTALAÇÃO COM DOCKER (RECOMENDADO)**

### **Método 1: Deploy Rápido**

#### **1. Clone do Repositório**
```bash
# Clone do projeto
git clone https://github.com/VANCIMJOAO/wppagent.git
cd wppagent

# Verificar arquivos necessários
ls -la docker-compose.yml Dockerfile .env.example
```

#### **2. Configuração de Ambiente**
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar variáveis de ambiente
nano .env
```

**Configuração `.env` essencial:**
```env
# === CONFIGURAÇÃO DO BANCO DE DADOS ===
DATABASE_URL=postgresql://postgres:senha_segura@db:5432/whatsapp_agent
POSTGRES_DB=whatsapp_agent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=senha_segura_123

# === CONFIGURAÇÃO DO REDIS ===
REDIS_URL=redis://redis:6379/0

# === CONFIGURAÇÃO JWT ===
JWT_SECRET_KEY=sua_chave_jwt_super_secreta_com_32_caracteres_minimo
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# === META WHATSAPP API ===
META_ACCESS_TOKEN=sua_meta_access_token_aqui
META_PHONE_NUMBER_ID=seu_phone_number_id
META_APP_ID=seu_app_id
META_APP_SECRET=seu_app_secret
WEBHOOK_VERIFY_TOKEN=token_verificacao_webhook
WEBHOOK_SECRET=chave_secreta_webhook

# === CONFIGURAÇÃO DO SERVIDOR ===
HOST=0.0.0.0
PORT=8000
WORKERS=4
RELOAD=false
ENVIRONMENT=production

# === CONFIGURAÇÃO FRONTEND ===
NEXT_PUBLIC_API_URL=https://seu-dominio.com
NEXTAUTH_SECRET=sua_chave_nextauth_secreta
NEXTAUTH_URL=https://seu-dominio.com
```

#### **3. Deploy com Docker Compose**
```bash
# Iniciar todos os serviços
docker-compose up -d

# Verificar status dos containers
docker-compose ps

# Acompanhar logs
docker-compose logs -f whatsapp-backend
```

#### **4. Verificação da Instalação**
```bash
# Teste de saúde da API
curl http://localhost:8000/health

# Resposta esperada:
# {"status":"healthy","timestamp":"2024-01-15T10:30:00Z"}

# Teste do frontend
curl http://localhost:3000

# Verificar logs
docker-compose logs whatsapp-backend | tail -20
```

### **Método 2: Configuração Avançada**

#### **Docker Compose Customizado**
```yaml
# docker-compose.production.yml
version: '3.8'
services:
  whatsapp-backend:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@external-db:5432/whatsapp_agent
      - REDIS_URL=redis://external-redis:6379/0
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  whatsapp-frontend:
    build: ./nextjs_dashboard
    environment:
      - NEXT_PUBLIC_API_URL=https://api.seu-dominio.com
    ports:
      - "3000:3000"
    depends_on:
      - whatsapp-backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx:/etc/nginx/conf.d
      - ./ssl:/etc/ssl/certs
    depends_on:
      - whatsapp-backend
      - whatsapp-frontend
```

---

## 🔧 **INSTALAÇÃO MANUAL**

### **1. Preparação do Ambiente**

#### **Ubuntu/Debian**
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql-14 redis-server git curl

# Configurar Python 3.11 como padrão
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

#### **CentOS/RHEL**
```bash
# Instalar EPEL repository
sudo dnf install -y epel-release

# Instalar dependências
sudo dnf install -y python3.11 python3-pip nodejs npm postgresql14-server redis git curl

# Inicializar PostgreSQL
sudo postgresql-setup --initdb
sudo systemctl enable postgresql redis
sudo systemctl start postgresql redis
```

### **2. Configuração do Banco de Dados**

#### **PostgreSQL Setup**
```bash
# Conectar como usuário postgres
sudo -u postgres psql

-- Criar usuário e banco
CREATE USER whatsapp_agent WITH PASSWORD 'senha_segura_123';
CREATE DATABASE whatsapp_agent OWNER whatsapp_agent;
GRANT ALL PRIVILEGES ON DATABASE whatsapp_agent TO whatsapp_agent;

-- Configurar extensões necessárias
\c whatsapp_agent
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

\q
```

#### **Configuração PostgreSQL**
```bash
# Editar postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Configurações recomendadas:
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### **3. Instalação da Aplicação**

#### **Backend (FastAPI)**
```bash
# Clone e setup
git clone https://github.com/VANCIMJOAO/wppagent.git
cd wppagent

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
nano .env

# Executar migrações
alembic upgrade head

# Testar aplicação
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### **Frontend (Next.js)**
```bash
# Navegar para pasta do frontend
cd nextjs_dashboard

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.example .env.local
nano .env.local

# Configurações necessárias:
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=sua_chave_secreta_aqui
NEXTAUTH_URL=http://localhost:3000

# Build e iniciar
npm run build
npm run start
```

---

## 🌐 **CONFIGURAÇÃO META WHATSAPP API**

### **1. Configuração no Meta for Developers**

#### **Criar Aplicação WhatsApp Business**
1. Acesse [Meta for Developers](https://developers.facebook.com)
2. Criar nova aplicação → **Business** → **WhatsApp Business Platform**
3. Adicionar produto **WhatsApp** à aplicação

#### **Configurar Webhook**
```
URL do Webhook: https://seu-dominio.com/webhook
Token de Verificação: seu_token_verificacao_webhook
Campos de Assinatura: messages, message_deliveries, message_reads
```

#### **Obter Credenciais**
```bash
# Necessário configurar no .env:
META_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
META_PHONE_NUMBER_ID=123456789012345
META_APP_ID=1234567890123456
META_APP_SECRET=abcdef123456789
WEBHOOK_VERIFY_TOKEN=meu_token_verificacao
WEBHOOK_SECRET=minha_chave_secreta_webhook
```

### **2. Teste da Integração**
```bash
# Testar webhook
curl -X GET "https://seu-dominio.com/webhook?hub.mode=subscribe&hub.challenge=123456&hub.verify_token=seu_token"

# Testar envio de mensagem
curl -X POST "https://graph.facebook.com/v18.0/SEU_PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer SEU_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "5511999999999",
    "type": "text",
    "text": {"body": "Olá! Esta é uma mensagem de teste."}
  }'
```

---

## 🚀 **DEPLOY EM PRODUÇÃO**

### **1. Railway (Recomendado)**

#### **Deploy Automático**
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login e setup
railway login
railway init

# Deploy
railway up

# Configurar variáveis de ambiente
railway variables set DATABASE_URL=postgresql://...
railway variables set REDIS_URL=redis://...
railway variables set META_ACCESS_TOKEN=...
```

#### **Configuração Railway**
```json
{
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "restartPolicyType": "on-failure",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

### **2. AWS/DigitalOcean**

#### **Servidor VPS Setup**
```bash
# Conectar ao servidor
ssh root@seu-servidor

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone e deploy
git clone https://github.com/VANCIMJOAO/wppagent.git
cd wppagent

# Configurar .env com valores de produção
cp .env.example .env
nano .env

# Deploy com Docker Compose
docker-compose -f docker-compose.production.yml up -d
```

### **3. Nginx Reverse Proxy**

#### **Configuração Nginx**
```nginx
# /etc/nginx/sites-available/whatsapp-agent
server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    ssl_certificate /etc/ssl/certs/seu-dominio.com.crt;
    ssl_certificate_key /etc/ssl/private/seu-dominio.com.key;

    # API Backend
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 🔍 **VERIFICAÇÃO E TESTES**

### **1. Health Checks**
```bash
# API Health
curl https://seu-dominio.com/health

# Resposta esperada:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "meta_api": "healthy"
  }
}

# Health detalhado (necessário login admin)
curl -X GET https://seu-dominio.com/health/detailed \
  -H "Authorization: Bearer SEU_TOKEN"
```

### **2. Testes de Funcionalidade**
```bash
# Teste de autenticação
curl -X POST https://seu-dominio.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"senha"}'

# Teste de agendamento
curl -X POST https://seu-dominio.com/appointments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "user_id": 1,
    "phone_number": "+5511999999999",
    "appointment_date": "2024-01-20",
    "appointment_time": "14:30:00"
  }'

# Teste de webhook
curl -X POST https://seu-dominio.com/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=assinatura" \
  -d '{"test": "webhook"}'
```

### **3. Performance Tests**
```bash
# Teste de carga com Apache Bench
ab -n 1000 -c 10 https://seu-dominio.com/health

# Teste de response time
curl -w "@curl-format.txt" -o /dev/null -s https://seu-dominio.com/health

# Formato curl-format.txt:
#     time_namelookup:  %{time_namelookup}\n
#      time_connect:  %{time_connect}\n
#   time_appconnect:  %{time_appconnect}\n
#  time_pretransfer:  %{time_pretransfer}\n
#     time_redirect:  %{time_redirect}\n
#time_starttransfer:  %{time_starttransfer}\n
#                   ----------\n
#        time_total:  %{time_total}\n
```

---

## 🔧 **TROUBLESHOOTING**

### **Problemas Comuns**

#### **Erro de Conexão com Banco**
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
psql -h localhost -U whatsapp_agent -d whatsapp_agent

# Verificar logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

#### **Erro de Webhook**
```bash
# Verificar certificado SSL
curl -I https://seu-dominio.com/webhook

# Testar webhook localmente
ngrok http 8000
# Usar URL do ngrok no Meta for Developers temporariamente
```

#### **Performance Issues**
```bash
# Verificar recursos do sistema
htop
df -h
free -h

# Verificar logs da aplicação
tail -f logs/security_audit.log | jq '.'

# Verificar cache Redis
redis-cli -u $REDIS_URL info stats
```

---

## 🛡️ **CONFIGURAÇÕES DE SEGURANÇA**

### **1. Firewall**
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable

# Bloquear acesso direto às portas da aplicação
sudo ufw deny 8000
sudo ufw deny 3000
```

### **2. SSL/TLS**
```bash
# Instalar Certbot (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Configurar renovação automática
sudo crontab -e
# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

### **3. Backup Automático**
```bash
# Script de backup do banco
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://seu-bucket/backups/

# Configurar cron para backup diário
0 2 * * * /path/to/backup.sh
```

---

## 📞 **SUPORTE**

### **Recursos de Ajuda**
- 📖 **Documentação Completa**: `docs/`
- 🔧 **Troubleshooting**: `docs/troubleshooting.md`
- 🛡️ **Segurança**: `docs/security-practices.md`
- ⚡ **Performance**: `docs/performance-optimization.md`

### **Contatos**
- 📧 **Suporte Técnico**: suporte@whatsappagent.com
- 💬 **Chat de Suporte**: https://whatsappagent.com/chat
- 🐛 **Report de Bugs**: https://github.com/VANCIMJOAO/wppagent/issues

---

<div align="center">

**🚀 CONFIGURAÇÃO ENTERPRISE COMPLETA**

*Guia definitivo para instalação e deploy em produção*

**Tempo de Setup: <30min** | **Uptime: 99.9%** | **Suporte 24/7**

</div>