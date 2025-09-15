"""
API Router para Cache Invalidation Manual
Interface administrativa para gerenciamento de cache
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..services.cache_invalidation_manual import (
    CacheInvalidationManager, CacheInvalidationRule, CacheInvalidationType,
    CacheScope, InvalidationRequest, InvalidationResponse,
    get_cache_invalidation_manager)
# from ..auth.dependencies import get_current_admin_user  # Comentado para desenvolvimento
from ..services.structured_apm import StructuredLogger


# Mock para desenvolvimento - remover em produção
async def get_current_admin_user():
    """Mock de usuário admin para desenvolvimento"""

    class MockUser:
        id = "admin_mock"
        email = "admin@example.com"
        role = "admin"

    return MockUser()


router = APIRouter(prefix="/api/cache", tags=["Cache Management"])
logger = StructuredLogger(__name__)


@router.post("/invalidate", response_model=InvalidationResponse)
async def manual_cache_invalidation(
    request: InvalidationRequest,
    background_tasks: BackgroundTasks,
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
    current_user=Depends(get_current_admin_user),
):
    """
    Endpoint principal para invalidação manual de cache

    Permite invalidar cache por:
    - Chaves específicas
    - Padrões de chaves
    - Escopos predefinidos
    - Invalidação em cascata
    """
    try:
        correlation_id = logger.generate_correlation_id()

        logger.info(
            "Iniciando invalidação manual de cache",
            correlation_id=correlation_id,
            user_id=getattr(current_user, "id", "unknown"),
            invalidation_type=request.invalidation_type,
            dry_run=request.dry_run,
            keys_count=len(request.keys or []),
            patterns_count=len(request.patterns or []),
            scopes_count=len(request.scopes or []),
            cascade=request.cascade,
        )

        # Validações
        if not any([request.keys, request.patterns, request.scopes]):
            raise HTTPException(
                status_code=400,
                detail="Deve especificar ao menos keys, patterns ou scopes",
            )

        # Executa invalidação
        result = await manager.execute_manual_invalidation(request)

        # Log do resultado
        logger.info(
            "Invalidação manual concluída",
            correlation_id=correlation_id,
            success=result.success,
            total_keys=result.total_keys,
            execution_time_ms=result.execution_time_ms,
            dry_run=result.dry_run,
            errors_count=len(result.errors),
        )

        # Se não for dry run, agenda tarefas em background
        if not request.dry_run and result.success:
            background_tasks.add_task(
                log_invalidation_audit, manager, request, result, current_user
            )

        return result

    except Exception as e:
        logger.error(
            f"Erro na invalidação manual: {str(e)}",
            correlation_id=correlation_id,
            user_id=getattr(current_user, "id", "unknown"),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def cache_statistics(
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
    current_user=Depends(get_current_admin_user),
):
    """Estatísticas detalhadas do cache"""
    try:
        stats = await manager.get_cache_statistics()

        logger.info(
            "Estatísticas de cache consultadas",
            user_id=getattr(current_user, "id", "unknown"),
            total_keys=stats.get("total_keys", 0),
            memory_usage_mb=stats.get("memory_usage_mb", 0),
        )

        return {"success": True, "data": stats, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys")
async def list_cache_keys(
    pattern: Optional[str] = Query(None, description="Padrão para filtrar chaves"),
    scope: Optional[CacheScope] = Query(None, description="Escopo para filtrar"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de chaves retornadas"),
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
    current_user=Depends(get_current_admin_user),
):
    """Lista chaves de cache com filtros"""
    try:
        if pattern:
            keys = await manager.get_cache_keys_by_pattern(pattern)
        elif scope:
            keys = await manager.get_cache_keys_by_scope(scope)
        else:
            keys = await manager.get_cache_keys_by_pattern("*")

        # Aplica limite
        limited_keys = keys[:limit]

        return {
            "success": True,
            "data": {
                "keys": limited_keys,
                "total_found": len(keys),
                "returned": len(limited_keys),
                "pattern": pattern,
                "scope": scope.value if scope else None,
            },
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Erro ao listar chaves: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def invalidation_history(
    limit: int = Query(50, ge=1, le=500, description="Número de registros"),
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
    current_user=Depends(get_current_admin_user),
):
    """Histórico de invalidações"""
    try:
        history = await manager.get_invalidation_history(limit)

        return {
            "success": True,
            "data": {"invalidations": history, "count": len(history)},
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Erro ao obter histórico: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def list_invalidation_rules(
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
    current_user=Depends(get_current_admin_user),
):
    """Lista todas as regras de invalidação"""
    try:
        rules_data = []
        for rule_id, rule in manager.rules.items():
            rules_data.append(
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "pattern": rule.pattern,
                    "scope": rule.scope.value,
                    "auto_trigger": rule.auto_trigger,
                    "dependencies": rule.dependencies,
                    "priority": rule.priority,
                    "description": rule.description,
                    "created_at": (
                        rule.created_at.isoformat() if rule.created_at else None
                    ),
                    "last_used": rule.last_used.isoformat() if rule.last_used else None,
                    "usage_count": rule.usage_count,
                }
            )

        return {
            "success": True,
            "data": {"rules": rules_data, "count": len(rules_data)},
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Erro ao listar regras: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules")
async def create_invalidation_rule(
    rule_data: Dict[str, Any],
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
    current_user=Depends(get_current_admin_user),
):
    """Cria nova regra de invalidação"""
    try:
        # Validação básica
        required_fields = ["rule_id", "name", "pattern", "scope"]
        for field in required_fields:
            if field not in rule_data:
                raise HTTPException(
                    status_code=400, detail=f"Campo obrigatório ausente: {field}"
                )

        # Cria regra
        rule = CacheInvalidationRule(
            rule_id=rule_data["rule_id"],
            name=rule_data["name"],
            pattern=rule_data["pattern"],
            scope=CacheScope(rule_data["scope"]),
            auto_trigger=rule_data.get("auto_trigger", False),
            dependencies=rule_data.get("dependencies", []),
            ttl_seconds=rule_data.get("ttl_seconds"),
            priority=rule_data.get("priority", 1),
            description=rule_data.get("description", ""),
            created_at=datetime.now(),
        )

        success = manager.add_custom_rule(rule)

        if success:
            logger.info(
                f"Regra de invalidação criada: {rule.rule_id}",
                user_id=getattr(current_user, "id", "unknown"),
                rule_id=rule.rule_id,
                scope=rule.scope.value,
            )

            return {
                "success": True,
                "message": f"Regra {rule.rule_id} criada com sucesso",
                "rule_id": rule.rule_id,
            }
        else:
            raise HTTPException(status_code=400, detail="Falha ao criar regra")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Valor inválido: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao criar regra: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_invalidation_rule(
    rule_id: str,
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
    current_user=Depends(get_current_admin_user),
):
    """Remove regra de invalidação"""
    try:
        success = manager.remove_rule(rule_id)

        if success:
            logger.info(
                f"Regra de invalidação removida: {rule_id}",
                user_id=getattr(current_user, "id", "unknown"),
                rule_id=rule_id,
            )

            return {"success": True, "message": f"Regra {rule_id} removida com sucesso"}
        else:
            raise HTTPException(status_code=404, detail="Regra não encontrada")

    except Exception as e:
        logger.error(f"Erro ao remover regra: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-invalidate")
async def bulk_cache_invalidation(
    scopes: List[CacheScope],
    background_tasks: BackgroundTasks,
    dry_run: bool = Query(False, description="Simular sem executar"),
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
    current_user=Depends(get_current_admin_user),
):
    """Invalidação em lote por múltiplos escopos"""
    try:
        correlation_id = logger.generate_correlation_id()

        logger.warning(
            "Iniciando invalidação em lote",
            correlation_id=correlation_id,
            user_id=getattr(current_user, "id", "unknown"),
            scopes=[scope.value for scope in scopes],
            dry_run=dry_run,
        )

        request = InvalidationRequest(
            scopes=scopes,
            invalidation_type=CacheInvalidationType.BULK,
            reason="Bulk invalidation via API",
            cascade=True,
            dry_run=dry_run,
        )

        result = await manager.execute_manual_invalidation(request)

        if not dry_run and result.success:
            background_tasks.add_task(
                log_invalidation_audit, manager, request, result, current_user
            )

        return result

    except Exception as e:
        logger.error(f"Erro na invalidação em lote: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


from ..services.cache_admin_dashboard import cache_admin_dashboard


@router.get("/admin", response_class=HTMLResponse)
async def cache_admin_interface():
    """Interface web para administração de cache"""
    return await cache_admin_dashboard()


@router.get("/health")
async def cache_health_check(
    manager: CacheInvalidationManager = Depends(get_cache_invalidation_manager),
):
    """Health check do sistema de cache"""
    try:
        stats = await manager.get_cache_statistics()

        # Determina saúde do sistema
        health_status = "healthy"
        issues = []

        if stats.get("memory_usage_mb", 0) > 1000:  # > 1GB
            issues.append("High memory usage")
            health_status = "warning"

        if stats.get("hit_rate", 0) < 0.8:  # < 80%
            issues.append("Low hit rate")
            health_status = "warning"

        if stats.get("connected_clients", 0) == 0:
            issues.append("No connected clients")
            health_status = "critical"

        return {
            "status": health_status,
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "issues": issues,
            "cache_invalidation": {
                "rules_count": len(manager.rules),
                "history_count": len(manager.invalidation_history),
                "dependency_graph_size": len(manager.dependency_graph),
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


# Funções auxiliares
async def log_invalidation_audit(
    manager: CacheInvalidationManager,
    request: InvalidationRequest,
    result: InvalidationResponse,
    user: Any,
):
    """Log de auditoria para invalidações"""
    try:
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": getattr(user, "id", "unknown"),
            "user_email": getattr(user, "email", "unknown"),
            "action": "cache_invalidation",
            "request": {
                "type": request.invalidation_type,
                "reason": request.reason,
                "keys_count": len(request.keys or []),
                "patterns": request.patterns,
                "scopes": [s.value for s in (request.scopes or [])],
                "cascade": request.cascade,
            },
            "result": {
                "success": result.success,
                "total_keys": result.total_keys,
                "execution_time_ms": result.execution_time_ms,
                "errors_count": len(result.errors),
            },
        }

        logger.info("Auditoria de invalidação registrada", **audit_entry)

    except Exception as e:
        logger.error(f"Erro ao registrar auditoria: {str(e)}")
