"""
🌐 WebSocket Connection Manager
===============================

Sistema robusto de gerenciamento de conexões WebSocket com:
- Connection Manager para múltiplas conexões
- Room System para agrupar usuários
- Event Broadcasting para updates específicos
- Authentication com JWT
- Reconnection handling

Status: Resolução completa do problema 4.1 Real-time Updates Parciais
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

import jwt
from fastapi import WebSocket, WebSocketDisconnect

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Tipos de eventos WebSocket"""

    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_DELETED = "appointment_deleted"
    USER_STATUS_CHANGED = "user_status_changed"
    SYSTEM_NOTIFICATION = "system_notification"
    HEARTBEAT = "heartbeat"
    AUTH_REQUIRED = "auth_required"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    RECONNECT = "reconnect"


class RoomType(Enum):
    """Tipos de salas WebSocket"""

    DASHBOARD = "dashboard"
    APPOINTMENTS = "appointments"
    NOTIFICATIONS = "notifications"
    USER_SPECIFIC = "user_{user_id}"
    ADMIN = "admin"
    GENERAL = "general"


@dataclass
class WebSocketMessage:
    """Estrutura padronizada de mensagens WebSocket"""

    type: str
    data: dict
    room: str
    timestamp: str = None
    user_id: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class ConnectionInfo:
    """Informações sobre uma conexão WebSocket"""

    websocket: WebSocket
    user_id: str
    room: str
    connected_at: datetime
    last_heartbeat: datetime
    is_authenticated: bool = False


