"""
Sistema de Cache Invalidation Manual Avançado
Permite invalidação manual e automática de cache com interface administrativa
"""

import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import redis
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheInvalidationType(str, Enum):
    """Tipos de invalidação de cache"""

    MANUAL = "manual"
    AUTO = "auto"
    SCHEDULED = "scheduled"
    DEPENDENCY = "dependency"
    PATTERN = "pattern"
    BULK = "bulk"


class CacheScope(str, Enum):
    """Escopo de invalidação"""

    ANALYTICS = "analytics"
    CUSTOMERS = "customers"
    CONVERSATIONS = "conversations"
    APPOINTMENTS = "appointments"
    TEMPLATES = "templates"
    REPORTS = "reports"
    DASHBOARD = "dashboard"
    ALL = "all"


@dataclass
class CacheInvalidationRule:
    """Regra de invalidação de cache"""

    rule_id: str
    name: str
    pattern: str
    scope: CacheScope
    auto_trigger: bool = False
    dependencies: List[str] = None
    ttl_seconds: Optional[int] = None
    priority: int = 1
    description: str = ""
    created_at: datetime = None
    last_used: Optional[datetime] = None
    usage_count: int = 0

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.now()


class InvalidationRequest(BaseModel):
    """Request para invalidação manual"""

    keys: Optional[List[str]] = None
    patterns: Optional[List[str]] = None
    scopes: Optional[List[CacheScope]] = None
    invalidation_type: CacheInvalidationType = CacheInvalidationType.MANUAL
    reason: str = "Manual invalidation"
    cascade: bool = False
    dry_run: bool = False


class InvalidationResponse(BaseModel):
    """Response da invalidação"""

    success: bool
    invalidated_keys: List[str]
    affected_scopes: List[str]
    total_keys: int
    execution_time_ms: float
    dry_run: bool = False
    errors: List[str] = []
    warnings: List[str] = []


