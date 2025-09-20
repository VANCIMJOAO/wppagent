"""
🔍 DEBUG WHATSAPP SERVICE
========================

Endpoint para debug do serviço WhatsApp.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.whatsapp import whatsapp_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["Debug WhatsApp"])


@router.post("/test-whatsapp-send")
async def debug_test_whatsapp_send(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Testa envio via WhatsApp diretamente
    """
    try:
        # Dados de teste
        test_phone = "16991022255"
        test_message = f"Teste direto WhatsApp {int(datetime.now().timestamp())}"
        
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "test_phone": test_phone,
            "test_message": test_message,
            "steps": []
        }
        
        # Step 1: Verificar configurações
        try:
            config_info = {
                "whatsapp_api_url": getattr(settings, "whatsapp_api_url", "NOT_SET"),
                "whatsapp_phone_id": getattr(settings, "whatsapp_phone_id", "NOT_SET"),
                "meta_access_token": "SET" if getattr(settings, "meta_access_token", None) else "NOT_SET",
                "whatsapp_webhook_secret": "SET" if getattr(settings, "whatsapp_webhook_secret", None) else "NOT_SET"
            }
            
            debug_info["steps"].append({
                "step": "check_config",
                "success": True,
                "config": config_info
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "check_config",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "config_check_failed"}
        
        # Step 2: Testar envio via WhatsApp
        try:
            whatsapp_response = await whatsapp_service.send_text_message(
                test_phone, test_message
            )
            
            debug_info["steps"].append({
                "step": "whatsapp_send",
                "success": True,
                "response": whatsapp_response
            })
            
            # Verificar se foi bem-sucedido
            if whatsapp_response.get("success") or "message_id" in whatsapp_response:
                debug_info["steps"].append({
                    "step": "whatsapp_success",
                    "success": True,
                    "message": "WhatsApp send successful"
                })
            else:
                debug_info["steps"].append({
                    "step": "whatsapp_success",
                    "success": False,
                    "message": "WhatsApp send failed",
                    "response": whatsapp_response
                })
                
        except Exception as e:
            debug_info["steps"].append({
                "step": "whatsapp_send",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "whatsapp_send_failed"}
        
        # Step 3: Testar serviço de segurança diretamente
        try:
            from app.services.whatsapp_security import whatsapp_security
            
            security_response = await whatsapp_security.send_message(
                phone_number=test_phone,
                message=test_message,
                message_type="text"
            )
            
            debug_info["steps"].append({
                "step": "security_send",
                "success": True,
                "response": security_response
            })
            
        except Exception as e:
            debug_info["steps"].append({
                "step": "security_send",
                "success": False,
                "error": str(e)
            })
        
        return {
            "debug_info": debug_info,
            "success": True,
            "message": "WhatsApp debug completed"
        }
        
    except Exception as e:
        logger.error(f"Erro no debug WhatsApp: {e}")
        return {
            "debug_info": {"error": str(e)},
            "error": "debug_failed"
        }


@router.get("/whatsapp-config")
async def debug_whatsapp_config():
    """
    Mostra configurações do WhatsApp (sem dados sensíveis)
    """
    try:
        config_info = {
            "whatsapp_api_url": getattr(settings, "whatsapp_api_url", "NOT_SET"),
            "whatsapp_phone_id": getattr(settings, "whatsapp_phone_id", "NOT_SET"),
            "meta_access_token": "SET" if getattr(settings, "meta_access_token", None) else "NOT_SET",
            "whatsapp_webhook_secret": "SET" if getattr(settings, "whatsapp_webhook_secret", None) else "NOT_SET",
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "config": config_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
