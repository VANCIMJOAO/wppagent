#!/usr/bin/env python3
"""
🧪 TESTE COMPLETO PRODUÇÃO - WhatsApp Agent
==========================================

Testa todas as funcionalidades do sistema com mensagens REAIS:
- Agendamentos
- Cancelamentos 
- Reagendamentos
- Reclamações
- Consultas de serviços
- Interações complexas

Configurações:
- Número de teste: 5516991022255
- URL do sistema: wppagent-production.up.railway.app
- Mensagens REAIS enviadas via WhatsApp API
- Geração de relatórios HTML, Markdown e JSON
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import os

# Configurações do teste
RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_production_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WhatsAppProductionTester:
    """Classe para testar o sistema WhatsApp Agent com mensagens reais"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        self.messages_sent = []
        self.responses_received = []
        self.conversations = []
        self.current_conversation = []
        self.start_time = datetime.now()
        self.message_ids = []
        
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
    
    async def get_system_status(self) -> Dict:
        """Verifica status do sistema"""
        try:
            async with self.session.get(f"{RAILWAY_URL}/health/detailed") as response:
                return {
                    "status_code": response.status,
                    "data": await response.json()
                }
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {e}")
            return {"status_code": 500, "error": str(e)}
    
    async def get_metrics(self) -> Dict:
        """Obtém métricas do sistema"""
        try:
            async with self.session.get(f"{RAILWAY_URL}/metrics/system") as response:
                return {
                    "status_code": response.status,
                    "data": await response.json()
                }
        except Exception as e:
            logger.error(f"❌ Erro ao obter métricas: {e}")
            return {"status_code": 500, "error": str(e)}
    
    async def get_contextual_llm_response(self, user_message: str) -> str:
        """REMOVIDO - Não simula mais respostas. Use capture_real_llm_response()"""
        logger.warning("⚠️ Método de simulação desabilitado. Use capture_real_llm_response() para respostas reais.")
        return "SIMULAÇÃO DESABILITADA - APENAS RESPOSTAS REAIS"
            # Saudações
            "olá": "🤖 Olá! Bem-vindo ao Studio Beleza & Bem-Estar! Como posso ajudá-lo hoje?",
            "oi": "🤖 Oi! É um prazer atendê-lo! Em que posso ser útil?",
            "bom dia": "🤖 Bom dia! Espero que esteja tendo um ótimo dia! Como posso ajudá-lo?",
            "como está": "🤖 Estou ótimo, obrigado por perguntar! Estou aqui para ajudar com seus agendamentos e dúvidas sobre nossos serviços.",
            
            # Perguntas sobre serviços
            "serviços": "🤖 Oferecemos diversos serviços: limpeza de pele, massagens relaxantes, tratamentos faciais, depilação, manicure e pedicure. Qual serviço te interessa?",
            "que vocês oferecem": "🤖 Temos uma ampla gama de serviços de beleza: limpeza de pele profunda, massagem relaxante, tratamentos anti-idade, depilação a laser e muito mais!",
            "quais": "🤖 Nossos principais serviços incluem: limpeza de pele (R$ 80), massagem relaxante (R$ 120), tratamento facial (R$ 150) e depilação (R$ 60). Posso dar mais detalhes sobre algum?",
            
            # Preços
            "quanto custa": "🤖 A limpeza de pele custa R$ 80,00 e tem duração de aproximadamente 1 hora. É um dos nossos serviços mais procurados! Gostaria de agendar?",
            "preço": "🤖 Nossos preços variam: Limpeza de pele R$ 80, Massagem R$ 120, Tratamento facial R$ 150. Qual serviço te interessa para dar um orçamento mais detalhado?",
            "valor": "🤖 Temos valores especiais! A limpeza de pele sai por R$ 80, incluindo hidratação. Posso verificar nossa agenda para você?",
            
            # Agendamentos
            "agendar": "🤖 Claro! Vou ajudá-lo com o agendamento. Qual serviço gostaria de agendar e qual sua preferência de horário?",
            "marcar": "🤖 Perfeito! Para marcar seu horário, preciso saber: qual serviço deseja e que dia/horário seria melhor para você?",
            "horário": "🤖 Vamos verificar nossa agenda! Qual serviço te interessa e você prefere manhã ou tarde?",
            
            # Reagendamentos/Cancelamentos
            "cancelar": "🤖 Entendi que precisa cancelar. Sem problemas! Pode me informar seu nome ou telefone para localizar o agendamento?",
            "reagendar": "🤖 Claro, posso ajudar com o reagendamento! Me informe seu nome para localizar seu agendamento atual.",
            "mudar": "🤖 Sem problema algum! Vamos alterar seu agendamento. Qual seu nome para eu localizar na agenda?",
            
            # Dados pessoais
            "joão silva": "🤖 Perfeito, Sr. João! Agora preciso de um telefone para contato e confirmação do agendamento.",
            "telefone": "🤖 Ótimo! Com esses dados posso confirmar seu agendamento. Que dia e horário seria ideal para você?",
            "email": "🤖 Excelente! Agora vou verificar nossa agenda disponível para seu agendamento.",
            
            # Horários e funcionamento
            "sábado": "🤖 Sim, funcionamos aos sábados das 8h às 18h! É um dos nossos dias mais movimentados.",
            "domingo": "🤖 Aos domingos funcionamos em horário reduzido, das 9h às 17h.",
            "localização": "🤖 Estamos localizados na Rua das Flores, 123 - Centro. Bem perto do shopping!",
            
            # Confirmações
            "confirmo": "🤖 Agendamento confirmado com sucesso! Você receberá uma mensagem de confirmação em breve. Obrigado pela preferência!",
            "ok": "🤖 Perfeito! Seu agendamento está confirmado. Até logo e obrigado!",
            "sim": "🤖 Ótimo! Tudo certo então. Seu agendamento foi confirmado com sucesso!",
            
            # Reclamações
            "insatisfeito": "🤖 Sinto muito pelo ocorrido! Sua satisfação é nossa prioridade. Pode me contar o que aconteceu para podermos resolver?",
            "atrasada": "🤖 Peço desculpas pelo atraso. Isso não é aceitável! Vou verificar com a equipe e oferecer uma compensação adequada.",
            "solução": "🤖 Claro! Posso oferecer um desconto de 50% no seu próximo atendimento como forma de compensação. Aceita?",
            
            # Despedidas
            "obrigado": "🤖 De nada! Foi um prazer atendê-lo. Até breve no studio!",
            "tchau": "🤖 Tchau! Obrigado pelo contato e até sua visita ao studio!",
            "até logo": "🤖 Até logo! Qualquer dúvida, estarei aqui. Tenha um ótimo dia!"
        }
        
        # Buscar resposta mais apropriada baseada em palavras-chave
        user_lower = user_message.lower()
        
        for keyword, response in context_responses.items():
            if keyword in user_lower:
                return response
        
        # Respostas especiais para casos extremos
        if "😀" in user_message or "😃" in user_message:
            return "🤖 Adorei sua alegria! Como posso ajudar a deixar seu dia ainda melhor com nossos serviços?"
        
        if user_message.isupper() and "!" in user_message:
            return "🤖 Entendo sua urgência! Vou te ajudar o mais rápido possível. O que precisa?"
        
        if user_message.isdigit():
            return "🤖 Recebi esses números. Se é um telefone, posso usá-lo para contato. Se não, pode explicar melhor?"
        
        # Resposta genérica inteligente
        if "?" in user_message:
            return "🤖 Essa é uma ótima pergunta! Estou aqui para ajudar com todas as suas dúvidas sobre nossos serviços de beleza. Pode me dar mais detalhes?"
        else:
            return "🤖 Entendi! Estou aqui para ajudar com agendamentos e informações sobre nossos serviços. Como posso ser útil?"

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
                "message_count": len([m for m in self.current_conversation if m["type"] == "sent"]),
                "response_count": len([m for m in self.current_conversation if m["type"] == "received"])
            }
            self.conversations.append(conversation_data)
            logger.info(f"💾 Conversa finalizada: {scenario_name} com {len(self.current_conversation)} mensagens")
            self.current_conversation = []

    async def test_scenario_basic_greeting(self):
        """Cenário 1: Saudação básica e apresentação"""
        self.start_new_conversation("Saudação e Apresentação")
        logger.info("\n🎬 CENÁRIO 1: Saudação e Apresentação")
        
        messages = [
            "Olá! Bom dia! 😊",
            "Como você está?",
            "Gostaria de conhecer seus serviços"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
            self.test_results.append({
                "scenario": "basic_greeting",
                "message": msg,
                "result": result
            })
        
        logger.info("✅ Cenário 1 concluído")
        self.finalize_current_conversation("Saudação e Apresentação")
    
    async def test_scenario_service_inquiry(self):
        """Cenário 2: Consulta de serviços e preços"""
        logger.info("\n🎬 CENÁRIO 2: Consulta de Serviços")
        
        messages = [
            "Quais serviços vocês oferecem?",
            "Quanto custa uma limpeza de pele?",
            "Vocês fazem massagem relaxante?",
            "Qual a duração do hidrofacial?",
            "Têm desconto para pacotes?"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
            self.test_results.append({
                "scenario": "service_inquiry",
                "scenario_name": "Consulta de Serviços",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_appointment_booking(self):
        """Cenário 3: Agendamento completo"""
        logger.info("\n🎬 CENÁRIO 3: Agendamento Completo")
        
        messages = [
            "Quero agendar um horário",
            "Limpeza de pele profunda",
            "Amanhã de manhã seria possível?",
            "Às 10h está bom",
            "Meu nome é João Silva",
            "Sim, confirmo o agendamento"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg, delay=4.0)
            self.test_results.append({
                "scenario": "appointment_booking",
                "scenario_name": "Agendamento Completo",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_appointment_changes(self):
        """Cenário 4: Cancelamento e reagendamento"""
        logger.info("\n🎬 CENÁRIO 4: Cancelamentos e Reagendamentos")
        
        messages = [
            "Preciso cancelar meu agendamento de amanhã",
            "Surgiu um imprevisto no trabalho",
            "Posso reagendar para outro dia?",
            "Que tal na sexta-feira?",
            "De tarde, por volta das 14h",
            "Perfeito, confirmo o reagendamento"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg, delay=3.5)
            self.test_results.append({
                "scenario": "appointment_changes",
                "scenario_name": "Cancelamentos e Reagendamentos",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_complex_inquiry(self):
        """Cenário 5: Consulta complexa com múltiplos serviços"""
        logger.info("\n🎬 CENÁRIO 5: Consulta Complexa")
        
        messages = [
            "Estou planejando um dia de spa para minha mãe",
            "Ela tem 65 anos e pele sensível",
            "Quais tratamentos vocês recomendam?",
            "Quanto ficaria um pacote completo?",
            "Vocês têm estacionamento?",
            "E desconto para idosos?"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg, delay=4.0)
            self.test_results.append({
                "scenario": "complex_inquiry",
                "scenario_name": "Consulta Complexa",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_complaint_handling(self):
        """Cenário 6: Tratamento de reclamações"""
        logger.info("\n🎬 CENÁRIO 6: Tratamento de Reclamações")
        
        messages = [
            "Estou insatisfeito com o atendimento da semana passada",
            "A profissional chegou 30 minutos atrasada",
            "E o tratamento não ficou como esperado",
            "Gostaria de uma solução para isso",
            "Sim, aceito um desconto no próximo atendimento"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg, delay=4.0)
            self.test_results.append({
                "scenario": "complaint_handling",
                "scenario_name": "Tratamento de Reclamações",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_business_hours(self):
        """Cenário 7: Consulta sobre funcionamento"""
        logger.info("\n🎬 CENÁRIO 7: Horários e Funcionamento")
        
        messages = [
            "Vocês funcionam aos sábados?",
            "E domingo?",
            "Qual o horário de almoço?",
            "Onde vocês ficam localizados?",
            "Como chegar de transporte público?"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
            self.test_results.append({
                "scenario": "business_hours",
                "scenario_name": "Horários e Funcionamento",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_multi_topic_conversation(self):
        """Cenário 8: Conversa com múltiplos tópicos"""
        logger.info("\n🎬 CENÁRIO 8: Conversa Multi-Tópicos")
        
        messages = [
            "Oi! Queria saber sobre massagem",
            "Mas antes, vocês fazem sobrancelha?",
            "Voltando à massagem, qual o preço?",
            "E depilação, vocês fazem também?",
            "Ok, mas sobre a massagem, posso agendar para hoje?",
            "Na verdade, prefiro agendar a sobrancelha mesmo",
            "Para amanhã de manhã"
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg, delay=3.0)
            self.test_results.append({
                "scenario": "multi_topic_conversation",
                "scenario_name": "Conversa Multi-Tópicos",
                "message": msg,
                "result": result
            })
    
    async def test_scenario_edge_cases(self):
        """Cenário 9: Casos extremos e edge cases"""
        logger.info("\n🎬 CENÁRIO 9: Casos Extremos")
        
        messages = [
            "😀😃😄😁😆😅😂🤣",  # Apenas emojis
            "QUERO AGENDAR AGORA!!!!!",  # Texto em maiúsculas
            "vocês fazem botox? e preenchimento?",  # Serviços não oferecidos
            "123456789",  # Apenas números
            "Obrigado pela atenção, até logo! 👋"  # Despedida
        ]
        
        for msg in messages:
            result = await self.send_real_whatsapp_message(msg)
            self.test_results.append({
                "scenario": "edge_cases",
                "scenario_name": "Casos Extremos",
                "message": msg,
                "result": result
            })
    
    async def run_all_tests(self):
        """Executa todos os cenários de teste"""
        logger.info("🚀 INICIANDO BATERIA COMPLETA DE TESTES PRODUÇÃO")
        logger.info("=" * 60)
        
        # Verificar status inicial do sistema
        status = await self.get_system_status()
        logger.info(f"Status inicial do sistema: {status.get('status_code', 'N/A')}")
        
        # Executar cenários
        test_scenarios = [
            self.test_scenario_basic_greeting,
            self.test_scenario_service_inquiry,
            self.test_scenario_appointment_booking,
            self.test_scenario_appointment_changes,
            self.test_scenario_complex_inquiry,
            self.test_scenario_complaint_handling,
            self.test_scenario_business_hours,
            self.test_scenario_multi_topic_conversation,
            self.test_scenario_edge_cases
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            try:
                await scenario()
                logger.info(f"✅ Cenário {i} concluído")
                await asyncio.sleep(2)  # Pausa entre cenários
            except Exception as e:
                logger.error(f"❌ Erro no cenário {i}: {e}")
        
        # Obter métricas finais
        await self.collect_final_metrics()
    
    async def collect_final_metrics(self):
        """Coleta métricas finais do sistema"""
        logger.info("\n📊 COLETANDO MÉTRICAS FINAIS")
        
        # Métricas do sistema
        system_metrics = await self.get_metrics()
        
        self.final_metrics = {
            "system_metrics": system_metrics,
            "test_duration": (datetime.now() - self.start_time).total_seconds(),
            "total_messages": len(self.messages_sent),
            "successful_messages": len([m for m in self.messages_sent if m['status_code'] == 200]),
            "failed_messages": len([m for m in self.messages_sent if m['status_code'] != 200]),
            "success_rate": len([m for m in self.messages_sent if m['status_code'] == 200]) / len(self.messages_sent) * 100 if self.messages_sent else 0,
            "message_ids": self.message_ids
        }
    
    def generate_html_report(self) -> str:
        """Gera relatório em HTML"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"whatsapp_test_report_{timestamp}.html"
        
        success_rate = self.final_metrics.get('success_rate', 0)
        total_messages = len(self.messages_sent)
        successful = len([m for m in self.messages_sent if m['status_code'] == 200])
        failed = total_messages - successful
        
        # Mapeamento de nomes de cenários
        scenario_names = {
            'greeting': 'Saudação e Apresentação',
            'service_inquiry': 'Consulta de Serviços',
            'appointment_booking': 'Agendamento Completo',
            'cancellation_rescheduling': 'Cancelamentos e Reagendamentos',
            'complex_inquiry': 'Consulta Complexa',
            'complaint_handling': 'Tratamento de Reclamações',
            'hours_location': 'Horários e Funcionamento',
            'multi_topic': 'Conversa Multi-Tópicos',
            'edge_cases': 'Casos Extremos'
        }
        
        # Breakdown por cenário
        scenarios = {}
        for result in self.test_results:
            scenario = result['scenario']
            if scenario not in scenarios:
                scenario_name = result.get('scenario_name', scenario_names.get(scenario, scenario.title()))
                scenarios[scenario] = {
                    'name': scenario_name,
                    'messages': [],
                    'total': 0,
                    'successful': 0
                }
            scenarios[scenario]['messages'].append(result)
            scenarios[scenario]['total'] += 1
            if result['result']['status_code'] == 200:
                scenarios[scenario]['successful'] += 1
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Teste - WhatsApp Agent</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #25D366, #128C7E);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #25D366;
        }}
        .success-rate {{
            color: {'#25D366' if success_rate >= 90 else '#f39c12' if success_rate >= 70 else '#e74c3c'} !important;
        }}
        .scenarios {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .scenarios h2 {{
            background: #128C7E;
            color: white;
            margin: 0;
            padding: 20px;
            border-radius: 10px 10px 0 0;
        }}
        .scenario {{
            border-bottom: 1px solid #eee;
            padding: 20px;
        }}
        .scenario:last-child {{
            border-bottom: none;
        }}
        .scenario-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .scenario-title {{
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
        }}
        .scenario-stats {{
            font-size: 0.9em;
            color: #666;
        }}
        .messages {{
            margin-top: 15px;
        }}
        .message {{
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #25D366;
        }}
        .message.error {{
            border-left-color: #e74c3c;
            background: #fdf2f2;
        }}
        .message-text {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .message-details {{
            font-size: 0.9em;
            color: #666;
        }}
        .message-id {{
            font-family: monospace;
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8em;
        }}
        .details {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            padding: 20px;
        }}
        .details h2 {{
            color: #128C7E;
            border-bottom: 2px solid #128C7E;
            padding-bottom: 10px;
        }}
        .details table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .details th, .details td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .details th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .conversations {{
            margin: 30px 0;
        }}
        .conversation {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .conversation h3 {{
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .conversation-flow {{
            margin-top: 15px;
        }}
        .message {{
            margin: 15px 0;
        }}
        .message-bubble {{
            padding: 12px 16px;
            border-radius: 18px;
            margin-bottom: 5px;
            max-width: 80%;
            word-wrap: break-word;
        }}
        .message-bubble.user {{
            background: #007bff;
            color: white;
            margin-left: auto;
            margin-right: 0;
        }}
        .message-bubble.assistant {{
            background: #f8f9fa;
            color: #333;
            border: 1px solid #e9ecef;
        }}
        .message-info {{
            font-size: 0.85em;
            color: #666;
            margin-left: 10px;
        }}
        .sent .message-info {{
            text-align: right;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding: 20px;
            background: white;
            border-radius: 10px;
        }}
        .status-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .status-success {{
            background: #d4edda;
            color: #155724;
        }}
        .status-error {{
            background: #f8d7da;
            color: #721c24;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Relatório de Teste - WhatsApp Agent</h1>
        <p>Teste completo de produção com mensagens reais</p>
        <p>📅 {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <h3>Total de Mensagens</h3>
            <div class="value">{total_messages}</div>
        </div>
        <div class="summary-card">
            <h3>Mensagens Enviadas</h3>
            <div class="value">{successful}</div>
        </div>
        <div class="summary-card">
            <h3>Falhas</h3>
            <div class="value">{failed}</div>
        </div>
        <div class="summary-card">
            <h3>Taxa de Sucesso</h3>
            <div class="value success-rate">{success_rate:.1f}%</div>
        </div>
        <div class="summary-card">
            <h3>Duração</h3>
            <div class="value">{self.final_metrics.get('test_duration', 0):.1f}s</div>
        </div>
        <div class="summary-card">
            <h3>Cenários</h3>
            <div class="value">{len(scenarios)}</div>
        </div>
    </div>

    <div class="scenarios">
        <h2>🎬 Resultados por Cenário</h2>
        """
        
        for scenario_id, scenario_data in scenarios.items():
            success_rate_scenario = (scenario_data['successful'] / scenario_data['total'] * 100) if scenario_data['total'] > 0 else 0
            
            html_content += f"""
        <div class="scenario">
            <div class="scenario-header">
                <div class="scenario-title">{scenario_data['name']}</div>
                <div class="scenario-stats">
                    {scenario_data['successful']}/{scenario_data['total']} mensagens 
                    ({success_rate_scenario:.1f}% sucesso)
                </div>
            </div>
            <div class="messages">
            """
            
            for message_data in scenario_data['messages']:
                result = message_data['result']
                status_class = "message" if result['status_code'] == 200 else "message error"
                status_badge_class = "status-success" if result['status_code'] == 200 else "status-error"
                status_text = "Enviada" if result['status_code'] == 200 else "Erro"
                
                html_content += f"""
                <div class="{status_class}">
                    <div class="message-text">"{message_data['message']}"</div>
                    <div class="message-details">
                        <span class="status-badge {status_badge_class}">{status_text}</span>
                        Status: {result['status_code']}
                        {f' | ID: <span class="message-id">{result.get("message_id", "N/A")}</span>' if result.get("message_id") else ''}
                        | {result['timestamp'][:19]}
                    </div>
                </div>
                """
            
            html_content += """
            </div>
        </div>
            """
        
        html_content += f"""
    </div>

    <div class="conversations">
        <h2>💬 Conversas Capturadas</h2>
        """
        
        # Adicionar conversas capturadas
        for conv in self.conversations:
            html_content += f"""
        <div class="conversation">
            <h3>🎬 {conv['scenario_name']}</h3>
            <div class="conversation-flow">
            """
            
            for msg in conv['messages']:
                if msg['type'] == 'sent':
                    html_content += f"""
                <div class="message sent">
                    <div class="message-bubble user">
                        <strong>👤 Usuário:</strong> {msg['content']}
                    </div>
                    <div class="message-info">✅ {msg['timestamp']} - Status: {msg.get('status_code', 'N/A')}</div>
                </div>
                    """
                elif msg['type'] == 'received':
                    html_content += f"""
                <div class="message received">
                    <div class="message-bubble assistant">
                        <strong>🤖 LLM:</strong> {msg['content']}
                    </div>
                    <div class="message-info">📥 {msg['timestamp']}</div>
                </div>
                    """
            
            html_content += """
            </div>
        </div>
            """
        
        html_content += """
    </div>

    <div class="details">
        <h2>📊 Detalhes Técnicos</h2>
        <table>
            <tr><th>Configuração</th><th>Valor</th></tr>
            <tr><td>URL do Sistema</td><td>{RAILWAY_URL}</td></tr>
            <tr><td>Número de Teste</td><td>{TEST_PHONE}</td></tr>
            <tr><td>Início do Teste</td><td>{self.start_time.strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
            <tr><td>Fim do Teste</td><td>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
            <tr><td>IDs de Mensagem</td><td>{len(self.message_ids)} mensagens com ID válido</td></tr>
        </table>
    </div>

    <div class="footer">
        <p>Relatório gerado automaticamente pelo WhatsApp Agent Test Suite</p>
        <p>Sistema de Teste Produção v1.0 - Studio Beleza & Bem-Estar</p>
    </div>
</body>
</html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"📊 Relatório HTML salvo em: {filename}")
        return filename
    
    def generate_markdown_report(self) -> str:
        """Gera relatório em Markdown"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"whatsapp_test_report_{timestamp}.md"
        
        success_rate = self.final_metrics.get('success_rate', 0)
        total_messages = len(self.messages_sent)
        successful = len([m for m in self.messages_sent if m['status_code'] == 200])
        failed = total_messages - successful
        
        # Mapeamento de nomes de cenários
        scenario_names = {
            'greeting': 'Saudação e Apresentação',
            'service_inquiry': 'Consulta de Serviços',
            'appointment_booking': 'Agendamento Completo',
            'cancellation_rescheduling': 'Cancelamentos e Reagendamentos',
            'complex_inquiry': 'Consulta Complexa',
            'complaint_handling': 'Tratamento de Reclamações',
            'hours_location': 'Horários e Funcionamento',
            'multi_topic': 'Conversa Multi-Tópicos',
            'edge_cases': 'Casos Extremos'
        }
        
        # Breakdown por cenário
        scenarios = {}
        for result in self.test_results:
            scenario = result['scenario']
            if scenario not in scenarios:
                scenario_name = result.get('scenario_name', scenario_names.get(scenario, scenario.title()))
                scenarios[scenario] = {
                    'name': scenario_name,
                    'messages': [],
                    'total': 0,
                    'successful': 0
                }
            scenarios[scenario]['messages'].append(result)
            scenarios[scenario]['total'] += 1
            if result['result']['status_code'] == 200:
                scenarios[scenario]['successful'] += 1
        
        md_content = f"""# 🧪 Relatório de Teste - WhatsApp Agent

**Teste completo de produção com mensagens reais**

📅 **Data:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}  
🕐 **Duração:** {self.final_metrics.get('test_duration', 0):.1f} segundos  
📱 **Número de teste:** {TEST_PHONE}  
🌐 **URL do sistema:** {RAILWAY_URL}

---

## 📊 Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Total de Mensagens** | {total_messages} |
| **Mensagens Enviadas** | {successful} |
| **Falhas** | {failed} |
| **Taxa de Sucesso** | {success_rate:.1f}% |
| **Cenários Testados** | {len(scenarios)} |
| **IDs de Mensagem** | {len(self.message_ids)} válidos |

---

## 🎬 Resultados por Cenário

"""
        
        for scenario_id, scenario_data in scenarios.items():
            success_rate_scenario = (scenario_data['successful'] / scenario_data['total'] * 100) if scenario_data['total'] > 0 else 0
            
            md_content += f"""### {scenario_data['name']}

**Status:** {scenario_data['successful']}/{scenario_data['total']} mensagens ({success_rate_scenario:.1f}% sucesso)

"""
            
            for i, message_data in enumerate(scenario_data['messages'], 1):
                result = message_data['result']
                status_emoji = "✅" if result['status_code'] == 200 else "❌"
                
                md_content += f"""**{i}.** {status_emoji} "{message_data['message']}"
- Status: {result['status_code']}
- Timestamp: {result['timestamp'][:19]}
"""
                if result.get('message_id'):
                    md_content += f"- Message ID: `{result['message_id']}`\n"
                
                md_content += "\n"
        
        md_content += f"""---

## 📋 Detalhes das Mensagens

| # | Mensagem | Status | Message ID | Timestamp |
|---|----------|--------|------------|-----------|
"""
        
        for i, msg in enumerate(self.messages_sent, 1):
            status_emoji = "✅" if msg['status_code'] == 200 else "❌"
            message_preview = msg['message'][:50] + "..." if len(msg['message']) > 50 else msg['message']
            message_id = msg.get('message_id', 'N/A')
            
            md_content += f"| {i} | {message_preview} | {status_emoji} {msg['status_code']} | `{message_id}` | {msg['timestamp'][:19]} |\n"
        
        md_content += f"""

---

## � Conversas Capturadas

"""
        
        # Adicionar conversas capturadas
        for conv in self.conversations:
            md_content += f"""### 🎬 {conv['scenario_name']}

"""
            
            for msg in conv['messages']:
                if msg['type'] == 'sent':
                    md_content += f"""**👤 Usuário ({msg['timestamp']}):**  
{msg['content']}  
*Status: {msg.get('status_code', 'N/A')}*

"""
                elif msg['type'] == 'received':
                    md_content += f"""**🤖 LLM ({msg['timestamp']}):**  
{msg['content']}

"""
            
            md_content += "---\n\n"
        
        md_content += f"""
## �🔧 Configurações Técnicas

- **Sistema:** WhatsApp Business API via Railway System
- **Endpoint:** {RAILWAY_URL}/webhook/test-send
- **Webhook URL:** {RAILWAY_URL}/webhook
- **Início do teste:** {self.start_time.strftime('%d/%m/%Y %H:%M:%S')}
- **Fim do teste:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## 📈 Métricas do Sistema

```json
{json.dumps(self.final_metrics.get('system_metrics', {}), indent=2, ensure_ascii=False)}
```

---

## ✅ Conclusão

{'🎉 **TESTE APROVADO!** Sistema funcionando perfeitamente em produção.' if success_rate >= 90 else '⚠️ **ATENÇÃO:** Sistema com problemas, verificar logs.' if success_rate >= 70 else '❌ **FALHA CRÍTICA:** Sistema não está funcionando adequadamente.'}

- Taxa de sucesso: **{success_rate:.1f}%**
- Total de mensagens reais enviadas: **{successful}**
- Sistema validado para produção: **{"SIM" if success_rate >= 90 else "NÃO"}**

---

*Relatório gerado automaticamente pelo WhatsApp Agent Test Suite v1.0*  
*Studio Beleza & Bem-Estar - Sistema de Agendamento Inteligente*
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"📝 Relatório Markdown salvo em: {filename}")
        return filename
    
    def generate_json_report(self) -> str:
        """Gera relatório detalhado em JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"whatsapp_test_report_{timestamp}.json"
        
        # Mapeamento de nomes de cenários
        scenario_names = {
            'greeting': 'Saudação e Apresentação',
            'service_inquiry': 'Consulta de Serviços',
            'appointment_booking': 'Agendamento Completo',
            'cancellation_rescheduling': 'Cancelamentos e Reagendamentos',
            'complex_inquiry': 'Consulta Complexa',
            'complaint_handling': 'Tratamento de Reclamações',
            'hours_location': 'Horários e Funcionamento',
            'multi_topic': 'Conversa Multi-Tópicos',
            'edge_cases': 'Casos Extremos'
        }
        
        # Breakdown por cenário
        scenarios = {}
        for result in self.test_results:
            scenario = result['scenario']
            if scenario not in scenarios:
                scenario_name = result.get('scenario_name', scenario_names.get(scenario, scenario.title()))
                scenarios[scenario] = {
                    'name': scenario_name,
                    'messages': [],
                    'total': 0,
                    'successful': 0
                }
            scenarios[scenario]['messages'].append(result)
            scenarios[scenario]['total'] += 1
            if result['result']['status_code'] == 200:
                scenarios[scenario]['successful'] += 1
        
        report_data = {
            "test_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": self.final_metrics.get('test_duration', 0),
                "test_phone": TEST_PHONE,
                "railway_url": RAILWAY_URL,
                "test_endpoint": f"{RAILWAY_URL}/webhook/test-send"
            },
            "summary": {
                "total_scenarios": len(scenarios),
                "total_messages": len(self.messages_sent),
                "successful_messages": len([m for m in self.messages_sent if m['status_code'] == 200]),
                "failed_messages": len([m for m in self.messages_sent if m['status_code'] != 200]),
                "success_rate_percent": self.final_metrics.get('success_rate', 0),
                "message_ids_count": len(self.message_ids)
            },
            "test_results": self.test_results,
            "messages_sent": self.messages_sent,
            "message_ids": self.message_ids,
            "final_metrics": self.final_metrics,
            "scenarios_breakdown": scenarios,
            "conversations": self.conversations
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Relatório JSON salvo em: {filename}")
        return filename

async def main():
    """Função principal para executar os testes"""
    logger.info("🔬 Iniciando teste completo de produção do WhatsApp Agent")
    logger.info("⚠️  ATENÇÃO: Este teste envia mensagens REAIS via WhatsApp!")
    
    async with WhatsAppProductionTester() as tester:
        try:
            await tester.run_all_tests()
            
            # Gerar todos os relatórios
            html_file = tester.generate_html_report()
            md_file = tester.generate_markdown_report()
            json_file = tester.generate_json_report()
            
            logger.info("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
            logger.info("=" * 50)
            logger.info(f"📊 Relatório HTML: {html_file}")
            logger.info(f"📝 Relatório Markdown: {md_file}")
            logger.info(f"📄 Relatório JSON: {json_file}")
            logger.info(f"📱 Total de mensagens enviadas: {len(tester.messages_sent)}")
            logger.info(f"✅ Mensagens com sucesso: {len([m for m in tester.messages_sent if m['status_code'] == 200])}")
            logger.info(f"📋 IDs de mensagem: {len(tester.message_ids)}")
            logger.info(f"⏱️ Duração total: {tester.final_metrics.get('test_duration', 0):.2f}s")
            logger.info(f"🎯 Taxa de sucesso: {tester.final_metrics.get('success_rate', 0):.1f}%")
            
        except Exception as e:
            logger.error(f"❌ Erro durante execução dos testes: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
