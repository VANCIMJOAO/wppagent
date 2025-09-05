#!/bin/bash

# Dashboard Deployment Script
# ===========================

echo "🚀 Iniciando deploy do Dashboard para Railway..."

# Verifica se está no diretório correto
if [ ! -f "app.py" ]; then
    echo "❌ Execute este script no diretório dashboard"
    exit 1
fi

# Verifica se existe Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI não encontrado. Instale com: npm install -g @railway/cli"
    exit 1
fi

# Login no Railway (se necessário)
echo "🔐 Verificando autenticação Railway..."
railway whoami || {
    echo "🔑 Faça login no Railway:"
    railway login
}

# Build da imagem Docker localmente (opcional - para teste)
echo "🏗️ Testando build Docker localmente..."
docker build -t dashboard-test . || {
    echo "❌ Falha no build Docker"
    exit 1
}

# Remove imagem de teste
docker rmi dashboard-test

# Deploy para Railway
echo "🚀 Iniciando deploy para Railway..."
railway up || {
    echo "❌ Falha no deploy"
    exit 1
}

echo "✅ Deploy concluído!"
echo "🌐 Acesse: https://seu-dominio.railway.app"
echo ""
echo "📋 Para verificar logs:"
echo "   railway logs"
echo ""
echo "📋 Para configurar variáveis de ambiente:"
echo "   railway variables"
