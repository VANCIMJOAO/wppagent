"""
PD003 - Cache Invalidation Policy

Política inteligente de invalidação de cache baseada em eventos do sistema.
"""

from typing import List, Dict, Any, Set
from app.services.cache_service import cache_service, CacheType
from app.services.cache_dashboard import dashboard_cache
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CacheInvalidationPolicy:
    """PD003 - Política inteligente de invalidação de cache"""
    
    # Mapeamento de eventos para tipos de cache a invalidar
    INVALIDATION_RULES = {
        # Eventos de mensagens
        'new_message': ['conversation_list', 'dashboard_stats', 'quick_stats', 'user_conversations'],
        'message_updated': ['conversation_list', 'user_conversations'],
        'message_deleted': ['conversation_list', 'dashboard_stats', 'user_conversations'],
        
        # Eventos de conversas
        'new_conversation': ['conversation_list', 'dashboard_stats', 'quick_stats', 'user_conversations'],
        'conversation_updated': ['conversation_list', 'dashboard_stats', 'user_conversations'],
        'conversation_status_changed': ['conversation_list', 'dashboard_stats', 'quick_stats'],
        'conversation_closed': ['conversation_list', 'dashboard_stats', 'quick_stats'],
        'conversation_archived': ['conversation_list', 'dashboard_stats'],
        
        # Eventos de appointments
        'new_appointment': ['appointment_list', 'dashboard_stats', 'business_metrics', 'quick_stats'],
        'appointment_updated': ['appointment_list', 'dashboard_stats', 'quick_stats'],
        'appointment_cancelled': ['appointment_list', 'dashboard_stats', 'business_metrics'],
        'appointment_completed': ['appointment_list', 'dashboard_stats', 'business_metrics'],
        'appointment_rescheduled': ['appointment_list', 'dashboard_stats'],
        
        # Eventos de usuários
        'user_created': ['user_stats', 'dashboard_stats', 'business_metrics'],
        'user_updated': ['user_profile', 'user_conversations', 'dashboard_stats'],
        'user_deleted': ['user_profile', 'user_conversations', 'dashboard_stats', 'business_metrics'],
        'user_login': ['user_stats', 'quick_stats'],
        'user_logout': ['user_stats'],
        
        # Eventos de business
        'business_config_changed': ['business_metrics', 'dashboard_stats', 'analytics_overview'],
        'business_hours_updated': ['business_metrics', 'dashboard_stats'],
        'business_services_updated': ['business_metrics', 'appointment_list'],
        'business_settings_changed': ['dashboard_stats', 'business_metrics', 'analytics_overview'],
        
        # Eventos de sistema
        'daily_analytics_update': ['analytics_overview', 'business_metrics', 'dashboard_stats'],
        'monthly_report_generated': ['analytics_overview'],
        'cache_cleanup_triggered': ['all'],  # Invalidar tudo
        'system_maintenance': ['all'],
        
        # Eventos de performance
        'bulk_data_import': ['all'],  # Quando importar dados em massa
        'database_migration': ['all'],  # Após migrações
        'schema_update': ['all'],
    }
    
    # TTL específico para re-cache após invalidação
    RECACHE_PRIORITY = {
        'dashboard_stats': 1,      # Alta prioridade - sempre recalcular
        'quick_stats': 1,          # Alta prioridade - real-time
        'conversation_list': 2,    # Média prioridade
        'appointment_list': 2,     # Média prioridade  
        'user_conversations': 3,   # Baixa prioridade
        'analytics_overview': 4,   # Muito baixa - pode esperar
        'business_metrics': 3,     # Baixa prioridade
        'user_stats': 3,          # Baixa prioridade
        'user_profile': 4,        # Muito baixa
    }
    
    def __init__(self):
        self.invalidation_count = {}
        self.last_invalidation = {}
        self.logger = logger
    
    async def invalidate_on_event(self, event_type: str, entity_data: Dict[str, Any]):
        """Invalidar cache baseado em evento do sistema"""
        try:
            cache_types_to_invalidate = self.INVALIDATION_RULES.get(event_type, [])
            
            if not cache_types_to_invalidate:
                self.logger.warning(f"⚠️ Evento não mapeado para invalidação: {event_type}")
                return
            
            self.logger.info(f"🔄 Iniciando invalidação para evento: {event_type}")
            
            # Registrar estatísticas
            self.invalidation_count[event_type] = self.invalidation_count.get(event_type, 0) + 1
            self.last_invalidation[event_type] = datetime.now().isoformat()
            
            # Invalidar todos os caches se solicitado
            if 'all' in cache_types_to_invalidate:
                await self._invalidate_all_cache()
                return
            
            # Invalidar caches específicos
            invalidation_tasks = []
            for cache_type in cache_types_to_invalidate:
                if cache_type == 'conversation_list':
                    invalidation_tasks.append(self._invalidate_conversation_cache(entity_data))
                elif cache_type == 'appointment_list':
                    invalidation_tasks.append(self._invalidate_appointment_cache(entity_data))
                elif cache_type == 'dashboard_stats':
                    invalidation_tasks.append(self._invalidate_dashboard_cache(entity_data))
                elif cache_type == 'quick_stats':
                    invalidation_tasks.append(self._invalidate_quick_stats_cache(entity_data))
                elif cache_type == 'user_conversations':
                    invalidation_tasks.append(self._invalidate_user_conversations_cache(entity_data))
                elif cache_type == 'business_metrics':
                    invalidation_tasks.append(self._invalidate_business_metrics_cache(entity_data))
                elif cache_type == 'analytics_overview':
                    invalidation_tasks.append(self._invalidate_analytics_cache(entity_data))
                elif cache_type == 'user_stats':
                    invalidation_tasks.append(self._invalidate_user_stats_cache(entity_data))
                elif cache_type == 'user_profile':
                    invalidation_tasks.append(self._invalidate_user_profile_cache(entity_data))
            
            # Executar invalidações em paralelo
            if invalidation_tasks:
                await asyncio.gather(*invalidation_tasks, return_exceptions=True)
            
            self.logger.info(f"✅ Invalidação concluída para evento {event_type} - {len(cache_types_to_invalidate)} tipos de cache")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na invalidação para evento {event_type}: {e}")
    
    async def _invalidate_conversation_cache(self, data: Dict[str, Any]):
        """Invalidar cache de conversas"""
        try:
            await dashboard_cache.invalidate_conversation_cache()
            
            # Se tem user_id específico, invalidar cache do usuário também
            user_id = data.get('user_id') or data.get('customer_id')
            if user_id:
                await cache_service.invalidate_user_cache(str(user_id))
            
            self.logger.debug("🧹 Cache de conversas invalidado")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de conversas: {e}")
    
    async def _invalidate_appointment_cache(self, data: Dict[str, Any]):
        """Invalidar cache de appointments"""
        try:
            await dashboard_cache.invalidate_appointment_cache()
            
            # Invalidar cache específico do business se disponível
            business_id = data.get('business_id')
            if business_id:
                await dashboard_cache.invalidate_dashboard_cache(business_id)
            
            self.logger.debug("🧹 Cache de appointments invalidado")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de appointments: {e}")
    
    async def _invalidate_dashboard_cache(self, data: Dict[str, Any]):
        """Invalidar cache específico do dashboard"""
        try:
            business_id = data.get('business_id')
            if business_id:
                await dashboard_cache.invalidate_dashboard_cache(business_id)
            else:
                # Se não tem business_id, invalidar cache geral de business
                await cache_service.invalidate_cache_by_type(CacheType.BUSINESS_DATA)
            
            self.logger.debug(f"🧹 Cache de dashboard invalidado (business: {business_id})")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de dashboard: {e}")
    
    async def _invalidate_quick_stats_cache(self, data: Dict[str, Any]):
        """Invalidar cache de estatísticas rápidas"""
        try:
            business_id = data.get('business_id')
            if business_id:
                # Invalidar quick stats específico
                await cache_service.invalidate_user_cache(str(business_id))
            else:
                # Invalidar todos os quick stats
                await cache_service.invalidate_cache_by_type(CacheType.BUSINESS_DATA)
            
            self.logger.debug("🧹 Cache de quick stats invalidado")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de quick stats: {e}")
    
    async def _invalidate_user_conversations_cache(self, data: Dict[str, Any]):
        """Invalidar cache de conversas do usuário"""
        try:
            user_id = data.get('user_id') or data.get('customer_id')
            if user_id:
                await cache_service.invalidate_user_cache(str(user_id))
            else:
                # Se não tem user_id, invalidar cache geral
                await cache_service.invalidate_cache_by_type(CacheType.USER_DATA)
            
            self.logger.debug(f"🧹 Cache de conversas do usuário invalidado (user: {user_id})")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de conversas do usuário: {e}")
    
    async def _invalidate_business_metrics_cache(self, data: Dict[str, Any]):
        """Invalidar cache de métricas de negócio"""
        try:
            business_id = data.get('business_id')
            if business_id:
                await dashboard_cache.invalidate_dashboard_cache(business_id)
            
            # Invalidar cache de métricas gerais também
            await cache_service.invalidate_cache_by_type(CacheType.BUSINESS_DATA)
            
            self.logger.debug("🧹 Cache de métricas de negócio invalidado")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de métricas: {e}")
    
    async def _invalidate_analytics_cache(self, data: Dict[str, Any]):
        """Invalidar cache de analytics"""
        try:
            business_id = data.get('business_id')
            if business_id:
                await dashboard_cache.invalidate_dashboard_cache(business_id)
            
            # Invalidar analytics gerais
            await cache_service.invalidate_cache_by_type(CacheType.ANALYTICS)
            
            self.logger.debug("🧹 Cache de analytics invalidado")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de analytics: {e}")
    
    async def _invalidate_user_stats_cache(self, data: Dict[str, Any]):
        """Invalidar cache de estatísticas do usuário"""
        try:
            user_id = data.get('user_id')
            if user_id:
                await cache_service.invalidate_user_cache(str(user_id))
            
            self.logger.debug("🧹 Cache de user stats invalidado")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de user stats: {e}")
    
    async def _invalidate_user_profile_cache(self, data: Dict[str, Any]):
        """Invalidar cache de perfil do usuário"""
        try:
            user_id = data.get('user_id')
            if user_id:
                await cache_service.invalidate_user_cache(str(user_id))
            
            self.logger.debug("🧹 Cache de user profile invalidado")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache de user profile: {e}")
    
    async def _invalidate_all_cache(self):
        """Invalidar todo o cache do sistema"""
        try:
            await cache_service.clear_all_cache()
            self.logger.warning("🧹 TODO O CACHE FOI INVALIDADO")
        except Exception as e:
            self.logger.error(f"Erro ao invalidar todo cache: {e}")
    
    async def scheduled_invalidation(self, cache_type: str, interval_minutes: int = 60):
        """Invalidação programada para caches específicos"""
        try:
            self.logger.info(f"⏰ Invalidação programada iniciada: {cache_type} (intervalo: {interval_minutes}min)")
            
            if cache_type == 'analytics':
                await cache_service.invalidate_cache_by_type(CacheType.ANALYTICS)
            elif cache_type == 'business_data':
                await cache_service.invalidate_cache_by_type(CacheType.BUSINESS_DATA)
            elif cache_type == 'user_data':
                await cache_service.invalidate_cache_by_type(CacheType.USER_DATA)
            elif cache_type == 'all':
                await self._invalidate_all_cache()
            
            self.logger.info(f"✅ Invalidação programada concluída: {cache_type}")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na invalidação programada {cache_type}: {e}")
    
    async def warm_cache_after_invalidation(self, cache_types: List[str], entity_data: Dict[str, Any]):
        """Re-popular cache crítico após invalidação"""
        try:
            # Ordenar por prioridade
            sorted_cache_types = sorted(
                cache_types, 
                key=lambda x: self.RECACHE_PRIORITY.get(x, 5)
            )
            
            self.logger.info(f"🔥 Iniciando warm-up de cache: {sorted_cache_types}")
            
            for cache_type in sorted_cache_types[:3]:  # Só os 3 mais prioritários
                if cache_type == 'dashboard_stats':
                    business_id = entity_data.get('business_id')
                    if business_id:
                        # Aqui você pode chamar a função que gera dashboard stats
                        # e automaticamente vai cachear via DashboardCacheService
                        pass
                elif cache_type == 'quick_stats':
                    business_id = entity_data.get('business_id')
                    if business_id:
                        # Gerar quick stats automaticamente
                        pass
            
            self.logger.info(f"✅ Cache warm-up concluído")
            
        except Exception as e:
            self.logger.error(f"❌ Erro no warm-up de cache: {e}")
    
    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Obter estatísticas de invalidação"""
        total_invalidations = sum(self.invalidation_count.values())
        
        return {
            'total_invalidations': total_invalidations,
            'invalidations_by_event': self.invalidation_count,
            'last_invalidations': self.last_invalidation,
            'mapped_events': len(self.INVALIDATION_RULES),
            'cache_types_managed': len(set(
                cache_type 
                for cache_list in self.INVALIDATION_RULES.values() 
                for cache_type in cache_list
            )),
            'invalidation_rules': self.INVALIDATION_RULES
        }
    
    def reset_stats(self):
        """Reset das estatísticas"""
        self.invalidation_count = {}
        self.last_invalidation = {}


# Instância global
invalidation_policy = CacheInvalidationPolicy()


# Helper function para facilitar uso em rotas
async def trigger_cache_invalidation(event_type: str, **kwargs):
    """Helper para trigger de invalidação de cache"""
    await invalidation_policy.invalidate_on_event(event_type, kwargs)
