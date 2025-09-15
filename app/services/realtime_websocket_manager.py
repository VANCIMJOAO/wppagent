"""
🌐 Sistema WebSocket Real-Time Avançado
=======================================

Sistema completo de WebSocket para atualizações em tempo real:
- Gerenciamento de conexões robustas
- Broadcasting inteligente por tópicos
- Reconexão automática
- Queue de mensagens
- Health monitoring
- Integração com modelos de dados
"""

import asyncio
import json
import logging
import threading
import time
import uuid
import weakref
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..services.structured_apm import get_structured_logger
from ..utils.logger import get_logger

logger = get_structured_logger(__name__)


class RealtimeEventType(Enum):
    """Tipos de eventos em tempo real otimizados"""

    # ============= CHAT & MENSAGENS =============
    NEW_MESSAGE = "new_message"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    CONVERSATION_UPDATED = "conversation_updated"

    # ============= AGENDAMENTOS =============
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_REMINDER = "appointment_reminder"

    # ============= USUÁRIOS & CLIENTES =============
    USER_STATUS_CHANGED = "user_status_changed"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    CLIENT_CREATED = "client_created"
    CLIENT_UPDATED = "client_updated"

    # ============= DASHBOARD & ANALYTICS =============
    DASHBOARD_STATS_UPDATE = "dashboard_stats_update"
    KPI_UPDATE = "kpi_update"
    ANALYTICS_UPDATE = "analytics_update"
    METRIC_INCREMENT = "metric_increment"

    # ============= SISTEMA =============
    WHATSAPP_STATUS_CHANGE = "whatsapp_status_change"
    SYSTEM_ALERT = "system_alert"
    SYSTEM_NOTIFICATION = "system_notification"
    CONNECTION_STATUS = "connection_status"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_RESPONSE = "heartbeat_response"

    # ============= ADMINISTRAÇÃO =============
    ADMIN_ALERT = "admin_alert"
    CACHE_INVALIDATED = "cache_invalidated"
    DATA_SYNC_REQUIRED = "data_sync_required"


class ConnectionStatus(Enum):
    """Status das conexões WebSocket"""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """Estrutura padronizada de mensagens WebSocket"""

    type: str
    data: Dict[str, Any]
    timestamp: str
    id: str
    room: Optional[str] = None
    target_user: Optional[str] = None
    source_user: Optional[str] = None
    priority: int = 1
    expires_at: Optional[str] = None