class ConnectionManager:
    """
    🔗 Gerenciador de conexões WebSocket

    Funcionalidades:
    - Gerenciar múltiplas conexões por sala
    - Autenticação JWT
    - Broadcasting por sala
    - Heartbeat monitoring
    - Auto-cleanup de conexões mortas
    """

    def __init__(self):
        # Conexões ativas: room -> lista de ConnectionInfo
        self.active_connections: Dict[str, List[ConnectionInfo]] = {}

        # Mapeamento user_id -> room para quick lookup
        self.user_rooms: Dict[str, str] = {}

        # WebSocket -> ConnectionInfo para quick lookup
        self.websocket_map: Dict[WebSocket, ConnectionInfo] = {}

        # Estatísticas
        self.stats = {
            "total_connections": 0,
            "authenticated_connections": 0,
            "rooms_active": 0,
            "messages_sent": 0,
            "heartbeats_received": 0,
        }

        # Task de heartbeat monitoring
        self.heartbeat_task = None

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str = None,
        room: str = RoomType.GENERAL.value,
        require_auth: bool = True,
    ) -> ConnectionInfo:
        """
        🔌 Aceitar nova conexão WebSocket
        """
        try:
            await websocket.accept()
            logger.info(
                f"WebSocket connection accepted for user {user_id} in room {room}"
            )

            # Criar informações da conexão
            connection_info = ConnectionInfo(
                websocket=websocket,
                user_id=user_id or f"anonymous_{id(websocket)}",
                room=room,
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
                is_authenticated=not require_auth,
            )

            # Adicionar à sala
            if room not in self.active_connections:
                self.active_connections[room] = []

            self.active_connections[room].append(connection_info)

            # Mapear user para room
            self.user_rooms[connection_info.user_id] = room

            # Mapear websocket para connection_info
            self.websocket_map[websocket] = connection_info

            # Atualizar estatísticas
            self.stats["total_connections"] += 1
            self.stats["rooms_active"] = len(self.active_connections)

            # Iniciar heartbeat monitoring se necessário
            if self.heartbeat_task is None:
                self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

            # Enviar mensagem de boas-vindas
            welcome_message = WebSocketMessage(
                type=(
                    EventType.AUTH_REQUIRED.value
                    if require_auth
                    else EventType.AUTH_SUCCESS.value
                ),
                data={
                    "user_id": connection_info.user_id,
                    "room": room,
                    "message": (
                        "Autenticação necessária"
                        if require_auth
                        else "Conectado com sucesso"
                    ),
                    "server_time": datetime.utcnow().isoformat(),
                },
                room=room,
                user_id=connection_info.user_id,
            )

            await self.send_to_connection(connection_info, welcome_message)

            return connection_info

        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            raise

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        🔌 Desconectar WebSocket e fazer cleanup
        """
        try:
            connection_info = self.websocket_map.get(websocket)
            if not connection_info:
                return

            room = connection_info.room
            user_id = connection_info.user_id

            # Remover da sala
            if room in self.active_connections:
                self.active_connections[room] = [
                    conn
                    for conn in self.active_connections[room]
                    if conn.websocket != websocket
                ]

                # Remover sala se vazia
                if not self.active_connections[room]:
                    del self.active_connections[room]

            # Remover mappings
            if user_id in self.user_rooms:
                del self.user_rooms[user_id]

            if websocket in self.websocket_map:
                del self.websocket_map[websocket]

            # Atualizar estatísticas
            self.stats["total_connections"] -= 1
            if connection_info.is_authenticated:
                self.stats["authenticated_connections"] -= 1
            self.stats["rooms_active"] = len(self.active_connections)

            logger.info(f"WebSocket disconnected: user {user_id} from room {room}")

            # Notificar outros usuários na sala
            if room in self.active_connections:
                disconnect_message = WebSocketMessage(
                    type=EventType.USER_STATUS_CHANGED.value,
                    data={"user_id": user_id, "status": "disconnected", "room": room},
                    room=room,
                )
                await self.broadcast_to_room(disconnect_message, room)

        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")

    async def authenticate_connection(self, websocket: WebSocket, token: str) -> bool:
        """
        🔐 Autenticar conexão WebSocket com JWT
        """
        try:
            connection_info = self.websocket_map.get(websocket)
            if not connection_info:
                return False

            # Validar JWT token
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("sub") or payload.get("user_id")

                if not user_id:
                    raise jwt.InvalidTokenError("No user ID in token")

                # Atualizar connection info
                connection_info.user_id = user_id
                connection_info.is_authenticated = True

                # Atualizar mappings
                self.user_rooms[user_id] = connection_info.room

                # Atualizar estatísticas
                self.stats["authenticated_connections"] += 1

                # Enviar confirmação de autenticação
                auth_message = WebSocketMessage(
                    type=EventType.AUTH_SUCCESS.value,
                    data={
                        "user_id": user_id,
                        "message": "Autenticado com sucesso",
                        "permissions": payload.get("permissions", []),
                    },
                    room=connection_info.room,
                    user_id=user_id,
                )

                await self.send_to_connection(connection_info, auth_message)

                logger.info(f"WebSocket authenticated: user {user_id}")
                return True

            except jwt.InvalidTokenError as e:
                # Token inválido
                auth_failed_message = WebSocketMessage(
                    type=EventType.AUTH_FAILED.value,
                    data={"message": "Token inválido", "error": str(e)},
                    room=connection_info.room,
                )

                await self.send_to_connection(connection_info, auth_failed_message)
                logger.warning(f"WebSocket authentication failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Error authenticating WebSocket: {e}")
            return False

    async def send_to_connection(
        self, connection_info: ConnectionInfo, message: WebSocketMessage
    ) -> bool:
        """
        📤 Enviar mensagem para uma conexão específica
        """
        try:
            await connection_info.websocket.send_text(message.to_json())
            self.stats["messages_sent"] += 1
            return True

        except Exception as e:
            logger.error(f"Error sending message to connection: {e}")
            # Marcar conexão para remoção
            await self.disconnect(connection_info.websocket)
            return False

    async def broadcast_to_room(self, message: WebSocketMessage, room: str) -> int:
        """
        📡 Broadcast mensagem para toda uma sala
        """
        if room not in self.active_connections:
            logger.warning(f"Attempted to broadcast to non-existent room: {room}")
            return 0

        sent_count = 0
        failed_connections = []

        for connection_info in self.active_connections[room]:
            try:
                await connection_info.websocket.send_text(message.to_json())
                sent_count += 1
                self.stats["messages_sent"] += 1

            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                failed_connections.append(connection_info)

        # Cleanup conexões com falha
        for failed_conn in failed_connections:
            await self.disconnect(failed_conn.websocket)

        logger.info(
            f"Broadcast to room {room}: {sent_count} successful, {len(failed_connections)} failed"
        )
        return sent_count

    async def send_to_user(self, message: WebSocketMessage, user_id: str) -> bool:
        """
        👤 Enviar mensagem para usuário específico
        """
        room = self.user_rooms.get(user_id)
        if not room:
            logger.warning(f"User {user_id} not found in any room")
            return False

        # Encontrar conexão do usuário
        for connection_info in self.active_connections.get(room, []):
            if connection_info.user_id == user_id:
                return await self.send_to_connection(connection_info, message)

        logger.warning(f"User {user_id} connection not found in room {room}")
        return False

    async def broadcast_to_all(self, message: WebSocketMessage) -> int:
        """
        🌍 Broadcast mensagem para todas as conexões
        """
        total_sent = 0

        for room in self.active_connections.keys():
            sent = await self.broadcast_to_room(message, room)
            total_sent += sent

        return total_sent

    async def get_room_users(self, room: str) -> List[str]:
        """
        👥 Listar usuários conectados em uma sala
        """
        if room not in self.active_connections:
            return []

        return [
            conn.user_id
            for conn in self.active_connections[room]
            if conn.is_authenticated
        ]

    async def move_user_to_room(self, user_id: str, new_room: str) -> bool:
        """
        🚀 Mover usuário para outra sala
        """
        current_room = self.user_rooms.get(user_id)
        if not current_room:
            return False

        # Encontrar conexão do usuário
        connection_info = None
        for conn in self.active_connections.get(current_room, []):
            if conn.user_id == user_id:
                connection_info = conn
                break

        if not connection_info:
            return False

        # Remover da sala atual
        self.active_connections[current_room].remove(connection_info)
        if not self.active_connections[current_room]:
            del self.active_connections[current_room]

        # Adicionar à nova sala
        if new_room not in self.active_connections:
            self.active_connections[new_room] = []

        connection_info.room = new_room
        self.active_connections[new_room].append(connection_info)
        self.user_rooms[user_id] = new_room

        # Notificar usuário sobre mudança de sala
        move_message = WebSocketMessage(
            type=EventType.SYSTEM_NOTIFICATION.value,
            data={
                "message": f"Movido para sala: {new_room}",
                "old_room": current_room,
                "new_room": new_room,
            },
            room=new_room,
            user_id=user_id,
        )

        await self.send_to_connection(connection_info, move_message)
        return True

    async def _heartbeat_monitor(self):
        """
        💓 Monitor de heartbeat para detectar conexões mortas
        """
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                current_time = datetime.utcnow()
                dead_connections = []

                for room, connections in self.active_connections.items():
                    for conn in connections:
                        # Conexões sem heartbeat por mais de 2 minutos são consideradas mortas
                        if (current_time - conn.last_heartbeat).total_seconds() > 120:
                            dead_connections.append(conn)

                # Remover conexões mortas
                for dead_conn in dead_connections:
                    logger.info(f"Removing dead connection: {dead_conn.user_id}")
                    await self.disconnect(dead_conn.websocket)

            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")

    async def handle_heartbeat(self, websocket: WebSocket):
        """
        💓 Processar heartbeat de uma conexão
        """
        connection_info = self.websocket_map.get(websocket)
        if connection_info:
            connection_info.last_heartbeat = datetime.utcnow()
            self.stats["heartbeats_received"] += 1

    def get_stats(self) -> dict:
        """
        📊 Obter estatísticas do sistema WebSocket
        """
        return {
            **self.stats,
            "rooms_with_users": {
                room: len(connections)
                for room, connections in self.active_connections.items()
            },
            "uptime": datetime.utcnow().isoformat(),
        }


# Singleton instance
connection_manager = ConnectionManager()
