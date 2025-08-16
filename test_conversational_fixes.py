#!/usr/bin/env python3
"""
🔍 TESTE FOCADO - CORREÇÕES DE FLUXO CONVERSACIONAL
=================================================
Teste específico para verificar se as melhorias implementadas
resolveram os problemas identificados nos fluxos de conversa:

🚨 PROBLEMAS IDENTIFICADOS ANTERIORMENTE:
1. ❌ "limpeza de pele" negada mas existe no banco
2. ❌ "massagem relaxante" negada mas existe no banco  
3. ❌ "radiofrequência" negada mas existe no banco
4. ❌ Busca por nome não funciona adequadamente
5. ❌ Contexto conversacional perdido
6. ❌ Respostas desconexas em fluxos complexos

🎯 OBJETIVO: Verificar se as correções funcionam
"""

import asyncio
import asyncpg
import aiohttp
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

class ConversationalFixTester:
    def __init__(self):
        # 🔧 CONFIGURAÇÕES
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        
        # 📱 CREDENCIAIS WHATSAPP
        self.META_ACCESS_TOKEN = "EAAI4WnfpZAe0BPBMBYZAZCjP8r0HNrQZCo2c74fADFset99JTNnZBkDZBdXHZCtZAJ4S1mJvICow0gxPq42R3LvGQ2boenhm7tThzVJQddWnZC4I4Ux5bwlDjbp5hCBGSAuUK44Qo2ByywVFbm2SpaP1peFo1sjZChPszHUyBeSJlGoaEVHWBQnl7IY5ycQsrqzCR7KZC16zWiwneieqY7dVDg3oZBo5O4UQyXihtP4Mb4LN5ffc99xeaOUZBGYQ94goZD"
        self.WHATSAPP_PHONE_ID = "728348237027885"
        self.BOT_PHONE = "15551536026"
        self.YOUR_PHONE = "5516991022255"
        
        # 🆔 SESSÃO
        self.session_id = f"conversational_test_{int(time.time())}"
        
        # 📊 RESULTADOS
        self.results = {
            "session": self.session_id,
            "start_time": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_failed": 0,
            "critical_fixes_verified": {},
            "detailed_tests": {}
        }
        
        # ⚡ LOGGING
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    async def connect_db(self) -> bool:
        """Conecta ao banco PostgreSQL"""
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            self.logger.info("✅ Conectado ao banco PostgreSQL")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar: {e}")
            return False

    async def send_message(self, message: str) -> bool:
        """Envia mensagem via webhook WhatsApp"""
        try:
            webhook_url = f"{self.API_BASE_URL}/webhook"
            
            payload = {
                "object": "whatsapp_business_account",
                "entry": [{
                    "id": self.WHATSAPP_PHONE_ID,
                    "changes": [{
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": self.BOT_PHONE,
                                "phone_number_id": self.WHATSAPP_PHONE_ID
                            },
                            "messages": [{
                                "from": self.YOUR_PHONE,
                                "id": f"wamid.fix_test_{int(time.time())}{random.randint(1000,9999)}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": message},
                                "type": "text"
                            }],
                            "contacts": [{
                                "profile": {"name": "Fix Tester"},
                                "wa_id": self.YOUR_PHONE
                            }]
                        },
                        "field": "messages"
                    }]
                }]
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "facebookexternalua"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        self.logger.info(f"✅ Enviado: '{message[:50]}...'")
                        return True
                    else:
                        self.logger.error(f"❌ Erro webhook: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar: {e}")
            return False

    async def get_bot_responses(self, timeout: int = 15) -> List[str]:
        """Monitora respostas do bot"""
        await asyncio.sleep(3)  # Aguarda processamento
        
        cutoff_time = datetime.now() - timedelta(seconds=60)
        responses = []
        
        for _ in range(timeout // 3):
            try:
                recent = await self.db.fetch("""
                    SELECT content, created_at 
                    FROM messages 
                    WHERE user_id = 2 
                    AND direction = 'out'
                    AND created_at > $1
                    ORDER BY created_at DESC
                    LIMIT 3
                """, cutoff_time)
                
                for msg in recent:
                    content = msg['content']
                    if content not in responses:
                        responses.append(content)
                        self.logger.info(f"🤖 Resposta: {content[:80]}...")
                
                if responses:
                    break
                    
                await asyncio.sleep(3)
                
            except Exception as e:
                self.logger.error(f"❌ Erro monitoramento: {e}")
                break
        
        return responses

    async def test_service_search_fixes(self) -> Dict:
        """
        🎯 TESTE CRÍTICO 1: Busca de Serviços
        Testa se o bot agora encontra serviços por nome/sinônimos
        """
        self.logger.info("\n🔍 TESTE CRÍTICO 1: Busca de Serviços")
        
        test_cases = [
            {
                "query": "Quanto custa limpeza de pele?",
                "should_find": "limpeza de pele",
                "should_not_contain": ["não oferecemos", "não está disponível"],
                "expected_price": "80,00"
            },
            {
                "query": "Valor da massagem relaxante",
                "should_find": "massagem relaxante", 
                "should_not_contain": ["não oferecemos", "não está disponível"],
                "expected_price": "100,00"
            },
            {
                "query": "Vocês fazem radiofrequência?",
                "should_find": "radiofrequência",
                "should_not_contain": ["não oferecemos", "não está disponível"], 
                "expected_price": "180,00"
            },
            {
                "query": "Preço do hidrofacial",
                "should_find": "hidrofacial",
                "should_not_contain": ["não oferecemos", "não está disponível"],
                "expected_price": "150,00"
            }
        ]
        
        results = {
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for i, test in enumerate(test_cases, 1):
            self.logger.info(f"  📝 Teste {i}/{len(test_cases)}: {test['query']}")
            
            # Enviar mensagem
            await self.send_message(test['query'])
            
            # Obter resposta
            responses = await self.get_bot_responses()
            
            if responses:
                response_text = " ".join(responses).lower()
                
                # Verificar se encontrou o serviço
                found_service = test['should_find'].lower() in response_text
                
                # Verificar se NÃO contém mensagens de negação
                no_denial = all(deny.lower() not in response_text for deny in test['should_not_contain'])
                
                # Verificar se contém preço correto
                has_price = test['expected_price'] in response_text
                
                test_passed = found_service and no_denial and has_price
                
                if test_passed:
                    results['passed'] += 1
                    self.logger.info(f"    ✅ PASSOU - Serviço encontrado e preço correto")
                else:
                    results['failed'] += 1
                    self.logger.error(f"    ❌ FALHOU")
                    if not found_service:
                        self.logger.error(f"      - Serviço '{test['should_find']}' não encontrado")
                    if not no_denial:
                        self.logger.error(f"      - Ainda contém mensagem de negação")
                    if not has_price:
                        self.logger.error(f"      - Preço {test['expected_price']} não encontrado")
                
                results['details'].append({
                    "query": test['query'],
                    "responses": responses,
                    "found_service": found_service,
                    "no_denial": no_denial,
                    "has_price": has_price,
                    "passed": test_passed
                })
            else:
                results['failed'] += 1
                self.logger.error(f"    ❌ FALHOU - Sem resposta")
                results['details'].append({
                    "query": test['query'],
                    "responses": [],
                    "passed": False,
                    "error": "No response"
                })
            
            await asyncio.sleep(5)  # Intervalo entre testes
        
        success_rate = (results['passed'] / results['total_tests']) * 100
        self.logger.info(f"\n📊 Resultado Busca de Serviços: {results['passed']}/{results['total_tests']} ({success_rate:.1f}%)")
        
        return results

    async def test_contextual_conversation(self) -> Dict:
        """
        🎯 TESTE CRÍTICO 2: Fluxo Conversacional Contextual
        Testa se o bot mantém contexto em conversas complexas
        """
        self.logger.info("\n🔍 TESTE CRÍTICO 2: Fluxo Conversacional Contextual")
        
        conversation_flow = [
            {
                "message": "Oi, quero saber sobre massagem",
                "expected": ["massagem"],
                "step": "1. Pergunta inicial sobre massagem"
            },
            {
                "message": "Na verdade, quanto custa?", 
                "expected": ["100,00", "massagem", "relaxante"],
                "step": "2. Pergunta contextual sobre preço (deve entender que é sobre massagem)"
            },
            {
                "message": "E limpeza de pele, vocês fazem?",
                "expected": ["limpeza", "80,00"],
                "step": "3. Mudança de assunto para limpeza"
            },
            {
                "message": "Posso agendar as duas coisas no mesmo dia?",
                "expected": ["agendar", "duas", "mesmo dia"],
                "step": "4. Pergunta contextual sobre agendamento conjunto"
            },
            {
                "message": "Voltando à massagem, quanto tempo demora?",
                "expected": ["massagem", "60", "minutos"],
                "step": "5. Retorno ao contexto anterior (massagem)"
            }
        ]
        
        results = {
            "total_steps": len(conversation_flow),
            "passed": 0,
            "failed": 0,
            "conversation_details": []
        }
        
        for i, step in enumerate(conversation_flow, 1):
            self.logger.info(f"  📝 {step['step']}")
            
            # Enviar mensagem
            await self.send_message(step['message'])
            
            # Obter resposta
            responses = await self.get_bot_responses()
            
            if responses:
                response_text = " ".join(responses).lower()
                
                # Verificar se contém padrões esperados
                patterns_found = sum(1 for pattern in step['expected'] if pattern.lower() in response_text)
                total_patterns = len(step['expected'])
                
                step_passed = patterns_found >= (total_patterns * 0.6)  # 60% dos padrões
                
                if step_passed:
                    results['passed'] += 1
                    self.logger.info(f"    ✅ PASSOU - {patterns_found}/{total_patterns} padrões encontrados")
                else:
                    results['failed'] += 1
                    self.logger.error(f"    ❌ FALHOU - {patterns_found}/{total_patterns} padrões encontrados")
                
                results['conversation_details'].append({
                    "step": step['step'],
                    "message": step['message'],
                    "expected_patterns": step['expected'],
                    "responses": responses,
                    "patterns_found": patterns_found,
                    "total_patterns": total_patterns,
                    "passed": step_passed
                })
            else:
                results['failed'] += 1
                self.logger.error(f"    ❌ FALHOU - Sem resposta")
                results['conversation_details'].append({
                    "step": step['step'],
                    "message": step['message'],
                    "passed": False,
                    "error": "No response"
                })
            
            await asyncio.sleep(6)  # Intervalo para manter contexto
        
        success_rate = (results['passed'] / results['total_steps']) * 100
        self.logger.info(f"\n📊 Resultado Fluxo Conversacional: {results['passed']}/{results['total_steps']} ({success_rate:.1f}%)")
        
        return results

    async def test_synonym_recognition(self) -> Dict:
        """
        🎯 TESTE CRÍTICO 3: Reconhecimento de Sinônimos
        Testa se o bot reconhece variações dos nomes dos serviços
        """
        self.logger.info("\n🔍 TESTE CRÍTICO 3: Reconhecimento de Sinônimos")
        
        synonym_tests = [
            {
                "variations": ["limpeza", "facial", "limpeza facial", "cuidado facial"],
                "should_find": "limpeza de pele",
                "expected_price": "80,00"
            },
            {
                "variations": ["massagem", "relaxante", "massoterapia"],
                "should_find": "massagem relaxante", 
                "expected_price": "100,00"
            },
            {
                "variations": ["radio", "radiofrequencia", "firmeza"],
                "should_find": "radiofrequência",
                "expected_price": "180,00"
            },
            {
                "variations": ["criolipolise", "congelar gordura", "redução gordura"],
                "should_find": "criolipólise",
                "expected_price": "300,00"
            }
        ]
        
        results = {
            "total_variations": 0,
            "passed": 0,
            "failed": 0,
            "synonym_details": []
        }
        
        for test in synonym_tests:
            for variation in test['variations']:
                results['total_variations'] += 1
                
                query = f"Quanto custa {variation}?"
                self.logger.info(f"  📝 Testando variação: '{variation}'")
                
                # Enviar mensagem
                await self.send_message(query)
                
                # Obter resposta
                responses = await self.get_bot_responses()
                
                if responses:
                    response_text = " ".join(responses).lower()
                    
                    # Verificar se encontrou o serviço correto
                    found_service = test['should_find'].lower() in response_text
                    has_price = test['expected_price'] in response_text
                    no_denial = "não oferecemos" not in response_text and "não está disponível" not in response_text
                    
                    test_passed = found_service and has_price and no_denial
                    
                    if test_passed:
                        results['passed'] += 1
                        self.logger.info(f"    ✅ '{variation}' → encontrou '{test['should_find']}'")
                    else:
                        results['failed'] += 1
                        self.logger.error(f"    ❌ '{variation}' → não encontrou corretamente")
                    
                    results['synonym_details'].append({
                        "variation": variation,
                        "expected_service": test['should_find'],
                        "query": query,
                        "responses": responses,
                        "found_service": found_service,
                        "has_price": has_price,
                        "no_denial": no_denial,
                        "passed": test_passed
                    })
                else:
                    results['failed'] += 1
                    self.logger.error(f"    ❌ '{variation}' → sem resposta")
                    results['synonym_details'].append({
                        "variation": variation,
                        "query": query,
                        "passed": False,
                        "error": "No response"
                    })
                
                await asyncio.sleep(4)  # Intervalo entre variações
        
        success_rate = (results['passed'] / results['total_variations']) * 100
        self.logger.info(f"\n📊 Resultado Sinônimos: {results['passed']}/{results['total_variations']} ({success_rate:.1f}%)")
        
        return results

    async def test_response_consistency(self) -> Dict:
        """
        🎯 TESTE CRÍTICO 4: Consistência de Respostas
        Testa se o bot é consistente ao responder sobre o mesmo serviço
        """
        self.logger.info("\n🔍 TESTE CRÍTICO 4: Consistência de Respostas")
        
        consistency_tests = [
            "Quanto custa limpeza de pele?",
            "Limpeza de pele, qual o valor?", 
            "Preço da limpeza facial?",
            "Valor do tratamento facial?"
        ]
        
        results = {
            "total_tests": len(consistency_tests),
            "responses": [],
            "consistent": False,
            "all_found_service": True,
            "all_have_price": True
        }
        
        for i, query in enumerate(consistency_tests, 1):
            self.logger.info(f"  📝 Teste {i}/{len(consistency_tests)}: {query}")
            
            await self.send_message(query)
            responses = await self.get_bot_responses()
            
            if responses:
                response_text = " ".join(responses).lower()
                
                # Verificar se encontrou limpeza de pele
                found_service = "limpeza" in response_text and ("pele" in response_text or "facial" in response_text)
                has_price = "80,00" in response_text
                
                if not found_service:
                    results['all_found_service'] = False
                if not has_price:
                    results['all_have_price'] = False
                
                results['responses'].append({
                    "query": query,
                    "response": responses[0] if responses else "",
                    "found_service": found_service,
                    "has_price": has_price
                })
            else:
                results['all_found_service'] = False
                results['all_have_price'] = False
                results['responses'].append({
                    "query": query,
                    "response": "",
                    "found_service": False,
                    "has_price": False
                })
            
            await asyncio.sleep(4)
        
        # Verificar consistência
        results['consistent'] = results['all_found_service'] and results['all_have_price']
        
        if results['consistent']:
            self.logger.info(f"    ✅ CONSISTENTE - Todas as variações encontraram o serviço com preço correto")
        else:
            self.logger.error(f"    ❌ INCONSISTENTE")
            if not results['all_found_service']:
                self.logger.error(f"      - Nem todas encontraram o serviço")
            if not results['all_have_price']:
                self.logger.error(f"      - Nem todas retornaram o preço")
        
        return results

    async def run_comprehensive_fix_test(self):
        """Executa todos os testes de correção"""
        self.logger.info("🚀 INICIANDO TESTE DE CORREÇÕES CONVERSACIONAIS")
        self.logger.info("=" * 60)
        
        try:
            # Conectar ao banco
            if not await self.connect_db():
                self.logger.error("❌ Falha na conexão - abortando")
                return
            
            # Executar testes críticos
            self.logger.info("🎯 Executando testes críticos das correções...")
            
            # Teste 1: Busca de Serviços
            service_search_results = await self.test_service_search_fixes()
            self.results['critical_fixes_verified']['service_search'] = service_search_results
            
            await asyncio.sleep(8)  # Pausa entre testes
            
            # Teste 2: Fluxo Conversacional  
            conversation_results = await self.test_contextual_conversation()
            self.results['critical_fixes_verified']['conversation_flow'] = conversation_results
            
            await asyncio.sleep(8)
            
            # Teste 3: Sinônimos
            synonym_results = await self.test_synonym_recognition()
            self.results['critical_fixes_verified']['synonym_recognition'] = synonym_results
            
            await asyncio.sleep(8)
            
            # Teste 4: Consistência
            consistency_results = await self.test_response_consistency()
            self.results['critical_fixes_verified']['response_consistency'] = consistency_results
            
            # Gerar relatório final
            await self.generate_fix_report()
            
        except Exception as e:
            self.logger.error(f"❌ Erro geral: {e}")
        finally:
            if hasattr(self, 'db'):
                await self.db.close()

    async def generate_fix_report(self):
        """Gera relatório das correções testadas"""
        print("\n" + "="*70)
        print("🎯 RELATÓRIO DE TESTE DAS CORREÇÕES CONVERSACIONAIS")
        print("="*70)
        
        print(f"🆔 Sessão: {self.results['session']}")
        print(f"⏱️  Tempo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Avaliar cada teste crítico
        critical_tests = {
            'service_search': '🔍 Busca de Serviços',
            'conversation_flow': '🗣️ Fluxo Conversacional', 
            'synonym_recognition': '📝 Reconhecimento de Sinônimos',
            'response_consistency': '🎯 Consistência de Respostas'
        }
        
        print(f"\n📊 RESULTADOS DOS TESTES CRÍTICOS:")
        print("-" * 50)
        
        total_tests_passed = 0
        total_tests = 0
        
        for test_key, test_name in critical_tests.items():
            if test_key in self.results['critical_fixes_verified']:
                test_data = self.results['critical_fixes_verified'][test_key]
                
                if test_key == 'response_consistency':
                    # Teste de consistência é booleano
                    passed = 1 if test_data.get('consistent', False) else 0
                    total = 1
                    status = "✅ PASSOU" if passed else "❌ FALHOU"
                else:
                    # Outros testes têm passed/total
                    passed = test_data.get('passed', 0)
                    total = test_data.get('total_tests', test_data.get('total_variations', test_data.get('total_steps', 1)))
                    
                    if total > 0:
                        success_rate = (passed / total) * 100
                        status = "✅ PASSOU" if success_rate >= 70 else "❌ FALHOU"
                    else:
                        success_rate = 0
                        status = "❌ FALHOU"
                
                total_tests_passed += passed
                total_tests += total
                
                print(f"{status} | {test_name}")
                if test_key != 'response_consistency':
                    print(f"    Taxa: {(passed/total)*100:.1f}% ({passed}/{total})")
                else:
                    print(f"    Resultado: {'Consistente' if test_data.get('consistent') else 'Inconsistente'}")
                print()
        
        # Resultado geral
        if total_tests > 0:
            overall_success = (total_tests_passed / total_tests) * 100
        else:
            overall_success = 0
        
        print(f"🎯 RESULTADO GERAL DAS CORREÇÕES:")
        if overall_success >= 85:
            print("   🏆 EXCELENTE! As correções funcionaram perfeitamente!")
            print(f"   ✅ {overall_success:.1f}% dos testes passaram")
            print("   🚀 Problemas de fluxo conversacional resolvidos")
        elif overall_success >= 70:
            print("   👍 MUITO BOM! A maioria das correções funcionou")
            print(f"   ✅ {overall_success:.1f}% dos testes passaram") 
            print("   💡 Algumas melhorias adicionais podem ser feitas")
        elif overall_success >= 50:
            print("   ⚠️ PARCIAL. Algumas correções funcionaram")
            print(f"   🔧 {overall_success:.1f}% dos testes passaram")
            print("   📝 Revise as implementações que falharam")
        else:
            print("   ❌ ATENÇÃO! As correções não funcionaram adequadamente")
            print(f"   🚨 Apenas {overall_success:.1f}% dos testes passaram")
            print("   🔧 Revise as implementações de busca e fluxo")
        
        # Recomendações específicas
        print(f"\n💡 ANÁLISE DETALHADA:")
        
        service_search = self.results['critical_fixes_verified'].get('service_search', {})
        if service_search.get('passed', 0) < service_search.get('total_tests', 1):
            print("  🔍 Busca de Serviços: Ainda há problemas com reconhecimento de serviços")
            print("    → Verifique se a busca flexível foi implementada corretamente")
        
        conversation = self.results['critical_fixes_verified'].get('conversation_flow', {})
        if conversation.get('passed', 0) < conversation.get('total_steps', 1):
            print("  🗣️ Fluxo Conversacional: Contexto ainda sendo perdido")
            print("    → Implemente sistema de memória conversacional")
        
        synonym = self.results['critical_fixes_verified'].get('synonym_recognition', {})
        if synonym.get('passed', 0) < synonym.get('total_variations', 1):
            print("  📝 Sinônimos: Sistema de sinônimos precisa melhorar")
            print("    → Adicione mais variações e sinônimos ao sistema")
        
        consistency = self.results['critical_fixes_verified'].get('response_consistency', {})
        if not consistency.get('consistent', False):
            print("  🎯 Consistência: Respostas ainda inconsistentes")
            print("    → Padronize as respostas para consultas similares")
        
        print("="*70)
        
        # Salvar relatório
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversational_fixes_test_{timestamp}.json"
        
        final_results = {
            **self.results,
            "end_time": datetime.now().isoformat(),
            "overall_success_rate": overall_success,
            "total_tests_passed": total_tests_passed,
            "total_tests": total_tests
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Relatório salvo em: {filename}")


async def main():
    """Função principal"""
    tester = ConversationalFixTester()
    
    try:
        await tester.run_comprehensive_fix_test()
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido")
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔍 TESTE FOCADO - CORREÇÕES CONVERSACIONAIS")
    print("=" * 50)
    print("🎯 Testando especificamente as correções implementadas:")
    print("  • ✅ Busca flexível de serviços (limpeza, massagem, radio)")
    print("  • ✅ Reconhecimento de sinônimos e variações")
    print("  • ✅ Fluxo conversacional com contexto")
    print("  • ✅ Consistência nas respostas")
    print("  • ✅ Eliminação de negações incorretas")
    print()
    print("🚨 PROBLEMAS ANTERIORES QUE ESTAMOS TESTANDO:")
    print("  ❌ 'limpeza de pele' negada mas existia no banco")
    print("  ❌ 'massagem relaxante' negada mas existia no banco")  
    print("  ❌ 'radiofrequência' negada mas existia no banco")
    print("  ❌ Contexto conversacional perdido")
    print("  ❌ Respostas inconsistentes")
    print("=" * 50)
    
    response = input("\n▶️ Executar teste das correções? (ENTER para continuar): ")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Programa finalizado pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro crítico: {e}")
        import traceback
        traceback.print_exc()