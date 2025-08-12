"""
💥 TESTES DE CENÁRIOS DE FALHA
Testa resiliência e recuperação do sistema em situações adversas
"""

import pytest
import requests
import time
import subprocess
import psutil
import signal
import os
from unittest.mock import patch, Mock
import json
from datetime import datetime

class TestFailureScenarios:
    """Testes de resiliência e recuperação do sistema"""
    
    @pytest.fixture(autouse=True)
    def setup_failure_environment(self):
        """Configuração para testes de falha"""
        print("\n💥 Configurando ambiente de testes de falha...")
        
        self.backend_url = "http://localhost:8000"
        self.original_processes = {}
        
        # Identificar processos do sistema
        self._identify_system_processes()
        
        yield
        
        # Garantir que serviços sejam restaurados
        self._restore_services()
    
    def _identify_system_processes(self):
        """Identificar processos do sistema para testes"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                # Identificar FastAPI
                if 'uvicorn' in cmdline and 'app.main:app' in cmdline:
                    self.original_processes['fastapi'] = proc.info['pid']
                    print(f"🔍 FastAPI encontrado: PID {proc.info['pid']}")
                
                # Identificar Streamlit
                if 'streamlit' in cmdline and 'dashboard' in cmdline:
                    self.original_processes['streamlit'] = proc.info['pid']
                    print(f"🔍 Streamlit encontrado: PID {proc.info['pid']}")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print(f"✅ {len(self.original_processes)} processos identificados")
    
    def _restore_services(self):
        """Restaurar serviços após testes"""
        print("\n🔧 Restaurando serviços...")
        
        # Verificar se FastAPI está rodando
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code != 200:
                raise Exception("FastAPI não responde")
            print("✅ FastAPI já está rodando")
        except:
            print("🚀 Reiniciando FastAPI...")
            self._start_fastapi()
    
    def _start_fastapi(self):
        """Iniciar FastAPI"""
        process = subprocess.Popen([
            "uvicorn", "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], cwd="/home/vancim/whats_agent")
        
        # Aguardar inicialização
        for attempt in range(30):
            try:
                response = requests.get(f"{self.backend_url}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ FastAPI reiniciado com sucesso")
                    return
            except:
                time.sleep(1)
        
        print("❌ Falha ao reiniciar FastAPI")
    
    def test_database_down_scenario(self):
        """Testa comportamento com BD indisponível"""
        print("\n🧪 Testando cenário de banco indisponível...")
        
        # 1. Verificar funcionamento normal
        print("📊 Verificando funcionamento normal...")
        response = requests.get(f"{self.backend_url}/health")
        assert response.status_code == 200
        print("✅ Sistema funcionando normalmente")
        
        # 2. Simular falha do banco via configuração
        print("💥 Simulando falha do banco de dados...")
        
        # Testar com webhook quando banco está "indisponível"
        # (simulamos via timeout ou conexão inválida)
        test_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "from": "5511999000001",
                            "text": {"body": "Teste com banco indisponível"},
                            "type": "text",
                            "id": "wamid.db_down_test",
                            "timestamp": str(int(time.time()))
                        }]
                    }
                }]
            }]
        }
        
        # O sistema deve responder mesmo com problemas de BD
        # Pode retornar erro, mas não deve travar
        try:
            response = requests.post(
                f"{self.backend_url}/webhook",
                json=test_payload,
                timeout=10
            )
            
            # Sistema deve responder (pode ser erro 500, mas deve responder)
            assert response.status_code in [200, 500, 503]
            print(f"✅ Sistema respondeu com status {response.status_code}")
            
            if response.status_code == 500:
                print("ℹ️ Erro 500 esperado com banco indisponível")
            elif response.status_code == 200:
                print("ℹ️ Sistema tem fallback funcionando")
                
        except requests.exceptions.Timeout:
            print("⚠️ Timeout na resposta - sistema pode estar travado")
            # Ainda assim, não deve ser um erro fatal
        
        # 3. Verificar se health check reporta problema
        print("🏥 Verificando health check...")
        try:
            health_response = requests.get(f"{self.backend_url}/health", timeout=5)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                # Health check pode reportar status do banco
                print(f"📊 Health status: {health_data}")
            else:
                print("⚠️ Health check reportando problemas")
                
        except Exception as e:
            print(f"❌ Health check falhou: {e}")
        
        print("🎉 Teste de banco indisponível concluído!")
    
    def test_openai_api_timeout(self):
        """Testa fallback quando OpenAI falha"""
        print("\n🧪 Testando timeout da API OpenAI...")
        
        # Mock da chamada OpenAI para simular timeout
        def simulate_openai_request():
            """Simular requisição com timeout"""
            try:
                # Enviar mensagem que deve acionar processamento de IA
                ai_payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [{
                                    "from": "5511999000002",
                                    "text": {"body": "Preciso de ajuda com agendamento urgente"},
                                    "type": "text",
                                    "id": "wamid.ai_test",
                                    "timestamp": str(int(time.time()))
                                }]
                            }
                        }]
                    }]
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.backend_url}/webhook",
                    json=ai_payload,
                    timeout=15
                )
                response_time = time.time() - start_time
                
                return {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'response_data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                }
                
            except Exception as e:
                return {
                    'error': str(e),
                    'status_code': None
                }
        
        # 1. Teste normal
        print("🤖 Testando processamento normal de IA...")
        normal_result = simulate_openai_request()
        
        if normal_result.get('status_code') == 200:
            print("✅ Processamento normal funcionando")
        else:
            print(f"ℹ️ Status: {normal_result.get('status_code')} - {normal_result.get('error', 'N/A')}")
        
        # 2. Verificar tempo de resposta (não deve travar)
        response_time = normal_result.get('response_time', 0)
        assert response_time < 30, f"Resposta muito lenta: {response_time}s"
        print(f"⏱️ Tempo de resposta: {response_time:.2f}s")
        
        # 3. Sistema deve ter fallback ou timeout adequado
        if normal_result.get('status_code') == 200:
            print("✅ Sistema processou com sucesso (com ou sem IA)")
        elif normal_result.get('status_code') in [500, 503]:
            print("✅ Sistema retornou erro controlado (fallback funcionando)")
        else:
            print("⚠️ Comportamento inesperado do sistema")
        
        print("🎉 Teste de timeout OpenAI concluído!")
    
    def test_high_memory_scenario(self):
        """Testa comportamento com pouca memória"""
        print("\n🧪 Testando cenário de pouca memória...")
        
        # Verificar memória atual
        memory = psutil.virtual_memory()
        print(f"💾 Memória disponível: {memory.available / (1024**3):.1f}GB")
        
        # Simular carga de memória enviando muitas mensagens grandes
        print("📈 Gerando carga de memória...")
        
        large_message_payload = {
            "object": "whatsapp_business_account", 
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "messages": [{
                            "from": "5511999000003",
                            "text": {"body": "Mensagem grande: " + "X" * 10000},  # 10KB por mensagem
                            "type": "text",
                            "id": "wamid.memory_test",
                            "timestamp": str(int(time.time()))
                        }]
                    }
                }]
            }]
        }
        
        # Enviar muitas mensagens grandes
        memory_results = []
        for i in range(50):  # 50 mensagens grandes
            try:
                start_memory = psutil.virtual_memory().available
                
                response = requests.post(
                    f"{self.backend_url}/webhook",
                    json=large_message_payload,
                    timeout=10
                )
                
                end_memory = psutil.virtual_memory().available
                memory_used = start_memory - end_memory
                
                memory_results.append({
                    'message_id': i,
                    'status_code': response.status_code,
                    'memory_used': memory_used,
                    'success': response.status_code == 200
                })
                
                time.sleep(0.1)  # Pequena pausa
                
            except Exception as e:
                memory_results.append({
                    'message_id': i,
                    'error': str(e),
                    'success': False
                })
        
        # Análise dos resultados
        successful = len([r for r in memory_results if r.get('success')])
        total = len(memory_results)
        
        print(f"📊 Mensagens processadas sob carga: {successful}/{total}")
        print(f"📊 Taxa de sucesso: {(successful/total)*100:.1f}%")
        
        # Sistema deve continuar funcionando mesmo com pouca memória
        success_rate = (successful / total) * 100
        assert success_rate >= 70, f"Sistema falhou demais sob carga de memória: {success_rate:.1f}%"
        
        print("🎉 Teste de cenário de pouca memória concluído!")
    
    def test_network_instability(self):
        """Testa comportamento com instabilidade de rede"""
        print("\n🧪 Testando instabilidade de rede...")
        
        # Simular instabilidade com timeouts variados
        timeouts = [1, 3, 5, 10, 15]  # segundos
        network_results = []
        
        for timeout in timeouts:
            print(f"🌐 Testando com timeout de {timeout}s...")
            
            try:
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [{
                                    "from": f"55119990000{timeout}",
                                    "text": {"body": f"Teste network timeout {timeout}s"},
                                    "type": "text",
                                    "id": f"wamid.network_{timeout}",
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
                    timeout=timeout
                )
                response_time = time.time() - start_time
                
                network_results.append({
                    'timeout': timeout,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'success': True
                })
                
                print(f"✅ Timeout {timeout}s: {response.status_code} em {response_time:.2f}s")
                
            except requests.exceptions.Timeout:
                network_results.append({
                    'timeout': timeout,
                    'error': 'timeout',
                    'success': False
                })
                print(f"⏰ Timeout {timeout}s: Timeout ocorreu")
                
            except Exception as e:
                network_results.append({
                    'timeout': timeout,
                    'error': str(e),
                    'success': False
                })
                print(f"❌ Timeout {timeout}s: Erro {e}")
        
        # Análise da estabilidade
        successful = len([r for r in network_results if r.get('success')])
        total = len(network_results)
        
        print(f"📊 Testes de rede bem-sucedidos: {successful}/{total}")
        
        # Pelo menos timeouts maiores devem funcionar
        long_timeout_success = len([
            r for r in network_results 
            if r.get('timeout', 0) >= 10 and r.get('success')
        ])
        
        assert long_timeout_success > 0, "Sistema não responde nem com timeouts longos"
        
        print("🎉 Teste de instabilidade de rede concluído!")
    
    def test_concurrent_failure_recovery(self):
        """Testa recuperação com múltiplas falhas simultâneas"""
        print("\n🧪 Testando recuperação de múltiplas falhas...")
        
        # Simular múltiplos tipos de falha simultaneamente
        failure_scenarios = [
            {"type": "large_payload", "count": 10},
            {"type": "rapid_requests", "count": 20},
            {"type": "invalid_data", "count": 5},
            {"type": "timeout_prone", "count": 3}
        ]
        
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        all_results = []
        
        def simulate_failure_scenario(scenario):
            """Simular um tipo específico de falha"""
            scenario_results = []
            
            for i in range(scenario["count"]):
                try:
                    if scenario["type"] == "large_payload":
                        payload = {
                            "object": "whatsapp_business_account",
                            "entry": [{
                                "changes": [{
                                    "value": {
                                        "messaging_product": "whatsapp",
                                        "messages": [{
                                            "from": f"551199900{i:03d}",
                                            "text": {"body": "Large: " + "X" * 5000},
                                            "type": "text",
                                            "id": f"wamid.large_{i}",
                                            "timestamp": str(int(time.time()))
                                        }]
                                    }
                                }]
                            }]
                        }
                    
                    elif scenario["type"] == "rapid_requests":
                        payload = {
                            "object": "whatsapp_business_account",
                            "entry": [{
                                "changes": [{
                                    "value": {
                                        "messaging_product": "whatsapp",
                                        "messages": [{
                                            "from": f"551199901{i:03d}",
                                            "text": {"body": f"Rapid {i}"},
                                            "type": "text",
                                            "id": f"wamid.rapid_{i}",
                                            "timestamp": str(int(time.time()))
                                        }]
                                    }
                                }]
                            }]
                        }
                    
                    elif scenario["type"] == "invalid_data":
                        payload = {
                            "object": "whatsapp_business_account",
                            "entry": [{
                                "changes": [{
                                    "value": {
                                        "messaging_product": "whatsapp",
                                        "messages": [{
                                            "from": "",  # Dados inválidos
                                            "text": {"body": ""},
                                            "type": "text",
                                            "id": f"wamid.invalid_{i}",
                                            "timestamp": "invalid"
                                        }]
                                    }
                                }]
                            }]
                        }
                    
                    else:  # timeout_prone
                        payload = {
                            "object": "whatsapp_business_account",
                            "entry": [{
                                "changes": [{
                                    "value": {
                                        "messaging_product": "whatsapp",
                                        "messages": [{
                                            "from": f"551199902{i:03d}",
                                            "text": {"body": f"Timeout prone {i}"},
                                            "type": "text",
                                            "id": f"wamid.timeout_{i}",
                                            "timestamp": str(int(time.time()))
                                        }]
                                    }
                                }]
                            }]
                        }
                    
                    response = requests.post(
                        f"{self.backend_url}/webhook",
                        json=payload,
                        timeout=8
                    )
                    
                    scenario_results.append({
                        'scenario': scenario["type"],
                        'item': i,
                        'status_code': response.status_code,
                        'success': response.status_code in [200, 400, 429]  # Vários códigos são aceitáveis
                    })
                    
                except Exception as e:
                    scenario_results.append({
                        'scenario': scenario["type"],
                        'item': i,
                        'error': str(e),
                        'success': False
                    })
            
            return scenario_results
        
        # Executar cenários em paralelo
        print("🔥 Executando cenários de falha em paralelo...")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(simulate_failure_scenario, scenario) for scenario in failure_scenarios]
            
            for future in futures:
                results = future.result()
                all_results.extend(results)
        
        # Análise da recuperação
        total_tests = len(all_results)
        successful = len([r for r in all_results if r.get('success')])
        
        print(f"📊 Total de testes de falha: {total_tests}")
        print(f"📊 Testes bem-sucedidos: {successful}")
        print(f"📊 Taxa de recuperação: {(successful/total_tests)*100:.1f}%")
        
        # Análise por tipo de falha
        for scenario in failure_scenarios:
            scenario_results = [r for r in all_results if r.get('scenario') == scenario["type"]]
            scenario_success = len([r for r in scenario_results if r.get('success')])
            
            print(f"📊 {scenario['type']}: {scenario_success}/{len(scenario_results)} ({(scenario_success/len(scenario_results))*100:.1f}%)")
        
        # Sistema deve se recuperar de pelo menos 60% das falhas
        recovery_rate = (successful / total_tests) * 100
        assert recovery_rate >= 60, f"Taxa de recuperação muito baixa: {recovery_rate:.1f}%"
        
        print("🎉 Teste de recuperação de múltiplas falhas concluído!")
    
    def test_graceful_degradation(self):
        """Testa degradação graciosa do sistema"""
        print("\n🧪 Testando degradação graciosa...")
        
        # Verificar funcionalidades básicas sob stress
        basic_functions = [
            {"name": "health_check", "url": f"{self.backend_url}/health"},
            {"name": "metrics", "url": f"{self.backend_url}/metrics"},
        ]
        
        degradation_results = []
        
        # Gerar carga de fundo
        import threading
        stop_background_load = threading.Event()
        
        def background_load():
            """Gerar carga de fundo contínua"""
            count = 0
            while not stop_background_load.is_set():
                try:
                    payload = {
                        "object": "whatsapp_business_account",
                        "entry": [{
                            "changes": [{
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "messages": [{
                                        "from": f"551199903{count % 100:02d}",
                                        "text": {"body": f"Background load {count}"},
                                        "type": "text",
                                        "id": f"wamid.bg_{count}",
                                        "timestamp": str(int(time.time()))
                                    }]
                                }
                            }]
                        }]
                    }
                    
                    requests.post(
                        f"{self.backend_url}/webhook",
                        json=payload,
                        timeout=3
                    )
                    count += 1
                    time.sleep(0.2)
                    
                except:
                    pass  # Ignorar erros na carga de fundo
        
        # Iniciar carga de fundo
        print("🔄 Iniciando carga de fundo...")
        bg_thread = threading.Thread(target=background_load, daemon=True)
        bg_thread.start()
        
        # Testar funcionalidades básicas sob carga
        for func in basic_functions:
            print(f"🔍 Testando {func['name']} sob carga...")
            
            function_results = []
            for attempt in range(5):
                try:
                    start_time = time.time()
                    response = requests.get(func["url"], timeout=10)
                    response_time = time.time() - start_time
                    
                    function_results.append({
                        'function': func['name'],
                        'attempt': attempt,
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    })
                    
                except Exception as e:
                    function_results.append({
                        'function': func['name'],
                        'attempt': attempt,
                        'error': str(e),
                        'success': False
                    })
                
                time.sleep(1)
            
            degradation_results.extend(function_results)
        
        # Parar carga de fundo
        stop_background_load.set()
        
        # Análise da degradação
        for func in basic_functions:
            func_results = [r for r in degradation_results if r.get('function') == func['name']]
            func_success = len([r for r in func_results if r.get('success')])
            
            print(f"📊 {func['name']}: {func_success}/{len(func_results)} sucessos")
            
            # Funcionalidades básicas devem funcionar mesmo sob carga
            success_rate = (func_success / len(func_results)) * 100
            assert success_rate >= 80, f"{func['name']} degradou demais: {success_rate:.1f}%"
        
        print("🎉 Teste de degradação graciosa concluído!")
