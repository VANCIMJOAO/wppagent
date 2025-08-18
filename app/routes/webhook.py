"""
🚨 WEBHOOK CORRIGIDO - CONTROLE DE RESPOSTA ÚNICA
===============================================

Este webhook foi criado para resolver o problema crítico de múltiplas respostas
simultâneas que estava acontecendo no sistema anterior.

CORREÇÕES IMPLEMENTADAS:
1. 🛑 Controle Global de Resposta Única
2. 🎯 Roteamento Simplificado
3. 🧹 Sistema de Limpeza Automática
4. 📊 Monitoramento de Efetividade

"""
import asyncio
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.logger import get_logger
from app.services.whatsapp import whatsapp_service
from app.services.data import UserService, ConversationService, MessageService
from app.utils.whatsapp_sanitizer import sanitize_whatsapp_data, sanitize_message, sanitize_phone
from app.models.database import MetaLog
from app.config import settings

logger = get_logger(__name__)

# 🚨 CONTROLE GLOBAL DE RESPOSTA ÚNICA
GLOBAL_RESPONSE_CONTROL = {
    'active_responses': {},  # user_id -> timestamp
    'processing_locks': {},  # user_id -> asyncio.Lock
    'message_cache': {},     # message_key -> response_data
    'stats': {
        'messages_processed': 0,
        'messages_blocked': 0,
        'responses_sent': 0,
        'duplicates_prevented': 0,
        'errors': 0
    }
}

def get_message_key(user_id: str, content: str) -> str:
    """Gera chave única para mensagem"""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    timestamp_window = int(time.time() / 10)  # Janela de 10 segundos
    return f"{user_id}_{content_hash}_{timestamp_window}"

async def ensure_single_response(user_id: str, message_content: str) -> bool:
    """
    🛑 GARANTE QUE APENAS UMA RESPOSTA SERÁ PROCESSADA POR MENSAGEM
    
    Returns:
        True: Deve processar a mensagem
        False: Deve ignorar (duplicada ou em processamento)
    """
    message_key = get_message_key(user_id, message_content)
    
    # Criar lock para este usuário se não existir
    if user_id not in GLOBAL_RESPONSE_CONTROL['processing_locks']:
        GLOBAL_RESPONSE_CONTROL['processing_locks'][user_id] = asyncio.Lock()
    
    async with GLOBAL_RESPONSE_CONTROL['processing_locks'][user_id]:
        current_time = time.time()
        
        # Verificar se já processamos mensagem similar
        if message_key in GLOBAL_RESPONSE_CONTROL['message_cache']:
            cache_entry = GLOBAL_RESPONSE_CONTROL['message_cache'][message_key]
            if current_time - cache_entry['timestamp'] < 15:  # 15 segundos de cache
                logger.info(f"🔄 Ignorando mensagem duplicada: {message_key}")
                GLOBAL_RESPONSE_CONTROL['stats']['messages_blocked'] += 1
                GLOBAL_RESPONSE_CONTROL['stats']['duplicates_prevented'] += 1
                return False
        
        # Verificar se há resposta ativa recente
        if user_id in GLOBAL_RESPONSE_CONTROL['active_responses']:
            last_response_time = GLOBAL_RESPONSE_CONTROL['active_responses'][user_id]
            if current_time - last_response_time < 3:  # 3 segundos entre respostas
                logger.info(f"🔄 Ignorando - resposta muito recente para {user_id}")
                GLOBAL_RESPONSE_CONTROL['stats']['messages_blocked'] += 1
                return False
        
        # Marcar como processando
        GLOBAL_RESPONSE_CONTROL['message_cache'][message_key] = {
            'timestamp': current_time,
            'processing': True,
            'user_id': user_id
        }
        
        GLOBAL_RESPONSE_CONTROL['active_responses'][user_id] = current_time
        GLOBAL_RESPONSE_CONTROL['stats']['messages_processed'] += 1
        
        logger.info(f"✅ Permitindo processamento para {user_id}: {message_key}")
        return True

