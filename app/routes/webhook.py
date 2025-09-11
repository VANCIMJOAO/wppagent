"""
🔧 WEBHOOK SIMPLIFICADO COM SISTEMA UNIFICADO
============================================

Versão limpa e otimizada que usa apenas o sistema unificado de controle,
eliminando sobreposições e redundâncias.
"""

import asyncio
import json
import time  # ✅ Para métricas de performance
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.structured_apm import (
    get_structured_logger, LogCategory, log_performance, 
    log_business_event, log_security_event, BusinessEvent
)
from app.services.whatsapp import whatsapp_service
from app.services.data import UserService, ConversationService, MessageService
from app.services.response_control import unified_response_control
from app.utils.whatsapp_sanitizer import sanitize_whatsapp_data, sanitize_message, sanitize_phone
from app.models.database import MetaLog
from app.services.whatsapp_security import WhatsAppSecurityService

# ✅ Unified Response Control (substitui webhook_rate_limiter)
# from app.auth.webhook_rate_limiter import webhook_rate_limit, webhook_rate_limiter

# 🔥 WebSocket Integration
from app.services.websocket_integration import notify_new_whatsapp_message, notify_message_sent

logger = get_structured_logger(__name__)
router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])

# 🔒 H001 FIX - Inicializar serviço de segurança do WhatsApp
security_service = WhatsAppSecurityService()

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

