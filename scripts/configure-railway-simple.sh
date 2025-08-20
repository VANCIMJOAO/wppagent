#!/bin/bash

# 🚂 Script SIMPLIFICADO para configurar Railway via CLI
# Execute este script para configurar o staging no Railway

set -e

echo "🚂 Configuração Simplificada do Railway"
echo "======================================="

# Verificar se Railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI não está instalado"
    echo "   → Instale em: https://railway.app/install"
    exit 1
fi

echo ""
echo "📋 Este script irá guiá-lo através da configuração manual:"
echo "   1. Verificar login no Railway"
echo "   2. Orientar criação do projeto"
echo "   3. Mostrar como obter informações"
echo ""

read -p "🤔 Continuar? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado pelo usuário"
    exit 1
fi

# Verificar login
echo ""
echo "1️⃣ Verificando login no Railway..."
if railway whoami >/dev/null 2>&1; then
    USER=$(railway whoami)
    echo "✅ Logado como: $USER"
else
    echo "🔑 Fazendo login no Railway..."
    railway login
    echo "✅ Login realizado!"
fi

# Listar projetos existentes
echo ""
echo "2️⃣ Projetos existentes:"
railway list 2>/dev/null || echo "   (nenhum projeto ou erro ao listar)"

echo ""
echo "3️⃣ CONFIGURAÇÃO MANUAL NECESSÁRIA:"
echo "=================================="
echo ""
echo "🌐 No navegador, acesse: https://railway.app/dashboard"
echo ""
echo "📋 Siga estes passos:"
echo "   1. Clique em 'New Project'"
echo "   2. Nome: 'whatsapp-agent-staging'"
echo "   3. Clique em '+ Add Service'"
echo "   4. Adicione 'PostgreSQL'"
echo "   5. Clique em '+ Add Service' novamente"
echo "   6. Adicione 'Redis'"
echo ""
echo "🔑 Para obter o API Token:"
echo "   1. Acesse: https://railway.app/account/tokens"
echo "   2. Clique 'Create New Token'"
echo "   3. Copie o token gerado"
echo ""
echo "🆔 Para obter o Project ID:"
echo "   1. No seu projeto staging"
echo "   2. Na URL: railway.app/project/[PROJECT-ID]"
echo "   3. Copie o PROJECT-ID"
echo ""
echo "🌐 Para obter as URLs de conexão:"
echo "   1. PostgreSQL: Service → Variables → DATABASE_URL"
echo "   2. Redis: Service → Variables → REDIS_URL"
echo "   3. Staging URL: Service → Settings → Generate Domain"
echo ""

# Aguardar configuração manual
echo ""
echo "⏸️  Configure o projeto no Railway e pressione Enter quando terminar..."
read -r

# Tentar obter informações automaticamente
echo ""
echo "4️⃣ Tentando obter informações do projeto..."

# Se usuário fez o link local
if railway status >/dev/null 2>&1; then
    echo "✅ Projeto Railway conectado localmente"
    
    PROJECT_INFO=$(railway status --json 2>/dev/null || echo '{}')
    PROJECT_ID=$(echo "$PROJECT_INFO" | jq -r '.project.id // empty' 2>/dev/null || echo "")
    
    if [ -n "$PROJECT_ID" ]; then
        echo "🆔 PROJECT ID: $PROJECT_ID"
    else
        echo "🆔 PROJECT ID: (obtenha manualmente do dashboard)"
    fi
    
    echo ""
    echo "🔍 Variáveis disponíveis:"
    railway variables --json 2>/dev/null | jq -r 'keys[]' 2>/dev/null || echo "   (obtenha manualmente do dashboard)"
else
    echo "⚠️  Projeto não conectado localmente"
    echo "   → Para conectar: cd /home/vancim/whats_agent && railway link [PROJECT-ID]"
fi

echo ""
echo "✅ Configuração Railway concluída!"
echo ""
echo "📋 INFORMAÇÕES NECESSÁRIAS PARA GITHUB SECRETS:"
echo "=============================================="
echo "🔑 RAILWAY_TOKEN: (token da sua conta Railway)"
echo "🆔 RAILWAY_STAGING_PROJECT_ID: (ID do projeto criado)"
echo "🗄️ STAGING_DATABASE_URL: (URL do PostgreSQL)"
echo "⚡ STAGING_REDIS_URL: (URL do Redis)"
echo "🌐 STAGING_URL: (URL pública do seu app)"
echo ""
echo "🎯 Próximo passo: Execute o script de GitHub Secrets"
echo "   → ./scripts/configure-github-secrets.sh"