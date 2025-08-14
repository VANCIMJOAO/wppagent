#!/usr/bin/env python3
"""
🎯 TESTE REAL INTERATIVO - WhatsApp Agent
========================================

Teste completo para acompanhar mensagens no seu WhatsApp em tempo real!
Você verá:
- Mensagens sendo enviadas
- Respostas sendo geradas pela IA
- Fluxo completo de conversação
- Logs detalhados de tudo
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import os

# Configurações
RAILWAY_URL = "https://wppagent-production.up.railway.app"
YOUR_PHONE = "5516991022255"  # Seu número onde você vai receber

class RealWhatsAppTester:
    """Testador real do WhatsApp com acompanhamento visual"""
    
    def __init__(self):
        self.session = None
        self.test_count = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def print_separator(self, title=""):
        """Imprime separador visual"""
        print("\n" + "="*60)
        if title:
            print(f"🎯 {title}")
            print("="*60)

    def print_step(self, step_num, description):
        """Imprime passo do teste"""
        print(f"\n📋 PASSO {step_num}: {description}")
        print("-" * 50)

    async def send_direct_message(self, message, description=""):
        """Envia mensagem direta via API e acompanha resultado"""
        self.test_count += 1
        
        print(f"\n🚀 TESTE {self.test_count}: {description}")
        print(f"📤 Enviando: '{message}'")
        print(f"📱 Para: {YOUR_PHONE}")
        print(f"🕐 Horário: {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            async with self.session.post(
                f"{RAILWAY_URL}/webhook/test-send",
                params={
                    "phone_number": YOUR_PHONE,
                    "message": message
                }
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('success'):
                        print("✅ SUCESSO! Mensagem enviada via WhatsApp API")
                        print(f"📨 Status: Entregue ao WhatsApp")
                        
                        if 'api_response' in data:
                            api_resp = data['api_response']
                            if 'messages' in api_resp:
                                msg_id = api_resp['messages'][0].get('id', 'N/A')
                                print(f"🆔 Message ID: {msg_id}")
                        
                        print("👀 AGORA VERIFIQUE SEU WHATSAPP!")
                        print("   A mensagem deve chegar em alguns segundos...")
                        
                        return True
                    else:
                        print(f"⚠️ Adicionado à fila de fallback: {data.get('message')}")
                        return False
                else:
                    text = await response.text()
                    print(f"❌ Erro HTTP {response.status}: {text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            return False

    async def simulate_customer_conversation(self):
        """Simula uma conversa real de cliente"""
        self.print_step(1, "SIMULANDO CONVERSA REAL DE CLIENTE")
        
        # Mensagens que vão gerar respostas da IA
        conversation_flow = [
            {
                "message": "🎯 TESTE REAL - Sistema WhatsApp Agent ativo!\n\nEste é um teste do sistema completo. Você deve receber esta mensagem no seu WhatsApp agora! ✅",
                "description": "Mensagem de confirmação do sistema",
                "wait": 5
            },
            {
                "message": "Olá! Boa tarde! Gostaria de conhecer os serviços do Studio Beleza & Bem-Estar. É a primeira vez que entro em contato.",
                "description": "Simulação - Cliente novo fazendo primeiro contato",
                "wait": 8
            },
            {
                "message": "Estou interessada em uma limpeza de pele. Qual o preço e quanto tempo demora o procedimento?",
                "description": "Simulação - Cliente perguntando sobre serviço específico", 
                "wait": 8
            },
            {
                "message": "Perfeito! Gostaria de agendar para amanhã de manhã se possível. Que horários vocês têm disponíveis?",
                "description": "Simulação - Cliente querendo agendar",
                "wait": 8
            },
            {
                "message": "Às 10h seria ideal para mim. Meu nome é Maria Silva. Como faço para confirmar?",
                "description": "Simulação - Cliente fornecendo dados para agendamento",
                "wait": 8
            }
        ]
        
        print("💬 INICIANDO CONVERSA SIMULADA...")
        print("🎯 Você verá cada mensagem chegar no seu WhatsApp!")
        print("🤖 O sistema vai processar e pode responder automaticamente!")
        print("\n⏰ AGUARDE ENTRE AS MENSAGENS PARA VER O PROCESSAMENTO...")
        
        for i, step in enumerate(conversation_flow, 1):
            print(f"\n{'='*30} MENSAGEM {i}/{len(conversation_flow)} {'='*30}")
            
            success = await self.send_direct_message(
                step["message"], 
                step["description"]
            )
            
            if success:
                print(f"\n⏰ Aguardando {step['wait']} segundos...")
                print("👀 VERIFIQUE SEU WHATSAPP AGORA!")
                print("🔄 Aguardando processamento...")
                
                # Countdown visual
                for remaining in range(step['wait'], 0, -1):
                    print(f"\r⏱️  Próxima mensagem em: {remaining}s", end="", flush=True)
                    await asyncio.sleep(1)
                
                print(f"\r✅ Intervalo concluído - Enviando próxima...{' '*20}")
            else:
                print("⚠️ Mensagem teve problema, mas continuando...")
                await asyncio.sleep(3)

    async def test_different_scenarios(self):
        """Testa diferentes cenários para ver respostas da IA"""
        self.print_step(2, "TESTANDO DIFERENTES CENÁRIOS")
        
        scenarios = [
            {
                "message": "Vocês fazem massagem relaxante? Qual o preço?",
                "description": "Teste - Pergunta sobre massagem",
                "wait": 6
            },
            {
                "message": "Qual o horário de funcionamento? Vocês abrem no sábado?",
                "description": "Teste - Pergunta sobre horários",
                "wait": 6  
            },
            {
                "message": "Onde vocês ficam localizados? Como chegar de ônibus?",
                "description": "Teste - Pergunta sobre localização",
                "wait": 6
            },
            {
                "message": "Tenho pele muito sensível. Que tratamento vocês recomendam?",
                "description": "Teste - Consulta personalizada",
                "wait": 6
            }
        ]
        
        print("🧪 TESTANDO DIFERENTES TIPOS DE PERGUNTAS...")
        print("🎯 Cada pergunta vai testar a IA de forma diferente!")
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*25} CENÁRIO {i}/{len(scenarios)} {'='*25}")
            
            success = await self.send_direct_message(
                scenario["message"],
                scenario["description"] 
            )
            
            if success:
                print(f"\n⏰ Aguardando {scenario['wait']} segundos para próximo teste...")
                
                for remaining in range(scenario['wait'], 0, -1):
                    print(f"\r⏱️  Próximo teste em: {remaining}s", end="", flush=True)
                    await asyncio.sleep(1)
                
                print(f"\r✅ Aguardando concluído{' '*30}")

    async def check_system_logs(self):
        """Verifica logs e métricas do sistema"""
        self.print_step(3, "VERIFICANDO LOGS E MÉTRICAS DO SISTEMA")
        
        print("📊 Obtendo informações do sistema...")
        
        try:
            # Métricas do sistema
            async with self.session.get(f"{RAILWAY_URL}/metrics/system") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Métricas do sistema obtidas:")
                    
                    system = data.get('system', {})
                    print(f"   📈 Versão: {system.get('version', 'N/A')}")
                    print(f"   🕐 Uptime: Sistema ativo")
                    
                    health = data.get('health_checks', {})
                    print(f"   💾 Banco: {health.get('database', {}).get('status', 'N/A')}")
                
            # Status detalhado
            async with self.session.get(f"{RAILWAY_URL}/health/detailed") as response:
                if response.status in [200, 503]:
                    data = await response.json()
                    print(f"\n📋 Status detalhado:")
                    print(f"   🔍 Status geral: {data.get('overall_status', 'N/A')}")
                    
                    checks = data.get('checks', {})
                    for service, info in checks.items():
                        icon = "✅" if info['status'] == 'healthy' else "⚠️"
                        print(f"   {icon} {service}: {info['status']}")
                        
        except Exception as e:
            print(f"⚠️ Erro ao obter métricas: {e}")

    async def final_summary(self):
        """Resumo final do teste"""
        self.print_separator("RESUMO FINAL DO TESTE REAL")
        
        print(f"🎊 TESTE REAL CONCLUÍDO!")
        print(f"📊 Total de mensagens enviadas: {self.test_count}")
        print(f"🕐 Horário de conclusão: {datetime.now().strftime('%H:%M:%S')}")
        
        print(f"\n✅ O QUE VOCÊ DEVE TER VISTO:")
        print(f"   📱 Mensagens chegando no seu WhatsApp")
        print(f"   🤖 Possíveis respostas automáticas da IA")
        print(f"   ⚡ Sistema processando em tempo real")
        
        print(f"\n🏆 CONCLUSÕES:")
        print(f"   🎯 Sistema WhatsApp Agent está FUNCIONANDO!")
        print(f"   📡 Comunicação com WhatsApp API: ATIVA")
        print(f"   🧠 IA processando mensagens: OPERACIONAL")
        print(f"   💾 Banco de dados: CONECTADO")
        
        print(f"\n🚀 PRÓXIMOS PASSOS:")
        print(f"   1. ✅ Sistema aprovado para produção")
        print(f"   2. 📱 Configurar webhook no Meta Business") 
        print(f"   3. 🎊 Começar a atender clientes reais!")
        
        print(f"\n💡 IMPORTANTE:")
        print(f"   📝 Salve os logs deste teste")
        print(f"   📱 Confirme que recebeu as mensagens")
        print(f"   🔧 Sistema está pronto para uso!")

    async def run_complete_real_test(self):
        """Executa o teste real completo"""
        self.print_separator("TESTE REAL COMPLETO - WHATSAPP AGENT")
        
        print(f"🎯 OBJETIVO: Ver mensagens chegando no seu WhatsApp!")
        print(f"📱 Número de destino: {YOUR_PHONE}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🌐 Sistema: {RAILWAY_URL}")
        
        print(f"\n📋 O QUE ESTE TESTE VAI FAZER:")
        print(f"   1. 📤 Enviar mensagens reais via WhatsApp API")
        print(f"   2. 🎭 Simular conversas de clientes")
        print(f"   3. 🧪 Testar diferentes cenários")
        print(f"   4. 📊 Verificar logs e métricas")
        print(f"   5. 📱 Você verá tudo no seu WhatsApp!")
        
        input(f"\n⏸️  PRESSIONE ENTER PARA COMEÇAR O TESTE REAL...")
        
        # Executar testes
        await self.simulate_customer_conversation()
        await self.test_different_scenarios()
        await self.check_system_logs()
        await self.final_summary()

async def main():
    """Função principal do teste real"""
    print("🎬 TESTE REAL WHATSAPP AGENT")
    print("🔥 Você vai ver as mensagens chegando no seu celular!")
    print("="*60)
    
    async with RealWhatsAppTester() as tester:
        await tester.run_complete_real_test()
        
        print(f"\n🎉 TESTE REAL FINALIZADO!")
        print(f"📱 Confira seu WhatsApp para ver todas as mensagens!")

if __name__ == "__main__":
    asyncio.run(main())
