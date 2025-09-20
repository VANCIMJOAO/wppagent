"""
🔍 DEBUG WEBHOOK ENDPOINT
========================

Endpoint específico para debug do processamento de mensagens.
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
router = APIRouter(prefix="/debug", tags=["Debug Webhook"])


@router.post("/process-message")
async def debug_process_message(
    message_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Debug específico para processamento de mensagem
    """
    try:
        debug_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "message_data": message_data,  # Manter como dict
            "steps": []
        }
        
        # Step 1: Sanitizar dados
        try:
            wa_id, clean_content, contact_info = sanitize_whatsapp_data(message_data)
            debug_info["steps"].append({
                "step": "sanitize_whatsapp_data",
                "success": True,
                "wa_id": wa_id,
                "clean_content": clean_content,
                "contact_info": str(contact_info)  # Converter para string
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "sanitize_whatsapp_data",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "sanitize_failed"}
        
        # Step 2: Verificar dados válidos
        if not wa_id or not clean_content:
            debug_info["steps"].append({
                "step": "validate_data",
                "success": False,
                "wa_id_valid": bool(wa_id),
                "content_valid": bool(clean_content),
                "reason": "invalid_data"
            })
            return {"debug_info": debug_info, "error": "invalid_data"}
        
        debug_info["steps"].append({
            "step": "validate_data",
            "success": True,
            "wa_id": wa_id,
            "content_length": len(clean_content)
        })
        
        # Step 3: Verificar controle unificado
        try:
            unified_control = get_unified_response_control()
            can_process, reason = await unified_control.can_process_message(wa_id, clean_content)
            debug_info["steps"].append({
                "step": "unified_control",
                "success": True,
                "can_process": can_process,
                "reason": reason
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "unified_control",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "unified_control_failed"}
        
        if not can_process:
            debug_info["steps"].append({
                "step": "message_blocked",
                "success": False,
                "reason": reason
            })
            return {"debug_info": debug_info, "blocked": True, "reason": reason}
        
        # Step 4: Verificar serviços
        try:
            from app.services.data import UserService, ConversationService, MessageService
            from app.services.whatsapp import whatsapp_service
            from app.services.response_generator import response_generator
            
            debug_info["steps"].append({
                "step": "import_services",
                "success": True,
                "services_available": True
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "import_services",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "import_services_failed"}
        
        # Step 5: Testar criação de usuário
        try:
            user = await UserService.get_or_create_user(
                db=db,
                wa_id=wa_id,
                nome=contact_info.get("name"),
                telefone=wa_id
            )
            debug_info["steps"].append({
                "step": "create_user",
                "success": True,
                "user_id": user.id,
                "user_name": user.nome
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "create_user",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "create_user_failed"}
        
        # Step 6: Testar criação de conversa
        try:
            conversation = await ConversationService.get_or_create_conversation(
                db=db, user_id=user.id
            )
            debug_info["steps"].append({
                "step": "create_conversation",
                "success": True,
                "conversation_id": conversation.id
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "create_conversation",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "create_conversation_failed"}
        
        # Step 7: Testar geração de resposta
        try:
            # Usar a mesma lógica do webhook principal
            class SimplifiedResponseGenerator:
                def __init__(self):
                    self.responses = {
                        "greeting": "Olá! Como posso ajudar você hoje no Studio Beleza Bem-Estar? 🌟",
                        "services": """📋 Aqui estão nossos serviços:

🔹 Limpeza de Pele - R$ 80,00 (60 min)
🔹 Hidrofacial - R$ 150,00 (75 min)
🔹 Criolipólise - R$ 300,00 (60 min)
🔹 Massagem - R$ 120,00 (60 min)

Digite "mais serviços" para ver outras opções! 😊""",
                        "default": "Como posso ajudar você? 😊\\n\\nPosso falar sobre serviços, preços, agendamentos ou informações!",
                    }

                def generate_single_response(self, message: str) -> str:
                    """Gera resposta única baseada na mensagem"""
                    message_lower = message.lower().strip()

                    # Saudações
                    if any(
                        word in message_lower
                        for word in ["ola", "olá", "oi", "bom dia", "boa tarde", "boa noite"]
                    ):
                        return self.responses["greeting"]

                    # Serviços
                    if any(
                        word in message_lower
                        for word in ["serviço", "serviços", "preço", "valor", "quanto"]
                    ):
                        return self.responses["services"]

                    # Resposta padrão
                    return self.responses["default"]
            
            response_generator = SimplifiedResponseGenerator()
            response_text = response_generator.generate_single_response(clean_content)
            debug_info["steps"].append({
                "step": "generate_response",
                "success": True,
                "response_length": len(response_text),
                "response_preview": response_text[:100]
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "generate_response",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "generate_response_failed"}
        
        # Step 8: Testar envio via WhatsApp (simulado)
        try:
            # Simular envio sem realmente enviar
            whatsapp_response = {
                "success": True,
                "message_id": f"debug_{int(datetime.utcnow().timestamp())}",
                "simulated": True
            }
            debug_info["steps"].append({
                "step": "whatsapp_send",
                "success": True,
                "simulated": True,
                "response": whatsapp_response
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "whatsapp_send",
                "success": False,
                "error": str(e)
            })
            return {"debug_info": debug_info, "error": "whatsapp_send_failed"}
        
        # Se chegou até aqui, tudo funcionou
        debug_info["steps"].append({
            "step": "final_result",
            "success": True,
            "processed": True,
            "response_text": response_text  # Incluir resposta gerada
        })
        
        return {
            "debug_info": debug_info,
            "processed": True,
            "message": "Debug processamento concluído com sucesso",
            "response_text": response_text,  # Incluir resposta no resultado final
            "user_id": user.id,
            "conversation_id": conversation.id
        }
        
    except Exception as e:
        logger.error(f"Erro no debug: {e}")
        return {
            "debug_info": {"error": str(e)},
            "error": "debug_failed"
        }