class CacheInvalidationManager:
    """Gerenciador principal de invalidação de cache"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.rules: Dict[str, CacheInvalidationRule] = {}
        self.invalidation_history: List[Dict] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        self._load_default_rules()

    def _load_default_rules(self):
        """Carrega regras padrão de invalidação"""
        default_rules = [
            CacheInvalidationRule(
                rule_id="analytics_dashboard",
                name="Analytics Dashboard",
                pattern="analytics:dashboard:*",
                scope=CacheScope.ANALYTICS,
                auto_trigger=True,
                dependencies=["analytics:*", "dashboard:*"],
                ttl_seconds=300,
                priority=1,
                description="Invalida cache do dashboard de analytics",
            ),
            CacheInvalidationRule(
                rule_id="customer_data",
                name="Customer Data",
                pattern="customer:*",
                scope=CacheScope.CUSTOMERS,
                auto_trigger=False,
                dependencies=["conversations:*", "appointments:*"],
                priority=2,
                description="Invalida dados de clientes",
            ),
            CacheInvalidationRule(
                rule_id="conversation_cache",
                name="Conversation Cache",
                pattern="conversation:*",
                scope=CacheScope.CONVERSATIONS,
                auto_trigger=True,
                dependencies=["messages:*"],
                ttl_seconds=600,
                priority=1,
                description="Cache de conversas e mensagens",
            ),
            CacheInvalidationRule(
                rule_id="appointment_cache",
                name="Appointment Cache",
                pattern="appointment:*",
                scope=CacheScope.APPOINTMENTS,
                auto_trigger=True,
                dependencies=["calendar:*", "customer:*"],
                priority=1,
                description="Cache de agendamentos",
            ),
            CacheInvalidationRule(
                rule_id="template_performance",
                name="Template Performance",
                pattern="template:performance:*",
                scope=CacheScope.TEMPLATES,
                auto_trigger=False,
                dependencies=["template:*", "analytics:templates:*"],
                ttl_seconds=1800,
                priority=2,
                description="Performance de templates",
            ),
            CacheInvalidationRule(
                rule_id="reports_cache",
                name="Reports Cache",
                pattern="reports:*",
                scope=CacheScope.REPORTS,
                auto_trigger=False,
                dependencies=["analytics:*"],
                ttl_seconds=3600,
                priority=3,
                description="Cache de relatórios",
            ),
        ]

        for rule in default_rules:
            self.rules[rule.rule_id] = rule
            self._build_dependency_graph(rule)

    def _build_dependency_graph(self, rule: CacheInvalidationRule):
        """Constrói grafo de dependências"""
        if rule.rule_id not in self.dependency_graph:
            self.dependency_graph[rule.rule_id] = set()

        for dep in rule.dependencies:
            self.dependency_graph[rule.rule_id].add(dep)

    async def get_cache_keys_by_pattern(self, pattern: str) -> List[str]:
        """Obtém chaves de cache por padrão"""
        try:
            keys = []
            cursor = 0

            while True:
                cursor, partial_keys = self.redis.scan(
                    cursor=cursor, match=pattern, count=1000
                )
                keys.extend([key.decode("utf-8") for key in partial_keys])

                if cursor == 0:
                    break

            return sorted(keys)
        except Exception as e:
            logger.error(f"Erro ao buscar chaves por padrão {pattern}: {e}")
            return []

    async def get_cache_keys_by_scope(self, scope: CacheScope) -> List[str]:
        """Obtém chaves por escopo"""
        scope_patterns = {
            CacheScope.ANALYTICS: ["analytics:*", "dashboard:analytics:*"],
            CacheScope.CUSTOMERS: ["customer:*", "client:*"],
            CacheScope.CONVERSATIONS: ["conversation:*", "chat:*", "message:*"],
            CacheScope.APPOINTMENTS: ["appointment:*", "schedule:*"],
            CacheScope.TEMPLATES: ["template:*"],
            CacheScope.REPORTS: ["report:*", "export:*"],
            CacheScope.DASHBOARD: ["dashboard:*"],
            CacheScope.ALL: ["*"],
        }

        patterns = scope_patterns.get(scope, [])
        all_keys = []

        for pattern in patterns:
            keys = await self.get_cache_keys_by_pattern(pattern)
            all_keys.extend(keys)

        return list(set(all_keys))  # Remove duplicatas

    async def invalidate_keys(self, keys: List[str], dry_run: bool = False) -> Dict:
        """Invalida chaves específicas"""
        start_time = datetime.now()

        if dry_run:
            return {"invalidated_keys": keys, "total_keys": len(keys), "dry_run": True}

        try:
            if keys:
                pipeline = self.redis.pipeline()
                for key in keys:
                    pipeline.delete(key)
                results = pipeline.execute()

                invalidated_count = sum(results)

                # Log da invalidação
                self._log_invalidation(
                    {
                        "type": "keys",
                        "keys": keys,
                        "invalidated_count": invalidated_count,
                        "timestamp": datetime.now(),
                    }
                )

                return {
                    "invalidated_keys": keys[:invalidated_count],
                    "total_keys": invalidated_count,
                    "dry_run": False,
                }
            else:
                return {"invalidated_keys": [], "total_keys": 0, "dry_run": False}

        except Exception as e:
            logger.error(f"Erro ao invalidar chaves: {e}")
            raise HTTPException(
                status_code=500, detail=f"Erro na invalidação: {str(e)}"
            )
        finally:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"Invalidação executada em {execution_time:.2f}ms")

    async def invalidate_by_patterns(
        self, patterns: List[str], dry_run: bool = False
    ) -> Dict:
        """Invalida cache por padrões"""
        all_keys = []

        for pattern in patterns:
            keys = await self.get_cache_keys_by_pattern(pattern)
            all_keys.extend(keys)

        unique_keys = list(set(all_keys))
        return await self.invalidate_keys(unique_keys, dry_run)

    async def invalidate_by_scopes(
        self, scopes: List[CacheScope], dry_run: bool = False
    ) -> Dict:
        """Invalida cache por escopos"""
        all_keys = []

        for scope in scopes:
            keys = await self.get_cache_keys_by_scope(scope)
            all_keys.extend(keys)

        unique_keys = list(set(all_keys))
        return await self.invalidate_keys(unique_keys, dry_run)

    async def invalidate_with_cascade(
        self, keys: List[str], dry_run: bool = False
    ) -> Dict:
        """Invalidação em cascata baseada em dependências"""
        cascade_keys = set(keys)

        # Encontra dependências
        for rule_id, rule in self.rules.items():
            for key in keys:
                for dependency in rule.dependencies:
                    if re.match(dependency.replace("*", ".*"), key):
                        # Adiciona chaves dependentes
                        dependent_keys = await self.get_cache_keys_by_pattern(
                            rule.pattern
                        )
                        cascade_keys.update(dependent_keys)

        final_keys = list(cascade_keys)
        return await self.invalidate_keys(final_keys, dry_run)

    def _log_invalidation(self, invalidation_data: Dict):
        """Registra histórico de invalidação"""
        self.invalidation_history.append(invalidation_data)

        # Mantém apenas os últimos 1000 registros
        if len(self.invalidation_history) > 1000:
            self.invalidation_history = self.invalidation_history[-1000:]

    async def get_cache_statistics(self) -> Dict:
        """Estatísticas do cache"""
        try:
            info = self.redis.info()

            # Contagem por escopo
            scope_counts = {}
            for scope in CacheScope:
                if scope != CacheScope.ALL:
                    keys = await self.get_cache_keys_by_scope(scope)
                    scope_counts[scope.value] = len(keys)

            total_keys = sum(scope_counts.values())

            return {
                "total_keys": total_keys,
                "scope_distribution": scope_counts,
                "memory_usage_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "hit_rate": info.get("keyspace_hit_rate", 0),
                "connected_clients": info.get("connected_clients", 0),
                "invalidation_rules": len(self.rules),
                "last_invalidations": len(self.invalidation_history),
                "redis_version": info.get("redis_version", "unknown"),
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"error": str(e)}

    async def get_invalidation_history(self, limit: int = 50) -> List[Dict]:
        """Histórico de invalidações"""
        return self.invalidation_history[-limit:]

    def add_custom_rule(self, rule: CacheInvalidationRule) -> bool:
        """Adiciona regra customizada"""
        try:
            self.rules[rule.rule_id] = rule
            self._build_dependency_graph(rule)
            logger.info(f"Regra {rule.rule_id} adicionada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar regra: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """Remove regra de invalidação"""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]
                if rule_id in self.dependency_graph:
                    del self.dependency_graph[rule_id]
                logger.info(f"Regra {rule_id} removida com sucesso")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao remover regra: {e}")
            return False

    async def execute_manual_invalidation(
        self, request: InvalidationRequest
    ) -> InvalidationResponse:
        """Executa invalidação manual"""
        start_time = datetime.now()
        errors = []
        warnings = []
        all_invalidated_keys = []
        affected_scopes = set()

        try:
            # Invalidação por chaves específicas
            if request.keys:
                result = await self.invalidate_keys(request.keys, request.dry_run)
                all_invalidated_keys.extend(result["invalidated_keys"])

            # Invalidação por padrões
            if request.patterns:
                result = await self.invalidate_by_patterns(
                    request.patterns, request.dry_run
                )
                all_invalidated_keys.extend(result["invalidated_keys"])

            # Invalidação por escopos
            if request.scopes:
                result = await self.invalidate_by_scopes(
                    request.scopes, request.dry_run
                )
                all_invalidated_keys.extend(result["invalidated_keys"])
                affected_scopes.update([scope.value for scope in request.scopes])

            # Invalidação em cascata
            if request.cascade and all_invalidated_keys:
                cascade_result = await self.invalidate_with_cascade(
                    all_invalidated_keys, request.dry_run
                )
                all_invalidated_keys = cascade_result["invalidated_keys"]

            # Remove duplicatas
            unique_keys = list(set(all_invalidated_keys))

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log da operação
            if not request.dry_run:
                self._log_invalidation(
                    {
                        "type": request.invalidation_type,
                        "reason": request.reason,
                        "keys_count": len(unique_keys),
                        "scopes": list(affected_scopes),
                        "cascade": request.cascade,
                        "timestamp": datetime.now(),
                        "execution_time_ms": execution_time,
                    }
                )

            return InvalidationResponse(
                success=True,
                invalidated_keys=unique_keys,
                affected_scopes=list(affected_scopes),
                total_keys=len(unique_keys),
                execution_time_ms=execution_time,
                dry_run=request.dry_run,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Erro na invalidação manual: {e}")
            return InvalidationResponse(
                success=False,
                invalidated_keys=[],
                affected_scopes=[],
                total_keys=0,
                execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                dry_run=request.dry_run,
                errors=[str(e)],
                warnings=warnings,
            )


# Instância global do gerenciador
cache_invalidation_manager = None


def get_cache_invalidation_manager() -> CacheInvalidationManager:
    """Dependency injection para o gerenciador"""
    global cache_invalidation_manager
    if cache_invalidation_manager is None:
        # Usar redis_manager da configuração da aplicação
        try:
            from app.config.redis_config import redis_manager

            redis_client = redis_manager.client
        except ImportError:
            # Fallback para configuração manual se redis_manager não disponível
            redis_client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30,
            )
        cache_invalidation_manager = CacheInvalidationManager(redis_client)
    return cache_invalidation_manager
