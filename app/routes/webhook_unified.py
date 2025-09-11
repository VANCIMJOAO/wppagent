"""
🔧 WEBHOOK SIMPLIFICADO COM SISTEMA UNIFICADO
============================================

Versão limpa e otimizada que usa apenas o sistema unificado de controle,
eliminando sobreposições e redundâncias.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.logger import get_logger
from app.services.whatsapp import whatsapp_service
from app.services.data import UserService, ConversationService, MessageService
from app.services.response_control import get_unified_response_control
from app.utils.whatsapp_sanitizer import sanitize_whatsapp_data, sanitize_message, sanitize_phone
from app.models.database import MetaLog

# 🔥 WebSocket Integration
from app.services.websocket_integration import notify_new_whatsapp_message, notify_message_sent

logger = get_logger(__name__)
router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])

# Sistema de resposta simplificado
class SimplifiedResponseGenerator:
    def __init__(self):
        self.responses = {
            'greeting': "Olá! Como posso ajudar você hoje no Studio Beleza Bem-Estar? 🌟",
            'services': """📋 Aqui estão nossos serviços:

🔹 Limpeza de Pele - R$ 80,00 (60 min)
🔹 Hidrofacial - R$ 150,00 (75 min)
🔹 Criolipólise - R$ 300,00 (60 min)
🔹 Massagem - R$ 120,00 (60 min)

Digite "mais serviços" para ver outras opções! 😊""",
            'default': "Como posso ajudar você? 😊\\n\\nPosso falar sobre serviços, preços, agendamentos ou informações!"
        }
    
    def generate_single_response(self, message: str) -> str:
        """Gera resposta única baseada na mensagem"""
        message_lower = message.lower().strip()
        
        # Saudações
        if any(word in message_lower for word in ['ola', 'olá', 'oi', 'bom dia', 'boa tarde', 'boa noite']):
            return self.responses['greeting']
        
        # Serviços
        if any(word in message_lower for word in ['serviço', 'serviços', 'preço', 'valor', 'quanto']):
            return self.responses['services']
        
        # Resposta padrão
        return self.responses['default']

response_generator = SimplifiedResponseGenerator()

@router.post("")
async def webhook_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    🔧 Endpoint principal do webhook - Versão unificada e otimizada
    """
    try:
        # Obter dados do webhook
        raw_data = await request.json()
        logger.info(f"📥 Webhook recebido: {json.dumps(raw_data, indent=2)[:500]}...")
        
        # Log para auditoria
        log_entry = MetaLog(
            webhook_data=raw_data,
            processed_at=datetime.utcnow()
        )
        db.add(log_entry)
        await db.commit()
        
        # Validar estrutura básica
        if "entry" not in raw_data:
            logger.warning("⚠️ Webhook sem campo 'entry'")
            return {"status": "ignored", "reason": "no_entry_field"}
        
        total_processed = 0
        total_blocked = 0
        
        # Processar cada entrada
        for entry in raw_data.get("entry", []):
            changes = entry.get("changes", [])
            
            for change in changes:
                if change.get("field") != "messages":
                    continue
                
                messages = change.get("value", {}).get("messages", [])
                
                for message_data in messages:
                    result = await process_single_message(message_data, db)
                    
                    if result["processed"]:
                        total_processed += 1
                    else:
                        total_blocked += 1
        
        logger.info(f"✅ Webhook finalizado: {total_processed} processadas, {total_blocked} bloqueadas")
        
        return {
            "status": "success",
            "processed": total_processed,
            "blocked": total_blocked,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        return {"status": "error", "error": str(e)}

async def process_single_message(message_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Processa uma única mensagem com controle unificado"""
    
    try:
        # Sanitizar dados
        wa_id, clean_content, contact_info = sanitize_whatsapp_data(message_data)
        
        if not wa_id or not clean_content:
            return {"processed": False, "reason": "invalid_data"}
        
        # 🔧 CONTROLE UNIFICADO - Verificação única
        can_process, reason = await get_unified_response_control().can_process_message(wa_id, clean_content)
        
        if not can_process:
            logger.warning(f"🚫 BLOQUEADO: {wa_id} - {reason}")
            return {"processed": False, "reason": reason}
        
        logger.info(f"📨 PROCESSANDO: {wa_id} - {clean_content[:50]}...")
        
        # Criar/buscar usuário
        user = await UserService.get_or_create_user(
            db=db,
            wa_id=wa_id,
            nome=contact_info.get("name"),
            telefone=sanitize_phone(wa_id)
        )
        
        # Criar/buscar conversa
        conversation = await ConversationService.get_or_create_conversation(
            db=db,
            user_id=user.id
        )
        
        # Salvar mensagem recebida
        await MessageService.create_message(
            db=db,
            user_id=user.id,
            conversation_id=conversation.id,
            direction="in",
            content=clean_content,
            message_type=message_data.get("type", "text"),
            raw_payload=message_data
        )
        
        # Gerar e enviar resposta
        response_text = response_generator.generate_single_response(clean_content)
        
        # Enviar via WhatsApp
        whatsapp_response = await whatsapp_service.send_text_message(wa_id, response_text)
        
        if whatsapp_response.get("success"):
            # Salvar mensagem enviada
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                direction="out",
                content=response_text,
                message_type="text",
                raw_payload=whatsapp_response
            )
            
            # Atualizar conversa
            conversation.last_message_at = datetime.utcnow()
            await db.commit()
            
            # Notificações WebSocket
            await notify_new_whatsapp_message(user.wa_id, clean_content)
            await notify_message_sent(user.wa_id, response_text)
            
            logger.info(f"✅ SUCESSO: {wa_id} - Resposta enviada")
            return {"processed": True, "response_sent": True}
        else:
            logger.error(f"❌ Erro ao enviar resposta: {whatsapp_response}")
            return {"processed": True, "response_sent": False}
            
    except Exception as e:
        logger.error(f"❌ Erro processando mensagem: {e}")
        return {"processed": False, "reason": f"error: {str(e)}"}

@router.get("/verify")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Verificação do webhook do WhatsApp"""
    
    # Verificar token (use uma variável de ambiente em produção)
    expected_token = "your_verify_token_here"  # TODO: Mover para config
    
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("✅ Webhook verificado com sucesso")
        return int(hub_challenge)
    else:
        logger.warning("❌ Falha na verificação do webhook")
        raise HTTPException(status_code=403, detail="Token de verificação inválido")

@router.get("/stats")
async def get_webhook_stats():
    """Estatísticas do sistema de controle unificado"""
    return await get_unified_response_control().get_stats()

@router.post("/clear-cache")
async def clear_webhook_cache():
    """Limpar cache do sistema de controle (para debug/testes)"""
    return await get_unified_response_control().clear_cache()

@router.get("/health")
async def webhook_health():
    """Verificação de saúde do webhook"""
    stats = await get_unified_response_control().get_stats()
    
    return {
        "status": "healthy",
        "system": "unified_response_control",
        "redis_available": stats["redis_available"],
        "messages_processed_total": stats["messages_processed"],
        "blocked_percentage": stats["blocked_percentage"],
        "memory_cache_size": stats["memory_cache_size"],
        "timestamp": datetime.utcnow().isoformat()
    }
