"""
🔄 Sistema de Cache Invalidation Centralizada
=============================================

Sistema centralizado para invalidação inteligente de cache baseado em eventos,
eliminando problemas de cache inconsistente entre diferentes endpoints.

Funcionalidades:
- Invalidation rules baseadas em eventos
- Propagação automática para caches relacionados
- Logging detalhado para debugging
- Suporte a padrões de wildcard
- Context-aware invalidation

Autor: Claude AI
Status: Solução crítica para cache inconsistency
"""

import asyncio
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from app.utils.logger import get_logger
from app.services.cache_optimized import cache_service

logger = get_logger(__name__)


class CacheEvent(str, Enum):
    """Eventos que podem trigger invalidation de cache"""
    # Appointments
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_DELETED = "appointment_deleted"
    APPOINTMENT_STATUS_CHANGED = "appointment_status_changed"
    
    # Conversations
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_UPDATED = "conversation_updated"
    CONVERSATION_DELETED = "conversation_deleted"
    CONVERSATION_MESSAGE_ADDED = "conversation_message_added"
    
    # Clients
    CLIENT_CREATED = "client_created"
    CLIENT_UPDATED = "client_updated"
    CLIENT_DELETED = "client_deleted"
    CLIENT_STATUS_CHANGED = "client_status_changed"
    
    # Business
    BUSINESS_UPDATED = "business_updated"
    BUSINESS_SETTINGS_CHANGED = "business_settings_changed"
    
    # Analytics
    ANALYTICS_RECALCULATED = "analytics_recalculated"
    REPORTS_GENERATED = "reports_generated"
    
    # Dashboard
    DASHBOARD_REFRESH = "dashboard_refresh"
    STATS_UPDATED = "stats_updated"


@dataclass
class InvalidationRule:
    """Regra de invalidação para um evento específico"""
    event: CacheEvent
    patterns: List[str]
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1  # 1 = alta, 2 = média, 3 = baixa
    delay_seconds: int = 0  # Delay antes da invalidação
    context_aware: bool = False  # Se deve usar context para construir patterns


