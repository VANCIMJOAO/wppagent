#!/bin/bash

# Setup Secrets Management para WhatsApp Agent
# Configuração automática do sistema de secrets

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[SETUP]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════╗"
echo "║    🔐 SECRETS MANAGEMENT SETUP      ║"
echo "║        WhatsApp Agent v1.0           ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# Verificar dependências
log "Verificando dependências..."

# Python
if ! command -v python &> /dev/null; then
    error "Python não encontrado"
    exit 1
fi

# Verificar pip packages
python -c "import hvac" 2>/dev/null || {
    warn "hvac não instalado, instalando..."
    pip install hvac
}

log "✅ Dependências verificadas"

# Criar estrutura de diretórios
log "Criando estrutura de diretórios..."

mkdir -p /home/vancim/whats_agent/secrets/{vault,docker,backup}
mkdir -p /home/vancim/whats_agent/config/secrets
mkdir -p /home/vancim/whats_agent/logs/security

log "✅ Estrutura criada"

# Configurar Docker Secrets (se Docker disponível)
if command -v docker &> /dev/null; then
    log "Configurando Docker Secrets..."
    
    # Criar network se não existir
    docker network ls | grep -q whats_agent || docker network create whats_agent
    
    # Template docker-compose.secrets.yml
    cat > /home/vancim/whats_agent/docker-compose.secrets.yml << 'EOF'
version: '3.8'

services:
  whats_agent:
    image: whats_agent:latest
    networks:
      - whats_agent
    secrets:
      - database_password
      - openai_api_key
      - meta_access_token
      - webhook_verify_token
      - jwt_secret
    environment:
      - ENVIRONMENT=production
      - USE_DOCKER_SECRETS=true
    volumes:
      - ./logs:/app/logs
    ports:
      - "8000:8000"

secrets:
  database_password:
    external: true
  openai_api_key:
    external: true
  meta_access_token:
    external: true
  webhook_verify_token:
    external: true
  jwt_secret:
    external: true

networks:
  whats_agent:
    external: true
EOF

    # Script para criar secrets
    cat > /home/vancim/whats_agent/create_secrets.sh << 'EOF'
#!/bin/bash

# Criar Docker Secrets para WhatsApp Agent

echo "🔐 Criando Docker Secrets..."

# Função para criar secret
create_secret() {
    local name=$1
    local description=$2
    
    echo -n "Digite o valor para $description: "
    read -s value
    echo
    
    echo "$value" | docker secret create "$name" - || {
        echo "⚠️ Secret $name já existe ou erro na criação"
    }
}

# Criar secrets
create_secret "database_password" "senha do banco de dados"
create_secret "openai_api_key" "chave da API OpenAI"
create_secret "meta_access_token" "token de acesso Meta/WhatsApp"
create_secret "webhook_verify_token" "token de verificação webhook"
create_secret "jwt_secret" "secret JWT"

echo "✅ Docker Secrets criados"
EOF

    chmod +x /home/vancim/whats_agent/create_secrets.sh
    
    log "✅ Docker Secrets configurado"
    info "Execute ./create_secrets.sh para criar os secrets"
else
    warn "Docker não encontrado, pulando configuração Docker Secrets"
fi

# Configurar HashiCorp Vault (desenvolvimento)
log "Configurando Vault de desenvolvimento..."

cat > /home/vancim/whats_agent/start_vault_dev.sh << 'EOF'
#!/bin/bash

# Iniciar HashiCorp Vault em modo desenvolvimento

echo "🔐 Iniciando Vault em modo desenvolvimento..."

# Verificar se Vault está instalado
if ! command -v vault &> /dev/null; then
    echo "⚠️ Vault não encontrado. Instalando..."
    
    # Download Vault
    curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
    sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
    sudo apt-get update && sudo apt-get install vault
fi

# Iniciar Vault dev server
vault server -dev -dev-root-token-id="root" -dev-listen-address="0.0.0.0:8200" &

VAULT_PID=$!
echo "🔐 Vault iniciado (PID: $VAULT_PID)"
echo "🌐 Vault UI: http://localhost:8200"
echo "🔑 Root Token: root"

# Configurar ambiente
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'

# Aguardar Vault inicializar
sleep 5

# Habilitar engines de secrets
vault auth enable userpass
vault secrets enable -path=database kv-v2
vault secrets enable -path=apis kv-v2
vault secrets enable -path=whatsapp kv-v2
vault secrets enable -path=general kv-v2

