"""
🔧 SISTEMA UNIFICADO DE CONTROLE DE RESPOSTA
============================================

Substitui os múltiplos controles sobrepostos por um sistema único e eficiente
baseado em Redis com fallback inteligente.

CARACTERÍSTICAS:
- ✅ Controle único via Redis com TTL automático
- ✅ Fallback para cache em memória se Redis não disponível
- ✅ Hash determinístico para detectar mensagens duplicadas
- ✅ Janela temporal configurável (padrão: 30 segundos)
- ✅ Métricas detalhadas e logging
- ✅ Performance otimizada

RESOLVE:
- ❌ Sobreposição de controles redundantes
- ❌ Cache persistente em arquivos temporários
- ❌ Verificações desnecessárias no banco
- ❌ Rate limiting middleware duplicado
"""

import hashlib
import time
import json
import asyncio
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import redis.asyncio as redis

from app.config.redis_config import redis_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ResponseControlStats:
    """Estatísticas do controle de resposta"""
    messages_processed: int = 0
    messages_blocked: int = 0
    messages_allowed: int = 0
    duplicates_prevented: int = 0
    redis_operations: int = 0
    fallback_operations: int = 0
    errors: int = 0
    last_reset: float = field(default_factory=time.time)
    
    def reset_if_needed(self):
        """Reset estatísticas a cada hora"""
        if time.time() - self.last_reset > 3600:  # 1 hora
            self.__post_init__()
            self.last_reset = time.time()
            logger.info("📊 Estatísticas resetadas")