def mark_response_sent(user_id: str, message_content: str, response: str):
    """Marca que resposta foi enviada"""
    message_key = get_message_key(user_id, message_content)
    
    if message_key in GLOBAL_RESPONSE_CONTROL['message_cache']:
        GLOBAL_RESPONSE_CONTROL['message_cache'][message_key].update({
            'response': response,
            'processing': False,
            'sent_at': time.time()
        })
    
    GLOBAL_RESPONSE_CONTROL['active_responses'][user_id] = time.time()
    GLOBAL_RESPONSE_CONTROL['stats']['responses_sent'] += 1
    logger.info(f"✅ Resposta marcada como enviada para {user_id}")

# ================================
# SISTEMA DE RESPOSTA SIMPLIFICADO
# ================================

class SimplifiedResponseGenerator:
    """Gerador de respostas simplificado para controle único"""
    
    def __init__(self):
        self.response_patterns = {
            'greeting': [
                'oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'tudo bem', 'tchau', 'até'
            ],
            'services': [
                'serviço', 'tratamento', 'procedimento', 'o que vocês fazem', 'quais serviços',
                'lista de serviços', 'oferece', 'especialidade'
            ],
            'price': [
                'preço', 'valor', 'quanto custa', 'custa quanto', 'investimento', 'orçamento',
                'tabela', 'custo', 'taxa'
            ],
            'booking': [
                'agendar', 'marcar', 'quero agendar', 'preciso agendar', 'disponibilidade',
                'horário livre', 'marcar consulta'
            ],
            'info': [
                'horário', 'funcionamento', 'endereço', 'onde', 'localização', 'telefone',
                'contato', 'como chegar'
            ],
            'more_services': [
                'mais serviço', 'outros serviços', 'mais opções', 'parte 2'
            ]
        }
        
        self.responses = {
            'greeting': "Olá! Como posso ajudar você hoje no Studio Beleza Bem-Estar? 🌟",
            'services': """📋 Aqui estão nossos serviços disponíveis:

🔹 Limpeza de Pele Profunda - R$ 80,00 (60 min)
🔹 Hidrofacial - R$ 150,00 (75 min)  
🔹 Radiofrequência - R$ 200,00 (45 min)
🔹 Criolipólise - R$ 300,00 (60 min)
🔹 Massagem Relaxante - R$ 120,00 (60 min)
🔹 Massagem Modeladora - R$ 140,00 (60 min)
🔹 Design de Sobrancelhas - R$ 40,00 (30 min)
🔹 Depilação - R$ 60,00 (45 min)

Digite "mais serviços" para ver mais opções! 😊""",
            
            'more_services': """📋 Mais serviços disponíveis:

🔹 Peeling Químico - R$ 180,00 (50 min)
🔹 Microagulhamento - R$ 250,00 (60 min)
🔹 Drenagem Linfática - R$ 100,00 (60 min)
🔹 Reflexologia - R$ 90,00 (45 min)
🔹 Aromaterapia - R$ 110,00 (50 min)
🔹 Tratamento Capilar - R$ 85,00 (45 min)
🔹 Manicure e Pedicure - R$ 50,00 (60 min)
🔹 Maquiagem - R$ 70,00 (40 min)

Qual serviço te interessa? 💆‍♀️""",
            
            'price': """💰 Aqui está a informação sobre preços:

🏷️ TRATAMENTOS FACIAIS:
• Limpeza de Pele - R$ 80,00
• Hidrofacial - R$ 150,00
• Peeling Químico - R$ 180,00

🏷️ TRATAMENTOS CORPORAIS:
• Massagem Relaxante - R$ 120,00
• Criolipólise - R$ 300,00
• Radiofrequência - R$ 200,00

Qual serviço específico te interessa? Posso dar mais detalhes! 😊""",
            
            'booking': """📅 Vamos agendar seu serviço!

Para fazer seu agendamento, preciso saber:
🔸 Qual serviço você deseja?
🔸 Que dia prefere?
🔸 Qual horário funciona melhor?
🔸 Seu nome completo

Nossos horários disponíveis:
• Segunda a Sexta: 9h às 18h
• Sábado: 9h às 16h
• Domingo: Fechado

Qual serviço gostaria de agendar? 💆‍♀️""",
            
            'info': """🏢 Aqui estão as informações da empresa:

📍 **Endereço:**
Rua das Flores, 123 - Centro
São Paulo - SP

📞 **Contato:**
(11) 98765-4321

🕐 **Horário de Funcionamento:**
• Segunda a Sexta: 9h às 18h
• Sábado: 9h às 16h  
• Domingo: Fechado

🚗 **Estacionamento:** Disponível na rua
🚌 **Transporte:** Próximo ao metrô e pontos de ônibus

Como posso ajudar mais? 😊""",
            
            'default': "Como posso ajudar você? 😊\n\nPosso falar sobre nossos serviços, preços, agendamentos ou informações da empresa!"
        }
    
    def generate_single_response(self, message: str) -> str:
        """Gera UMA única resposta para a mensagem"""
        message_lower = message.lower().strip()
        
        # Verificar comando especial primeiro
        if 'mais serviço' in message_lower or 'outros serviços' in message_lower or 'parte 2' in message_lower:
            return self.responses['more_services']
        
        # Detectar intenção principal com prioridade
        intent_scores = {}
        
        for intent, patterns in self.response_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in message_lower:
                    score += len(pattern.split())  # Palavras maiores têm mais peso
            
            if score > 0:
                intent_scores[intent] = score
        
        # Selecionar intenção com maior score
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            return self.responses[best_intent]
        
        return self.responses['default']

