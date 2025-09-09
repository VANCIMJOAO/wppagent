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
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from app.websocket.connection_manager import (
        connection_manager, 
        WebSocketMessage, 
        EventType, 
        RoomType,
        ConnectionInfo
    )
except ImportError:
    # Fallback se não conseguir importar
    logger.warning("Could not import connection_manager, using fallback")
    from app.websocket.connection_manager import connection_manager

# Router para WebSocket
router = APIRouter()
security = HTTPBearer()

class WebSocketHandler:
    """
    🔧 Handler para processar mensagens WebSocket
    """
    
    def __init__(self):
        self.message_handlers = {
            "authenticate": self._handle_authenticate,
            "join_room": self._handle_join_room,
            "leave_room": self._handle_leave_room,
            "heartbeat": self._handle_heartbeat,
            "get_room_users": self._handle_get_room_users,
            "send_message": self._handle_send_message,
            "get_stats": self._handle_get_stats
        }
    
    async def handle_message(self, websocket: WebSocket, message_data: dict):
        """
        📨 Processar mensagem recebida via WebSocket
        """
        try:
            message_type = message_data.get("type")
            if message_type not in self.message_handlers:
                await self._send_error(websocket, f"Unknown message type: {message_type}")
                return
            
            handler = self.message_handlers[message_type]
            await handler(websocket, message_data)
            
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self._send_error(websocket, f"Error processing message: {str(e)}")
    
    async def _handle_authenticate(self, websocket: WebSocket, message_data: dict):
        """
        🔐 Handler para autenticação
        """
        token = message_data.get("token")
        if not token:
            await self._send_error(websocket, "Token is required")
            return
        
        success = await connection_manager.authenticate_connection(websocket, token)
        if not success:
            await self._send_error(websocket, "Authentication failed")
    
    async def _handle_join_room(self, websocket: WebSocket, message_data: dict):
        """
        🚪 Handler para entrar em sala
        """
        room = message_data.get("room", "general")
        connection_info = connection_manager.websocket_map.get(websocket)
        
        if not connection_info:
            await self._send_error(websocket, "Connection not found")
            return
        
        # Mover usuário para nova sala
        success = await connection_manager.move_user_to_room(connection_info.user_id, room)
        if success:
            response_data = {
                "type": "system_notification",
                "data": {"message": f"Joined room: {room}", "room": room},
                "room": room,
                "user_id": connection_info.user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(response_data))
    
    async def _handle_leave_room(self, websocket: WebSocket, message_data: dict):
        """
        🚪 Handler para sair de sala
        """
        # Mover para sala geral
        connection_info = connection_manager.websocket_map.get(websocket)
        if connection_info:
            await connection_manager.move_user_to_room(
                connection_info.user_id, 
                "general"
            )
    
    async def _handle_heartbeat(self, websocket: WebSocket, message_data: dict):
        """
        💓 Handler para heartbeat
        """
        await connection_manager.handle_heartbeat(websocket)
        
        # Responder com pong
        pong_data = {
            "type": "heartbeat",
            "data": {"status": "pong"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await websocket.send_text(json.dumps(pong_data))
        except Exception as e:
            logger.error(f"Error sending pong: {e}")
    
    async def _handle_get_room_users(self, websocket: WebSocket, message_data: dict):
        """
        👥 Handler para listar usuários da sala
        """
        room = message_data.get("room")
        connection_info = connection_manager.websocket_map.get(websocket)
        
        if not connection_info:
            await self._send_error(websocket, "Connection not found")
            return
        
        # Use room da conexão se não especificado
        if not room:
            room = connection_info.room
        
        users = await connection_manager.get_room_users(room)
        
        response_data = {
            "type": "system_notification",
            "data": {
                "room": room,
                "users": users,
                "count": len(users)
            },
            "room": room,
            "user_id": connection_info.user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await websocket.send_text(json.dumps(response_data))
        except Exception as e:
            logger.error(f"Error sending room users: {e}")
    
    async def _handle_send_message(self, websocket: WebSocket, message_data: dict):
        """
        💬 Handler para enviar mensagem
        """
        connection_info = connection_manager.websocket_map.get(websocket)
        if not connection_info or not connection_info.is_authenticated:
            await self._send_error(websocket, "Authentication required")
            return
        
        target_room = message_data.get("room", connection_info.room)
        message_content = message_data.get("message", "")
        
        broadcast_data = {
            "type": "system_notification",
            "data": {
                "from_user": connection_info.user_id,
                "message": message_content,
                "room": target_room
            },
            "room": target_room,
            "user_id": connection_info.user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast para todos na sala
        if target_room in connection_manager.active_connections:
            for conn in connection_manager.active_connections[target_room]:
                try:
                    await conn.websocket.send_text(json.dumps(broadcast_data))
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
    
    async def _handle_get_stats(self, websocket: WebSocket, message_data: dict):
        """
        📊 Handler para estatísticas do sistema
        """
        connection_info = connection_manager.websocket_map.get(websocket)
        if not connection_info:
            await self._send_error(websocket, "Connection not found")
            return
        
        stats = connection_manager.get_stats()
        
        response_data = {
            "type": "system_notification",
            "data": {"stats": stats},
            "room": connection_info.room,
            "user_id": connection_info.user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await websocket.send_text(json.dumps(response_data))
        except Exception as e:
            logger.error(f"Error sending stats: {e}")
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """
        ❌ Enviar mensagem de erro
        """
        error_data = {
            "type": "error",
            "data": {
                "error": error_message,
                "level": "error"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await websocket.send_text(json.dumps(error_data))
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

# Handler instance
ws_handler = WebSocketHandler()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    🌐 Endpoint principal do WebSocket
    
    Protocolo de comunicação:
    1. Cliente conecta
    2. Servidor solicita autenticação
    3. Cliente envia token JWT
    4. Servidor autentica e aceita
    5. Troca de mensagens em tempo real
    
    Tipos de mensagem suportados:
    - authenticate: Autenticar com JWT
    - join_room: Entrar em sala específica
    - leave_room: Sair da sala atual
    - heartbeat: Manter conexão viva
    - get_room_users: Listar usuários da sala
    - send_message: Enviar mensagem para sala
    - get_stats: Estatísticas do sistema
    """
    
    connection_info = None
    
    try:
        # Conectar sem autenticação inicialmente
        connection_info = await connection_manager.connect(
            websocket=websocket,
            user_id=None,
            room="general",
            require_auth=True
        )
        
        logger.info(f"New WebSocket connection established")
        
        # Loop principal de mensagens
        while True:
            try:
                # Receber mensagem
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    await ws_handler._send_error(websocket, "Invalid JSON format")
                    continue
                
                # Processar mensagem
                await ws_handler.handle_message(websocket, message_data)
                
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected normally")
                break
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await ws_handler._send_error(websocket, f"Processing error: {str(e)}")
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during setup")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        
    finally:
        # Cleanup da conexão
        if connection_info:
            await connection_manager.disconnect(websocket)

@router.websocket("/ws/{room}")
async def websocket_room_endpoint(websocket: WebSocket, room: str):
    """
    🏠 Endpoint WebSocket para sala específica
    """
    connection_info = None
    
    try:
        # Conectar diretamente à sala
        connection_info = await connection_manager.connect(
            websocket=websocket,
            user_id=None,
            room=room,
            require_auth=True
        )
        
        logger.info(f"New WebSocket connection to room: {room}")
        
        # Loop principal de mensagens
        while True:
            try:
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    await ws_handler._send_error(websocket, "Invalid JSON format")
                    continue
                
                await ws_handler.handle_message(websocket, message_data)
                
            except WebSocketDisconnect:
                break
                
            except Exception as e:
                logger.error(f"Error in room WebSocket: {e}")
                await ws_handler._send_error(websocket, str(e))
    
    except WebSocketDisconnect:
        pass
    
    except Exception as e:
        logger.error(f"Room WebSocket error: {e}")
        
    finally:
        if connection_info:
            await connection_manager.disconnect(websocket)

# HTTP endpoints para gerenciar WebSocket
@router.get("/ws/stats")
async def get_websocket_stats():
    """
    📊 Estatísticas do sistema WebSocket
    """
    return connection_manager.get_stats()

@router.get("/ws/rooms")
async def list_active_rooms():
    """
    🏠 Listar salas ativas
    """
    stats = connection_manager.get_stats()
    return {
        "active_rooms": list(connection_manager.active_connections.keys()),
        "room_details": stats.get("rooms_with_users", {})
    }

@router.get("/ws/rooms/{room}/users")
async def get_room_users_http(room: str):
    """
    👥 Listar usuários de uma sala via HTTP
    """
    users = await connection_manager.get_room_users(room)
    return {
        "room": room,
        "users": users,
        "count": len(users)
    }

@router.post("/ws/broadcast")
async def broadcast_message(message_data: dict):
    """
    📡 Broadcast mensagem para sala específica (HTTP API)
    
    Exemplo de payload:
    {
        "room": "dashboard",
        "type": "appointment_created",
        "data": {
            "appointment_id": 123,
            "patient_name": "João",
            "date": "2025-09-08T10:00:00"
        }
    }
    """
    
    room = message_data.get("room", "general")
    message_type = message_data.get("type", "system_notification")
    data = message_data.get("data", {})
    
    broadcast_msg = {
        "type": message_type,
        "data": data,
        "room": room,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Broadcast para sala
    sent_count = 0
    if room in connection_manager.active_connections:
        for connection_info in connection_manager.active_connections[room]:
            try:
                await connection_info.websocket.send_text(json.dumps(broadcast_msg))
                sent_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
    
    return {
        "success": True,
        "message": "Broadcast sent",
        "recipients": sent_count,
        "room": room,
        "type": message_type
    }
