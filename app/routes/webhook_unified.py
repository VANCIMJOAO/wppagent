"""
🔧 WEBHOOK SIMPLIFICADO COM SISTEMA UNIFICADO
============================================

Versão limpa e otimizada que usa apenas o sistema unificado de controle,
eliminando sobreposições e redundâncias.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import MetaLog
from app.services.data import ConversationService, MessageService, UserService
from app.services.entity_extractor import entity_extractor
from app.services.auto_booking import auto_booking_service
from app.services.response_control import get_unified_response_control

# 🔥 WebSocket Integration
from app.services.websocket_integration import (
    notify_message_sent,
    notify_new_whatsapp_message,
)
from app.services.whatsapp import whatsapp_service
from app.utils.logger import get_logger
from app.utils.whatsapp_data_extractor import (
    sanitize_message,
    sanitize_phone,
    sanitize_whatsapp_data,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])


# Sistema de resposta simplificado
class AIResponseGenerator:
    """Gerador de respostas usando OpenAI GPT-4"""
    
    def __init__(self):
        from openai import AsyncOpenAI
        
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
        
        self.system_prompt = """Você é um assistente virtual do Studio Beleza Bem-Estar, uma clínica de estética e bem-estar.

INFORMAÇÕES DA CLÍNICA:
- Nome: Studio Beleza Bem-Estar
- Horário: Segunda a Sexta 8h-18h, Sábado 8h-14h
- Endereço: Rua das Flores, 123 - Centro
- Telefone: (16) 3333-4444

SERVIÇOS DISPONÍVEIS:
🔹 Limpeza de Pele - R$ 80,00 (60 min)
🔹 Hidrofacial - R$ 150,00 (75 min)
🔹 Criolipólise - R$ 300,00 (60 min)
🔹 Massagem Relaxante - R$ 120,00 (60 min)
🔹 Drenagem Linfática - R$ 100,00 (50 min)
🔹 Peeling - R$ 130,00 (45 min)

POLÍTICA DE AGENDAMENTO:
- Agendamentos com 24h de antecedência
- Cancelamento até 2h antes (sem taxa)
- Reagendamento: até 2x por mês
- Aceita: Dinheiro, PIX, Cartão

INSTRUÇÕES:
1. Seja simpático, profissional e prestativo
2. Use emojis moderadamente (1-2 por mensagem)
3. Respostas curtas e objetivas (máx 3 linhas)
4. Se não souber, ofereça contato telefônico
5. Ao falar de agendamento, sugira horários disponíveis
6. Sempre finalize oferecendo mais ajuda

