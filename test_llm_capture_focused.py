#!/usr/bin/env python3
"""
🧪 TESTE FOCADO - Captura de Respostas LLM
==========================================
Teste específico para verificar captura de respostas
"""

import asyncio
import aiohttp
import asyncpg
import json
import time
import random
import logging
import hmac
import hashlib
from datetime import datetime, timezone

# Configurações
RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"
WEBHOOK_URL = f"{RAILWAY_URL}/webhook"
DATABASE_URL = 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMCaptureTester:
    def __init__(self):
        self.session = None
        self.db_conn = None
        self.llm_responses = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        self.db_conn = await asyncpg.connect(DATABASE_URL)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.db_conn:
            await self.db_conn.close()

    async def send_test_message(self, message: str):
        """Envia uma mensagem de teste"""
        message_id = f"wamid.test_{int(time.time())}{random.randint(1000, 9999)}"
        timestamp = str(int(time.time()))
        
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "24386792860950513",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550987654",
                            "phone_number_id": "728348237027885"
                        },
                        "contacts": [{
                            "profile": {
                                "name": "João Testador Sistema"
                            },
                            "wa_id": TEST_PHONE
                        }],
                        "messages": [{
                            "from": TEST_PHONE,
                            "id": message_id,
                            "timestamp": timestamp,
                            "type": "text",
                            "text": {
                                "body": message
                            }
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        # Criar assinatura
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
        webhook_secret = "meutoken123"
        signature = hmac.new(webhook_secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        
        logger.info(f"📤 Enviando: {message}")
        
        try:
            start_time = time.time()
            async with self.session.post(
                WEBHOOK_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WhatsApp/2.0",
                    "X-Hub-Signature-256": f"sha256={signature}"
                }
            ) as response:
                response_time = time.time() - start_time
                logger.info(f"📨 Status: {response.status} | Tempo: {response_time*1000:.1f}ms")
                
                if response.status == 200:
                    # Aguardar processamento
                    logger.info("⏳ Aguardando processamento da LLM (5s)...")
                    await asyncio.sleep(5)
                    
                    # Capturar resposta
                    await self.capture_llm_response(message)
                    
                return response.status
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar '{message}': {e}")
            return 500

    async def capture_llm_response(self, sent_message: str):
        """Captura resposta da LLM"""
        try:
            # Buscar mensagens mais recentes
            messages = await self.db_conn.fetch("""
                SELECT m.id, m.direction, m.content, m.created_at
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE u.wa_id = $1 AND m.direction = 'out'
                ORDER BY m.created_at DESC
                LIMIT 3
            """, TEST_PHONE)
            
            logger.info(f"🔍 Verificando {len(messages)} mensagens de saída...")
            
            for msg in messages:
                now = datetime.now(timezone.utc)
                msg_time = msg['created_at']
                if msg_time.tzinfo is None:
                    msg_time = msg_time.replace(tzinfo=timezone.utc)
                
                time_diff = now - msg_time
                logger.info(f"   📥 {msg_time.strftime('%H:%M:%S')} ({time_diff.total_seconds():.1f}s ago): {msg['content'][:50]}...")
                
                if time_diff.total_seconds() <= 30:
                    # Verificar se já capturamos
                    already_captured = any(
                        resp.get('message_id') == msg['id'] 
                        for resp in self.llm_responses
                    )
                    
                    if not already_captured:
                        llm_response = {
                            "user_message": sent_message,
                            "llm_response": msg['content'],
                            "message_id": msg['id'],
                            "timestamp": msg['created_at'].isoformat(),
                            "processing_time": time_diff.total_seconds()
                        }
                        
                        self.llm_responses.append(llm_response)
                        logger.info(f"✅ LLM Response capturada: {msg['content'][:80]}...")
                        return
            
            logger.warning("⚠️ Nenhuma resposta LLM recente encontrada")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao capturar resposta LLM: {e}")

    async def run_focused_test(self):
        """Executa teste focado"""
        logger.info("🚀 TESTE FOCADO - Captura de Respostas LLM")
        logger.info("=" * 50)
        
        test_messages = [
            "Olá! Como vocês estão?",
            "Quais serviços vocês oferecem?",
            "Quero agendar uma limpeza de pele"
        ]
        
        for i, message in enumerate(test_messages, 1):
            logger.info(f"\n🧪 Teste {i}/{len(test_messages)}")
            status = await self.send_test_message(message)
            
            if i < len(test_messages):
                logger.info("⏳ Pausa entre testes...")
                await asyncio.sleep(3)
        
        logger.info(f"\n🎯 RESULTADOS:")
        logger.info(f"📊 Respostas LLM capturadas: {len(self.llm_responses)}")
        
        for i, response in enumerate(self.llm_responses, 1):
            logger.info(f"\n{i}. 👤 Usuário: {response['user_message']}")
            logger.info(f"   🤖 LLM: {response['llm_response'][:100]}...")
            logger.info(f"   ⏱️ Tempo: {response['processing_time']:.1f}s")

async def main():
    async with LLMCaptureTester() as tester:
        await tester.run_focused_test()

if __name__ == "__main__":
    asyncio.run(main())
