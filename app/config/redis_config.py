"""
Configuração inteligente do Redis com detecção automática
"""

import redis
import logging
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RedisConfig:
    """Configuração do Redis"""
    available: bool = False
    client: Optional[redis.Redis] = None
    url: Optional[str] = None
    fallback_mode: bool = True

class RedisManager:
    """Gerenciador inteligente do Redis"""
    
    _instance: Optional['RedisManager'] = None
    _config: Optional[RedisConfig] = None
    
    def __new__(cls):
        if cls._instance is None:
            logger.info("🆕 Criando nova instância do RedisManager (Singleton)")
            cls._instance = super().__new__(cls)
        else:
            logger.info("♻️  Reutilizando instância existente do RedisManager")
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            logger.info("🔧 Inicializando RedisManager...")
            self._config = self._detect_redis()
            logger.info(f"🔧 RedisManager inicializado - Available: {self._config.available}, Fallback: {self._config.fallback_mode}")
    
    def _detect_redis(self) -> RedisConfig:
        """Detecta se Redis está disponível - Railway priority"""
        # 1. Primeiro tentar Railway Redis se disponível
        railway_redis = os.getenv("REDIS_URL")
        if railway_redis:
            try:
                logger.info(f"🚀 Tentando conectar ao Redis do Railway: {railway_redis[:50]}...")
                # Aumentar timeout para Railway (pode ser mais lento que local)
                client = redis.from_url(
                    railway_redis, 
                    socket_timeout=15,  # 15s timeout
                    socket_connect_timeout=15,  # 15s para conectar
                    retry_on_timeout=True,
                    retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                    health_check_interval=30
                )
                logger.info("🔄 Enviando ping para Railway Redis...")
                result = client.ping()
                logger.info(f"✅ Redis Railway conectado com sucesso! Ping: {result}")
                logger.info(f"🔧 Final RedisConfig: available={True}, fallback_mode={False}, url={railway_redis[:50]}...")
                return RedisConfig(
                    available=True,
                    client=client,
                    url=railway_redis,
                    fallback_mode=False
                )
            except redis.ConnectionError as e:
                logger.error(f"❌ Erro de conexão Redis Railway: {e}")
            except redis.TimeoutError as e:
                logger.error(f"❌ Timeout Redis Railway: {e}")
            except Exception as e:
                logger.error(f"❌ Falha geral Redis Railway: {type(e).__name__}: {e}")
        
        # 2. Tentar URLs locais como fallback
        redis_urls = [
            "redis://localhost:6379/0",
            "redis://redis:6379/0",  # Docker
            "redis://127.0.0.1:6379/0"
        ]
        
        for url in redis_urls:
            try:
                client = redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
                client.ping()
                logger.info(f"✅ Redis local conectado: {url}")
                return RedisConfig(
                    available=True,
                    client=client,
                    url=url,
                    fallback_mode=False
                )
            except Exception as e:
                logger.debug(f"Redis não disponível em {url}: {e}")
                continue
        
        logger.warning("⚠️ Redis não disponível - usando cache em memória")
        logger.info(f"🔧 Final RedisConfig: available={False}, fallback_mode={True}")
        return RedisConfig(
            available=False,
            client=None,
            url=None,
            fallback_mode=True
        )
    
    @property
    def is_available(self) -> bool:
        """Verifica se Redis está disponível"""
        return self._config.available
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Retorna cliente Redis se disponível"""
        return self._config.client
    
    @property
    def fallback_mode(self) -> bool:
        """Verifica se está em modo fallback"""
        return self._config.fallback_mode
    
    def get_safe_client(self) -> Optional[redis.Redis]:
        """Retorna cliente Redis com verificação de saúde"""
        if not self.is_available:
            return None
        
        try:
            self.client.ping()
            return self.client
        except Exception as e:
            logger.warning(f"Redis perdeu conexão: {e}")
            # Tentar reconectar
            self._config = self._detect_redis()
            return self.client if self.is_available else None
    
    def execute_safe(self, operation: callable, *args, **kwargs) -> Any:
        """Executa operação Redis com fallback seguro"""
        if not self.is_available:
            return None
        
        try:
            client = self.get_safe_client()
            if client:
                return operation(client, *args, **kwargs)
        except Exception as e:
            logger.debug(f"Operação Redis falhou: {e}")
        
        return None

# Instância global
redis_manager = RedisManager()

def get_redis_client() -> Optional[redis.Redis]:
    """Retorna cliente Redis se disponível"""
    return redis_manager.get_safe_client()

def is_redis_available() -> bool:
    """Verifica se Redis está disponível"""
    return redis_manager.is_available

def execute_redis_safe(operation: callable, *args, **kwargs) -> Any:
    """Executa operação Redis com fallback seguro"""
    return redis_manager.execute_safe(operation, *args, **kwargs)

async def execute_redis_safe_async(operation: callable, *args, **kwargs) -> Any:
    """Executa operação Redis assíncrona com fallback seguro"""
    return redis_manager.execute_safe(operation, *args, **kwargs)