# Instância global
response_generator = SimplifiedResponseGenerator()

# ================================
# LIMPEZA AUTOMÁTICA
# ================================

async def cleanup_response_control():
    """Limpa controles antigos periodicamente"""
    current_time = time.time()
    
    # Limpar cache antigo (mais de 1 hora)
    old_keys = [
        key for key, data in GLOBAL_RESPONSE_CONTROL['message_cache'].items()
        if current_time - data['timestamp'] > 3600
    ]
    
    for key in old_keys:
        del GLOBAL_RESPONSE_CONTROL['message_cache'][key]
    
    # Limpar respostas ativas antigas (mais de 5 minutos)
    old_users = [
        user_id for user_id, timestamp in GLOBAL_RESPONSE_CONTROL['active_responses'].items()
        if current_time - timestamp > 300
    ]
    
    for user_id in old_users:
        del GLOBAL_RESPONSE_CONTROL['active_responses'][user_id]
        # Também limpar locks antigos
        if user_id in GLOBAL_RESPONSE_CONTROL['processing_locks']:
            del GLOBAL_RESPONSE_CONTROL['processing_locks'][user_id]
    
    logger.info(f"🧹 Limpeza: removidos {len(old_keys)} caches e {len(old_users)} respostas ativas")

# ================================
# WEBHOOK CORRIGIDO
# ================================

router = APIRouter()

