"""
Rotas do webhook para receber mensagens do WhatsApp
"""
import json
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.whatsapp import whatsapp_service
from app.services.llm_advanced import advanced_llm_service
from app.services.strategy_compatibility import hybrid_service
from app.services.dynamic_integrated_crewai import DynamicIntegratedCrewAIService
from app.services.service_validator import service_validator
from app.services.intelligent_handoff import intelligent_handoff_service
from app.services.business_data import business_data_service
from app.services.booking_workflow import BookingWorkflow
from app.services.data import (
    UserService, ConversationService, MessageService, AppointmentService
)
from app.services.rate_limiter import whatsapp_rate_limiter
from app.services.simple_cache import simple_cache
from app.models.database import MetaLog
from app.config import settings

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
    logger.info(f"  - Token esperado: '{settings.webhook_verify_token}'")
    logger.info(f"  - Challenge: {hub_challenge}")
    
    if hub_mode == "subscribe":
        challenge = whatsapp_service.verify_webhook(hub_verify_token, hub_challenge)
        if challenge:
            logger.info("✅ Webhook verificado com sucesso!")
            return int(challenge)
        else:
            logger.error(f"❌ Token não confere! Recebido: '{hub_verify_token}', Esperado: '{settings.webhook_verify_token}'")
    
    logger.error("❌ Falha na verificação do webhook")
    raise HTTPException(status_code=403, detail="Erro de verificação")


