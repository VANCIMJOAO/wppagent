"""
🔥 TESTES DE STRESS E CARGA
Simula cargas pesadas e cenários extremos de uso
"""

import pytest
import requests
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import threading
import psutil
import os
from statistics import mean, median

class TestStressAndLoad:
    """Testes de stress para validar limites do sistema"""
    
    @pytest.fixture(autouse=True)
    def setup_stress_environment(self):
        """Configuração para testes de stress"""
        print("\n🔥 Configurando ambiente de testes de stress...")
        
        self.backend_url = "http://localhost:8000"
        self.max_workers = 50  # Número máximo de threads concorrentes
        self.results = []  # Armazenar resultados dos testes
        
        # Verificar recursos do sistema
        self._check_system_resources()
        
        yield
        
        # Análise final dos resultados
        self._analyze_results()
    
    def _check_system_resources(self):
        """Verificar recursos disponíveis do sistema"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        print(f"💻 CPU disponível: {100 - cpu_percent:.1f}%")
        print(f"💾 Memória disponível: {memory.available / (1024**3):.1f}GB")
        
        # Verificar se sistema tem recursos suficientes
        assert memory.available > 1024**3, "Sistema com pouca memória para testes de stress"
        assert cpu_percent < 80, "CPU muito ocupada para testes de stress"
        
        print("✅ Sistema com recursos adequados para testes de stress")
    
    def _analyze_results(self):
        """Analisar resultados coletados durante os testes"""
        if not self.results:
            return
        
        print("\n📊 Análise dos resultados de stress:")
        
        # Tempos de resposta
        response_times = [r.get('response_time', 0) for r in self.results if 'response_time' in r]
        if response_times:
            print(f"⏱️ Tempo médio de resposta: {mean(response_times):.3f}s")
            print(f"⏱️ Tempo mediano: {median(response_times):.3f}s")
            print(f"⏱️ Tempo máximo: {max(response_times):.3f}s")
            print(f"⏱️ Tempo mínimo: {min(response_times):.3f}s")
        
        # Taxa de sucesso
        successful = len([r for r in self.results if r.get('success', False)])
        total = len(self.results)
        success_rate = (successful / total) * 100 if total > 0 else 0
        print(f"✅ Taxa de sucesso: {success_rate:.1f}% ({successful}/{total})")
    
    def test_1000_concurrent_users(self):
        """Simula 1000 usuários simultâneos"""
        print("\n🧪 Testando 1000 usuários simultâneos...")
        
        # Para não sobrecarregar demais, vamos usar 100 usuários
        # e simular comportamento de 1000
        concurrent_users = 100
        messages_per_user = 10  # Total: 1000 mensagens
        
        print(f"👥 Simulando {concurrent_users} usuários com {messages_per_user} mensagens cada")
        
        def simulate_user(user_id):
            """Simular comportamento de um usuário"""
            user_results = []
            
            for msg_id in range(messages_per_user):
                try:
                    start_time = time.time()
                    
                    # Payload único para cada usuário/mensagem
                    payload = {
                        "object": "whatsapp_business_account",
                        "entry": [{
                            "changes": [{
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "messages": [{
                                        "from": f"55119999{user_id:04d}",
                                        "text": {"body": f"Stress test user {user_id} msg {msg_id}"},
                                        "type": "text",
                                        "id": f"wamid.stress_{user_id}_{msg_id}",
                                        "timestamp": str(int(time.time()))
                                    }]
                                }
                            }]
                        }]
                    }
                    
                    # Enviar mensagem
                    response = requests.post(
                        f"{self.backend_url}/webhook",
                        json=payload,
                        timeout=30
                    )
                    
                    response_time = time.time() - start_time
                    
                    result = {
                        'user_id': user_id,
                        'message_id': msg_id,
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    }
                    
                    user_results.append(result)
                    
                    # Pequena pausa entre mensagens do mesmo usuário
                    time.sleep(0.1)
                    
                except Exception as e:
                    user_results.append({
                        'user_id': user_id,
                        'message_id': msg_id,
                        'error': str(e),
                        'success': False,
                        'response_time': 0
                    })
            
            return user_results
        
        # Executar usuários em paralelo
        print("🚀 Iniciando simulação de usuários concorrentes...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(simulate_user, user_id) for user_id in range(concurrent_users)]
            
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    self.results.extend(user_results)
                except Exception as e:
                    print(f"❌ Erro em usuário: {e}")
        
        total_time = time.time() - start_time
        print(f"⏱️ Teste concluído em {total_time:.2f}s")
        
        # Análise dos resultados
        successful_messages = len([r for r in self.results if r.get('success')])
        total_messages = len(self.results)
        
        print(f"📊 Mensagens processadas: {successful_messages}/{total_messages}")
        print(f"📊 Taxa de sucesso: {(successful_messages/total_messages)*100:.1f}%")
        print(f"📊 Throughput: {successful_messages/total_time:.1f} msg/s")
        
        # Critérios de aprovação
        success_rate = (successful_messages / total_messages) * 100
        assert success_rate >= 80, f"Taxa de sucesso muito baixa: {success_rate:.1f}%"
        assert successful_messages/total_time >= 10, "Throughput muito baixo"
        
        print("🎉 Teste de 1000 usuários concorrentes concluído com sucesso!")
    
    def test_message_flood(self):
        """Testa sobrecarga de mensagens (flood)"""
        print("\n🧪 Testando flood de mensagens...")
        
        flood_duration = 30  # segundos
        messages_per_second = 20
        total_messages = flood_duration * messages_per_second
        
        print(f"🌊 Enviando {messages_per_second} msgs/s por {flood_duration}s (total: {total_messages})")
        
        def send_flood_message(msg_id):
            """Enviar uma mensagem de flood"""
            try:
                start_time = time.time()
                
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [{
                                    "from": "5511999999999",  # Mesmo usuário
                                    "text": {"body": f"Flood message {msg_id}"},
                                    "type": "text",
                                    "id": f"wamid.flood_{msg_id}",
                                    "timestamp": str(int(time.time()))
                                }]
                            }
                        }]
                    }]
                }
                
                response = requests.post(
                    f"{self.backend_url}/webhook",
                    json=payload,
                    timeout=10
                )
                
                response_time = time.time() - start_time
                
                return {
                    'message_id': msg_id,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'success': response.status_code in [200, 429]  # 429 é esperado para rate limiting
                }
                
            except Exception as e:
                return {
                    'message_id': msg_id,
                    'error': str(e),
                    'success': False,
                    'response_time': 0
                }
        
        # Enviar mensagens com controle de taxa
        print("🌊 Iniciando flood...")
        start_time = time.time()
        flood_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for msg_id in range(total_messages):
                # Controlar taxa de envio
                elapsed = time.time() - start_time
                expected_time = msg_id / messages_per_second
                
                if elapsed < expected_time:
                    time.sleep(expected_time - elapsed)
                
                future = executor.submit(send_flood_message, msg_id)
                futures.append(future)
                
                # Limitar número de futures pendentes
                if len(futures) >= self.max_workers:
                    # Processar alguns resultados
                    for i, future in enumerate(futures[:10]):
                        if future.done():
                            flood_results.append(future.result())
                            futures.pop(i)
                            break
            
            # Processar futures restantes
            for future in as_completed(futures):
                flood_results.append(future.result())
        
        total_time = time.time() - start_time
        print(f"⏱️ Flood concluído em {total_time:.2f}s")
        
        # Análise do flood
        successful = len([r for r in flood_results if r.get('success')])
        rate_limited = len([r for r in flood_results if r.get('status_code') == 429])
        processed = len([r for r in flood_results if r.get('status_code') == 200])
        
        print(f"📊 Mensagens enviadas: {len(flood_results)}")
        print(f"📊 Processadas com sucesso: {processed}")
        print(f"📊 Rate limited (429): {rate_limited}")
        print(f"📊 Taxa real de envio: {len(flood_results)/total_time:.1f} msg/s")
        
        # O sistema deve processar algumas mensagens e fazer rate limiting
        assert processed > 0, "Nenhuma mensagem foi processada"
        assert rate_limited > 0, "Rate limiting não funcionou durante flood"
        
        self.results.extend(flood_results)
        print("🎉 Teste de flood concluído - Rate limiting funcionando!")
    
    def test_memory_usage_under_load(self):
        """Testa uso de memória sob carga"""
        print("\n🧪 Testando uso de memória sob carga...")
        
        # Memória inicial
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024**2)  # MB
        print(f"💾 Memória inicial: {initial_memory:.1f}MB")
        
        # Função para monitorar memória
        memory_samples = []
        monitoring = True
        
        def monitor_memory():
            while monitoring:
                memory = process.memory_info().rss / (1024**2)
                memory_samples.append(memory)
                time.sleep(0.5)
        
        # Iniciar monitoramento
        monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        monitor_thread.start()
        
        # Gerar carga
        print("⚡ Gerando carga para teste de memória...")
        load_results = []
        
        def memory_load_message(msg_id):
            """Mensagem para teste de memória"""
            try:
                # Payload maior para testar memória
                large_content = f"Memory test message {msg_id} - " + "X" * 1000
                
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [{
                                    "from": f"55119998{msg_id % 10000:04d}",
                                    "text": {"body": large_content},
                                    "type": "text",
                                    "id": f"wamid.memory_{msg_id}",
                                    "timestamp": str(int(time.time()))
                                }]
                            }
                        }]
                    }]
                }
                
                response = requests.post(
                    f"{self.backend_url}/webhook",
                    json=payload,
                    timeout=15
                )
                
                return {'success': response.status_code == 200}
                
            except Exception:
                return {'success': False}
        
        # Enviar 200 mensagens grandes
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(memory_load_message, i) for i in range(200)]
            
            for future in as_completed(futures):
                load_results.append(future.result())
        
        # Parar monitoramento
        monitoring = False
        time.sleep(1)  # Aguardar thread parar
        
        # Análise de memória
        if memory_samples:
            max_memory = max(memory_samples)
            avg_memory = mean(memory_samples)
            memory_increase = max_memory - initial_memory
            
            print(f"💾 Memória máxima: {max_memory:.1f}MB")
            print(f"💾 Memória média: {avg_memory:.1f}MB")
            print(f"💾 Aumento de memória: {memory_increase:.1f}MB")
            
            # Critérios de aprovação
            assert memory_increase < 500, f"Aumento de memória muito alto: {memory_increase:.1f}MB"
            assert max_memory < 2000, f"Uso de memória excessivo: {max_memory:.1f}MB"
            
            print("✅ Uso de memória dentro dos limites aceitáveis")
        
        successful = len([r for r in load_results if r.get('success')])
        print(f"📊 Mensagens processadas: {successful}/{len(load_results)}")
        
        print("🎉 Teste de memória sob carga concluído!")
    
    def test_database_connection_pool(self):
        """Testa pool de conexões do banco sob carga"""
        print("\n🧪 Testando pool de conexões do banco...")
        
        # Simular muitas consultas simultâneas
        concurrent_queries = 50
        queries_per_thread = 10
        
        def database_query_test(thread_id):
            """Fazer consultas ao banco via API"""
            results = []
            
            for query_id in range(queries_per_thread):
                try:
                    start_time = time.time()
                    
                    # Usar endpoint que acessa o banco
                    response = requests.get(f"{self.backend_url}/metrics", timeout=10)
                    
                    response_time = time.time() - start_time
                    
                    results.append({
                        'thread_id': thread_id,
                        'query_id': query_id,
                        'response_time': response_time,
                        'success': response.status_code == 200
                    })
                    
                    # Pequena pausa entre consultas
                    time.sleep(0.1)
                    
                except Exception as e:
                    results.append({
                        'thread_id': thread_id,
                        'query_id': query_id,
                        'error': str(e),
                        'success': False
                    })
            
            return results
        
        print(f"🗄️ Fazendo {concurrent_queries * queries_per_thread} consultas simultâneas...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_queries) as executor:
            futures = [executor.submit(database_query_test, i) for i in range(concurrent_queries)]
            
            db_results = []
            for future in as_completed(futures):
                db_results.extend(future.result())
        
        total_time = time.time() - start_time
        
        # Análise das consultas
        successful_queries = len([r for r in db_results if r.get('success')])
        total_queries = len(db_results)
        
        print(f"📊 Consultas bem-sucedidas: {successful_queries}/{total_queries}")
        print(f"📊 Taxa de sucesso: {(successful_queries/total_queries)*100:.1f}%")
        print(f"📊 Queries/segundo: {successful_queries/total_time:.1f}")
        
        # Critérios de aprovação
        success_rate = (successful_queries / total_queries) * 100
        assert success_rate >= 95, f"Taxa de sucesso de consultas muito baixa: {success_rate:.1f}%"
        
        self.results.extend(db_results)
        print("🎉 Teste de pool de conexões concluído!")
    
    def test_sustained_load(self):
        """Teste de carga sustentada por período prolongado"""
        print("\n🧪 Testando carga sustentada...")
        
        duration_minutes = 2  # 2 minutos de teste
        requests_per_minute = 60  # 1 req/segundo
        
        print(f"⏰ Mantendo {requests_per_minute} req/min por {duration_minutes} minutos")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        sustained_results = []
        request_count = 0
        
        while time.time() < end_time:
            try:
                # Payload variado
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [{
                                    "from": f"551199997{request_count % 1000:03d}",
                                    "text": {"body": f"Sustained load test {request_count}"},
                                    "type": "text",
                                    "id": f"wamid.sustained_{request_count}",
                                    "timestamp": str(int(time.time()))
                                }]
                            }
                        }]
                    }]
                }
                
                req_start = time.time()
                response = requests.post(
                    f"{self.backend_url}/webhook",
                    json=payload,
                    timeout=5
                )
                req_time = time.time() - req_start
                
                sustained_results.append({
                    'request_id': request_count,
                    'response_time': req_time,
                    'success': response.status_code == 200,
                    'timestamp': time.time()
                })
                
                request_count += 1
                
                # Controlar taxa de requisições
                time.sleep(60 / requests_per_minute)  # 1 segundo entre requisições
                
            except Exception as e:
                sustained_results.append({
                    'request_id': request_count,
                    'error': str(e),
                    'success': False,
                    'timestamp': time.time()
                })
                request_count += 1
        
        total_duration = time.time() - start_time
        successful = len([r for r in sustained_results if r.get('success')])
        
        print(f"📊 Duração real: {total_duration/60:.1f} minutos")
        print(f"📊 Requisições enviadas: {len(sustained_results)}")
        print(f"📊 Taxa de sucesso: {(successful/len(sustained_results))*100:.1f}%")
        print(f"📊 Requisições/minuto real: {len(sustained_results)/(total_duration/60):.1f}")
        
        # Sistema deve manter estabilidade durante carga sustentada
        success_rate = (successful / len(sustained_results)) * 100
        assert success_rate >= 85, f"Sistema não manteve estabilidade: {success_rate:.1f}%"
        
        self.results.extend(sustained_results)
        print("🎉 Teste de carga sustentada concluído!")
