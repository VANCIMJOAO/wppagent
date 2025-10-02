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
from starlette.websockets import WebSocketState
from pydantic import BaseModel
from collections import deque

# CORREÇÃO: Imports para validação de schema
from app.schemas.websocket_events import validate_event_data, get_event_schema, EVENT_SCHEMA_MAP
from sqlalchemy.orm import Session
import json

from ..config.logging_config import get_optimized_logger

logger = get_optimized_logger(__name__)

# ============= UTILITY FUNCTIONS =============
def safe_json_serialize(data: Any) -> str:
    """
    CORREÇÃO: Serializa dados para JSON de forma segura, convertendo datetime para string
    
    Args:
        data: Dados para serializar
        
    Returns:
        String JSON serializada
    """
    def json_serializer(obj):
        """Serializador customizado para datetime e outros tipos"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    return json.dumps(data, default=json_serializer, ensure_ascii=False)

@dataclass
class PendingMessage:
    """CORREÇÃO: Mensagem pendente de confirmação ACK"""
    message: Dict[str, Any]
    sent_at: datetime
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class AckStats:
    """CORREÇÃO: Estatísticas de confirmação de entrega"""
    total_sent: int = 0
    total_acked: int = 0
    total_timeout: int = 0
    total_retry: int = 0
    avg_ack_time: float = 0.0
    pending_count: int = 0

class RateLimiter:
    """
    CORREÇÃO: Sistema de Rate Limiting para WebSocket
    
    Controla a taxa de mensagens por conexão para prevenir abuso e DoS.
    """
    
    def __init__(self, max_messages: int = 100, window_seconds: int = 60):
        """
        Inicializa o rate limiter
        
        Args:
            max_messages: Número máximo de mensagens por janela de tempo
            window_seconds: Duração da janela de tempo em segundos
        """
        self.max_messages = max_messages
        self.window = timedelta(seconds=window_seconds)
        self.message_timestamps: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_messages)
        )
        self.blocked_connections: Set[str] = set()
        self.rate_limit_stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "current_active_connections": 0,
            "rate_limit_hits": 0
        }
    
    def is_allowed(self, connection_id: str) -> bool:
        """
        CORREÇÃO: Verifica se uma conexão pode enviar mensagem
        
        Args:
            connection_id: ID da conexão
            
        Returns:
            True se a conexão pode enviar mensagem
        """
        try:
            now = datetime.now(UTC)
            timestamps = self.message_timestamps[connection_id]
            
            # Remover timestamps antigos (fora da janela)
            while timestamps and now - timestamps[0] > self.window:
                timestamps.popleft()
            
            # Atualizar estatísticas
            self.rate_limit_stats["total_requests"] += 1
            
            # Verificar se conexão está bloqueada
            if connection_id in self.blocked_connections:
                self.rate_limit_stats["blocked_requests"] += 1
                return False
            
            # Verificar limite de mensagens
            if len(timestamps) >= self.max_messages:
                self.rate_limit_stats["rate_limit_hits"] += 1
                self.blocked_connections.add(connection_id)
                logger.warning(f"🚫 Rate limit excedido para conexão {connection_id}")
                return False
            
            # Adicionar timestamp atual
            timestamps.append(now)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro no rate limiter para {connection_id}: {e}")
            return False
    
    def unblock_connection(self, connection_id: str):
        """
        CORREÇÃO: Desbloqueia uma conexão
        
        Args:
            connection_id: ID da conexão
        """
        try:
            if connection_id in self.blocked_connections:
                self.blocked_connections.remove(connection_id)
                logger.info(f"🔓 Conexão {connection_id} desbloqueada")
        except Exception as e:
            logger.error(f"❌ Erro ao desbloquear conexão {connection_id}: {e}")
    
    def cleanup_old_connections(self, active_connections: Set[str]):
        """
        CORREÇÃO: Limpa dados de conexões inativas
        
        Args:
            active_connections: Set de conexões ativas
        """
        try:
            # Remover timestamps de conexões inativas
            inactive_connections = set(self.message_timestamps.keys()) - active_connections
            for conn_id in inactive_connections:
                if conn_id in self.message_timestamps:
                    del self.message_timestamps[conn_id]
                if conn_id in self.blocked_connections:
                    self.blocked_connections.remove(conn_id)
            
            # Atualizar estatísticas
            self.rate_limit_stats["current_active_connections"] = len(active_connections)
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de conexões inativas: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        CORREÇÃO: Retorna estatísticas do rate limiter
        
        Returns:
            Estatísticas do rate limiter
        """
        try:
            total_requests = self.rate_limit_stats["total_requests"]
            blocked_requests = self.rate_limit_stats["blocked_requests"]
            
            return {
                "max_messages_per_window": self.max_messages,
                "window_seconds": self.window.total_seconds(),
                "total_requests": total_requests,
                "blocked_requests": blocked_requests,
                "rate_limit_hits": self.rate_limit_stats["rate_limit_hits"],
                "current_active_connections": self.rate_limit_stats["current_active_connections"],
                "blocked_connections_count": len(self.blocked_connections),
                "block_rate": round((blocked_requests / max(total_requests, 1)) * 100, 2),
                "timestamp": datetime.now(UTC).isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas do rate limiter: {e}")
            return {}
    
    def reset_stats(self):
        """CORREÇÃO: Reseta estatísticas do rate limiter"""
        try:
            self.rate_limit_stats = {
                "total_requests": 0,
                "blocked_requests": 0,
                "current_active_connections": 0,
                "rate_limit_hits": 0
            }
            logger.info("🔄 Estatísticas do rate limiter resetadas")
        except Exception as e:
            logger.error(f"❌ Erro ao resetar estatísticas: {e}")


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
    ACK = "ack"  # CORREÇÃO: Confirmação de entrega
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

    def is_stale(self, timeout_seconds: int = 30) -> bool:
        """
        CORREÇÃO: Verifica se a conexão está obsoleta (sem heartbeat)
        
        Args:
            timeout_seconds: Timeout em segundos (padrão: 30s)
            
        Returns:
            True se a conexão está obsoleta
        """
        elapsed = (datetime.now(UTC) - self.last_heartbeat).total_seconds()
        return elapsed > timeout_seconds

    def update_heartbeat(self):
        """CORREÇÃO: Atualiza timestamp do último heartbeat"""
        self.last_heartbeat = datetime.now(UTC)

    def get_heartbeat_age_seconds(self) -> float:
        """CORREÇÃO: Retorna idade do último heartbeat em segundos"""
        return (datetime.now(UTC) - self.last_heartbeat).total_seconds()

    def is_mobile_connection(self) -> bool:
        """CORREÇÃO: Detecta se é uma conexão móvel baseada no user_agent"""
        if not self.user_agent:
            return False
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
        return any(indicator in self.user_agent.lower() for indicator in mobile_indicators)


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
        
        # CORREÇÃO: Configurações de timeout de heartbeat
        self.heartbeat_timeout_desktop = 30  # 30 segundos para desktop
        self.heartbeat_timeout_mobile = 60   # 60 segundos para mobile (mais tolerante)
        self.heartbeat_interval = 30         # Envia heartbeat a cada 30 segundos

        # Background tasks
        self._heartbeat_task = None
        self._cleanup_task = None
        self._running = False

        # CORREÇÃO: Sistema de confirmação de entrega (ACK)
        self.pending_acks: Dict[str, Dict[str, PendingMessage]] = defaultdict(dict)  # conn_id -> msg_id -> PendingMessage
        self.ack_stats = AckStats()
        self.ack_timeout = 5.0  # 5 segundos para timeout de ACK
        self.ack_retry_interval = 1.0  # 1 segundo entre tentativas
        self._ack_cleanup_task = None

        # CORREÇÃO: Sistema de recuperação de mensagens na reconexão
        self.message_history: List[Dict[str, Any]] = []  # Histórico de mensagens para recuperação
        self.max_history_size = 10000  # Máximo de mensagens no histórico
        self.last_message_ids: Dict[str, str] = {}  # user_id -> last_message_id
        self.reconnection_recovery_enabled = True  # Flag para habilitar recuperação

        # CORREÇÃO: Sistema de Rate Limiting
        self.rate_limiter = RateLimiter(
            max_messages=100,  # 100 mensagens por janela
            window_seconds=60  # Janela de 60 segundos
        )
        self.rate_limiting_enabled = True  # Flag para habilitar rate limiting

        logger.info("🌐 RealtimeWebSocketManager inicializado")

    async def start_background_tasks(self):
        """Inicia tarefas em background"""
        if self._running:
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._ack_cleanup_task = asyncio.create_task(self._ack_cleanup_loop())  # CORREÇÃO: Task de limpeza de ACKs

        logger.info("🚀 Tarefas em background iniciadas")

    async def stop_background_tasks(self):
        """Para tarefas em background"""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._ack_cleanup_task:  # CORREÇÃO: Parar task de limpeza de ACKs
            self._ack_cleanup_task.cancel()

        logger.info("⏹️ Tarefas em background paradas")

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        subscriptions: List[str] = None,
        room: str = None,
        metadata: Dict[str, Any] = None,
        last_message_id: str = None,
    ) -> str:
        """
        CORREÇÃO: Conecta um WebSocket com limpeza adequada de conexões antigas e recuperação de mensagens

        Args:
            websocket: Conexão WebSocket
            user_id: ID do usuário
            subscriptions: Lista de tópicos para se inscrever
            room: Sala para entrar
            metadata: Metadados adicionais
            last_message_id: ID da última mensagem recebida (para recuperação)

        Returns:
            connection_id: ID único da conexão
        """
        try:
            # CORREÇÃO: 1. FORÇA cleanup completo ANTES de criar nova conexão
            await self._force_cleanup_user(user_id)
            
            # CORREÇÃO: 2. Aguarda um pouco para garantir que cleanup finalizou
            await asyncio.sleep(0.1)

            # Accept WebSocket connection
            await websocket.accept()

            # CORREÇÃO: 3. Gera connection_id único (não user_id)
            connection_id = f"{user_id}_{uuid.uuid4().hex[:8]}_{int(time.time())}"

            # Create connection info
            connection = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                connection_id=connection_id,
                subscriptions=set(subscriptions or []),
                status=ConnectionStatus.CONNECTED,
                connected_at=datetime.now(UTC),
                last_heartbeat=datetime.now(UTC),
                last_activity=datetime.now(UTC),
                room=room,
                metadata=metadata or {},
            )

            # CORREÇÃO: 4. Registra com mapeamento usuário -> conexões
            self.connections[connection_id] = connection
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
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
                    "server_time": datetime.now(UTC).isoformat(),
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

            # CORREÇÃO: 5. Recuperação de mensagens perdidas na reconexão
            if self.reconnection_recovery_enabled and last_message_id:
                await self._recover_missed_messages(connection_id, user_id, last_message_id)

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

    async def _force_cleanup_user(self, user_id: str):
        """
        CORREÇÃO: Força limpeza completa de todas as conexões de um usuário
        
        Garante que todas as conexões antigas sejam completamente limpas
        antes de criar novas conexões, evitando vazamento de memória.
        """
        if user_id not in self.user_connections:
            return
        
        # Obtém todas as conexões do usuário
        user_connection_ids = list(self.user_connections[user_id])
        
        if not user_connection_ids:
            return
        
        logger.info(f"🧹 Forçando limpeza de {len(user_connection_ids)} conexões para usuário {user_id}")
        
        # Desconecta todas as conexões do usuário
        cleanup_tasks = []
        for connection_id in user_connection_ids:
            if connection_id in self.connections:
                cleanup_tasks.append(
                    self.disconnect(connection_id, "Force cleanup before reconnection")
                )
        
        # Aguarda todas as desconexões completarem
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Aguarda um pouco para garantir que cleanup finalizou
        await asyncio.sleep(0.1)
        
        # Verifica se ainda há conexões pendentes
        remaining_connections = [
            conn_id for conn_id in user_connection_ids 
            if conn_id in self.connections
        ]
        
        if remaining_connections:
            logger.warning(f"⚠️ {len(remaining_connections)} conexões ainda pendentes após cleanup forçado")
            # Força remoção direta se necessário
            for conn_id in remaining_connections:
                if conn_id in self.connections:
                    del self.connections[conn_id]
                self.user_connections[user_id].discard(conn_id)
        
        # Limpa referência vazia do usuário
        if not self.user_connections[user_id]:
            del self.user_connections[user_id]
        
        logger.info(f"✅ Cleanup forçado concluído para usuário {user_id}")

    async def disconnect_user(self, user_id: str, reason: str = "User disconnected"):
        """
        CORREÇÃO: Desconecta todas as conexões de um usuário específico
        
        Útil para logout ou limpeza de usuário específico.
        """
        await self._force_cleanup_user(user_id)

    async def cleanup_stale_connections(self) -> int:
        """
        CORREÇÃO: Limpa conexões obsoletas com verificação robusta
        
        Retorna número de conexões limpas.
        """
        if not self.connections:
            return 0
        
        stale_connections = []
        current_time = datetime.now(UTC)
        
        # CORREÇÃO: Identifica conexões obsoletas com timeout diferenciado
        for connection_id, connection in self.connections.items():
            timeout = (
                self.heartbeat_timeout_mobile 
                if connection.is_mobile_connection() 
                else self.heartbeat_timeout_desktop
            )
            if connection.is_stale(timeout_seconds=timeout):
                stale_connections.append(connection_id)
        
        # Limpa conexões obsoletas
        cleaned_count = 0
        for connection_id in stale_connections:
            try:
                await self.disconnect(connection_id, "Stale connection cleanup")
                cleaned_count += 1
            except Exception as e:
                logger.error(f"Erro ao limpar conexão obsoleta {connection_id}: {e}")
                # Força remoção se desconexão falhar
                if connection_id in self.connections:
                    conn = self.connections[connection_id]
                    del self.connections[connection_id]
                    self.user_connections[conn.user_id].discard(connection_id)
                    cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"🧹 Limpeza de conexões: {cleaned_count} conexões obsoletas removidas")
        
        return cleaned_count

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        CORREÇÃO: Retorna estatísticas detalhadas das conexões
        
        Inclui informações sobre limpeza e vazamentos.
        """
        total_connections = len(self.connections)
        active_connections = sum(
            1 for conn in self.connections.values() 
            if conn.status == ConnectionStatus.CONNECTED
        )
        
        # Estatísticas por usuário
        user_stats = {}
        for user_id, conn_ids in self.user_connections.items():
            user_stats[user_id] = {
                "connection_count": len(conn_ids),
                "connection_ids": list(conn_ids),
                "active_connections": sum(
                    1 for conn_id in conn_ids 
                    if conn_id in self.connections and 
                    self.connections[conn_id].status == ConnectionStatus.CONNECTED
                )
            }
        
        # Detecta possíveis vazamentos
        potential_leaks = []
        for user_id, conn_ids in self.user_connections.items():
            active_conns = [
                conn_id for conn_id in conn_ids 
                if conn_id in self.connections
            ]
            if len(active_conns) != len(conn_ids):
                potential_leaks.append({
                    "user_id": user_id,
                    "registered_connections": len(conn_ids),
                    "active_connections": len(active_conns),
                    "orphaned_connections": len(conn_ids) - len(active_conns)
                })
        
        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "stale_connections": total_connections - active_connections,
            "unique_users": len(self.user_connections),
            "user_stats": user_stats,
            "potential_leaks": potential_leaks,
            "cleanup_recommended": len(potential_leaks) > 0 or (total_connections - active_connections) > 0,
            "memory_usage_estimate": total_connections * 1024,  # Estimativa em bytes
        }

    async def force_cleanup_all(self) -> int:
        """
        CORREÇÃO: Força limpeza de todas as conexões
        
        Útil para shutdown ou limpeza de emergência.
        """
        if not self.connections:
            return 0
        
        logger.warning("🚨 Forçando limpeza de TODAS as conexões")
        
        connection_ids = list(self.connections.keys())
        cleanup_tasks = []
        
        for connection_id in connection_ids:
            cleanup_tasks.append(
                self.disconnect(connection_id, "Force cleanup all")
            )
        
        # Aguarda todas as desconexões
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Limpa estruturas de dados
        self.connections.clear()
        self.user_connections.clear()
        self.room_connections.clear()
        
        logger.info(f"✅ Limpeza forçada concluída: {len(connection_ids)} conexões removidas")
        return len(connection_ids)

    async def _join_room(self, connection_id: str, room_id: str):
        """Adiciona conexão a uma sala"""
        if connection_id not in self.connections:
            return False

        # Create room if doesn't exist
        if room_id not in self.rooms:
            self.rooms[room_id] = RoomInfo(
                room_id=room_id,
                connections=set(),
                created_at=datetime.now(UTC),
                last_activity=datetime.now(UTC),
            )

        # Add to room
        self.rooms[room_id].connections.add(connection_id)
        self.room_connections[room_id].add(connection_id)
        self.rooms[room_id].last_activity = datetime.now(UTC)

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
        """
        CORREÇÃO: Envia mensagem para uma conexão específica com validação de schema
        
        Valida os dados do evento usando schemas Pydantic antes do envio.
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]

        try:
            # CORREÇÃO: Valida dados do evento usando schema Pydantic
            try:
                validated_data = validate_event_data(event_type.value, data)
                logger.debug(f"✅ Dados do evento '{event_type.value}' validados com sucesso")
            except Exception as validation_error:
                logger.error(f"❌ Erro de validação para evento '{event_type.value}': {validation_error}")
                # Envia evento de erro em vez de falhar silenciosamente
                error_data = {
                    "error_code": "VALIDATION_ERROR",
                    "error_message": f"Erro de validação: {str(validation_error)}",
                    "original_event_type": event_type.value,
                    "original_data": data,
                }
                validated_data = error_data
                event_type = RealtimeEventType.ERROR

            message = WebSocketMessage(
                type=event_type.value,
                data=validated_data,
                timestamp=datetime.now(UTC).isoformat(),
                id=uuid.uuid4().hex,
                source_user="system",
                target_user=connection.user_id,
                priority=priority,
            )

            # Add to queue for history
            self.message_queue.append(message)

            # CORREÇÃO: Adicionar ao histórico para recuperação
            self._add_message_to_history({
                "id": message.id,
                "type": message.type,
                "data": message.data,
                "timestamp": message.timestamp,
                "priority": priority,
                "target_user": message.target_user,
                "source_user": message.source_user
            })

            # CORREÇÃO: Enviar mensagem de forma segura com verificação de estado
            success = await self._safe_send_message(connection, safe_json_serialize(asdict(message)))
            
            if not success:
                # Se falhou, marcar como desconectado e remover
                logger.debug(f"🔌 Conexão {connection_id} falhou no envio, marcando como desconectada")
                connection.status = ConnectionStatus.DISCONNECTED
                self.stats["messages_failed"] += 1
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem para {connection_id}: {e}")
            self.stats["messages_failed"] += 1

            # Disconnect on error
            await self.disconnect(connection_id, "Send error")
            return False

    async def send_with_ack(
        self,
        connection_id: str,
        event_type: RealtimeEventType,
        data: Dict[str, Any],
        timeout: float = None,
        priority: int = 1,
    ) -> bool:
        """
        CORREÇÃO: Envia mensagem com confirmação de entrega (ACK)
        
        Args:
            connection_id: ID da conexão
            event_type: Tipo do evento
            data: Dados do evento
            timeout: Timeout para confirmação (padrão: self.ack_timeout)
            priority: Prioridade da mensagem
            
        Returns:
            True se mensagem foi confirmada, False se timeout ou erro
        """
        if connection_id not in self.connections:
            logger.warning(f"❌ Conexão {connection_id} não encontrada para envio com ACK")
            return False

        if timeout is None:
            timeout = self.ack_timeout

        # Gerar ID único para a mensagem
        msg_id = uuid.uuid4().hex
        
        # Criar mensagem com flag de ACK
        message = {
            "id": msg_id,
            "type": event_type.value,
            "data": data,
            "requires_ack": True,
            "timestamp": datetime.now(UTC).isoformat(),
            "priority": priority,
        }

        # Registrar mensagem pendente
        pending_msg = PendingMessage(
            message=message,
            sent_at=datetime.now(UTC),
            retry_count=0,
            max_retries=3
        )
        
        self.pending_acks[connection_id][msg_id] = pending_msg
        self.ack_stats.total_sent += 1
        self.ack_stats.pending_count = sum(len(acks) for acks in self.pending_acks.values())

        try:
            # Enviar mensagem
            connection = self.connections[connection_id]
            
            # CORREÇÃO: Verificar estado da conexão antes de enviar
            if not self._is_connection_healthy(connection):
                logger.debug(f"🔌 Conexão {connection_id} não está saudável para ACK")
                # Remover da lista de pendentes
                if connection_id in self.pending_acks and msg_id in self.pending_acks[connection_id]:
                    del self.pending_acks[connection_id][msg_id]
                    self.ack_stats.pending_count = sum(len(acks) for acks in self.pending_acks.values())
                return False
            
            # Enviar mensagem de forma segura
            success = await self._safe_send_message(connection, safe_json_serialize(message))
            if not success:
                # Remover da lista de pendentes
                if connection_id in self.pending_acks and msg_id in self.pending_acks[connection_id]:
                    del self.pending_acks[connection_id][msg_id]
                    self.ack_stats.pending_count = sum(len(acks) for acks in self.pending_acks.values())
                return False
            
            logger.debug(f"📤 Mensagem com ACK enviada: {msg_id} para {connection_id}")

            # Aguardar confirmação
            try:
                await asyncio.wait_for(
                    self._wait_for_ack(connection_id, msg_id),
                    timeout=timeout
                )
                
                # ACK recebido com sucesso
                self.ack_stats.total_acked += 1
                ack_time = (datetime.now(UTC) - pending_msg.sent_at).total_seconds()
                self.ack_stats.avg_ack_time = (
                    (self.ack_stats.avg_ack_time * (self.ack_stats.total_acked - 1) + ack_time) 
                    / self.ack_stats.total_acked
                )
                
                logger.debug(f"✅ ACK confirmado para mensagem {msg_id} em {ack_time:.2f}s")
                return True
                
            except asyncio.TimeoutError:
                # Timeout - tentar retry
                logger.warning(f"⏰ Timeout de ACK para mensagem {msg_id} após {timeout}s")
                return await self._retry_message(connection_id, msg_id)
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem com ACK {msg_id}: {e}")
            # Remover da lista de pendentes
            if connection_id in self.pending_acks and msg_id in self.pending_acks[connection_id]:
                del self.pending_acks[connection_id][msg_id]
                self.ack_stats.pending_count = sum(len(acks) for acks in self.pending_acks.values())
            return False

    async def _wait_for_ack(self, connection_id: str, msg_id: str):
        """CORREÇÃO: Aguarda confirmação ACK de uma mensagem específica"""
        while connection_id in self.pending_acks and msg_id in self.pending_acks[connection_id]:
            await asyncio.sleep(0.1)  # Aguarda 100ms antes de verificar novamente

    async def _retry_message(self, connection_id: str, msg_id: str) -> bool:
        """CORREÇÃO: Tenta reenviar mensagem que não foi confirmada"""
        if connection_id not in self.pending_acks or msg_id not in self.pending_acks[connection_id]:
            return False

        pending_msg = self.pending_acks[connection_id][msg_id]
        
        if pending_msg.retry_count >= pending_msg.max_retries:
            # Esgotou tentativas
            logger.error(f"❌ Esgotadas tentativas de ACK para mensagem {msg_id}")
            del self.pending_acks[connection_id][msg_id]
            self.ack_stats.total_timeout += 1
            self.ack_stats.pending_count = sum(len(acks) for acks in self.pending_acks.values())
            return False

        # Incrementar contador de tentativas
        pending_msg.retry_count += 1
        self.ack_stats.total_retry += 1
        
        logger.info(f"🔄 Tentativa {pending_msg.retry_count}/{pending_msg.max_retries} para mensagem {msg_id}")
        
        # Aguardar intervalo entre tentativas
        await asyncio.sleep(self.ack_retry_interval)
        
        try:
            # Reenviar mensagem
            connection = self.connections[connection_id]
            await connection.websocket.send_text(safe_json_serialize(pending_msg.message))
            
            # Aguardar ACK novamente
            await asyncio.wait_for(
                self._wait_for_ack(connection_id, msg_id),
                timeout=self.ack_timeout
            )
            
            # ACK recebido
            self.ack_stats.total_acked += 1
            ack_time = (datetime.now(UTC) - pending_msg.sent_at).total_seconds()
            self.ack_stats.avg_ack_time = (
                (self.ack_stats.avg_ack_time * (self.ack_stats.total_acked - 1) + ack_time) 
                / self.ack_stats.total_acked
            )
            
            logger.info(f"✅ ACK confirmado na tentativa {pending_msg.retry_count} para mensagem {msg_id}")
            return True
            
        except asyncio.TimeoutError:
            # Ainda timeout - tentar novamente
            return await self._retry_message(connection_id, msg_id)
        except Exception as e:
            logger.error(f"❌ Erro ao reenviar mensagem {msg_id}: {e}")
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
        CORREÇÃO: Faz broadcast de mensagem para uma sala com validação de schema

        Returns:
            Número de conexões que receberam a mensagem
        """
        if room_id not in self.room_connections:
            return 0

        # CORREÇÃO: Valida dados uma vez antes de enviar para todas as conexões
        try:
            validated_data = validate_event_data(event_type.value, data)
            logger.debug(f"✅ Dados do evento '{event_type.value}' validados para broadcast na sala '{room_id}'")
        except Exception as validation_error:
            logger.error(f"❌ Erro de validação para evento '{event_type.value}' na sala '{room_id}': {validation_error}")
            # Converte para evento de erro
            error_data = {
                "error_code": "VALIDATION_ERROR",
                "error_message": f"Erro de validação: {str(validation_error)}",
                "original_event_type": event_type.value,
                "original_data": data,
            }
            validated_data = error_data
            event_type = RealtimeEventType.ERROR

        exclude_connections = exclude_connections or set()
        connections_to_send = self.room_connections[room_id] - exclude_connections

        if not connections_to_send:
            return 0

        # Update room activity
        if room_id in self.rooms:
            self.rooms[room_id].last_activity = datetime.now(UTC)
            self.rooms[room_id].message_count += 1

        # CORREÇÃO: Filtrar conexões mortas antes de enviar
        healthy_connections = []
        for connection_id in connections_to_send:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if self._is_connection_healthy(connection):
                    healthy_connections.append(connection_id)
                else:
                    logger.debug(f"🔌 Pulando conexão morta {connection_id} no broadcast para sala {room_id}")

        # Send to healthy connections in parallel
        tasks = []
        for connection_id in healthy_connections:
            tasks.append(
                self._send_to_connection(connection_id, event_type, validated_data, priority)
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

        # CORREÇÃO: Filtrar conexões mortas antes de enviar
        healthy_connections = []
        for connection_id in self.connections:
            if connection_id not in exclude_connections:
                connection = self.connections[connection_id]
                if self._is_connection_healthy(connection):
                    healthy_connections.append(connection_id)
                else:
                    logger.debug(f"🔌 Pulando conexão morta {connection_id} no broadcast global")

        tasks = []
        for connection_id in healthy_connections:
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
        connection.last_activity = datetime.now(UTC)

        # CORREÇÃO: Verificar rate limiting antes de processar mensagem
        if self.rate_limiting_enabled and not self.rate_limiter.is_allowed(connection_id):
            logger.warning(f"🚫 Rate limit excedido para conexão {connection_id}")
            await self._send_to_connection(
                connection_id,
                RealtimeEventType.ERROR,
                {
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "error_message": "Rate limit excedido. Tente novamente em alguns segundos.",
                    "retry_after": 60,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )
            return

        message_type = data.get("type")

        try:
            if message_type == "heartbeat":
                # CORREÇÃO: Usa método update_heartbeat
                connection.update_heartbeat()
                await self._send_to_connection(
                    connection_id,
                    RealtimeEventType.HEARTBEAT_RESPONSE,
                    {"timestamp": datetime.now(UTC).isoformat()},
                )

            elif message_type == "ack":
                # CORREÇÃO: Processa confirmação de entrega (ACK)
                msg_id = data.get("message_id")
                if msg_id and connection_id in self.pending_acks and msg_id in self.pending_acks[connection_id]:
                    # Remove mensagem da lista de pendentes
                    del self.pending_acks[connection_id][msg_id]
                    self.ack_stats.pending_count = sum(len(acks) for acks in self.pending_acks.values())
                    logger.debug(f"✅ ACK recebido para mensagem {msg_id} de {connection_id}")
                else:
                    logger.warning(f"⚠️ ACK recebido para mensagem inexistente {msg_id} de {connection_id}")

            elif message_type == "reconnect":
                # CORREÇÃO: Processa reconexão com recuperação de mensagens
                last_message_id = data.get("last_message_id")
                if last_message_id:
                    # Atualizar last_message_id do usuário
                    await self.set_last_message_id(connection.user_id, last_message_id)
                    
                    # Recuperar mensagens perdidas
                    recovered_count = await self._recover_missed_messages(
                        connection_id, connection.user_id, last_message_id
                    )
                    
                    # Enviar confirmação de reconexão
                    await self._send_to_connection(
                        connection_id,
                        RealtimeEventType.CONNECTION_STATUS,
                        {
                            "status": "reconnected",
                            "recovered_messages": recovered_count,
                            "last_message_id": last_message_id,
                            "timestamp": datetime.now(UTC).isoformat()
                        }
                    )
                    
                    logger.info(f"🔄 Reconexão processada para {connection.user_id}: {recovered_count} mensagens recuperadas")
                else:
                    logger.warning(f"⚠️ Reconexão sem last_message_id de {connection_id}")

            elif message_type == "message_received":
                # CORREÇÃO: Cliente confirma recebimento de mensagem
                message_id = data.get("message_id")
                if message_id:
                    await self.set_last_message_id(connection.user_id, message_id)
                    logger.debug(f"📝 Mensagem {message_id} confirmada por {connection.user_id}")

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
        """
        CORREÇÃO: Loop de heartbeat com timeout otimizado
        
        Timeout reduzido de 60s para 30s para detecção mais rápida
        de conexões mortas e liberação de recursos.
        """
        while self._running:
            try:
                now = datetime.now(UTC)
                stale_connections = []

                for connection_id, connection in self.connections.items():
                    # CORREÇÃO: Timeout diferenciado por tipo de conexão
                    timeout = (
                        self.heartbeat_timeout_mobile 
                        if connection.is_mobile_connection() 
                        else self.heartbeat_timeout_desktop
                    )
                    
                    if connection.is_stale(timeout_seconds=timeout):
                        stale_connections.append(connection_id)
                        heartbeat_age = connection.get_heartbeat_age_seconds()
                        connection_type = "mobile" if connection.is_mobile_connection() else "desktop"
                        logger.debug(
                            f"🔍 Conexão obsoleta detectada: {connection_id} "
                            f"({connection_type}, sem heartbeat há {heartbeat_age:.1f}s, timeout: {timeout}s)"
                        )

                # Disconnect stale connections
                for connection_id in stale_connections:
                    connection = self.connections.get(connection_id)
                    timeout = (
                        self.heartbeat_timeout_mobile 
                        if connection and connection.is_mobile_connection() 
                        else self.heartbeat_timeout_desktop
                    )
                    await self.disconnect(connection_id, f"Heartbeat timeout ({timeout}s)")

                if stale_connections:
                    # Conta conexões por tipo
                    mobile_count = sum(
                        1 for conn_id in stale_connections 
                        if self.connections.get(conn_id) and self.connections[conn_id].is_mobile_connection()
                    )
                    desktop_count = len(stale_connections) - mobile_count
                    
                    logger.info(
                        f"🔄 Limpeza de heartbeat: {len(stale_connections)} conexões removidas "
                        f"(desktop: {desktop_count}, mobile: {mobile_count})"
                    )

                # Send heartbeat to all active connections
                for connection_id in list(self.connections.keys()):
                    await self._send_to_connection(
                        connection_id,
                        RealtimeEventType.HEARTBEAT,
                        {"timestamp": now.isoformat()},
                    )

                await asyncio.sleep(self.heartbeat_interval)  # CORREÇÃO: Usa configuração

            except Exception as e:
                logger.error(f"❌ Erro no loop de heartbeat: {e}")
                await asyncio.sleep(10)

    async def _cleanup_loop(self):
        """Loop de limpeza para manter sistema saudável"""
        while self._running:
            try:
                now = datetime.now(UTC)

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

                # CORREÇÃO: Limpeza de conexões mortas
                dead_connections_removed = await self.cleanup_dead_connections()
                if dead_connections_removed > 0:
                    logger.info(f"🧹 Limpeza de conexões mortas: {dead_connections_removed} conexões removidas")

                # CORREÇÃO: Limpeza do rate limiter
                if self.rate_limiting_enabled:
                    active_connections = set(self.connections.keys())
                    self.rate_limiter.cleanup_old_connections(active_connections)

                # Update cleanup time
                self.stats["last_cleanup"] = now

                await asyncio.sleep(300)  # Cleanup every 5 minutes

            except Exception as e:
                logger.error(f"❌ Erro no loop de limpeza: {e}")
                await asyncio.sleep(60)

    async def _ack_cleanup_loop(self):
        """CORREÇÃO: Loop de limpeza para ACKs expirados"""
        while self._running:
            try:
                now = datetime.now(UTC)
                expired_messages = []
                
                # Verificar ACKs expirados
                for connection_id, acks in self.pending_acks.items():
                    for msg_id, pending_msg in acks.items():
                        # Considerar expirado se passou mais que 2x o timeout
                        if (now - pending_msg.sent_at).total_seconds() > (self.ack_timeout * 2):
                            expired_messages.append((connection_id, msg_id))
                
                # Remover mensagens expiradas
                for connection_id, msg_id in expired_messages:
                    if connection_id in self.pending_acks and msg_id in self.pending_acks[connection_id]:
                        del self.pending_acks[connection_id][msg_id]
                        self.ack_stats.total_timeout += 1
                        logger.warning(f"⏰ ACK expirado removido: {msg_id} de {connection_id}")
                
                # Atualizar contador de pendentes
                self.ack_stats.pending_count = sum(len(acks) for acks in self.pending_acks.values())
                
                if expired_messages:
                    logger.info(f"🧹 Limpeza de ACKs: {len(expired_messages)} mensagens expiradas removidas")
                
                # Limpar conexões vazias
                empty_connections = [
                    conn_id for conn_id, acks in self.pending_acks.items() 
                    if not acks
                ]
                for conn_id in empty_connections:
                    del self.pending_acks[conn_id]
                
                await asyncio.sleep(30)  # Verificar a cada 30 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro no loop de limpeza de ACKs: {e}")
                await asyncio.sleep(60)

    def get_stats(self) -> Dict[str, Any]:
        """CORREÇÃO: Retorna estatísticas do sistema com informações de limpeza"""
        now = datetime.now(UTC)
        uptime = now - self.stats["uptime_started"]
        
        # Obtém estatísticas detalhadas de conexões
        connection_stats = self.get_connection_stats()

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
            
            # CORREÇÃO: Adiciona estatísticas de limpeza e vazamentos
            "connection_cleanup": {
                "stale_connections": connection_stats["stale_connections"],
                "potential_leaks": connection_stats["potential_leaks"],
                "cleanup_recommended": connection_stats["cleanup_recommended"],
                "memory_usage_estimate": connection_stats["memory_usage_estimate"],
                "user_stats": connection_stats["user_stats"],
            },
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
            
            # CORREÇÃO: Estatísticas de confirmação de entrega (ACK)
            "ack_stats": {
                "total_sent": self.ack_stats.total_sent,
                "total_acked": self.ack_stats.total_acked,
                "total_timeout": self.ack_stats.total_timeout,
                "total_retry": self.ack_stats.total_retry,
                "pending_count": self.ack_stats.pending_count,
                "avg_ack_time": round(self.ack_stats.avg_ack_time, 3),
                "success_rate": round(
                    (self.ack_stats.total_acked / max(self.ack_stats.total_sent, 1)) * 100, 2
                ) if self.ack_stats.total_sent > 0 else 0,
                "timeout_rate": round(
                    (self.ack_stats.total_timeout / max(self.ack_stats.total_sent, 1)) * 100, 2
                ) if self.ack_stats.total_sent > 0 else 0,
            },
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

    def get_ack_stats(self) -> Dict[str, Any]:
        """CORREÇÃO: Retorna estatísticas detalhadas do sistema ACK"""
        return {
            "total_sent": self.ack_stats.total_sent,
            "total_acked": self.ack_stats.total_acked,
            "total_timeout": self.ack_stats.total_timeout,
            "total_retry": self.ack_stats.total_retry,
            "pending_count": self.ack_stats.pending_count,
            "avg_ack_time": round(self.ack_stats.avg_ack_time, 3),
            "success_rate": round(
                (self.ack_stats.total_acked / max(self.ack_stats.total_sent, 1)) * 100, 2
            ) if self.ack_stats.total_sent > 0 else 0,
            "timeout_rate": round(
                (self.ack_stats.total_timeout / max(self.ack_stats.total_sent, 1)) * 100, 2
            ) if self.ack_stats.total_sent > 0 else 0,
            "retry_rate": round(
                (self.ack_stats.total_retry / max(self.ack_stats.total_sent, 1)) * 100, 2
            ) if self.ack_stats.total_sent > 0 else 0,
            "pending_messages": {
                conn_id: {
                    "count": len(acks),
                    "messages": [
                        {
                            "msg_id": msg_id,
                            "sent_at": pending_msg.sent_at.isoformat(),
                            "retry_count": pending_msg.retry_count,
                            "age_seconds": (datetime.now(UTC) - pending_msg.sent_at).total_seconds(),
                        }
                        for msg_id, pending_msg in acks.items()
                    ]
                }
                for conn_id, acks in self.pending_acks.items()
                if acks
            }
        }

    def reset_ack_stats(self):
        """CORREÇÃO: Reseta estatísticas do sistema ACK"""
        self.ack_stats = AckStats()
        logger.info("🔄 Estatísticas de ACK resetadas")

    async def force_ack_cleanup(self) -> int:
        """CORREÇÃO: Força limpeza de todos os ACKs pendentes"""
        total_cleaned = 0
        
        for connection_id, acks in list(self.pending_acks.items()):
            total_cleaned += len(acks)
            del self.pending_acks[connection_id]
        
        self.ack_stats.pending_count = 0
        logger.info(f"🧹 Limpeza forçada de ACKs: {total_cleaned} mensagens pendentes removidas")
        return total_cleaned

    async def mark_message_as_delivered(
        self,
        message_id: str,
        conversation_id: str = None,
        user_id: str = None,
        delivered_at: datetime = None
    ) -> bool:
        """
        CORREÇÃO: Marca mensagem como entregue e notifica via WebSocket
        
        Args:
            message_id: ID da mensagem
            conversation_id: ID da conversa (opcional)
            user_id: ID do usuário (opcional)
            delivered_at: Timestamp de entrega (padrão: agora)
            
        Returns:
            True se notificação foi enviada com sucesso
        """
        try:
            if delivered_at is None:
                delivered_at = datetime.now(UTC)
            
            # Dados do evento
            event_data = {
                "message_id": message_id,
                "status": "delivered",
                "delivered_at": delivered_at.isoformat(),
                "conversation_id": conversation_id,
                "user_id": user_id,
            }
            
            # Enviar notificação
            if conversation_id:
                # Broadcast para a conversa específica
                sent_count = await self.broadcast_to_room(
                    room_id=conversation_id,
                    event_type=RealtimeEventType.MESSAGE_DELIVERED,
                    data=event_data
                )
            elif user_id:
                # Enviar para usuário específico
                sent_count = await self.send_to_user(
                    user_id=user_id,
                    event_type=RealtimeEventType.MESSAGE_DELIVERED,
                    data=event_data
                )
            else:
                # Broadcast geral
                sent_count = await self.broadcast_to_all(
                    event_type=RealtimeEventType.MESSAGE_DELIVERED,
                    data=event_data
                )
            
            logger.info(f"📬 Mensagem {message_id} marcada como entregue - {sent_count} notificações enviadas")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao marcar mensagem {message_id} como entregue: {e}")
            return False

    async def mark_message_as_read(
        self,
        message_id: str,
        conversation_id: str = None,
        user_id: str = None,
        read_at: datetime = None
    ) -> bool:
        """
        CORREÇÃO: Marca mensagem como lida e notifica via WebSocket
        
        Args:
            message_id: ID da mensagem
            conversation_id: ID da conversa (opcional)
            user_id: ID do usuário (opcional)
            read_at: Timestamp de leitura (padrão: agora)
            
        Returns:
            True se notificação foi enviada com sucesso
        """
        try:
            if read_at is None:
                read_at = datetime.now(UTC)
            
            # Dados do evento
            event_data = {
                "message_id": message_id,
                "status": "read",
                "read_at": read_at.isoformat(),
                "conversation_id": conversation_id,
                "user_id": user_id,
            }
            
            # Enviar notificação
            if conversation_id:
                # Broadcast para a conversa específica
                sent_count = await self.broadcast_to_room(
                    room_id=conversation_id,
                    event_type=RealtimeEventType.MESSAGE_READ,
                    data=event_data
                )
            elif user_id:
                # Enviar para usuário específico
                sent_count = await self.send_to_user(
                    user_id=user_id,
                    event_type=RealtimeEventType.MESSAGE_READ,
                    data=event_data
                )
            else:
                # Broadcast geral
                sent_count = await self.broadcast_to_all(
                    event_type=RealtimeEventType.MESSAGE_READ,
                    data=event_data
                )
            
            logger.info(f"👁️ Mensagem {message_id} marcada como lida - {sent_count} notificações enviadas")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao marcar mensagem {message_id} como lida: {e}")
            return False

    async def mark_multiple_messages_as_delivered(
        self,
        message_ids: List[str],
        conversation_id: str = None,
        user_id: str = None,
        delivered_at: datetime = None
    ) -> int:
        """
        CORREÇÃO: Marca múltiplas mensagens como entregues
        
        Args:
            message_ids: Lista de IDs das mensagens
            conversation_id: ID da conversa (opcional)
            user_id: ID do usuário (opcional)
            delivered_at: Timestamp de entrega (padrão: agora)
            
        Returns:
            Número de mensagens marcadas com sucesso
        """
        success_count = 0
        
        for message_id in message_ids:
            if await self.mark_message_as_delivered(
                message_id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                delivered_at=delivered_at
            ):
                success_count += 1
        
        logger.info(f"📬 {success_count}/{len(message_ids)} mensagens marcadas como entregues")
        return success_count

    async def mark_multiple_messages_as_read(
        self,
        message_ids: List[str],
        conversation_id: str = None,
        user_id: str = None,
        read_at: datetime = None
    ) -> int:
        """
        CORREÇÃO: Marca múltiplas mensagens como lidas
        
        Args:
            message_ids: Lista de IDs das mensagens
            conversation_id: ID da conversa (opcional)
            user_id: ID do usuário (opcional)
            read_at: Timestamp de leitura (padrão: agora)
            
        Returns:
            Número de mensagens marcadas com sucesso
        """
        success_count = 0
        
        for message_id in message_ids:
            if await self.mark_message_as_read(
                message_id=message_id,
                conversation_id=conversation_id,
                user_id=user_id,
                read_at=read_at
            ):
                success_count += 1
        
        logger.info(f"👁️ {success_count}/{len(message_ids)} mensagens marcadas como lidas")
        return success_count

    async def _recover_missed_messages(
        self,
        connection_id: str,
        user_id: str,
        last_message_id: str
    ) -> int:
        """
        CORREÇÃO: Recupera mensagens perdidas durante desconexão
        
        Args:
            connection_id: ID da conexão
            user_id: ID do usuário
            last_message_id: ID da última mensagem recebida
            
        Returns:
            Número de mensagens recuperadas
        """
        try:
            if not self.message_history:
                logger.debug(f"📭 Nenhum histórico de mensagens para recuperar para {user_id}")
                return 0
            
            # Buscar mensagens perdidas desde last_message_id
            missed_messages = []
            last_message_found = False
            
            for msg in self.message_history:
                if msg.get("id") == last_message_id:
                    last_message_found = True
                    continue
                
                if last_message_found:
                    # Verificar se a mensagem é relevante para o usuário
                    if self._is_message_relevant_for_user(msg, user_id):
                        missed_messages.append(msg)
            
            if not last_message_found:
                logger.warning(f"⚠️ Last message ID {last_message_id} não encontrado no histórico para {user_id}")
                # Se não encontrou a mensagem, enviar as últimas N mensagens
                missed_messages = self.message_history[-50:]  # Últimas 50 mensagens
            
            # Enviar mensagens perdidas sequencialmente
            recovered_count = 0
            for msg in missed_messages:
                try:
                    # Reenviar mensagem para a conexão
                    await self._send_to_connection(
                        connection_id=connection_id,
                        event_type=RealtimeEventType(msg["type"]),
                        data=msg["data"],
                        priority=msg.get("priority", 1)
                    )
                    recovered_count += 1
                    
                    # Pequena pausa para evitar sobrecarga
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao reenviar mensagem {msg.get('id', 'unknown')}: {e}")
                    continue
            
            if recovered_count > 0:
                logger.info(f"🔄 Recuperadas {recovered_count} mensagens perdidas para {user_id} ({connection_id})")
            
            return recovered_count
            
        except Exception as e:
            logger.error(f"❌ Erro na recuperação de mensagens para {user_id}: {e}")
            return 0

    def _is_message_relevant_for_user(self, message: Dict[str, Any], user_id: str) -> bool:
        """
        CORREÇÃO: Verifica se uma mensagem é relevante para um usuário
        
        Args:
            message: Dados da mensagem
            user_id: ID do usuário
            
        Returns:
            True se a mensagem é relevante
        """
        try:
            # Mensagens de sistema são sempre relevantes
            if message.get("type") in ["system_notification", "heartbeat", "connection_status"]:
                return True
            
            # Verificar se é para o usuário específico
            target_user = message.get("data", {}).get("target_user")
            if target_user == user_id:
                return True
            
            # Verificar se é para uma sala que o usuário está
            room = message.get("data", {}).get("room")
            if room and user_id in self.user_connections:
                # Verificar se o usuário está na sala
                for conn_id in self.user_connections[user_id]:
                    if conn_id in self.connections:
                        connection = self.connections[conn_id]
                        if connection.room == room:
                            return True
            
            # Verificar se é um broadcast geral
            if message.get("data", {}).get("broadcast") == True:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar relevância da mensagem: {e}")
            return False

    def _add_message_to_history(self, message: Dict[str, Any]):
        """
        CORREÇÃO: Adiciona mensagem ao histórico para recuperação
        
        Args:
            message: Dados da mensagem
        """
        try:
            # Adicionar timestamp se não existir
            if "timestamp" not in message:
                message["timestamp"] = datetime.now(UTC).isoformat()
            
            # Adicionar ao histórico
            self.message_history.append(message)
            
            # Manter histórico limitado
            if len(self.message_history) > self.max_history_size:
                # Remover mensagens mais antigas
                self.message_history = self.message_history[-self.max_history_size:]
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar mensagem ao histórico: {e}")

    async def get_last_message_id(self, user_id: str) -> str:
        """
        CORREÇÃO: Retorna o ID da última mensagem para um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            ID da última mensagem ou None
        """
        try:
            return self.last_message_ids.get(user_id)
        except Exception as e:
            logger.error(f"❌ Erro ao obter last_message_id para {user_id}: {e}")
            return None

    async def set_last_message_id(self, user_id: str, message_id: str):
        """
        CORREÇÃO: Define o ID da última mensagem para um usuário
        
        Args:
            user_id: ID do usuário
            message_id: ID da mensagem
        """
        try:
            self.last_message_ids[user_id] = message_id
            logger.debug(f"📝 Last message ID atualizado para {user_id}: {message_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao definir last_message_id para {user_id}: {e}")

    def _is_connection_healthy(self, connection: ConnectionInfo) -> bool:
        """
        CORREÇÃO: Verifica se uma conexão WebSocket está saudável
        
        Args:
            connection: Informações da conexão
            
        Returns:
            True se a conexão está saudável
        """
        try:
            # Verificar se o WebSocket existe
            if not connection.websocket:
                return False
            
            # Verificar estado do WebSocket
            if hasattr(connection.websocket, 'client_state'):
                if connection.websocket.client_state != WebSocketState.CONNECTED:
                    logger.debug(f"🔌 Conexão {connection.connection_id} não está conectada (estado: {connection.websocket.client_state})")
                    return False
            
            # Verificar se a conexão não está marcada como morta
            if connection.status != ConnectionStatus.CONNECTED:
                logger.debug(f"🔌 Conexão {connection.connection_id} não está ativa (status: {connection.status})")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar saúde da conexão {connection.connection_id}: {e}")
            return False

    async def _safe_send_message(self, connection: ConnectionInfo, message: str) -> bool:
        """
        CORREÇÃO: Envia mensagem de forma segura com verificação de estado
        
        Args:
            connection: Informações da conexão
            message: Mensagem JSON para enviar
            
        Returns:
            True se mensagem foi enviada com sucesso
        """
        try:
            # Verificar se conexão está saudável
            if not self._is_connection_healthy(connection):
                logger.debug(f"🔌 Conexão {connection.connection_id} não está saudável, pulando envio")
                return False
            
            # Tentar enviar mensagem
            await connection.websocket.send_text(message)
            
            # Atualizar atividade
            connection.last_activity = datetime.now(UTC)
            self.stats["messages_sent"] += 1
            
            return True
            
        except WebSocketDisconnect:
            logger.debug(f"🔌 WebSocket desconectado: {connection.connection_id}")
            connection.status = ConnectionStatus.DISCONNECTED
            return False
            
        except RuntimeError as e:
            logger.warning(f"⚠️ Erro de runtime ao enviar para {connection.connection_id}: {e}")
            connection.status = ConnectionStatus.DISCONNECTED
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar para {connection.connection_id}: {e}")
            connection.status = ConnectionStatus.DISCONNECTED
            return False

    async def cleanup_dead_connections(self) -> int:
        """
        CORREÇÃO: Limpa conexões mortas/inativas
        
        Returns:
            Número de conexões removidas
        """
        try:
            dead_connections = []
            
            for connection_id, connection in self.connections.items():
                if not self._is_connection_healthy(connection):
                    dead_connections.append(connection_id)
            
            # Remover conexões mortas
            removed_count = 0
            for connection_id in dead_connections:
                try:
                    await self.disconnect(connection_id, "Dead connection cleanup")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"❌ Erro ao remover conexão morta {connection_id}: {e}")
            
            if removed_count > 0:
                logger.info(f"🧹 Limpeza de conexões mortas: {removed_count} conexões removidas")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"❌ Erro na limpeza de conexões mortas: {e}")
            return 0

    async def get_connection_health_stats(self) -> Dict[str, Any]:
        """
        CORREÇÃO: Retorna estatísticas de saúde das conexões
        
        Returns:
            Estatísticas de saúde das conexões
        """
        try:
            total_connections = len(self.connections)
            healthy_connections = 0
            dead_connections = 0
            connection_states = {}
            
            for connection_id, connection in self.connections.items():
                is_healthy = self._is_connection_healthy(connection)
                
                if is_healthy:
                    healthy_connections += 1
                else:
                    dead_connections += 1
                
                # Contar estados
                state = connection.status.value if hasattr(connection.status, 'value') else str(connection.status)
                connection_states[state] = connection_states.get(state, 0) + 1
            
            return {
                "total_connections": total_connections,
                "healthy_connections": healthy_connections,
                "dead_connections": dead_connections,
                "health_percentage": round((healthy_connections / max(total_connections, 1)) * 100, 2),
                "connection_states": connection_states,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas de saúde: {e}")
            return {}

    async def get_rate_limiter_stats(self) -> Dict[str, Any]:
        """
        CORREÇÃO: Retorna estatísticas do rate limiter
        
        Returns:
            Estatísticas do rate limiter
        """
        try:
            return self.rate_limiter.get_stats()
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas do rate limiter: {e}")
            return {}

    async def configure_rate_limiting(
        self,
        max_messages: int = None,
        window_seconds: int = None,
        enabled: bool = None
    ) -> bool:
        """
        CORREÇÃO: Configura o rate limiting
        
        Args:
            max_messages: Número máximo de mensagens por janela
            window_seconds: Duração da janela em segundos
            enabled: Habilitar/desabilitar rate limiting
            
        Returns:
            True se configuração foi aplicada
        """
        try:
            if max_messages is not None:
                self.rate_limiter.max_messages = max_messages
                logger.info(f"📊 Rate limiter: max_messages configurado para {max_messages}")
            
            if window_seconds is not None:
                self.rate_limiter.window = timedelta(seconds=window_seconds)
                logger.info(f"📊 Rate limiter: window_seconds configurado para {window_seconds}")
            
            if enabled is not None:
                self.rate_limiting_enabled = enabled
                logger.info(f"📊 Rate limiter: {'habilitado' if enabled else 'desabilitado'}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar rate limiting: {e}")
            return False

    async def unblock_connection(self, connection_id: str) -> bool:
        """
        CORREÇÃO: Desbloqueia uma conexão específica
        
        Args:
            connection_id: ID da conexão
            
        Returns:
            True se conexão foi desbloqueada
        """
        try:
            self.rate_limiter.unblock_connection(connection_id)
            logger.info(f"🔓 Conexão {connection_id} desbloqueada manualmente")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao desbloquear conexão {connection_id}: {e}")
            return False

    async def reset_rate_limiter_stats(self) -> bool:
        """
        CORREÇÃO: Reseta estatísticas do rate limiter
        
        Returns:
            True se estatísticas foram resetadas
        """
        try:
            self.rate_limiter.reset_stats()
            logger.info("🔄 Estatísticas do rate limiter resetadas")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao resetar estatísticas do rate limiter: {e}")
            return False

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

    def validate_event_data(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CORREÇÃO: Valida dados de evento usando schema Pydantic
        
        Args:
            event_type: Tipo do evento
            data: Dados do evento
            
        Returns:
            Dados validados e serializados
            
        Raises:
            ValueError: Se os dados são inválidos
        """
        return validate_event_data(event_type, data)
    
    def get_event_schema(self, event_type: str) -> Optional[BaseModel]:
        """
        CORREÇÃO: Retorna o schema para um tipo de evento
        
        Args:
            event_type: Tipo do evento
            
        Returns:
            Classe do schema ou None se não existir
        """
        return get_event_schema(event_type)
    
    def list_available_schemas(self) -> Dict[str, str]:
        """
        CORREÇÃO: Lista todos os schemas disponíveis
        
        Returns:
            Dicionário com tipos de eventos e suas classes de schema
        """
        return {
            event_type: schema_class.__name__ 
            for event_type, schema_class in EVENT_SCHEMA_MAP.items()
        }


# Singleton instance
realtime_manager = RealtimeWebSocketManager()


def get_realtime_manager() -> RealtimeWebSocketManager:
    """Retorna a instância singleton do gerenciador"""
    return realtime_manager
