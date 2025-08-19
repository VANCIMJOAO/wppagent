#!/usr/bin/env python3
"""
🤖 TESTADOR ESPECÍFICO DE MENSAGENS WHATSAPP
============================================

Este script testa especificamente o fluxo completo de mensagens WhatsApp:
- Simulação de conversas reais
- Teste de agendamentos via WhatsApp
- Teste de cancelamentos
- Teste de coleta de dados
- Teste de diferentes tipos de mensagem
- Validação de respostas da LLM

Uso:
    python whatsapp_message_tester.py --test-conversations
    python whatsapp_message_tester.py --test-appointments
    python whatsapp_message_tester.py --test-all
"""

import asyncio
import json
import os
import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
import psycopg2
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MessageTest:
    """Teste de mensagem individual"""
    user_id: str
    message: str
    expected_keywords: List[str]
    test_type: str
    description: str

class WhatsAppMessageTester:
    """Testador específico para mensagens WhatsApp"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base = config.get('api_base', 'http://localhost:8000')
        self.webhook_url = f"{self.api_base}/webhook"
        
        # Conectar ao banco
        self.db_connection = psycopg2.connect(
            host=config.get('DB_HOST', 'localhost'),
            port=int(config.get('DB_PORT', 5432)),
            user=config.get('DB_USER'),
            password=config.get('DB_PASSWORD'),
            database=config.get('DB_NAME')
        )
        
        self.test_results = []
        self.created_users = []
        self.created_conversations = []
        self.created_appointments = []
    
    def simulate_whatsapp_message(self, user_id: str, message: str, message_type: str = "text") -> dict:
        """Simular recebimento de mensagem do WhatsApp"""
        
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "ENTRY_ID",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550000000",
                            "phone_number_id": self.config.get('PHONE_NUMBER_ID', 'TEST_PHONE_ID')
                        },
                        "contacts": [{
                            "profile": {"name": f"Test User {user_id}"},
                            "wa_id": user_id
                        }],
                        "messages": [{
                            "from": user_id,
                            "id": f"wamid_{int(time.time())}_{random.randint(1000, 9999)}",
                            "timestamp": str(int(time.time())),
                            "type": message_type
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        # Adicionar conteúdo baseado no tipo
        if message_type == "text":
            webhook_payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"] = {
                "body": message
            }
        elif message_type == "button":
            webhook_payload["entry"][0]["changes"][0]["value"]["messages"][0]["button"] = {
                "text": message,
                "payload": f"button_payload_{int(time.time())}"
            }
        
        # Enviar webhook
        try:
            response = requests.post(
                self.webhook_url,
                json=webhook_payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            return {
                "status_code": response.status_code,
                "response": response.text,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "status_code": 0,
                "response": str(e),
                "success": False
            }
    
    def wait_for_response(self, user_id: str, timeout: int = 30) -> List[str]:
        """Aguardar resposta da LLM no banco de dados"""
        
        start_time = time.time()
        responses = []
        
        while time.time() - start_time < timeout:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    SELECT content, created_at FROM messages 
                    WHERE user_id = (SELECT id FROM users WHERE wa_id = %s)
                    AND direction = 'out'
                    AND created_at > NOW() - INTERVAL '2 minutes'
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (user_id,))
                
                new_responses = cursor.fetchall()
                
                for response_content, created_at in new_responses:
                    if response_content not in responses:
                        responses.append(response_content)
                        logger.info(f"📨 Resposta recebida para {user_id}: {response_content[:100]}...")
                
                if responses:
                    break
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Erro ao verificar respostas: {e}")
                break
        
        return responses
    
    def check_appointment_created(self, user_id: str) -> Dict[str, Any]:
        """Verificar se agendamento foi criado"""
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT a.id, a.date_time, a.status, s.name as service_name
                FROM appointments a
                JOIN users u ON a.user_id = u.id
                JOIN services s ON a.service_id = s.id
                WHERE u.wa_id = %s
                AND a.created_at > NOW() - INTERVAL '5 minutes'
                ORDER BY a.created_at DESC
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "found": True,
                    "appointment_id": result[0],
                    "date_time": result[1],
                    "status": result[2],
                    "service_name": result[3]
                }
            else:
                return {"found": False}
                
        except Exception as e:
            logger.error(f"Erro ao verificar agendamento: {e}")
            return {"found": False, "error": str(e)}
    
    def test_conversation_flow(self) -> Dict[str, Any]:
        """Testar fluxo completo de conversa"""
        
        logger.info("🗣️ Testando fluxo de conversa...")
        
        # Conversas de teste
        conversation_tests = [
            {
                "user_id": f"test_conv_{int(time.time())}_1",
                "messages": [
                    "Olá",
                    "Gostaria de agendar um horário",
                    "João Silva",
                    "joao@email.com",
                    "11999887766",
                    "Corte de cabelo",
                    "Amanhã às 14h"
                ],
                "expected_flow": ["greeting", "appointment_request", "data_collection", "scheduling"]
            },
            {
                "user_id": f"test_conv_{int(time.time())}_2", 
                "messages": [
                    "Oi, bom dia!",
                    "Quais serviços vocês oferecem?",
                    "Quanto custa um corte?",
                    "Obrigado!"
                ],
                "expected_flow": ["greeting", "service_inquiry", "pricing", "farewell"]
            }
        ]
        
        results = []
        
        for test in conversation_tests:
            user_id = test["user_id"]
            logger.info(f"👤 Testando conversa com usuário: {user_id}")
            
            conversation_result = {
                "user_id": user_id,
                "messages_sent": 0,
                "responses_received": 0,
                "errors": [],
                "llm_responses": [],
                "success": False
            }
            
            for i, message in enumerate(test["messages"]):
                logger.info(f"📤 Enviando mensagem {i+1}: {message}")
                
                # Enviar mensagem
                send_result = self.simulate_whatsapp_message(user_id, message)
                conversation_result["messages_sent"] += 1
                
                if not send_result["success"]:
                    conversation_result["errors"].append(f"Falha ao enviar mensagem {i+1}: {send_result['response']}")
                    continue
                
                # Aguardar resposta
                responses = self.wait_for_response(user_id, timeout=20)
                
                if responses:
                    conversation_result["responses_received"] += len(responses)
                    conversation_result["llm_responses"].extend(responses)
                    logger.info(f"✅ Resposta recebida: {responses[0][:100]}...")
                else:
                    conversation_result["errors"].append(f"Nenhuma resposta para mensagem {i+1}")
                
                # Aguardar um pouco entre mensagens
                time.sleep(2)
            
            # Verificar sucesso geral
            response_rate = conversation_result["responses_received"] / conversation_result["messages_sent"]
            conversation_result["success"] = response_rate >= 0.8 and len(conversation_result["errors"]) == 0
            
            results.append(conversation_result)
            self.created_users.append(user_id)
        
        # Resumo
        successful_conversations = len([r for r in results if r["success"]])
        
        return {
            "total_conversations": len(conversation_tests),
            "successful_conversations": successful_conversations,
            "success_rate": successful_conversations / len(conversation_tests) * 100,
            "details": results
        }
    
    def test_appointment_booking(self) -> Dict[str, Any]:
        """Testar agendamento completo via WhatsApp"""
        
        logger.info("📅 Testando agendamento via WhatsApp...")
        
        appointment_tests = [
            {
                "user_id": f"test_appointment_{int(time.time())}_1",
                "flow": [
                    "Quero agendar um horário",
                    "Maria Santos",
                    "maria@email.com", 
                    "11987654321",
                    "Corte e escova",
                    "Amanhã às 15h"
                ]
            },
            {
                "user_id": f"test_appointment_{int(time.time())}_2",
                "flow": [
                    "Preciso marcar um horário",
                    "Pedro Oliveira",
                    "pedro@gmail.com",
                    "11876543210", 
                    "Barba",
                    "Sexta-feira às 10h"
                ]
            }
        ]
        
        results = []
        
        for test in appointment_tests:
            user_id = test["user_id"]
            logger.info(f"👤 Testando agendamento para: {user_id}")
            
            appointment_result = {
                "user_id": user_id,
                "messages_sent": 0,
                "appointment_created": False,
                "appointment_details": {},
                "errors": [],
                "success": False
            }
            
            for message in test["flow"]:
                logger.info(f"📤 Enviando: {message}")
                
                send_result = self.simulate_whatsapp_message(user_id, message)
                appointment_result["messages_sent"] += 1
                
                if not send_result["success"]:
                    appointment_result["errors"].append(f"Falha ao enviar: {message}")
                    continue
                
                # Aguardar processamento
                time.sleep(3)
                
                # Aguardar resposta
                responses = self.wait_for_response(user_id, timeout=15)
                if not responses:
                    appointment_result["errors"].append(f"Sem resposta para: {message}")
            
            # Verificar se agendamento foi criado
            time.sleep(5)  # Aguardar processamento final
            appointment_check = self.check_appointment_created(user_id)
            
            if appointment_check["found"]:
                appointment_result["appointment_created"] = True
                appointment_result["appointment_details"] = appointment_check
                appointment_result["success"] = True
                self.created_appointments.append(appointment_check["appointment_id"])
                logger.info(f"✅ Agendamento criado: ID {appointment_check['appointment_id']}")
            else:
                appointment_result["errors"].append("Agendamento não foi criado no banco")
            
            results.append(appointment_result)
            self.created_users.append(user_id)
        
        # Resumo
        successful_appointments = len([r for r in results if r["appointment_created"]])
        
        return {
            "total_tests": len(appointment_tests),
            "successful_appointments": successful_appointments,
            "success_rate": successful_appointments / len(appointment_tests) * 100,
            "details": results
        }
    
    def test_appointment_cancellation(self) -> Dict[str, Any]:
        """Testar cancelamento de agendamentos"""
        
        logger.info("❌ Testando cancelamento de agendamentos...")
        
        if not self.created_appointments:
            return {
                "success": False,
                "message": "Nenhum agendamento disponível para cancelar"
            }
        
        # Criar teste de cancelamento
        user_id = f"test_cancel_{int(time.time())}"
        
        cancel_result = {
            "user_id": user_id,
            "messages_sent": 0,
            "cancellation_successful": False,
            "errors": []
        }
        
        # Simular fluxo de cancelamento
        cancel_messages = [
            "Olá",
            "Gostaria de cancelar meu agendamento",
            "Sim, confirmo o cancelamento"
        ]
        
        for message in cancel_messages:
            logger.info(f"📤 Enviando: {message}")
            
            send_result = self.simulate_whatsapp_message(user_id, message)
            cancel_result["messages_sent"] += 1
            
            if not send_result["success"]:
                cancel_result["errors"].append(f"Falha ao enviar: {message}")
                continue
            
            time.sleep(3)
            
            # Aguardar resposta
            responses = self.wait_for_response(user_id, timeout=15)
            if not responses:
                cancel_result["errors"].append(f"Sem resposta para: {message}")
        
        # Verificar cancelamentos no banco
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM appointments 
                WHERE status = 'cancelled' 
                AND cancelled_at > NOW() - INTERVAL '5 minutes'
            """)
            recent_cancellations = cursor.fetchone()[0]
            
            if recent_cancellations > 0:
                cancel_result["cancellation_successful"] = True
                logger.info(f"✅ {recent_cancellations} cancelamentos detectados")
            
        except Exception as e:
            cancel_result["errors"].append(f"Erro ao verificar cancelamentos: {e}")
        
        self.created_users.append(user_id)
        
        return {
            "success": cancel_result["cancellation_successful"],
            "details": cancel_result
        }
    
    def test_data_collection(self) -> Dict[str, Any]:
        """Testar coleta de dados do usuário"""
        
        logger.info("📋 Testando coleta de dados...")
        
        user_id = f"test_data_{int(time.time())}"
        
        data_collection_result = {
            "user_id": user_id,
            "data_collected": {},
            "collection_successful": False,
            "errors": []
        }
        
        # Fluxo de coleta de dados
        data_messages = [
            "Olá, preciso de informações",
            "João da Silva",
            "joao.silva@email.com",
            "11987654321"
        ]
        
        for message in data_messages:
            logger.info(f"📤 Enviando: {message}")
            
            send_result = self.simulate_whatsapp_message(user_id, message)
            
            if not send_result["success"]:
                data_collection_result["errors"].append(f"Falha ao enviar: {message}")
                continue
            
            time.sleep(2)
            
            # Aguardar resposta
            responses = self.wait_for_response(user_id, timeout=10)
            if not responses:
                data_collection_result["errors"].append(f"Sem resposta para: {message}")
        
        # Verificar dados coletados
        try:
            cursor = self.db_connection.cursor()
            
            # Verificar usuário criado
            cursor.execute("""
                SELECT wa_id, nome, email, telefone FROM users 
                WHERE wa_id = %s
            """, (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                data_collection_result["data_collected"] = {
                    "wa_id": user_data[0],
                    "nome": user_data[1],
                    "email": user_data[2],
                    "telefone": user_data[3]
                }
                
                # Verificar se dados essenciais foram coletados
                has_name = bool(user_data[1])
                has_email = bool(user_data[2]) 
                has_phone = bool(user_data[3])
                
                data_collection_result["collection_successful"] = has_name and (has_email or has_phone)
                
                if data_collection_result["collection_successful"]:
                    logger.info(f"✅ Dados coletados com sucesso para {user_id}")
            else:
                data_collection_result["errors"].append("Usuário não foi criado no banco")
                
        except Exception as e:
            data_collection_result["errors"].append(f"Erro ao verificar dados: {e}")
        
        self.created_users.append(user_id)
        
        return data_collection_result
    
    def test_message_types(self) -> Dict[str, Any]:
        """Testar diferentes tipos de mensagem"""
        
        logger.info("💬 Testando tipos de mensagem...")
        
        message_types_tests = [
            {
                "type": "text",
                "content": "Esta é uma mensagem de texto simples",
                "description": "Mensagem de texto básica"
            },
            {
                "type": "text",
                "content": "📅 Quero agendar um horário para amanhã às 14h 💇‍♀️",
                "description": "Mensagem com emojis"
            },
            {
                "type": "text", 
                "content": "Olá! Como estão os preços dos serviços? Vocês fazem desconto para estudantes?",
                "description": "Mensagem longa com múltiplas perguntas"
            }
        ]
        
        results = []
        
        for test in message_types_tests:
            user_id = f"test_msgtype_{int(time.time())}_{random.randint(100, 999)}"
            
            logger.info(f"📤 Testando {test['description']}")
            
            test_result = {
                "type": test["type"],
                "description": test["description"], 
                "user_id": user_id,
                "message_sent": False,
                "response_received": False,
                "response_content": "",
                "errors": []
            }
            
            # Enviar mensagem
            send_result = self.simulate_whatsapp_message(user_id, test["content"], test["type"])
            
            if send_result["success"]:
                test_result["message_sent"] = True
                
                # Aguardar resposta
                responses = self.wait_for_response(user_id, timeout=15)
                
                if responses:
                    test_result["response_received"] = True
                    test_result["response_content"] = responses[0]
                    logger.info(f"✅ Resposta recebida para {test['description']}")
                else:
                    test_result["errors"].append("Nenhuma resposta recebida")
            else:
                test_result["errors"].append(f"Falha ao enviar: {send_result['response']}")
            
            results.append(test_result)
            self.created_users.append(user_id)
        
        # Resumo
        successful_tests = len([r for r in results if r["response_received"]])
        
        return {
            "total_tests": len(message_types_tests),
            "successful_tests": successful_tests,
            "success_rate": successful_tests / len(message_types_tests) * 100,
            "details": results
        }
    
    def cleanup_test_data(self):
        """Limpar dados de teste"""
        
        logger.info("🧹 Limpando dados de teste...")
        
        try:
            cursor = self.db_connection.cursor()
            
            # Remover agendamentos de teste
            if self.created_appointments:
                cursor.execute("DELETE FROM appointments WHERE id = ANY(%s)", (self.created_appointments,))
                logger.info(f"Removidos {len(self.created_appointments)} agendamentos de teste")
            
            # Remover usuários de teste
            if self.created_users:
                cursor.execute("DELETE FROM users WHERE wa_id = ANY(%s)", (self.created_users,))
                logger.info(f"Removidos {len(self.created_users)} usuários de teste")
            
            # Remover mensagens de teste
            cursor.execute("""
                DELETE FROM messages 
                WHERE user_id IN (
                    SELECT id FROM users WHERE wa_id LIKE 'test_%'
                ) OR message_id LIKE 'wamid_%'
            """)
            
            # Remover conversas de teste
            cursor.execute("""
                DELETE FROM conversations 
                WHERE user_id IN (
                    SELECT id FROM users WHERE wa_id LIKE 'test_%'
                )
            """)
            
            self.db_connection.commit()
            logger.info("✅ Limpeza concluída")
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza: {e}")
    
    def run_all_tests(self):
        """Executar todos os testes"""
        
        logger.info("🚀 Iniciando testes completos de mensagens WhatsApp")
        
        all_results = {
            "start_time": datetime.now().isoformat(),
            "tests": {}
        }
        
        try:
            # Teste 1: Fluxo de conversas
            logger.info("\n" + "="*50)
            all_results["tests"]["conversation_flow"] = self.test_conversation_flow()
            
            # Teste 2: Agendamentos
            logger.info("\n" + "="*50)
            all_results["tests"]["appointment_booking"] = self.test_appointment_booking()
            
            # Teste 3: Cancelamentos
            logger.info("\n" + "="*50)
            all_results["tests"]["appointment_cancellation"] = self.test_appointment_cancellation()
            
            # Teste 4: Coleta de dados
            logger.info("\n" + "="*50)
            all_results["tests"]["data_collection"] = self.test_data_collection()
            
            # Teste 5: Tipos de mensagem
            logger.info("\n" + "="*50)
            all_results["tests"]["message_types"] = self.test_message_types()
            
        except Exception as e:
            logger.error(f"❌ Erro durante os testes: {e}")
            all_results["error"] = str(e)
        
        all_results["end_time"] = datetime.now().isoformat()
        
        # Gerar relatório
        self.generate_whatsapp_report(all_results)
        
        return all_results
    
    def generate_whatsapp_report(self, results: Dict[str, Any]):
        """Gerar relatório específico dos testes WhatsApp"""
        
        print("\n" + "="*80)
        print("📊 RELATÓRIO - TESTES DE MENSAGENS WHATSAPP")
        print("="*80)
        
        total_success = 0
        total_tests = 0
        
        for test_name, test_result in results["tests"].items():
            print(f"\n📱 {test_name.upper().replace('_', ' ')}")
            print("-" * 40)
            
            if test_name == "conversation_flow":
                success_rate = test_result["success_rate"]
                total = test_result["total_conversations"]
                successful = test_result["successful_conversations"]
                
                print(f"   Conversas testadas: {total}")
                print(f"   Conversas bem-sucedidas: {successful}")
                print(f"   Taxa de sucesso: {success_rate:.1f}%")
                
                total_tests += total
                total_success += successful
                
            elif test_name == "appointment_booking":
                success_rate = test_result["success_rate"]
                total = test_result["total_tests"]
                successful = test_result["successful_appointments"]
                
                print(f"   Agendamentos testados: {total}")
                print(f"   Agendamentos criados: {successful}")
                print(f"   Taxa de sucesso: {success_rate:.1f}%")
                
                total_tests += total
                total_success += successful
                
            elif test_name == "appointment_cancellation":
                success = "✅ SIM" if test_result["success"] else "❌ NÃO"
                print(f"   Cancelamento funcionando: {success}")
                
                total_tests += 1
                if test_result["success"]:
                    total_success += 1
                
            elif test_name == "data_collection":
                success = "✅ SIM" if test_result["collection_successful"] else "❌ NÃO"
                print(f"   Coleta de dados: {success}")
                
                if test_result["data_collected"]:
                    data = test_result["data_collected"]
                    print(f"   Nome coletado: {'✅' if data.get('nome') else '❌'}")
                    print(f"   Email coletado: {'✅' if data.get('email') else '❌'}")
                    print(f"   Telefone coletado: {'✅' if data.get('telefone') else '❌'}")
                
                total_tests += 1
                if test_result["collection_successful"]:
                    total_success += 1
                
            elif test_name == "message_types":
                success_rate = test_result["success_rate"] 
                total = test_result["total_tests"]
                successful = test_result["successful_tests"]
                
                print(f"   Tipos testados: {total}")
                print(f"   Respostas recebidas: {successful}")
                print(f"   Taxa de sucesso: {success_rate:.1f}%")
                
                total_tests += total
                total_success += successful
        
        # Resumo geral
        overall_success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 RESUMO GERAL:")
        print(f"   Total de testes: {total_tests}")
        print(f"   Testes bem-sucedidos: {total_success}")
        print(f"   Taxa de sucesso geral: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 90:
            print("🟢 EXCELENTE - Sistema WhatsApp funcionando perfeitamente!")
        elif overall_success_rate >= 75:
            print("🟡 BOM - Alguns ajustes podem ser necessários")
        elif overall_success_rate >= 50:
            print("🟠 ATENÇÃO - Problemas detectados no sistema")
        else:
            print("🔴 CRÍTICO - Sistema WhatsApp com falhas graves")
        
        # Salvar relatório
        timestamp = int(time.time())
        with open(f"whatsapp_test_report_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo: whatsapp_test_report_{timestamp}.json")

def load_config():
    """Carregar configuração"""
    config = {}
    
    # Tentar carregar do .env
    env_files = ['.env', '.env.development', '.env.testing']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        config[key] = value.strip('"\'')
            break
    
    return config

async def main():
    """Função principal"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Testador de Mensagens WhatsApp")
    parser.add_argument("--test-conversations", action="store_true", help="Testar apenas conversas")
    parser.add_argument("--test-appointments", action="store_true", help="Testar apenas agendamentos")
    parser.add_argument("--test-cancellations", action="store_true", help="Testar cancelamentos")
    parser.add_argument("--test-data-collection", action="store_true", help="Testar coleta de dados")
    parser.add_argument("--test-message-types", action="store_true", help="Testar tipos de mensagem")
    parser.add_argument("--test-all", action="store_true", help="Executar todos os testes")
    parser.add_argument("--cleanup", action="store_true", help="Apenas limpar dados de teste")
    
    args = parser.parse_args()
    
    # Carregar configuração
    config = load_config()
    
    if not config:
        logger.error("❌ Configuração não encontrada. Certifique-se de ter um arquivo .env")
        return
    
    # Inicializar testador
    tester = WhatsAppMessageTester(config)
    
    try:
        if args.cleanup:
            tester.cleanup_test_data()
            return
        
        results = {}
        
        if args.test_all or not any([args.test_conversations, args.test_appointments, 
                                   args.test_cancellations, args.test_data_collection, 
                                   args.test_message_types]):
            # Executar todos os testes
            results = tester.run_all_tests()
        else:
            # Executar testes específicos
            if args.test_conversations:
                results["conversation_flow"] = tester.test_conversation_flow()
            
            if args.test_appointments:
                results["appointment_booking"] = tester.test_appointment_booking()
            
            if args.test_cancellations:
                results["appointment_cancellation"] = tester.test_appointment_cancellation()
            
            if args.test_data_collection:
                results["data_collection"] = tester.test_data_collection()
            
            if args.test_message_types:
                results["message_types"] = tester.test_message_types()
        
        # Limpar dados de teste
        tester.cleanup_test_data()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Teste interrompido pelo usuário")
        tester.cleanup_test_data()
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        tester.cleanup_test_data()
        raise
    finally:
        if tester.db_connection:
            tester.db_connection.close()

if __name__ == "__main__":
    asyncio.run(main())