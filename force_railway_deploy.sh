#!/bin/bash
# 🚀 Force Railway Deploy Script
# This script forces a Railway deployment by making a commit and pushing

set -e

echo "🚀 FORÇA DEPLOY RAILWAY - $(date)"
echo "========================================"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Erro: Não está em um repositório Git"
    exit 1
fi

# Check git status
echo "📊 Status do Git:"
git status --short

# Add all changes
echo "📦 Adicionando mudanças..."
git add .

# Create commit with timestamp to force rebuild
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
COMMIT_MSG="fix: Force Railway deploy - rebuild trigger $TIMESTAMP"

echo "💾 Fazendo commit: $COMMIT_MSG"
git commit -m "$COMMIT_MSG" || {
    echo "ℹ️  Nenhuma mudança para commit"
}

# Push to trigger Railway deployment
echo "🌐 Fazendo push para Railway..."
git push origin main

echo "✅ Deploy iniciado! Railway vai detectar o push e fazer redeploy"
echo "🔗 Monitore em: https://railway.app/dashboard"
echo "🌍 URL do app: https://wppagent-production.up.railway.app"

echo ""
echo "🔍 Para verificar o deploy:"
echo "   curl https://wppagent-production.up.railway.app/ping"
echo ""