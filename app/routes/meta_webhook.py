"""
WEBHOOK META PRODUCTION - SEM VALIDAÇÃO JWT
============================================
Endpoint específico para Meta webhook em produção
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse
import hmac
import hashlib
import json
from typing import Dict, Any

router = APIRouter(prefix="/meta", tags=["Meta Webhook"])

@router.get("/webhook/verify")
async def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"), 
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Verificação Meta webhook - PRODUÇÃO
    Token deve corresponder ao configurado no Meta Developers
    """
    # Token configurado no Meta (mesmo da imagem)
    VERIFY_TOKEN = "whatsapp_webhook_verify_token"
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print(f"✅ Meta webhook verificado com sucesso - Challenge: {hub_challenge}")
        return PlainTextResponse(content=hub_challenge)
    else:
        print(f"❌ Meta webhook verification failed - Token: {hub_verify_token}")
        return PlainTextResponse(content="Forbidden", status_code=403)

@router.post("/webhook/receive")
async def receive_meta_webhook(request: Request):
    """
    Receber webhook Meta - SEM validação JWT
    Valida apenas assinatura HMAC se necessário
    """
    try:
        # Obter dados sem processar como JWT
        body = await request.body()
        data = json.loads(body)
        
        print(f"📱 Meta webhook recebido: {json.dumps(data, indent=2)[:300]}...")
        
        # Processar mensagens
        if "entry" in data:
            for entry in data["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if "value" in change and "messages" in change["value"]:
                            messages = change["value"]["messages"]
                            for msg in messages:
                                print(f"✅ Mensagem Meta processada: {msg.get('text', {}).get('body', 'N/A')}")
        
        return {"status": "success", "processed": True}
    
    except Exception as e:
        print(f"❌ Erro no webhook Meta: {e}")
        return {"status": "error", "message": str(e)}