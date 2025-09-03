"""
Sistema de Cache Simples para Dashboard
=====================================

Sistema de cache em memória com TTL (Time To Live) para otimizar
chamadas repetitivas à API e melhorar performance da dashboard.

Características:
- Cache em memória com TTL configurável
- Decorator para automatizar cache de funções
- Limpeza automática de itens expirados
- Chaves de cache baseadas em função + parâmetros
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict, Callable
from functools import wraps


class SimpleCache:
    """
    Sistema de cache simples com TTL (Time To Live)
    
    Armazena dados em memória com expiração automática baseada
    no tempo de vida (TTL) especificado para cada item.
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """
        Busca item do cache com verificação de TTL
        
        Args:
            key: Chave do item no cache
            ttl: Time To Live em segundos (padrão: 5 minutos)
            
        Returns:
            Valor armazenado ou None se não existir/expirado
        """
        if key in self._cache:
            # Verifica se o item não expirou
            if time.time() - self._timestamps[key] < ttl:
                return self._cache[key]
            else:
                # Cache expirado - remove item
                self._remove_expired_item(key)
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Armazena item no cache com timestamp atual
        
        Args:
            key: Chave para armazenar o item
            value: Valor a ser armazenado
        """
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def _remove_expired_item(self, key: str) -> None:
        """Remove item expirado do cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        self._cache.clear()
        self._timestamps.clear()
    
    def cleanup_expired(self, ttl: int = 300) -> int:
        """
        Remove todos os itens expirados do cache
        
        Args:
            ttl: Time To Live em segundos para considerar expirado
            
        Returns:
            Número de itens removidos
        """
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time - timestamp >= ttl
        ]
        
        for key in expired_keys:
            self._remove_expired_item(key)
        
        return len(expired_keys)
    
    def size(self) -> int:
        """Retorna o número de itens no cache"""
        return len(self._cache)
    
    def keys(self) -> list:
        """Retorna todas as chaves do cache"""
        return list(self._cache.keys())


# Instância global do cache
cache = SimpleCache()


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Gera chave única para cache baseada na função e parâmetros
    
    Args:
        func_name: Nome da função
        args: Argumentos posicionais
        kwargs: Argumentos nomeados
        
    Returns:
        Chave única para o cache
    """
    # Converte argumentos para string JSON para garantir consistência
    args_str = json.dumps(args, sort_keys=True, default=str)
    kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
    
    # Combina função + argumentos
    combined = f"{func_name}_{args_str}_{kwargs_str}"
    
    # Gera hash MD5 para chave mais curta
    return hashlib.md5(combined.encode()).hexdigest()


def cached_api_call(ttl: int = 300):
    """
    Decorator para cache automático de chamadas API
    
    Args:
        ttl: Time To Live em segundos (padrão: 5 minutos)
        
    Usage:
        @cached_api_call(ttl=600)  # Cache por 10 minutos
        def get_dashboard_stats():
            return APIService.get_dashboard_stats()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave única para esta chamada
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Tenta buscar do cache
            result = cache.get(cache_key, ttl)
            
            if result is None:
                # Cache miss - executa função e armazena resultado
                try:
                    result = func(*args, **kwargs)
                    cache.set(cache_key, result)
                except Exception as e:
                    # Em caso de erro, não armazena no cache
                    raise e
            
            return result
        
        # Adiciona métodos úteis ao wrapper
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_size = lambda: cache.size()
        
        return wrapper
    return decorator


def cached_database_call(ttl: int = 180):
    """
    Decorator específico para chamadas de banco de dados
    
    Args:
        ttl: Time To Live em segundos (padrão: 3 minutos)
        
    Usage:
        @cached_database_call(ttl=300)
        def get_conversations():
            return db.execute_query("SELECT * FROM conversations")
    """
    return cached_api_call(ttl)


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalida itens do cache que correspondem a um padrão
    
    Args:
        pattern: Padrão para buscar nas chaves (substring)
        
    Returns:
        Número de itens removidos
    """
    keys_to_remove = [
        key for key in cache.keys()
        if pattern in key
    ]
    
    for key in keys_to_remove:
        cache._remove_expired_item(key)
    
    return len(keys_to_remove)


# Funções utilitárias para gerenciamento do cache
def get_cache_info() -> dict:
    """
    Retorna informações sobre o estado atual do cache
    
    Returns:
        Dicionário com estatísticas do cache
    """
    current_time = time.time()
    expired_count = 0
    
    for timestamp in cache._timestamps.values():
        if current_time - timestamp >= 300:  # TTL padrão
            expired_count += 1
    
    return {
        'total_items': cache.size(),
        'expired_items': expired_count,
        'active_items': cache.size() - expired_count,
        'keys': cache.keys()
    }


def clear_all_cache() -> None:
    """Limpa todo o cache"""
    cache.clear()


# Auto-limpeza periódica do cache (executar em background se necessário)
def periodic_cleanup(ttl: int = 300) -> None:
    """
    Função para limpeza periódica do cache
    Pode ser chamada por um scheduler ou timer
    
    Args:
        ttl: Time To Live para considerar expirado
    """
    removed_count = cache.cleanup_expired(ttl)
    if removed_count > 0:
        print(f"🧹 Cache cleanup: {removed_count} itens expirados removidos")
