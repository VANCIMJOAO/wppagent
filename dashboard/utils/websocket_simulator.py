"""
WebSocket Simulator para Updates em Tempo Real
=============================================

Simula funcionalidade de WebSocket para:
✅ Updates em tempo real de mensagens
✅ Notificações de novas conversas
✅ Status de leitura de mensagens
✅ Indicadores de digitação
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random

class WebSocketSimulator:
    """Simula comportamento de WebSocket para desenvolvimento"""
    
    def __init__(self):
        self.clients = {}
        self.message_queue = []
        self.active_conversations = set()
        
    def connect_client(self, client_id: str):
        """Conecta um cliente ao simulador"""
        self.clients[client_id] = {
            'connected_at': datetime.now(),
            'active_conversation': None,
            'status': 'online'
        }
        print(f"🔌 Cliente {client_id} conectado ao WebSocket simulado")
        
    def disconnect_client(self, client_id: str):
        """Desconecta um cliente"""
        if client_id in self.clients:
            del self.clients[client_id]
            print(f"🔌 Cliente {client_id} desconectado do WebSocket")
    
    def simulate_incoming_message(self, conversation_id: int, content: str, sender_name: str = "Cliente"):
        """Simula recebimento de mensagem"""
        message_data = {
            'type': 'new_message',
            'conversation_id': conversation_id,
            'content': content,
            'sender_name': sender_name,
            'timestamp': datetime.now().isoformat(),
            'message_id': f"msg_{random.randint(10000, 99999)}",
            'is_user': True
        }
        
        self.message_queue.append(message_data)
        print(f"📨 Mensagem simulada: {content[:50]}...")
        return message_data
    
    def simulate_typing_indicator(self, conversation_id: int, is_typing: bool = True):
        """Simula indicador de digitação"""
        typing_data = {
            'type': 'typing_indicator',
            'conversation_id': conversation_id,
            'is_typing': is_typing,
            'timestamp': datetime.now().isoformat()
        }
        
        self.message_queue.append(typing_data)
        return typing_data
    
    def simulate_message_status_update(self, message_id: str, status: str):
        """Simula atualização de status da mensagem (sent, delivered, read)"""
        status_data = {
            'type': 'message_status',
            'message_id': message_id,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        self.message_queue.append(status_data)
        return status_data
    
    def get_pending_updates(self, client_id: str = None) -> List[Dict[str, Any]]:
        """Retorna atualizações pendentes para um cliente"""
        if not self.message_queue:
            return []
        
        # Por simplicidade, retorna todas as mensagens pendentes
        updates = self.message_queue.copy()
        self.message_queue.clear()  # Limpa a fila após entrega
        
        return updates
    
    def generate_random_updates(self):
        """Gera updates aleatórios para simular atividade real"""
        random_messages = [
            "Olá! Tudo bem?",
            "Gostaria de mais informações",
            "Qual o horário de funcionamento?",
            "Obrigado pelo atendimento!",
            "Preciso cancelar meu agendamento",
            "Vocês atendem aos sábados?",
            "Quanto custa o serviço?",
            "Como faço para chegar aí?"
        ]
        
        customer_names = [
            "Ana Silva", "João Santos", "Maria Oliveira", "Pedro Costa",
            "Carla Lima", "Ricardo Alves", "Juliana Pereira", "Roberto Ferreira"
        ]
        
        # 20% de chance de gerar uma nova mensagem
        if random.random() < 0.2:
            conversation_id = random.randint(1, 10)
            message = random.choice(random_messages)
            sender = random.choice(customer_names)
            
            return self.simulate_incoming_message(conversation_id, message, sender)
        
        # 10% de chance de indicador de digitação
        elif random.random() < 0.1:
            conversation_id = random.randint(1, 10)
            return self.simulate_typing_indicator(conversation_id, True)
        
        return None

# Classe para gerenciar estado das conversas
class ConversationStateManager:
    """Gerencia estado das conversas para WebSocket simulation"""
    
    def __init__(self):
        self.conversation_states = {}
        self.typing_timers = {}
        
    def set_conversation_state(self, conversation_id: int, state: Dict[str, Any]):
        """Define estado de uma conversa"""
        self.conversation_states[conversation_id] = {
            **state,
            'last_updated': datetime.now()
        }
    
    def get_conversation_state(self, conversation_id: int) -> Dict[str, Any]:
        """Retorna estado atual de uma conversa"""
        return self.conversation_states.get(conversation_id, {
            'is_online': False,
            'is_typing': False,
            'last_seen': datetime.now() - timedelta(minutes=30),
            'unread_count': 0
        })
    
    def mark_as_read(self, conversation_id: int):
        """Marca conversa como lida"""
        if conversation_id in self.conversation_states:
            self.conversation_states[conversation_id]['unread_count'] = 0
    
    def increment_unread(self, conversation_id: int):
        """Incrementa contador de não lidas"""
        state = self.get_conversation_state(conversation_id)
        state['unread_count'] = state.get('unread_count', 0) + 1
        self.set_conversation_state(conversation_id, state)

# Instâncias globais
ws_simulator = WebSocketSimulator()
conversation_manager = ConversationStateManager()

# Funções auxiliares para integração com Dash
def get_realtime_updates() -> Dict[str, Any]:
    """Função para ser chamada pelos callbacks do Dash"""
    
    # Gera updates aleatórios ocasionalmente
    random_update = ws_simulator.generate_random_updates()
    
    # Pega todos os updates pendentes
    updates = ws_simulator.get_pending_updates()
    
    if updates:
        return {
            'timestamp': datetime.now().isoformat(),
            'updates': updates,
            'count': len(updates)
        }
    
    return {'timestamp': datetime.now().isoformat(), 'updates': [], 'count': 0}

def simulate_user_activity(conversation_id: int):
    """Simula atividade do usuário em uma conversa específica"""
    
    # Simula que o usuário está digitando
    ws_simulator.simulate_typing_indicator(conversation_id, True)
    
    # Após alguns segundos, para de digitar e envia mensagem
    import threading
    import time
    
    def delayed_message():
        time.sleep(2)  # Simula tempo de digitação
        ws_simulator.simulate_typing_indicator(conversation_id, False)
        
        # Mensagens de resposta automática baseadas no contexto
        auto_responses = [
            "Entendi sua solicitação. Deixe-me verificar isso para você.",
            "Obrigado pela mensagem! Vou encaminhar para o setor responsável.",
            "Posso ajudar com isso. Qual seria o melhor horário para você?",
            "Perfeito! Vou preparar as informações que você solicitou.",
            "Claro! Fico à disposição para qualquer esclarecimento."
        ]
        
        response = random.choice(auto_responses)
        ws_simulator.simulate_incoming_message(conversation_id, response, "Atendente")
    
    # Executa em thread separada para não bloquear
    threading.Thread(target=delayed_message, daemon=True).start()

def get_conversation_activity_indicators(conversation_id: int) -> Dict[str, Any]:
    """Retorna indicadores de atividade para uma conversa"""
    
    # Simula indicadores como "última vez visto", "online", etc.
    now = datetime.now()
    
    # Simula que há 70% de chance do usuário estar online
    is_online = random.random() < 0.7
    
    # Se não está online, simula última atividade
    if not is_online:
        last_seen = now - timedelta(minutes=random.randint(5, 120))
        last_seen_text = f"Visto por último às {last_seen.strftime('%H:%M')}"
    else:
        last_seen_text = "Online agora"
    
    return {
        'conversation_id': conversation_id,
        'is_online': is_online,
        'last_seen': last_seen_text,
        'is_typing': False,  # Será atualizado pelos updates em tempo real
        'unread_count': random.randint(0, 3) if random.random() < 0.3 else 0
    }

# Funções para integração com callbacks Dash
def start_websocket_simulation():
    """Inicia a simulação de WebSocket"""
    ws_simulator.connect_client("dash_client")
    print("🚀 Simulação de WebSocket iniciada")

def stop_websocket_simulation():
    """Para a simulação de WebSocket"""
    ws_simulator.disconnect_client("dash_client")
    print("⏹️ Simulação de WebSocket parada")

def inject_test_message(conversation_id: int = 1):
    """Injeta uma mensagem de teste para debugging"""
    test_messages = [
        "Esta é uma mensagem de teste do sistema WebSocket!",
        "Testando funcionalidade em tempo real...",
        "WebSocket simulado funcionando corretamente! 🚀"
    ]
    
    message = random.choice(test_messages)
    return ws_simulator.simulate_incoming_message(conversation_id, message, "Sistema")

def get_conversation_status_updates() -> List[Dict[str, Any]]:
    """Retorna updates de status das conversas"""
    
    status_updates = []
    
    # Para cada conversa ativa, gera possíveis updates de status
    for conversation_id in range(1, 11):  # IDs 1-10 para exemplo
        # 15% de chance de atualizar status
        if random.random() < 0.15:
            state = conversation_manager.get_conversation_state(conversation_id)
            
            # Atualiza status aleatoriamente
            if random.random() < 0.5:
                state['is_online'] = not state.get('is_online', False)
            
            if random.random() < 0.3:
                state['is_typing'] = not state.get('is_typing', False)
            
            conversation_manager.set_conversation_state(conversation_id, state)
            
            status_updates.append({
                'type': 'status_update',
                'conversation_id': conversation_id,
                'is_online': state['is_online'],
                'is_typing': state['is_typing'],
                'timestamp': datetime.now().isoformat()
            })
    
    return status_updates

def generate_push_notification(conversation_id: int, message: str, sender_name: str) -> Dict[str, Any]:
    """Gera dados de notificação push"""
    
    return {
        'type': 'push_notification',
        'conversation_id': conversation_id,
        'title': f'Nova mensagem de {sender_name}',
        'body': message[:50] + ('...' if len(message) > 50 else ''),
        'timestamp': datetime.now().isoformat(),
        'badge_count': conversation_manager.get_conversation_state(conversation_id).get('unread_count', 0) + 1
    }

# Utilitários para debugging
def debug_websocket_state() -> Dict[str, Any]:
    """Retorna estado atual do WebSocket para debugging"""
    
    return {
        'connected_clients': len(ws_simulator.clients),
        'pending_messages': len(ws_simulator.message_queue),
        'active_conversations': len(ws_simulator.active_conversations),
        'conversation_states': len(conversation_manager.conversation_states),
        'timestamp': datetime.now().isoformat()
    }

def clear_websocket_state():
    """Limpa estado do WebSocket - útil para testes"""
    global ws_simulator, conversation_manager
    ws_simulator = WebSocketSimulator()
    conversation_manager = ConversationStateManager()
    print("🗑️ Estado do WebSocket limpo")

def create_browser_notification_data(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Cria dados para notificação do browser"""
    
    if message_data['type'] == 'new_message':
        return {
            'title': f"Nova mensagem - {message_data.get('sender_name', 'Cliente')}",
            'body': message_data['content'],
            'icon': '/assets/notification-icon.png',
            'tag': f"conversation_{message_data['conversation_id']}",
            'data': {
                'conversation_id': message_data['conversation_id'],
                'action': 'open_conversation'
            }
        }
    
    return {}

# Export das funções principais para uso nos callbacks
__all__ = [
    'get_realtime_updates',
    'simulate_user_activity', 
    'get_conversation_activity_indicators',
    'start_websocket_simulation',
    'stop_websocket_simulation',
    'inject_test_message',
    'get_conversation_status_updates',
    'generate_push_notification',
    'debug_websocket_state',
    'clear_websocket_state',
    'create_browser_notification_data',
    'ws_simulator',
    'conversation_manager'
]
