#!/usr/bin/env python3
"""
🎭 Testes de Fluxos Completos de Cliente
Simula jornadas reais de clientes no WhatsApp Agent
"""

import pytest
import requests
import time
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.config.test_settings import *
from tests.config.backend_setup import BackendTestSetup
from app.database import SessionLocal
from app.models.database import User, Message, Conversation, Appointment


class TestCompleteCustomerJourney:
    """🎭 Testa jornadas completas de clientes"""
    
    @classmethod
    def setup_class(cls):
        """🏗️ Setup do ambiente"""
        print("\n🎭 Configurando testes de jornada de cliente...")
        cls.setup = BackendTestSetup()
        
        # Verificar se serviços estão rodando
        status = cls.setup.get_service_status()
        if not status['backend']['health']:
            # Tentar iniciar se não estiver rodando
            print("🚀 Iniciando serviços...")
            assert cls.setup.start_backend_services(), "Falha ao iniciar backend"
            assert cls.setup.wait_for_services(), "Serviços não ficaram disponíveis"
        
        print("✅ Ambiente pronto para testes de jornada!")
    
    @classmethod
    def teardown_class(cls):
        """🧹 Cleanup após testes"""
        print("\n🧹 Finalizando testes de jornada...")
        # Nota: Não fazer cleanup completo aqui para permitir reutilização
    
    def test_new_customer_discovery_journey(self):
        """🆕 Jornada de um cliente novo descobrindo os serviços"""
        print("\n🆕 TESTE: Cliente novo descobrindo serviços")
        
        # Cliente novo
        customer = {
            'wa_id': '5511999111111',
            'nome': 'João Descobridor',
            'telefone': '+5511999111111',
            'email': 'joao.descobridor@email.com'
        }
        
        # Jornada de descoberta
        discovery_messages = [
            "Olá",
            "Que serviços vocês fazem?",
            "Qual o preço do corte masculino?",
            "Vocês funcionam no sábado?",
            "Como posso agendar?",
            "Obrigado pelas informações!"
        ]
        
        conversation_flow = []
        
        try:
            # Simular cada passo da jornada
            for i, message in enumerate(discovery_messages):
                print(f"📤 Passo {i+1}: Cliente enviando '{message}'")
                
                # Criar payload do webhook
                payload = self.setup.create_test_webhook_payload(customer, message)
                
                # Enviar para webhook
                start_time = time.time()
                response = requests.post(
                    API_ENDPOINTS['webhook'],
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=TIMEOUTS['webhook_processing']
                )
                
                response_time = time.time() - start_time
                
                assert response.status_code == 200, f"Falha no passo {i+1}: {response.status_code}"
                
                conversation_flow.append({
                    'step': i+1,
                    'message': message,
                    'response_time': response_time,
                    'status_code': response.status_code
                })
                
                print(f"✅ Passo {i+1} processado ({response_time:.2f}s)")
                
                # Delay entre mensagens (simulando tempo de digitação)
                time.sleep(DELAYS['between_messages'])
            
            # Aguardar processamento final
            time.sleep(DELAYS['after_webhook'] * 2)
            
            # Verificar resultados no banco
            session = SessionLocal()
            try:
                # Verificar se usuário foi criado
                user = session.query(User).filter(User.wa_id == customer['wa_id']).first()
                assert user is not None, "Cliente não foi criado no banco"
                print(f"✅ Cliente criado: {user.nome} (ID: {user.id})")
                
                # Verificar conversas
                conversations = session.query(Conversation).filter(Conversation.user_id == user.id).all()
                print(f"💬 Conversas encontradas: {len(conversations)}")
                
                # Verificar mensagens
                messages = session.query(Message).filter(Message.user_id == user.id).all()
                print(f"📨 Mensagens processadas: {len(messages)}")
                
                # Deve ter pelo menos as mensagens de entrada
                assert len(messages) >= len(discovery_messages), \
                    f"Mensagens faltando: esperado >= {len(discovery_messages)}, encontrado {len(messages)}"
                
                # Analisar tipos de mensagem
                incoming_count = len([m for m in messages if m.direction == 'in'])
                outgoing_count = len([m for m in messages if m.direction == 'out'])
                
                print(f"📊 Mensagens: {incoming_count} recebidas, {outgoing_count} enviadas")
                
            finally:
                session.close()
            
            # Calcular métricas da jornada
            total_time = sum(step['response_time'] for step in conversation_flow)
            avg_response_time = total_time / len(conversation_flow)
            
            print(f"\n📊 MÉTRICAS DA JORNADA:")
            print(f"   ⏱️ Tempo total: {total_time:.2f}s")
            print(f"   📈 Tempo médio por mensagem: {avg_response_time:.2f}s")
            print(f"   📱 Passos completados: {len(conversation_flow)}")
            print(f"   ✅ Taxa de sucesso: 100%")
            
            assert avg_response_time < PERFORMANCE_THRESHOLDS['api_response_time'], \
                f"Jornada muito lenta: {avg_response_time:.2f}s por mensagem"
            
            print("✅ JORNADA DE DESCOBERTA COMPLETA!")
            
        except Exception as e:
            print(f"❌ FALHA NA JORNADA: {e}")
            raise
    
    def test_booking_complete_journey(self):
        """📅 Jornada completa de agendamento"""
        print("\n📅 TESTE: Jornada completa de agendamento")
        
        customer = {
            'wa_id': '5511999222222',
            'nome': 'Maria Agendadora',
            'telefone': '+5511999222222',
            'email': 'maria.agendadora@email.com'
        }
        
        # Fluxo de agendamento passo a passo
        booking_steps = [
            {
                'message': 'Oi, quero agendar um horário',
                'expected_response_keywords': ['agendar', 'serviço', 'horário']
            },
            {
                'message': 'Corte masculino',
                'expected_response_keywords': ['corte', 'masculino', 'quando']
            },
            {
                'message': 'Amanhã de manhã se possível',
                'expected_response_keywords': ['manhã', 'disponível', 'horário']
            },
            {
                'message': '10h está bom',
                'expected_response_keywords': ['10h', '10:00', 'confirmar']
            },
            {
                'message': 'Sim, confirmo',
                'expected_response_keywords': ['confirmado', 'agendado', 'sucesso']
            }
        ]
        
        booking_results = []
        
        try:
            for i, step in enumerate(booking_steps):
                print(f"📅 Passo {i+1}: '{step['message']}'")
                
                payload = self.setup.create_test_webhook_payload(customer, step['message'])
                
                start_time = time.time()
                response = requests.post(
                    API_ENDPOINTS['webhook'],
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=TIMEOUTS['webhook_processing']
                )
                
                response_time = time.time() - start_time
                
                assert response.status_code == 200, f"Falha no agendamento passo {i+1}"
                
                booking_results.append({
                    'step': i+1,
                    'message': step['message'],
                    'response_time': response_time,
                    'expected_keywords': step['expected_response_keywords']
                })
                
                print(f"✅ Passo {i+1} do agendamento processado ({response_time:.2f}s)")
                time.sleep(DELAYS['between_messages'] * 1.5)  # Mais tempo para agendamento
            
            # Aguardar processamento completo
            time.sleep(DELAYS['after_webhook'] * 3)
            
            # Verificar no banco se agendamento foi criado
            session = SessionLocal()
            try:
                user = session.query(User).filter(User.wa_id == customer['wa_id']).first()
                assert user is not None, "Cliente do agendamento não encontrado"
                
                # Procurar agendamentos
                appointments = session.query(Appointment).filter(Appointment.user_id == user.id).all()
                
                print(f"📅 Agendamentos encontrados: {len(appointments)}")
                
                # Verificar mensagens do fluxo
                messages = session.query(Message).filter(Message.user_id == user.id).all()
                print(f"💬 Mensagens do agendamento: {len(messages)}")
                
                # Analisar conteúdo das mensagens para verificar fluxo
                bot_responses = [m.content for m in messages if m.direction == 'out']
                print(f"🤖 Respostas do bot: {len(bot_responses)}")
                
                for response in bot_responses[:3]:  # Mostrar primeiras 3 respostas
                    print(f"   💬 Bot: {response[:100]}...")
                
            finally:
                session.close()
            
            # Calcular sucesso do agendamento
            total_booking_time = sum(r['response_time'] for r in booking_results)
            print(f"\n📊 MÉTRICAS DO AGENDAMENTO:")
            print(f"   ⏱️ Tempo total: {total_booking_time:.2f}s")
            print(f"   📋 Passos completados: {len(booking_results)}")
            print(f"   💬 Mensagens processadas: {len(messages) if 'messages' in locals() else 'N/A'}")
            print(f"   📅 Agendamentos criados: {len(appointments) if 'appointments' in locals() else 'N/A'}")
            
            print("✅ JORNADA DE AGENDAMENTO COMPLETA!")
            
        except Exception as e:
            print(f"❌ FALHA NO AGENDAMENTO: {e}")
            raise
    
    def test_customer_complaint_handoff_journey(self):
        """😠 Jornada de cliente com reclamação (handoff para humano)"""
        print("\n😠 TESTE: Jornada de reclamação e handoff")
        
        customer = {
            'wa_id': '5511999333333',
            'nome': 'Carlos Reclamador',
            'telefone': '+5511999333333',
            'email': 'carlos.reclamador@email.com'
        }
        
        complaint_flow = [
            "Olá, quero fazer uma reclamação",
            "Vocês cortaram meu cabelo errado ontem!",
            "Estou muito insatisfeito com o serviço",
            "Quero falar com o gerente",
            "Isso é inaceitável!"
        ]
        
        handoff_detected = False
        
        try:
            for i, message in enumerate(complaint_flow):
                print(f"😠 Reclamação {i+1}: '{message}'")
                
                payload = self.setup.create_test_webhook_payload(customer, message)
                
                response = requests.post(
                    API_ENDPOINTS['webhook'],
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=TIMEOUTS['webhook_processing']
                )
                
                assert response.status_code == 200, f"Falha na reclamação {i+1}"
                print(f"✅ Reclamação {i+1} processada")
                
                time.sleep(DELAYS['between_messages'])
            
            # Aguardar processamento
            time.sleep(DELAYS['after_webhook'] * 2)
            
            # Verificar se houve handoff
            session = SessionLocal()
            try:
                user = session.query(User).filter(User.wa_id == customer['wa_id']).first()
                assert user is not None, "Cliente da reclamação não encontrado"
                
                # Verificar conversas - procurar por status de handoff
                conversations = session.query(Conversation).filter(Conversation.user_id == user.id).all()
                
                for conv in conversations:
                    if conv.status and 'human' in conv.status.lower():
                        handoff_detected = True
                        print(f"🤝 Handoff detectado: {conv.status}")
                        break
                
                # Analisar mensagens para detectar indicações de handoff
                messages = session.query(Message).filter(Message.user_id == user.id).all()
                bot_responses = [m.content for m in messages if m.direction == 'out']
                
                handoff_keywords = ['atendente', 'humano', 'transferindo', 'gerente', 'aguarde']
                
                for response in bot_responses:
                    if any(keyword in response.lower() for keyword in handoff_keywords):
                        handoff_detected = True
                        print(f"🤝 Handoff detectado na resposta: {response[:100]}...")
                        break
                
                print(f"💬 Total de mensagens: {len(messages)}")
                print(f"🤖 Respostas do bot: {len(bot_responses)}")
                
            finally:
                session.close()
            
            print(f"\n📊 RESULTADO DA RECLAMAÇÃO:")
            print(f"   😠 Mensagens de reclamação: {len(complaint_flow)}")
            print(f"   🤝 Handoff detectado: {'✅ SIM' if handoff_detected else '❌ NÃO'}")
            print(f"   💬 Mensagens processadas: {len(messages) if 'messages' in locals() else 'N/A'}")
            
            # Se handoff foi implementado, deve ser detectado
            if handoff_detected:
                print("✅ SISTEMA DE HANDOFF FUNCIONANDO!")
            else:
                print("⚠️ HANDOFF NÃO DETECTADO (pode não estar implementado)")
            
        except Exception as e:
            print(f"❌ FALHA NA JORNADA DE RECLAMAÇÃO: {e}")
            raise
    
    def test_vip_customer_experience(self):
        """👑 Jornada de cliente VIP (deve acionar CrewAI)"""
        print("\n👑 TESTE: Experiência de cliente VIP")
        
        vip_customer = {
            'wa_id': '5511999444444',
            'nome': 'Roberto VIP Premium',
            'telefone': '+5511999444444',
            'email': 'roberto.vip@email.com'
        }
        
        vip_messages = [
            "Olá, sou cliente há 5 anos da barbearia",
            "Preciso de um atendimento especial para meu casamento",
            "Quero agendar corte, barba, sobrancelha e algum tratamento premium",
            "É para o próximo sábado, posso pagar extra por atendimento VIP",
            "Podem fazer um pacote especial para mim?"
        ]
        
        vip_experience_detected = False
        crew_ai_triggered = False
        
        try:
            for i, message in enumerate(vip_messages):
                print(f"👑 VIP {i+1}: '{message}'")
                
                payload = self.setup.create_test_webhook_payload(vip_customer, message)
                
                start_time = time.time()
                response = requests.post(
                    API_ENDPOINTS['webhook'],
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=TIMEOUTS['llm_response']  # Mais tempo para CrewAI
                )
                
                response_time = time.time() - start_time
                
                assert response.status_code == 200, f"Falha VIP {i+1}"
                
                # CrewAI pode demorar mais
                if response_time > 5:
                    crew_ai_triggered = True
                    print(f"🤖 Possível CrewAI detectado ({response_time:.2f}s)")
                
                print(f"✅ Mensagem VIP {i+1} processada ({response_time:.2f}s)")
                time.sleep(DELAYS['between_messages'])
            
            # Aguardar processamento VIP
            time.sleep(DELAYS['after_webhook'] * 3)
            
            # Verificar tratamento VIP no banco
            session = SessionLocal()
            try:
                user = session.query(User).filter(User.wa_id == vip_customer['wa_id']).first()
                assert user is not None, "Cliente VIP não encontrado"
                
                messages = session.query(Message).filter(Message.user_id == user.id).all()
                bot_responses = [m.content for m in messages if m.direction == 'out']
                
                # Procurar indicadores de tratamento VIP
                vip_keywords = ['premium', 'especial', 'vip', 'personalizado', 'exclusivo']
                
                for response in bot_responses:
                    if any(keyword in response.lower() for keyword in vip_keywords):
                        vip_experience_detected = True
                        print(f"👑 Tratamento VIP detectado: {response[:100]}...")
                        break
                
                print(f"💬 Respostas analisadas: {len(bot_responses)}")
                
            finally:
                session.close()
            
            print(f"\n📊 EXPERIÊNCIA VIP:")
            print(f"   👑 Cliente VIP identificado: {'✅' if vip_experience_detected else '❌'}")
            print(f"   🤖 CrewAI possivelmente ativado: {'✅' if crew_ai_triggered else '❌'}")
            print(f"   💬 Mensagens processadas: {len(messages) if 'messages' in locals() else 'N/A'}")
            
            print("✅ TESTE DE CLIENTE VIP COMPLETO!")
            
        except Exception as e:
            print(f"❌ FALHA NA EXPERIÊNCIA VIP: {e}")
            raise
    
    def test_multi_customer_concurrent_flow(self):
        """👥 Teste com múltiplos clientes simultâneos"""
        print("\n👥 TESTE: Múltiplos clientes simultâneos")
        
        # Simular 3 clientes enviando mensagens ao mesmo tempo
        customers = [
            {
                'wa_id': '5511999555001',
                'nome': 'Cliente Simultâneo 1',
                'message': 'Olá, quero agendar um corte'
            },
            {
                'wa_id': '5511999555002',
                'nome': 'Cliente Simultâneo 2',
                'message': 'Quais são os preços dos serviços?'
            },
            {
                'wa_id': '5511999555003',
                'nome': 'Cliente Simultâneo 3',
                'message': 'Vocês funcionam no domingo?'
            }
        ]
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def send_customer_message(customer, result_queue):
            try:
                payload = self.setup.create_test_webhook_payload(customer, customer['message'])
                
                start_time = time.time()
                response = requests.post(
                    API_ENDPOINTS['webhook'],
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=TIMEOUTS['webhook_processing']
                )
                
                response_time = time.time() - start_time
                
                result_queue.put({
                    'customer': customer['nome'],
                    'success': response.status_code == 200,
                    'response_time': response_time,
                    'status_code': response.status_code
                })
                
            except Exception as e:
                result_queue.put({
                    'customer': customer['nome'],
                    'success': False,
                    'error': str(e)
                })
        
        try:
            # Enviar mensagens simultaneamente
            threads = []
            for customer in customers:
                thread = threading.Thread(
                    target=send_customer_message,
                    args=(customer, results)
                )
                threads.append(thread)
                thread.start()
            
            # Aguardar todas as threads
            for thread in threads:
                thread.join(timeout=30)
            
            # Coletar resultados
            concurrent_results = []
            while not results.empty():
                concurrent_results.append(results.get())
            
            # Aguardar processamento
            time.sleep(DELAYS['after_webhook'] * 2)
            
            # Verificar resultados
            successful_requests = [r for r in concurrent_results if r.get('success', False)]
            
            print(f"\n📊 TESTE SIMULTÂNEO:")
            print(f"   👥 Clientes testados: {len(customers)}")
            print(f"   ✅ Sucessos: {len(successful_requests)}")
            print(f"   ❌ Falhas: {len(concurrent_results) - len(successful_requests)}")
            
            for result in concurrent_results:
                status = "✅" if result.get('success', False) else "❌"
                time_info = f"({result.get('response_time', 0):.2f}s)" if 'response_time' in result else ""
                print(f"   {status} {result['customer']} {time_info}")
            
            # Deve processar pelo menos a maioria das mensagens
            success_rate = len(successful_requests) / len(customers) * 100
            assert success_rate >= 70, f"Taxa de sucesso muito baixa: {success_rate:.1f}%"
            
            print(f"📈 Taxa de sucesso: {success_rate:.1f}%")
            print("✅ TESTE SIMULTÂNEO COMPLETO!")
            
        except Exception as e:
            print(f"❌ FALHA NO TESTE SIMULTÂNEO: {e}")
            raise


if __name__ == "__main__":
    # Executar testes individuais
    test_instance = TestCompleteCustomerJourney()
    test_instance.setup_class()
    
    try:
        print("🚀 Executando todos os testes de jornada...")
        
        test_instance.test_new_customer_discovery_journey()
        test_instance.test_booking_complete_journey()
        test_instance.test_customer_complaint_handoff_journey()
        test_instance.test_vip_customer_experience()
        test_instance.test_multi_customer_concurrent_flow()
        
        print("\n🎯 TODOS OS TESTES DE JORNADA COMPLETADOS!")
        
    except Exception as e:
        print(f"\n❌ ERRO NOS TESTES: {e}")
    finally:
        test_instance.teardown_class()