class CacheInvalidationService:
    """
    🎯 Serviço Centralizado de Cache Invalidation
    
    Gerencia todas as regras de invalidação de cache baseado em eventos,
    garantindo consistência entre diferentes módulos e endpoints.
    """
    
    def __init__(self):
        self.rules: Dict[CacheEvent, InvalidationRule] = {}
        self.active_invalidations: Set[str] = set()  # Track invalidations em progresso
        self._setup_rules()
        
    def _setup_rules(self):
        """🔧 Configure invalidation rules para todos os eventos"""
        
        # ===== APPOINTMENT EVENTS =====
        self.rules[CacheEvent.APPOINTMENT_CREATED] = InvalidationRule(
            event=CacheEvent.APPOINTMENT_CREATED,
            patterns=[
                "appointments:list:*",      # Lista de appointments
                "appointments:stats:*",     # Estatísticas de appointments
                "dashboard:stats:*",        # Dashboard geral
                "dashboard:overview:*",     # Overview do dashboard
                "clients:stats:*",          # Stats do cliente afetado
                "analytics:funnel:*",       # Analytics de conversão
                "analytics:appointments:*", # Analytics específico
                "reports:appointments:*",   # Relatórios
                "reports:daily:*",         # Relatórios diários
                "calendar:view:*"          # Views de calendário
            ],
            dependencies=["client_stats", "business_stats"],
            priority=1
        )
        
        self.rules[CacheEvent.APPOINTMENT_UPDATED] = InvalidationRule(
            event=CacheEvent.APPOINTMENT_UPDATED,
            patterns=[
                "appointments:list:*",
                "appointments:detail:{appointment_id}",  # Context-aware
                "appointments:stats:*",
                "dashboard:stats:*",
                "clients:stats:*",
                "analytics:funnel:*",
                "calendar:view:*"
            ],
            context_aware=True,
            priority=1
        )
        
        self.rules[CacheEvent.APPOINTMENT_DELETED] = InvalidationRule(
            event=CacheEvent.APPOINTMENT_DELETED,
            patterns=[
                "appointments:list:*",
                "appointments:detail:{appointment_id}",
                "appointments:stats:*",
                "dashboard:stats:*",
                "clients:stats:*",
                "analytics:funnel:*",
                "reports:appointments:*",
                "calendar:view:*"
            ],
            context_aware=True,
            priority=1
        )
        
        # ===== CONVERSATION EVENTS =====
        self.rules[CacheEvent.CONVERSATION_CREATED] = InvalidationRule(
            event=CacheEvent.CONVERSATION_CREATED,
            patterns=[
                "conversations:list:*",
                "conversations:stats:*",
                "dashboard:stats:*",
                "dashboard:overview:*",
                "clients:stats:*",
                "analytics:conversations:*",
                "analytics:time:*",
                "reports:conversations:*"
            ],
            priority=1
        )
        
        self.rules[CacheEvent.CONVERSATION_UPDATED] = InvalidationRule(
            event=CacheEvent.CONVERSATION_UPDATED,
            patterns=[
                "conversations:list:*",
                "conversations:detail:{conversation_id}",
                "conversations:stats:*",
                "dashboard:stats:*",
                "analytics:time:*"
            ],
            context_aware=True,
            priority=1
        )
        
        self.rules[CacheEvent.CONVERSATION_MESSAGE_ADDED] = InvalidationRule(
            event=CacheEvent.CONVERSATION_MESSAGE_ADDED,
            patterns=[
                "conversations:list:*",
                "conversations:detail:{conversation_id}",
                "conversations:messages:{conversation_id}:*",
                "dashboard:stats:*",
                "analytics:messages:*",
                "reports:messages:*"
            ],
            context_aware=True,
            priority=2
        )
        
        # ===== CLIENT EVENTS =====
        self.rules[CacheEvent.CLIENT_CREATED] = InvalidationRule(
            event=CacheEvent.CLIENT_CREATED,
            patterns=[
                "clients:list:*",
                "clients:stats:*",
                "dashboard:stats:*",
                "analytics:clients:*",
                "reports:clients:*"
            ],
            priority=1
        )
        
        self.rules[CacheEvent.CLIENT_UPDATED] = InvalidationRule(
            event=CacheEvent.CLIENT_UPDATED,
            patterns=[
                "clients:list:*",
                "clients:detail:{client_id}",
                "clients:stats:*",
                "appointments:list:*",     # Appointments do cliente afetado
                "conversations:list:*",   # Conversas do cliente afetado
                "analytics:clients:*"
            ],
            context_aware=True,
            priority=1
        )
        
        # ===== BUSINESS EVENTS =====
        self.rules[CacheEvent.BUSINESS_UPDATED] = InvalidationRule(
            event=CacheEvent.BUSINESS_UPDATED,
            patterns=[
                "business:*",              # Tudo relacionado ao business
                "dashboard:*",             # Todo o dashboard
                "analytics:*",             # Todas as analytics
                "reports:*",               # Todos os relatórios
                "appointments:*",          # Todos appointments
                "conversations:*"          # Todas conversas
            ],
            priority=1,
            delay_seconds=2  # Delay para permitir propagação
        )
        
        # ===== ANALYTICS EVENTS =====
        self.rules[CacheEvent.ANALYTICS_RECALCULATED] = InvalidationRule(
            event=CacheEvent.ANALYTICS_RECALCULATED,
            patterns=[
                "analytics:*",
                "dashboard:overview:*",
                "reports:analytics:*"
            ],
            priority=2
        )
        
        logger.info(f"✅ Cache invalidation rules configuradas: {len(self.rules)} eventos")
    
    async def invalidate_for_event(
        self, 
        event: CacheEvent, 
        context: Optional[Dict[str, Any]] = None,
        skip_dependencies: bool = False
    ) -> Dict[str, Any]:
        """
        🎯 Invalidar cache baseado em evento
        
        Args:
            event: Evento que triggou a invalidação
            context: Contexto adicional (IDs, dados específicos)
            skip_dependencies: Se deve pular invalidação de dependências
            
        Returns:
            Relatório da invalidação executada
        """
        
        if event not in self.rules:
            logger.warning(f"⚠️ Evento não configurado para invalidation: {event}")
            return {"success": False, "reason": "event_not_configured"}
        
        rule = self.rules[event]
        context = context or {}
        
        # Gerar ID único para esta invalidação
        invalidation_id = f"{event}:{hash(str(context))}"
        
        # Evitar invalidações duplicadas simultâneas
        if invalidation_id in self.active_invalidations:
            logger.info(f"⏭️ Invalidation já em progresso: {invalidation_id}")
            return {"success": True, "reason": "already_running"}
        
        self.active_invalidations.add(invalidation_id)
        
        try:
            # Delay se configurado
            if rule.delay_seconds > 0:
                logger.info(f"⏱️ Aguardando {rule.delay_seconds}s antes da invalidation")
                await asyncio.sleep(rule.delay_seconds)
            
            # Construir patterns com context
            final_patterns = self._build_patterns_with_context(rule.patterns, context)
            
            # Executar invalidação
            invalidated_count = 0
            errors = []
            
            for pattern in final_patterns:
                try:
                    if "*" in pattern:
                        # Pattern com wildcard
                        count = await self._invalidate_pattern(pattern)
                        invalidated_count += count
                    else:
                        # Key específica
                        success = await self._invalidate_key(pattern)
                        if success:
                            invalidated_count += 1
                            
                except Exception as e:
                    error_msg = f"Erro invalidando pattern '{pattern}': {e}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)
            
            # Invalidar dependências se necessário
            dependency_count = 0
            if not skip_dependencies and rule.dependencies:
                for dependency in rule.dependencies:
                    try:
                        dep_count = await self._invalidate_pattern(f"{dependency}:*")
                        dependency_count += dep_count
                    except Exception as e:
                        logger.error(f"❌ Erro invalidando dependência '{dependency}': {e}")
            
            # Log do resultado
            logger.info(
                f"✅ Cache invalidated para evento '{event}': "
                f"{invalidated_count} keys, {dependency_count} dependencies, "
                f"{len(errors)} errors"
            )
            
            # 🔔 NOTIFICAR VIA WEBSOCKET - Integração automática
            try:
                # Import dinâmico para evitar circular imports
                from app.services.websocket_cache_sync import notify_cache_invalidation
                
                # Notificar clientes WebSocket sobre a invalidação
                websocket_result = await notify_cache_invalidation(
                    event=event,
                    entity_id=context.get('appointment_id') or context.get('client_id') or context.get('conversation_id'),
                    context=context
                )
                
                logger.debug(f"🔔 WebSocket notification sent: {websocket_result}")
                
            except Exception as ws_error:
                logger.debug(f"WebSocket notification falhou (não crítico): {ws_error}")
            
            return {
                "success": True,
                "event": str(event),
                "invalidated_keys": invalidated_count,
                "invalidated_dependencies": dependency_count,
                "patterns": final_patterns,
                "errors": errors,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"❌ Erro crítico na invalidation para evento '{event}': {e}")
            return {
                "success": False,
                "event": str(event),
                "error": str(e),
                "context": context
            }
            
        finally:
            self.active_invalidations.discard(invalidation_id)
    
    def _build_patterns_with_context(
        self, 
        patterns: List[str], 
        context: Dict[str, Any]
    ) -> List[str]:
        """🔧 Construir patterns finais com context"""
        
        final_patterns = []
        for pattern in patterns:
            if "{" in pattern and "}" in pattern:
                # Pattern context-aware
                try:
                    final_pattern = pattern.format(**context)
                    final_patterns.append(final_pattern)
                except KeyError as e:
                    logger.warning(f"⚠️ Context missing para pattern '{pattern}': {e}")
                    # Usar pattern original como fallback
                    final_patterns.append(pattern)
            else:
                # Pattern estático
                final_patterns.append(pattern)
        
        return final_patterns
    
    async def _invalidate_pattern(self, pattern: str) -> int:
        """🎯 Invalidar todas as keys que matcham um pattern"""
        try:
            return cache_service.invalidate_pattern(pattern)
        except Exception as e:
            logger.error(f"❌ Erro invalidando pattern '{pattern}': {e}")
            return 0
    
    async def _invalidate_key(self, key: str) -> bool:
        """🎯 Invalidar uma key específica"""
        try:
            return cache_service.delete(key)
        except Exception as e:
            logger.error(f"❌ Erro invalidando key '{key}': {e}")
            return False
    
    def get_patterns_for_event(self, event: CacheEvent) -> List[str]:
        """📋 Obter patterns que seriam invalidados por um evento"""
        if event not in self.rules:
            return []
        return self.rules[event].patterns.copy()
    
    def list_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """📋 Listar todas as rules configuradas"""
        return {
            str(event): {
                "patterns": rule.patterns,
                "dependencies": rule.dependencies,
                "priority": rule.priority,
                "delay_seconds": rule.delay_seconds,
                "context_aware": rule.context_aware
            }
            for event, rule in self.rules.items()
        }
    
    async def test_invalidation(
        self, 
        event: CacheEvent, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """🧪 Testar invalidation sem executar (dry-run)"""
        
        if event not in self.rules:
            return {"success": False, "reason": "event_not_configured"}
        
        rule = self.rules[event]
        context = context or {}
        
        final_patterns = self._build_patterns_with_context(rule.patterns, context)
        
        return {
            "event": str(event),
            "patterns": final_patterns,
            "dependencies": rule.dependencies,
            "priority": rule.priority,
            "delay_seconds": rule.delay_seconds,
            "context_aware": rule.context_aware,
            "context": context
        }


# Instância global do serviço
cache_invalidation_service = CacheInvalidationService()


# ===== HELPER FUNCTIONS =====

async def invalidate_appointment_cache(
    event: CacheEvent,
    appointment_id: Optional[int] = None,
    client_id: Optional[int] = None,
    business_id: Optional[int] = None
):
    """🎯 Helper específico para invalidation de appointments"""
    context = {}
    if appointment_id:
        context["appointment_id"] = appointment_id
    if client_id:
        context["client_id"] = client_id
    if business_id:
        context["business_id"] = business_id
    
    return await cache_invalidation_service.invalidate_for_event(event, context)


async def invalidate_conversation_cache(
    event: CacheEvent,
    conversation_id: Optional[int] = None,
    client_id: Optional[int] = None
):
    """🎯 Helper específico para invalidation de conversations"""
    context = {}
    if conversation_id:
        context["conversation_id"] = conversation_id
    if client_id:
        context["client_id"] = client_id
    
    return await cache_invalidation_service.invalidate_for_event(event, context)


async def invalidate_client_cache(
    event: CacheEvent,
    client_id: Optional[int] = None
):
    """🎯 Helper específico para invalidation de clients"""
    context = {}
    if client_id:
        context["client_id"] = client_id
    
    return await cache_invalidation_service.invalidate_for_event(event, context)


# ===== LOGGING & DEBUGGING =====

def log_cache_invalidation_summary():
    """📊 Log resumo das rules de invalidation"""
    rules = cache_invalidation_service.list_all_rules()
    
    logger.info("📊 Cache Invalidation Rules Summary:")
    for event, rule_info in rules.items():
        logger.info(f"  🔹 {event}:")
        logger.info(f"    - Patterns: {len(rule_info['patterns'])}")
        logger.info(f"    - Dependencies: {len(rule_info['dependencies'])}")
        logger.info(f"    - Priority: {rule_info['priority']}")
        if rule_info['delay_seconds'] > 0:
            logger.info(f"    - Delay: {rule_info['delay_seconds']}s")


# Log summary na inicialização
log_cache_invalidation_summary()
