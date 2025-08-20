#!/bin/bash

# 🚀 Script para Setup do Staging Environment
# Execute este script para configurar o ambiente de staging

set -e

echo "🚀 WhatsApp Agent - Staging Environment Setup"
echo "============================================"

# Verificar se estamos no repositório correto
if [ ! -f ".github/workflows/ci-cd.yml" ]; then
    echo "❌ Execute este script na raiz do projeto whats_agent"
    exit 1
fi

echo ""
echo "1️⃣ Criando branch develop..."

# Verificar se branch develop já existe
if git branch -r | grep -q "origin/develop"; then
    echo "✅ Branch develop já existe no remote"
    git checkout develop 2>/dev/null || git checkout -b develop origin/develop
else
    echo "🆕 Criando nova branch develop"
    git checkout -b develop
    git push -u origin develop
fi

echo ""
echo "2️⃣ Verificando configuração atual..."

# Mostrar status do repositório
echo "📊 Status do Git:"
echo "Branch atual: $(git branch --show-current)"
echo "Remote URL: $(git remote get-url origin)"

echo ""
echo "3️⃣ Próximos passos necessários:"
echo ""
echo "🔑 A. Configure os GitHub Secrets:"
echo "   → Acesse: https://github.com/$(git remote get-url origin | sed 's/.*github.com[/:]//;s/\.git$//')/settings/secrets/actions"
echo "   → Adicione:"
echo "     - RAILWAY_TOKEN"
echo "     - RAILWAY_STAGING_PROJECT_ID" 
echo "     - STAGING_DATABASE_URL"
echo "     - STAGING_REDIS_URL"
echo "     - STAGING_SECRET_KEY"
echo ""
echo "🌐 B. Configure as GitHub Variables:"
echo "   → Acesse: https://github.com/$(git remote get-url origin | sed 's/.*github.com[/:]//;s/\.git$//')/settings/variables/actions"
echo "   → Adicione:"
echo "     - STAGING_URL"
echo ""
echo "🚂 C. Configure o Railway:"
echo "   1. Acesse https://railway.app"
echo "   2. Crie novo projeto: 'whatsapp-agent-staging'"
echo "   3. Adicione PostgreSQL e Redis"
echo "   4. Copie o Project ID da URL"
echo "   5. Crie API Token em Account → Tokens"
echo ""
echo "🧪 D. Teste o Staging:"
echo "   → git add ."
echo "   → git commit -m 'Test staging deployment'"
echo "   → git push origin develop"
echo ""
echo "📚 Documentação completa em: .github/STAGING_SETUP_GUIDE.md"
echo ""
echo "✅ Setup inicial concluído!"
echo "🎯 Agora configure os secrets e variables no GitHub para ativar o staging."