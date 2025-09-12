#!/bin/bash

echo "🔒 HF002 HTTP Integration Test"
echo "=============================="

# Test with sensitive data in HTTP requests
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token_hf002_validation" \
  -d '{
    "message": "Contact me at +55 11 99999-8888 or email test@example.com",
    "user_id": "5511999887766@s.whatsapp.net",
    "metadata": {
      "phone": "+55 21 98765-4321",
      "document": "123.456.789-00"
    }
  }' \
  --max-time 10 \
  --write-out "\nHTTP Status: %{http_code}\n" \
  --silent

echo ""
echo "✅ Check server logs - all sensitive data should be sanitized with HF002"
echo "Expected sanitization:"
echo "- Phones: [PHONE_REDACTED_HF002]"  
echo "- Emails: [EMAIL_REDACTED_HF002]"
echo "- WhatsApp IDs: [WHATSAPP_ID_REDACTED_HF002]"
echo "- Tokens: [TOKEN_REDACTED_HF002]"
echo "- Documents: [DOCUMENT_REDACTED_HF002]"