IMPORTANTE: Mantenha tom conversacional e natural."""

        self.conversation_history = {}  # {phone: [messages]}
        
    async def generate_single_response(self, message: str, phone: str = None) -> str:
        """Gera resposta usando GPT-4 com contexto"""
        
        try:
            # Inicializar histórico se necessário
            if phone and phone not in self.conversation_history:
                self.conversation_history[phone] = []
            
            # Adicionar mensagem ao histórico
            if phone:
                self.conversation_history[phone].append({
                    "role": "user",
                    "content": message
                })
                
                # Limitar histórico a últimas 10 mensagens
                if len(self.conversation_history[phone]) > 10:
                    self.conversation_history[phone] = self.conversation_history[phone][-10:]
            
            # Montar mensagens para API
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            if phone and phone in self.conversation_history:
                messages.extend(self.conversation_history[phone])
            else:
                messages.append({"role": "user", "content": message})
            
            # Chamar OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-5-nano",  # Modelo nano - mais rápido e econômico
                messages=messages,
                max_completion_tokens=150,  # gpt-5-nano usa max_completion_tokens
                temperature=0.7,
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # Adicionar resposta ao histórico
            if phone:
                self.conversation_history[phone].append({
                    "role": "assistant",
                    "content": bot_response
                })
            
            logger.info(f"🤖 GPT-4 gerou resposta: {bot_response[:50]}...")
            
            return bot_response
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta GPT-4: {e}")
            # Fallback para resposta simples
            return "Desculpe, estou com dificuldades no momento. Por favor, entre em contato pelo telefone (16) 3333-4444. 😊"


response_generator = AIResponseGenerator()


@router.post("/clear-memory/{phone}")
async def clear_memory(phone: str):
    """Limpa memória do GPT-4 para um telefone específico (útil para testes)"""
    if phone in response_generator.conversation_history:
        del response_generator.conversation_history[phone]
        logger.info(f"🧹 Memória limpa para {phone}")
        return {"status": "success", "message": f"Memória limpa para {phone}"}
    return {"status": "info", "message": f"Nenhuma memória encontrada para {phone}"}


@router.post("")
async def webhook_endpoint(request: Request, db: AsyncSession = Depends(get_db)):
    """
    🔧 Endpoint principal do webhook - Versão unificada e otimizada
    """
    try:
        # Obter dados do webhook
        raw_data = await request.json()
        logger.info(f"📥 Webhook recebido: {json.dumps(raw_data, indent=2)[:500]}...")

        # Log para auditoria
        log_entry = MetaLog(
            direction="in",
            endpoint="/webhook",
            method="POST",
            payload=raw_data
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

        logger.info(
            f"✅ Webhook finalizado: {total_processed} processadas, {total_blocked} bloqueadas"
        )

        return {
            "status": "success",
            "processed": total_processed,
            "blocked": total_blocked,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"❌ Erro no webhook: {e}")
        logger.error(f"Traceback: {error_details}")
        return {"status": "error", "error": str(e), "traceback": error_details[:500]}


async def process_single_message(
    message_data: Dict[str, Any], db: AsyncSession
) -> Dict[str, Any]:
    """Processa uma única mensagem com controle unificado"""

    try:
        # Sanitizar dados
        wa_id, clean_content, contact_info = sanitize_whatsapp_data(message_data)

        if not wa_id or not clean_content:
            return {"processed": False, "reason": "invalid_data"}

        # 🔧 CONTROLE UNIFICADO - Verificação única
        can_process, reason = await get_unified_response_control().can_process_message(
            wa_id, clean_content
        )

        if not can_process:
            logger.warning(f"🚫 BLOQUEADO: {wa_id} - {reason}")
            return {"processed": False, "reason": reason}

        logger.info(f"📨 PROCESSANDO: {wa_id} - {clean_content[:50]}...")

        # Criar/buscar usuário
        user = await UserService.get_or_create_user(
            db=db,
            wa_id=wa_id,
            nome=contact_info.get("name"),
            telefone=sanitize_phone(wa_id),
        )

        # Criar/buscar conversa
        conversation = await ConversationService.get_or_create_conversation(
            db=db, user_id=user.id
        )

        # Salvar mensagem recebida
        await MessageService.create_message(
            db=db,
            user_id=user.id,
            conversation_id=conversation.id,
            direction="in",
            content=clean_content,
            message_type=message_data.get("type", "text"),
            raw_payload=message_data,
        )

        # Gerar e enviar resposta com contexto (GPT-4)
        response_text = await response_generator.generate_single_response(clean_content, wa_id)

        # Enviar via WhatsApp
        whatsapp_response = await whatsapp_service.send_text_message(
            wa_id, response_text
        )

        # ✅ SEMPRE salvar mensagem OUT (independente de envio WhatsApp)
        # Importante para testes e auditoria
        await MessageService.create_message(
            db=db,
            user_id=user.id,
            conversation_id=conversation.id,
            direction="out",
            content=response_text,
            message_type="text",
            raw_payload=whatsapp_response,
        )

        # 🧠 EXTRAÇÃO DE DADOS - Capturar informações da conversa
        try:
            # Carregar serviços (cache na primeira vez)
            if not entity_extractor.services_map:
                await entity_extractor.load_services(db)
            
            # Montar histórico de mensagens para contexto
            conversation_messages = [
                {"role": "user", "content": clean_content},
                {"role": "assistant", "content": response_text}
            ]
            
            # Adicionar histórico do GPT-4 se existir
            if wa_id in response_generator.conversation_history:
                conversation_messages = response_generator.conversation_history[wa_id][-6:]  # Últimas 6 msgs
            
            # Extrair dados
            extracted_data = await entity_extractor.extract_from_messages(
                messages=conversation_messages,
                conversation_history=None
            )
            
            # Salvar apenas se tiver dados relevantes (confidence > 0.3)
            if extracted_data.get("confidence", 0) > 0.3:
                saved_data = await entity_extractor.save_extraction(
                    db=db,
                    conversation_id=conversation.id,
                    user_id=user.id,
                    extracted_data=extracted_data
                )
                
                if saved_data:
                    logger.info(f"🎯 DADOS EXTRAÍDOS: Nome={extracted_data.get('customer_name')}, Serviço={extracted_data.get('service_name')}, Data={extracted_data.get('appointment_date')}, Hora={extracted_data.get('appointment_time')}")
                    
                    # 📅 AGENDAMENTO AUTOMÁTICO - Tentar criar se tiver dados completos
                    try:
                        success, message, appointment = await auto_booking_service.try_auto_book(
                            db=db,
                            user_id=user.id,
                            conversation_id=conversation.id,
                            collected_data=saved_data.collected_data
                        )
                        
                        if success and appointment:
                            # Buscar nome do serviço
                            from app.models.database import Service
                            from sqlalchemy import select as sql_select
                            result_svc = await db.execute(
                                sql_select(Service).where(Service.id == appointment.service_id)
                            )
                            service = result_svc.scalar_one_or_none()
                            service_name = service.name if service else "Serviço"
                            
                            # Gerar mensagem de confirmação
                            confirmation_msg = auto_booking_service.format_confirmation_message(
                                appointment=appointment,
                                service_name=service_name,
                                user_name=extracted_data.get('customer_name')
                            )
                            
                            # Enviar confirmação via WhatsApp
                            confirm_response = await whatsapp_service.send_text_message(
                                wa_id, confirmation_msg
                            )
                            
                            # Salvar mensagem de confirmação
                            await MessageService.create_message(
                                db=db,
                                user_id=user.id,
                                conversation_id=conversation.id,
                                direction="out",
                                content=confirmation_msg,
                                message_type="text",
                                raw_payload=confirm_response,
                            )
                            
                            logger.info(f"🎉 AGENDAMENTO AUTOMÁTICO CRIADO! ID: {appointment.id}")
                        else:
                            logger.debug(f"⏸️ Agendamento não criado: {message}")
                            
                    except Exception as booking_error:
                        logger.error(f"❌ Erro no agendamento automático: {booking_error}")
                        # Não falhar o webhook se agendamento falhar
                        pass
            else:
                logger.debug(f"⚠️ Confidence baixa ({extracted_data.get('confidence')}), dados não salvos")
                
        except Exception as e:
            logger.error(f"❌ Erro na extração de dados: {e}")
            # Não falhar o webhook se extração falhar
            pass

        # Atualizar conversa
        conversation.last_message_at = datetime.utcnow()
        await db.commit()

        # Notificações WebSocket
        try:
            await notify_new_whatsapp_message(user.wa_id, clean_content)
            await notify_message_sent(user.wa_id, response_text)
        except Exception as ws_error:
            logger.warning(f"⚠️ WebSocket notification failed: {ws_error}")

        # Log baseado no resultado do envio
        if whatsapp_response.get("success") or whatsapp_response.get("status") == "queued":
            logger.info(f"✅ SUCESSO: {wa_id} - Resposta salva (WhatsApp: {whatsapp_response.get('status', 'success')})")
            return {"processed": True, "response_sent": True, "response_saved": True}
        else:
            logger.warning(f"⚠️ Resposta salva mas envio WhatsApp falhou: {whatsapp_response}")
            return {"processed": True, "response_sent": False, "response_saved": True}

    except Exception as e:
        logger.error(f"❌ Erro processando mensagem: {e}")
        return {"processed": False, "reason": f"error: {str(e)}"}


@router.get("/verify")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Verificação do webhook do WhatsApp"""

    # Verificar token (use uma variável de ambiente em produção)
    expected_token = "your_verify_token_here"  # TODO: Mover para config

    if not hub_mode or not hub_challenge or not hub_verify_token:
        logger.warning("❌ Parâmetros de verificação ausentes")
        raise HTTPException(status_code=400, detail="Parâmetros hub.mode, hub.challenge e hub.verify_token são obrigatórios")

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("✅ Webhook verificado com sucesso")
        # Meta espera o challenge de volta como plain text integer
        return Response(content=hub_challenge, media_type="text/plain")
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
        "timestamp": datetime.utcnow().isoformat(),
    }
