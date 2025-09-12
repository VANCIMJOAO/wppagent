#!/bin/bash

echo "🔄 CF001 HTTP Integration Test - Naming Standardization"
echo "======================================================"

BASE_URL="http://localhost:8000"
# Para produção: BASE_URL="https://wppagent-production.up.railway.app"

echo ""
echo "🔄 Testing CF001 - API accepts both camelCase and snake_case"
echo ""

# Test 1: Request com camelCase
echo "📝 Test 1: POST appointment with camelCase"
curl -X POST "$BASE_URL/appointments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token" \
  -d '{
    "userId": 123,
    "businessId": 456,
    "dateTime": "2025-09-12T14:00:00Z", 
    "durationMinutes": 60,
    "clientName": "João Silva",
    "clientPhone": "+55 11 99999-8888",
    "status": "agendado"
  }' \
  --max-time 10 \
  --write-out "\nHTTP Status: %{http_code}\n" \
  --silent || echo "⚠️  Server not running - test with production URL"

echo ""
echo "📝 Test 2: POST appointment with snake_case"
curl -X POST "$BASE_URL/appointments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token" \
  -d '{
    "user_id": 123,
    "business_id": 456,
    "date_time": "2025-09-12T15:00:00Z",
    "duration_minutes": 90,
    "client_name": "Maria Santos", 
    "client_phone": "+55 21 88888-7777",
    "status": "confirmado"
  }' \
  --max-time 10 \
  --write-out "\nHTTP Status: %{http_code}\n" \
  --silent || echo "⚠️  Server not running - test with production URL"

echo ""
echo "📝 Test 3: GET appointments (response should be camelCase)"
curl -X GET "$BASE_URL/appointments?limit=2" \
  -H "Authorization: Bearer test_token" \
  --max-time 10 \
  --write-out "\nHTTP Status: %{http_code}\n" \
  --silent || echo "⚠️  Server not running - test with production URL"

echo ""
echo "✅ CF001 Expected Behavior:"
echo "- POST requests accept both camelCase and snake_case"
echo "- GET responses return fields in camelCase:"
echo "  • userId (not user_id)"
echo "  • businessId (not business_id)" 
echo "  • dateTime (not date_time)"
echo "  • durationMinutes (not duration_minutes)"
echo "  • createdAt (not created_at)"
echo "  • clientName (not client_name)"
echo ""
echo "🔍 Manual check: Verify response JSON contains camelCase fields"
echo "🔍 Manual check: Verify both request formats return HTTP 200/201"