@router.post("/webhook")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Recebe mensagens do WhatsApp via webhook COM SANITIZAÇÃO ROBUSTA
    """
    try:
        # 🛡️ ETAPA 1: OBTER PAYLOAD BRUTO E VALIDAR ASSINATURA
        payload_raw = await request.body()
        
        # Validar assinatura do webhook se configurada
        signature = request.headers.get('x-hub-signature-256', '')
        if settings.webhook_secret and signature:
            is_valid_signature = whatsapp_sanitizer.validate_webhook_signature(
                signature, payload_raw.decode('utf-8'), settings.webhook_secret
            )
            if not is_valid_signature:
                logger.error("❌ Assinatura do webhook inválida")
                raise HTTPException(status_code=403, detail="Assinatura inválida")
        
        # 🛡️ ETAPA 2: PARSEAR E SANITIZAR PAYLOAD
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
        
        # 🛡️ ETAPA 3: LOG SEGURO DA REQUISIÇÃO
        await _log_incoming_request_secure(db, sanitized_payload, dict(request.headers))
        
        # 🛡️ ETAPA 4: PROCESSAR ENTRADAS SANITIZADAS
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


async def _log_incoming_request(db: AsyncSession, payload: dict, headers: dict):
    """DEPRECATED: Use _log_incoming_request_secure instead"""
    await _log_incoming_request_secure(db, payload, headers)


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


async def _process_message_change(db: AsyncSession, value: dict):
    """DEPRECATED: Use _process_message_change_secure instead"""
    await _process_message_change_secure(db, value)


async def _process_single_message_secure(db: AsyncSession, message: dict, contact_info: dict):
    """
    Processa uma mensagem individual COM SANITIZAÇÃO ROBUSTA
    
    Args:
        db: Sessão do banco
        message: Dados da mensagem (já sanitizados)
        contact_info: Informações do contato (já sanitizadas)
    """
    try:
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


async def _process_single_message(db: AsyncSession, message: dict, contact_info: dict):
    """DEPRECATED: Use _process_single_message_secure instead"""
    await _process_single_message_secure(db, message, contact_info)


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
            cached_response = simple_cache.get(
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
                        "processing_system": "simple_cache",
                        "cache_hit": True,
                        "system_used": "cache_primary",
                        "sanitized": True
                    }
                )
                
                logger.info(f"✅ Resposta segura do cache enviada para {user.wa_id}")
                return
        
        # ====== VERIFICAÇÃO DE HANDOFF INTELIGENTE ======
        handoff_decision = await intelligent_handoff_service.should_handoff_to_human(
            user_message=content,
            conversation_history=[],  # Simplificado para exemplo
            user_context={"wa_id": user.wa_id, "nome": user.nome}
        )
        
        if handoff_decision.get("should_handoff", False):
            reason = handoff_decision.get("reason", "Necessário atendimento humano")
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
        response = await advanced_llm_service.process_message(
            user_id=user.wa_id,
            message=content,  # Já sanitizado
            conversation_id=conversation.id,
            message_type=message_type
        )
        
        if response and response.get("content"):
            # 🛡️ Sanitizar resposta do LLM
            safe_response = sanitize_message(response["content"], "text")
            
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
                    "sanitized": True
                }
            )
            
            logger.info(f"✅ Resposta segura do LLM enviada para {user.wa_id}")
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento seguro para {user.wa_id}: {e}")
        
        # Resposta de erro sanitizada
        error_message = sanitize_message(
            "🤖 Desculpe, houve um problema temporário. Tente novamente em alguns instantes.",
            "text"
        )
        
        try:
            await whatsapp_service.send_text_message(user.wa_id, error_message)
        except Exception as send_error:
            logger.error(f"❌ Erro ao enviar mensagem de erro: {send_error}")


async def _extract_message_content(message: dict) -> str:
    """DEPRECATED: Use _extract_message_content_secure instead"""
    return await _extract_message_content_secure(message)


async def _process_and_respond(db: AsyncSession, user, conversation, content: str, original_message: dict):
    """DEPRECATED: Use _process_and_respond_secure instead"""
    await _process_and_respond_secure(db, user, conversation, content, original_message)


async def _process_message_status(db: AsyncSession, status: dict):
    """DEPRECATED: Use _process_message_status_secure instead"""
    await _process_message_status_secure(db, status)
    """
    Processa mensagem e gera resposta usando sistema LLM avançado
    
    Args:
        db: Sessão do banco
        user: Usuário
        conversation: Conversa
        content: Conteúdo da mensagem
        original_message: Mensagem original completa
    """
    try:
        message_type = original_message.get("type", "text")
        
        # ====== VERIFICAÇÃO DE CACHE DE RESPOSTA ======
        # Tentar obter resposta do cache (apenas para mensagens de texto simples)
        if message_type == "text" and content:
            cached_response = simple_cache.get(
                message=content,
                user_id=user.wa_id
            )
            
            if cached_response:
                logger.info(f"💾 Cache hit para {user.wa_id}: {content[:50]}...")
                
                # Enviar resposta do cache
                await whatsapp_service.send_text_message(user.wa_id, cached_response)
                
                # Salvar resposta do cache no banco
                await MessageService.create_message(
                    db=db,
                    user_id=user.id,
                    conversation_id=conversation.id,
                    direction="out",
                    content=cached_response,
                    message_type="text",
                    metadata={
                        "processing_system": "simple_cache",
                        "cache_hit": True,
                        "system_used": "cache_primary"
                    }
                )
                
                logger.info(f"✅ Resposta do cache enviada para {user.wa_id}")
                return  # PARAR AQUI - resposta do cache enviada
        
        # ====== VERIFICAÇÃO DE HANDOFF INTELIGENTE ======
        # Obter histórico da conversa para análise
        conversation_history = await MessageService.get_conversation_history(
            db=db, 
            conversation_id=conversation.id, 
            limit=10
        )
        
        # Converter histórico para formato esperado
        history_formatted = []
        if conversation_history:
            for msg in conversation_history:
                history_formatted.append({
                    "sender": "user" if msg.direction == "in" else "bot",
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                })
        
        # Verificar se deve prevenir handoff (muitos handoffs recentes)
        should_prevent, prevent_message = await intelligent_handoff_service.should_prevent_handoff(
            user_id=str(user.wa_id), 
            message=content
        )
        
        if should_prevent:
            logger.info(f"🛡️ Handoff prevenido para {user.wa_id}: {prevent_message}")
            await whatsapp_service.send_text_message(user.wa_id, prevent_message)
            return
        
        # Analisar se deve fazer handoff
        should_handoff, handoff_reason, handoff_config = await intelligent_handoff_service.analyze_message_for_handoff(
            user_id=str(user.wa_id),
            message=content,
            conversation_history=history_formatted
        )
        
        if should_handoff:
            logger.info(f"🎯 Handoff detectado: {handoff_reason} para {user.wa_id}")
            
            # Verificar se auto-escalação está habilitada
            if handoff_config.get("auto_escalate", False):
                # Marcar conversa como em modo humano
                await ConversationService.update_conversation_status(
                    db=db,
                    conversation_id=conversation.id,
                    status="human"
                )
                
                # Enviar mensagem de handoff
                handoff_message = handoff_config.get("message", "Conectando você com um atendente...")
                await whatsapp_service.send_text_message(user.wa_id, handoff_message)
                
                # Registrar handoff no banco
                await MessageService.create_message(
                    db=db,
                    user_id=user.id,
                    conversation_id=conversation.id,
                    direction="out",
                    content=f"[HANDOFF] {handoff_message}",
                    message_type="handoff",
                    metadata={
                        "handoff_reason": handoff_reason.value if handoff_reason else "unknown",
                        "escalation_level": handoff_config.get("escalation_level"),
                        "department": handoff_config.get("department"),
                        "auto_escalate": True
                    }
                )
                
                logger.info(f"✅ Conversa {conversation.id} transferida para {handoff_config.get('department', 'atendimento humano')}")
                return  # PARAR AQUI - handoff automático executado
            else:
                # Apenas sugerir handoff sem auto-escalação
                handoff_message = handoff_config.get("message", "Posso conectar você com um atendente se preferir.")
                handoff_message += "\n\nDigite 'FALAR COM ATENDENTE' se quiser ser transferido."
                
                await whatsapp_service.send_text_message(user.wa_id, handoff_message)
                
                # Continuar com processamento automático, mas marcar flag
                conversation.handoff_suggested = True
                await db.commit()
        
        # ====== PROCESSAMENTO NORMAL (se não houve handoff) ======
        
        # Verificar comandos manuais de handoff
        content_upper = content.upper().strip()
        manual_handoff_triggers = [
            "FALAR COM ATENDENTE", "QUERO FALAR COM ATENDENTE", "FALAR COM PESSOA", 
            "QUERO PESSOA", "ATENDIMENTO HUMANO", "TRANSFERIR", "ESCALACIONAR",
            "FALAR COM SUPERVISOR", "FALAR COM GERENTE"
        ]
        
        if any(trigger in content_upper for trigger in manual_handoff_triggers):
            logger.info(f"🎯 Handoff manual solicitado por {user.wa_id}: {content}")
            
            # Marcar conversa como em modo humano
            await ConversationService.update_conversation_status(
                db=db,
                conversation_id=conversation.id,
                status="human"
            )
            
            # Enviar mensagem de confirmação
            await whatsapp_service.send_text_message(
                user.wa_id, 
                "✅ Entendi! Estou conectando você com um atendente humano. Em breve alguém da nossa equipe entrará em contato."
            )
            
            # Registrar handoff manual
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                direction="out",
                content="[HANDOFF_MANUAL] Conversa transferida para atendimento humano por solicitação do usuário",
                message_type="handoff",
                metadata={
                    "handoff_reason": "manual_request",
                    "escalation_level": "general",
                    "department": "Atendimento Geral",
                    "user_request": content
                }
            )
            
            logger.info(f"✅ Handoff manual executado para {user.wa_id}")
            return  # PARAR AQUI - handoff manual executado
        
        # ====== SISTEMA DE AGENDAMENTO AVANÇADO ======
        # Verificar se a mensagem está relacionada a agendamento OU se usuário já está em processo
        booking_keywords = [
            "agendar", "agendamento", "marcar", "reservar", "horario", "horário",
            "corte", "cabelo", "barba", "manicure", "servico", "serviço",
            "hoje", "amanha", "amanhã", "semana", "dia", "hora"
        ]
        
        message_lower = content.lower()
        is_booking_related = any(keyword in message_lower for keyword in booking_keywords)
        
        # Verificar se o usuário já está em processo de agendamento ativo
        user_has_active_booking = user.wa_id in booking_workflow_instance.active_bookings
        
        if is_booking_related or user_has_active_booking:
            logger.info(f"🗓️ Mensagem de agendamento detectada para {user.wa_id}: {content}")
            
            try:
                # Usar a instância global do sistema de agendamento
                # Processar a mensagem com o workflow de agendamento
                response_text, response_buttons = await booking_workflow_instance.process_booking_step(
                    user_id=user.wa_id,
                    message=content,
                    db=db
                )
                
                if response_text:
                    # Enviar resposta do sistema de agendamento
                    if response_buttons:
                        # Verificar se response_buttons é uma estrutura completa ou lista simples
                        if isinstance(response_buttons, dict) and "action" in response_buttons:
                            # É uma estrutura completa - extrair apenas os botões
                            buttons_list = response_buttons["action"]["buttons"]
                            # Converter para formato esperado pelo send_interactive_buttons
                            simple_buttons = []
                            for btn in buttons_list:
                                if "reply" in btn:
                                    simple_buttons.append({
                                        "id": btn["reply"]["id"],
                                        "title": btn["reply"]["title"]
                                    })
                            
                            await whatsapp_service.send_interactive_buttons(
                                to=user.wa_id,
                                text=response_text,
                                buttons=simple_buttons
                            )
                        else:
                            # É uma lista simples
                            await whatsapp_service.send_interactive_buttons(
                                to=user.wa_id,
                                text=response_text,
                                buttons=response_buttons
                            )
                    else:
                        await whatsapp_service.send_text_message(
                            to=user.wa_id,
                            message=response_text
                        )
                    
                    # Salvar resposta do agendamento
                    await MessageService.create_message(
                        db=db,
                        user_id=user.id,
                        conversation_id=conversation.id,
                        content=response_text,
                        direction="out",
                        message_type="text",
                        metadata={
                            "processing_system": "booking_workflow",
                            "system_used": "booking_primary",
                            "has_buttons": response_buttons is not None
                        }
                    )
                    
                    # ====== SALVAR NO CACHE (AGENDAMENTO) ======
                    # Salvar no cache apenas se não teve botões (mensagem simples)
                    if not response_buttons and response_text:
                        simple_cache.set(
                            message=content,
                            user_id=user.wa_id,
                            response=response_text
                        )
                        logger.info(f"💾 Resposta de agendamento salva no cache para {user.wa_id}")
                    
                    logger.info(f"✅ Resposta de agendamento enviada para {user.wa_id}")
                    return  # PARAR AQUI - agendamento processado com sucesso
                else:
                    logger.warning(f"⚠️ Sistema de agendamento não retornou resposta")
                    # Continuar para o sistema híbrido se o agendamento falhou
                    
            except Exception as e:
                logger.error(f"❌ Erro no sistema de agendamento: {e}")
                # Continuar para o sistema híbrido se houver erro
        
        # Se for áudio, transcrever primeiro
        if message_type == "audio":
            audio_id = original_message.get("audio", {}).get("id")
            if audio_id:
                audio_bytes = await whatsapp_service.download_media(audio_id)
                if audio_bytes:
                    transcribed_text = await advanced_llm_service.transcribe_audio(audio_bytes)
                    if transcribed_text:
                        content = transcribed_text
                        logger.info(f"Áudio transcrito: {transcribed_text}")
                    else:
                        content = "Não foi possível transcrever o áudio. Poderia repetir por texto?"
        
        # Verificar se é um clique em botão interativo
        if original_message.get("type") == "interactive":
            interactive = original_message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                button_id = interactive.get("button_reply", {}).get("id", "")
                content = f"[BUTTON_CLICK:{button_id}] {content}"
                message_type = "button_click"
                
                # Processar ação específica do botão antes do LLM
                button_handled = await _handle_interactive_button(db, user, conversation, button_id, content)
                if button_handled:
                    # Se o botão foi processado com sucesso, não precisa passar pelo LLM
                    return  # PARAR AQUI - botão interativo processado
        
        # SISTEMA HÍBRIDO LLM + CREWAI (PRINCIPAL)
        try:
            logger.info(f"🤖 Processando mensagem '{content}' do usuário {user.wa_id}")
            
            # Usar sistema híbrido como sistema principal
            hybrid_response = await hybrid_service.process_message(
                user_id=str(user.wa_id),
                conversation_id=str(conversation.id),
                message=content,
                message_type=message_type
            )
            
            response_text = hybrid_response.get("response", "")
            interactive_buttons = hybrid_response.get("interactive_buttons", [])
            suggested_actions = hybrid_response.get("suggested_actions", [])
            
            # Log da estratégia usada
            strategy = hybrid_response.get("processing_strategy", "unknown")
            agent_used = hybrid_response.get("agent_used", "unknown")
            logger.info(f"✅ Processamento: {strategy} | Agente: {agent_used} | Tempo: {hybrid_response.get('response_time', 0):.2f}s")
            logger.info(f"💬 Resposta gerada: {response_text[:100]}...")

            # Processar ações sugeridas se existirem
            if suggested_actions:
                for action in suggested_actions:
                    await _handle_advanced_llm_action(db, user, conversation, action)

            # Enviar resposta apropriada
            if interactive_buttons:
                logger.info(f"📱 Enviando resposta com {len(interactive_buttons)} botões")
                # Enviar com botões interativos
                await whatsapp_service.send_interactive_buttons(
                    to=user.wa_id,
                    text=response_text,
                    buttons=interactive_buttons
                )
            else:
                logger.info(f"📤 Enviando resposta de texto simples")
                # Enviar texto simples
                await whatsapp_service.send_text_message(
                    to=user.wa_id,
                    message=response_text
                )

            # Salvar resposta enviada
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                content=response_text,
                direction="outbound",
                message_type="text",
                metadata={
                    "processing_strategy": strategy,
                    "agent_used": agent_used,
                    "hybrid_metadata": hybrid_response.get("metadata", {}),
                    "system_used": "hybrid_primary"
                }
            )
            
            # ====== SALVAR NO CACHE (APENAS RESPOSTAS SIMPLES) ======
            # Salvar no cache apenas se foi mensagem de texto simples sem botões
            if message_type == "text" and content and response_text and not interactive_buttons:
                simple_cache.set(
                    message=content,
                    user_id=user.wa_id,
                    response=response_text
                )
                logger.info(f"💾 Resposta salva no cache para {user.wa_id}")

            logger.info(f"✅ Resposta enviada e salva para {user.wa_id}")
            return  # PARAR AQUI - sistema híbrido processado com sucesso
            
        except Exception as e:
            logger.error(f"❌ Erro no sistema híbrido principal: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # FALLBACK 1: SISTEMA DINÂMICO CREWAI
            try:
                # Inicializar o serviço dinâmico
                dynamic_service = DynamicIntegratedCrewAIService(business_id=1)
                
                # Processar mensagem com o novo sistema dinâmico
                response_text = await dynamic_service.process_message(
                    message=content,
                    context={
                        "customer_phone": user.wa_id,
                        "customer_name": user.name,
                        "message_type": message_type,
                        "user": user,
                        "conversation": conversation
                    },
                    db_session=db
                )
                
                if response_text:
                    # Log da resposta dinâmica
                    logger.info(f"Sistema Dinâmico: Resposta processada para {user.wa_id}")
                    
                    # Enviar resposta
                    await whatsapp_service.send_text_message(
                        to=user.wa_id,
                        message=response_text
                    )
                    
                    # Salvar resposta enviada
                    await MessageService.create_message(
                        db=db,
                        user_id=user.id,
                        conversation_id=conversation.id,
                        content=response_text,
                        direction="outbound",
                        message_type="text",
                        metadata={
                            "processing_system": "dynamic_integrated_crewai",
                            "automated_response": True,
                            "system_used": "dynamic_fallback"
                        }
                    )
                    
                    # ====== SALVAR NO CACHE (SISTEMA DINÂMICO) ======
                    # Salvar no cache apenas se foi mensagem de texto simples
                    if message_type == "text" and content and response_text:
                        simple_cache.set(
                            message=content,
                            user_id=user.wa_id,
                            response=response_text
                        )
                        logger.info(f"💾 Resposta dinâmica salva no cache para {user.wa_id}")
                    
                    logger.info(f"Resposta dinâmica enviada para {user.wa_id}")
                    return  # PARAR AQUI - sistema dinâmico processado com sucesso
                else:
                    logger.warning(f"Sistema dinâmico não retornou resposta válida")
                    
            except Exception as e:
                logger.error(f"Erro no sistema dinâmico integrado: {e}")
            
            # FALLBACK 2: Sistema LLM avançado original
            try:
                logger.info(f"🔄 Usando fallback LLM avançado para {user.wa_id}")
                llm_response = await advanced_llm_service.process_message(
                    user_id=str(user.wa_id),
                    conversation_id=str(conversation.id),
                    message=content,
                    message_type=message_type
                )
                
                response_text = llm_response.text
                interactive_buttons = llm_response.interactive_buttons
                suggested_actions = llm_response.suggested_actions
                
                # Processar ações sugeridas
                if suggested_actions:
                    for action in suggested_actions:
                        await _handle_advanced_llm_action(db, user, conversation, action)
                
                # Enviar resposta apropriada
                if interactive_buttons:
                    # Enviar com botões interativos
                    await whatsapp_service.send_interactive_buttons(
                        to=user.wa_id,
                        text=response_text,
                        buttons=interactive_buttons
                    )
                else:
                    # Enviar texto simples
                    await whatsapp_service.send_text_message(
                        to=user.wa_id,
                        message=response_text
                    )
                
                # Salvar resposta enviada com metadados do LLM
                await MessageService.create_message(
                    db=db,
                    user_id=user.id,
                    conversation_id=conversation.id,
                    content=response_text,
                    direction="outbound",
                    message_type="text",
                    metadata={
                        "system_used": "advanced_llm_fallback",
                        "llm_intent": llm_response.intent.type.value if llm_response.intent else None,
                        "llm_confidence": llm_response.confidence,
                        "plugins_used": len([k for k, v in llm_response.metadata.items() if k.startswith("plugin_")]),
                        "processing_metadata": llm_response.metadata,
                        "fallback_used": True
                    }
                )
                
                # ====== SALVAR NO CACHE (LLM FALLBACK) ======
                # Salvar no cache apenas se foi mensagem de texto simples sem botões
                if message_type == "text" and content and response_text and not interactive_buttons:
                    simple_cache.set(
                        message=content,
                        user_id=user.wa_id,
                        response=response_text
                    )
                    logger.info(f"💾 Resposta LLM salva no cache para {user.wa_id}")
                
                logger.info(f"✅ Fallback LLM usado com sucesso para {user.wa_id}")
                return  # PARAR AQUI - LLM avançado processado com sucesso
                
            except Exception as fallback_error:
                logger.error(f"❌ Erro no fallback LLM para {user.wa_id}: {fallback_error}")
                
                # Resposta de erro final
                error_response = "Desculpe, estou com dificuldades técnicas no momento. Nossa equipe foi notificada. Pode tentar novamente em alguns minutos?"
                
                # Tentar enviar resposta de erro
                try:
                    await whatsapp_service.send_text_message(
                        to=user.wa_id,
                        message=error_response
                    )
                    logger.info(f"⚠️  Enviada resposta de erro para {user.wa_id}")
                except Exception as send_error:
                    logger.error(f"❌ Falha ao enviar resposta de erro: {send_error}")
                
                await MessageService.create_message(
                    db=db,
                    user_id=user.id,
                    conversation_id=conversation.id,
                    content=error_response,
                    direction="outbound",
                    message_type="error",
                    metadata={"system_error": True, "error": str(fallback_error)}
                )
                return  # PARAR AQUI - resposta de erro enviada
            
    except Exception as e:
        logger.error(f"❌ Erro geral no processamento de mensagem para {user.wa_id}: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        
        # Resposta de erro final
        error_message = "Desculpe, estou com dificuldades técnicas no momento. Tente novamente em alguns minutos."
        
        try:
            await whatsapp_service.send_text_message(
                to=user.wa_id,
                message=error_message
            )
            logger.info(f"⚠️  Enviada resposta de erro geral para {user.wa_id}")
        except Exception as send_error:
            logger.error(f"❌ Falha crítica ao enviar resposta de erro: {send_error}")
        
        try:
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                content=error_message,
                direction="outbound",
                message_type="error",
                metadata={"general_error": True, "error": str(e)}
            )
        except Exception as save_error:
            logger.error(f"❌ Falha ao salvar mensagem de erro: {save_error}")
            await whatsapp_service.send_text_message(
                to=user.wa_id,
                message=error_message
            )
            
            # Salvar mensagem de erro
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                content=error_message,
                direction="outbound",
                message_type="text",
                metadata={
                    "system_used": "general_error_fallback",
                    "error": True, 
                    "error_message": str(e)
                }
            )
        except Exception as send_error:
            logger.error(f"Erro crítico - não foi possível enviar mensagem de erro para {user.wa_id}: {send_error}")


async def _handle_advanced_llm_action(db: AsyncSession, user, conversation, action: dict):
    """
    Processa ações sugeridas pelo sistema LLM avançado
    
    Args:
        db: Sessão do banco
        user: Usuário
        conversation: Conversa
        action: Ação sugerida pelo LLM
    """
    try:
        action_type = action.get("type")
        action_data = action.get("data", {})
        priority = action.get("priority", "medium")
        
        logger.info(f"Processando ação LLM: {action_type} (prioridade: {priority})")
        
        if action_type == "create_appointment":
            # Criar agendamento
            service = action_data.get("service")
            date = action_data.get("date")
            time = action_data.get("time")
            notes = action_data.get("notes", "")
            
            if service and date and time:
                appointment = await AppointmentService.create_appointment(
                    db=db,
                    user_id=user.id,
                    service=service,
                    appointment_date=f"{date} {time}",
                    notes=f"Agendado via LLM avançado. {notes}",
                    status="pendente"
                )
                
                logger.info(f"Agendamento criado via LLM: {appointment.id}")
            
        elif action_type == "cancel_appointment":
            # Cancelar agendamento
            appointment_id = action_data.get("appointment_id")
            reason = action_data.get("reason", "Cancelado via chat")
            
            if appointment_id:
                await AppointmentService.cancel_appointment(
                    db=db,
                    appointment_id=appointment_id,
                    reason=reason
                )
                
                logger.info(f"Agendamento {appointment_id} cancelado via LLM")
        
        elif action_type == "reschedule_appointment":
            # Reagendar compromisso
            appointment_id = action_data.get("appointment_id")
            new_date = action_data.get("new_date")
            new_time = action_data.get("new_time")
            
            if appointment_id and new_date and new_time:
                await AppointmentService.reschedule_appointment(
                    db=db,
                    appointment_id=appointment_id,
                    new_date=f"{new_date} {new_time}"
                )
                
                logger.info(f"Agendamento {appointment_id} reagendado via LLM")
        
        elif action_type == "human_handoff":
            # Transferir para atendimento humano
            reason = action_data.get("reason", "Solicitado pelo usuário")
            
            # Marcar conversa para handoff
            conversation.status = "handoff_pending"
            conversation.handoff_reason = reason
            conversation.handoff_requested_at = datetime.now()
            
            db.add(conversation)
            await db.commit()
            
            logger.info(f"Handoff solicitado para conversa {conversation.id}: {reason}")
        
        elif action_type == "collect_feedback":
            # Coletar feedback do usuário
            feedback_type = action_data.get("feedback_type", "general")
            
            # Marcar conversa para coleta de feedback
            if not conversation.metadata:
                conversation.metadata = {}
            
            conversation.metadata["feedback_requested"] = {
                "type": feedback_type,
                "requested_at": datetime.now().isoformat()
            }
            
            db.add(conversation)
            await db.commit()
            
            logger.info(f"Feedback solicitado para conversa {conversation.id}")
        
        else:
            logger.warning(f"Tipo de ação não reconhecido: {action_type}")
            
    except Exception as e:
        logger.error(f"Erro ao processar ação LLM: {e}")


async def _handle_button_action(db: AsyncSession, user, conversation, button_id: str) -> dict:
    """
    Processa ação de botão clicado
    
    Args:
        db: Sessão do banco
        user: Usuário
        conversation: Conversa
        button_id: ID do botão clicado
        
    Returns:
        Dict com resposta e botões opcionais
    """
    if button_id == "confirm_schedule":
        return {
            "response": "✅ Agendamento confirmado! Você receberá uma confirmação em breve.",
            "buttons": []
        }
    
    elif button_id == "change_schedule":
        return {
            "response": "📅 Sem problemas! Por favor, me informe o novo horário desejado.",
            "buttons": []
        }
    
    elif button_id == "cancel_action":
        return {
            "response": "❌ Operação cancelada. Como posso ajudar?",
            "buttons": [
                {"id": "new_schedule", "title": "📅 Novo agendamento"},
                {"id": "human_support", "title": "👤 Falar com humano"}
            ]
        }
    
    elif button_id == "human_support":
        # Alterar status da conversa para humano
        await ConversationService.update_conversation_status(
            db=db,
            conversation_id=conversation.id,
            status="human"
        )
        return {
            "response": "👤 Você será atendido por um de nossos especialistas em breve. Aguarde que alguém entrará em contato!",
            "buttons": []
        }
    
    elif button_id == "new_schedule":
        return {
            "response": "📅 Perfeito! Vamos fazer seu agendamento. Qual serviço você gostaria?",
            "buttons": []
        }
    
    elif button_id == "check_schedule":
        # Buscar agendamentos do usuário
        appointments = await AppointmentService.get_user_appointments(
            db=db, 
            user_id=user.id
        )
        
        if appointments:
            response = "📋 Seus agendamentos:\n\n"
            for apt in appointments[:5]:  # Mostrar até 5
                status_emoji = {"pendente": "⏳", "confirmado": "✅", "cancelado": "❌"}
                emoji = status_emoji.get(apt.status, "📅")
                response += f"{emoji} {apt.service}\n"
                response += f"   Data: {apt.date_time.strftime('%d/%m/%Y às %H:%M')}\n"
                response += f"   Status: {apt.status.title()}\n\n"
        else:
            response = "📋 Você não possui agendamentos no momento."
        
        return {
            "response": response,
            "buttons": [
                {"id": "new_schedule", "title": "📅 Novo agendamento"}
            ]
        }
    
    else:
        return {
            "response": "Não entendi a opção selecionada. Como posso ajudar?",
            "buttons": []
        }


async def _handle_llm_action(db: AsyncSession, user, conversation, action: dict):
    """
    Processa ação extraída pelo LLM
    
    Args:
        db: Sessão do banco
        user: Usuário
        conversation: Conversa
        action: Ação a ser executada
    """
    try:
        action_type = action.get("type")
        action_data = action.get("data", {})
        
        if action_type == "schedule_create":
            # Criar agendamento
            service = action_data.get("service")
            date_str = action_data.get("date")
            time_str = action_data.get("time")
            notes = action_data.get("notes")
            
            if service and date_str and time_str:
                # Parsear data e hora
                datetime_str = f"{date_str} {time_str}"
                try:
                    appointment_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                    
                    # Criar agendamento
                    appointment = await AppointmentService.create_appointment(
                        db=db,
                        user_id=user.id,
                        service=service,
                        date_time=appointment_datetime,
                        notes=notes
                    )
                    
                    logger.info(f"Agendamento criado: {appointment.id}")
                    
                except ValueError as e:
                    logger.error(f"Erro ao parsear data/hora: {e}")
        
        elif action_type == "schedule_cancel":
            # Cancelar agendamento
            appointment_id = action_data.get("appointment_id")
            if appointment_id:
                await AppointmentService.update_appointment_status(
                    db=db,
                    appointment_id=appointment_id,
                    status="cancelado"
                )
                logger.info(f"Agendamento {appointment_id} cancelado")
        
        elif action_type == "handoff_human":
            # Transferir para humano
            await ConversationService.update_conversation_status(
                db=db,
                conversation_id=conversation.id,
                status="human"
            )
            logger.info(f"Conversa {conversation.id} transferida para humano")
        
    except Exception as e:
        logger.error(f"Erro ao processar ação do LLM: {e}")


async def _handle_interactive_button(db: AsyncSession, user, conversation, button_id: str, content: str) -> bool:
    """
    Processa cliques em botões interativos específicos de agendamento
    
    Args:
        db: Sessão do banco
        user: Usuário
        conversation: Conversa
        button_id: ID do botão clicado
        content: Conteúdo da mensagem
        
    Returns:
        True se o botão foi processado, False caso contrário
    """
    try:
        logger.info(f"Processando botão interativo: {button_id} para usuário {user.wa_id}")
        
        # Extrair ID do agendamento do button_id se presente
        appointment_id = None
        if "_" in button_id:
            parts = button_id.split("_")
            if len(parts) >= 2 and parts[-1].isdigit():
                appointment_id = int(parts[-1])
        
        response_text = ""
        
        # Processar diferentes tipos de botões
        if button_id.startswith("confirm_appointment"):
            if appointment_id:
                appointment = await AppointmentService.confirm_appointment(
                    db=db,
                    appointment_id=appointment_id,
                    confirmed_by="customer"
                )
                
                if appointment:
                    response_text = f"""✅ **Agendamento Confirmado!**

