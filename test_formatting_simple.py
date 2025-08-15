#!/usr/bin/env python3
"""
🎨 TESTE SIMPLES - Formatação WhatsApp
====================================
Testa especificamente as melhorias de formatação implementadas:
- Formatação de serviços com emojis e numeração
- Formatação de horários de funcionamento
- Formatação de informações da empresa
"""

import asyncio
import asyncpg
import aiohttp
import time
from datetime import datetime, timedelta
import logging
import json
import random

class SimpleFormattingTester:
    def __init__(self):
        # CONFIGURAÇÕES
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        
        # CREDENCIAIS
        self.YOUR_PHONE = "5516991022255"
        self.WHATSAPP_PHONE_ID = "728348237027885"
        self.BOT_PHONE = "15551536026"
        
        # CENÁRIOS ESPECÍFICOS PARA TESTAR FORMATAÇÃO
        self.formatting_tests = [
            {
                "name": "📋 Teste Lista de Serviços",
                "message": "Quais serviços vocês oferecem?",
                "expected_formatting": [
                    "1.", "2.", "3.",  # Numeração
                    "💰", "⏰",  # Emojis de preço e duração
                    "*",  # Negrito para nomes
                    "_"   # Itálico para descrições
                ]
            },
            {
                "name": "🕘 Teste Horário de Funcionamento",
                "message": "Qual o horário de funcionamento?",
                "expected_formatting": [
                    "🕘", "🚫",  # Emojis de aberto/fechado
                    "Segunda", "Domingo",  # Dias da semana
                    "às"  # Formatação de horários
                ]
            },
            {
                "name": "🏢 Teste Informações da Empresa",
                "message": "Onde vocês ficam? Qual o endereço?",
                "expected_formatting": [
                    "🏢", "📍", "📞", "📧", "🌐",  # Emojis da empresa
                    "Studio", "Beleza"  # Nome da empresa
                ]
            },
            {
                "name": "💰 Teste Consulta de Preços",
                "message": "Quanto custa uma limpeza de pele?",
                "expected_formatting": [
                    "💰", "R$",  # Emojis e símbolo de preço
                    "⏰",  # Emoji de duração
                    "*"  # Negrito para destaque
                ]
            }
        ]
        
        self.session_id = f"formatting_test_{int(time.time())}"
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        self.results = {
            "session": self.session_id,
            "start_time": datetime.now().isoformat(),
            "tests_run": 0,
            "formatting_checks_passed": 0,
            "test_details": []
        }

    async def connect_db(self):
        """Conecta ao banco"""
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            self.logger.info("✅ Conectado ao banco PostgreSQL")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar: {e}")
            return False

    async def send_message(self, message: str):
        """Envia mensagem para o bot"""
        try:
            webhook_url = f"{self.API_BASE_URL}/webhook"
            
            webhook_payload = {
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
                                "id": f"wamid.format_test_{int(time.time())}{random.randint(100,999)}",
                                "timestamp": str(int(time.time())),
                                "text": {"body": message},
                                "type": "text"
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
                async with session.post(webhook_url, json=webhook_payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        self.logger.info(f"✅ Mensagem enviada: '{message}'")
                        return True
                    else:
                        response_text = await response.text()
                        self.logger.error(f"❌ Falha no webhook: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Erro no envio: {e}")
            return False

    async def get_bot_response(self, timeout=15):
        """Captura resposta do bot"""
        self.logger.info("⏳ Aguardando resposta do bot...")
        await asyncio.sleep(3)  # Dar tempo para processar
        
        cutoff_time = datetime.now() - timedelta(seconds=30)
        
        for attempt in range(int(timeout / 2)):
            try:
                response = await self.db.fetchrow("""
                    SELECT content, created_at
                    FROM messages 
                    WHERE user_id = 2 
                    AND direction = 'out'
                    AND created_at > $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, cutoff_time)
                
                if response:
                    self.logger.info(f"🤖 Resposta recebida: {len(response['content'])} caracteres")
                    return response['content']
                
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"❌ Erro ao buscar resposta: {e}")
                break
        
        self.logger.warning("⚠️ Nenhuma resposta recebida no tempo limite")
        return None

    def check_formatting(self, response: str, expected_elements: list) -> dict:
        """Verifica se a resposta contém os elementos de formatação esperados"""
        formatting_results = {
            "total_expected": len(expected_elements),
            "found": [],
            "missing": [],
            "score": 0
        }
        
        if not response:
            return formatting_results
        
        for element in expected_elements:
            if element in response:
                formatting_results["found"].append(element)
            else:
                formatting_results["missing"].append(element)
        
        formatting_results["score"] = (len(formatting_results["found"]) / len(expected_elements)) * 100
        
        return formatting_results

    async def run_formatting_test(self, test_data: dict):
        """Executa um teste específico de formatação"""
        self.logger.info(f"\n{test_data['name']}")
        self.logger.info(f"📨 Enviando: {test_data['message']}")
        
        test_result = {
            "test_name": test_data['name'],
            "message_sent": test_data['message'],
            "response_received": None,
            "formatting_check": None,
            "success": False
        }
        
        # Enviar mensagem
        if await self.send_message(test_data['message']):
            # Capturar resposta
            response = await self.get_bot_response()
            
            if response:
                test_result["response_received"] = response
                
                # Verificar formatação
                formatting_check = self.check_formatting(response, test_data['expected_formatting'])
                test_result["formatting_check"] = formatting_check
                
                # Mostrar resultados
                self.logger.info(f"📊 Formatação: {formatting_check['score']:.1f}% ({len(formatting_check['found'])}/{formatting_check['total_expected']})")
                
                if formatting_check['found']:
                    self.logger.info(f"✅ Elementos encontrados: {', '.join(formatting_check['found'])}")
                
                if formatting_check['missing']:
                    self.logger.warning(f"❌ Elementos faltando: {', '.join(formatting_check['missing'])}")
                
                # Mostrar preview da resposta
                preview = response[:200] + "..." if len(response) > 200 else response
                self.logger.info(f"📝 Preview: {preview}")
                
                # Considerar sucesso se >= 70% dos elementos estão presentes
                if formatting_check['score'] >= 70:
                    test_result["success"] = True
                    self.results["formatting_checks_passed"] += 1
                    self.logger.info("🎉 TESTE PASSOU!")
                else:
                    self.logger.warning("⚠️ Formatação pode ser melhorada")
            else:
                self.logger.error("❌ Nenhuma resposta recebida")
        
        self.results["test_details"].append(test_result)
        self.results["tests_run"] += 1
        
        return test_result["success"]

    async def run_all_formatting_tests(self):
        """Executa todos os testes de formatação"""
        self.logger.info("🎨 INICIANDO TESTE DE FORMATAÇÃO")
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 {len(self.formatting_tests)} testes de formatação")
        self.logger.info("=" * 60)
        
        if not await self.connect_db():
            return False
        
        passed_tests = 0
        
        for i, test_data in enumerate(self.formatting_tests, 1):
            self.logger.info(f"\n📍 TESTE {i}/{len(self.formatting_tests)}")
            
            success = await self.run_formatting_test(test_data)
            if success:
                passed_tests += 1
            
            # Intervalo entre testes
            if i < len(self.formatting_tests):
                self.logger.info("⏳ Aguardando 8s antes do próximo teste...")
                await asyncio.sleep(8)
        
        # Relatório final
        await self.generate_report(passed_tests)
        
        return True

    async def generate_report(self, passed_tests: int):
        """Gera relatório final"""
        end_time = datetime.now()
        duration = (end_time - datetime.fromisoformat(self.results["start_time"])).total_seconds()
        
        print("\n" + "="*70)
        print("🎨 RELATÓRIO - TESTE DE FORMATAÇÃO WHATSAPP")
        print("="*70)
        
        print(f"🆔 Sessão: {self.results['session']}")
        print(f"⏱️  Duração: {duration:.1f}s")
        print(f"📱 Usuário: {self.YOUR_PHONE}")
        
        print(f"\n📊 RESULTADOS:")
        print(f"  🎯 Testes executados: {self.results['tests_run']}")
        print(f"  ✅ Testes aprovados: {passed_tests}")
        print(f"  ❌ Testes reprovados: {self.results['tests_run'] - passed_tests}")
        print(f"  📈 Taxa de sucesso: {(passed_tests/self.results['tests_run']*100):.1f}%")
        
        print(f"\n📋 DETALHES POR TESTE:")
        print("-" * 50)
        
        for test in self.results['test_details']:
            status = "✅ PASSOU" if test['success'] else "❌ FALHOU"
            print(f"{status} | {test['test_name']}")
            
            if test['formatting_check']:
                score = test['formatting_check']['score']
                found = len(test['formatting_check']['found'])
                total = test['formatting_check']['total_expected']
                print(f"    Formatação: {score:.1f}% ({found}/{total})")
                
                if test['formatting_check']['found']:
                    print(f"    ✅ Encontrados: {', '.join(test['formatting_check']['found'])}")
                
                if test['formatting_check']['missing']:
                    print(f"    ❌ Faltando: {', '.join(test['formatting_check']['missing'])}")
            print()
        
        # Resultado final
        success_rate = (passed_tests / self.results['tests_run']) * 100
        
        print(f"🎯 RESULTADO FINAL:")
        if success_rate >= 80:
            print("   🎉 EXCELENTE! A formatação está funcionando muito bem!")
            print(f"   ✅ {success_rate:.1f}% dos testes passaram")
        elif success_rate >= 60:
            print("   👍 BOM! A formatação está adequada")
            print(f"   ✅ {success_rate:.1f}% dos testes passaram")
            print("   💡 Algumas melhorias podem ser feitas")
        else:
            print("   ⚠️ ATENÇÃO! A formatação precisa de ajustes")
            print(f"   ❌ Apenas {success_rate:.1f}% dos testes passaram")
        
        print("="*70)
        
        # Salvar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"formatting_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Resultados salvos: {filename}")

    async def close(self):
        """Fecha conexões"""
        try:
            if hasattr(self, 'db'):
                await self.db.close()
                self.logger.info("✅ Conexão fechada")
        except Exception as e:
            self.logger.error(f"❌ Erro ao fechar: {e}")


async def main():
    """Função principal"""
    tester = SimpleFormattingTester()
    
    try:
        await tester.run_all_formatting_tests()
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.close()


if __name__ == "__main__":
    print("🎨 TESTE SIMPLES - Formatação WhatsApp")
    print("=" * 50)
    print("🎯 Este teste verificará:")
    print("  • Formatação de lista de serviços (emojis, numeração)")
    print("  • Formatação de horários de funcionamento")
    print("  • Formatação de informações da empresa")
    print("  • Formatação de consultas de preços")
    print()
    print("📊 Critérios de aprovação:")
    print("  • ≥70% dos elementos de formatação presentes")
    print("  • Emojis, numeração e formatação de texto")
    print("=" * 50)
    
    response = input("\n▶️ Executar teste de formatação? (ENTER para continuar): ")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Programa finalizado")
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
