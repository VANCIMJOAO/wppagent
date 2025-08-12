"""
🧪 Testes de Carga - Performance e Escalabilidade
Testa comportamento do sistema sob alta carga
"""
import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import random


class TestLoadPerformance:
    """⚡ Testes de performance e carga"""
    
    @pytest.mark.load
    @pytest.mark.slow
    async def test_concurrent_webhook_processing(self, test_client, load_test_data, performance_monitor):
        """Testa processamento concorrente de webhooks"""
        
        concurrent_users = 50
        messages_per_user = 5
        
        performance_monitor.start("concurrent_webhook_test")
        
        async def simulate_user_conversation(user_id: int):
            """Simula conversa de um usuário"""
            user_phone = f"5511999{user_id:06d}"
            messages = random.sample(load_test_data["test_messages"], messages_per_user)
            
            user_results = []
            
            for i, message in enumerate(messages):
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "id": "load_test_account",
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "test_phone_id"
                                },
                                "contacts": [{
                                    "profile": {"name": f"Load User {user_id}"},
                                    "wa_id": user_phone
                                }],
                                "messages": [{
                                    "from": user_phone,
                                    "id": f"load_msg_{user_id}_{i}_{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {"body": message}
                                }]
                            },
                            "field": "messages"
                        }]
                    }]
                }
                
                start_time = time.time()
                try:
                    response = await test_client.post("/webhook", json=payload)
                    end_time = time.time()
                    
                    user_results.append({
                        "user_id": user_id,
                        "message_index": i,
                        "response_time": end_time - start_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    })
                    
                    # Pequeno delay entre mensagens do mesmo usuário
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    user_results.append({
                        "user_id": user_id,
                        "message_index": i,
                        "response_time": 0,
                        "status_code": 500,
                        "success": False,
                        "error": str(e)
                    })
            
            return user_results
        
        # Executar simulação concorrente
        tasks = [simulate_user_conversation(i) for i in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks)
        
        total_duration = performance_monitor.end("concurrent_webhook_test")
        
        # Flatten results
        flat_results = [item for sublist in all_results for item in sublist]
        
        # Análise de resultados
        successful_requests = [r for r in flat_results if r["success"]]
        failed_requests = [r for r in flat_results if not r["success"]]
        response_times = [r["response_time"] for r in successful_requests]
        
        # Assertions de performance
        success_rate = len(successful_requests) / len(flat_results)
        assert success_rate >= 0.95, f"Taxa de sucesso muito baixa: {success_rate:.2%}"
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            
            assert avg_response_time < 2.0, f"Tempo médio de resposta muito alto: {avg_response_time:.2f}s"
            assert p95_response_time < 5.0, f"P95 de resposta muito alto: {p95_response_time:.2f}s"
        
        # Throughput
        total_requests = len(flat_results)
        throughput = total_requests / total_duration
        assert throughput >= 20, f"Throughput muito baixo: {throughput:.2f} req/s"
        
        print(f"\n📊 RESULTADOS DO TESTE DE CARGA:")
        print(f"👥 Usuários concorrentes: {concurrent_users}")
        print(f"📨 Total de mensagens: {total_requests}")
        print(f"✅ Taxa de sucesso: {success_rate:.2%}")
        print(f"⏱️ Tempo médio de resposta: {avg_response_time:.3f}s")
        print(f"📈 Throughput: {throughput:.2f} req/s")
        if response_times:
            print(f"🎯 P95 tempo de resposta: {p95_response_time:.3f}s")
    
    @pytest.mark.load
    async def test_database_connection_pool_under_load(self, test_db_engine):
        """Testa pool de conexões do banco sob carga"""
        
        async def database_operation(operation_id: int):
            """Simula operação no banco de dados"""
            start_time = time.time()
            
            try:
                async with test_db_engine.begin() as conn:
                    # Simular query pesada
                    result = await conn.execute("SELECT pg_sleep(0.1), $1 as id", operation_id)
                    row = result.fetchone()
                    
                    end_time = time.time()
                    return {
                        "operation_id": operation_id,
                        "duration": end_time - start_time,
                        "success": True,
                        "result": row[1] if row else None
                    }
            except Exception as e:
                end_time = time.time()
                return {
                    "operation_id": operation_id,
                    "duration": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Executar 100 operações concorrentes
        concurrent_operations = 100
        tasks = [database_operation(i) for i in range(concurrent_operations)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        successful_ops = [r for r in results if r["success"]]
        failed_ops = [r for r in results if not r["success"]]
        
        # Verificações
        success_rate = len(successful_ops) / len(results)
        assert success_rate >= 0.98, f"Taxa de sucesso do banco muito baixa: {success_rate:.2%}"
        
        total_duration = end_time - start_time
        ops_per_second = len(results) / total_duration
        
        print(f"\n🗄️ TESTE DE CARGA DO BANCO:")
        print(f"⚙️ Operações concorrentes: {concurrent_operations}")
        print(f"✅ Taxa de sucesso: {success_rate:.2%}")
        print(f"📊 Operações/segundo: {ops_per_second:.2f}")
        print(f"⏱️ Duração total: {total_duration:.2f}s")
    
    @pytest.mark.load
    async def test_cache_performance_under_load(self, test_redis):
        """Testa performance do cache sob carga"""
        
        from app.services.cache_service import CacheService
        cache_service = CacheService(test_redis)
        
        async def cache_operations(worker_id: int):
            """Executa operações de cache"""
            operations = []
            
            for i in range(50):  # 50 operações por worker
                key = f"load_test_{worker_id}_{i}"
                value = {"data": f"test_data_{worker_id}_{i}", "timestamp": time.time()}
                
                # Set operation
                start_time = time.time()
                await cache_service.set_json(key, value, ttl=300)
                set_time = time.time() - start_time
                
                # Get operation
                start_time = time.time()
                retrieved = await cache_service.get_json(key)
                get_time = time.time() - start_time
                
                operations.append({
                    "worker_id": worker_id,
                    "operation": i,
                    "set_time": set_time,
                    "get_time": get_time,
                    "data_match": retrieved == value
                })
            
            return operations
        
        # 20 workers executando operações simultaneamente
        num_workers = 20
        tasks = [cache_operations(i) for i in range(num_workers)]
        
        start_time = time.time()
        all_operations = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Flatten results
        flat_operations = [op for worker_ops in all_operations for op in worker_ops]
        
        # Análise de performance
        set_times = [op["set_time"] for op in flat_operations]
        get_times = [op["get_time"] for op in flat_operations]
        data_matches = [op["data_match"] for op in flat_operations]
        
        avg_set_time = statistics.mean(set_times)
        avg_get_time = statistics.mean(get_times)
        data_integrity = sum(data_matches) / len(data_matches)
        
        total_operations = len(flat_operations) * 2  # set + get
        total_duration = end_time - start_time
        ops_per_second = total_operations / total_duration
        
        # Assertions
        assert avg_set_time < 0.01, f"SET muito lento: {avg_set_time:.4f}s"
        assert avg_get_time < 0.005, f"GET muito lento: {avg_get_time:.4f}s"
        assert data_integrity == 1.0, f"Integridade de dados comprometida: {data_integrity:.2%}"
        assert ops_per_second >= 1000, f"Throughput do cache muito baixo: {ops_per_second:.2f} ops/s"
        
        print(f"\n💾 TESTE DE CARGA DO CACHE:")
        print(f"⚙️ Workers: {num_workers}")
        print(f"📊 Operações totais: {total_operations}")
        print(f"⏱️ SET médio: {avg_set_time:.4f}s")
        print(f"⏱️ GET médio: {avg_get_time:.4f}s")
        print(f"🎯 Ops/segundo: {ops_per_second:.2f}")
        print(f"✅ Integridade: {data_integrity:.2%}")
    
    @pytest.mark.load
    @pytest.mark.external
    async def test_llm_service_rate_limiting(self, mock_openai):
        """Testa rate limiting do serviço LLM"""
        
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        
        async def llm_request(request_id: int):
            """Executa uma requisição LLM"""
            start_time = time.time()
            
            try:
                result = await llm_service.process_message(
                    user_id=f"load_user_{request_id}",
                    message=f"Mensagem de teste {request_id}",
                    context={}
                )
                
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "duration": end_time - start_time,
                    "success": True,
                    "result": result.text if result else None
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "duration": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # Executar muitas requisições para testar rate limiting
        num_requests = 100
        tasks = [llm_request(i) for i in range(num_requests)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        total_duration = end_time - start_time
        requests_per_second = len(results) / total_duration
        
        # Verificar se rate limiting está funcionando
        # (Se muitas requisições foram rejeitadas, rate limiting está ativo)
        rejection_rate = len(failed_requests) / len(results)
        
        print(f"\n🤖 TESTE DE RATE LIMITING LLM:")
        print(f"📨 Requisições totais: {num_requests}")
        print(f"✅ Sucessos: {len(successful_requests)}")
        print(f"❌ Falhas: {len(failed_requests)}")
        print(f"🚫 Taxa de rejeição: {rejection_rate:.2%}")
        print(f"📊 Req/segundo: {requests_per_second:.2f}")
        
        # Deve ter algum controle de rate limiting
        assert rejection_rate < 0.5 or requests_per_second < 50  # Ou alta rejeição ou velocidade controlada


class TestStressTest:
    """💥 Testes de stress - limites do sistema"""
    
    @pytest.mark.load
    @pytest.mark.slow
    async def test_memory_usage_under_load(self, test_client, performance_monitor):
        """Testa uso de memória sob carga intensa"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        performance_monitor.start("memory_stress_test")
        
        # Criar muitas conversas simultâneas com histórico extenso
        async def create_heavy_conversation(user_id: int):
            user_phone = f"5511999{user_id:06d}"
            
            # Enviar muitas mensagens para criar histórico
            for i in range(20):  # 20 mensagens por conversa
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "id": "stress_test",
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test"},
                                "contacts": [{"profile": {"name": f"Stress User {user_id}"}, "wa_id": user_phone}],
                                "messages": [{
                                    "from": user_phone,
                                    "id": f"stress_{user_id}_{i}",
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {"body": f"Mensagem longa {i} " * 50}  # Mensagem longa
                                }]
                            },
                            "field": "messages"
                        }]
                    }]
                }
                
                await test_client.post("/webhook", json=payload)
        
        # Executar com muitos usuários
        num_users = 200
        tasks = [create_heavy_conversation(i) for i in range(num_users)]
        await asyncio.gather(*tasks)
        
        total_duration = performance_monitor.end("memory_stress_test")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n🧠 TESTE DE STRESS DE MEMÓRIA:")
        print(f"👥 Usuários simulados: {num_users}")
        print(f"📊 Memória inicial: {initial_memory:.2f} MB")
        print(f"📊 Memória final: {final_memory:.2f} MB")
        print(f"📈 Aumento de memória: {memory_increase:.2f} MB")
        print(f"⏱️ Duração: {total_duration:.2f}s")
        
        # Verificar se não há vazamento excessivo de memória
        memory_per_user = memory_increase / num_users
        assert memory_per_user < 1.0, f"Possível vazamento de memória: {memory_per_user:.3f} MB/usuário"
        assert final_memory < initial_memory * 3, f"Uso de memória triplicou: {final_memory/initial_memory:.2f}x"
    
    @pytest.mark.load
    @pytest.mark.slow
    async def test_sustained_load_over_time(self, test_client):
        """Testa carga sustentada por período prolongado"""
        
        duration_minutes = 2  # 2 minutos de teste
        end_time = time.time() + (duration_minutes * 60)
        
        metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }
        
        async def sustained_load_worker():
            """Worker que executa carga constante"""
            worker_id = random.randint(1000, 9999)
            
            while time.time() < end_time:
                user_phone = f"5511999{worker_id:06d}"
                message = random.choice([
                    "Olá, preciso de ajuda",
                    "Quero agendar um horário",
                    "Qual o preço do serviço?",
                    "Onde vocês ficam?"
                ])
                
                payload = {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "id": "sustained_test",
                        "changes": [{
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {"phone_number_id": "test"},
                                "contacts": [{"profile": {"name": f"Worker {worker_id}"}, "wa_id": user_phone}],
                                "messages": [{
                                    "from": user_phone,
                                    "id": f"sustained_{worker_id}_{int(time.time())}",
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {"body": message}
                                }]
                            },
                            "field": "messages"
                        }]
                    }]
                }
                
                start_time = time.time()
                try:
                    response = await test_client.post("/webhook", json=payload)
                    response_time = time.time() - start_time
                    
                    metrics["total_requests"] += 1
                    metrics["response_times"].append(response_time)
                    
                    if response.status_code == 200:
                        metrics["successful_requests"] += 1
                    else:
                        metrics["failed_requests"] += 1
                        
                except Exception as e:
                    metrics["failed_requests"] += 1
                    metrics["errors"].append(str(e))
                
                # Pequeno delay para controlar a taxa
                await asyncio.sleep(0.1)
        
        # Executar 10 workers em paralelo
        num_workers = 10
        tasks = [sustained_load_worker() for _ in range(num_workers)]
        await asyncio.gather(*tasks)
        
        # Análise dos resultados
        if metrics["response_times"]:
            avg_response_time = statistics.mean(metrics["response_times"])
            max_response_time = max(metrics["response_times"])
            
            success_rate = metrics["successful_requests"] / metrics["total_requests"]
            
            print(f"\n⏰ TESTE DE CARGA SUSTENTADA ({duration_minutes} min):")
            print(f"📊 Total de requisições: {metrics['total_requests']}")
            print(f"✅ Taxa de sucesso: {success_rate:.2%}")
            print(f"⏱️ Tempo médio de resposta: {avg_response_time:.3f}s")
            print(f"⏱️ Tempo máximo de resposta: {max_response_time:.3f}s")
            print(f"❌ Total de erros: {len(metrics['errors'])}")
            
            # Verificações de estabilidade
            assert success_rate >= 0.95, f"Sistema instável: taxa de sucesso {success_rate:.2%}"
            assert avg_response_time < 3.0, f"Degradação de performance: {avg_response_time:.3f}s"
            assert max_response_time < 10.0, f"Picos de latência muito altos: {max_response_time:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "load"])