Seu agendamento foi confirmado com sucesso:
📅 Data: {appointment.date_time.strftime('%d/%m/%Y')}
🕐 Horário: {appointment.date_time.strftime('%H:%M')}
✨ Status: Confirmado

Estaremos esperando você! 😊

Se precisar fazer alguma alteração, é só me avisar."""
                else:
                    response_text = "❌ Não foi possível confirmar o agendamento. Por favor, entre em contato conosco."
            else:
                response_text = "❌ Agendamento não identificado. Por favor, tente novamente."
        
        elif button_id.startswith("cancel_appointment"):
            if appointment_id:
                appointment = await AppointmentService.cancel_appointment(
                    db=db,
                    appointment_id=appointment_id,
                    reason="Cancelado pelo cliente via WhatsApp",
                    cancelled_by="customer"
                )
                
                if appointment:
                    response_text = f"""❌ **Agendamento Cancelado**

Seu agendamento foi cancelado:
📅 Data: {appointment.date_time.strftime('%d/%m/%Y')}
🕐 Horário: {appointment.date_time.strftime('%H:%M')}
✨ Status: Cancelado

Não se preocupe! Você pode agendar novamente quando quiser. 
Basta me enviar uma mensagem! 😊"""
                else:
                    response_text = "❌ Não foi possível cancelar o agendamento. Por favor, entre em contato conosco."
            else:
                response_text = "❌ Agendamento não identificado. Por favor, tente novamente."
        
        elif button_id.startswith("reschedule_appointment"):
            if appointment_id:
                response_text = f"""📅 **Reagendar Agendamento**

