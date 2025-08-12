from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema Avançado de Gestão de Estado para Conversações
Gerenciamento distribuído com Redis e fallback em memória
"""
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConversationStatus(Enum):
    """Estados possíveis da conversa"""
    INACTIVE = "inactive"
    ACTIVE = "active" 
    WAITING_INPUT = "waiting_input"
    PROCESSING = "processing"
    BOOKING_FLOW = "booking_flow"
    HANDOFF_PENDING = "handoff_pending"
    COMPLETED = "completed"
    EXPIRED = "expired"


class MessageRole(Enum):
    """Papéis das mensagens"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ConversationMessage:
    """Estrutura de mensagem na conversa"""
    role: MessageRole
    content: str
    timestamp: datetime
    message_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Cria instância a partir de dicionário"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_id=data.get("message_id"),
            metadata=data.get("metadata", {})
        )


@dataclass
class BookingContext:
    """Contexto específico para agendamentos"""
    service_type: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    confirmed: bool = False
    booking_id: Optional[str] = None
    step: str = "initial"  # initial, service_selection, datetime, confirmation, completed
    attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookingContext':
        return cls(**data)


@dataclass
class ConversationState:
    """Estado completo da conversa"""
    user_id: str
    phone: str
    status: ConversationStatus = ConversationStatus.INACTIVE
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    messages: List[ConversationMessage] = field(default_factory=list)
    
    # Contextos específicos
    booking_context: Optional[BookingContext] = None
    user_context: Dict[str, Any] = field(default_factory=dict)
    
    # Configurações
    timeout_minutes: int = 30
    max_messages: int = 100
    
    # Metadados
    strategy_history: List[str] = field(default_factory=list)
    total_messages: int = 0
    session_id: Optional[str] = None
    
    def add_message(self, message: ConversationMessage):
        """Adiciona mensagem ao histórico"""
        self.messages.append(message)
        self.total_messages += 1
        self.last_activity = datetime.now()
        
        # Limita número de mensagens
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, count: int = 10) -> List[ConversationMessage]:
        """Obtém mensagens recentes"""
        return self.messages[-count:]
    
    def is_expired(self) -> bool:
        """Verifica se a conversa expirou"""
        timeout = timedelta(minutes=self.timeout_minutes)
        return datetime.now() - self.last_activity > timeout
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Gera resumo do contexto"""
        return {
            "status": self.status.value,
            "duration_minutes": (datetime.now() - self.started_at).total_seconds() / 60,
            "total_messages": self.total_messages,
            "last_activity_ago": (datetime.now() - self.last_activity).total_seconds() / 60,
            "has_booking": self.booking_context is not None,
            "booking_step": self.booking_context.step if self.booking_context else None
        }
    
    def to_json(self) -> str:
        """Serializa para JSON"""
        data = {
            "user_id": self.user_id,
            "phone": self.phone,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "messages": [msg.to_dict() for msg in self.messages],
            "booking_context": self.booking_context.to_dict() if self.booking_context else None,
            "user_context": self.user_context,
            "timeout_minutes": self.timeout_minutes,
            "max_messages": self.max_messages,
            "strategy_history": self.strategy_history,
            "total_messages": self.total_messages,
            "session_id": self.session_id
        }
        return json.dumps(data, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_data: str) -> 'ConversationState':
        """Deserializa de JSON"""
        data = json.loads(json_data)
        
        messages = [ConversationMessage.from_dict(msg) for msg in data.get("messages", [])]
        booking_context = None
        if data.get("booking_context"):
            booking_context = BookingContext.from_dict(data["booking_context"])
        
        return cls(
            user_id=data["user_id"],
            phone=data["phone"],
            status=ConversationStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            messages=messages,
            booking_context=booking_context,
            user_context=data.get("user_context", {}),
            timeout_minutes=data.get("timeout_minutes", 30),
            max_messages=data.get("max_messages", 100),
            strategy_history=data.get("strategy_history", []),
            total_messages=data.get("total_messages", 0),
            session_id=data.get("session_id")
        )


class ConversationStateManager:
    """
    Gerenciador avançado de estado de conversação
    
    Features:
    - Armazenamento Redis distribuído
    - Fallback em memória
    - TTL automático
    - Limpeza de estados expirados
    - Backup/restore
    - Métricas de performance
    """
    
    def __init__(self, redis_url: str = None, default_ttl: int = 1800):
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self.default_ttl = default_ttl  # 30 minutos
        self.redis_client = None
        self.memory_cache: Dict[str, ConversationState] = {}
        self.redis_available = False
        
        # Estatísticas
        self.stats = {
            "redis_hits": 0,
            "redis_misses": 0,
            "memory_hits": 0,
            "memory_misses": 0,
            "saves": 0,
            "errors": 0,
            "cleanups": 0
        }
        
        asyncio.create_task(self._init_redis())
    
    async def _init_redis(self):
        """Inicializa conexão Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis não disponível, usando apenas cache em memória")
            return
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Testa conexão
            await self.redis_client.ping()
            self.redis_available = True
            logger.info("Redis conectado com sucesso")
            
            # Inicia limpeza automática
            asyncio.create_task(self._cleanup_expired_states())
            
        except Exception as e:
            logger.error(f"Erro ao conectar Redis: {e}")
            self.redis_available = False
    
    def _get_state_key(self, user_id: str) -> str:
        """Gera chave para estado no Redis"""
        return f"conversation_state:{user_id}"
    
    async def get_state(self, user_id: str) -> ConversationState:
        """
        Obtém estado da conversa
        Prioridade: Redis > Memory Cache > Novo Estado
        """
        try:
            # Tenta Redis primeiro
            if self.redis_available and self.redis_client:
                try:
                    key = self._get_state_key(user_id)
                    data = await self.redis_client.get(key)
                    
                    if data:
                        state = ConversationState.from_json(data)
                        
                        # Verifica se não expirou
                        if not state.is_expired():
                            self.stats["redis_hits"] += 1
                            # Atualiza cache em memória
                            self.memory_cache[user_id] = state
                            return state
                        else:
                            # Remove estado expirado
                            await self.redis_client.delete(key)
                    
                    self.stats["redis_misses"] += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao ler Redis: {e}")
                    self.stats["errors"] += 1
            
            # Tenta cache em memória
            if user_id in self.memory_cache:
                state = self.memory_cache[user_id]
                if not state.is_expired():
                    self.stats["memory_hits"] += 1
                    return state
                else:
                    del self.memory_cache[user_id]
            
            self.stats["memory_misses"] += 1
            
            # Cria novo estado
            return ConversationState(user_id=user_id, phone="")
            
        except Exception as e:
            logger.error(f"Erro ao obter estado: {e}")
            self.stats["errors"] += 1
            return ConversationState(user_id=user_id, phone="")
    
    async def save_state(self, user_id: str, state: ConversationState, ttl: Optional[int] = None):
        """
        Salva estado da conversa
        Salva tanto no Redis quanto em memória
        """
        try:
            ttl = ttl or self.default_ttl
            state.last_activity = datetime.now()
            
            # Salva no Redis
            if self.redis_available and self.redis_client:
                try:
                    key = self._get_state_key(user_id)
                    json_data = state.to_json()
                    
                    await self.redis_client.setex(key, ttl, json_data)
                    logger.debug(f"Estado salvo no Redis: {user_id}")
                    
                except Exception as e:
                    logger.error(f"Erro ao salvar no Redis: {e}")
                    self.stats["errors"] += 1
            
            # Salva em memória como backup
            self.memory_cache[user_id] = state
            self.stats["saves"] += 1
            
            logger.debug(f"Estado salvo para usuário: {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar estado: {e}")
            self.stats["errors"] += 1
    
    async def delete_state(self, user_id: str):
        """Remove estado da conversa"""
        try:
            # Remove do Redis
            if self.redis_available and self.redis_client:
                key = self._get_state_key(user_id)
                await self.redis_client.delete(key)
            
            # Remove da memória
            self.memory_cache.pop(user_id, None)
            
            logger.debug(f"Estado removido: {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao remover estado: {e}")
            self.stats["errors"] += 1
    
    async def update_status(self, user_id: str, status: ConversationStatus):
        """Atualiza apenas o status da conversa"""
        try:
            state = await self.get_state(user_id)
            state.status = status
            state.last_activity = datetime.now()
            await self.save_state(user_id, state)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")
            self.stats["errors"] += 1
    
    async def add_message(self, user_id: str, message: ConversationMessage):
        """Adiciona mensagem ao histórico"""
        try:
            state = await self.get_state(user_id)
            
            # Se é a primeira mensagem, configura phone
            if not state.phone and hasattr(message, 'phone'):
                state.phone = getattr(message, 'phone', '')
            
            state.add_message(message)
            
            # Atualiza status baseado no conteúdo
            if state.status == ConversationStatus.INACTIVE:
                state.status = ConversationStatus.ACTIVE
            
            await self.save_state(user_id, state)
            
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem: {e}")
            self.stats["errors"] += 1
    
    async def get_conversation_history(self, user_id: str, limit: int = 20) -> List[ConversationMessage]:
        """Obtém histórico de mensagens"""
        try:
            state = await self.get_state(user_id)
            return state.get_recent_messages(limit)
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    async def start_booking_flow(self, user_id: str) -> BookingContext:
        """Inicia fluxo de agendamento"""
        try:
            state = await self.get_state(user_id)
            state.status = ConversationStatus.BOOKING_FLOW
            state.booking_context = BookingContext()
            
            await self.save_state(user_id, state)
            return state.booking_context
            
        except Exception as e:
            logger.error(f"Erro ao iniciar booking: {e}")
            return BookingContext()
    
    async def update_booking_context(self, user_id: str, **kwargs):
        """Atualiza contexto de agendamento"""
        try:
            state = await self.get_state(user_id)
            
            if not state.booking_context:
                state.booking_context = BookingContext()
            
            # Atualiza campos
            for key, value in kwargs.items():
                if hasattr(state.booking_context, key):
                    setattr(state.booking_context, key, value)
            
            await self.save_state(user_id, state)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar booking context: {e}")
    
    async def get_active_conversations(self) -> List[str]:
        """Lista conversas ativas"""
        active = []
        
        try:
            # Verifica cache em memória
            for user_id, state in self.memory_cache.items():
                if not state.is_expired() and state.status in [ConversationStatus.ACTIVE, ConversationStatus.BOOKING_FLOW]:
                    active.append(user_id)
            
            # Se Redis disponível, verifica lá também
            if self.redis_available and self.redis_client:
                try:
                    keys = await self.redis_client.keys("conversation_state:*")
                    for key in keys:
                        user_id = key.split(":")[-1]
                        if user_id not in active:  # Evita duplicatas
                            data = await self.redis_client.get(key)
                            if data:
                                state = ConversationState.from_json(data)
                                if not state.is_expired() and state.status in [ConversationStatus.ACTIVE, ConversationStatus.BOOKING_FLOW]:
                                    active.append(user_id)
                except Exception as e:
                    logger.error(f"Erro ao listar conversas ativas no Redis: {e}")
            
            return active
            
        except Exception as e:
            logger.error(f"Erro ao obter conversas ativas: {e}")
            return []
    
    async def _cleanup_expired_states(self):
        """Limpeza automática de estados expirados"""
        while True:
            try:
                await asyncio.sleep(300)  # Executa a cada 5 minutos
                
                cleaned = 0
                
                # Limpa cache em memória
                expired_keys = []
                for user_id, state in self.memory_cache.items():
                    if state.is_expired():
                        expired_keys.append(user_id)
                
                for key in expired_keys:
                    del self.memory_cache[key]
                    cleaned += 1
                
                # Redis TTL automático já remove, mas vamos verificar
                if self.redis_available and self.redis_client:
                    try:
                        keys = await self.redis_client.keys("conversation_state:*")
                        for key in keys:
                            ttl = await self.redis_client.ttl(key)
                            if ttl == -1:  # Sem TTL
                                data = await self.redis_client.get(key)
                                if data:
                                    state = ConversationState.from_json(data)
                                    if state.is_expired():
                                        await self.redis_client.delete(key)
                                        cleaned += 1
                    except Exception as e:
                        logger.error(f"Erro na limpeza Redis: {e}")
                
                if cleaned > 0:
                    self.stats["cleanups"] += cleaned
                    logger.info(f"Limpeza automática: {cleaned} estados removidos")
                
            except Exception as e:
                logger.error(f"Erro na limpeza automática: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do manager"""
        return {
            "redis_available": self.redis_available,
            "memory_cache_size": len(self.memory_cache),
            "stats": self.stats,
            "uptime": time.time()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do sistema"""
        health = {
            "status": "healthy",
            "redis_available": self.redis_available,
            "memory_cache_size": len(self.memory_cache),
            "total_operations": sum(self.stats.values())
        }
        
        # Testa Redis se disponível
        if self.redis_available and self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis_ping"] = "ok"
            except Exception as e:
                health["redis_ping"] = f"error: {e}"
                health["status"] = "degraded"
        
        return health


# Instância global
def get_state_manager():
    """Factory function para obter instância do state_manager com configurações corretas"""
    from app.config.config_factory import get_settings
    settings = get_settings()
    return ConversationStateManager(redis_url=settings.redis_url)

state_manager = None  # Será inicializado quando necessário


# === HELPER FUNCTIONS ===

async def get_user_state(user_id: str) -> ConversationState:
    """Função helper para obter estado do usuário"""
    return await state_manager.get_state(user_id)


async def save_user_state(user_id: str, state: ConversationState):
    """Função helper para salvar estado do usuário"""
    await state_manager.save_state(user_id, state)


async def add_user_message(user_id: str, content: str, role: MessageRole = MessageRole.USER, **metadata):
    """Função helper para adicionar mensagem"""
    message = ConversationMessage(
        role=role,
        content=content,
        timestamp=datetime.now(),
        metadata=metadata
    )
    await state_manager.add_message(user_id, message)


async def start_booking_for_user(user_id: str) -> BookingContext:
    """Função helper para iniciar booking"""
    return await state_manager.start_booking_flow(user_id)


if __name__ == "__main__":
    # Teste básico
    async def test_state_manager():
        # Cria estado
        state = ConversationState(user_id="test_user", phone="+5511999999999")
        
        # Adiciona mensagem
        message = ConversationMessage(
            role=MessageRole.USER,
            content="Olá, quero agendar um horário",
            timestamp=datetime.now()
        )
        state.add_message(message)
        
        # Salva estado
        await state_manager.save_state("test_user", state)
        
        # Recupera estado
        recovered_state = await state_manager.get_state("test_user")
        
        logger.info(f"Estado recuperado: {recovered_state.user_id}")
        logger.info(f"Mensagens: {len(recovered_state.messages)}")
        logger.info(f"Status: {recovered_state.status.value}")
    
    # Executa teste
    asyncio.run(test_state_manager())
