#!/bin/bash

echo "🔍 Teste específico do 2FA"

# 1. Login e obter token fresco
echo "1. Login..."
RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "SECURE_PASSWORD_FROM_ENV"}')

TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.loads(sys.stdin.read()).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Falha ao obter token"
    exit 1
fi

echo "✅ Token: ${TOKEN:0:30}..."

# 2. Testar setup de 2FA
echo "2. Configurando 2FA..."
SETUP_RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/2fa/setup" \
     -H "Authorization: Bearer $TOKEN")

echo "Setup Response: $SETUP_RESPONSE"

# 3. Testar criação de secret
echo "3. Criando secret..."
SECRET_RESPONSE=$(curl -s -X POST "http://localhost:8001/secrets/create" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"secret_id": "test_secret", "secret_type": "api_key", "value": "test_value_123"}')

echo "Secret Response: $SECRET_RESPONSE"