class UnifiedResponseControl:
    """Sistema unificado de controle de resposta única"""
    
    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, float] = {}
        self.stats = ResponseControlStats()
        self._lock = asyncio.Lock()
        self._initialize_redis()
        
    def _initialize_redis(self):
        """Inicializa conexão Redis de forma assíncrona"""
        try:
            redis_config = redis_manager._config
            if redis_config and redis_config.available:
                # Criar cliente Redis assíncrono
                self.redis_client = redis.from_url(
                    redis_config.url or "redis://localhost:6379/0",
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2
                )
                logger.info("🔧 Redis cliente assíncrono inicializado")
            else:
                logger.warning("⚠️ Redis não disponível - usando cache em memória")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Redis: {e}")
            self.redis_client = None
    
    def generate_message_hash(self, content: str) -> str:
        """
        Gera hash determinístico do conteúdo da mensagem
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            Hash MD5 truncado (12 caracteres) do conteúdo normalizado
        """
        # Normalizar conteúdo
        content_clean = content.strip().lower()
        # Limitar tamanho para evitar hash de mensagens muito grandes
        content_clean = content_clean[:200]
        # Gerar hash
        return hashlib.md5(content_clean.encode('utf-8')).hexdigest()[:12]
    
    def _get_cache_key(self, user_id: str, message_hash: str) -> str:
        """Gera chave única para cache"""
        return f"msg_processed:{user_id}:{message_hash}"
    
    async def can_process_message(self, user_id: str, content: str) -> Tuple[bool, str]:
        """
        Verifica se a mensagem pode ser processada (sistema unificado)
        
        Args:
            user_id: ID único do usuário (telefone)
            content: Conteúdo da mensagem
            
        Returns:
            Tuple[bool, str]: (pode_processar, motivo)
        """
        async with self._lock:
            self.stats.messages_processed += 1
            self.stats.reset_if_needed()
            
            try:
                # Gerar hash da mensagem
                message_hash = self.generate_message_hash(content)
                cache_key = self._get_cache_key(user_id, message_hash)
                
                logger.debug(f"🔍 Verificando: {user_id} - hash:{message_hash}")
                
                # Tentar usar Redis primeiro
                if await self._can_process_redis(cache_key):
                    return await self._allow_message(user_id, cache_key, "Redis - primeira vez")
                
                # Fallback para cache em memória
                if await self._can_process_memory(cache_key):
                    return await self._allow_message(user_id, cache_key, "Memory - primeira vez")
                
                # Mensagem já processada
                return await self._block_message(user_id, "Mensagem duplicada detectada")
                
            except Exception as e:
                self.stats.errors += 1
                logger.error(f"❌ Erro no controle de resposta: {e}")
                # Em caso de erro, permitir processamento para evitar bloqueio completo
                return True, f"Erro no controle - permitindo: {str(e)}"
    
    async def _can_process_redis(self, cache_key: str) -> bool:
        """Verifica via Redis se pode processar mensagem"""
        if not self.redis_client:
            return False
            
        try:
            self.stats.redis_operations += 1
            
            # Usar SET com NX (só define se não existir) e EX (TTL)
            result = await self.redis_client.set(
                cache_key,
                "1",
                ex=self.window_seconds,  # TTL automático
                nx=True  # Só define se a chave não existir
            )
            
            # Se result é True, a chave foi criada (mensagem pode ser processada)
            # Se result é None, a chave já existia (mensagem duplicada)
            return result is not None
            
        except Exception as e:
            logger.warning(f"⚠️ Erro Redis: {e} - usando fallback")
            return False
    
    async def _can_process_memory(self, cache_key: str) -> bool:
        """Verifica via cache em memória se pode processar mensagem"""
        try:
            self.stats.fallback_operations += 1
            current_time = time.time()
            
            # Limpar entradas expiradas
            expired_keys = [
                key for key, timestamp in self.memory_cache.items()
                if current_time - timestamp > self.window_seconds
            ]
            
            for key in expired_keys:
                del self.memory_cache[key]
            
            # Verificar se chave já existe
            if cache_key in self.memory_cache:
                return False  # Já processada
            
            # Marcar como processada
            self.memory_cache[cache_key] = current_time
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro cache memória: {e}")
            return True  # Em caso de erro, permitir processamento
    
    async def _allow_message(self, user_id: str, cache_key: str, reason: str) -> Tuple[bool, str]:
        """Permite processamento da mensagem"""
        self.stats.messages_allowed += 1
        logger.info(f"✅ PERMITIDO: {user_id} - {reason}")
        return True, reason
    
    async def _block_message(self, user_id: str, reason: str) -> Tuple[bool, str]:
        """Bloqueia processamento da mensagem"""
        self.stats.messages_blocked += 1
        self.stats.duplicates_prevented += 1
        logger.warning(f"🚫 BLOQUEADO: {user_id} - {reason}")
        return False, reason
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas"""
        self.stats.reset_if_needed()
        
        # Calcular percentuais
        total = self.stats.messages_processed
        blocked_pct = (self.stats.messages_blocked / total * 100) if total > 0 else 0
        allowed_pct = (self.stats.messages_allowed / total * 100) if total > 0 else 0
        
        return {
            "messages_processed": self.stats.messages_processed,
            "messages_blocked": self.stats.messages_blocked,
            "messages_allowed": self.stats.messages_allowed,
            "duplicates_prevented": self.stats.duplicates_prevented,
            "redis_operations": self.stats.redis_operations,
            "fallback_operations": self.stats.fallback_operations,
            "errors": self.stats.errors,
            "blocked_percentage": round(blocked_pct, 2),
            "allowed_percentage": round(allowed_pct, 2),
            "redis_available": self.redis_client is not None,
            "window_seconds": self.window_seconds,
            "memory_cache_size": len(self.memory_cache),
            "last_reset": datetime.fromtimestamp(self.stats.last_reset).isoformat()
        }
    
    async def clear_cache(self) -> Dict[str, Any]:
        """Limpa todos os caches (para testes/debug)"""
        try:
            cleared_redis = 0
            cleared_memory = len(self.memory_cache)
            
            # Limpar Redis
            if self.redis_client:
                # Buscar chaves do padrão
                keys = await self.redis_client.keys("msg_processed:*")
                if keys:
                    cleared_redis = await self.redis_client.delete(*keys)
            
            # Limpar cache em memória
            self.memory_cache.clear()
            
            logger.info(f"🧹 Cache limpo: {cleared_redis} Redis + {cleared_memory} memória")
            
            return {
                "cleared_redis_keys": cleared_redis,
                "cleared_memory_keys": cleared_memory,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache: {e}")
            return {
                "error": str(e),
                "status": "error"
            }

# Instância global unificada
unified_response_control = UnifiedResponseControl()
