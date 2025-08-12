#!/bin/bash

# Criar Docker Secrets para WhatsApp Agent

echo "🔐 Criando Docker Secrets..."

# Função para criar secret
create_secret() {
    local name=$1
    local description=$2
    
    echo -n "Digite o valor para $description: "
    read -s value
    echo
    
    echo "$value" | docker secret create "$name" - || {
        echo "⚠️ Secret $name já existe ou erro na criação"
    }
}

# Criar secrets
create_secret "database_password" "senha do banco de dados"
create_secret "openai_api_key" "chave da API OpenAI"
create_secret "meta_access_token" "token de acesso Meta/WhatsApp"
create_secret "webhook_verify_token" "token de verificação webhook"
create_secret "jwt_secret" "secret JWT"

echo "✅ Docker Secrets criados"
