"""
Serviço de Updates em Tempo Real - WebSocket Real
===============================================

Substitui simulações por conexão WebSocket real com o backend.
Permite recebimento de notificações em tempo real para:
- Novas mensagens
- Updates de conversas
- Updates de agendamentos
- Mudanças de status
"""

import asyncio
import json
import logging
from typing import Dict, Callable, Optional, Any
from datetime import datetime
import websockets
from threading import Thread
import time
import os

logger = logging.getLogger(__name__)

def get_websocket_url():
    """Detecta a URL do WebSocket baseada no ambiente"""
    # Verifica variáveis de ambiente primeiro
    if os.getenv('WEBSOCKET_URL'):
        return os.getenv('WEBSOCKET_URL')
    
    # Em produção, usar URL do backend
    if os.getenv('ENVIRONMENT') == 'production':
        backend_url = os.getenv('BACKEND_URL', 'ws://localhost:8000')
        return f"{backend_url}/ws"
    
    # Desenvolvimento: tentar diferentes portas
    possible_ports = [8000, 8080, 3000, 5000]
    for port in possible_ports:
        websocket_url = f"ws://localhost:{port}/ws"
        # TODO: Futuramente, testar conectividade aqui
        if port == 8000:  # Por enquanto, usar 8000 como padrão
            return websocket_url
    
    return "ws://localhost:8000/ws"

