#!/usr/bin/env python3
"""
🔍 TESTE RÁPIDO DAS CORREÇÕES DO WEBHOOK
=====================================

Testa se as correções do webhook estão funcionando adequadamente
antes de executar o teste completo.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

class WebhookCorrectionTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoints_exist(self):
        """Testa se os endpoints de correção existem"""
        print("🔍 Testando existência dos endpoints...")
        
        endpoints_to_test = [
            "/webhook/stats",
            "/webhook/status", 
            "/webhook/control"
        ]
        
        results = {}
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{self.base_url}{endpoint}"
                async with self.session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        results[endpoint] = {
                            "exists": True,
                            "status": response.status,
                            "data": data
                        }
                        print(f"  ✅ {endpoint} - OK ({response.status})")
                    else:
                        results[endpoint] = {
                            "exists": False,
                            "status": response.status,
                            "error": f"Status {response.status}"
                        }
                        print(f"  ❌ {endpoint} - Erro {response.status}")
            except Exception as e:
                results[endpoint] = {
                    "exists": False,
                    "status": None,
                    "error": str(e)
                }
                print(f"  ❌ {endpoint} - Erro: {e}")
        
        return results
    
    async def test_single_response_mechanism(self):
        """Testa o mecanismo de resposta única enviando mensagens similares"""
        print("\n🎯 Testando mecanismo de resposta única...")
        
        # Simular webhook payload
        test_payload = {
            "entry": [{
                "id": "test_entry",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"display_phone_number": "15550123456", "phone_number_id": "test"},
                        "contacts": [{"profile": {"name": "Tester"}, "wa_id": "5511999999999"}],
                        "messages": [{
                            "from": "5511999999999",
                            "id": f"test_message_{int(time.time())}",
                            "timestamp": str(int(time.time())),
                            "text": {"body": "olá, quais são os serviços?"},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        responses = []
        
        print("  📤 Enviando 5 mensagens idênticas rapidamente...")
        
        # Resetar estatísticas primeiro
        try:
            async with self.session.post(f"{self.base_url}/webhook/reset-stats") as response:
                if response.status == 200:
                    print("  🔄 Estatísticas resetadas")
        except:
            pass
        
        # Enviar múltiplas mensagens idênticas
        start_time = time.time()
        
        for i in range(5):
            try:
                # Pequeno delay para simular condições reais
                if i > 0:
                    await asyncio.sleep(0.1)
                
                async with self.session.post(
                    f"{self.base_url}/webhook",
                    json=test_payload,
                    timeout=10
                ) as response:
                    response_time = time.time() - start_time
                    responses.append({
                        "attempt": i + 1,
                        "status": response.status,
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    if response.status == 200:
                        print(f"    ✅ Mensagem {i+1} - OK ({response.status}) [{response_time:.2f}s]")
                    else:
                        print(f"    ❌ Mensagem {i+1} - Erro ({response.status}) [{response_time:.2f}s]")
            except Exception as e:
                responses.append({
                    "attempt": i + 1,
                    "status": None,
                    "error": str(e),
                    "response_time": time.time() - start_time
                })
                print(f"    ❌ Mensagem {i+1} - Exceção: {e}")
        
        # Aguardar um pouco para processar
        await asyncio.sleep(2)
        
        # Verificar estatísticas finais
        try:
            async with self.session.get(f"{self.base_url}/webhook/stats") as response:
                if response.status == 200:
                    stats_data = await response.json()
                    
                    print(f"\n  📊 Estatísticas finais:")
                    stats = stats_data.get('stats', {})
                    print(f"    - Mensagens processadas: {stats.get('messages_processed', 0)}")
                    print(f"    - Mensagens bloqueadas: {stats.get('messages_blocked', 0)}")
                    print(f"    - Respostas enviadas: {stats.get('responses_sent', 0)}")
                    print(f"    - Duplicatas prevenidas: {stats.get('duplicates_prevented', 0)}")
                    print(f"    - Erros: {stats.get('errors', 0)}")
                    
                    metrics = stats_data.get('metrics', {})
                    effectiveness = metrics.get('effectiveness_percent', 0)
                    print(f"    - Efetividade: {effectiveness}%")
                    
                    # Avaliar resultado
                    messages_processed = stats.get('messages_processed', 0)
                    responses_sent = stats.get('responses_sent', 0)
                    
                    if messages_processed == 1 and responses_sent == 1:
                        print(f"  ✅ SUCESSO: Controle de resposta única funcionando!")
                        print(f"     └─ Apenas 1 mensagem foi processada das 5 enviadas")
                    elif messages_processed > 1 or responses_sent > 1:
                        print(f"  ❌ FALHA: Múltiplas mensagens processadas")
                        print(f"     └─ Processadas: {messages_processed}, Respostas: {responses_sent}")
                    else:
                        print(f"  ⚠️  INCONCLUSIVO: Nenhuma mensagem processada")
                    
                    return {
                        "test_successful": messages_processed == 1 and responses_sent == 1,
                        "messages_processed": messages_processed,
                        "responses_sent": responses_sent,
                        "stats": stats_data
                    }
        except Exception as e:
            print(f"  ❌ Erro ao obter estatísticas: {e}")
        
        return {
            "test_successful": False,
            "error": "Falha ao obter estatísticas",
            "responses": responses
        }
    
    async def test_endpoint_functionality(self):
        """Testa funcionalidade específica dos endpoints"""
        print("\n🔧 Testando funcionalidade dos endpoints...")
        
        results = {}
        
        # Teste /webhook/status
        try:
            async with self.session.get(f"{self.base_url}/webhook/status") as response:
                if response.status == 200:
                    data = await response.json()
                    results['status'] = {
                        "working": True,
                        "corrections_active": data.get('corrections_active', False),
                        "single_response_system": data.get('single_response_system', False),
                        "effectiveness": data.get('effectiveness_percent', 0)
                    }
                    print(f"  ✅ /webhook/status:")
                    print(f"    - Correções ativas: {data.get('corrections_active', False)}")
                    print(f"    - Sistema resposta única: {data.get('single_response_system', False)}")
                    print(f"    - Efetividade: {data.get('effectiveness_percent', 0)}%")
        except Exception as e:
            results['status'] = {"working": False, "error": str(e)}
            print(f"  ❌ /webhook/status erro: {e}")
        
        # Teste /webhook/control
        try:
            async with self.session.get(f"{self.base_url}/webhook/control") as response:
                if response.status == 200:
                    data = await response.json()
                    results['control'] = {
                        "working": True,
                        "response_control": data.get('response_control', False),
                        "single_response_working": data.get('single_response_working', False),
                        "issues": data.get('issues', [])
                    }
                    print(f"  ✅ /webhook/control:")
                    print(f"    - Controle de resposta: {data.get('response_control', False)}")
                    print(f"    - Sistema funcionando: {data.get('single_response_working', False)}")
                    if data.get('issues'):
                        print(f"    - Issues detectados: {data.get('issues')}")
        except Exception as e:
            results['control'] = {"working": False, "error": str(e)}
            print(f"  ❌ /webhook/control erro: {e}")
        
        return results

async def run_quick_test():
    """Executa teste rápido das correções"""
    print("🚀 TESTE RÁPIDO DAS CORREÇÕES DO WEBHOOK")
    print("=" * 50)
    
    async with WebhookCorrectionTester() as tester:
        try:
            # 1. Testar se endpoints existem
            endpoint_results = await tester.test_endpoints_exist()
            
            # 2. Testar funcionalidade
            functionality_results = await tester.test_endpoint_functionality()
            
            # 3. Testar mecanismo de resposta única
            single_response_results = await tester.test_single_response_mechanism()
            
            # Resumo final
            print(f"\n🏁 RESUMO DO TESTE RÁPIDO")
            print("=" * 30)
            
            endpoints_working = all(r.get('exists', False) for r in endpoint_results.values())
            print(f"📊 Endpoints existem: {'✅ SIM' if endpoints_working else '❌ NÃO'}")
            
            functionality_working = all(r.get('working', False) for r in functionality_results.values())
            print(f"🔧 Funcionalidade: {'✅ OK' if functionality_working else '❌ FALHA'}")
            
            single_response_working = single_response_results.get('test_successful', False)
            print(f"🎯 Resposta única: {'✅ FUNCIONANDO' if single_response_working else '❌ FALHA'}")
            
            all_working = endpoints_working and functionality_working and single_response_working
            
            if all_working:
                print(f"\n🎉 RESULTADO: CORREÇÕES FUNCIONANDO!")
                print(f"   └─ Pronto para teste completo")
            else:
                print(f"\n⚠️  RESULTADO: CORREÇÕES COM PROBLEMAS")
                print(f"   └─ Verifique os logs acima")
            
            return {
                "all_working": all_working,
                "endpoints": endpoint_results,
                "functionality": functionality_results,
                "single_response": single_response_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO NO TESTE: {e}")
            return {
                "all_working": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

if __name__ == "__main__":
    try:
        result = asyncio.run(run_quick_test())
        
        # Salvar resultado
        with open("test_webhook_corrections_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Resultado salvo em: test_webhook_corrections_result.json")
        
        # Exit code
        exit(0 if result.get('all_working', False) else 1)
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Teste cancelado pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n💥 Erro fatal: {e}")
        exit(1)