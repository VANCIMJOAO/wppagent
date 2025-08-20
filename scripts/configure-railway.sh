#!/bin/bash

# 🚂 Script para configurar Railway via CLI
# Execute este script para criar projeto staging no Railway

set -e

echo "🚂 Configurando Railway para Staging"
echo "===================================="

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "📦 Railway CLI não encontrado. Instalando..."
    curl -fsSL https://railway.app/install.sh | sh
    export PATH="$PATH:$HOME/.railway/bin"
    echo "✅ Railway CLI instalado"
fi

echo ""
echo "📋 Este script irá:"
echo "   1. Fazer login no Railway"
echo "   2. Criar projeto 'whatsapp-agent-staging'"
echo "   3. Adicionar PostgreSQL"
echo "   4. Adicionar Redis"
echo "   5. Mostrar informações para configurar secrets"
echo ""

read -p "🤔 Continuar? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado pelo usuário"
    exit 1
fi

# Login no Railway
echo ""
echo "🔑 Fazendo login no Railway..."
echo "   → Uma página web será aberta para autenticação"
railway login

echo ""
echo "✅ Login realizado com sucesso!"

# Listar projetos existentes
echo ""
echo "📋 Projetos existentes no Railway:"
railway list || echo "   (nenhum projeto encontrado)"

# Criar novo projeto
echo ""
echo "🆕 Criando projeto de staging..."
read -p "   → Nome do projeto [whatsapp-agent-staging]: " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-"whatsapp-agent-staging"}

# Criar projeto
railway init --name "$PROJECT_NAME"

echo "✅ Projeto '$PROJECT_NAME' criado com sucesso!"

# Adicionar PostgreSQL
echo ""
echo "🗄️ Adicionando PostgreSQL..."
railway add postgresql
echo "✅ PostgreSQL adicionado"

# Adicionar Redis
echo ""
echo "⚡ Adicionando Redis..."
railway add redis
echo "✅ Redis adicionado"

# Mostrar informações do projeto
echo ""
echo "📊 Informações do projeto:"
echo "================================"

# Obter Project ID usando status
PROJECT_INFO=$(railway status --json 2>/dev/null || echo '{}')
PROJECT_ID=$(echo "$PROJECT_INFO" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$PROJECT_ID" ]; then
    echo "🆔 PROJECT ID: $PROJECT_ID"
    echo "   → Use este ID no secret RAILWAY_STAGING_PROJECT_ID"
else
    echo "🆔 PROJECT ID: (não foi possível obter automaticamente)"
    echo "   → Acesse https://railway.app/dashboard"
    echo "   → Entre no projeto '$PROJECT_NAME'"
    echo "   → Na URL: railway.app/project/[PROJECT-ID]"
    echo "   → Copie o PROJECT-ID"
fi

echo ""
echo "🌐 URLs de conexão:"
echo "==================="

# Tentar obter URLs de conexão
echo "🗄️ PostgreSQL:"
POSTGRES_URL=$(railway variables get DATABASE_URL 2>/dev/null || echo "Não disponível ainda")
echo "   DATABASE_URL: $POSTGRES_URL"

echo ""
echo "⚡ Redis:"
REDIS_URL=$(railway variables get REDIS_URL 2>/dev/null || echo "Não disponível ainda")
echo "   REDIS_URL: $REDIS_URL"

echo ""
echo "🌍 Domain público:"
echo "   → Será gerado automaticamente no primeiro deploy"
echo "   → Acesse Railway dashboard para ver URL completa"

echo ""
echo "🔑 API Token:"
echo "   → Acesse: https://railway.app/account/tokens"
echo "   → Clique em 'Create New Token'"
echo "   → Use no secret RAILWAY_TOKEN"

echo ""
echo "✅ Configuração do Railway concluída!"
echo ""
echo "📋 Resumo para configurar GitHub Secrets:"
echo "========================================"
echo "RAILWAY_TOKEN: (obter em railway.app/account/tokens)"
echo "RAILWAY_STAGING_PROJECT_ID: $PROJECT_ID"
echo "STAGING_DATABASE_URL: $POSTGRES_URL"
echo "STAGING_REDIS_URL: $REDIS_URL"

echo ""
echo "🎯 Próximos passos:"
echo "1. Configure os GitHub Secrets com as informações acima"
echo "2. Execute: ./scripts/configure-github-secrets.sh"
echo "3. Execute: ./scripts/configure-github-variables.sh"
echo "4. Teste: git push origin develop"