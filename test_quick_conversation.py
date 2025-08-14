#!/usr/bin/env python3
"""
🧪 TESTE RÁPIDO COM CONVERSAS - WhatsApp Agent
============================================

Testa apenas o primeiro cenário para verificar se a captura de conversas está funcionando.
"""

import asyncio
import logging
from test_whatsapp_production_complete import WhatsAppProductionTester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_quick_conversation():
    """Teste rápido com captura de conversas"""
    
    async with WhatsAppProductionTester() as tester:
        logger.info("🚀 Iniciando teste rápido com conversas")
        
        # Executar apenas o cenário 1
        await tester.test_scenario_basic_greeting()
        
        # Estatísticas
        logger.info(f"\n📊 RESULTADO:")
        logger.info(f"💬 Conversas: {len(tester.conversations)}")
        logger.info(f"📱 Mensagens: {len(tester.messages_sent)}")
        logger.info(f"🤖 Respostas: {len(tester.responses_received)}")
        
        # Debug das conversas
        for i, conv in enumerate(tester.conversations):
            logger.info(f"🔍 Conversa {i+1}: {conv['scenario_name']} - {len(conv['messages'])} mensagens")
            for j, msg in enumerate(conv['messages']):
                logger.info(f"   Msg {j+1}: {msg['type']} - {msg['message'][:50]}...")

if __name__ == "__main__":
    asyncio.run(test_quick_conversation())
