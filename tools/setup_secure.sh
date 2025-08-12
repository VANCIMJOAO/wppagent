#!/bin/bash

# 🔐 Setup Seguro do WhatsApp Agent
# Este script ajuda a configurar as variáveis de ambiente de forma segura

echo "🔐 WhatsApp Agent - Setup Seguro"
echo "================================"

# Verificar se .env já existe
if [ -f ".env" ]; then
    echo "⚠️  Arquivo .env já existe!"
    read -p "Sobrescrever? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "❌ Setup cancelado"
        exit 1
    fi
fi

echo ""
echo "📝 Configure suas credenciais:"
echo ""

# Meta WhatsApp
echo "🔷 Meta WhatsApp Cloud API:"
read -p "Meta Access Token: " META_TOKEN
read -p "Phone Number ID: " PHONE_ID
read -p "Webhook Verify Token: " WEBHOOK_TOKEN

echo ""
echo "🤖 OpenAI:"
read -s -p "OpenAI API Key: " OPENAI_KEY
echo ""

echo ""
echo "🗄️  Banco de Dados:"
read -p "Database User: " DB_USER
read -s -p "Database Password: " DB_PASS
echo ""

# Gerar .env
cat > .env << EOF
# Meta WhatsApp Cloud API
META_ACCESS_TOKEN=${META_TOKEN}
PHONE_NUMBER_ID=${PHONE_ID}
WEBHOOK_VERIFY_TOKEN=${WEBHOOK_TOKEN}
META_API_VERSION=v18.0

# WhatsApp Security
WHATSAPP_WEBHOOK_SECRET=$(openssl rand -hex 32)
WHATSAPP_ACCESS_TOKEN=${META_TOKEN}
WHATSAPP_PHONE_NUMBER_ID=${PHONE_ID}

# OpenAI
OPENAI_API_KEY=${OPENAI_KEY}

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=whats_agent
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASS}
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASS}@localhost:5432/whats_agent

# Ngrok (configure depois)
NGROK_AUTHTOKEN=YOUR_NGROK_AUTHTOKEN_HERE
NGROK_REGION=us

# App
APP_HOST=0.0.0.0
APP_PORT=8000
WEBHOOK_URL=https://your-ngrok-url.ngrok.io/webhook

# Streamlit
STREAMLIT_PORT=8501
SECRET_KEY=$(openssl rand -hex 32)

# Admin (ALTERE ESTAS CREDENCIAIS!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$(openssl rand -base64 12)
ADMIN_EMAIL=admin@yourdomain.com

# Debug
DEBUG=True
LOG_LEVEL=INFO
EOF

# Definir permissões seguras
chmod 600 .env

echo ""
echo "✅ Arquivo .env criado com segurança!"
echo "🔒 Permissões restritivas aplicadas (600)"
echo ""
echo "🚨 IMPORTANTE:"
echo "- Sua senha de admin foi gerada automaticamente"
echo "- Não compartilhe o arquivo .env"
echo "- Configure o Ngrok separadamente"
echo ""
echo "📋 Credenciais geradas:"
echo "Admin Password: $(grep ADMIN_PASSWORD .env | cut -d= -f2)"
echo ""
echo "🚀 Pronto para usar!"
