"""
🔍 Endpoint de Debug para Webhook Secret
======================================

Endpoint temporário para debugar problemas de webhook signature.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from app.services.whatsapp_security import WhatsAppSecurityService
from app.config import settings
import hmac
import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Endpoint público para debug (sem autenticação)
@router.get("/public/webhook-secret-info")
async def public_webhook_secret_info():
    """
    Endpoint público para debug do webhook secret - REMOVER EM PRODUÇÃO
    """
    try:
        service = WhatsAppSecurityService()
        
        result = {
            "webhook_secret_configured": bool(service.webhook_secret),
            "webhook_secret_length": len(service.webhook_secret) if service.webhook_secret else 0,
            "timestamp": "2025-08-13T01:10:00Z",
            "debug_mode": True
        }
        
        if service.webhook_secret:
            # Criar uma assinatura de teste
            test_payload = '{"test": "payload"}'
            test_signature = hmac.new(
                service.webhook_secret.encode('utf-8'),
                test_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            result.update({
                "webhook_secret_first_8": service.webhook_secret[:8],
                "webhook_secret_last_8": service.webhook_secret[-8:],
                "full_secret_for_meta_console": service.webhook_secret,  # APENAS PARA DEBUG
                "test_payload": test_payload,
                "test_signature": f"sha256={test_signature}",
                "validation_info": "Configure este secret no Meta Developers Console",
                "current_signature_mismatch": {
                    "received_from_meta": "d2d86b5217f9683c9d81cbedc8d7294aa42c3aab15e07e33f41c6eddc187da5f",
                    "expected_by_app": "35a55f92ec03aa5f74f0631964c6ac90144e85866d21114f381e18d6355134ca"
                }
            })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro no debug webhook secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug/webhook-test")
async def test_webhook_signature(request: Request):
    """
    Endpoint para testar validação de assinatura - REMOVER EM PRODUÇÃO
    """
    try:
        service = WhatsAppSecurityService()
        
        # Obter payload e signature
        payload = await request.body()
        signature = request.headers.get('X-Hub-Signature-256', '')
        
        # Tentar validar
        is_valid = service.validate_webhook_signature(payload, signature)
        
        result = {
            "signature_provided": signature,
            "payload_length": len(payload),
            "validation_result": is_valid,
            "webhook_secret_configured": bool(service.webhook_secret)
        }
        
        if service.webhook_secret and payload:
            # Calcular assinatura esperada
            expected_signature = hmac.new(
                service.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            result.update({
                "expected_signature": f"sha256={expected_signature}",
                "signature_match": signature == f"sha256={expected_signature}" or signature == expected_signature
            })
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erro no teste webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
