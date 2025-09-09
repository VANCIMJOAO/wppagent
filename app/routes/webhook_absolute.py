"""
import logging
logger = logging.getLogger(__name__)

🚨 WEBHOOK CORRIGIDO - VERSÃO ABSOLUTA DEFINITIVA
===============================================

Esta versão integra o sistema de controle absoluto no webhook existente,
garantindo APENAS UMA RESPOSTA por mensagem.

CORREÇÕES IMPLEMENTADAS:
1. ✅ Cache persistente em arquivo (/tmp/webhook_absolute_cache.json)
2. ✅ Verificação tripla antes de qualquer resposta
3. ✅ Bloqueio por 30 segundos entre respostas do mesmo usuário
4. ✅ Cache de 5 minutos para mensagens duplicadas
5. ✅ Detecção de conteúdo similar (80% de similaridade)
6. ✅ Log detalhado de todos os bloqueios
7. ✅ Estatísticas em tempo real
"""

import asyncio
import time
import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.whatsapp import whatsapp_service
from app.services.data import UserService, ConversationService, MessageService
from app.utils.whatsapp_sanitizer import sanitize_whatsapp_data, sanitize_message, sanitize_phone
from app.models.database import MetaLog
from app.config import settings

# CACHE ABSOLUTO EM ARQUIVO
CACHE_FILE = "/tmp/webhook_absolute_cache.json"
ACTIVE_RESPONSES_FILE = "/tmp/webhook_active_responses.json"