Para reagendar seu agendamento, me informe:
• Nova data desejada (ex: 28/07/2025)
• Novo horário desejado (ex: 15:30)

Exemplo: "Gostaria de reagendar para 28/07/2025 às 15:30"

Qual seria a nova data e horário ideal para você?"""
            else:
                response_text = "❌ Agendamento não identificado. Por favor, tente novamente."
        
        elif button_id == "view_appointments":
            # Listar agendamentos do usuário
            appointments = await AppointmentService.get_user_appointments(
                db=db,
                user_id=user.id
            )
            
            if appointments:
                response_text = "📋 **Seus Agendamentos:**\n\n"
                for apt in appointments[:5]:  # Mostrar até 5 agendamentos
                    status_emoji = {
                        "pendente": "⏳",
                        "confirmado": "✅", 
                        "cancelado": "❌",
                        "concluido": "✅",
                        "reagendado": "🔄"
                    }.get(apt.status, "📅")
                    
                    response_text += f"{status_emoji} {apt.date_time.strftime('%d/%m/%Y %H:%M')}\n"
                    response_text += f"   Status: {apt.status.title()}\n\n"
            else:
                response_text = "📋 Você não possui agendamentos no momento.\n\nGostaria de fazer um novo agendamento?"
        
        elif button_id == "new_appointment":
            response_text = """📅 **Novo Agendamento**

