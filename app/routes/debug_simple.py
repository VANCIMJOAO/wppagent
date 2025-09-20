"""
🔍 DEBUG SIMPLE WEBHOOK
======================

Endpoint simples para debug do webhook.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.response_control import get_unified_response_control
from app.utils.whatsapp_data_extractor import sanitize_whatsapp_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/debug", tags=["Debug Simple"])


@router.post("/test-message")
async def debug_test_message(
    message_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Debug simples para testar processamento de mensagem
    """
    try:
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "success": False,
            "steps": []
        }
        
        # Step 1: Sanitizar dados
        try:
            wa_id, clean_content, contact_info = sanitize_whatsapp_data(message_data)
            result["steps"].append({
                "step": "sanitize",
                "success": True,
                "wa_id": wa_id,
                "content_length": len(clean_content) if clean_content else 0
            })
        except Exception as e:
            result["steps"].append({
                "step": "sanitize",
                "success": False,
                "error": str(e)
            })
            return result
        
        # Step 2: Verificar dados válidos
        if not wa_id or not clean_content:
            result["steps"].append({
                "step": "validate",
                "success": False,
                "reason": "invalid_data"
            })
            return result
        
        result["steps"].append({
            "step": "validate",
            "success": True
        })
        
        # Step 3: Verificar controle unificado
        try:
            unified_control = get_unified_response_control()
            can_process, reason = await unified_control.can_process_message(wa_id, clean_content)
            result["steps"].append({
                "step": "unified_control",
                "success": True,
                "can_process": can_process,
                "reason": reason
            })
        except Exception as e:
            result["steps"].append({
                "step": "unified_control",
                "success": False,
                "error": str(e)
            })
            return result
        
        if not can_process:
            result["steps"].append({
                "step": "final",
                "success": False,
                "reason": f"blocked: {reason}"
            })
            return result
        
        # Step 4: Testar criação de usuário
        try:
            from app.services.data import UserService
            user = await UserService.get_or_create_user(
                db=db,
                wa_id=wa_id,
                nome=contact_info.get("name"),
                telefone=wa_id
            )
            result["steps"].append({
                "step": "create_user",
                "success": True,
                "user_id": user.id
            })
        except Exception as e:
            result["steps"].append({
                "step": "create_user",
                "success": False,
                "error": str(e)
            })
            return result
        
        # Se chegou até aqui, tudo funcionou
        result["success"] = True
        result["steps"].append({
            "step": "final",
            "success": True,
            "message": "All steps completed successfully"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no debug: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "success": False,
            "error": str(e),
            "steps": []
        }
