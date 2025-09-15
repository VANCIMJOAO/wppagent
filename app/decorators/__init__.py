"""
🔄 Decorators para Cache Invalidation
===================================

Módulo de decorators para automatização de cache invalidation.
"""

from .cache_invalidation import (cache_on_success,
                                 invalidate_appointment_cache_on_success,
                                 invalidate_cache,
                                 invalidate_client_cache_on_success,
                                 invalidate_conversation_cache_on_success,
                                 invalidate_multiple_caches,
                                 log_cache_invalidation_activity)

__all__ = [
    "invalidate_cache",
    "invalidate_multiple_caches",
    "cache_on_success",
    "invalidate_appointment_cache_on_success",
    "invalidate_conversation_cache_on_success",
    "invalidate_client_cache_on_success",
    "log_cache_invalidation_activity",
]
