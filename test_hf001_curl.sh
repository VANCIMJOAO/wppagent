#!/bin/bash
"""
🔒 HF001 - Test Script: Validação Webhook via cURL
==================================================

Script bash para testar rapidamente a implementação HF001
usando curl commands.
"""

WEBHOOK_URL="https://wppagent-production.up.railway.app/webhook"
TEST_PAYLOAD='{"entry":[]}'

echo "🔒 HF001 Test Suite - Webhook Signature Validation (cURL)"
echo "========================================================"
echo "Target URL: $WEBHOOK_URL"
echo "Test Payload: $TEST_PAYLOAD"
echo ""

# Teste 1: Webhook sem signature (deve retornar 403)
echo "Test 1: Missing signature (expect HTTP 403)"
echo "--------------------------------------------"
response=$(curl -s -w "%{http_code}" -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD")

http_code="${response: -3}"
response_body="${response%???}"

echo "HTTP Status: $http_code"
echo "Response: $response_body"

if [ "$http_code" = "403" ]; then
  echo "✅ PASSED: Missing signature correctly rejected"
else
  echo "❌ FAILED: Expected 403, got $http_code"
fi
echo ""

# Teste 2: Webhook com signature inválida (deve retornar 403)
echo "Test 2: Invalid signature (expect HTTP 403)"
echo "--------------------------------------------"
response=$(curl -s -w "%{http_code}" -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=invalid_signature_should_be_rejected" \
  -d "$TEST_PAYLOAD")

http_code="${response: -3}"
response_body="${response%???}"

echo "HTTP Status: $http_code"
echo "Response: $response_body"

if [ "$http_code" = "403" ]; then
  echo "✅ PASSED: Invalid signature correctly rejected"
else
  echo "❌ FAILED: Expected 403, got $http_code"
fi
echo ""

# Teste 3: Webhook com signature malformada (deve retornar 403)
echo "Test 3: Malformed signature (expect HTTP 403)"
echo "----------------------------------------------"
response=$(curl -s -w "%{http_code}" -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: malformed_without_sha256_prefix" \
  -d "$TEST_PAYLOAD")

http_code="${response: -3}"
response_body="${response%???}"

echo "HTTP Status: $http_code"
echo "Response: $response_body"

if [ "$http_code" = "403" ]; then
  echo "✅ PASSED: Malformed signature correctly rejected"
else
  echo "❌ FAILED: Expected 403, got $http_code"
fi
echo ""

# Teste 4: Webhook com signature válida (se WEBHOOK_SECRET estiver configurado)
if [ -n "$WHATSAPP_WEBHOOK_SECRET" ]; then
  echo "Test 4: Valid signature (expect HTTP 200)"
  echo "-----------------------------------------"
  
  # Gerar signature válida usando openssl
  valid_signature="sha256=$(echo -n "$TEST_PAYLOAD" | openssl dgst -sha256 -hmac "$WHATSAPP_WEBHOOK_SECRET" | sed 's/^.* //')"
  
  response=$(curl -s -w "%{http_code}" -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -H "X-Hub-Signature-256: $valid_signature" \
    -d "$TEST_PAYLOAD")

  http_code="${response: -3}"
  response_body="${response%???}"

  echo "HTTP Status: $http_code"
  echo "Response: $response_body"
  echo "Signature used: ${valid_signature:0:30}..."

  if [ "$http_code" = "200" ]; then
    echo "✅ PASSED: Valid signature correctly accepted"
  else
    echo "❌ FAILED: Expected 200, got $http_code"
  fi
else
  echo "Test 4: Valid signature (SKIPPED)"
  echo "---------------------------------"
  echo "⏭️ SKIPPED: WHATSAPP_WEBHOOK_SECRET not configured"
fi

echo ""
echo "📊 HF001 Test Summary Complete"
echo "Check logs for 'HF001 PROTECTION' messages in the application"
