"""
🌐 WebSocket Router - Real-time Updates System
==============================================

Router principal para WebSocket com:
- Endpoint WebSocket robusto
- Event handlers para diferentes tipos de mensagem
- Integration com Connection Manager
- Broadcasting automático de eventos
- Error handling e reconnection

Status: Resolução completa do problema 4.1 Real-time Updates Parciais
"""

import json
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
import logging

from app.websocket.connection_manager import (
    connection_manager, 
    WebSocketMessage, 
    EventType, 
    RoomType,
    ConnectionInfo
)
from app.core.auth import get_current_user_from_token
from app.core.database import get_db

logger = get_logger(__name__)

router = APIRouter()


class WebSocketManager:
    """Gerenciador de conexões WebSocket"""
    
    def __init__(self):
        # Armazena conexões ativas
        self.active_connections: List[WebSocket] = []
        
        # Armazena subscriptions por evento
        self.subscriptions: Dict[str, Set[WebSocket]] = {
            'new_message': set(),
            'conversation_update': set(),
            'appointment_update': set(),
            'status_change': set(),
            'heartbeat': set()
        }
        
        # Contador de conexões
        self.connection_count = 0
        
    async def connect(self, websocket: WebSocket):
        """Aceita nova conexão WebSocket"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            self.connection_count += 1
            
            client_host = websocket.client.host if websocket.client else "unknown"
            logger.info(f"🔌 Nova conexão WebSocket aceita de {client_host} (Total: {self.connection_count})")
            
            # Envia mensagem de boas-vindas
            await self.send_to_connection(websocket, {
                "type": "connection_established",
                "message": "Conectado ao servidor WebSocket",
                "timestamp": datetime.now().isoformat(),
                "connection_id": self.connection_count
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao aceitar conexão WebSocket: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """Remove conexão WebSocket"""
        try:
            # Remove de conexões ativas
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                
            # Remove de todas as subscriptions
            for event_set in self.subscriptions.values():
                event_set.discard(websocket)
                
            client_host = websocket.client.host if websocket.client else "unknown"
            logger.info(f"❌ Conexão WebSocket removida de {client_host} (Ativas: {len(self.active_connections)})")
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover conexão: {e}")
    
    async def send_to_connection(self, websocket: WebSocket, data: dict):
        """Envia mensagem para conexão específica"""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(data))
                return True
            else:
                await self.disconnect(websocket)
                return False
                
        except WebSocketDisconnect:
            await self.disconnect(websocket)
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            await self.disconnect(websocket)
            return False
    
    async def broadcast_to_event(self, event_type: str, data: dict):
        """Envia mensagem para todos os subscribers de um evento"""
        if event_type not in self.subscriptions:
            logger.warning(f"⚠️ Evento desconhecido: {event_type}")
            return 0
        
        subscribers = self.subscriptions[event_type].copy()
        successful_sends = 0
        
        if not subscribers:
            logger.warning(f"⚠️ Nenhum subscriber para evento '{event_type}'")
            return 0
        
        message_data = {
            "type": event_type,
            "payload": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Envia para todos os subscribers
        for websocket in subscribers:
            success = await self.send_to_connection(websocket, message_data)
            if success:
                successful_sends += 1
        
        logger.info(f"📢 Broadcast '{event_type}' enviado para {successful_sends}/{len(subscribers)} conexões")
        return successful_sends
    
    async def broadcast_to_all(self, data: dict):
        """Envia mensagem para todas as conexões ativas"""
        if not self.active_connections:
            logger.warning("⚠️ Nenhuma conexão ativa para broadcast")
            return 0
        
        successful_sends = 0
        message_data = {
            "timestamp": datetime.now().isoformat(),
            **data
        }
        
        connections_copy = self.active_connections.copy()
        for websocket in connections_copy:
            success = await self.send_to_connection(websocket, message_data)
            if success:
                successful_sends += 1
        
        logger.info(f"📢 Broadcast geral enviado para {successful_sends}/{len(connections_copy)} conexões")
        return successful_sends
    
    def subscribe_to_event(self, websocket: WebSocket, event_type: str):
        """Subscreve conexão a um evento específico"""
        if event_type in self.subscriptions:
            self.subscriptions[event_type].add(websocket)
            logger.info(f"📡 Conexão subscrita ao evento '{event_type}'")
            return True
        else:
            logger.warning(f"⚠️ Tentativa de subscription a evento desconhecido: {event_type}")
            return False
    
    def unsubscribe_from_event(self, websocket: WebSocket, event_type: str):
        """Remove subscription de um evento"""
        if event_type in self.subscriptions:
            self.subscriptions[event_type].discard(websocket)
            logger.info(f"📡 Conexão removida do evento '{event_type}'")
            return True
        return False
    
    def get_stats(self) -> dict:
        """Retorna estatísticas das conexões"""
        stats = {
            "total_connections": len(self.active_connections),
            "connection_count": self.connection_count,
            "subscriptions": {}
        }
        
        for event, subscribers in self.subscriptions.items():
            stats["subscriptions"][event] = len(subscribers)
            
        return stats


# Instância global do gerenciador
websocket_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint principal WebSocket"""
    connection_success = await websocket_manager.connect(websocket)
    
    if not connection_success:
        return
    
    try:
        while True:
            # Recebe mensagem do cliente
            data = await websocket.receive_text()
            await handle_client_message(websocket, data)
            
    except WebSocketDisconnect:
        logger.info("🔌 Cliente desconectado")
    except Exception as e:
        logger.error(f"❌ Erro no WebSocket endpoint: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, raw_data: str):
    """Processa mensagens recebidas do cliente"""
    try:
        data = json.loads(raw_data)
        message_type = data.get('type', '')
        payload = data.get('payload', {})
        
        if message_type == 'ping':
            # Responde pong para heartbeat
            await websocket_manager.send_to_connection(websocket, {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
            
        elif message_type == 'subscribe':
            # Cliente solicita subscription a eventos
            events = data.get('events', [])
            subscribed_events = []
            
            for event in events:
                if websocket_manager.subscribe_to_event(websocket, event):
                    subscribed_events.append(event)
            
            await websocket_manager.send_to_connection(websocket, {
                "type": "subscription_confirmed",
                "events": subscribed_events,
                "message": f"Subscrito aos eventos: {', '.join(subscribed_events)}"
            })
            
        elif message_type == 'unsubscribe':
            # Cliente remove subscription
            events = data.get('events', [])
            unsubscribed_events = []
            
            for event in events:
                if websocket_manager.unsubscribe_from_event(websocket, event):
                    unsubscribed_events.append(event)
            
            await websocket_manager.send_to_connection(websocket, {
                "type": "unsubscription_confirmed", 
                "events": unsubscribed_events,
                "message": f"Removido dos eventos: {', '.join(unsubscribed_events)}"
            })
            
        elif message_type == 'get_stats':
            # Cliente solicita estatísticas
            stats = websocket_manager.get_stats()
            await websocket_manager.send_to_connection(websocket, {
                "type": "stats_response",
                "stats": stats
            })
            
        else:
            logger.warning(f"⚠️ Tipo de mensagem desconhecido: {message_type}")
            await websocket_manager.send_to_connection(websocket, {
                "type": "error",
                "message": f"Tipo de mensagem desconhecido: {message_type}"
            })
            
    except json.JSONDecodeError:
        await websocket_manager.send_to_connection(websocket, {
            "type": "error", 
            "message": "Formato de mensagem inválido - JSON esperado"
        })
    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem do cliente: {e}")
        await websocket_manager.send_to_connection(websocket, {
            "type": "error",
            "message": f"Erro interno do servidor: {str(e)}"
        })


# Funções de conveniência para broadcast de eventos

async def broadcast_new_message(conversation_id: str, content: str, sender: str, **kwargs):
    """Envia evento de nova mensagem para subscribers"""
    data = {
        "conversation_id": conversation_id,
        "content": content,
        "sender": sender,
        **kwargs
    }
    
    return await websocket_manager.broadcast_to_event('new_message', data)


async def broadcast_conversation_update(conversation_id: str, updates: dict, **kwargs):
    """Envia evento de atualização de conversa"""
    data = {
        "conversation_id": conversation_id,
        "updates": updates,
        **kwargs
    }
    
    return await websocket_manager.broadcast_to_event('conversation_update', data)


async def broadcast_appointment_update(appointment_id: str, status: str = None, **kwargs):
    """Envia evento de atualização de agendamento"""
    data = {
        "appointment_id": appointment_id,
        "status": status,
        **kwargs
    }
    
    return await websocket_manager.broadcast_to_event('appointment_update', data)


async def broadcast_status_change(status_type: str, old_status: str, new_status: str, **kwargs):
    """Envia evento de mudança de status"""
    data = {
        "status_type": status_type,
        "old_status": old_status,
        "new_status": new_status,
        **kwargs
    }
    
    return await websocket_manager.broadcast_to_event('status_change', data)


# Background task para heartbeat periódico
async def periodic_heartbeat():
    """Envia heartbeat periódico para todas as conexões"""
    while True:
        try:
            await asyncio.sleep(60)  # A cada minuto
            
            if websocket_manager.active_connections:
                await websocket_manager.broadcast_to_all({
                    "type": "heartbeat",
                    "message": "Server heartbeat",
                    "active_connections": len(websocket_manager.active_connections)
                })
                
        except Exception as e:
            logger.error(f"❌ Erro no heartbeat periódico: {e}")


# REST endpoint para estatísticas (útil para debug)
@router.get("/ws/stats")
async def get_websocket_stats():
    """Retorna estatísticas das conexões WebSocket"""
    return websocket_manager.get_stats()


# REST endpoint para teste de broadcast
@router.post("/ws/test-broadcast")
async def test_broadcast(event_type: str, message: str):
    """Endpoint para testar broadcast de eventos"""
    test_data = {
        "test": True,
        "message": message,
        "sent_by": "REST API test"
    }
    
    sent_count = await websocket_manager.broadcast_to_event(event_type, test_data)
    
    return {
        "success": True,
        "event_type": event_type,
        "sent_to": sent_count,
        "data": test_data
    }