@dataclass
class ConnectionInfo:
    """Informações de uma conexão WebSocket"""

    websocket: WebSocket
    user_id: str
    connection_id: str
    subscriptions: Set[str]
    status: ConnectionStatus
    connected_at: datetime
    last_heartbeat: datetime
    last_activity: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    room: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RoomInfo:
    """Informações de uma sala/tópico"""

    room_id: str
    connections: Set[str]  # connection_ids
    created_at: datetime
    last_activity: datetime
    message_count: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RealtimeWebSocketManager:
    """Gerenciador avançado de WebSocket para real-time"""

    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(
            set
        )  # user_id -> connection_ids
        self.rooms: Dict[str, RoomInfo] = {}
        self.room_connections: Dict[str, Set[str]] = defaultdict(
            set
        )  # room_id -> connection_ids

        # Message queues and broadcasting
        self.message_queue: deque = deque(maxlen=10000)  # Circular buffer
        self.broadcast_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # Health monitoring
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_failed": 0,
            "rooms_active": 0,
            "uptime_started": datetime.now(UTC),
            "last_cleanup": datetime.now(UTC),
        }

        # Background tasks
        self._heartbeat_task = None
        self._cleanup_task = None
        self._running = False

        logger.info("🌐 RealtimeWebSocketManager inicializado")

    async def start_background_tasks(self):
        """Inicia tarefas em background"""
        if self._running:
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("🚀 Tarefas em background iniciadas")

    async def stop_background_tasks(self):
        """Para tarefas em background"""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

        logger.info("⏹️ Tarefas em background paradas")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        subscriptions: List[str] = None,
        room: str = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Conecta um WebSocket e registra a conexão

        Returns:
            connection_id: ID único da conexão
        """
        try:
            # Accept WebSocket connection
            await websocket.accept()

            # Generate connection ID
            connection_id = f"{user_id}_{uuid.uuid4().hex[:8]}_{int(time.time())}"

            # Create connection info
            connection = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                connection_id=connection_id,
                subscriptions=set(subscriptions or []),
                status=ConnectionStatus.CONNECTED,
                connected_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                room=room,
                metadata=metadata or {},
            )

            # Register connection
            self.connections[connection_id] = connection
            self.user_connections[user_id].add(connection_id)

            # Join room if specified
            if room:
                await self._join_room(connection_id, room)

            # Join subscription rooms
            for subscription in connection.subscriptions:
                await self._join_room(connection_id, f"topic_{subscription}")

            # Update stats
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = len(self.connections)

            # Send welcome message
            await self._send_to_connection(
                connection_id,
                RealtimeEventType.CONNECTION_STATUS,
                {
                    "status": "connected",
                    "connection_id": connection_id,
                    "subscriptions": list(connection.subscriptions),
                    "room": room,
                    "server_time": datetime.utcnow().isoformat(),
                },
            )

            # Notify room about new connection
            if room:
                await self.broadcast_to_room(
                    room,
                    RealtimeEventType.USER_ONLINE,
                    {"user_id": user_id, "connection_id": connection_id},
                    exclude_connections={connection_id},
                )

            logger.info(
                f"🔌 Conexão WebSocket estabelecida: {user_id} ({connection_id}) -> {subscriptions}"
            )

            # Start background tasks if not running
            if not self._running:
                await self.start_background_tasks()

            return connection_id

        except Exception as e:
            logger.error(f"❌ Erro ao conectar WebSocket: {e}")
            try:
                await websocket.close(code=1011, reason="Connection error")
            except:
                pass
            raise

    async def disconnect(self, connection_id: str, reason: str = "Client disconnected"):
        """Desconecta um WebSocket e limpa recursos"""
        if connection_id not in self.connections:
            return

        connection = self.connections[connection_id]

        try:
            # Update status
            connection.status = ConnectionStatus.DISCONNECTING

            # Notify room about disconnection
            if connection.room:
                await self.broadcast_to_room(
                    connection.room,
                    RealtimeEventType.USER_OFFLINE,
                    {"user_id": connection.user_id, "connection_id": connection_id},
                    exclude_connections={connection_id},
                )

            # Remove from rooms
            for room_id in list(self.room_connections.keys()):
                if connection_id in self.room_connections[room_id]:
                    await self._leave_room(connection_id, room_id)

            # Close WebSocket
            if connection.websocket and not connection.websocket.client_state.CLOSED:
                await connection.websocket.close(code=1000, reason=reason)

            # Clean up references
            del self.connections[connection_id]
            self.user_connections[connection.user_id].discard(connection_id)

            # Clean empty user references
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]

            # Update stats
            self.stats["active_connections"] = len(self.connections)

            logger.info(
                f"🔌 Conexão WebSocket desconectada: {connection.user_id} ({connection_id}) - {reason}"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao desconectar WebSocket: {e}")

    async def _join_room(self, connection_id: str, room_id: str):
        """Adiciona conexão a uma sala"""
        if connection_id not in self.connections:
            return False

        # Create room if doesn't exist
        if room_id not in self.rooms:
            self.rooms[room_id] = RoomInfo(
                room_id=room_id,
                connections=set(),
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
            )

        # Add to room
        self.rooms[room_id].connections.add(connection_id)
        self.room_connections[room_id].add(connection_id)
        self.rooms[room_id].last_activity = datetime.utcnow()

        # Update stats
        self.stats["rooms_active"] = len(
            [r for r in self.rooms.values() if r.connections]
        )

        return True

    async def _leave_room(self, connection_id: str, room_id: str):
        """Remove conexão de uma sala"""
        if room_id in self.rooms:
            self.rooms[room_id].connections.discard(connection_id)

            # Remove room if empty
            if not self.rooms[room_id].connections:
                del self.rooms[room_id]

        if room_id in self.room_connections:
            self.room_connections[room_id].discard(connection_id)

            # Remove empty room reference
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]

        # Update stats
        self.stats["rooms_active"] = len(
            [r for r in self.rooms.values() if r.connections]
        )

    async def _send_to_connection(
        self,
        connection_id: str,
        event_type: RealtimeEventType,
        data: Dict[str, Any],
        priority: int = 1,
    ) -> bool:
        """Envia mensagem para uma conexão específica"""
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]

        try:
            message = WebSocketMessage(
                type=event_type.value,
                data=data,
                timestamp=datetime.utcnow().isoformat(),
                id=uuid.uuid4().hex,
                source_user="system",
                target_user=connection.user_id,
                priority=priority,
            )

            # Add to queue for history
            self.message_queue.append(message)

            # Send message
            await connection.websocket.send_text(json.dumps(asdict(message)))

            # Update activity
            connection.last_activity = datetime.utcnow()
            self.stats["messages_sent"] += 1

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem para {connection_id}: {e}")
            self.stats["messages_failed"] += 1

            # Disconnect on error
            await self.disconnect(connection_id, "Send error")
            return False

    async def broadcast_to_room(
        self,
        room_id: str,
        event_type: RealtimeEventType,
        data: Dict[str, Any],
        exclude_connections: Set[str] = None,
        priority: int = 1,
    ) -> int:
        """
        Faz broadcast de mensagem para uma sala

        Returns:
            Número de conexões que receberam a mensagem
        """
        if room_id not in self.room_connections:
            return 0

        exclude_connections = exclude_connections or set()
        connections_to_send = self.room_connections[room_id] - exclude_connections

        if not connections_to_send:
            return 0

        # Update room activity
        if room_id in self.rooms:
            self.rooms[room_id].last_activity = datetime.utcnow()
            self.rooms[room_id].message_count += 1

        # Send to all connections in parallel
        tasks = []
        for connection_id in connections_to_send:
            if connection_id in self.connections:
                tasks.append(
                    self._send_to_connection(connection_id, event_type, data, priority)
                )

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_sends = sum(1 for r in results if r is True)

            logger.info(
                f"📡 Broadcast para sala '{room_id}': {successful_sends}/{len(tasks)} conexões"
            )
            return successful_sends

        return 0

    async def broadcast_to_subscriptions(
        self,
        subscription: str,
        event_type: RealtimeEventType,
        data: Dict[str, Any],
        priority: int = 1,
    ) -> int:
        """Faz broadcast para todas as conexões inscritas em um tópico"""
        room_id = f"topic_{subscription}"
        return await self.broadcast_to_room(
            room_id, event_type, data, priority=priority
        )

    async def broadcast_to_user(
        self,
        user_id: str,
        event_type: RealtimeEventType,
        data: Dict[str, Any],
        priority: int = 1,
    ) -> int:
        """Faz broadcast para todas as conexões de um usuário"""
        if user_id not in self.user_connections:
            return 0

        tasks = []
        for connection_id in self.user_connections[user_id]:
            if connection_id in self.connections:
                tasks.append(
                    self._send_to_connection(connection_id, event_type, data, priority)
                )

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_sends = sum(1 for r in results if r is True)

            logger.info(
                f"📡 Broadcast para usuário '{user_id}': {successful_sends}/{len(tasks)} conexões"
            )
            return successful_sends

        return 0

    async def broadcast_global(
        self,
        event_type: RealtimeEventType,
        data: Dict[str, Any],
        exclude_connections: Set[str] = None,
        priority: int = 1,
    ) -> int:
        """Faz broadcast global para todas as conexões"""
        exclude_connections = exclude_connections or set()

        tasks = []
        for connection_id in self.connections:
            if connection_id not in exclude_connections:
                tasks.append(
                    self._send_to_connection(connection_id, event_type, data, priority)
                )

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_sends = sum(1 for r in results if r is True)

            logger.info(f"📡 Broadcast global: {successful_sends}/{len(tasks)} conexões")
            return successful_sends

        return 0

    async def handle_client_message(self, connection_id: str, data: Dict[str, Any]):
        """Processa mensagens recebidas do cliente"""
        if connection_id not in self.connections:
            return

        connection = self.connections[connection_id]
        connection.last_activity = datetime.utcnow()

        message_type = data.get("type")

        try:
            if message_type == "heartbeat":
                connection.last_heartbeat = datetime.utcnow()
                await self._send_to_connection(
                    connection_id,
                    RealtimeEventType.HEARTBEAT_RESPONSE,
                    {"timestamp": datetime.utcnow().isoformat()},
                )

            elif message_type == "join_room":
                room_id = data.get("room")
                if room_id:
                    await self._join_room(connection_id, room_id)
                    await self._send_to_connection(
                        connection_id,
                        RealtimeEventType.CONNECTION_STATUS,
                        {"status": "joined_room", "room": room_id},
                    )

            elif message_type == "leave_room":
                room_id = data.get("room")
                if room_id:
                    await self._leave_room(connection_id, room_id)
                    await self._send_to_connection(
                        connection_id,
                        RealtimeEventType.CONNECTION_STATUS,
                        {"status": "left_room", "room": room_id},
                    )

            elif message_type == "subscribe":
                subscription = data.get("subscription")
                if subscription:
                    connection.subscriptions.add(subscription)
                    await self._join_room(connection_id, f"topic_{subscription}")

            elif message_type == "unsubscribe":
                subscription = data.get("subscription")
                if subscription:
                    connection.subscriptions.discard(subscription)
                    await self._leave_room(connection_id, f"topic_{subscription}")

            elif message_type == "typing_start":
                # Broadcast typing indicator
                if connection.room:
                    await self.broadcast_to_room(
                        connection.room,
                        RealtimeEventType.TYPING_START,
                        {"user_id": connection.user_id},
                        exclude_connections={connection_id},
                    )

            elif message_type == "typing_stop":
                # Broadcast typing stop
                if connection.room:
                    await self.broadcast_to_room(
                        connection.room,
                        RealtimeEventType.TYPING_STOP,
                        {"user_id": connection.user_id},
                        exclude_connections={connection_id},
                    )

            else:
                logger.warning(f"⚠️ Tipo de mensagem desconhecido: {message_type}")

        except Exception as e:
            logger.error(
                f"❌ Erro ao processar mensagem do cliente {connection_id}: {e}"
            )

    async def _heartbeat_loop(self):
        """Loop de heartbeat para monitorar conexões"""
        while self._running:
            try:
                now = datetime.utcnow()
                stale_connections = []

                for connection_id, connection in self.connections.items():
                    # Check if connection is stale (no heartbeat in 60s)
                    if now - connection.last_heartbeat > timedelta(seconds=60):
                        stale_connections.append(connection_id)

                # Disconnect stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id, "Heartbeat timeout")

                if stale_connections:
                    logger.info(
                        f"🔄 Limpeza de heartbeat: {len(stale_connections)} conexões removidas"
                    )

                # Send heartbeat to all active connections
                for connection_id in list(self.connections.keys()):
                    await self._send_to_connection(
                        connection_id,
                        RealtimeEventType.HEARTBEAT,
                        {"timestamp": now.isoformat()},
                    )

                await asyncio.sleep(30)  # Heartbeat every 30 seconds

            except Exception as e:
                logger.error(f"❌ Erro no loop de heartbeat: {e}")
                await asyncio.sleep(10)

    async def _cleanup_loop(self):
        """Loop de limpeza para manter sistema saudável"""
        while self._running:
            try:
                now = datetime.utcnow()

                # Clean old rooms with no activity
                old_rooms = []
                for room_id, room in self.rooms.items():
                    if not room.connections and now - room.last_activity > timedelta(
                        hours=1
                    ):
                        old_rooms.append(room_id)

                for room_id in old_rooms:
                    del self.rooms[room_id]
                    if room_id in self.room_connections:
                        del self.room_connections[room_id]

                if old_rooms:
                    logger.info(
                        f"🧹 Limpeza de salas: {len(old_rooms)} salas vazias removidas"
                    )

                # Update cleanup time
                self.stats["last_cleanup"] = now

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except Exception as e:
                logger.error(f"❌ Erro no loop de limpeza: {e}")
                await asyncio.sleep(60)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        now = datetime.utcnow()
        uptime = now - self.stats["uptime_started"]

        return {
            "total_connections": self.stats["total_connections"],
            "active_connections": len(self.connections),
            "active_users": len(self.user_connections),
            "active_rooms": len([r for r in self.rooms.values() if r.connections]),
            "total_rooms": len(self.rooms),
            "messages_sent": self.stats["messages_sent"],
            "messages_failed": self.stats["messages_failed"],
            "message_queue_size": len(self.message_queue),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime),
            "last_cleanup": self.stats["last_cleanup"].isoformat(),
            "system_healthy": len(self.connections) > 0 or uptime.total_seconds() < 300,
            "rooms_info": [
                {
                    "room_id": room.room_id,
                    "connections": len(room.connections),
                    "message_count": room.message_count,
                    "last_activity": room.last_activity.isoformat(),
                }
                for room in self.rooms.values()
            ][
                :10
            ],  # Top 10 rooms
        }

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Retorna informações de uma conexão específica"""
        if connection_id not in self.connections:
            return None

        connection = self.connections[connection_id]
        return {
            "connection_id": connection.connection_id,
            "user_id": connection.user_id,
            "status": connection.status.value,
            "connected_at": connection.connected_at.isoformat(),
            "last_heartbeat": connection.last_heartbeat.isoformat(),
            "last_activity": connection.last_activity.isoformat(),
            "subscriptions": list(connection.subscriptions),
            "room": connection.room,
            "metadata": connection.metadata,
        }

    async def cleanup_all(self):
        """Limpa todas as conexões e para o sistema"""
        logger.info("🧹 Iniciando limpeza completa do sistema WebSocket...")

        # Stop background tasks
        await self.stop_background_tasks()

        # Disconnect all connections
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id, "Server shutdown")

        # Clear all data structures
        self.connections.clear()
        self.user_connections.clear()
        self.rooms.clear()
        self.room_connections.clear()
        self.message_queue.clear()

        logger.info("✅ Limpeza completa finalizada")


# Singleton instance
realtime_manager = RealtimeWebSocketManager()


def get_realtime_manager() -> RealtimeWebSocketManager:
    """Retorna a instância singleton do gerenciador"""
    return realtime_manager
