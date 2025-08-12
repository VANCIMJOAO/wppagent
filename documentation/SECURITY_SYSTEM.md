# 🔒 Sistema de Autenticação e Autorização - WhatsApp Agent

## 📋 Visão Geral

Sistema completo de segurança implementado com as seguintes funcionalidades:

### ✅ Funcionalidades Implementadas

- **🚫 Revogação de Tokens**: Todos os tokens expostos foram revogados
- **🔐 Secrets Manager**: Gerenciamento seguro com rotação automática  
- **🔑 2FA Obrigatório**: Autenticação de dois fatores para administradores
- **🔄 JWT com Rotação**: Tokens JWT com rotação automática de secrets
- **🚦 Rate Limiting**: Proteção rigorosa contra ataques DDoS

## 🏗️ Arquitetura

### Componentes Principais

1. **JWT Manager** (`app/auth/jwt_manager.py`)
   - Geração e verificação de tokens
   - Rotação automática de secrets
   - Blacklist de tokens revogados
   - Suporte a access e refresh tokens

2. **Two-Factor Auth** (`app/auth/two_factor.py`)
   - TOTP (Time-based One-Time Password)
   - Códigos de backup
   - QR Code para configuração
   - Bloqueio por tentativas falhadas

3. **Rate Limiter** (`app/auth/rate_limiter.py`)
   - Múltiplas camadas (IP, User, Endpoint, Global)
   - Proteção DDoS
   - Sliding window algorithm
   - Bloqueios temporários

4. **Secrets Manager** (`app/auth/secrets_manager.py`)
   - Armazenamento criptografado
   - Versionamento de secrets
   - Rotação automática
   - Auditoria completa

5. **Auth Middleware** (`app/auth/middleware.py`)
   - Integração de todos os componentes
   - Verificação automática
   - Headers de segurança
   - Autorização baseada em roles

## 🚀 Instalação e Configuração

### 1. Executar Script de Configuração

```bash
# Executar configuração completa
./setup_security.sh
```

### 2. Instalar Dependências Manualmente (se necessário)

```bash
pip install PyJWT cryptography pyotp qrcode[pil] email-validator
```

### 3. Configurar Variáveis de Ambiente

```bash
# Arquivo .env.security (criado automaticamente)
SECURITY_LEVEL=high
JWT_SECRET_ROTATION_HOURS=24
RATE_LIMITING_ENABLED=true
FORCE_2FA_FOR_ADMINS=true
```

## 🔐 Configuração de 2FA

### Para Administradores

1. **Login inicial**:
   ```bash
   POST /auth/login
   {
     "username": "admin",
     "password": "sua_senha"
   }
   ```

2. **Configurar 2FA**:
   ```bash
   POST /auth/2fa/setup
   # Retorna QR code e secret
   ```

3. **Confirmar 2FA**:
   ```bash
   POST /auth/2fa/confirm
   {
     "code": "123456"
   }
   # Retorna códigos de backup
   ```

4. **Login com 2FA**:
   ```bash
   POST /auth/2fa/verify
   {
     "code": "123456",
     "type": "totp"  # ou "backup"
   }
   ```

## 🚦 Rate Limiting

### Configurações por Tipo

#### Por IP
- **Padrão**: 100 req/min (block 5min)
- **Auth**: 10 req/min (block 15min)  
- **Admin**: 5 req/min (block 30min)

#### Por Usuário
- **Padrão**: 500 req/min (block 1min)
- **Admin**: 1000 req/min (block 30s)
- **Upload**: 10 uploads/5min (block 10min)

#### Por Endpoint
- `/auth/login`: 5 req/5min
- `/auth/2fa`: 10 req/5min  
- `/webhook`: 1000 req/min
- `/admin/*`: 100 req/min

#### Global
- **Total**: 10k req/min
- **Auth**: 1k auth/min

### Proteção DDoS
- **Threshold**: 1000 req/min por IP
- **Bloqueio**: 1 hora
- **Detecção**: Automática com logs

## 🔄 Gerenciamento de Secrets

### Tipos de Secrets

- `JWT_SECRET`: Rotação diária
- `WEBHOOK_SECRET`: Rotação mensal  
- `API_KEY`: Rotação trimestral
- `WHATSAPP_TOKEN`: Rotação semestral
- `ADMIN_PASSWORD`: Rotação mensal

### Operações Principais

#### Criar Secret
```bash
POST /secrets/create
{
  "secret_id": "my_secret",
  "secret_type": "api_key",
  "value": "optional_custom_value"
}
```

#### Rotacionar Secret
```bash
POST /secrets/my_secret/rotate
{
  "new_value": "optional_new_value"
}
```

#### Listar Secrets
```bash
GET /secrets/list?secret_type=jwt_secret
```

#### Obter Valor (SENSÍVEL)
```bash
GET /secrets/my_secret/value
# Registra auditoria
```

### Rotação Automática

```bash
# Script diário (cron)
0 2 * * * cd /path/to/whats_agent && python3 tools/rotate_secrets.py

# Rotação manual
python3 tools/rotate_secrets.py

# Verificar expirações
GET /secrets/expiring/check?days_ahead=7
```

## 🛡️ Endpoints de Segurança