Para agendar um horário, me informe:
• Que serviço você gostaria? (ex: corte, barba, etc.)
• Qual data você prefere? (ex: amanhã, 26/07/2025)
• Qual horário? (ex: 14:00, tarde)

Exemplo: "Quero agendar um corte para amanhã às 14h"

Como posso ajudar você?"""
        
        else:
            # Botão não reconhecido, deixar o LLM processar
            return False
        
        # Enviar resposta se foi processada
        if response_text:
            await whatsapp_service.send_text_message(
                to=user.wa_id,
                message=response_text
            )
            
            # Salvar resposta
            await MessageService.create_message(
                db=db,
                user_id=user.id,
                conversation_id=conversation.id,
                direction="out",
                content=response_text,
                message_type="text",
                metadata={
                    "button_processed": button_id,
                    "appointment_id": appointment_id,
                    "automated_response": True
                }
            )
            
            logger.info(f"Botão {button_id} processado com sucesso para usuário {user.wa_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Erro ao processar botão interativo {button_id}: {e}")
        return False


async def _process_message_status(db: AsyncSession, status: dict):
    """
    Processa status de mensagens (entregue, lida, etc.)
    
    Args:
        db: Sessão do banco
        status: Dados do status
    """
    try:
        # Log do status (para métricas futuras)
        logger.info(f"Status da mensagem: {status}")
        
        # Aqui poderia implementar lógica para marcar mensagens como lidas,
        # calcular tempo de resposta, etc.
        
    except Exception as e:
        logger.error(f"Erro ao processar status da mensagem: {e}")

@router.post("/api/whatsapp/send")
async def send_message_endpoint(
    to: str,
    message: str,
    type: str = "text",
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para envio de mensagens via WhatsApp API
    Usado pelo dashboard para envio manual de mensagens
    """
    try:
        # Validar número do WhatsApp
        if not to:
            raise HTTPException(status_code=400, detail="Número de destino é obrigatório")
        
        # Limpar e validar número
        wa_id = validate_whatsapp_number(to)
        
        # Validar mensagem
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Mensagem não pode estar vazia")
        
        # Verificar rate limit
        if not await whatsapp_rate_limiter.check_rate_limit(wa_id):
            raise HTTPException(
                status_code=429, 
                detail="Rate limit excedido. Tente novamente em alguns segundos."
            )
        
        # Enviar mensagem via WhatsApp service
        result = await whatsapp_service.send_text_message(wa_id, message.strip())
        
        if "error" in result:
            logger.error(f"Erro ao enviar mensagem para {wa_id}: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Erro no envio: {result['error']}")
        
        # Salvar mensagem no banco de dados
        try:
            # Buscar ou criar usuário
            user_service = UserService(db)
            user = await user_service.get_or_create_user(wa_id, wa_id)
            
            # Salvar mensagem enviada
            message_service = MessageService(db)
            await message_service.create_message(
                user_id=user.id,
                wa_message_id=result.get('messages', [{}])[0].get('id', ''),
                message_type="text",
                content=message.strip(),
                direction="outbound",
                status="sent"
            )
            
            logger.info(f"Mensagem enviada com sucesso para {wa_id} via dashboard")
            
        except Exception as db_error:
            logger.error(f"Erro ao salvar mensagem no banco: {db_error}")
            # Não falhar o endpoint se der erro no banco, a mensagem já foi enviada
        
        return {
            "success": True,
            "message": "Mensagem enviada com sucesso",
            "wa_id": wa_id,
            "message_id": result.get('messages', [{}])[0].get('id'),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao enviar mensagem: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
