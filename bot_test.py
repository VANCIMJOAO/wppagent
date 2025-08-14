#!/usr/bin/env python3
"""
🔄 TESTE REAL CORRIGIDO - WhatsApp LLM
====================================
VOCÊ envia → BOT responde (fluxo correto)
"""

import asyncio
import asyncpg
import aiohttp
import time
from datetime import datetime, timedelta
import logging
import json

class RealWhatsAppTesterCorrected:
    def __init__(self):
        # CONFIGURAÇÕES CORRETAS
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self.API_BASE_URL = "https://wppagent-production.up.railway.app"
        
        # SUAS CREDENCIAIS
        self.META_ACCESS_TOKEN = "EAAI4WnfpZAe0BPArVTSZAtZBeVO6qBtBZAmLxiD67HFhIUZAV7L5Ei5qUs5NK7ZBBuOYzi25lnLK1CsfC32EK7OMwnzz3670LQey0ZCKVZBeqURNrKrEIMZAyYruTSy5C9DHL1GkDM9zSxh8g4GyZBU6kCt1v4iTJZBLGGEF5t57vfKZAwu2Tq4ecn1FtqXAtA1jeZAeGZCzFBhtAok2uMd4xx1oZBtKfWRd9wLRksC5rdj25ZB9HRIA91wAEgArmPw2KXcZD"
        self.WHATSAPP_PHONE_ID = "728348237027885"
        self.BOT_PHONE = "15551536026"  # Número do BOT (para onde você envia)
        self.YOUR_PHONE = "5516991022255"  # SEU número (quem envia)
        
        # Mensagens de teste
        self.TEST_MESSAGES = [
            "Teste automatizado - Oi!",
            "Quanto custa um corte?",
            "Qual o horário de funcionamento?"
        ]
        
        self.session_id = f"corrected_test_{int(time.time())}"
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        self.results = {
            "session": self.session_id,
            "start_time": datetime.now().isoformat(),
            "messages_sent": 0,
            "bot_responses": 0,
            "conversation_log": [],
            "webhook_tests": []
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

    async def simulate_user_message_via_webhook(self, message: str):
        """Simula VOCÊ enviando mensagem para o BOT via webhook"""
        try:
            webhook_url = f"{self.API_BASE_URL}/webhook"
            
            # Payload que simula WhatsApp enviando SUA mensagem para o bot
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
                                "from": self.YOUR_PHONE,  # SUA mensagem
                                "id": f"wamid.test_{int(time.time())}{hash(message) % 1000}",
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
                        self.logger.info(f"✅ Webhook simulado - VOCÊ: '{message}'")
                        
                        self.results["messages_sent"] += 1
                        self.results["conversation_log"].append({
                            "type": "user_sent",
                            "content": message,
                            "timestamp": datetime.now().isoformat(),
                            "method": "webhook_simulation"
                        })
                        
                        return True
                    else:
                        response_text = await response.text()
                        self.logger.error(f"❌ Webhook falhou: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Erro webhook: {e}")
            return False

    async def monitor_bot_responses(self, timeout=30):
        """Monitora respostas do bot no banco com abordagem melhorada"""
        start_time = time.time()
        
        # Primeiro, aguardar um pouco para a mensagem ser processada
        await asyncio.sleep(2)
        
        # Agora vamos procurar mensagens criadas nos últimos 60 segundos
        cutoff_time = datetime.now() - timedelta(seconds=60)
        
        self.logger.info(f"� Buscando respostas do bot dos últimos 60s...")
        
        detected_responses = []
        check_count = 0
        max_checks = int(timeout / 3)
        
        while check_count < max_checks:
            try:
                # Buscar mensagens recentes do bot (direction = 'out')
                recent_responses = await self.db.fetch("""
                    SELECT direction, content, created_at, message_type
                    FROM messages 
                    WHERE user_id = 2 
                    AND direction = 'out'
                    AND created_at > $1
                    ORDER BY created_at DESC
                """, cutoff_time)
                
                self.logger.info(f"🔍 Check {check_count + 1}/{max_checks}: Encontradas {len(recent_responses)} respostas do bot")
                
                # Verificar se há novas respostas que não foram detectadas ainda
                for msg in recent_responses:
                    # Verificar se já foi detectada antes
                    already_detected = any(
                        resp['timestamp'] == msg['created_at'].isoformat() 
                        for resp in detected_responses
                    )
                    
                    if not already_detected:
                        response_data = {
                            "content": msg['content'],
                            "timestamp": msg['created_at'].isoformat(),
                            "type": msg['message_type'] if msg['message_type'] else 'text'
                        }
                        
                        detected_responses.append(response_data)
                        self.results["bot_responses"] += 1
                        self.results["conversation_log"].append({
                            "type": "bot_response",
                            "content": msg['content'],
                            "timestamp": msg['created_at'].isoformat()
                        })
                        
                        self.logger.info(f"🤖 NOVA RESPOSTA DETECTADA: {msg['content'][:80]}...")
                
                check_count += 1
                
                if detected_responses:
                    self.logger.info(f"✅ Total de {len(detected_responses)} resposta(s) detectada(s) até agora")
                
                await asyncio.sleep(3)
                
            except (KeyboardInterrupt, asyncio.CancelledError):
                self.logger.info("⏹️ Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"❌ Erro no monitoramento: {e}")
                break
        
        self.logger.info(f"🔍 Final: Total de {len(detected_responses)} resposta(s) detectada(s)")
        return detected_responses

    async def get_message_count(self):
        """Conta mensagens do usuário"""
        try:
            # Usar diretamente user_id = 2 para evitar problemas de JOIN
            count = await self.db.fetchval(
                "SELECT COUNT(*) FROM messages WHERE user_id = 2"
            ) or 0
            return count
        except Exception as e:
            self.logger.error(f"❌ Erro ao contar mensagens: {e}")
            return 0

    async def run_corrected_test(self):
        """Executa teste corrigido VOCÊ → BOT"""
        self.logger.info("🚀 INICIANDO TESTE CORRIGIDO - VOCÊ → BOT")
        self.logger.info("=" * 60)
        
        try:
            # 1. Conectar ao banco
            if not await self.connect_db():
                return False
            
            # 2. Status inicial
            initial_count = await self.get_message_count()
            self.logger.info(f"📊 Mensagens iniciais no banco: {initial_count}")
            self.logger.info(f"👤 Seu número: {self.YOUR_PHONE}")
            self.logger.info(f"🤖 Bot número: {self.BOT_PHONE}")
            
            # 3. Executar testes
            for i, message in enumerate(self.TEST_MESSAGES, 1):
                try:
                    self.logger.info(f"📱 TESTE {i}/{len(self.TEST_MESSAGES)}")
                    self.logger.info(f"Simulando VOCÊ enviando: {message}")
                    
                    # Simular você enviando via webhook
                    success = await self.simulate_user_message_via_webhook(message)
                    
                    if success:
                        # Monitorar resposta do bot com mais tempo
                        responses = await self.monitor_bot_responses(timeout=30)
                        
                        if responses:
                            self.logger.info(f"✅ {len(responses)} resposta(s) do bot detectada(s)")
                            for resp in responses:
                                self.logger.info(f"   💬 {resp['content'][:100]}...")
                        else:
                            self.logger.warning("⚠️ Bot não respondeu neste ciclo")
                    
                    # Intervalo entre mensagens maior para garantir processamento
                    if i < len(self.TEST_MESSAGES):
                        self.logger.info("⏳ Aguardando 15s antes da próxima...")
                        await asyncio.sleep(15)
                        
                except (KeyboardInterrupt, asyncio.CancelledError):
                    self.logger.info("⏹️ Teste interrompido pelo usuário")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Erro no teste {i}: {e}")
                    continue
            
            # 4. Relatório final
            await self.generate_final_report()
            
            self.logger.info("✅ TESTE CORRIGIDO CONCLUÍDO!")
            return True
            
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.logger.info("⏹️ Teste principal interrompido pelo usuário")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erro geral no teste: {e}")
            return False

    async def generate_final_report(self):
        """Gera relatório final"""
        end_time = datetime.now()
        duration = (end_time - datetime.fromisoformat(self.results["start_time"])).total_seconds()
        
        print("\n" + "="*70)
        print("🎉 RELATÓRIO FINAL - TESTE CORRIGIDO")
        print("="*70)
        
        print(f"🆔 Sessão: {self.results['session']}")
        print(f"📱 Fluxo: VOCÊ ({self.YOUR_PHONE}) → BOT ({self.BOT_PHONE})")
        print(f"⏱️  Duração: {duration:.1f}s")
        print(f"📤 Mensagens enviadas (webhook): {self.results['messages_sent']}")
        print(f"🤖 Respostas do bot: {self.results['bot_responses']}")
        
        if self.results['messages_sent'] > 0:
            response_rate = (self.results['bot_responses'] / self.results['messages_sent']) * 100
            print(f"📈 Taxa de resposta: {response_rate:.1f}%")
        
        print(f"\n💬 CONVERSA SIMULADA:")
        print("-" * 50)
        
        for entry in self.results['conversation_log']:
            if entry['type'] == 'user_sent':
                print(f"👤 VOCÊ: {entry['content']}")
                print(f"   ⏰ {entry['timestamp']}")
            elif entry['type'] == 'bot_response':
                print(f"🤖 BOT: {entry['content']}")
                print(f"   ⏰ {entry['timestamp']}")
            print()
        
        # Análise final
        print("🎯 RESULTADO:")
        if self.results['bot_responses'] > 0:
            print("   🎉 SEU BOT ESTÁ FUNCIONANDO!")
            print(f"   ✅ {self.results['bot_responses']} respostas automáticas")
            print("   🚀 Webhook processando corretamente")
        else:
            print("   ⚠️  Bot não respondeu automaticamente")
            print("   🔍 Webhook pode estar processando, mas LLM inativo")
        
        print("="*70)
        
        # Salvar dados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"corrected_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Dados salvos: {filename}")

    async def close(self):
        """Fecha conexões"""
        try:
            if hasattr(self, 'db'):
                await self.db.close()
                self.logger.info("✅ Conexão do banco fechada")
        except Exception as e:
            self.logger.error(f"❌ Erro ao fechar: {e}")


async def main():
    """Função principal"""
    tester = RealWhatsAppTesterCorrected()
    
    try:
        await tester.run_corrected_test()
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n⏹️ Teste interrompido")
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.close()


if __name__ == "__main__":
    print("🔄 TESTE CORRIGIDO - WhatsApp LLM")
    print("=" * 50)
    print("👤 VOCÊ (5516991022255) → 🤖 BOT (16991022255)")
    print("📝 Simula webhook de você enviando para o bot")
    print("👀 Monitora respostas automáticas da LLM")
    print("=" * 50)
    
    response = input("\n▶️ Executar teste corrigido? (ENTER para continuar): ")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Programa finalizado")
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        import traceback
        traceback.print_exc()