echo "✅ Vault configurado"
echo "💡 Execute 'export VAULT_ADDR=http://127.0.0.1:8200 && export VAULT_TOKEN=root' para usar o Vault"

# Aguardar sinal para parar
wait $VAULT_PID
EOF

chmod +x /home/vancim/whats_agent/start_vault_dev.sh

log "✅ Vault configurado"

# Configuração de ambiente
log "Criando configuração de ambiente..."

cat > /home/vancim/whats_agent/.env.secrets << 'EOF'
# Configuração do Sistema de Secrets
# Este arquivo contém apenas configurações de secrets management

# Ambiente de execução
ENVIRONMENT=development

# Configurações de Secrets Management
USE_VAULT=false
USE_DOCKER_SECRETS=false
SECRETS_CACHE_TTL=300

# Vault Configuration (desenvolvimento)
VAULT_URL=http://127.0.0.1:8200
VAULT_TOKEN=root
VAULT_MOUNT_POINT=secret

# Docker Secrets Path
DOCKER_SECRETS_PATH=/run/secrets

# Backup de Secrets
SECRETS_BACKUP_ENABLED=true
SECRETS_BACKUP_PATH=/home/vancim/whats_agent/secrets/backup

# Logging de Segurança
SECURITY_LOG_LEVEL=INFO
SECURITY_LOG_FILE=/home/vancim/whats_agent/logs/security/secrets.log
EOF

log "✅ Configuração de ambiente criada"

# Script de validação
log "Criando script de validação..."

cat > /home/vancim/whats_agent/validate_secrets.py << 'EOF'
#!/usr/bin/env python3
"""
Validação do Sistema de Secrets Management
"""
import asyncio
import sys
import os

# Adicionar diretório do projeto ao Python path
sys.path.append('/home/vancim/whats_agent')

async def validate_secrets():
    """Validar sistema de secrets"""
    try:
        print("🔐 Validando Sistema de Secrets...")
        
        # Importar módulos
        from app.services.secrets_manager import secrets_manager
        from app.config.secure_config import config_manager
        
        # Testar inicialização
        print("📋 Testando inicialização...")
        success = await config_manager.load_configuration()
        
        if success:
            print("✅ Configuração carregada com sucesso")
            
            # Status dos provedores
            status = secrets_manager.get_provider_status()
            print(f"📊 Provedores ativos: {list(status['providers'].keys())}")
            
            # Health check
            health = await config_manager.health_check()
            print(f"🏥 Status geral: {health['status']}")
            
            if health['issues']:
                print("⚠️ Problemas encontrados:")
                for issue in health['issues']:
                    print(f"   - {issue}")
        
        else:
            print("❌ Falha na inicialização")
            return False
        
        print("✅ Validação concluída com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            await secrets_manager.close()
        except:
            pass

if __name__ == "__main__":
    result = asyncio.run(validate_secrets())
    sys.exit(0 if result else 1)
EOF

chmod +x /home/vancim/whats_agent/validate_secrets.py

log "✅ Script de validação criado"

# Atualizar .gitignore
log "Atualizando .gitignore..."

cat >> /home/vancim/whats_agent/.gitignore << 'EOF'

# Secrets Management
secrets/
*.secrets
.env.secrets
vault_data/
docker_secrets/
EOF

log "✅ .gitignore atualizado"

# Documentação
log "Criando documentação..."

cat > /home/vancim/whats_agent/SECRETS_MANAGEMENT.md << 'EOF'
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
EOF

log "✅ Documentação criada"

# Resumo final
echo -e "\n${GREEN}╔══════════════════════════════════════╗"
echo -e "║   ✅ SETUP CONCLUÍDO COM SUCESSO    ║"
echo -e "╚══════════════════════════════════════╝${NC}\n"

info "Arquivos criados:"
echo "  📁 secrets/ - Diretório de secrets"
echo "  🐳 docker-compose.secrets.yml - Docker Secrets"
echo "  🔐 start_vault_dev.sh - Vault desenvolvimento"
echo "  ✅ validate_secrets.py - Validação do sistema"
echo "  📚 SECRETS_MANAGEMENT.md - Documentação"

echo -e "\n${YELLOW}Próximos passos:${NC}"
echo "1. Execute: ./validate_secrets.py"
echo "2. Para Docker: ./create_secrets.sh"
echo "3. Para Vault: ./start_vault_dev.sh"
echo "4. Leia: SECRETS_MANAGEMENT.md"

echo -e "\n${GREEN}🎉 Sistema de Secrets Management configurado!${NC}"