class AbsoluteResponseControl:
    def __init__(self):
        self.cache = {}
        self.active_responses = {}
        self.processing_locks = {}  # asyncio locks para usuários
        self.stats = {
            'messages_processed': 0,
            'messages_blocked': 0,
            'responses_sent': 0,
            'duplicates_prevented': 0,
            'cache_saves': 0,
            'cache_loads': 0,
            'errors': 0
        }
        self.load_cache()
        logger.info("🚨 Sistema de controle absoluto inicializado")
    
    def load_cache(self):
        """Carrega cache de arquivo"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    self.cache = json.load(f)
                self.stats['cache_loads'] += 1
                logger.info(f"📂 Cache carregado: {len(self.cache)} entradas")
            
            if os.path.exists(ACTIVE_RESPONSES_FILE):
                with open(ACTIVE_RESPONSES_FILE, 'r') as f:
                    self.active_responses = json.load(f)
                logger.info(f"📂 Respostas ativas: {len(self.active_responses)} usuários")
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar cache: {e}")
            self.cache = {}
            self.active_responses = {}
    
    def save_cache(self):
        """Salva cache em arquivo"""
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f)
            with open(ACTIVE_RESPONSES_FILE, 'w') as f:
                json.dump(self.active_responses, f)
            self.stats['cache_saves'] += 1
            logger.debug("💾 Cache persistente salvo")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar cache: {e}")
    
    def get_message_key(self, user_id: str, content: str) -> str:
        """Gera chave única para mensagem"""
        content_clean = content.strip().lower()[:100]
        content_hash = hashlib.md5(content_clean.encode()).hexdigest()[:10]
        # Janela de 5 minutos
        time_window = int(time.time() / 300)
        return f"{user_id}_{content_hash}_{time_window}"
    
    def cleanup_old_entries(self):
        """Remove entradas antigas"""
        current_time = time.time()
        old_cache = [k for k, v in self.cache.items() 
                    if current_time - v.get('timestamp', 0) > 3600]  # 1 hora
        old_responses = [k for k, v in self.active_responses.items() 
                        if current_time - v > 600]  # 10 minutos
        
        for k in old_cache:
            del self.cache[k]
        for k in old_responses:
            del self.active_responses[k]
        
        if old_cache or old_responses:
            logger.info(f"🧹 Limpeza: {len(old_cache)} cache + {len(old_responses)} respostas")
            self.save_cache()
    
    async def can_process_message(self, user_id: str, content: str) -> Tuple[bool, str]:
        """
        VERIFICAÇÃO ABSOLUTA - CONTROLE TOTAL
        Returns: (pode_processar, motivo)
        """
        # Criar lock para usuário se não existir
        if user_id not in self.processing_locks:
            self.processing_locks[user_id] = asyncio.Lock()
        
        # LOCK CRÍTICO - apenas uma verificação por usuário por vez
        async with self.processing_locks[user_id]:
            current_time = time.time()
            message_key = self.get_message_key(user_id, content)
            
            logger.debug(f"🔍 Verificação: {user_id} - {content[:30]}... - {message_key}")
            
            # BLOQUEIO 1: Mensagem duplicada?
            if message_key in self.cache:
                cache_entry = self.cache[message_key]
                time_diff = current_time - cache_entry['timestamp']
                if time_diff < 300:  # 5 minutos
                    self.stats['messages_blocked'] += 1
                    self.stats['duplicates_prevented'] += 1
                    logger.warning(f"🚫 DUPLICATA: {user_id} - {time_diff:.1f}s")
                    return False, f"Mensagem duplicada há {time_diff:.1f}s"
            
            # BLOQUEIO 2: Resposta muito recente?
            if user_id in self.active_responses:
                last_response = self.active_responses[user_id]
                time_diff = current_time - last_response
                if time_diff < 30:  # 30 segundos
                    self.stats['messages_blocked'] += 1
                    logger.warning(f"🚫 RESPOSTA RECENTE: {user_id} - {time_diff:.1f}s")
                    return False, f"Resposta há apenas {time_diff:.1f}s"
            
            # BLOQUEIO 3: Conteúdo similar?
            content_lower = content.lower().strip()
            for cached_key, cached_data in self.cache.items():
                if (cached_data.get('user_id') == user_id and 
                    cached_data.get('content')):
                    
                    similarity = self._calculate_similarity(
                        content_lower, 
                        cached_data.get('content', '').lower()
                    )
                    
                    if similarity > 0.8:
                        time_diff = current_time - cached_data['timestamp']
                        if time_diff < 120:  # 2 minutos
                            self.stats['messages_blocked'] += 1
                            logger.warning(f"🚫 SIMILAR: {user_id} - {similarity:.2f}")
                            return False, f"Conteúdo similar (80%+) há {time_diff:.1f}s"
            
            logger.info(f"✅ LIBERADO: {user_id}")
            return True, "Aprovado"
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre textos"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def mark_processing(self, user_id: str, content: str) -> str:
        """Marca como processando"""
        current_time = time.time()
        message_key = self.get_message_key(user_id, content)
        
        self.cache[message_key] = {
            'timestamp': current_time,
            'user_id': user_id,
            'content': content[:100],
            'status': 'processing'
        }
        
        self.stats['messages_processed'] += 1
        logger.info(f"🔒 PROCESSANDO: {message_key}")
        self.save_cache()
        
        return message_key
    
    def mark_response_sent(self, user_id: str, content: str, response: str):
        """Marca resposta enviada"""
        current_time = time.time()
        message_key = self.get_message_key(user_id, content)
        
        if message_key in self.cache:
            self.cache[message_key].update({
                'status': 'responded',
                'response': response[:200],
                'sent_at': current_time
            })
        
        self.active_responses[user_id] = current_time
        self.stats['responses_sent'] += 1
        
        logger.info(f"📤 ENVIADA: {user_id}")
        self.save_cache()
    
    def get_stats(self) -> dict:
        """Estatísticas completas"""
        self.cleanup_old_entries()
        
        total_messages = self.stats['messages_processed']
        if total_messages > 0:
            block_rate = (self.stats['messages_blocked'] / total_messages) * 100
            effectiveness = (self.stats['responses_sent'] / total_messages) * 100
        else:
            block_rate = 0
            effectiveness = 0
        
        return {
            'status': 'active',
            'stats': self.stats.copy(),
            'metrics': {
                'block_rate_percent': round(block_rate, 2),
                'effectiveness_percent': round(effectiveness, 2),
                'single_response_ratio': round(
                    self.stats['responses_sent'] / max(self.stats['messages_processed'], 1), 2
                )
            },
            'health': {
                'single_response_working': effectiveness >= 95,
                'duplicate_prevention_working': block_rate >= 10,
                'cache_working': self.stats['cache_saves'] > 0,
                'low_errors': self.stats['errors'] < 5
            },
            'cache_info': {
                'cached_messages': len(self.cache),
                'active_users': len(self.active_responses),
                'processing_locks': len(self.processing_locks)
            },
            'timestamp': datetime.now().isoformat()
        }

# INSTÂNCIA GLOBAL
ABSOLUTE_CONTROL = AbsoluteResponseControl()

# Sistema de resposta simplificado (mantido do original)
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
        message_lower = message.lower().strip()
        
        if any(word in message_lower for word in ['oi', 'olá', 'bom dia', 'tudo bem']):
            return self.responses['greeting']
        elif any(word in message_lower for word in ['serviço', 'tratamento', 'oferece']):
            return self.responses['services']
        else:
            return self.responses['default']

# Gerador de respostas
response_generator = SimplifiedResponseGenerator()

# Router
router = APIRouter()

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Verificação do webhook"""
    logger.info(f"🔍 Verificação webhook: mode={hub_mode}")
    
    if hub_mode == "subscribe":
        challenge = whatsapp_service.verify_webhook(hub_verify_token, hub_challenge)
        if challenge:
            logger.info("✅ Webhook verificado!")
            return int(challenge)
    
    logger.error("❌ Falha na verificação")
    raise HTTPException(status_code=403, detail="Verificação falhada")

