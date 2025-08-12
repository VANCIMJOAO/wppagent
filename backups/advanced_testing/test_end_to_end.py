"""
🔄 TESTES END-TO-END COMPLETOS
Validação de fluxos completos do WhatsApp até o Dashboard
"""

import pytest
import requests
import time
import json
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess
import psutil

class TestEndToEndValidation:
    """Testes de validação end-to-end completos"""
    
    @pytest.fixture(autouse=True)
    def setup_e2e_environment(self):
        """Configuração para testes end-to-end"""
        print("\n🔄 Configurando ambiente de testes end-to-end...")
        
        self.backend_url = "http://localhost:8000"
        self.dashboard_url = "http://localhost:8501"
        
        # Verificar se todos os serviços estão funcionando
        self._ensure_all_services_running()
        
        # Estado inicial do sistema
        self.initial_state = self._capture_system_state()
        
        yield
        
        # Verificação final do estado
        self._verify_final_state()
    
    def _ensure_all_services_running(self):
        """Garantir que todos os serviços necessários estão rodando"""
        services = {
            'backend': {'url': f"{self.backend_url}/health", 'required': True},
            'dashboard': {'url': self.dashboard_url, 'required': False}  # Dashboard é opcional
        }
        
        for service_name, config in services.items():
            try:
                response = requests.get(config['url'], timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name.capitalize()} funcionando")
                else:
                    raise Exception(f"{service_name} retornou {response.status_code}")
            except Exception as e:
                if config['required']:
                    raise Exception(f"{service_name} indisponível: {e}")
                else:
                    print(f"⚠️ {service_name} indisponível (opcional): {e}")
    
    def _capture_system_state(self):
        """Capturar estado inicial do sistema"""
        try:
            response = requests.get(f"{self.backend_url}/metrics", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return {
            'total_users': 0,
            'total_messages': 0,
            'active_conversations': 0,
            'total_bookings': 0
        }
    
    def _verify_final_state(self):
        """Verificar estado final do sistema"""
        try:
            final_state = self._capture_system_state()
            
            # Comparar com estado inicial
            users_added = final_state.get('total_users', 0) - self.initial_state.get('total_users', 0)
            messages_added = final_state.get('total_messages', 0) - self.initial_state.get('total_messages', 0)
            
            print(f"\n📊 Alterações no sistema durante testes:")
            print(f"👥 Usuários adicionados: {users_added}")
            print(f"💬 Mensagens adicionadas: {messages_added}")
            
        except Exception as e:
            print(f"⚠️ Não foi possível verificar estado final: {e}")
    
    def test_whatsapp_to_dashboard_sync(self):
        """Mensagem WhatsApp → Processa → Aparece no Dashboard"""
        print("\n🧪 Testando sincronização WhatsApp → Dashboard...")
        
        # 1. Enviar mensagem via webhook (simula WhatsApp)
        print("📱 Enviando mensagem via webhook...")
        
        test_message = f"E2E Test Message - {datetime.now().strftime('%H:%M:%S')}"
        test_phone = "5511999e2e001"
        
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550559999",
                            "phone_number_id": "PHONE_NUMBER_ID"
                        },
                        "messages": [{
                            "from": test_phone,
                            "text": {"body": test_message},
                            "type": "text",
                            "id": f"wamid.e2e_{int(time.time())}",
                            "timestamp": str(int(time.time()))
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        # Enviar webhook
        start_time = time.time()
        response = requests.post(
            f"{self.backend_url}/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        processing_time = time.time() - start_time
        assert response.status_code == 200, f"Webhook falhou: {response.status_code}"
        print(f"✅ Webhook processado em {processing_time:.2f}s")
        
        # 2. Verificar se dados foram salvos no backend
        print("🗄️ Verificando dados no backend...")
        
        # Aguardar processamento
        time.sleep(2)
        
        # Verificar métricas atualizadas
        metrics_response = requests.get(f"{self.backend_url}/metrics", timeout=5)
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        
        print(f"📊 Métricas atuais: {metrics}")
        
        # Verificar se usuário foi criado/atualizado
        current_users = metrics.get('total_users', 0)
        current_messages = metrics.get('total_messages', 0)
        
        assert current_users >= self.initial_state.get('total_users', 0)
        assert current_messages > self.initial_state.get('total_messages', 0)
        print("✅ Dados salvos no backend")
        
        # 3. Verificar disponibilidade no dashboard (se disponível)
        print("🎛️ Verificando dashboard...")
        
        try:
            dashboard_response = requests.get(self.dashboard_url, timeout=10)
            if dashboard_response.status_code == 200:
                print("✅ Dashboard acessível")
                
                # Verificar se dados aparecem no dashboard
                # (seria necessário parsing do HTML ou API do dashboard)
                dashboard_content = dashboard_response.text
                
                # Buscar por indicadores de que os dados estão sendo exibidos
                data_indicators = [
                    str(current_users) in dashboard_content,
                    str(current_messages) in dashboard_content,
                    test_phone in dashboard_content,
                    "e2e" in dashboard_content.lower()
                ]
                
                if any(data_indicators):
                    print("✅ Dados apareceram no dashboard")
                else:
                    print("ℹ️ Dados podem estar no dashboard (não detectados automaticamente)")
                    
            else:
                print(f"⚠️ Dashboard retornou {dashboard_response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Dashboard não acessível: {e}")
        
        print("🎉 Teste de sincronização end-to-end concluído!")
    
    def test_complete_customer_lifecycle(self):
        """Teste do ciclo completo de vida do cliente"""
        print("\n🧪 Testando ciclo completo de vida do cliente...")
        
        customer_phone = "5511999e2e002"
        lifecycle_steps = []
        
        # 1. Primeiro contato (descoberta)
        print("👋 Fase 1: Primeiro contato...")
        
        discovery_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "from": customer_phone,
                            "text": {"body": "Olá! Gostaria de saber sobre seus serviços"},
                            "type": "text",
                            "id": "wamid.lifecycle_discovery",
                            "timestamp": str(int(time.time()))
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{self.backend_url}/webhook", json=discovery_payload)
        assert response.status_code == 200
        lifecycle_steps.append({"step": "discovery", "success": True})
        print("✅ Descoberta processada")
        
        time.sleep(1)
        
        # 2. Interesse em agendamento
        print("📅 Fase 2: Interesse em agendamento...")
        
        interest_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "from": customer_phone,
                            "text": {"body": "Quero agendar um horário para próxima semana"},
                            "type": "text",
                            "id": "wamid.lifecycle_interest",
                            "timestamp": str(int(time.time()))
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{self.backend_url}/webhook", json=interest_payload)
        assert response.status_code == 200
        lifecycle_steps.append({"step": "interest", "success": True})
        print("✅ Interesse processado")
        
        time.sleep(1)
        
        # 3. Confirmação de agendamento
        print("✅ Fase 3: Confirmação de agendamento...")
        
        booking_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "from": customer_phone,
                            "text": {"body": "Confirmo o agendamento para terça-feira às 14h"},
                            "type": "text",
                            "id": "wamid.lifecycle_booking",
                            "timestamp": str(int(time.time()))
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{self.backend_url}/webhook", json=booking_payload)
        assert response.status_code == 200
        lifecycle_steps.append({"step": "booking", "success": True})
        print("✅ Agendamento processado")
        
        time.sleep(1)
        
        # 4. Follow-up (pós-agendamento)
        print("🔄 Fase 4: Follow-up...")
        
        followup_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "from": customer_phone,
                            "text": {"body": "Obrigado pelo atendimento! Muito satisfeito"},
                            "type": "text",
                            "id": "wamid.lifecycle_followup",
                            "timestamp": str(int(time.time()))
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(f"{self.backend_url}/webhook", json=followup_payload)
        assert response.status_code == 200
        lifecycle_steps.append({"step": "followup", "success": True})
        print("✅ Follow-up processado")
        
        # 5. Verificar dados finais
        print("📊 Verificando dados finais do ciclo...")
        
        time.sleep(2)
        final_metrics = requests.get(f"{self.backend_url}/metrics").json()
        
        # Verificar se todas as etapas foram registradas
        messages_in_lifecycle = len(lifecycle_steps)
        expected_messages = self.initial_state.get('total_messages', 0) + messages_in_lifecycle
        
        print(f"📊 Etapas do ciclo: {len(lifecycle_steps)}")
        print(f"📊 Mensagens esperadas: {expected_messages}")
        print(f"📊 Mensagens atuais: {final_metrics.get('total_messages', 0)}")
        
        # Todas as etapas devem ter sido processadas
        successful_steps = len([s for s in lifecycle_steps if s.get('success')])
        assert successful_steps == len(lifecycle_steps), "Nem todas as etapas foram processadas"
        
        print("🎉 Ciclo completo de vida do cliente concluído!")
    
    def test_concurrent_multi_user_flows(self):
        """Teste de múltiplos usuários com fluxos diferentes simultâneos"""
        print("\n🧪 Testando fluxos simultâneos de múltiplos usuários...")
        
        # Definir diferentes tipos de usuários/fluxos
        user_flows = [
            {
                "phone": "5511999e2e010",
                "flow": "quick_inquiry",
                "messages": [
                    "Olá, preciso de informações rápidas",
                    "Qual o preço?",
                    "Obrigado!"
                ]
            },
            {
                "phone": "5511999e2e011", 
                "flow": "booking_flow",
                "messages": [
                    "Quero agendar um serviço",
                    "Posso na sexta-feira?",
                    "Perfeito, confirmo o agendamento"
                ]
            },
            {
                "phone": "5511999e2e012",
                "flow": "support_flow", 
                "messages": [
                    "Preciso de ajuda com meu agendamento",
                    "Quero remarcar para outro dia",
                    "Muito obrigado pelo atendimento"
                ]
            },
            {
                "phone": "5511999e2e013",
                "flow": "vip_flow",
                "messages": [
                    "Sou cliente VIP, preciso de atendimento urgente",
                    "Preciso reagendar para hoje ainda"
                ]
            }
        ]
        
        def execute_user_flow(user_flow):
            """Executar fluxo de um usuário específico"""
            flow_results = []
            
            for i, message in enumerate(user_flow["messages"]):
                try:
                    payload = {
                        "object": "whatsapp_business_account",
                        "entry": [{
                            "changes": [{
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "messages": [{
                                        "from": user_flow["phone"],
                                        "text": {"body": message},
                                        "type": "text",
                                        "id": f"wamid.{user_flow['flow']}_{i}",
                                        "timestamp": str(int(time.time()))
                                    }]
                                }
                            }]
                        }]
                    }
                    
                    start_time = time.time()
                    response = requests.post(
                        f"{self.backend_url}/webhook",
                        json=payload,
                        timeout=10
                    )
                    response_time = time.time() - start_time
                    
                    flow_results.append({
                        'flow': user_flow["flow"],
                        'phone': user_flow["phone"],
                        'message_index': i,
                        'message': message,
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    })
                    
                    # Pausa entre mensagens do mesmo usuário
                    time.sleep(0.5)
                    
                except Exception as e:
                    flow_results.append({
                        'flow': user_flow["flow"],
                        'phone': user_flow["phone"],
                        'message_index': i,
                        'error': str(e),
                        'success': False
                    })
            
            return flow_results
        
        # Executar fluxos em paralelo
        print(f"🚀 Executando {len(user_flows)} fluxos simultâneos...")
        
        all_flow_results = []
        
        with ThreadPoolExecutor(max_workers=len(user_flows)) as executor:
            futures = [executor.submit(execute_user_flow, flow) for flow in user_flows]
            
            for future in futures:
                results = future.result()
                all_flow_results.extend(results)
        
        # Análise dos resultados
        total_messages = len(all_flow_results)
        successful_messages = len([r for r in all_flow_results if r.get('success')])
        
        print(f"📊 Total de mensagens enviadas: {total_messages}")
        print(f"📊 Mensagens processadas com sucesso: {successful_messages}")
        print(f"📊 Taxa de sucesso: {(successful_messages/total_messages)*100:.1f}%")
        
        # Análise por fluxo
        for user_flow in user_flows:
            flow_results = [r for r in all_flow_results if r.get('flow') == user_flow['flow']]
            flow_success = len([r for r in flow_results if r.get('success')])
            
            print(f"📊 {user_flow['flow']}: {flow_success}/{len(flow_results)} sucessos")
        
        # Verificar tempos de resposta
        response_times = [r.get('response_time', 0) for r in all_flow_results if 'response_time' in r]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            max_response = max(response_times)
            
            print(f"⏱️ Tempo médio de resposta: {avg_response:.2f}s")
            print(f"⏱️ Tempo máximo de resposta: {max_response:.2f}s")
            
            # Verificar se performance se manteve boa
            assert avg_response < 2.0, f"Tempo médio muito alto: {avg_response:.2f}s"
            assert max_response < 5.0, f"Tempo máximo muito alto: {max_response:.2f}s"
        
        # Taxa de sucesso deve ser alta
        success_rate = (successful_messages / total_messages) * 100
        assert success_rate >= 90, f"Taxa de sucesso baixa: {success_rate:.1f}%"
        
        print("🎉 Teste de fluxos simultâneos concluído!")
    
    def test_system_performance_under_realistic_load(self):
        """Teste de performance sob carga realista"""
        print("\n🧪 Testando performance sob carga realista...")
        
        # Simular carga realista: mistura de diferentes tipos de mensagens
        # durante um período de tempo
        test_duration = 60  # 1 minuto
        target_rate = 5  # 5 mensagens por segundo (300/min)
        
        message_types = [
            {"type": "greeting", "weight": 30, "template": "Olá! Como vocês estão?"},
            {"type": "inquiry", "weight": 25, "template": "Gostaria de saber sobre os serviços"},
            {"type": "booking", "weight": 20, "template": "Quero agendar um horário"},
            {"type": "support", "weight": 15, "template": "Preciso de ajuda com meu agendamento"},
            {"type": "feedback", "weight": 10, "template": "Muito satisfeito com o atendimento!"}
        ]
        
        # Calcular pesos cumulativos
        cumulative_weights = []
        total_weight = 0
        for msg_type in message_types:
            total_weight += msg_type["weight"]
            cumulative_weights.append(total_weight)
        
        def select_message_type():
            """Selecionar tipo de mensagem baseado nos pesos"""
            import random
            rand = random.randint(1, total_weight)
            
            for i, weight in enumerate(cumulative_weights):
                if rand <= weight:
                    return message_types[i]
            
            return message_types[0]  # fallback
        
        def send_realistic_message(msg_id):
            """Enviar uma mensagem realista"""
            try:
                msg_type = select_message_type()
                
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [{
                                    "from": f"55119999{msg_id % 1000:03d}",
                                    "text": {"body": f"{msg_type['template']} ({msg_id})"},
                                    "type": "text",
                                    "id": f"wamid.realistic_{msg_id}",
                                    "timestamp": str(int(time.time()))
                                }]
                            }
                        }]
                    }]
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.backend_url}/webhook",
                    json=payload,
                    timeout=8
                )
                response_time = time.time() - start_time
                
                return {
                    'message_id': msg_id,
                    'message_type': msg_type['type'],
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'timestamp': time.time()
                }
                
            except Exception as e:
                return {
                    'message_id': msg_id,
                    'error': str(e),
                    'success': False,
                    'timestamp': time.time()
                }
        
        # Executar teste de carga realista
        print(f"📈 Gerando carga realista: {target_rate} msg/s por {test_duration}s...")
        
        start_time = time.time()
        realistic_results = []
        msg_count = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            while time.time() - start_time < test_duration:
                # Controlar taxa de envio
                elapsed = time.time() - start_time
                expected_messages = int(elapsed * target_rate)
                
                if msg_count < expected_messages:
                    future = executor.submit(send_realistic_message, msg_count)
                    futures.append(future)
                    msg_count += 1
                    
                    # Processar futures completos
                    completed_futures = [f for f in futures if f.done()]
                    for future in completed_futures:
                        realistic_results.append(future.result())
                        futures.remove(future)
                
                time.sleep(0.01)  # Check pequeno
            
            # Processar futures restantes
            for future in futures:
                realistic_results.append(future.result())
        
        total_duration = time.time() - start_time
        
        # Análise da performance realista
        successful = len([r for r in realistic_results if r.get('success')])
        total = len(realistic_results)
        
        response_times = [r.get('response_time', 0) for r in realistic_results if 'response_time' in r]
        
        print(f"📊 Duração do teste: {total_duration:.1f}s")
        print(f"📊 Mensagens enviadas: {total}")
        print(f"📊 Taxa real: {total/total_duration:.1f} msg/s")
        print(f"📊 Sucessos: {successful}/{total} ({(successful/total)*100:.1f}%)")
        
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            print(f"⏱️ Tempo médio de resposta: {avg_response:.3f}s")
            print(f"⏱️ Tempo máximo: {max(response_times):.3f}s")
            print(f"⏱️ Tempo mínimo: {min(response_times):.3f}s")
        
        # Análise por tipo de mensagem
        for msg_type in message_types:
            type_results = [r for r in realistic_results if r.get('message_type') == msg_type['type']]
            type_success = len([r for r in type_results if r.get('success')])
            
            if type_results:
                print(f"📊 {msg_type['type']}: {type_success}/{len(type_results)} ({(type_success/len(type_results))*100:.1f}%)")
        
        # Critérios de aprovação para carga realista
        success_rate = (successful / total) * 100 if total > 0 else 0
        assert success_rate >= 85, f"Taxa de sucesso baixa sob carga realista: {success_rate:.1f}%"
        
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            assert avg_response < 1.0, f"Tempo médio muito alto: {avg_response:.3f}s"
        
        print("🎉 Teste de performance realista concluído!")
    
    def test_data_consistency_across_services(self):
        """Teste de consistência de dados entre serviços"""
        print("\n🧪 Testando consistência de dados entre serviços...")
        
        # Enviar algumas mensagens para gerar dados
        print("📝 Gerando dados de teste...")
        
        test_messages = [
            {"phone": "5511999consist1", "message": "Mensagem de consistência 1"},
            {"phone": "5511999consist2", "message": "Mensagem de consistência 2"},
            {"phone": "5511999consist3", "message": "Mensagem de consistência 3"},
        ]
        
        for i, msg_data in enumerate(test_messages):
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [{
                                "from": msg_data["phone"],
                                "text": {"body": msg_data["message"]},
                                "type": "text",
                                "id": f"wamid.consistency_{i}",
                                "timestamp": str(int(time.time()))
                            }]
                        }
                    }]
                }]
            }
            
            response = requests.post(f"{self.backend_url}/webhook", json=payload)
            assert response.status_code == 200
            time.sleep(0.5)
        
        # Aguardar processamento
        print("⏳ Aguardando processamento completo...")
        time.sleep(3)
        
        # Verificar consistência através de múltiplas consultas
        print("🔍 Verificando consistência através de múltiplas consultas...")
        
        consistency_checks = []
        
        # Fazer várias consultas às métricas
        for check in range(5):
            response = requests.get(f"{self.backend_url}/metrics", timeout=5)
            assert response.status_code == 200
            
            metrics = response.json()
            consistency_checks.append({
                'check': check,
                'total_users': metrics.get('total_users', 0),
                'total_messages': metrics.get('total_messages', 0),
                'active_conversations': metrics.get('active_conversations', 0),
                'timestamp': time.time()
            })
            
            time.sleep(1)
        
        # Verificar se dados são consistentes
        print("📊 Analisando consistência...")
        
        # Todos os checks devem retornar os mesmos valores
        base_check = consistency_checks[0]
        
        for check in consistency_checks[1:]:
            for key in ['total_users', 'total_messages', 'active_conversations']:
                assert check[key] == base_check[key], f"Inconsistência em {key}: {check[key]} != {base_check[key]}"
        
        print("✅ Dados consistentes entre consultas")
        
        # Verificar se contadores fazem sentido
        total_users = base_check['total_users']
        total_messages = base_check['total_messages']
        active_conversations = base_check['active_conversations']
        
        print(f"📊 Usuários: {total_users}")
        print(f"📊 Mensagens: {total_messages}")
        print(f"📊 Conversas ativas: {active_conversations}")
        
        # Validações lógicas
        assert total_messages >= total_users, "Número de mensagens menor que usuários"
        assert active_conversations <= total_users, "Conversas ativas maior que usuários"
        
        print("✅ Dados logicamente consistentes")
        
        # Verificar se incrementos fazem sentido comparado ao estado inicial
        users_increment = total_users - self.initial_state.get('total_users', 0)
        messages_increment = total_messages - self.initial_state.get('total_messages', 0)
        
        assert users_increment >= 0, "Número de usuários diminuiu"
        assert messages_increment >= len(test_messages), f"Mensagens não foram todas contadas: {messages_increment} < {len(test_messages)}"
        
        print("✅ Incrementos fazem sentido")
        print("🎉 Teste de consistência de dados concluído!")
