#!/usr/bin/env python3
"""
Teste simples para verificar captura de conversas
"""
import asyncio
import aiohttp
import logging
from datetime import datetime
import json

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
RAILWAY_URL = "https://wppagent-production.up.railway.app"
TEST_PHONE = "5516991022255"

class ConversationCaptureTester:
    def __init__(self):
        self.conversations = []
        self.current_conversation = []
        
    def get_contextual_llm_response(self, user_message: str) -> str:
        """Gera resposta contextual da LLM baseada na mensagem do usuário"""
        message_lower = user_message.lower()
        
        # Mapeamento de respostas contextuais
        if any(word in message_lower for word in ['olá', 'oi', 'bom dia', 'boa tarde']):
            return "Olá! Seja muito bem-vindo(a) ao Studio Beleza & Bem-Estar! 😊 Como posso ajudá-lo(a) hoje?"
        elif any(word in message_lower for word in ['serviços', 'tratamentos', 'oferece']):
            return "Oferecemos diversos tratamentos: limpeza de pele, hidrofacial, massagem relaxante, design de sobrancelha e muito mais! Qual serviço tem interesse?"
        elif any(word in message_lower for word in ['preço', 'valor', 'custa', 'quanto']):
            return "Nossos preços variam conforme o tratamento. Limpeza de pele: R$ 80, Hidrofacial: R$ 120, Massagem: R$ 90. Temos pacotes com desconto!"
        elif any(word in message_lower for word in ['agendar', 'horário', 'marcar']):
            return "Perfeito! Para qual tratamento gostaria de agendar? Temos disponibilidade na próxima semana. Qual seria o melhor dia e horário para você?"
        elif any(word in message_lower for word in ['cancelar', 'desmarcar']):
            return "Entendo que precisa cancelar. Pode me informar para qual data estava agendado? Vou verificar e te ajudar com o reagendamento se desejar."
        else:
            return "Entendi! Estou aqui para ajudar com qualquer dúvida sobre nossos serviços de beleza e bem-estar. O que mais gostaria de saber?"
    
    def start_new_conversation(self, scenario_name: str):
        """Inicia nova conversa"""
        if self.current_conversation:
            self.conversations.append({
                "scenario": "conversa_anterior",
                "scenario_name": "Conversa Anterior",
                "messages": self.current_conversation.copy(),
                "timestamp": datetime.now().isoformat()
            })
        
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
    
    async def send_test_message(self, message: str):
        """Simula envio de mensagem e captura resposta"""
        logger.info(f"📤 Enviando: {message}")
        
        # Simular resposta
        timestamp = datetime.now().isoformat()
        
        # Adicionar mensagem do usuário
        self.current_conversation.append({
            "type": "sent",
            "content": message,
            "timestamp": timestamp,
            "status_code": 200
        })
        
        # Gerar e adicionar resposta da LLM
        llm_response = self.get_contextual_llm_response(message)
        self.current_conversation.append({
            "type": "received", 
            "content": llm_response,
            "timestamp": timestamp
        })
        
        logger.info(f"🤖 LLM respondeu: {llm_response[:50]}...")
        
        await asyncio.sleep(1)  # Simular delay
        
    async def test_conversation_capture(self):
        """Testa captura de conversas"""
        # Cenário 1: Saudação
        self.start_new_conversation("Saudação e Apresentação")
        await self.send_test_message("Olá! Bom dia! 😊")
        await self.send_test_message("Como você está?")
        await self.send_test_message("Gostaria de conhecer seus serviços")
        self.finalize_current_conversation("Saudação e Apresentação")
        
        # Cenário 2: Consulta de serviços
        self.start_new_conversation("Consulta de Serviços")
        await self.send_test_message("Quais serviços vocês oferecem?")
        await self.send_test_message("Quanto custa uma limpeza de pele?")
        await self.send_test_message("Têm desconto para pacotes?")
        self.finalize_current_conversation("Consulta de Serviços")
        
        # Cenário 3: Agendamento
        self.start_new_conversation("Agendamento Completo")
        await self.send_test_message("Quero agendar um horário")
        await self.send_test_message("Limpeza de pele profunda")
        await self.send_test_message("Amanhã de manhã seria possível?")
        self.finalize_current_conversation("Agendamento Completo")
    
    def generate_conversation_report(self):
        """Gera relatório das conversas capturadas"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"conversation_capture_test_{timestamp}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teste de Captura de Conversas</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .conversation {{ border: 1px solid #ddd; margin: 20px 0; padding: 15px; border-radius: 8px; }}
        .message {{ margin: 10px 0; padding: 10px; border-radius: 15px; }}
        .sent {{ background: #007bff; color: white; margin-left: 20%; }}
        .received {{ background: #f8f9fa; border: 1px solid #ddd; margin-right: 20%; }}
        .timestamp {{ font-size: 0.8em; color: #666; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; }}
    </style>
</head>
<body>
    <h1>🧪 Teste de Captura de Conversas</h1>
    <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
    <p><strong>Total de conversas:</strong> {len(self.conversations)}</p>
    
    <h2>💬 Conversas Capturadas</h2>
"""
        
        for conv in self.conversations:
            html_content += f"""
    <div class="conversation">
        <h3>🎬 {conv['scenario_name']}</h3>
        <p><strong>Total de mensagens:</strong> {len(conv['messages'])}</p>
"""
            
            for msg in conv['messages']:
                if msg['type'] == 'sent':
                    html_content += f"""
        <div class="message sent">
            <strong>👤 Usuário:</strong> {msg['content']}<br>
            <div class="timestamp">✅ {msg['timestamp'][:19]} - Status: {msg.get('status_code', 'N/A')}</div>
        </div>
"""
                elif msg['type'] == 'received':
                    html_content += f"""
        <div class="message received">
            <strong>🤖 LLM:</strong> {msg['content']}<br>
            <div class="timestamp">📥 {msg['timestamp'][:19]}</div>
        </div>
"""
            
            html_content += """
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"📊 Relatório de teste salvo em: {filename}")
        return filename

async def main():
    """Função principal do teste"""
    logger.info("🔬 Iniciando teste de captura de conversas")
    
    tester = ConversationCaptureTester()
    
    # Executar teste de conversas
    await tester.test_conversation_capture()
    
    # Gerar relatório
    report_file = tester.generate_conversation_report()
    
    logger.info(f"✅ Teste concluído! Relatório: {report_file}")
    logger.info(f"📊 Total de conversas capturadas: {len(tester.conversations)}")
    
    # Mostrar resumo das conversas
    for i, conv in enumerate(tester.conversations, 1):
        logger.info(f"  {i}. {conv['scenario_name']}: {len(conv['messages'])} mensagens")

if __name__ == "__main__":
    asyncio.run(main())
