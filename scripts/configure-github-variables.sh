#!/bin/bash

# 🌐 Script para configurar GitHub Variables via CLI
# Execute este script para adicionar as variables necessárias

set -e

echo "🌐 Configurando GitHub Variables para Staging"
echo "============================================"

# Verificar se GitHub CLI está autenticado
if ! gh auth status >/dev/null 2>&1; then
    echo "❌ GitHub CLI não está autenticado"
    echo "Execute: gh auth login"
    exit 1
fi

echo ""
echo "📋 Este script irá configurar as seguintes variables:"
echo "   - STAGING_URL"
echo "   - PRODUCTION_URL (opcional)"
echo ""

read -p "🤔 Continuar? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado pelo usuário"
    exit 1
fi

echo ""
echo "🌐 Configurando variables..."

# STAGING_URL
echo ""
echo "1️⃣ STAGING_URL"
echo "   → No seu projeto Railway staging"
echo "   → Acesse Settings → Domains"
echo "   → Copie a URL gerada (ex: https://your-app-staging.railway.app)"
read -p "   → Cole a STAGING_URL: " STAGING_URL
gh variable set STAGING_URL --body "$STAGING_URL"
echo "✅ STAGING_URL configurado: $STAGING_URL"

# PRODUCTION_URL (opcional)
echo ""
echo "2️⃣ PRODUCTION_URL (opcional)"
read -p "   → Deseja configurar PRODUCTION_URL também? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   → No seu projeto Railway production"
    echo "   → Acesse Settings → Domains"
    echo "   → Copie a URL gerada (ex: https://your-app-prod.railway.app)"
    read -p "   → Cole a PRODUCTION_URL: " PRODUCTION_URL
    gh variable set PRODUCTION_URL --body "$PRODUCTION_URL"
    echo "✅ PRODUCTION_URL configurado: $PRODUCTION_URL"
else
    echo "⏭️ PRODUCTION_URL pulado"
fi

echo ""
echo "✅ Todas as variables foram configuradas com sucesso!"
echo ""
echo "📋 Variables configuradas:"
gh variable list | grep -E "(STAGING|PRODUCTION)" || echo "   (listagem de variables pode não estar disponível)"

echo ""
echo "🎯 Próximo passo: Configure o Railway"
echo "   Execute: ./scripts/configure-railway.sh"