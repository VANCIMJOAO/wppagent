"""
Rotas do webhook para receber mensagens do WhatsApp COM SANITIZAÇÃO ROBUSTA E SEGURANÇA
"""
import json
import time
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.utils.logger import get_logger
from app.services.whatsapp import whatsapp_service
logger = get_logger(__name__)
from app.services.llm_advanced import advanced_llm_service
from app.services.strategy_compatibility import hybrid_service
from app.services.hybrid_llm_crew import HybridLLMCrewService
from app.services.service_validator import service_validator
from app.services.intelligent_handoff import intelligent_handoff_service
from app.services.business_data import business_data_service
from app.services.booking_workflow import BookingWorkflow
from app.services.whatsapp_security import whatsapp_security
from app.services.data import (
    UserService, ConversationService, MessageService, AppointmentService
)
from app.services.rate_limiter import whatsapp_rate_limiter
from app.services.cache_service import cache_service
from app.models.database import MetaLog
from app.config import settings

# Prometheus metrics integration
from app.utils.metrics import metrics_collector, webhook_timer

# 🛡️ IMPORTAÇÕES DE SEGURANÇA E SANITIZAÇÃO
from app.utils.whatsapp_sanitizer import (
    whatsapp_sanitizer, security_validator,
    sanitize_whatsapp_data, sanitize_message, sanitize_phone, validate_security
)
from app.utils.validators import ValidationError, RobustValidator

import logging
import re

logger = logging.getLogger(__name__)

def validate_whatsapp_number(wa_id: str) -> str:
    """
    DEPRECATED: Use sanitize_phone from whatsapp_sanitizer instead
    Mantido para compatibilidade com código existente
    """
    try:
        return sanitize_phone(wa_id)
    except ValueError as e:
        logger.error(f"❌ Erro na validação do número {wa_id}: {e}")
        raise ValueError(str(e))

router = APIRouter()

# TEMPORÁRIO: Endpoint para debug do webhook secret (REMOVER APÓS FIX)
@router.get("/webhook-debug-secret")
async def webhook_debug_secret():
    """
    Endpoint temporário para obter informações do webhook secret
    """
    try:
        import hmac
        import hashlib
        
        service = whatsapp_security
        
        result = {
            "status": "debug_active",
            "webhook_secret_configured": bool(service.webhook_secret),
            "timestamp": "2025-08-13T01:15:00Z"
        }
        
        if service.webhook_secret:
            result.update({
                "webhook_secret_length": len(service.webhook_secret),
                "secret_first_8": service.webhook_secret[:8],
                "secret_last_8": service.webhook_secret[-8:],
                "full_secret": service.webhook_secret,  # TEMPORÁRIO APENAS
                "meta_console_config": "Use this secret in Meta Developers Console"
            })
        
        return result
        
    except Exception as e:
        return {"error": str(e), "status": "error"}

# Instância global do BookingWorkflow para manter estado
booking_workflow_instance = BookingWorkflow()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """
    Verificação do webhook do WhatsApp
    """
    logger.info(f"Verificação webhook recebida:")
    logger.info(f"  - Mode: {hub_mode}")
    logger.info(f"  - Token recebido: '{hub_verify_token}'")
    
    # Usar método seguro para acessar webhook_verify_token
    try:
        webhook_token = getattr(settings, 'webhook_verify_token', None)
        if webhook_token and hasattr(webhook_token, 'get_secret_value'):
            expected_token = webhook_token.get_secret_value()
        elif webhook_token:
            expected_token = str(webhook_token)
        else:
            expected_token = None
        logger.info(f"  - Token esperado: '{expected_token}'")
    except Exception as e:
        logger.error(f"Erro ao acessar webhook_verify_token: {e}")
        expected_token = None
    
    logger.info(f"  - Challenge: {hub_challenge}")
    
    if hub_mode == "subscribe":
        challenge = whatsapp_service.verify_webhook(hub_verify_token, hub_challenge)
        if challenge:
            logger.info("✅ Webhook verificado com sucesso!")
            return int(challenge)
        else:
            logger.error(f"❌ Token não confere! Recebido: '{hub_verify_token}', Esperado: '{expected_token}'")
    
    logger.error("❌ Falha na verificação do webhook")
    raise HTTPException(status_code=403, detail="Erro de verificação")


