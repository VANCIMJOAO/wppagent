#!/bin/bash

# 🔑 Script para configurar GitHub Secrets via CLI
# Execute este script para adicionar os secrets necessários

set -e

echo "🔑 Configurando GitHub Secrets para Staging"
echo "==========================================="

# Verificar se GitHub CLI está autenticado
if ! gh auth status >/dev/null 2>&1; then
    echo "❌ GitHub CLI não está autenticado"
    echo "Execute: gh auth login"
    exit 1
fi

echo ""
echo "📋 Este script irá configurar os seguintes secrets:"
echo "   - RAILWAY_TOKEN"
echo "   - RAILWAY_STAGING_PROJECT_ID"
echo "   - STAGING_DATABASE_URL"
echo "   - STAGING_REDIS_URL"
echo "   - STAGING_SECRET_KEY"
echo ""

read -p "🤔 Continuar? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado pelo usuário"
    exit 1
fi

echo ""
echo "🔑 Configurando secrets..."

# RAILWAY_TOKEN
echo ""
echo "1️⃣ RAILWAY_TOKEN"
echo "   → Acesse: https://railway.app/account/tokens"
echo "   → Clique em 'Create New Token'"
echo "   → Copie o token gerado"
read -s -p "   → Cole o RAILWAY_TOKEN: " RAILWAY_TOKEN
echo ""
gh secret set RAILWAY_TOKEN --body "$RAILWAY_TOKEN"
echo "✅ RAILWAY_TOKEN configurado"

# RAILWAY_STAGING_PROJECT_ID  
echo ""
echo "2️⃣ RAILWAY_STAGING_PROJECT_ID"
echo "   → Acesse seu projeto staging no Railway"
echo "   → Na URL: railway.app/project/[PROJECT-ID]"
echo "   → Copie apenas o PROJECT-ID"
read -p "   → Cole o PROJECT_ID: " STAGING_PROJECT_ID
gh secret set RAILWAY_STAGING_PROJECT_ID --body "$STAGING_PROJECT_ID"
echo "✅ RAILWAY_STAGING_PROJECT_ID configurado"

# STAGING_DATABASE_URL
echo ""
echo "3️⃣ STAGING_DATABASE_URL"
echo "   → No seu projeto Railway staging"
echo "   → Acesse PostgreSQL service → Connect → Database URL"
read -s -p "   → Cole a DATABASE_URL: " STAGING_DB_URL
echo ""
gh secret set STAGING_DATABASE_URL --body "$STAGING_DB_URL"
echo "✅ STAGING_DATABASE_URL configurado"

# STAGING_REDIS_URL
echo ""
echo "4️⃣ STAGING_REDIS_URL"
echo "   → No seu projeto Railway staging"
echo "   → Acesse Redis service → Connect → Redis URL"
read -s -p "   → Cole a REDIS_URL: " STAGING_REDIS_URL
echo ""
gh secret set STAGING_REDIS_URL --body "$STAGING_REDIS_URL"
echo "✅ STAGING_REDIS_URL configurado"

# STAGING_SECRET_KEY
echo ""
echo "5️⃣ STAGING_SECRET_KEY"
echo "   → Gerando chave secreta automaticamente..."
STAGING_SECRET=$(openssl rand -hex 32)
gh secret set STAGING_SECRET_KEY --body "$STAGING_SECRET"
echo "✅ STAGING_SECRET_KEY gerado e configurado: ${STAGING_SECRET:0:8}..."

echo ""
echo "✅ Todos os secrets foram configurados com sucesso!"
echo ""
echo "📋 Secrets configurados:"
gh secret list | grep -E "(RAILWAY|STAGING)" || echo "   (listagem de secrets pode não estar disponível)"

echo ""
echo "🎯 Próximo passo: Configure as GitHub Variables"
echo "   Execute: ./scripts/configure-github-variables.sh"