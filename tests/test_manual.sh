#!/bin/bash

echo "🔍 Teste manual do fluxo de autenticação"

# 1. Login e salvar token
echo "1. Fazendo login..."
RESPONSE=$(curl -s -X POST "http://localhost:8001/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")"}')

echo "Response: $RESPONSE"

# Extrair token
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.loads(sys.stdin.read()).get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
    echo "❌ Falha ao obter token"
    exit 1
fi

echo "✅ Token obtido: ${TOKEN:0:50}..."

# 2. Testar status imediatamente
echo "2. Testando status imediatamente..."
STATUS_RESPONSE=$(curl -s -X GET "http://localhost:8001/auth/status" \
     -H "Authorization: Bearer $TOKEN")

echo "Status Response: $STATUS_RESPONSE"