@router.get("/webhook/status")
async def get_webhook_status():
    """
    Status da integração WhatsApp com Meta API
    """
    try:
        status = whatsapp_security.get_api_status()
        
        # Processar fila de fallback se API estiver disponível
        if status["status"] == "available" and status["fallback_queue_size"] > 0:
            await whatsapp_security.process_fallback_queue()
            # Atualizar status após processamento
            status = whatsapp_security.get_api_status()
        
        return {
            "webhook_status": "active",
            "meta_api": status,
            "security": {
                "signature_validation": "enabled" if settings.whatsapp_webhook_secret else "disabled",
                "user_agent_validation": "enabled"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do webhook: {e}")
        return {
            "webhook_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/webhook/test-send")
async def test_send_message(
    phone_number: str,
    message: str = "Teste de conectividade da API WhatsApp"
):
    """
    Testa envio de mensagem via WhatsApp com retry robusto
    """
    try:
        # Sanitizar número de telefone
        clean_phone = sanitize_phone(phone_number)
        
        # Tentar enviar mensagem
        result = await whatsapp_security.send_message(
            phone_number=clean_phone,
            message=message
        )
        
        if result:
            return {
                "success": True,
                "message": "Mensagem enviada com sucesso",
                "api_response": result,
                "api_status": whatsapp_security.get_api_status()
            }
        else:
            return {
                "success": False,
                "message": "Falha ao enviar mensagem - adicionado à fila de fallback",
                "api_status": whatsapp_security.get_api_status()
            }
            
    except Exception as e:
        logger.error(f"❌ Erro no teste de envio: {e}")
        return {
            "success": False,
            "error": str(e),
            "api_status": whatsapp_security.get_api_status()
        }


@router.post("/webhook")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Recebe mensagens do WhatsApp via webhook COM SANITIZAÇÃO ROBUSTA E VALIDAÇÃO DE ASSINATURA
    """
    try:
        # 🛡️ ETAPA 1: VALIDAÇÃO COMPLETA DE SEGURANÇA DO WEBHOOK
        is_valid_request = await whatsapp_security.validate_webhook_request(request)
        if not is_valid_request:
            logger.error("❌ Validação de segurança do webhook falhou")
            raise HTTPException(status_code=403, detail="Webhook inválido")
        
        # 🛡️ ETAPA 2: OBTER PAYLOAD BRUTO JÁ VALIDADO
        payload_raw = await request.body()
        
        # 🛡️ ETAPA 3: PARSEAR E SANITIZAR PAYLOAD
        try:
            payload_dict = json.loads(payload_raw)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Payload JSON inválido: {e}")
            raise HTTPException(status_code=400, detail="JSON inválido")
        
        # 🧹 SANITIZAÇÃO COMPLETA DO PAYLOAD
        try:
            sanitized_payload = sanitize_whatsapp_data(payload_dict)
            logger.info("✅ Payload WhatsApp sanitizado com sucesso")
        except ValueError as e:
            logger.error(f"❌ Falha na sanitização do payload: {e}")
            raise HTTPException(status_code=400, detail=f"Payload inseguro: {str(e)}")
        
        # 🛡️ ETAPA 4: LOG SEGURO DA REQUISIÇÃO
        await _log_incoming_request_secure(db, sanitized_payload, dict(request.headers))
        
        # 🛡️ ETAPA 5: PROCESSAR ENTRADAS SANITIZADAS
        if "entry" in sanitized_payload:
            for entry in sanitized_payload["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            await _process_message_change_secure(db, change["value"])
        
        return {"status": "ok"}
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"❌ Erro crítico no webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


async def _log_incoming_request_secure(db: AsyncSession, payload: dict, headers: dict):
    """
    Registra requisição recebida nos logs COM SANITIZAÇÃO
    """
    try:
        # 🛡️ Sanitizar headers antes de salvar
        safe_headers = {}
        for key, value in headers.items():
            if isinstance(key, str) and isinstance(value, str):
                # Sanitizar chave e valor
                safe_key = RobustValidator.sanitize_sql_input(key[:100])
                safe_value = RobustValidator.sanitize_sql_input(value[:500])
                safe_headers[safe_key] = safe_value
        
        # Payload já foi sanitizado na função principal
        log_entry = MetaLog(
            direction="in",
            endpoint="/webhook",
            method="POST",
            status_code=200,
            headers=safe_headers,
            payload=payload
        )
        db.add(log_entry)
        await db.commit()
        logger.debug("✅ Log de entrada salvo com segurança")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar log de entrada seguro: {e}")


async def _process_message_change_secure(db: AsyncSession, value: dict):
    """
    Processa mudanças relacionadas a mensagens COM SANITIZAÇÃO ROBUSTA
    
    Args:
        db: Sessão do banco
        value: Dados da mudança recebida (já sanitizados)
    """
    try:
        # Verificar se há mensagens
        if "messages" not in value:
            return
        
        # 🛡️ Sanitizar informações do contato
        contacts = value.get("contacts", [])
        contact_info = {}
        if contacts:
            contact = contacts[0]
            contact_info = whatsapp_sanitizer.sanitize_contact_info(contact)
        
        # 🛡️ Processar cada mensagem com sanitização
        for message in value["messages"]:
            await _process_single_message_secure(db, message, contact_info)
            
        # 🛡️ Processar status de mensagens (entregue, lida, etc.)
        if "statuses" in value:
            for status in value["statuses"]:
                await _process_message_status_secure(db, status)
                
    except Exception as e:
        logger.error(f"❌ Erro ao processar mudança de mensagem segura: {e}")


async def _process_single_message_secure(db: AsyncSession, message: dict, contact_info: dict):
    """
    Processa uma mensagem individual COM SANITIZAÇÃO ROBUSTA
    
    Args:
        db: Sessão do banco
        message: Dados da mensagem (já sanitizados)
        contact_info: Informações do contato (já sanitizadas)
    """
    try:
        # Record webhook processing metrics
        with webhook_timer():
            raw_wa_id = message.get("from")
            message_id = message.get("id")
        message_type = message.get("type")
        timestamp = message.get("timestamp")
        
        if not raw_wa_id:
            logger.warning("Mensagem sem wa_id recebida")
            return
        
        # 🛡️ Sanitizar e validar número do WhatsApp
        try:
            wa_id = sanitize_phone(raw_wa_id)
        except ValueError as e:
            logger.error(f"❌ Número WhatsApp inválido '{raw_wa_id}': {e}")
            return  # Ignorar mensagem com número inválido
        
        # 🛡️ Validar ID da mensagem
        if message_id:
            try:
                message_id = RobustValidator.sanitize_sql_input(str(message_id))
                if len(message_id) > 100:
                    message_id = message_id[:100]
            except Exception:
                message_id = None
        
        # Verificar rate limit para este usuário
        is_allowed, limit_info = await whatsapp_rate_limiter.check_user_message_limit(wa_id)
        
        if not is_allowed:
            logger.warning(f"Rate limit excedido para usuário {wa_id}: {limit_info}")
            
            # Enviar mensagem de aviso se for um limite temporário
            if limit_info.get("error") == "rate_limit_exceeded":
                retry_after = limit_info.get("retry_after", 60)
                await whatsapp_service.send_text_message(
                    wa_id,
                    f"🚫 Você está enviando muitas mensagens. Aguarde {retry_after} segundos antes de enviar outra mensagem."
                )
            elif limit_info.get("error") == "burst_limit_exceeded":
                await whatsapp_service.send_text_message(
                    wa_id,
                    "🚫 Muitas mensagens em pouco tempo. Por favor, aguarde um momento antes de continuar."
                )
            
            return
        
        # 🛡️ Extrair e sanitizar conteúdo da mensagem
        content = await _extract_message_content_secure(message)
        
        if not content:
            logger.warning(f"❌ Não foi possível extrair conteúdo seguro da mensagem")
            return
        
        # 🛡️ VALIDAÇÕES DE SEGURANÇA
        security_check = validate_security(content)
        
        if security_check['is_spam']:
            logger.warning(f"🚫 Possível spam detectado de {wa_id}: {content[:50]}...")
            await whatsapp_service.send_text_message(
                wa_id,
                "🚫 Mensagem identificada como spam. Por favor, envie apenas mensagens relevantes."
            )
            return
        
        if security_check['is_phishing']:
            logger.error(f"🚨 Possível phishing detectado de {wa_id}: {content[:50]}...")
            await whatsapp_service.send_text_message(
                wa_id,
                "🚫 Mensagem suspeita detectada. Entre em contato conosco por outros meios se necessário."
            )
            return
        
        # Obter ou criar usuário
        user = await UserService.get_or_create_user(
            db=db,
            wa_id=wa_id,
            nome=contact_info.get("profile", {}).get("name") if contact_info else None,
            telefone=wa_id
        )
        
        # Obter ou criar conversa
        conversation = await ConversationService.get_or_create_conversation(
            db=db, 
            user_id=user.id
        )
        
        # Verificar se a conversa está em modo humano
        if conversation.status == "human":
            logger.info(f"Conversa {conversation.id} em modo humano - mensagem ignorada pelo bot")
            # Apenas salvar a mensagem, não responder
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                direction="in",
                content=content,
                message_type=message_type,
                message_id=message_id,
                raw_payload=message
            )
            return
        
        # Salvar mensagem recebida
        await MessageService.create_message(
            db=db,
            user_id=user.id,
            conversation_id=conversation.id,
            direction="in",
            content=content,
            message_type=message_type,
            message_id=message_id,
            raw_payload=message
        )
        
        # Processar mensagem e gerar resposta
        await _process_and_respond_secure(db, user, conversation, content, message)
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem individual segura: {e}")


async def _extract_message_content_secure(message: dict) -> str:
    """
    Extrai o conteúdo da mensagem COM SANITIZAÇÃO ROBUSTA
    
    Args:
        message: Dados da mensagem (já sanitizados)
        
    Returns:
        Conteúdo extraído e sanitizado como string
    """
    try:
        message_type = message.get("type")
        content = ""
        
        if message_type == "text":
            raw_content = message.get("text", {}).get("body", "")
            content = sanitize_message(raw_content, "text")
        
        elif message_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                button_reply = interactive.get("button_reply", {})
                title = sanitize_message(button_reply.get("title", ""), "text")
                button_id = RobustValidator.sanitize_sql_input(button_reply.get("id", ""))
                content = f"{title} {button_id}".strip()
            elif interactive.get("type") == "list_reply":
                list_reply = interactive.get("list_reply", {})
                content = sanitize_message(list_reply.get("title", ""), "text")
        
        elif message_type == "audio":
            content = "[Mensagem de áudio recebida]"
        
        elif message_type == "image":
            raw_caption = message.get("image", {}).get("caption", "")
            caption = sanitize_message(raw_caption, "image") if raw_caption else ""
            content = f"[Imagem enviada] {caption}".strip()
        
        elif message_type == "document":
            doc_info = message.get("document", {})
            filename = doc_info.get("filename", "documento")
            mime_type = doc_info.get("mime_type", "")
            
            # 🛡️ Verificar se o documento é seguro
            security_check = validate_security("", filename, mime_type)
            if security_check['is_malware']:
                logger.warning(f"🚨 Possível malware detectado: {filename}")
                return "[Documento bloqueado - tipo de arquivo não permitido]"
            
            # Sanitizar nome do arquivo
            safe_filename = whatsapp_sanitizer._sanitize_filename(filename)
            content = f"[Documento enviado: {safe_filename}]"
        
        elif message_type == "video":
            raw_caption = message.get("video", {}).get("caption", "")
            caption = sanitize_message(raw_caption, "video") if raw_caption else ""
            content = f"[Vídeo enviado] {caption}".strip()
        
        elif message_type == "location":
            content = "[Localização compartilhada]"
        
        elif message_type == "contacts":
            content = "[Contato compartilhado]"
        
        else:
            content = f"[Mensagem do tipo {RobustValidator.sanitize_sql_input(str(message_type))}]"
        
        # 🛡️ Sanitização final do conteúdo
        if content:
            content = sanitize_message(content, message_type)
        
        return content or "[Conteúdo não disponível]"
        
    except Exception as e:
        logger.error(f"❌ Erro ao extrair conteúdo seguro da mensagem: {e}")
        return "[Erro no processamento da mensagem]"


async def _process_and_respond_secure(db: AsyncSession, user, conversation, content: str, original_message: dict):
    """
    Processa mensagem e gera resposta COM SANITIZAÇÃO ROBUSTA
    
    Args:
        db: Sessão do banco
        user: Usuário
        conversation: Conversa
        content: Conteúdo sanitizado da mensagem
        original_message: Mensagem original completa (já sanitizada)
    """
    try:
        message_type = original_message.get("type", "text")
        
        # 🛡️ Validação adicional do conteúdo antes do processamento
        if not content or len(content.strip()) == 0:
            logger.warning(f"❌ Conteúdo vazio após sanitização para {user.wa_id}")
            return
        
        # 🛡️ Verificação de tamanho seguro
        if len(content) > 4096:  # Limite WhatsApp
            logger.warning(f"⚠️ Conteúdo muito longo truncado para {user.wa_id}")
            content = content[:4096]
        
        # ====== VERIFICAÇÃO DE CACHE DE RESPOSTA ======
        if message_type == "text" and content:
            cached_response = await cache_service.get_cached_response(
                message=content,
                user_id=user.wa_id
            )
            
            if cached_response:
                logger.info(f"💾 Cache hit para {user.wa_id}: {content[:50]}...")
                
                # 🛡️ Sanitizar resposta do cache antes de enviar
                safe_response = sanitize_message(cached_response, "text")
                
                await whatsapp_service.send_text_message(user.wa_id, safe_response)
                
                await MessageService.create_message(
                    db=db,
                    user_id=user.id,
                    conversation_id=conversation.id,
                    direction="out",
                    content=safe_response,
                    message_type="text",
                    metadata={
                        "processing_system": "cache_service",
                        "cache_hit": True,
                        "system_used": "cache_primary",
                        "sanitized": True
                    }
                )
                
                logger.info(f"✅ Resposta segura do cache enviada para {user.wa_id}")
                return
        
        # ====== VERIFICAÇÃO DE HANDOFF INTELIGENTE ======
        handoff_decision = await intelligent_handoff_service.analyze_message_for_handoff(
            user_id=user.wa_id,
            message=content,
            conversation_history=[]  # Simplificado para exemplo
        )
        
        should_handoff, handoff_reason, handoff_config = handoff_decision
        
        if should_handoff:
            reason = str(handoff_reason.value) if handoff_reason else "Necessário atendimento humano"
            logger.info(f"🔄 Handoff para humano: {user.wa_id} - {reason}")
            
            # Atualizar status da conversa
            conversation.status = "human"
            await db.commit()
            
            # Resposta padrão sanitizada
            handoff_message = sanitize_message(
                f"📞 Entendi que você precisa de um atendimento mais personalizado. "
                f"Um de nossos atendentes entrará em contato em breve. "
                f"Motivo: {reason}",
                "text"
            )
            
            await whatsapp_service.send_text_message(user.wa_id, handoff_message)
            
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                direction="out",
                content=handoff_message,
                message_type="text",
                metadata={
                    "processing_system": "handoff",
                    "handoff_reason": reason,
                    "sanitized": True
                }
            )
            
            return
        
        # ====== PROCESSAMENTO COM LLM AVANÇADO ======
        start_time = time.time()
        response = await advanced_llm_service.process_message(
            user_id=user.wa_id,
            message=content,  # Já sanitizado
            conversation_id=conversation.id,
            message_type=message_type
        )
        
        if response and response.get("content"):
            # 🛡️ Sanitizar resposta do LLM
            safe_response = sanitize_message(response["content"], "text")
            
            # Record processing time
            processing_time = time.time() - start_time
            metrics_collector.record_webhook_processing("success", processing_time)
            
            await whatsapp_service.send_text_message(user.wa_id, safe_response)
            
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                direction="out",
                content=safe_response,
                message_type="text",
                metadata={
                    "processing_system": "advanced_llm",
                    "llm_confidence": response.get("confidence", 0),
                    "processing_time": processing_time,
                    "sanitized": True
                }
            )
            
            logger.info(f"✅ Resposta segura do LLM enviada para {user.wa_id}")
        else:
            # Record failed processing
            processing_time = time.time() - start_time
            metrics_collector.record_webhook_processing("failed", processing_time)
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento seguro para {user.wa_id}: {e}")
        
        # Record error metrics
        processing_time = time.time() - start_time if 'start_time' in locals() else 0
        metrics_collector.record_webhook_processing("error", processing_time)
        
        # Resposta de erro sanitizada
        error_message = sanitize_message(
            "🤖 Desculpe, houve um problema temporário. Tente novamente em alguns instantes.",
            "text"
        )
        
        try:
            await whatsapp_service.send_text_message(user.wa_id, error_message)
        except Exception as send_error:
            logger.error(f"❌ Erro ao enviar mensagem de erro: {send_error}")


async def _process_message_status_secure(db: AsyncSession, status: dict):
    """
    Processa status de mensagem COM SANITIZAÇÃO
    
    Args:
        db: Sessão do banco
        status: Dados do status (já sanitizados)
    """
    try:
        # 🛡️ Sanitizar dados do status
        message_id = status.get("id")
        recipient_id = status.get("recipient_id")
        status_type = status.get("status")
        
        if message_id:
            message_id = RobustValidator.sanitize_sql_input(str(message_id))[:100]
        
        if recipient_id:
            try:
                recipient_id = sanitize_phone(recipient_id)
            except ValueError:
                recipient_id = None
        
        if status_type:
            status_type = RobustValidator.sanitize_sql_input(str(status_type))[:50]
        
        logger.debug(f"✅ Status processado: {message_id} -> {status_type}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar status de mensagem seguro: {e}")


# ==================== FUNÇÕES DEPRECADAS PARA COMPATIBILIDADE ====================

async def _log_incoming_request(db: AsyncSession, payload: dict, headers: dict):
    """DEPRECATED: Use _log_incoming_request_secure instead"""
    await _log_incoming_request_secure(db, payload, headers)

async def _process_message_change(db: AsyncSession, value: dict):
    """DEPRECATED: Use _process_message_change_secure instead"""
    await _process_message_change_secure(db, value)

async def _process_single_message(db: AsyncSession, message: dict, contact_info: dict):
    """DEPRECATED: Use _process_single_message_secure instead"""
    await _process_single_message_secure(db, message, contact_info)

async def _extract_message_content(message: dict) -> str:
    """DEPRECATED: Use _extract_message_content_secure instead"""
    return await _extract_message_content_secure(message)

async def _process_and_respond(db: AsyncSession, user, conversation, content: str, original_message: dict):
    """DEPRECATED: Use _process_and_respond_secure instead"""
    await _process_and_respond_secure(db, user, conversation, content, original_message)

async def _process_message_status(db: AsyncSession, status: dict):
    """DEPRECATED: Use _process_message_status_secure instead"""
    await _process_message_status_secure(db, status)


# ==================== LOG DO SISTEMA ====================
logger.info("✅ Webhook WhatsApp carregado com sanitização robusta ativada")
logger.info("🛡️ Proteções ativas: SQL Injection, XSS, Spam, Phishing, Malware")
logger.info("🧹 Sanitização aplicada em: Payload, Números, Conteúdo, Contatos, Mídia")
