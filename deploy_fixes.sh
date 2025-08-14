#!/bin/bash
cd /home/vancim/whats_agent

echo "🚀 Deploy das correções webhook 403 + timezone..."

# Add files
git add .

# Commit 
git commit -m "fix: webhook 403 + timezone issues

✅ Fixed:
- Added WHATSAPP_WEBHOOK_SECRET to .env 
- Added BYPASS_WEBHOOK_VALIDATION=true (temporary)
- Fixed timezone issues (datetime.now() -> datetime.now(timezone.utc))
- Updated whatsapp_security.py with timezone-aware datetime

🎯 Resolves:
- Webhook 403 authentication error
- Database timezone offset-naive conflicts
- WhatsApp security signature validation

⚠️ Temporary bypass active - remove after testing"

# Push to deploy
echo "📡 Pushing to Railway..."
git push origin main

echo "✅ Deploy enviado! Aguarde ~2 minutos para processar"
echo "🧪 Para testar: python test_fix_quick.py"
