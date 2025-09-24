#!/bin/bash

# Script para configurar variáveis de ambiente seguras
# Execute este script para configurar as variáveis de ambiente do sistema

echo "🔒 Configurando variáveis de ambiente seguras..."

# Database Configuration
export DATABASE_URL="postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"

# Redis Configuration
export REDIS_URL="redis://default:SvSHiMNuuQEtmIUgGIEGqPpXsdZeInDG@yamanote.proxy.rlwy.net:14106"

# Environment
export ENVIRONMENT="development"

# WhatsApp Meta Configuration
export META_ACCESS_TOKEN="EAAGAXIrC3H0BOwz9XiZCRcIJZLKNxYMKZB..."
export WEBHOOK_VERIFY_TOKEN="verify_token_12345"

# Security - Chaves unificadas para JWT
export SECRET_KEY="whatsapp_agent_super_secret_2024_railway_production"
export JWT_SECRET="whatsapp_agent_super_secret_2024_railway_production"

# Features
export DEBUG="False"
export TESTING="False"

# Admin Configuration
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="admin123"

echo "✅ Variáveis de ambiente configuradas!"
echo "⚠️  IMPORTANTE: Execute 'source setup_env.sh' para aplicar as variáveis"
echo "🔒 As credenciais agora estão em variáveis de ambiente, não no arquivo .env"
