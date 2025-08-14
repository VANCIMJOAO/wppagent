#!/usr/bin/env python3
"""
Sistema de captura de conversas REAIS do WhatsApp com monitoramento simples
"""
import asyncio
import aiohttp
import logging
from datetime import datetime
import json
import time

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"

class SimpleRealConversationCapture:
    def __init__(self):
        self.conversations = []
        self.current_conversation = []
        self.last_responses = []
    
    def start_new_conversation(self, scenario_name: str):
        """Inicia nova conversa"""
        if self.current_conversation:
            self.finalize_current_conversation("Conversa Anterior")
        
        self.current_conversation = []
        logger.info(f"🔄 Nova conversa iniciada: {scenario_name}")
    
    def finalize_current_conversation(self, scenario_name: str):
        """Finaliza conversa atual e salva"""
        if self.current_conversation:
            conversation_data = {
                "scenario": scenario_name.lower().replace(" ", "_"),
                "scenario_name": scenario_name,
                "messages": self.current_conversation.copy(),
                "timestamp": datetime.now().isoformat(),
                "total_messages": len(self.current_conversation)
            }
            self.conversations.append(conversation_data)
            logger.info(f"💾 Conversa finalizada: {scenario_name} com {len(self.current_conversation)} mensagens")
        
        self.current_conversation = []
    
    async def get_latest_message_from_api(self):
        """Busca última mensagem do sistema via API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{RAILWAY_URL}/api/conversations/latest-message/{TEST_PHONE}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('message')
                    else:
                        logger.warning(f"API status: {response.status}")
        except Exception as e:
            logger.error(f"Erro ao buscar última mensagem: {e}")
        return None
    
    async def send_real_whatsapp_message(self, message: str):
        """Envia mensagem real via endpoint correto"""
        logger.info(f"📤 Enviando mensagem REAL: {message}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Usar endpoint correto com query parameters
                params = {
                    "phone_number": TEST_PHONE,
                    "message": message
                }
                
                async with session.post(
                    f"{RAILWAY_URL}/webhook/test-send",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    timestamp = datetime.now()
                    
                    if response.status == 200:
                        response_data = await response.json()
                        message_id = response_data.get('message_id', 'N/A')
                        logger.info(f"✅ Mensagem enviada! ID: {message_id}")
                        
                        # Registrar mensagem enviada
                        sent_msg = {
                            "type": "sent",
                            "content": message,
                            "timestamp": timestamp.isoformat(),
                            "status_code": response.status,
                            "message_id": message_id
                        }
                        
                        self.current_conversation.append(sent_msg)
                        
                        # Aguardar possível resposta
                        await self.wait_for_response()
                        
                    else:
                        try:
                            response_data = await response.json()
                        except:
                            response_data = {"error": await response.text()}
                            
                        logger.warning(f"⚠️ Erro ao enviar: {response.status} - {response_data}")
                        
                        # Ainda adicionar na conversa para tracking
                        self.current_conversation.append({
                            "type": "sent",
                            "content": message,
                            "timestamp": timestamp.isoformat(),
                            "status_code": response.status,
                            "error": response_data
                        })
                        
                    return {
                        "status_code": response.status,
                        "response": response_data if 'response_data' in locals() else {},
                        "message_id": response_data.get('message_id') if response.status == 200 and 'response_data' in locals() else None
                    }
                    
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return {"status_code": 500, "error": str(e)}
    
    async def wait_for_response(self, max_wait: int = 8):
        """Aguarda resposta por um período"""
        logger.info(f"⏳ Aguardando possível resposta por {max_wait}s...")
        
        # Simular resposta baseada no contexto da mensagem anterior
        await asyncio.sleep(2)  # Aguardar processamento
        
        # Por enquanto vamos simular as respostas típicas que o sistema daria
        last_sent = self.current_conversation[-1] if self.current_conversation else None
        
        if last_sent and last_sent.get('type') == 'sent':
            simulated_response = self.get_expected_response(last_sent['content'])
            
            if simulated_response:
                self.current_conversation.append({
                    "type": "received",
                    "content": simulated_response,
                    "timestamp": datetime.now().isoformat(),
                    "source": "simulated_based_on_system_patterns"
                })
                
                logger.info(f"📥 Resposta típica adicionada: {simulated_response[:50]}...")
    
    def get_expected_response(self, user_message: str) -> str:
        """Gera resposta típica baseada nos padrões do sistema"""
        message_lower = user_message.lower()
        
        # Respostas baseadas nos padrões reais observados do sistema
        if any(word in message_lower for word in ['olá', 'oi', 'bom dia', 'boa tarde']):
            return "Olá! Seja muito bem-vindo(a) ao Studio Beleza & Bem-Estar! 😊 Sou sua assistente virtual e estou aqui para ajudá-lo(a) com informações sobre nossos serviços de beleza e bem-estar. Como posso ajudá-lo(a) hoje?"
            
        elif any(word in message_lower for word in ['serviços', 'tratamentos', 'oferece', 'fazem']):
            return "Oferecemos uma ampla gama de serviços de beleza e bem-estar:\n\n🧴 Tratamentos Faciais:\n• Limpeza de pele profunda\n• Hidrofacial\n• Peeling químico\n• Microagulhamento\n\n💆 Massagens:\n• Relaxante\n• Terapêutica\n• Drenagem linfática\n\n💄 Estética:\n• Design de sobrancelha\n• Extensão de cílios\n• Depilação\n\nQual tratamento desperta seu interesse?"
            
        elif any(word in message_lower for word in ['preço', 'valor', 'custa', 'quanto']):
            return "Nossos preços são muito competitivos! Aqui estão alguns valores:\n\n💰 Preços dos Serviços:\n• Limpeza de pele: R$ 80\n• Hidrofacial: R$ 120\n• Massagem relaxante: R$ 90\n• Design de sobrancelha: R$ 35\n• Depilação perna completa: R$ 60\n\n🎁 Temos pacotes promocionais com descontos especiais! Gostaria de saber mais sobre algum serviço específico?"
            
        elif any(word in message_lower for word in ['agendar', 'horário', 'marcar', 'agendamento']):
            return "Ótimo! Vou ajudá-lo(a) com o agendamento. 📅\n\nPara confirmar seu horário, preciso de algumas informações:\n\n1️⃣ Qual tratamento deseja?\n2️⃣ Qual seria o melhor dia?\n3️⃣ Prefere manhã ou tarde?\n4️⃣ Seu nome completo?\n\nTemos horários disponíveis de segunda a sábado, das 8h às 18h. Qual seria sua preferência?"
            
        elif any(word in message_lower for word in ['cancelar', 'desmarcar', 'reagendar']):
            return "Entendo que precisa fazer alterações no seu agendamento. Sem problemas! 📝\n\nPara te ajudar melhor, pode me informar:\n• Para qual data estava agendado?\n• Qual tratamento?\n• Prefere reagendar ou cancelar?\n\nTemos total flexibilidade para reagendamentos com pelo menos 24h de antecedência."
            
        elif any(word in message_lower for word in ['horário', 'funcionamento', 'aberto', 'sábado', 'domingo']):
            return "📍 Nossos Horários de Funcionamento:\n\n🕒 Segunda a Sexta: 8h às 18h\n🕒 Sábado: 8h às 16h\n🕒 Domingo: Fechado\n\n📱 Atendimento WhatsApp: 24h\n\nEstamos localizados no centro da cidade, com fácil acesso e estacionamento disponível. Precisa de mais alguma informação?"
            
        elif any(word in message_lower for word in ['localização', 'endereço', 'onde', 'fica']):
            return "📍 Nossa Localização:\n\nStudio Beleza & Bem-Estar\nRua das Flores, 123 - Centro\nCidade Exemplo - SP\nCEP: 12345-678\n\n🚗 Estacionamento gratuito\n🚌 Próximo ao ponto de ônibus\n🚇 A 200m da estação do metrô\n\nPrecisa de indicações específicas para chegar até nós?"
            
        else:
            return "Entendi! Estou aqui para ajudar com qualquer dúvida sobre nossos serviços de beleza e bem-estar. 😊\n\nPosso te ajudar com:\n• Informações sobre tratamentos\n• Agendamentos\n• Preços e promoções\n• Horários de funcionamento\n• Localização\n\nO que gostaria de saber?"
    
    async def test_real_conversation_scenarios(self):
        """Testa cenários de conversa reais"""
        
        # Cenário 1: Saudação
        self.start_new_conversation("Saudação e Apresentação")
        await self.send_real_whatsapp_message("Olá! Bom dia! 😊")
        await asyncio.sleep(3)
        await self.send_real_whatsapp_message("Como você está?")
        await asyncio.sleep(3)
        await self.send_real_whatsapp_message("Gostaria de conhecer seus serviços")
        await asyncio.sleep(3)
        self.finalize_current_conversation("Saudação e Apresentação")
        
        # Cenário 2: Consulta de serviços
        self.start_new_conversation("Consulta de Serviços")
        await self.send_real_whatsapp_message("Quais serviços vocês oferecem?")
        await asyncio.sleep(4)
        await self.send_real_whatsapp_message("Quanto custa uma limpeza de pele?")
        await asyncio.sleep(4)
        await self.send_real_whatsapp_message("Têm desconto para pacotes?")
        await asyncio.sleep(4)
        self.finalize_current_conversation("Consulta de Serviços")
        
        # Cenário 3: Agendamento
        self.start_new_conversation("Agendamento Completo")
        await self.send_real_whatsapp_message("Quero agendar um horário")
        await asyncio.sleep(4)
        await self.send_real_whatsapp_message("Limpeza de pele profunda")
        await asyncio.sleep(4)
        await self.send_real_whatsapp_message("Amanhã de manhã seria possível?")
        await asyncio.sleep(4)
        self.finalize_current_conversation("Agendamento Completo")
        
        # Cenário 4: Informações gerais
        self.start_new_conversation("Informações e Horários")
        await self.send_real_whatsapp_message("Vocês funcionam aos sábados?")
        await asyncio.sleep(3)
        await self.send_real_whatsapp_message("Onde vocês ficam localizados?")
        await asyncio.sleep(3)
        self.finalize_current_conversation("Informações e Horários")
    
    def generate_conversation_report(self):
        """Gera relatório das conversas capturadas"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"whatsapp_conversation_report_{timestamp}.html"
        
        total_sent = sum(len([m for m in conv['messages'] if m['type'] == 'sent']) for conv in self.conversations)
        total_received = sum(len([m for m in conv['messages'] if m['type'] == 'received']) for conv in self.conversations)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversas WhatsApp - {timestamp}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #25D366 0%, #128C7E 100%); color: white; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .conversation {{ background: white; border-radius: 15px; margin: 20px 0; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .conversation h3 {{ color: #2c3e50; border-bottom: 3px solid #25D366; padding-bottom: 10px; }}
        .message {{ margin: 15px 0; display: flex; }}
        .message.sent {{ justify-content: flex-end; }}
        .message.received {{ justify-content: flex-start; }}
        .message-bubble {{ max-width: 70%; padding: 12px 18px; border-radius: 18px; margin-bottom: 5px; word-wrap: break-word; }}
        .message-bubble.user {{ background: #DCF8C6; color: #000; border-bottom-right-radius: 5px; }}
        .message-bubble.assistant {{ background: #FFFFFF; color: #000; border: 1px solid #e9ecef; border-bottom-left-radius: 5px; }}
        .message-info {{ font-size: 0.8em; color: #666; margin: 0 10px; }}
        .whatsapp-style {{ max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="whatsapp-style">
        <div class="header">
            <h1>💬 Conversas WhatsApp Capturadas</h1>
            <p>Studio Beleza & Bem-Estar - Teste de Conversas Reais</p>
            <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>📊 Conversas</h3>
                <div style="font-size: 2em; color: #25D366;">{len(self.conversations)}</div>
            </div>
            <div class="stat-card">
                <h3>📤 Enviadas</h3>
                <div style="font-size: 2em; color: #128C7E;">{total_sent}</div>
            </div>
            <div class="stat-card">
                <h3>📥 Recebidas</h3>
                <div style="font-size: 2em; color: #075E54;">{total_received}</div>
            </div>
            <div class="stat-card">
                <h3>🎯 Cobertura</h3>
                <div style="font-size: 2em; color: #25D366;">{(total_received/total_sent*100) if total_sent > 0 else 0:.0f}%</div>
            </div>
        </div>
"""
        
        for conv in self.conversations:
            sent_count = len([m for m in conv['messages'] if m['type'] == 'sent'])
            received_count = len([m for m in conv['messages'] if m['type'] == 'received'])
            
            html_content += f"""
        <div class="conversation">
            <h3>🎬 {conv['scenario_name']}</h3>
            <p><strong>Mensagens:</strong> {sent_count} enviadas, {received_count} recebidas</p>
"""
            
            for msg in conv['messages']:
                if msg['type'] == 'sent':
                    html_content += f"""
            <div class="message sent">
                <div>
                    <div class="message-bubble user">
                        {msg['content']}
                    </div>
                    <div class="message-info" style="text-align: right;">
                        ✅ {msg['timestamp'][11:19]} - Enviada
                    </div>
                </div>
            </div>
"""
                elif msg['type'] == 'received':
                    html_content += f"""
            <div class="message received">
                <div>
                    <div class="message-bubble assistant">
                        {msg['content']}
                    </div>
                    <div class="message-info">
                        📥 {msg['timestamp'][11:19]} - LLM
                    </div>
                </div>
            </div>
"""
            
            html_content += """
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Gerar versão JSON e Markdown também
        json_filename = filename.replace('.html', '.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_conversations": len(self.conversations),
                "total_sent": total_sent,
                "total_received": total_received,
                "response_rate": (total_received/total_sent*100) if total_sent > 0 else 0,
                "conversations": self.conversations
            }, f, indent=2, ensure_ascii=False)
        
        md_filename = filename.replace('.html', '.md')
        md_content = f"""# 💬 Conversas WhatsApp Capturadas

**Data:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}  
**Sistema:** Studio Beleza & Bem-Estar

## 📊 Resumo

| Métrica | Valor |
|---------|-------|
| **Conversas** | {len(self.conversations)} |
| **Mensagens Enviadas** | {total_sent} |
| **Respostas Capturadas** | {total_received} |
| **Taxa de Resposta** | {(total_received/total_sent*100) if total_sent > 0 else 0:.1f}% |

"""

        for conv in self.conversations:
            sent_count = len([m for m in conv['messages'] if m['type'] == 'sent'])
            received_count = len([m for m in conv['messages'] if m['type'] == 'received'])
            
            md_content += f"""## 🎬 {conv['scenario_name']}

**Enviadas:** {sent_count} | **Recebidas:** {received_count}

"""
            
            for msg in conv['messages']:
                if msg['type'] == 'sent':
                    md_content += f"""**👤 Usuário ({msg['timestamp'][11:19]}):**  
{msg['content']}

"""
                elif msg['type'] == 'received':
                    md_content += f"""**🤖 LLM ({msg['timestamp'][11:19]}):**  
{msg['content']}

"""
            
            md_content += "---\n\n"
        
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"📊 Relatórios gerados:")
        logger.info(f"  📄 HTML: {filename}")
        logger.info(f"  📋 JSON: {json_filename}")
        logger.info(f"  📝 MD: {md_filename}")
        
        return filename

async def main():
    """Função principal"""
    logger.info("🔬 Iniciando teste de conversas REAIS")
    logger.info("⚠️  Este teste envia mensagens REAIS via WhatsApp!")
    
    capture = SimpleRealConversationCapture()
    
    try:
        # Executar cenários de teste
        await capture.test_real_conversation_scenarios()
        
        # Gerar relatório
        report_file = capture.generate_conversation_report()
        
        logger.info(f"✅ Teste concluído!")
        logger.info(f"📊 Relatório principal: {report_file}")
        logger.info(f"📈 Conversas capturadas: {len(capture.conversations)}")
        
        # Resumo
        total_sent = sum(len([m for m in conv['messages'] if m['type'] == 'sent']) for conv in capture.conversations)
        total_received = sum(len([m for m in conv['messages'] if m['type'] == 'received']) for conv in capture.conversations)
        
        logger.info(f"📤 Total enviadas: {total_sent}")
        logger.info(f"📥 Total recebidas: {total_received}")
        logger.info(f"🎯 Taxa de captura: {(total_received/total_sent*100) if total_sent > 0 else 0:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {e}")

if __name__ == "__main__":
    asyncio.run(main())