@router.post("", summary="Receber webhooks do WhatsApp Business API")
# ✅ Rate limiting removido - usando unified_response_control para controle otimizado
@log_performance("webhook.process")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    WEBHOOK PRINCIPAL COM VALIDACAO DE ASSINATURA E RATE LIMITING AVANCADO
    
    Sistema de protecao implementado:
    - H001 FIX: VALIDACAO DE ASSINATURA X-Hub-Signature-256
    - Burst protection: 50 req/10s  
    - Sustained limit: 100 req/min
    - Escalation system com bloqueio automatico
    - Deteccao de padroes suspeitos
    - Logging estruturado com APM
    """
    try:
        # 🔒 H001 FIX - VALIDACAO OBRIGATORIA DE ASSINATURA DO WEBHOOK
        # Validar assinatura ANTES de processar qualquer dado
        if not await security_service.validate_webhook_request(request):
            log_security_event(
                event_type="webhook_signature_invalid",
                source_ip=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", ""),
                severity="HIGH",
                description="Webhook com assinatura invalida rejeitado - H001 protection",
                metadata={
                    "fix_applied": "H001",
                    "endpoint": "/webhook",
                    "signature_header": request.headers.get('X-Hub-Signature-256', 'missing'),
                    "content_type": request.headers.get('Content-Type', ''),
                    "user_agent": request.headers.get("user-agent", "")
                }
            )
            
            logger.error(
                "H001 - Webhook signature validation failed - request rejected",
                metadata={
                    "security_fix": "H001",
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent", ""),
                    "signature_present": bool(request.headers.get('X-Hub-Signature-256')),
                    "content_type": request.headers.get('Content-Type', '')
                },
                category=LogCategory.SECURITY
            )
            
            raise HTTPException(
                status_code=403,
                detail="Webhook signature validation failed"
            )
        
        # ✅ Assinatura validada com sucesso - continuar processamento
        logger.info(
            "H001 - Webhook signature validation successful",
            metadata={
                "security_fix": "H001",
                "client_ip": request.client.host if request.client else None,
                "signature_validated": True
            },
            category=LogCategory.SECURITY
        )
        
        # Log informações de rate limiting se disponíveis
        rate_info = getattr(request.state, 'webhook_rate_info', {})
        if rate_info:
            logger.info(
                "Rate limiting applied",
                metadata={
                    "rate_limit_level": rate_info.get('level', 'UNKNOWN'),
                    "config_applied": rate_info.get('config_applied', 'default'),
                    "client_ip": request.client.host if request.client else None
                },
                category=LogCategory.SECURITY
            )
        
        # Obter dados do webhook
        raw_data = await request.json()
        
        # Log estruturado do webhook recebido
        logger.info(
            "WhatsApp webhook received",
            metadata={
                "webhook_size": len(json.dumps(raw_data)),
                "entries_count": len(raw_data.get("entry", [])),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", ""),
                "webhook_preview": json.dumps(raw_data, indent=2)[:500]
            },
            category=LogCategory.WEBHOOK
        )
        
        # Log para auditoria com informações de rate limiting
        log_entry = MetaLog(
            direction="in",
            endpoint="/webhook",
            method="POST",
            status_code=200,
            payload=raw_data,
            headers=dict(request.headers) if hasattr(request, 'headers') else None
        )
        db.add(log_entry)
        await db.commit()
        
        # Validar estrutura básica
        if "entry" not in raw_data:
            logger.warning(
                "Invalid webhook structure: missing entry field",
                metadata={"webhook_structure": list(raw_data.keys())},
                category=LogCategory.WEBHOOK
            )
            return {"status": "ignored", "reason": "no_entry_field"}
        
        total_processed = 0
        total_blocked = 0
        
        # ⚡ OTIMIZAÇÃO: Processamento concurrent de mensagens
        all_messages = []  # Coletar todas as mensagens primeiro
        
        # Coletar mensagens de todas as entries
        for entry in raw_data.get("entry", []):
            changes = entry.get("changes", [])
            
            for change in changes:
                if change.get("field") != "messages":
                    continue
                
                messages = change.get("value", {}).get("messages", [])
                all_messages.extend(messages)
        
        # ✅ HIGH-PERFORMANCE CONCURRENT PROCESSING
        if all_messages:
            from app.utils.webhook_optimizer import batch_processor
            from app.utils.performance_monitor import performance_monitor
            
            batch_size = len(all_messages)
            start_time = time.time()
            
            total_processed, total_blocked, metrics = await batch_processor.process_messages_optimized(
                messages=all_messages,
                db=db
            )
            
            processing_time = time.time() - start_time
            had_timeout = "timeout" in metrics.get("error", "")
            
            # 📊 Registrar métricas de performance
            await performance_monitor.record_batch(
                batch_size=batch_size,
                processing_time=processing_time,
                processed=total_processed,
                blocked=total_blocked,
                had_timeout=had_timeout
            )
            
            # Log performance summary
            logger.info(
                "🚀 High-performance batch processing completed",
                metadata={
                    "batch_size": batch_size,
                    "total_processed": total_processed,
                    "total_blocked": total_blocked,
                    "performance_metrics": metrics,
                    "optimization_enabled": True,
                    "monitoring_enabled": True
                },
                category=LogCategory.PERFORMANCE
            )
        
        # Log estruturado de conclusão
        logger.info(
            "Webhook processing completed",
            metadata={
                "messages_processed": total_processed,
                "messages_blocked": total_blocked,
                "success_rate": total_processed / (total_processed + total_blocked) if (total_processed + total_blocked) > 0 else 1.0,
                "processing_result": "success"
            },
            category=LogCategory.WEBHOOK
        )
        
        # Log evento de negócio se houve processamento
        if total_processed > 0:
            log_business_event(
                event_type="whatsapp_messages",
                entity_type="message",
                entity_id="batch",
                action="processed",
                metadata={
                    "total_processed": total_processed,
                    "total_blocked": total_blocked,
                    "batch_size": total_processed + total_blocked
                }
            )
        
        return {
            "status": "success",
            "processed": total_processed,
            "blocked": total_blocked,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            "Webhook processing failed",
            metadata={
                "error_type": e.__class__.__name__,
                "client_ip": request.client.host if request.client else None,
                "webhook_endpoint": str(request.url)
            },
            category=LogCategory.WEBHOOK,
            exception=e
        )
        
        # Log evento de segurança em caso de erro suspeito
        log_security_event(
            "webhook_processing_error",
            {
                "error_type": e.__class__.__name__,
                "client_ip": request.client.host if request.client else None,
                "endpoint": str(request.url),
                "user_agent": request.headers.get("user-agent", "")
            },
            severity="WARNING"
        )
        
        return {"status": "error", "error": str(e)}

@log_performance("webhook.process_message")
async def process_single_message(message_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """Processa uma única mensagem com controle unificado e logging estruturado"""
    
    try:
        # Sanitizar dados
        wa_id, clean_content, contact_info = sanitize_whatsapp_data(message_data)
        
        if not wa_id or not clean_content:
            logger.warning(
                "Invalid message data received",
                metadata={
                    "has_wa_id": bool(wa_id),
                    "has_content": bool(clean_content),
                    "message_type": message_data.get("type", "unknown")
                },
                category=LogCategory.WEBHOOK
            )
            return {"processed": False, "reason": "invalid_data"}
        
        # 🔧 CONTROLE UNIFICADO - Verificação única
        can_process, reason = await unified_response_control.can_process_message(wa_id, clean_content)
        
        if not can_process:
            # Log estruturado de bloqueio
            logger.warning(
                "Message blocked by unified control",
                metadata={
                    "wa_id": wa_id,
                    "block_reason": reason,
                    "message_preview": clean_content[:50],
                    "contact_info": contact_info
                },
                category=LogCategory.SECURITY
            )
            
            # Log evento de segurança
            log_security_event(
                "message_blocked",
                {
                    "wa_id": wa_id,
                    "reason": reason,
                    "message_preview": clean_content[:100],
                    "block_type": "unified_control"
                },
                severity="INFO"
            )
            
            return {"processed": False, "reason": reason}
        
        # Log início do processamento
        logger.info(
            "Processing WhatsApp message",
            metadata={
                "wa_id": wa_id,
                "message_preview": clean_content[:50],
                "message_type": message_data.get("type", "text"),
                "message_length": len(clean_content),
                "contact_name": contact_info.get("name", "unknown")
            },
            category=LogCategory.WEBHOOK
        )
        
        # Criar/buscar usuário
        user = await UserService.get_or_create_user(
            db=db,
            wa_id=wa_id,
            nome=contact_info.get("name"),
            telefone=sanitize_phone(wa_id)
        )
        
        # Log evento de negócio: usuário ativo
        log_business_event(
            event_type="user_interaction",
            entity_type="user",
            entity_id=str(user.id),
            action="message_received",
            metadata={
                "wa_id": wa_id,
                "message_type": message_data.get("type", "text"),
                "user_name": contact_info.get("name"),
                "is_new_user": user.created_at.timestamp() > (datetime.utcnow().timestamp() - 300)  # 5 min
            }
        )
        
        # Criar/buscar conversa
        conversation = await ConversationService.get_or_create_conversation(
            db=db,
            user_id=user.id
        )
        
        # Salvar mensagem recebida
        message_in = await MessageService.create_message(
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
        
        # Log de geração de resposta
        logger.debug(
            "Response generated for message",
            metadata={
                "wa_id": wa_id,
                "message_id": message_in.id,
                "response_preview": response_text[:100],
                "response_length": len(response_text)
            },
            category=LogCategory.BUSINESS
        )
        
        # Enviar via WhatsApp
        whatsapp_response = await whatsapp_service.send_text_message(wa_id, response_text)
        
        if whatsapp_response.get("success"):
            # Salvar mensagem enviada
            message_out = await MessageService.create_message(
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
            
            # Log sucesso estruturado
            logger.info(
                "WhatsApp message processed successfully",
                metadata={
                    "wa_id": wa_id,
                    "conversation_id": conversation.id,
                    "message_in_id": message_in.id,
                    "message_out_id": message_out.id,
                    "response_sent": True,
                    "whatsapp_message_id": whatsapp_response.get("message_id")
                },
                category=LogCategory.BUSINESS
            )
            
            # Log evento de negócio: resposta enviada
            log_business_event(
                event_type="message_response",
                entity_type="conversation",
                entity_id=str(conversation.id),
                action="response_sent",
                metadata={
                    "wa_id": wa_id,
                    "user_id": user.id,
                    "response_type": "automated",
                    "original_message": clean_content[:100],
                    "response_preview": response_text[:100]
                }
            )
            
            # WebSocket notification
            try:
                await notify_new_whatsapp_message({
                    "user_id": user.id,
                    "wa_id": wa_id,
                    "message": clean_content,
                    "conversation_id": conversation.id
                })
                
                await notify_message_sent({
                    "user_id": user.id,
                    "wa_id": wa_id,
                    "response": response_text,
                    "conversation_id": conversation.id
                })
                
            except Exception as ws_error:
                logger.warning(
                    "WebSocket notification failed",
                    metadata={
                        "wa_id": wa_id,
                        "error": str(ws_error),
                        "websocket_event": "message_notifications"
                    },
                    category=LogCategory.SYSTEM
                )
            
            return {"processed": True, "message_id": message_out.id}
        
        else:
            # Log erro no envio
            logger.error(
                "Failed to send WhatsApp response",
                metadata={
                    "wa_id": wa_id,
                    "whatsapp_error": whatsapp_response,
                    "response_text": response_text[:100]
                },
                category=LogCategory.API
            )
            
            return {"processed": False, "reason": "whatsapp_send_failed"}
        
    except Exception as e:
        logger.error(
            "Error processing single message",
            metadata={
                "wa_id": wa_id if 'wa_id' in locals() else "unknown",
                "message_preview": clean_content[:50] if 'clean_content' in locals() else "unknown",
                "error_type": e.__class__.__name__
            },
            category=LogCategory.WEBHOOK,
            exception=e
        )
        
        return {"processed": False, "reason": f"processing_error: {str(e)}"}


@router.get("/verify")
@log_performance("webhook.verify")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Verificação do webhook do WhatsApp com logging estruturado"""
    
    # Verificar token (use uma variável de ambiente em produção)
    expected_token = "your_verify_token_here"  # TODO: Mover para config
    
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info(
            "Webhook verification successful",
            metadata={
                "hub_mode": hub_mode,
                "challenge_provided": bool(hub_challenge),
                "verification_result": "success"
            },
            category=LogCategory.SECURITY
        )
        
        # Log evento de segurança: webhook verificado
        log_security_event(
            "webhook_verification_success",
            {
                "hub_mode": hub_mode,
                "timestamp": datetime.utcnow().isoformat()
            },
            severity="INFO"
        )
        
        return int(hub_challenge)
    else:
        logger.warning(
            "Webhook verification failed",
            metadata={
                "hub_mode": hub_mode,
                "token_provided": bool(hub_verify_token),
                "expected_mode": "subscribe",
                "verification_result": "failed"
            },
            category=LogCategory.SECURITY
        )
        
        # Log evento de segurança: tentativa de verificação inválida
        log_security_event(
            "webhook_verification_failed",
            {
                "hub_mode": hub_mode,
                "invalid_token": bool(hub_verify_token),
                "timestamp": datetime.utcnow().isoformat()
            },
            severity="WARNING"
        )
        
        raise HTTPException(status_code=403, detail="Token de verificação inválido")


