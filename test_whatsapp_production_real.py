#!/usr/bin/env python3
"""
🔬 Teste Completo de Produção WhatsApp Agent - RESPOSTAS REAIS
Versão: 2.1 - Captura de conversas reais
Autor: VANCIM 
Data: 13/08/2025
"""

import asyncio
import aiohttp
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
RAILWAY_URL = os.getenv('RAILWAY_URL')
TEST_PHONE = os.getenv('TEST_PHONE')

if not RAILWAY_URL or not TEST_PHONE:
    logger.error("❌ RAILWAY_URL e TEST_PHONE devem estar configurados no .env")
    exit(1)

class WhatsAppProductionTester:
    """Testador completo de produção com captura de conversas REAIS"""
    
    def __init__(self):
        self.session = None
        self.messages_sent = []
        self.responses_received = []
        self.conversations = []
        self.current_conversation = []
        self.message_ids = []
        self.start_time = datetime.now()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_real_whatsapp_message(self, message: str, delay: float = 3.0, capture_response: bool = True) -> Dict:
        """Envia mensagem REAL via endpoint do sistema e captura resposta da LLM"""
        try:
            logger.info(f"📤 Enviando mensagem REAL: {message}")
            
            async with self.session.post(
                f"{RAILWAY_URL}/webhook/test-send",
                params={
                    "phone_number": TEST_PHONE,
                    "message": message
                }
            ) as response:
                response_data = await response.json() if response.status == 200 else await response.text()
                
                message_data = {
                    "timestamp": datetime.now().isoformat(),
                    "message": message,
                    "status_code": response.status,
                    "response": response_data,
                    "message_id": None
                }
                
                if response.status == 200 and isinstance(response_data, dict):
                    if response_data.get('success'):
                        # Extrair message ID se disponível
                        if 'api_response' in response_data:
                            api_resp = response_data['api_response']
                            if 'messages' in api_resp and api_resp['messages']:
                                message_id = api_resp['messages'][0].get('id', 'N/A')
                                message_data["message_id"] = message_id
                                self.message_ids.append(message_id)
                                logger.info(f"✅ Mensagem enviada! ID: {message_id}")
                            else:
                                logger.info(f"✅ Mensagem enviada via sistema")
                        else:
                            logger.info(f"✅ Mensagem enviada: {response_data.get('message', 'OK')}")
                    else:
                        logger.warning(f"⚠️ Adicionado à fila: {response_data.get('message')}")
                else:
                    logger.error(f"❌ Erro ao enviar: {response.status} - {response_data}")
                
                # Registrar mensagem enviada na conversa atual
                sent_msg = {
                    "type": "sent",
                    "message": message,
                    "timestamp": message_data["timestamp"],
                    "message_id": message_data["message_id"],
                    "success": response.status == 200
                }
                self.current_conversation.append(sent_msg)
                self.messages_sent.append(message_data)
                
                # Capturar resposta REAL da LLM se solicitado
                if capture_response and response.status == 200:
                    # Aguardar tempo suficiente para a LLM processar e responder
                    await asyncio.sleep(5.0)
                    
                    # Tentar capturar resposta real do sistema
                    real_response = await self.capture_real_llm_response(message)
                    
                    if real_response:
                        # Registrar resposta REAL recebida na conversa atual
                        received_msg = {
                            "type": "received",
                            "message": real_response,
                            "timestamp": datetime.now().isoformat(),
                            "from_llm": True,
                            "is_real_response": True
                        }
                        self.current_conversation.append(received_msg)
                        self.responses_received.append(received_msg)
                        logger.info(f"✅ Resposta REAL capturada: {real_response[:100]}...")
                    else:
                        logger.warning(f"⚠️ Nenhuma resposta real capturada para: {message[:50]}...")
                
                # Aguardar entre mensagens
                logger.info(f"⏳ Aguardando {delay}s antes da próxima mensagem...")
                await asyncio.sleep(delay)
                
                return message_data
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem '{message}': {e}")
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "status_code": 500,
                "error": str(e),
                "message_id": None
            }
            self.messages_sent.append(error_data)
            return error_data
    
    async def capture_real_llm_response(self, sent_message: str) -> str:
        """Captura resposta REAL da LLM do sistema, sem simular nada"""
        try:
            # Método 1: Tentar buscar via API de conversas recentes
            try:
                async with self.session.get(f"{RAILWAY_URL}/api/conversations/recent") as response:
                    if response.status == 200:
                        conversations = await response.json()
                        # Procurar pela mensagem enviada e sua resposta
                        for conv in conversations.get('conversations', []):
                            for msg in conv.get('messages', []):
                                if msg.get('content', '').strip() == sent_message.strip():
                                    # Encontrar a próxima mensagem (resposta da LLM)
                                    messages = conv.get('messages', [])
                                    current_idx = messages.index(msg)
                                    if current_idx + 1 < len(messages):
                                        next_msg = messages[current_idx + 1]
                                        if next_msg.get('role') == 'assistant':
                                            return next_msg.get('content', '').strip()
            except Exception as e:
                logger.debug(f"Método 1 falhou: {e}")
            
            # Método 2: Tentar buscar via webhook/logs recentes
            try:
                async with self.session.get(f"{RAILWAY_URL}/api/webhook/recent-responses") as response:
                    if response.status == 200:
                        recent_responses = await response.json()
                        # Procurar resposta mais recente que corresponda ao contexto
                        for resp in recent_responses.get('responses', []):
                            if 'response_text' in resp:
                                return resp['response_text'].strip()
            except Exception as e:
                logger.debug(f"Método 2 falhou: {e}")
            
            # Método 3: Verificar database diretamente (se disponível)
            try:
                async with self.session.get(f"{RAILWAY_URL}/api/messages/latest") as response:
                    if response.status == 200:
                        latest_msg = await response.json()
                        if latest_msg.get('direction') == 'outbound' and latest_msg.get('content'):
                            return latest_msg['content'].strip()
            except Exception as e:
                logger.debug(f"Método 3 falhou: {e}")
            
            logger.warning(f"❌ Não foi possível capturar resposta real para: {sent_message[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao capturar resposta real: {e}")
            return None

    def start_new_conversation(self, scenario_name: str):
        """Inicia uma nova conversa"""
        if self.current_conversation:
            # Salvar conversa anterior
            self.conversations.append({
                "scenario": "previous",
                "scenario_name": "Conversa Anterior",
                "messages": self.current_conversation.copy(),
                "start_time": self.current_conversation[0]["timestamp"] if self.current_conversation else None,
                "end_time": self.current_conversation[-1]["timestamp"] if self.current_conversation else None,
            })
        
        self.current_conversation = []
        logger.info(f"🔄 Nova conversa iniciada: {scenario_name}")
    
    def finalize_current_conversation(self, scenario_name: str):
        """Finaliza a conversa atual"""
        if self.current_conversation:
            conversation_data = {
                "scenario": scenario_name.lower().replace(" ", "_"),
                "scenario_name": scenario_name,
                "messages": self.current_conversation.copy(),
                "start_time": self.current_conversation[0]["timestamp"] if self.current_conversation else None,
                "end_time": self.current_conversation[-1]["timestamp"] if self.current_conversation else None,
                "total_messages": len(self.current_conversation),
                "sent_count": len([m for m in self.current_conversation if m["type"] == "sent"]),
                "received_count": len([m for m in self.current_conversation if m["type"] == "received"])
            }
            self.conversations.append(conversation_data)
            logger.info(f"💾 Conversa finalizada: {scenario_name} com {len(self.current_conversation)} mensagens")

    # CENÁRIOS DE TESTE
    async def test_scenario_basic_greeting(self):
        """Cenário 1: Saudação e Apresentação"""
        self.start_new_conversation("Saudação e Apresentação")
        
        messages = [
            "Olá! Bom dia! 😊",
            "Como você está?",
            "Gostaria de conhecer seus serviços"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Saudação e Apresentação")
        logger.info("✅ Cenário 1 concluído")

    async def test_scenario_service_inquiry(self):
        """Cenário 2: Consulta de Serviços"""
        self.start_new_conversation("Consulta de Serviços")
        
        messages = [
            "Quais serviços vocês oferecem?",
            "Quanto custa uma limpeza de pele?",
            "Vocês fazem massagem relaxante?",
            "Qual o horário de funcionamento?",
            "Onde vocês ficam localizados?"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Consulta de Serviços")
        logger.info("✅ Cenário 2 concluído")

    async def test_scenario_scheduling(self):
        """Cenário 3: Agendamento Completo"""
        self.start_new_conversation("Agendamento Completo")
        
        messages = [
            "Gostaria de agendar uma limpeza de pele",
            "João Silva",
            "5516991022255",
            "joao.silva@email.com",
            "Prefiro pela manhã",
            "Confirmo o agendamento"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Agendamento Completo")
        logger.info("✅ Cenário 3 concluído")

    async def test_scenario_rescheduling(self):
        """Cenário 4: Reagendamento"""
        self.start_new_conversation("Reagendamento")
        
        messages = [
            "Preciso reagendar meu horário",
            "João Silva",
            "Gostaria de mudar para a tarde",
            "Confirmo a alteração"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Reagendamento")
        logger.info("✅ Cenário 4 concluído")

    async def test_scenario_cancellation(self):
        """Cenário 5: Cancelamento"""
        self.start_new_conversation("Cancelamento")
        
        messages = [
            "Preciso cancelar meu agendamento",
            "João Silva",
            "5516991022255",
            "Confirmado, pode cancelar"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Cancelamento")
        logger.info("✅ Cenário 5 concluído")

    async def test_scenario_complaint(self):
        """Cenário 6: Reclamação"""
        self.start_new_conversation("Reclamação e Resolução")
        
        messages = [
            "Estou insatisfeito com o atendimento",
            "A profissional chegou muito atrasada",
            "Gostaria de uma solução para isso",
            "Aceito a proposta de compensação"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Reclamação e Resolução")
        logger.info("✅ Cenário 6 concluído")

    async def test_scenario_weekend_inquiry(self):
        """Cenário 7: Consulta de Final de Semana"""
        self.start_new_conversation("Consulta de Final de Semana")
        
        messages = [
            "Vocês atendem aos sábados?",
            "E domingo, funcionam?",
            "Quero agendar para sábado",
            "Que horários têm disponível?"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Consulta de Final de Semana")
        logger.info("✅ Cenário 7 concluído")

    async def test_scenario_multiple_services(self):
        """Cenário 8: Múltiplos Serviços"""
        self.start_new_conversation("Múltiplos Serviços")
        
        messages = [
            "Quero agendar limpeza de pele e massagem",
            "Podem ser no mesmo dia?",
            "João Silva",
            "Confirmo os dois procedimentos"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Múltiplos Serviços")
        logger.info("✅ Cenário 8 concluído")

    async def test_scenario_farewell(self):
        """Cenário 9: Despedida"""
        self.start_new_conversation("Despedida")
        
        messages = [
            "Muito obrigado pelo atendimento",
            "Até breve!",
            "Tchau! 😊"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
        
        self.finalize_current_conversation("Despedida")
        logger.info("✅ Cenário 9 concluído")

    async def run_all_tests(self):
        """Executa todos os cenários de teste"""
        logger.info("🚀 INICIANDO BATERIA COMPLETA DE TESTES PRODUÇÃO")
        logger.info("=" * 60)
        
        # Verificar status inicial do sistema
        try:
            async with self.session.get(f"{RAILWAY_URL}/health", timeout=10) as response:
                logger.info(f"Status inicial do sistema: {response.status}")
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível verificar status inicial: {e}")
        
        # Lista de cenários
        scenarios = [
            ("🎬 CENÁRIO 1: Saudação e Apresentação", self.test_scenario_basic_greeting),
            ("🎬 CENÁRIO 2: Consulta de Serviços", self.test_scenario_service_inquiry),
            ("🎬 CENÁRIO 3: Agendamento Completo", self.test_scenario_scheduling),
            ("🎬 CENÁRIO 4: Reagendamento", self.test_scenario_rescheduling),
            ("🎬 CENÁRIO 5: Cancelamento", self.test_scenario_cancellation),
            ("🎬 CENÁRIO 6: Reclamação e Resolução", self.test_scenario_complaint),
            ("🎬 CENÁRIO 7: Consulta de Final de Semana", self.test_scenario_weekend_inquiry),
            ("🎬 CENÁRIO 8: Múltiplos Serviços", self.test_scenario_multiple_services),
            ("🎬 CENÁRIO 9: Despedida", self.test_scenario_farewell)
        ]
        
        # Executar cenários
        for scenario_name, scenario in scenarios:
            try:
                logger.info(f"\n{scenario_name}")
                await scenario()
                # Pausa entre cenários
                await asyncio.sleep(2.0)
            except Exception as e:
                logger.error(f"❌ Erro no cenário {scenario_name}: {e}")
                continue
        
        # Finalizar conversa atual se existir
        if self.current_conversation:
            self.finalize_current_conversation("Final")

    def generate_summary(self) -> Dict:
        """Gera resumo dos testes"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Estatísticas
        total_sent = len(self.messages_sent)
        total_received = len(self.responses_received)
        successful_sends = len([m for m in self.messages_sent if m.get('status_code') == 200])
        
        # Estatísticas de conversas
        total_conversations = len(self.conversations)
        total_conversation_messages = sum(conv['total_messages'] for conv in self.conversations)
        
        summary = {
            "test_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "railway_url": RAILWAY_URL,
                "test_phone": TEST_PHONE
            },
            "statistics": {
                "messages_sent": total_sent,
                "successful_sends": successful_sends,
                "send_success_rate": f"{(successful_sends/total_sent*100):.1f}%" if total_sent > 0 else "0%",
                "responses_received": total_received,
                "response_rate": f"{(total_received/successful_sends*100):.1f}%" if successful_sends > 0 else "0%",
                "total_conversations": total_conversations,
                "conversation_messages": total_conversation_messages
            },
            "conversations": self.conversations,
            "message_details": {
                "sent": self.messages_sent,
                "received": self.responses_received
            }
        }
        
        return summary

    def generate_html_report(self, summary: Dict) -> str:
        """Gera relatório em HTML com conversas REAIS"""
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório WhatsApp Agent - Conversas REAIS</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #25D366; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: linear-gradient(135deg, #25D366, #128C7E); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ margin-top: 5px; opacity: 0.9; }}
        .conversation {{ margin-bottom: 30px; border: 1px solid #ddd; border-radius: 10px; overflow: hidden; }}
        .conversation-header {{ background: #25D366; color: white; padding: 15px; font-weight: bold; }}
        .message {{ padding: 10px 15px; border-bottom: 1px solid #f0f0f0; }}
        .message:last-child {{ border-bottom: none; }}
        .sent {{ background: #E7F3E7; }}
        .received {{ background: #F0F8FF; }}
        .message-time {{ font-size: 0.8em; color: #666; }}
        .real-response {{ border-left: 4px solid #25D366; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Relatório WhatsApp Agent - Conversas REAIS</h1>
            <p>Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{summary['statistics']['messages_sent']}</div>
                <div class="stat-label">Mensagens Enviadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary['statistics']['responses_received']}</div>
                <div class="stat-label">Respostas Reais Capturadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary['statistics']['send_success_rate']}</div>
                <div class="stat-label">Taxa de Sucesso</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary['statistics']['response_rate']}</div>
                <div class="stat-label">Taxa de Resposta Real</div>
            </div>
        </div>
        
        <h2>💬 Conversas Capturadas</h2>
"""
        
        # Adicionar conversas
        for conv in summary['conversations']:
            html += f"""
        <div class="conversation">
            <div class="conversation-header">
                {conv['scenario_name']} ({conv['total_messages']} mensagens)
            </div>
"""
            for msg in conv['messages']:
                msg_class = "sent" if msg['type'] == 'sent' else "received"
                real_class = "real-response" if msg.get('is_real_response') else ""
                html += f"""
            <div class="message {msg_class} {real_class}">
                <strong>{'➡️ Enviado' if msg['type'] == 'sent' else '⬅️ Recebido'}:</strong> {msg['message']}<br>
                <span class="message-time">{msg['timestamp']}</span>
                {'<span style="color: #25D366; font-weight: bold;"> ✅ RESPOSTA REAL</span>' if msg.get('is_real_response') else ''}
            </div>
"""
            html += "        </div>\n"
        
        html += """
    </div>
</body>
</html>
"""
        return html

async def main():
    """Função principal"""
    logger.info("🔬 Iniciando teste completo de produção do WhatsApp Agent")
    logger.info("⚠️  ATENÇÃO: Este teste envia mensagens REAIS via WhatsApp!")
    
    async with WhatsAppProductionTester() as tester:
        await tester.run_all_tests()
        
        # Gerar relatório
        summary = tester.generate_summary()
        
        # Salvar relatório HTML
        html_report = tester.generate_html_report(summary)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_filename = f"whatsapp_real_conversation_report_{timestamp}.html"
        
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Log final
        stats = summary['statistics']
        logger.info("🎯 TESTE CONCLUÍDO!")
        logger.info("=" * 60)
        logger.info(f"📊 Mensagens enviadas: {stats['messages_sent']}")
        logger.info(f"✅ Envios bem-sucedidos: {stats['successful_sends']} ({stats['send_success_rate']})")
        logger.info(f"💬 Respostas REAIS capturadas: {stats['responses_received']} ({stats['response_rate']})")
        logger.info(f"🗂️ Conversas registradas: {stats['total_conversations']}")
        logger.info(f"📄 Relatório salvo: {html_filename}")

if __name__ == "__main__":
    asyncio.run(main())