@router.post("/webhook")
async def receive_webhook_absolute(request: Request, db: AsyncSession = Depends(get_db)):
    """
    🚨 WEBHOOK COM CONTROLE ABSOLUTO DE RESPOSTA ÚNICA
    """
    try:
        # Parse payload
        payload_raw = await request.body()
        payload_dict = json.loads(payload_raw)
        
        # Sanitizar
        sanitized_payload = sanitize_whatsapp_data(payload_dict)
        logger.debug("✅ Payload sanitizado")
        
        # Log
        await log_request_safe(db, sanitized_payload, dict(request.headers))
        
        # Processar entradas
        if "entry" in sanitized_payload:
            for entry in sanitized_payload["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            await process_message_absolute(db, change["value"])
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        ABSOLUTE_CONTROL.stats['errors'] += 1
        raise HTTPException(status_code=500, detail="Erro interno")

async def log_request_safe(db: AsyncSession, payload: dict, headers: dict):
    """Log seguro"""
    try:
        safe_headers = {k[:100]: str(v)[:500] for k, v in headers.items() 
                      if isinstance(k, str) and isinstance(v, str)}
        
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
        
    except Exception as e:
        logger.error(f"❌ Erro no log: {e}")

async def process_message_absolute(db: AsyncSession, value: dict):
    """🎯 Processamento com controle absoluto"""
    try:
        if "messages" not in value:
            return
        
        # Processar contatos
        contacts = value.get("contacts", [])
        contact_info = {}
        if contacts and "profile" in contacts[0]:
            contact_info["name"] = contacts[0]["profile"].get("name")
        
        for message in value["messages"]:
            wa_id = message.get("from")
            content = extract_message_content_safe(message)
            message_id = message.get("id")
            
            if not wa_id or not content:
                continue
            
            # Sanitizar
            try:
                clean_wa_id = sanitize_phone(wa_id)
                clean_content = sanitize_message(content, "text")
            except ValueError as e:
                logger.error(f"❌ Dados inválidos: {e}")
                continue
            
            # 🚨 CONTROLE ABSOLUTO - VERIFICAÇÃO CRÍTICA
            can_process, reason = await ABSOLUTE_CONTROL.can_process_message(
                clean_wa_id, clean_content
            )
            
            if not can_process:
                logger.warning(f"🚫 BLOQUEADO: {clean_wa_id} - {reason}")
                continue
            
            logger.info(f"📨 PROCESSANDO: {clean_wa_id} - {clean_content[:30]}...")
            
            # Marcar como processando
            message_key = ABSOLUTE_CONTROL.mark_processing(clean_wa_id, clean_content)
            
            # Criar usuário e conversa
            try:
                user = await UserService.get_or_create_user(
                    db=db, wa_id=clean_wa_id, nome=contact_info.get("name"), 
                    telefone=clean_wa_id
                )
                
                conversation = await ConversationService.get_or_create_conversation(
                    db=db, user_id=user.id
                )
                
                # Verificar modo humano
                if conversation.status == "human":
                    logger.info(f"Conversa {conversation.id} em modo humano")
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
                
                # 🎯 GERAR RESPOSTA ÚNICA
                response = response_generator.generate_single_response(clean_content)
                safe_response = sanitize_message(response, "text")
                
                # 🚨 ENVIAR ÚNICA RESPOSTA
                send_result = await whatsapp_service.send_text_message(
                    clean_wa_id, safe_response
                )
                
                if send_result and "error" not in send_result:
                    # Salvar resposta
                    await MessageService.create_message(
                        db=db, user_id=user.id, conversation_id=conversation.id,
                        direction="out", content=safe_response, message_type="text",
                        metadata={
                            "system": "absolute_single_response",
                            "message_key": message_key,
                            "whatsapp_response": send_result
                        }
                    )
                    
                    # MARCAR COMO ENVIADA
                    ABSOLUTE_CONTROL.mark_response_sent(
                        clean_wa_id, clean_content, safe_response
                    )
                    
                    logger.info(f"✅ RESPOSTA ÚNICA ENVIADA: {clean_wa_id}")
                else:
                    logger.error(f"❌ Falha no envio: {send_result}")
                    ABSOLUTE_CONTROL.stats['errors'] += 1
                
            except Exception as e:
                logger.error(f"❌ Erro no processamento: {e}")
                ABSOLUTE_CONTROL.stats['errors'] += 1
                
    except Exception as e:
        logger.error(f"❌ Erro na mensagem: {e}")
        ABSOLUTE_CONTROL.stats['errors'] += 1

def extract_message_content_safe(message: dict) -> str:
    """Extrai conteúdo da mensagem"""
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
        else:
            return f"[Mensagem {message_type}]"
            
    except Exception as e:
        logger.error(f"❌ Erro ao extrair conteúdo: {e}")
        return "[Erro ao processar]"

# Endpoints de monitoramento
@router.get("/webhook/stats")
async def get_absolute_stats():
    """Estatísticas do controle absoluto"""
    return ABSOLUTE_CONTROL.get_stats()

@router.get("/webhook/status")
async def webhook_status():
    """Status do webhook absoluto"""
    stats = ABSOLUTE_CONTROL.get_stats()
    return {
        "status": "active",
        "corrections_active": True,
        "single_response_system": True,
        "absolute_control": True,
        "cache_persistent": True,
        **stats
    }

@router.get("/webhook/control")
async def webhook_control():
    """Controle de resposta"""
    stats = ABSOLUTE_CONTROL.get_stats()
    
    return {
        "status": "active",
        "response_control": True,
        "single_response_working": stats['health']['single_response_working'],
        "anti_duplication_active": True,
        "cache_working": stats['health']['cache_working'],
        "metrics": stats['metrics'],
        "cache_files": {
            "cache_exists": os.path.exists(CACHE_FILE),
            "responses_exists": os.path.exists(ACTIVE_RESPONSES_FILE)
        }
    }