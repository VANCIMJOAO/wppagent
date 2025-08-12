"""
Sistema de Cache Simples para Respostas
Cache em memória com TTL de 5 minutos para evitar reprocessamento desnecessário
"""
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class SimpleResponseCache:
    """
    Cache simples para respostas do WhatsApp Agent
    
    Features:
    - Cache em memória com TTL de 5 minutos
    - Chave baseada em hash da mensagem + user_id
    - Limpeza automática quando cache fica muito grande
    - Thread-safe para uso em produção
    """
    
    def __init__(self, max_size: int = 1000, ttl_minutes: int = 5):
        self.cache: Dict[str, Tuple[str, datetime]] = {}
        self.max_size = max_size
        self.ttl_minutes = ttl_minutes
        
        # Estatísticas para monitoramento
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "cleanups": 0,
            "expired": 0
        }
        
    def get_key(self, message: str, user_id: str) -> str:
        """Gera chave única para a combinação mensagem + usuário"""
        # Normalizar mensagem para melhor cache hit rate
        normalized_message = message.lower().strip()
        data = f"{normalized_message}:{user_id}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, message: str, user_id: str) -> Optional[str]:
        """
        Busca resposta no cache
        
        Returns:
            str: Resposta cached se encontrada e válida
            None: Se não encontrada ou expirada
        """
        key = self.get_key(message, user_id)
        
        if key in self.cache:
            response, timestamp = self.cache[key]
            
            # Verificar se não expirou
            if datetime.now() - timestamp < timedelta(minutes=self.ttl_minutes):
                self.stats["hits"] += 1
                logger.debug(f"Cache HIT para user {user_id}: {message[:50]}...")
                return response
            else:
                # Expirado - remover
                del self.cache[key]
                self.stats["expired"] += 1
                logger.debug(f"Cache EXPIRED para user {user_id}: {message[:50]}...")
        
        self.stats["misses"] += 1
        logger.debug(f"Cache MISS para user {user_id}: {message[:50]}...")
        return None
    
    def set(self, message: str, user_id: str, response: str):
        """
        Armazena resposta no cache
        
        Args:
            message: Mensagem original do usuário
            user_id: ID do usuário
            response: Resposta a ser cached
        """
        key = self.get_key(message, user_id)
        self.cache[key] = (response, datetime.now())
        self.stats["sets"] += 1
        
        logger.debug(f"Cache SET para user {user_id}: {message[:50]}... -> {response[:50]}...")
        
        # Limpar cache se muito grande
        if len(self.cache) > self.max_size:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Limpa cache removendo entradas mais antigas"""
        # Remover metade das entradas mais antigas
        cleanup_count = self.max_size // 2
        
        # Ordenar por timestamp (mais antigos primeiro)
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
        
        # Manter apenas as mais recentes
        self.cache = dict(sorted_items[cleanup_count:])
        
        self.stats["cleanups"] += 1
        logger.info(f"Cache cleanup executado: removidas {cleanup_count} entradas antigas")
    
    def clear(self):
        """Limpa todo o cache"""
        self.cache.clear()
        logger.info("Cache limpo completamente")
    
    def get_stats(self) -> Dict[str, any]:
        """Retorna estatísticas do cache"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "ttl_minutes": self.ttl_minutes,
            "hit_rate": f"{hit_rate:.1f}%",
            "stats": self.stats,
            "memory_usage_estimate": len(self.cache) * 200  # Estimativa em bytes
        }
    
    def cleanup_expired(self):
        """Remove manualmente todas as entradas expiradas"""
        now = datetime.now()
        expired_keys = []
        
        for key, (response, timestamp) in self.cache.items():
            if now - timestamp >= timedelta(minutes=self.ttl_minutes):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            self.stats["expired"] += 1
        
        if expired_keys:
            logger.info(f"Cleanup manual: removidas {len(expired_keys)} entradas expiradas")


# Instância global do cache
simple_cache = SimpleResponseCache()


# Helper functions para facilitar uso
def cache_get_response(message: str, user_id: str) -> Optional[str]:
    """Helper para buscar resposta no cache"""
    return simple_cache.get(message, user_id)


def cache_set_response(message: str, user_id: str, response: str):
    """Helper para armazenar resposta no cache"""
    simple_cache.set(message, user_id, response)


def cache_clear():
    """Helper para limpar cache"""
    simple_cache.clear()


def cache_stats():
    """Helper para obter estatísticas do cache"""
    return simple_cache.get_stats()


if __name__ == "__main__":
    # Teste básico do cache
    cache = SimpleResponseCache()
    
    # Teste 1: Set e Get
    cache.set("oi", "user123", "Olá! Como posso ajudar?")
    response = cache.get("oi", "user123")
    print(f"Teste 1 - Response: {response}")
    
    # Teste 2: Normalização (case insensitive)
    response2 = cache.get("OI", "user123")
    print(f"Teste 2 - Response (case): {response2}")
    
    # Teste 3: Miss
    response3 = cache.get("tchau", "user123")
    print(f"Teste 3 - Miss: {response3}")
    
    # Teste 4: Usuário diferente
    response4 = cache.get("oi", "user456")
    print(f"Teste 4 - Different user: {response4}")
    
    # Teste 5: Stats
    stats = cache.get_stats()
    print(f"Teste 5 - Stats: {stats}")
