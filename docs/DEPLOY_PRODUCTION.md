# 🚀 Guia de Deploy em Produção - WhatsApp Agent

## 📋 Pré-requisitos

### Servidor
- **SO**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: Mínimo 4GB (recomendado 8GB+)
- **CPU**: 2 cores mínimo (recomendado 4+)
- **Disco**: 50GB+ espaço livre
- **Rede**: Portas 80, 443, 22 abertas

### Software
- Docker 20.10+
- Docker Compose 2.0+
- Git
- OpenSSL

## 🔧 Configuração Inicial

### 1. Clone e Configuração

```bash
# Clone o repositório
git clone <seu-repositorio> whatsapp-agent
cd whatsapp-agent

# Copiar configuração de produção
cp .env.production .env

# Editar configurações
nano .env
```

### 2. Configurar Variáveis Essenciais

**Banco de Dados:**
```env
DB_PASSWORD=SENHA_MUITO_SEGURA_123!@#
```

**WhatsApp API:**
```env
META_ACCESS_TOKEN=EAAxxxxx...
PHONE_NUMBER_ID=123456789
WEBHOOK_VERIFY_TOKEN=TOKEN_WEBHOOK_SEGURO
```

**Segurança:**
```env
SECRET_KEY=chave-jwt-64-caracteres-minimo-super-segura-para-producao
ADMIN_PASSWORD=SENHA_ADMIN_MUITO_SEGURA
```

## 🌐 Configuração de Domínio

### 1. DNS
Configure seu domínio para apontar para o servidor:
```
A     seu-dominio.com     → IP_DO_SERVIDOR
CNAME dashboard           → seu-dominio.com
CNAME grafana            → seu-dominio.com
```

### 2. SSL com Let's Encrypt
```bash
# Para domínio real em produção
./scripts/setup_letsencrypt.sh seu-dominio.com admin@seu-dominio.com
```

## 🚀 Deploy

### Método 1: Deploy Automatizado
```bash
# Deploy completo com SSL
./deploy_production.sh
```

### Método 2: Deploy Manual
```bash
# Gerar certificados SSL (desenvolvimento)
./scripts/generate_ssl_certs.sh

# Construir e iniciar
docker-compose build
docker-compose up -d

# Verificar status
docker-compose ps
docker-compose logs -f
```

## 📊 Verificação Pós-Deploy

### 1. Health Checks
```bash
# API
curl -k https://seu-dominio.com/health

# Dashboard
curl -k https://seu-dominio.com/dashboard/

# Banco de dados
docker-compose exec postgres psql -U whatsapp_user -d whatsapp_agent -c "SELECT 1;"
```

### 2. URLs Disponíveis
- **API**: `https://seu-dominio.com/api/`
- **Dashboard**: `https://seu-dominio.com/dashboard/`
- **Docs**: `https://seu-dominio.com/docs`
- **Prometheus**: `http://seu-dominio.com:9090`
- **Grafana**: `http://seu-dominio.com:3000`

## 🔒 Segurança em Produção

### 1. Firewall
```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=22/tcp
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### 2. Atualizações
```bash
# Criar script de atualização
cat > update.sh << 'EOF'
#!/bin/bash
git pull
docker-compose build --no-cache
docker-compose up -d
EOF

chmod +x update.sh
```

### 3. Backup Automático
```bash
# Configurar cron para backup
crontab -e

# Adicionar linha para backup diário às 2h
0 2 * * * cd /path/to/whatsapp-agent && ./backups/database/backup_script.sh full_backup
```

## 📈 Monitoramento

### 1. Logs
```bash
# Ver logs em tempo real
docker-compose logs -f

# Logs específicos
docker-compose logs -f app
docker-compose logs -f nginx
docker-compose logs -f postgres
```

### 2. Métricas
- **Prometheus**: Monitor de sistema e aplicação
- **Grafana**: Dashboards visuais
- **Health Checks**: Endpoints automáticos

### 3. Alertas
Configure alertas no Grafana para:
- Alto uso de CPU/RAM
- Erros de API
- Falhas de banco de dados
- SSL expirado

## 🔧 Manutenção

### Comandos Úteis
```bash
# Reiniciar serviços
docker-compose restart

# Atualizar apenas a aplicação
docker-compose up -d --no-deps app

# Backup manual
./backups/database/backup_script.sh full_backup

# Restaurar backup
./backups/database/restore_script.sh backup_20240808.sql.gz

# Ver uso de recursos
docker stats

# Limpar logs antigos
docker system prune -f
```

### Troubleshooting

**Problema**: Container não inicia
```bash
# Verificar logs
docker-compose logs container_name

# Verificar recursos
df -h
free -h
```

**Problema**: SSL não funciona
```bash
# Verificar certificados
openssl x509 -in config/nginx/ssl/server.crt -text -noout

# Testar configuração nginx
docker-compose exec nginx nginx -t
```

**Problema**: Database connection failed
```bash
# Verificar se postgres está rodando
docker-compose exec postgres psql -U whatsapp_user -d whatsapp_agent -c "SELECT version();"

# Verificar variáveis de ambiente
docker-compose exec app env | grep DB_
```

## 🔄 Rotina de Manutenção

### Diária
- [ ] Verificar logs de erro
- [ ] Confirmar backup automático
- [ ] Monitorar métricas de performance

### Semanal
- [ ] Atualizar sistema operacional
- [ ] Verificar espaço em disco
- [ ] Revisar alertas do Grafana

### Mensal
- [ ] Atualizar dependências
- [ ] Testar procedimento de restore
- [ ] Revisar configurações de segurança
- [ ] Verificar validade do SSL

## 📞 Suporte

Para problemas ou dúvidas:
1. Verificar logs primeiro
2. Consultar documentação da API
3. Revisar configurações
4. Contatar suporte técnico

## 🚨 Cenários de Emergência

### Aplicação Down
```bash
# Restart rápido
docker-compose restart app

# Se persistir
docker-compose down
docker-compose up -d
```

### Banco Corrompido
```bash
# Restaurar último backup
./backups/database/restore_script.sh latest
```

### SSL Expirado
```bash
# Renovar Let's Encrypt
certbot renew --force-renewal
docker-compose restart nginx
```

### Falta de Espaço
```bash
# Limpar Docker
docker system prune -a -f

# Limpar logs antigos
find logs/ -name "*.log" -mtime +30 -delete
```
