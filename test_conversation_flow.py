#!/usr/bin/env python3
"""
🧪 TESTE SIMPLES COM CONVERSAS VISÍVEIS
=====================================

Teste básico para garantir que as conversas apareçam nos relatórios
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import logging

# Importar da classe principal
import sys
sys.path.append('/home/vancim/whats_agent')
from test_whatsapp_with_llm_responses import WhatsAppConversationTester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_conversation_flow():
    """Teste com conversas que devem aparecer no relatório"""
    
    async with WhatsAppConversationTester() as tester:
        logger.info("🚀 Iniciando teste de conversas")
        
        # CENÁRIO 1: Saudação
        tester.start_new_conversation("Teste de Saudação")
        
        # Enviar mensagens e simular respostas
        msg1 = await tester.send_message_and_wait_response("Olá! Como está?", delay=1.0, wait_response=3.0)
        msg2 = await tester.send_message_and_wait_response("Estou bem, obrigado!", delay=1.0, wait_response=3.0)
        
        logger.info(f"📝 Conversa 1 tem {len(tester.current_conversation)} mensagens")
        
        # CENÁRIO 2: Serviços
        tester.start_new_conversation("Consulta de Serviços")
        
        msg3 = await tester.send_message_and_wait_response("Quais serviços vocês oferecem?", delay=1.0, wait_response=3.0)
        msg4 = await tester.send_message_and_wait_response("Quanto custa uma limpeza de pele?", delay=1.0, wait_response=3.0)
        
        logger.info(f"📝 Conversa 2 tem {len(tester.current_conversation)} mensagens")
        
        # Finalizar e salvar métricas
        await tester.collect_final_metrics()
        
        # Salvar última conversa manualmente se necessário
        if tester.current_conversation:
            conversation_data = {
                "scenario": "consulta_servicos",
                "scenario_name": "Consulta de Serviços",
                "messages": tester.current_conversation.copy(),
                "start_time": tester.current_conversation[0]["timestamp"] if tester.current_conversation else None,
                "end_time": tester.current_conversation[-1]["timestamp"] if tester.current_conversation else None,
                "message_count": len([m for m in tester.current_conversation if m["type"] == "sent"]),
                "response_count": len([m for m in tester.current_conversation if m["type"] == "received"])
            }
            tester.conversations.append(conversation_data)
            logger.info(f"💾 Última conversa salva manualmente")
        
        logger.info(f"📊 TOTAL DE CONVERSAS: {len(tester.conversations)}")
        logger.info(f"📱 TOTAL DE MENSAGENS: {len(tester.messages_sent)}")
        logger.info(f"🤖 TOTAL DE RESPOSTAS: {len(tester.responses_received)}")
        
        # Debug: Mostrar estrutura das conversas
        for i, conv in enumerate(tester.conversations):
            logger.info(f"🔍 Conversa {i+1}: {conv['scenario_name']} - {len(conv['messages'])} mensagens")
            for j, msg in enumerate(conv['messages']):
                logger.info(f"   Msg {j+1}: {msg['type']} - {msg['message'][:50]}...")
        
        # Gerar relatórios
        html_file = tester.generate_html_report_with_conversations()
        md_file = tester.generate_markdown_report_with_conversations()
        json_file = tester.generate_json_report_with_conversations()
        
        logger.info("\n🎉 TESTE CONCLUÍDO!")
        logger.info(f"📊 Relatório HTML: {html_file}")
        logger.info(f"📝 Relatório Markdown: {md_file}")
        logger.info(f"📄 Relatório JSON: {json_file}")

if __name__ == "__main__":
    asyncio.run(test_conversation_flow())
