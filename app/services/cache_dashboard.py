"""
PD003 - Dashboard Cache Service

Cache inteligente para dashboards e listas com TTLs específicos e chaves organizacionais.
"""

from app.services.cache_service import cache_service, CacheType
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import hashlib
import asyncio
import logging

logger = logging.getLogger(__name__)


class DashboardCacheService:
    """PD003 - Cache específico para dashboards e listas"""
    
    # Configuração de TTL por tipo de dado (em segundos)
    CACHE_TTL = {
        'dashboard_stats': 300,        # 5 min - estatísticas mudam frequentemente
        'conversation_list': 180,      # 3 min - lista de conversas atualiza rápido  
        'appointment_list': 600,       # 10 min - appointments menos frequentes
        'user_stats': 900,             # 15 min - estatísticas de usuário estáveis
        'business_metrics': 1800,      # 30 min - métricas de negócio estáveis
        'analytics_overview': 3600,    # 1 hora - analytics consolidados
        'quick_stats': 60,             # 1 min - stats rápidos para real-time
        'monthly_report': 7200,        # 2 horas - relatórios mensais
    }
    
    # Prefixos organizacionais para chaves de cache
    CACHE_KEYS = {
        'dashboard_stats': 'pd003:dashboard:stats:{}',           # business_id
        'conversation_list': 'pd003:lists:conversations:{}:{}',  # filters_hash:page
        'appointment_list': 'pd003:lists:appointments:{}:{}',    # filters_hash:page
        'user_profile': 'pd003:user:profile:{}',                 # user_id
        'business_metrics': 'pd003:business:metrics:{}:{}',      # business_id:period
        'analytics_data': 'pd003:analytics:overview:{}',         # business_id
        'quick_stats': 'pd003:quick:stats:{}',                   # business_id
        'user_conversations': 'pd003:user:conversations:{}',      # user_id
        'monthly_summary': 'pd003:monthly:summary:{}:{}',        # business_id:month
    }
    
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.logger = logger
    
    async def get_dashboard_stats(self, business_id: int) -> Optional[Dict[str, Any]]:
        """Cache para estatísticas do dashboard principal"""
        cache_key = self.CACHE_KEYS['dashboard_stats'].format(business_id)
        
        try:
            cached = await cache_service.get_cached_response(
                message=f"dashboard_stats_{business_id}",
                user_id=str(business_id),
                context={"type": "dashboard_stats", "business_id": business_id}
            )
            
            if cached:
                self.cache_hits += 1
                self.logger.info(f"🎯 Cache HIT - Dashboard stats para business {business_id}")
                return json.loads(cached)
            else:
                self.cache_misses += 1
                self.logger.info(f"❌ Cache MISS - Dashboard stats para business {business_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar dashboard stats do cache: {e}")
            return None
    
    async def set_dashboard_stats(self, business_id: int, stats_data: Dict[str, Any]):
        """Cachear estatísticas do dashboard"""
        try:
            # Adicionar timestamp para debugging
            stats_data['cached_at'] = datetime.now().isoformat()
            stats_data['ttl_seconds'] = self.CACHE_TTL['dashboard_stats']
            
            await cache_service.cache_response(
                message=f"dashboard_stats_{business_id}",
                user_id=str(business_id),
                response=json.dumps(stats_data),
                context={"type": "dashboard_stats", "business_id": business_id},
                custom_ttl=self.CACHE_TTL['dashboard_stats']
            )
            
            self.logger.info(f"💾 Cache SET - Dashboard stats para business {business_id} (TTL: {self.CACHE_TTL['dashboard_stats']}s)")
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear dashboard stats: {e}")
    
    async def get_conversation_list(self, filters: Dict[str, Any], page: int = 1, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Cache para lista de conversas com filtros"""
        filters_hash = self._hash_filters(filters)
        cache_message = f"conversations_list_{filters_hash}_{page}_{limit}"
        
        try:
            cached = await cache_service.get_cached_response(
                message=cache_message,
                user_id="system",
                context={
                    "type": "conversation_list", 
                    "filters": filters, 
                    "page": page,
                    "limit": limit
                }
            )
            
            if cached:
                self.cache_hits += 1
                self.logger.info(f"🎯 Cache HIT - Conversation list (filters: {filters_hash}, page: {page})")
                return json.loads(cached)
            else:
                self.cache_misses += 1
                self.logger.info(f"❌ Cache MISS - Conversation list (filters: {filters_hash}, page: {page})")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar conversation list do cache: {e}")
            return None
    
    async def set_conversation_list(self, filters: Dict[str, Any], page: int, limit: int, data: Dict[str, Any]):
        """Cachear lista de conversas"""
        filters_hash = self._hash_filters(filters)
        cache_message = f"conversations_list_{filters_hash}_{page}_{limit}"
        
        try:
            # Adicionar metadados de cache
            data['cache_metadata'] = {
                'cached_at': datetime.now().isoformat(),
                'ttl_seconds': self.CACHE_TTL['conversation_list'],
                'filters_hash': filters_hash,
                'page': page,
                'limit': limit
            }
            
            await cache_service.cache_response(
                message=cache_message,
                user_id="system", 
                response=json.dumps(data),
                context={
                    "type": "conversation_list", 
                    "filters": filters,
                    "page": page,
                    "limit": limit
                },
                custom_ttl=self.CACHE_TTL['conversation_list']
            )
            
            self.logger.info(f"💾 Cache SET - Conversation list (filters: {filters_hash}, page: {page}, TTL: {self.CACHE_TTL['conversation_list']}s)")
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear conversation list: {e}")
    
    async def get_appointment_list(self, filters: Dict[str, Any], page: int = 1, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Cache para lista de appointments"""
        filters_hash = self._hash_filters(filters)
        cache_message = f"appointments_list_{filters_hash}_{page}_{limit}"
        
        try:
            cached = await cache_service.get_cached_response(
                message=cache_message,
                user_id="system",
                context={
                    "type": "appointment_list", 
                    "filters": filters,
                    "page": page,
                    "limit": limit
                }
            )
            
            if cached:
                self.cache_hits += 1
                self.logger.info(f"🎯 Cache HIT - Appointment list (filters: {filters_hash}, page: {page})")
                return json.loads(cached)
            else:
                self.cache_misses += 1
                self.logger.info(f"❌ Cache MISS - Appointment list (filters: {filters_hash}, page: {page})")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar appointment list do cache: {e}")
            return None
    
    async def set_appointment_list(self, filters: Dict[str, Any], page: int, limit: int, data: Dict[str, Any]):
        """Cachear lista de appointments"""
        filters_hash = self._hash_filters(filters)
        cache_message = f"appointments_list_{filters_hash}_{page}_{limit}"
        
        try:
            # Adicionar metadados de cache
            data['cache_metadata'] = {
                'cached_at': datetime.now().isoformat(),
                'ttl_seconds': self.CACHE_TTL['appointment_list'],
                'filters_hash': filters_hash,
                'page': page,
                'limit': limit
            }
            
            await cache_service.cache_response(
                message=cache_message,
                user_id="system",
                response=json.dumps(data), 
                context={
                    "type": "appointment_list", 
                    "filters": filters,
                    "page": page,
                    "limit": limit
                },
                custom_ttl=self.CACHE_TTL['appointment_list']
            )
            
            self.logger.info(f"💾 Cache SET - Appointment list (filters: {filters_hash}, page: {page}, TTL: {self.CACHE_TTL['appointment_list']}s)")
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear appointment list: {e}")
    
    async def get_quick_stats(self, business_id: int) -> Optional[Dict[str, Any]]:
        """Cache para estatísticas rápidas (1 minuto TTL)"""
        cache_message = f"quick_stats_{business_id}"
        
        try:
            cached = await cache_service.get_cached_response(
                message=cache_message,
                user_id=str(business_id),
                context={"type": "quick_stats", "business_id": business_id}
            )
            
            if cached:
                self.cache_hits += 1
                self.logger.info(f"🎯 Cache HIT - Quick stats para business {business_id}")
                return json.loads(cached)
            else:
                self.cache_misses += 1
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar quick stats do cache: {e}")
            return None
    
    async def set_quick_stats(self, business_id: int, stats_data: Dict[str, Any]):
        """Cachear estatísticas rápidas"""
        try:
            stats_data['cached_at'] = datetime.now().isoformat()
            stats_data['ttl_seconds'] = self.CACHE_TTL['quick_stats']
            
            await cache_service.cache_response(
                message=f"quick_stats_{business_id}",
                user_id=str(business_id),
                response=json.dumps(stats_data),
                context={"type": "quick_stats", "business_id": business_id},
                custom_ttl=self.CACHE_TTL['quick_stats']
            )
            
            self.logger.info(f"💾 Cache SET - Quick stats para business {business_id} (TTL: {self.CACHE_TTL['quick_stats']}s)")
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear quick stats: {e}")
    
    async def get_user_conversations(self, user_id: int, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Cache para conversas recentes de um usuário"""
        cache_message = f"user_conversations_{user_id}_{limit}"
        
        try:
            cached = await cache_service.get_cached_response(
                message=cache_message,
                user_id=str(user_id),
                context={"type": "user_conversations", "user_id": user_id, "limit": limit}
            )
            
            if cached:
                self.cache_hits += 1
                self.logger.info(f"🎯 Cache HIT - User conversations para user {user_id}")
                return json.loads(cached)
            else:
                self.cache_misses += 1
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar user conversations do cache: {e}")
            return None
    
    async def set_user_conversations(self, user_id: int, limit: int, conversations_data: List[Dict[str, Any]]):
        """Cachear conversas de usuário"""
        try:
            cache_data = {
                'conversations': conversations_data,
                'cached_at': datetime.now().isoformat(),
                'ttl_seconds': self.CACHE_TTL['conversation_list'],
                'user_id': user_id,
                'limit': limit
            }
            
            await cache_service.cache_response(
                message=f"user_conversations_{user_id}_{limit}",
                user_id=str(user_id),
                response=json.dumps(cache_data),
                context={"type": "user_conversations", "user_id": user_id, "limit": limit},
                custom_ttl=self.CACHE_TTL['conversation_list']
            )
            
            self.logger.info(f"💾 Cache SET - User conversations para user {user_id} (TTL: {self.CACHE_TTL['conversation_list']}s)")
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear user conversations: {e}")
    
    async def get_business_analytics(self, business_id: int, period: str = 'month') -> Optional[Dict[str, Any]]:
        """Cache para analytics de negócio (TTL longo)"""
        cache_message = f"business_analytics_{business_id}_{period}"
        
        try:
            cached = await cache_service.get_cached_response(
                message=cache_message,
                user_id=str(business_id),
                context={"type": "analytics_overview", "business_id": business_id, "period": period}
            )
            
            if cached:
                self.cache_hits += 1
                self.logger.info(f"🎯 Cache HIT - Business analytics para business {business_id} (period: {period})")
                return json.loads(cached)
            else:
                self.cache_misses += 1
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar business analytics do cache: {e}")
            return None
    
    async def set_business_analytics(self, business_id: int, period: str, analytics_data: Dict[str, Any]):
        """Cachear analytics de negócio"""
        try:
            analytics_data['cached_at'] = datetime.now().isoformat()
            analytics_data['ttl_seconds'] = self.CACHE_TTL['analytics_overview']
            analytics_data['period'] = period
            
            await cache_service.cache_response(
                message=f"business_analytics_{business_id}_{period}",
                user_id=str(business_id),
                response=json.dumps(analytics_data),
                context={"type": "analytics_overview", "business_id": business_id, "period": period},
                custom_ttl=self.CACHE_TTL['analytics_overview']
            )
            
            self.logger.info(f"💾 Cache SET - Business analytics para business {business_id} (period: {period}, TTL: {self.CACHE_TTL['analytics_overview']}s)")
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear business analytics: {e}")
    
    def _hash_filters(self, filters: Dict[str, Any]) -> str:
        """Gera hash consistente dos filtros para chave de cache"""
        try:
            # Remover valores None e ordenar para consistência
            clean_filters = {k: v for k, v in filters.items() if v is not None}
            filter_str = json.dumps(clean_filters, sort_keys=True, default=str)
            return hashlib.md5(filter_str.encode()).hexdigest()[:8]
        except Exception as e:
            self.logger.error(f"Erro ao gerar hash dos filtros: {e}")
            return "default"
    
    async def invalidate_dashboard_cache(self, business_id: int):
        """Invalidar todo cache relacionado a um business"""
        try:
            # Invalidar cache específico do business
            await cache_service.invalidate_user_cache(str(business_id))
            self.logger.info(f"🧹 Cache INVALIDATED - Dashboard para business {business_id}")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache do dashboard: {e}")
    
    async def invalidate_conversation_cache(self):
        """Invalidar cache de listas de conversas"""
        try:
            await cache_service.invalidate_cache_by_type(CacheType.BUSINESS_DATA)
            self.logger.info("🧹 Cache INVALIDATED - Conversation lists")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de conversas: {e}")
    
    async def invalidate_appointment_cache(self):
        """Invalidar cache de listas de appointments"""
        try:
            await cache_service.invalidate_cache_by_type(CacheType.BUSINESS_DATA)
            self.logger.info("🧹 Cache INVALIDATED - Appointment lists")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de appointments: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas de performance do cache"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'total_requests': total_requests,
            'hit_rate_percentage': round(hit_rate, 2),
            'cache_types': list(self.CACHE_TTL.keys()),
            'ttl_config': self.CACHE_TTL
        }
    
    def reset_stats(self):
        """Reset das estatísticas de cache"""
        self.cache_hits = 0
        self.cache_misses = 0


# Instância global
dashboard_cache = DashboardCacheService()
