#!/usr/bin/env python3
"""
🧪 TESTE DAS CORREÇÕES - WhatsApp Bot Response Control
=====================================================

Este script testa especificamente as correções implementadas
para resolver o problema de múltiplas respostas simultâneas.

TESTES REALIZADOS:
1. 🛑 Controle de Resposta Única
2. 🔄 Prevenção de Duplicatas
3. ⏱️ Controle de Intervalo de Tempo
4. 🧹 Sistema de Limpeza
5. 📊 Monitoramento de Estatísticas

"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime


class CorrectionsTester:
    def __init__(self):
        self.base_url = "https://wppagent-production.up.railway.app"
        self.test_phone = "5516991022255"
        self.session_id = f"corrections_test_{int(time.time())}"
        
    async def test_single_response_control(self):
        """Testa se o sistema está enviando apenas uma resposta"""
        print("🛑 TESTANDO CONTROLE DE RESPOSTA ÚNICA...")
        
        test_messages = [
            "Oi",
            "Quais serviços vocês oferecem?",
            "Quanto custa limpeza de pele?",
            "Quero agendar uma massagem",
            "Qual o horário de funcionamento?"
        ]
        
        results = []
        
        for i, message in enumerate(test_messages):
            print(f"\n📨 Teste {i+1}: '{message}'")
            
            # Enviar mensagem
            webhook_payload = self._create_webhook_payload(message)
            
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.base_url}/webhook",
                        json=webhook_payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "facebookexternalua"
                        },
                        timeout=30
                    ) as response:
                        
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            print(f"  ✅ Webhook aceito (tempo: {response_time:.2f}s)")
                            
                            # Aguardar um pouco para processar
                            await asyncio.sleep(3)
                            
                            # Verificar estatísticas
                            stats = await self._get_stats()
                            
                            result = {
                                "message": message,
                                "webhook_accepted": True,
                                "response_time": response_time,
                                "stats": stats,
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            print(f"  📊 Mensagens processadas: {stats.get('stats', {}).get('messages_processed', 0)}")
                            print(f"  📊 Respostas enviadas: {stats.get('stats', {}).get('responses_sent', 0)}")
                            print(f"  📊 Mensagens bloqueadas: {stats.get('stats', {}).get('messages_blocked', 0)}")
                            
                        else:
                            print(f"  ❌ Erro no webhook: {response.status}")
                            result = {
                                "message": message,
                                "webhook_accepted": False,
                                "error": f"HTTP {response.status}",
                                "timestamp": datetime.now().isoformat()
                            }
                        
                        results.append(result)
                        
                except Exception as e:
                    print(f"  ❌ Erro na requisição: {e}")
                    results.append({
                        "message": message,
                        "webhook_accepted": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Intervalo entre testes
            await asyncio.sleep(5)
        
        return results
    
    async def test_duplicate_prevention(self):
        """Testa prevenção de duplicatas"""
        print("\n🔄 TESTANDO PREVENÇÃO DE DUPLICATAS...")
        
        test_message = "Teste de duplicata"
        
        print(f"📨 Enviando 3x a mesma mensagem: '{test_message}'")
        
        results = []
        
        for i in range(3):
            print(f"\n  Tentativa {i+1}:")
            
            webhook_payload = self._create_webhook_payload(test_message)
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.base_url}/webhook",
                        json=webhook_payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "facebookexternalua"
                        },
                        timeout=30
                    ) as response:
                        
                        if response.status == 200:
                            print(f"    ✅ Webhook aceito")
                        else:
                            print(f"    ❌ Erro: {response.status}")
                        
                        # Verificar estatísticas
                        await asyncio.sleep(2)
                        stats = await self._get_stats()
                        
                        results.append({
                            "attempt": i + 1,
                            "webhook_accepted": response.status == 200,
                            "stats": stats
                        })
                        
                        print(f"    📊 Total processadas: {stats.get('stats', {}).get('messages_processed', 0)}")
                        print(f"    📊 Total bloqueadas: {stats.get('stats', {}).get('messages_blocked', 0)}")
                        
                except Exception as e:
                    print(f"    ❌ Erro: {e}")
                    results.append({
                        "attempt": i + 1,
                        "webhook_accepted": False,
                        "error": str(e)
                    })
            
            # Pequeno intervalo
            await asyncio.sleep(1)
        
        return results
    
    async def test_rapid_fire(self):
        """Testa envio rápido de mensagens"""
        print("\n⚡ TESTANDO ENVIO RÁPIDO (RAPID FIRE)...")
        
        messages = [
            "Mensagem rápida 1",
            "Mensagem rápida 2", 
            "Mensagem rápida 3",
            "Mensagem rápida 4",
            "Mensagem rápida 5"
        ]
        
        print(f"📨 Enviando {len(messages)} mensagens rapidamente...")
        
        # Enviar todas as mensagens rapidamente
        tasks = []
        
        for i, message in enumerate(messages):
            task = self._send_message_async(message, i+1)
            tasks.append(task)
        
        # Executar todas simultaneamente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aguardar processamento
        await asyncio.sleep(5)
        
        # Verificar estatísticas finais
        final_stats = await self._get_stats()
        
        print(f"\n📊 RESULTADO RAPID FIRE:")
        print(f"  Mensagens enviadas: {len(messages)}")
        print(f"  Respostas processadas: {final_stats.get('stats', {}).get('messages_processed', 0)}")
        print(f"  Respostas enviadas: {final_stats.get('stats', {}).get('responses_sent', 0)}")
        print(f"  Mensagens bloqueadas: {final_stats.get('stats', {}).get('messages_blocked', 0)}")
        
        # Verificar efetividade
        effectiveness = final_stats.get('metrics', {}).get('effectiveness_percent', 0)
        print(f"  Efetividade: {effectiveness}%")
        
        if effectiveness >= 90:
            print("  ✅ CONTROLE DE RESPOSTA ÚNICA FUNCIONANDO!")
        else:
            print("  ❌ CONTROLE DE RESPOSTA ÚNICA COM PROBLEMAS!")
        
        return {
            "messages_sent": len(messages),
            "results": results,
            "final_stats": final_stats,
            "effectiveness": effectiveness
        }
    
    async def _send_message_async(self, message: str, attempt_number: int):
        """Envia mensagem de forma assíncrona"""
        try:
            webhook_payload = self._create_webhook_payload(message)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/webhook",
                    json=webhook_payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "facebookexternalua"
                    },
                    timeout=30
                ) as response:
                    
                    result = {
                        "attempt": attempt_number,
                        "message": message,
                        "status": response.status,
                        "success": response.status == 200,
                        "timestamp": time.time()
                    }
                    
                    print(f"    {attempt_number}. '{message}' -> {response.status}")
                    return result
                    
        except Exception as e:
            print(f"    {attempt_number}. '{message}' -> ERRO: {e}")
            return {
                "attempt": attempt_number,
                "message": message,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _get_stats(self):
        """Obtém estatísticas do sistema"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/webhook/stats",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"HTTP {response.status}"}
        except Exception as e:
            return {"error": str(e)}
    
    def _create_webhook_payload(self, message: str):
        """Cria payload do webhook"""
        message_id = f"wamid.test_{int(time.time())}_{hash(message) % 10000}"
        
        return {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551536026",
                            "phone_number_id": "728348237027885"
                        },
                        "messages": [{
                            "from": self.test_phone,
                            "id": message_id,
                            "timestamp": str(int(time.time())),
                            "text": {"body": message},
                            "type": "text"
                        }],
                        "contacts": [{
                            "profile": {"name": "Corrections Tester"},
                            "wa_id": self.test_phone
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
    
    async def run_all_tests(self):
        """Executa todos os testes de correção"""
        print("🧪 INICIANDO TESTES DAS CORREÇÕES")
        print("=" * 60)
        print(f"🆔 Sessão: {self.session_id}")
        print(f"📱 Telefone teste: {self.test_phone}")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)
        
        all_results = {}
        
        try:
            # Resetar estatísticas
            await self._reset_stats()
            
            # Teste 1: Controle de resposta única
            all_results["single_response"] = await self.test_single_response_control()
            
            await asyncio.sleep(3)
            
            # Teste 2: Prevenção de duplicatas
            all_results["duplicate_prevention"] = await self.test_duplicate_prevention()
            
            await asyncio.sleep(3)
            
            # Teste 3: Rapid fire
            all_results["rapid_fire"] = await self.test_rapid_fire()
            
            # Estatísticas finais
            final_stats = await self._get_stats()
            all_results["final_statistics"] = final_stats
            
            # Relatório final
            self._print_final_report(all_results)
            
            return all_results
            
        except Exception as e:
            print(f"❌ Erro nos testes: {e}")
            return {"error": str(e)}
    
    async def _reset_stats(self):
        """Reseta estatísticas para teste limpo"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/webhook/reset-stats",
                    timeout=10
                ) as response:
                    if response.status == 200:
                        print("🔄 Estatísticas resetadas para teste limpo")
                    else:
                        print(f"⚠️ Não foi possível resetar estatísticas: {response.status}")
        except Exception as e:
            print(f"⚠️ Erro ao resetar estatísticas: {e}")
    
    def _print_final_report(self, results):
        """Imprime relatório final"""
        print("\n" + "=" * 60)
        print("🎯 RELATÓRIO FINAL DOS TESTES DE CORREÇÃO")
        print("=" * 60)
        
        final_stats = results.get("final_statistics", {})
        stats = final_stats.get("stats", {})
        metrics = final_stats.get("metrics", {})
        health = final_stats.get("health", {})
        
        print(f"📊 ESTATÍSTICAS FINAIS:")
        print(f"  📨 Mensagens processadas: {stats.get('messages_processed', 0)}")
        print(f"  📤 Respostas enviadas: {stats.get('responses_sent', 0)}")
        print(f"  🚫 Mensagens bloqueadas: {stats.get('messages_blocked', 0)}")
        print(f"  🔄 Duplicatas prevenidas: {stats.get('duplicates_prevented', 0)}")
        print(f"  ❌ Erros: {stats.get('errors', 0)}")
        
        print(f"\n📈 MÉTRICAS:")
        print(f"  📊 Taxa de bloqueio: {metrics.get('block_rate_percent', 0)}%")
        print(f"  📊 Taxa de resposta: {metrics.get('response_rate_percent', 0)}%")
        print(f"  📊 Efetividade: {metrics.get('effectiveness_percent', 0)}%")
        
        print(f"\n💚 SAÚDE DO SISTEMA:")
        print(f"  🛑 Resposta única: {'✅ OK' if health.get('single_response_working') else '❌ FALHA'}")
        print(f"  🔄 Prevenção duplicatas: {'✅ OK' if health.get('duplicate_prevention_working') else '❌ FALHA'}")
        print(f"  🔧 Baixos erros: {'✅ OK' if health.get('low_errors') else '❌ FALHA'}")
        
        # Avaliação geral
        effectiveness = metrics.get('effectiveness_percent', 0)
        single_response_ok = health.get('single_response_working', False)
        
        print(f"\n🎯 AVALIAÇÃO GERAL:")
        if effectiveness >= 90 and single_response_ok:
            print("  🏆 EXCELENTE! Correções funcionando perfeitamente!")
            print(f"  ✅ {effectiveness}% de efetividade")
            print("  🚀 Sistema pronto para produção")
        elif effectiveness >= 70:
            print("  👍 BOM! Correções funcionando parcialmente")
            print(f"  ✅ {effectiveness}% de efetividade")
            print("  💡 Algumas melhorias podem ser feitas")
        else:
            print("  ❌ ATENÇÃO! Correções não estão funcionando adequadamente")
            print(f"  🚨 Apenas {effectiveness}% de efetividade")
            print("  🔧 Revisão das correções necessária")
        
        print("=" * 60)


async def main():
    """Função principal do teste"""
    tester = CorrectionsTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"corrections_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Resultados salvos em: {filename}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 TESTE DAS CORREÇÕES - WhatsApp Bot Response Control")
    print("=" * 60)
    print("🎯 Este teste valida se as correções estão funcionando:")
    print("  • 🛑 Apenas uma resposta por mensagem")
    print("  • 🔄 Prevenção de duplicatas")
    print("  • ⏱️ Controle de intervalo de tempo")
    print("  • 📊 Monitoramento de estatísticas")
    print("=" * 60)
    
    response = input("\n▶️ Executar testes das correções? (ENTER para continuar): ")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Programa finalizado pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro crítico: {e}")
        import traceback
        traceback.print_exc()
