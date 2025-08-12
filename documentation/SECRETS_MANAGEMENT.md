# 🔐 Sistema de Secrets Management

## Visão Geral

O WhatsApp Agent implementa um sistema robusto de gerenciamento de secrets com múltiplos provedores:

- **HashiCorp Vault** (produção)
- **Docker Secrets** (containers)
- **Environment Variables** (desenvolvimento)

## Configuração Rápida

### 1. Desenvolvimento Local
```bash
# Usar apenas environment variables
export ENVIRONMENT=development
python validate_secrets.py
```

### 2. Com Docker Secrets
```bash
# Criar secrets
./create_secrets.sh

# Executar com docker-compose
docker-compose -f docker-compose.secrets.yml up
```

### 3. Com HashiCorp Vault
```bash
# Iniciar Vault dev
./start_vault_dev.sh

# Em outro terminal
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=root
export USE_VAULT=true

python validate_secrets.py
```

## Estrutura do Sistema

### Hierarquia de Provedores
1. **Vault** (prioritário em produção)
2. **Docker Secrets** (containers)
3. **Environment Variables** (fallback)

### Secrets Suportados
- `database_password` - Senha do PostgreSQL
- `openai_api_key` - Chave da API OpenAI
- `meta_access_token` - Token Meta/WhatsApp
- `webhook_verify_token` - Token de verificação
- `jwt_secret` - Secret para JWT

## Uso na Aplicação

```python
from app.config.secure_config import get_config

# Obter configuração
config = get_config()

# Acessar secrets
db_url = config.get('database_url')
api_key = config.get('openai_api_key')
```

## Monitoramento

### Health Check
```bash
curl http://localhost:8000/health/secrets
```

### Status da Configuração
```bash
curl http://localhost:8000/health/config
```

## Segurança

- ✅ Nenhum secret em código fonte
- ✅ Rotação automática (Vault)
- ✅ Cache com TTL configurável
- ✅ Logs de auditoria
- ✅ Fallback seguro

## Comandos Úteis

```bash
# Validar sistema
./validate_secrets.py

# Criar Docker secrets
./create_secrets.sh

# Iniciar Vault dev
./start_vault_dev.sh

# Ver status
python -c "
import asyncio
from app.config.secure_config import config_manager
asyncio.run(config_manager.health_check())
"
```