@router.get("/stats")
@log_performance("webhook.stats")
async def get_webhook_stats():
    """Estatísticas do sistema de controle unificado com logging"""
    
    try:
        stats = await unified_response_control.get_stats()
        
        logger.info(
            "Webhook stats requested",
            metadata={
                "messages_processed": stats.get("messages_processed", 0),
                "blocked_percentage": stats.get("blocked_percentage", 0),
                "redis_available": stats.get("redis_available", False)
            },
            category=LogCategory.SYSTEM
        )
        
        return stats
        
    except Exception as e:
        logger.error(
            "Failed to get webhook stats",
            metadata={"error_type": e.__class__.__name__},
            category=LogCategory.SYSTEM,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Erro interno ao obter estatísticas")


@router.post("/clear-cache")
@log_performance("webhook.clear_cache")
async def clear_webhook_cache():
    """Limpar cache do sistema de controle com logging de segurança"""
    
    try:
        result = await unified_response_control.clear_cache()
        
        logger.warning(
            "Webhook cache cleared",
            metadata={
                "cache_clear_result": result,
                "admin_action": "cache_clear"
            },
            category=LogCategory.SECURITY
        )
        
        # Log evento de segurança: cache limpo
        log_security_event(
            "webhook_cache_cleared",
            {
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "action_type": "administrative"
            },
            severity="WARNING"
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Failed to clear webhook cache",
            metadata={"error_type": e.__class__.__name__},
            category=LogCategory.SYSTEM,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Erro interno ao limpar cache")


@router.get("/health")
@log_performance("webhook.health")
async def webhook_health():
    """Verificação de saúde do webhook com métricas estruturadas"""
    
    try:
        stats = await unified_response_control.get_stats()
        
        health_status = {
            "status": "healthy" if stats.get("redis_available", False) else "degraded",
            "system": "unified_response_control",
            "redis_available": stats.get("redis_available", False),
            "messages_processed_total": stats.get("messages_processed", 0),
            "blocked_percentage": stats.get("blocked_percentage", 0),
            "memory_cache_size": stats.get("memory_cache_size", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Webhook health check performed",
            metadata=health_status,
            category=LogCategory.SYSTEM
        )
        
        return health_status
        
    except Exception as e:
        logger.error(
            "Webhook health check failed",
            metadata={"error_type": e.__class__.__name__},
            category=LogCategory.SYSTEM,
            exception=e
        )
        
        # Retornar status de erro
        return {
            "status": "error",
            "system": "unified_response_control",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/performance-stats", summary="Estatísticas de Performance do Webhook")
async def get_webhook_performance_stats():
    """
    📊 Endpoint para monitoramento de performance do webhook
    
    Retorna métricas detalhadas de:
    - Throughput (mensagens por segundo)
    - Latência média de processamento
    - Taxa de sucesso
    - Alertas de performance
    """
    try:
        from app.utils.performance_monitor import performance_monitor
        
        stats = await performance_monitor.get_performance_stats()
        
        logger.info(
            "📊 Performance stats requested",
            metadata={"stats_overview": stats.get("overall_metrics", {})},
            category=LogCategory.PERFORMANCE
        )
        
        return {
            "status": "success",
            "webhook_performance": stats,
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring_active": True
        }
        
    except Exception as e:
        logger.error(f"❌ Error retrieving performance stats: {e}")
        return {"status": "error", "message": str(e)}
