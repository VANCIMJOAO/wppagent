"""
Configuração inteligente do Redis com detecção automática
"""

import redis
import logging
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
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = self._detect_redis()
    
    def _detect_redis(self) -> RedisConfig:
        """Detecta se Redis está disponível"""
        redis_urls = [
            "redis://localhost:6379/0",
            "redis://redis:6379/0",  # Docker
            "redis://127.0.0.1:6379/0"
        ]
        
        for url in redis_urls:
            try:
                client = redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
                client.ping()
                logger.info(f"✅ Redis conectado com sucesso: {url}")
                return RedisConfig(
                    available=True,
                    client=client,
                    url=url,
                    fallback_mode=False
                )
            except Exception as e:
                logger.debug(f"Redis não disponível em {url}: {e}")
                continue
        
        logger.info("🔶 Redis não detectado automaticamente - Sistema funcionando com cache em memória")
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