class RealtimeService:
    """Serviço para updates em tempo real via WebSocket"""
    
    def __init__(self, websocket_url: str = None):
        self.websocket_url = websocket_url or get_websocket_url()
        self.websocket = None
        self.callbacks: Dict[str, Callable] = {}
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # segundos
        self.loop = None
        self.thread = None
        
    def register_callback(self, event_type: str, callback: Callable):
        """Registra callback para evento específico"""
        self.callbacks[event_type] = callback
        logger.info(f"📡 Callback registrado para evento '{event_type}'")
        
    async def connect(self):
        """Conecta ao WebSocket do backend"""
        try:
            logger.info(f"🔌 Tentando conectar ao WebSocket: {self.websocket_url}")
            
            self.websocket = await websockets.connect(
                self.websocket_url,
                timeout=10,
                close_timeout=10
            )
            
            self.is_connected = True
            self.reconnect_attempts = 0
            
            logger.info("✅ WebSocket conectado com sucesso!")
            
            # Inicia o loop de escuta
            await self.listen()
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar WebSocket: {e}")
            self.is_connected = False
            await self.handle_reconnection()
            
    async def listen(self):
        """Escuta mensagens do WebSocket"""
        try:
            async for message in self.websocket:
                await self.handle_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ Conexão WebSocket perdida")
            self.is_connected = False
            await self.handle_reconnection()
            
        except Exception as e:
            logger.error(f"❌ Erro no loop de escuta: {e}")
            self.is_connected = False
            
    async def handle_message(self, message: str):
        """Processa mensagem recebida do WebSocket"""
        try:
            data = json.loads(message)
            event_type = data.get('type')
            payload = data.get('payload', {})
            
            logger.info(f"📨 Evento recebido: {event_type}")
            
            # Dispatch para callback apropriado
            if event_type in self.callbacks:
                callback = self.callbacks[event_type]
                
                # Executa callback em thread separada para não bloquear
                Thread(
                    target=callback, 
                    args=(payload,), 
                    daemon=True
                ).start()
                
        except json.JSONDecodeError:
            logger.error(f"❌ Mensagem inválida recebida: {message}")
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            
    async def handle_reconnection(self):
        """Gerencia reconexão automática"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("❌ Máximo de tentativas de reconexão atingido")
            return
            
        self.reconnect_attempts += 1
        logger.info(f"🔄 Tentativa de reconexão {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        await asyncio.sleep(self.reconnect_delay)
        await self.connect()
        
    async def send_message(self, message: dict):
        """Envia mensagem para o WebSocket"""
        if not self.is_connected or not self.websocket:
            logger.warning("⚠️ WebSocket não conectado - não é possível enviar mensagem")
            return
            
        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"📤 Mensagem enviada: {message.get('type', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            
    def start_background_connection(self):
        """Inicia conexão WebSocket em background"""
        def run_websocket():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.connect())
            
        self.thread = Thread(target=run_websocket, daemon=True)
        self.thread.start()
        logger.info("🚀 Serviço WebSocket iniciado em background")
        
    def stop(self):
        """Para a conexão WebSocket"""
        self.is_connected = False
        
        if self.websocket:
            asyncio.create_task(self.websocket.close())
            
        if self.loop and self.loop.is_running():
            self.loop.stop()
            
        logger.info("🛑 Serviço WebSocket parado")

    # Handlers específicos para diferentes tipos de eventos
    
    def handle_new_message(self, data: dict):
        """Processa nova mensagem recebida"""
        logger.info(f"💬 Nova mensagem recebida - Conversa: {data.get('conversation_id')}")
        
        # Callback específico pode ser registrado externamente
        if 'new_message' in self.callbacks:
            self.callbacks['new_message'](data)
            
    def handle_conversation_update(self, data: dict):
        """Processa update de conversa"""
        logger.info(f"🔄 Conversa atualizada - ID: {data.get('conversation_id')}")
        
        if 'conversation_update' in self.callbacks:
            self.callbacks['conversation_update'](data)
            
    def handle_appointment_update(self, data: dict):
        """Processa update de agendamento"""
        logger.info(f"📅 Agendamento atualizado - ID: {data.get('appointment_id')}")
        
        if 'appointment_update' in self.callbacks:
            self.callbacks['appointment_update'](data)
            
    def handle_status_change(self, data: dict):
        """Processa mudança de status"""
        logger.info(f"🔄 Status alterado - Tipo: {data.get('status_type')}")
        
        if 'status_change' in self.callbacks:
            self.callbacks['status_change'](data)


# Instância global do serviço
_realtime_service = None

def get_realtime_service() -> RealtimeService:
    """Retorna instância singleton do serviço de tempo real"""
    global _realtime_service
    
    if _realtime_service is None:
        _realtime_service = RealtimeService()
        
    return _realtime_service

def start_realtime_service():
    """Inicia o serviço de tempo real"""
    service = get_realtime_service()
    service.start_background_connection()
    return service

def stop_realtime_service():
    """Para o serviço de tempo real"""
    global _realtime_service
    
    if _realtime_service:
        _realtime_service.stop()
        _realtime_service = None


# Classe de conveniência para uso em callbacks Dash
class DashRealtimeIntegration:
    """Integração específica para callbacks Dash"""
    
    def __init__(self):
        self.service = get_realtime_service()
        self.dash_stores = {}
        
    def register_dash_store(self, event_type: str, store_id: str):
        """Registra um Dash Store para receber updates de um evento específico"""
        self.dash_stores[event_type] = store_id
        
        # Registra callback que atualiza o store
        def update_dash_store(data):
            # Aqui devemos integrar com o sistema de updates do Dash
            # Por enquanto, apenas logga
            logger.info(f"📊 Atualizando store '{store_id}' com dados: {data}")
            
        self.service.register_callback(event_type, update_dash_store)
        
    def setup_conversation_updates(self, conversations_store_id: str):
        """Configura updates automáticos para conversas"""
        self.register_dash_store('new_message', conversations_store_id)
        self.register_dash_store('conversation_update', conversations_store_id)
        
    def setup_appointment_updates(self, appointments_store_id: str):
        """Configura updates automáticos para agendamentos"""
        self.register_dash_store('appointment_update', appointments_store_id)


if __name__ == "__main__":
    # Teste do serviço
    import logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_realtime_service():
        service = RealtimeService()
        
        # Registra callbacks de teste
        service.register_callback('new_message', lambda data: print(f"Nova mensagem: {data}"))
        service.register_callback('conversation_update', lambda data: print(f"Conversa atualizada: {data}"))
        
        # Conecta e aguarda
        await service.connect()
        
    # Executa teste
    asyncio.run(test_realtime_service())
