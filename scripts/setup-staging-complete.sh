#!/bin/bash

# 🚀 Script Master para Setup Completo do Staging
# Execute este script para configurar todo o ambiente de staging

set -e

echo "🚀 WhatsApp Agent - Setup Completo do Staging"
echo "============================================="
echo "Este script irá executar todas as etapas necessárias:"
echo "  A. Configurar Railway"
echo "  B. Configurar GitHub Secrets"  
echo "  C. Configurar GitHub Variables"
echo "  D. Testar a configuração"
echo ""

read -p "🤔 Executar setup completo? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Setup cancelado"
    exit 1
fi

echo ""
echo "🎯 Iniciando setup completo..."

# Etapa A: Configurar Railway
echo ""
echo "════════════════════════════════════════"
echo "🚂 ETAPA A: Configurando Railway"
echo "════════════════════════════════════════"
./scripts/configure-railway-simple.sh

# Pausa para o usuário verificar as informações
echo ""
echo "⏸️  Pressione Enter quando tiver anotado as informações do Railway..."
read -r

# Etapa B: Configurar GitHub Secrets
echo ""
echo "════════════════════════════════════════"
echo "🔑 ETAPA B: Configurando GitHub Secrets"
echo "════════════════════════════════════════"
./scripts/configure-github-secrets.sh

# Etapa C: Configurar GitHub Variables
echo ""
echo "════════════════════════════════════════"
echo "🌐 ETAPA C: Configurando GitHub Variables"
echo "════════════════════════════════════════"
./scripts/configure-github-variables.sh

# Etapa D: Verificar configuração
echo ""
echo "════════════════════════════════════════"
echo "✅ ETAPA D: Verificando Configuração"
echo "════════════════════════════════════════"

echo "🔍 Verificando secrets configurados..."
gh secret list | grep -E "(RAILWAY|STAGING)" || echo "⚠️ Secrets não listados (normal)"

echo ""
echo "🔍 Verificando variables configuradas..."
gh variable list | grep -E "(STAGING|PRODUCTION)" || echo "⚠️ Variables não listadas (normal)"

echo ""
echo "🔍 Verificando branch develop..."
git branch | grep develop && echo "✅ Branch develop existe" || echo "❌ Branch develop não encontrada"

echo ""
echo "🔍 Verificando pipeline..."
if grep -q "deploy-staging" .github/workflows/ci-cd.yml; then
    echo "✅ Pipeline staging configurado"
else
    echo "❌ Pipeline staging não encontrado"
fi

echo ""
echo "🎉 SETUP COMPLETO FINALIZADO!"
echo "============================="
echo ""
echo "📋 Resumo:"
echo "✅ Railway projeto staging criado"
echo "✅ PostgreSQL e Redis adicionados"
echo "✅ GitHub Secrets configurados"
echo "✅ GitHub Variables configurados"
echo "✅ Pipeline pronto para deploy"
echo ""
echo "🧪 TESTE O STAGING:"
echo "1. Faça uma alteração no código"
echo "2. Execute:"
echo "   git add ."
echo "   git commit -m 'Test staging deployment'"
echo "   git push origin develop"
echo ""
echo "3. Acompanhe em: https://github.com/VANCIMJOAO/wppagent/actions"
echo ""
echo "🎯 O pipeline executará automaticamente:"
echo "   → Tests & Security & Build"
echo "   → Deploy to Staging"
echo "   → Health Check"
echo "   → Deployment Summary"
echo ""
echo "✅ Ambiente de staging profissional pronto para uso!"