@router.get("/webhook")
async def verify_webhook_corrected(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Verificação do webhook (mantida do original)"""
    logger.info(f"🔍 Verificação webhook recebida:")
    logger.info(f"  - Mode: {hub_mode}")
    logger.info(f"  - Token recebido: '{hub_verify_token}'")
    
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

@router.post("/webhook")
async def receive_webhook_corrected(request: Request, db: AsyncSession = Depends(get_db)):
    """
    🚨 WEBHOOK CORRIGIDO QUE ENVIA APENAS UMA RESPOSTA POR MENSAGEM
    """
    try:
        # 1. Validar e parsear payload
        payload_raw = await request.body()
        
        try:
            payload_dict = json.loads(payload_raw)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Payload JSON inválido: {e}")
            raise HTTPException(status_code=400, detail="JSON inválido")
        
        # 2. Sanitizar payload
        try:
            sanitized_payload = sanitize_whatsapp_data(payload_dict)
            logger.info("✅ Payload WhatsApp sanitizado com sucesso")
        except ValueError as e:
            logger.error(f"❌ Falha na sanitização do payload: {e}")
            raise HTTPException(status_code=400, detail=f"Payload inseguro: {str(e)}")
        
        # 3. Log da requisição
        await log_incoming_request_safe(db, sanitized_payload, dict(request.headers))
        
        # 4. Processar entradas
        if "entry" in sanitized_payload:
            for entry in sanitized_payload["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            await process_single_message_corrected(db, change["value"])
        
        return {"status": "ok"}
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"❌ Erro crítico no webhook corrigido: {e}")
        GLOBAL_RESPONSE_CONTROL['stats']['errors'] += 1
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

async def log_incoming_request_safe(db: AsyncSession, payload: dict, headers: dict):
    """Registra requisição de forma segura"""
    try:
        # Sanitizar headers
        safe_headers = {}
        for key, value in headers.items():
            if isinstance(key, str) and isinstance(value, str):
                safe_key = key[:100]
                safe_value = value[:500]
                safe_headers[safe_key] = safe_value
        
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
        logger.error(f"❌ Erro ao salvar log: {e}")

async def process_single_message_corrected(db: AsyncSession, value: dict):
    """🎯 Processa mensagem com controle de resposta única"""
    try:
        if "messages" not in value:
            return
        
        # Processar contatos se disponível
        contacts = value.get("contacts", [])
        contact_info = {}
        if contacts:
            contact = contacts[0]
            if "profile" in contact and "name" in contact["profile"]:
                contact_info["name"] = contact["profile"]["name"]
        
        for message in value["messages"]:
            # Extrair dados básicos
            wa_id = message.get("from")
            content = extract_message_content_safe(message)
            message_id = message.get("id")
            
            if not wa_id or not content:
                logger.warning("❌ Mensagem sem wa_id ou conteúdo")
                continue
            
            # Sanitizar dados
            try:
                clean_wa_id = sanitize_phone(wa_id)
                clean_content = sanitize_message(content, "text")
            except ValueError as e:
                logger.error(f"❌ Dados inválidos: {e}")
                continue
            
            # 🚨 CONTROLE DE RESPOSTA ÚNICA CRÍTICO
            should_process = await ensure_single_response(clean_wa_id, clean_content)
            if not should_process:
                logger.info(f"🔄 Mensagem ignorada - controle de resposta única: {clean_wa_id}")
                continue
            
            logger.info(f"📨 Processando mensagem de {clean_wa_id}: {clean_content[:50]}...")
            
            # Obter/criar usuário e conversa
            user = await UserService.get_or_create_user(
                db=db, 
                wa_id=clean_wa_id, 
                nome=contact_info.get("name"), 
                telefone=clean_wa_id
            )
            
            conversation = await ConversationService.get_or_create_conversation(
                db=db, user_id=user.id
            )
            
            # Verificar se conversa está em modo humano
            if conversation.status == "human":
                logger.info(f"Conversa {conversation.id} em modo humano - ignorando")
                # Apenas salvar mensagem, não responder
                await MessageService.create_message(
                    db=db, user_id=user.id, conversation_id=conversation.id,
                    direction="in", content=clean_content, message_type="text",
                    message_id=message_id
                )
                continue
            
            # Salvar mensagem recebida
            await MessageService.create_message(
                db=db, user_id=user.id, conversation_id=conversation.id,
                direction="in", content=clean_content, message_type="text",
                message_id=message_id
            )
            
            # 🎯 GERAR UMA ÚNICA RESPOSTA
            start_time = time.time()
            response = response_generator.generate_single_response(clean_content)
            
            # Sanitizar resposta
            safe_response = sanitize_message(response, "text")
            
            # 🚨 ENVIAR APENAS UMA RESPOSTA
            try:
                send_result = await whatsapp_service.send_text_message(clean_wa_id, safe_response)
                
                if send_result and "error" not in send_result:
                    # Salvar resposta enviada
                    await MessageService.create_message(
                        db=db, user_id=user.id, conversation_id=conversation.id,
                        direction="out", content=safe_response, message_type="text",
                        metadata={
                            "system": "corrected_single_response",
                            "response_time": time.time() - start_time,
                            "timestamp": time.time(),
                            "whatsapp_response": send_result
                        }
                    )
                    
                    # Marcar como enviada
                    mark_response_sent(clean_wa_id, clean_content, safe_response)
                    
                    logger.info(f"✅ ÚNICA resposta enviada para {clean_wa_id}")
                else:
                    logger.error(f"❌ Falha no envio para {clean_wa_id}: {send_result}")
                    GLOBAL_RESPONSE_CONTROL['stats']['errors'] += 1
                
            except Exception as send_error:
                logger.error(f"❌ Erro ao enviar resposta para {clean_wa_id}: {send_error}")
                GLOBAL_RESPONSE_CONTROL['stats']['errors'] += 1
                
    except Exception as e:
        logger.error(f"❌ Erro no processamento da mensagem: {e}")
        GLOBAL_RESPONSE_CONTROL['stats']['errors'] += 1

def extract_message_content_safe(message: dict) -> str:
    """Extrai conteúdo da mensagem de forma segura"""
    try:
        message_type = message.get("type", "text")
        
        if message_type == "text":
            return message.get("text", {}).get("body", "")
        elif message_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                return interactive.get("button_reply", {}).get("title", "")
            elif interactive.get("type") == "list_reply":
                return interactive.get("list_reply", {}).get("title", "")
        elif message_type == "audio":
            return "[Mensagem de áudio recebida]"
        elif message_type == "image":
            caption = message.get("image", {}).get("caption", "")
            return f"[Imagem enviada] {caption}".strip()
        elif message_type == "document":
            filename = message.get("document", {}).get("filename", "documento")
            return f"[Documento enviado: {filename}]"
        elif message_type == "video":
            caption = message.get("video", {}).get("caption", "")
            return f"[Vídeo enviado] {caption}".strip()
        elif message_type == "location":
            return "[Localização compartilhada]"
        elif message_type == "contacts":
            return "[Contato compartilhado]"
        else:
            return f"[Mensagem do tipo {message_type}]"
        
        return ""
    except Exception as e:
        logger.error(f"❌ Erro ao extrair conteúdo da mensagem: {e}")
        return "[Erro ao processar mensagem]"

# ================================
# ENDPOINTS DE MONITORAMENTO
# ================================

@router.get("/webhook/stats")
async def get_correction_stats():
    """Retorna estatísticas das correções"""
    try:
        stats = GLOBAL_RESPONSE_CONTROL['stats'].copy()
        
        # Calcular métricas
        total_messages = stats['messages_processed']
        
        if total_messages > 0:
            block_rate = (stats['messages_blocked'] / total_messages) * 100
            response_rate = (stats['responses_sent'] / total_messages) * 100
            
            # Verificar efetividade (idealmente 1 resposta por mensagem processada)
            expected_responses = total_messages - stats['messages_blocked']
            effectiveness = (stats['responses_sent'] / expected_responses * 100) if expected_responses > 0 else 0
        else:
            block_rate = 0
            response_rate = 0
            effectiveness = 0
        
        return {
            "status": "active",
            "stats": stats,
            "metrics": {
                "block_rate_percent": round(block_rate, 2),
                "response_rate_percent": round(response_rate, 2),
                "effectiveness_percent": round(effectiveness, 2)
            },
            "health": {
                "single_response_working": effectiveness >= 90,
                "duplicate_prevention_working": block_rate >= 5,
                "low_errors": stats['errors'] < 10
            },
            "cache_info": {
                "cached_messages": len(GLOBAL_RESPONSE_CONTROL['message_cache']),
                "active_users": len(GLOBAL_RESPONSE_CONTROL['active_responses']),
                "processing_locks": len(GLOBAL_RESPONSE_CONTROL['processing_locks'])
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@router.post("/webhook/cleanup")
async def manual_cleanup():
    """Executa limpeza manual dos caches"""
    try:
        await cleanup_response_control()
        return {
            "status": "cleanup_completed",
            "timestamp": datetime.now().isoformat(),
            "remaining": {
                "cached_messages": len(GLOBAL_RESPONSE_CONTROL['message_cache']),
                "active_users": len(GLOBAL_RESPONSE_CONTROL['active_responses']),
                "processing_locks": len(GLOBAL_RESPONSE_CONTROL['processing_locks'])
            }
        }
    except Exception as e:
        logger.error(f"❌ Erro na limpeza manual: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

@router.post("/webhook/reset-stats")
async def reset_stats():
    """Reseta estatísticas (apenas para desenvolvimento)"""
    try:
        GLOBAL_RESPONSE_CONTROL['stats'] = {
            'messages_processed': 0,
            'messages_blocked': 0,
            'responses_sent': 0,
            'duplicates_prevented': 0,
            'errors': 0
        }
        
        return {
            "status": "stats_reset",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao resetar estatísticas: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

logger.info("✅ Webhook corrigido carregado com controle de resposta única")
logger.info("🛑 Proteções ativas: Resposta única, Cache temporal, Locks por usuário")
logger.info("🎯 Sistema simplificado: Roteamento direto, Respostas pré-definidas")
