#!/bin/bash

echo "🔍 Teste específico do 2FA setup"

# 1. Login
echo "1. Fazendo login..."
LOGIN_RESP=$(curl -s -X POST "http://localhost:8001/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "SECURE_PASSWORD_FROM_ENV"}')

echo "Login response: $LOGIN_RESP"

# Extrair token manualmente
TOKEN=$(echo "$LOGIN_RESP" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

if [ -z "$TOKEN" ]; then
    echo "❌ Falha ao extrair token"
    exit 1
fi

echo "✅ Token extraído: ${TOKEN:0:30}..."

# 2. Testar 2FA setup
echo "2. Testando 2FA setup..."
SETUP_RESP=$(curl -v -X POST "http://localhost:8001/auth/2fa/setup" \
     -H "Authorization: Bearer $TOKEN" 2>&1)

echo "Setup response: $SETUP_RESP"