### Autenticação
- `POST /auth/login` - Login básico
- `POST /auth/2fa/setup` - Configurar 2FA
- `POST /auth/2fa/confirm` - Confirmar 2FA  
- `POST /auth/2fa/verify` - Verificar 2FA
- `POST /auth/refresh` - Renovar tokens
- `POST /auth/revoke` - Revogar tokens
- `GET /auth/status` - Status da autenticação

### Secrets Management
- `POST /secrets/create` - Criar secret
- `GET /secrets/list` - Listar secrets
- `GET /secrets/{id}` - Info do secret
- `GET /secrets/{id}/value` - Valor do secret (AUDIT)
- `POST /secrets/{id}/rotate` - Rotacionar secret
- `DELETE /secrets/{id}` - Revogar secret

### Monitoramento  
- `GET /auth/rate-limit/status` - Status rate limiting
- `GET /auth/security/events` - Eventos de segurança
- `GET /secrets/audit/all` - Log de auditoria

### Emergência
- `POST /auth/revoke-all` - Revogar TODOS os tokens
- `POST /secrets/emergency/revoke-all` - Revogar TODOS os secrets

## 📊 Monitoramento

### Scripts de Monitoramento

```bash
# Relatório de segurança
python3 tools/security_monitor.py

# Status dos secrets
python3 tools/rotate_secrets.py

# Verificar rate limiting
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/auth/rate-limit/status
```

### Logs de Auditoria

- **JWT**: Criação, verificação, revogação
- **2FA**: Setup, verificação, tentativas falhadas
- **Secrets**: Criação, rotação, acesso, revogação
- **Rate Limit**: Bloqueios, DDoS, suspeitas

### Métricas Redis

```bash
# Verificar no Redis
redis-cli keys "*auth*"
redis-cli keys "*secrets*"
redis-cli keys "*rate*"
redis-cli keys "*2fa*"
```

## 🚨 Procedimentos de Emergência

### Comprometimento de Tokens

1. **Revogar todos os tokens**:
   ```bash
   POST /auth/revoke-all
   # Headers: Authorization: Bearer $ADMIN_TOKEN
   ```

2. **Rotacionar JWT secret**:
   ```bash
   POST /secrets/jwt_secret/rotate
   ```

### Comprometimento de Secrets

1. **Revogar todos os secrets**:
   ```bash
   POST /secrets/emergency/revoke-all
   {
     "confirm": "EMERGENCY_REVOKE_ALL_SECRETS"
   }
   ```

2. **Recriar secrets essenciais**:
   ```bash
   ./setup_security.sh
   ```

### Ataque DDoS

1. **Verificar bloqueios**:
   ```bash
   GET /auth/security/events
   ```

2. **Desbloquear IP específico**:
   ```bash
   # Via Redis
   redis-cli del "blocked:ip:1.2.3.4"
   ```

## 🔒 Boas Práticas

### Para Desenvolvedores

1. **Sempre usar HTTPS** em produção
2. **Nunca logar tokens** ou secrets
3. **Verificar autorização** em todos os endpoints
4. **Implementar timeout** apropriado
5. **Validar input** rigorosamente

### Para Administradores

1. **Habilitar 2FA** imediatamente
2. **Monitorar logs** regularmente  
3. **Rotacionar secrets** periodicamente
4. **Backup códigos** de recuperação
5. **Documentar incidentes** de segurança

### Para Produção

1. **Configurar alertas** automáticos
2. **Backup regular** do Redis
3. **Monitoramento** 24/7
4. **Testes de penetração** regulares
5. **Auditoria** mensal de acessos

## 📈 Métricas de Segurança

### KPIs Importantes

- **Taxa de bloqueios** por rate limiting
- **Tentativas de 2FA** falhadas
- **Acessos a secrets** sensíveis  
- **Rotações automáticas** realizadas
- **Eventos de DDoS** detectados

### Dashboards

- **Grafana**: Métricas em tempo real
- **Logs**: Auditoria centralizada
- **Alertas**: Notificações automáticas
- **Relatórios**: Análise semanal/mensal

## 🆘 Suporte e Troubleshooting

### Problemas Comuns

1. **Token expirado**: Usar refresh token
2. **2FA bloqueado**: Usar código de backup
3. **Rate limit**: Aguardar período de reset
4. **Secret não encontrado**: Verificar rotação

### Logs Importantes

```bash
# Logs de aplicação
tail -f logs/app.log | grep -i auth

# Logs do Redis  
redis-cli monitor | grep -i auth

# Eventos de segurança
redis-cli lrange security:events 0 10
```

### Contatos de Emergência

- **Administrador**: admin@whatsapp-agent.com
- **Segurança**: security@whatsapp-agent.com  
- **Suporte**: support@whatsapp-agent.com

---

## ⚡ Quick Start

```bash
# 1. Configurar sistema
./setup_security.sh

# 2. Login como admin
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")"}'

# 3. Configurar 2FA
curl -X POST http://localhost:8000/auth/2fa/setup \
  -H "Authorization: Bearer $TOKEN"

# 4. Verificar status
curl -X GET http://localhost:8000/auth/status \
  -H "Authorization: Bearer $TOKEN"
```

🎉 **Sistema de segurança pronto para produção!**
