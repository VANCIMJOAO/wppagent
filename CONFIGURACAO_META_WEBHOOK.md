📋 CONFIGURAÇÃO META WEBHOOK - INSTRUÇÕES
=============================================

🔗 URL do Webhook para configurar no Meta Developers:
https://wppagent-production-app-production.up.railway.app/meta/webhook/receive

🔑 Token de Verificação: whatsapp_webhook_verify_token

📱 Eventos para subscrever:
- messages
- message_deliveries  
- message_reads
- messaging_postbacks

🛠️ PASSOS NO META DEVELOPERS:
1. Cole a URL: https://wppagent-production-app-production.up.railway.app/meta/webhook/receive
2. Token de verificação: whatsapp_webhook_verify_token  
3. Clique em "Verificar e Salvar"
4. Subscreva aos eventos: messages

⚠️ IMPORTANTE:
- O endpoint /meta/webhook NÃO usa validação JWT
- Apenas validação por token de verificação
- Funciona diretamente com o Meta sem middleware de auth

🧪 TESTE RÁPIDO:
curl "https://wppagent-production-app-production.up.railway.app/meta/webhook/verify?hub.mode=subscribe&hub.verify_token=whatsapp_webhook_verify_token&hub.challenge=12345"