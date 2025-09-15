"""
Dashboard Administrativo para Monitoramento de Logs APM
======================================================

Sistema de monitoramento em tempo real com:
- Visualização de logs estruturados em tempo real
- Métricas de performance e APM
- Análise de trends e alertas
- Filtragem avançada por categorias, níveis e contextos
- Dashboard interativo para administradores
"""

import asyncio
import csv
import io
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routes.admin_auth import get_current_admin_user

# Alias para compatibilidade
require_admin = get_current_admin_user
from app.services.structured_apm import (
    LogCategory,
    LogLevel,
    get_current_context,
    get_structured_logger,
)

router = APIRouter(prefix="/apm-logs", tags=["APM Monitoring"])

# Logger para o próprio sistema de monitoramento
logger = get_structured_logger("apm.monitoring")


class LogAnalyzer:
    """Analisador de logs estruturados"""

    def __init__(self, log_dir: Path = Path("logs")):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)

    async def get_recent_logs(
        self,
        limit: int = 100,
        level_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        service_filter: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Obter logs recentes com filtros"""

        logs = []
        log_files = []

        # Coletar arquivos de log
        if self.log_dir.exists():
            log_files.extend(self.log_dir.glob("*.log"))
            log_files.extend(self.log_dir.glob("structured.log*"))

        # Ordenar por data de modificação (mais recente primeiro)
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        for log_file in log_files[:5]:  # Máximo 5 arquivos
            try:
                async with aiofiles.open(log_file, "r", encoding="utf-8") as f:
                    lines = await f.readlines()

                    # Processar linhas mais recentes primeiro
                    for line in reversed(lines[-1000:]):  # Últimas 1000 linhas
                        if len(logs) >= limit:
                            break

                        try:
                            log_entry = json.loads(line.strip())

                            # Aplicar filtros
                            if level_filter and log_entry.get("level") != level_filter:
                                continue

                            if (
                                category_filter
                                and log_entry.get("category") != category_filter
                            ):
                                continue

                            if (
                                service_filter
                                and log_entry.get("service") != service_filter
                            ):
                                continue

                            # Filtro por tempo
                            if start_time or end_time:
                                try:
                                    log_time = datetime.fromisoformat(
                                        log_entry.get("timestamp", "").replace(
                                            "Z", "+00:00"
                                        )
                                    )
                                    if start_time and log_time < start_time:
                                        continue
                                    if end_time and log_time > end_time:
                                        continue
                                except:
                                    continue

                            logs.append(log_entry)

                        except json.JSONDecodeError:
                            # Log não estruturado, pular
                            continue

                        except Exception as e:
                            logger.warning(f"Erro ao processar linha de log: {e}")
                            continue

                if len(logs) >= limit:
                    break

            except Exception as e:
                logger.error(f"Erro ao ler arquivo de log {log_file}: {e}")
                continue

        return logs[:limit]

    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Analisar métricas de performance das últimas horas"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        logs = await self.get_recent_logs(
            limit=1000,
            category_filter="performance",
            start_time=start_time,
            end_time=end_time,
        )

        performance_data = {
            "total_operations": 0,
            "avg_duration_ms": 0,
            "slowest_operations": [],
            "operations_by_type": defaultdict(list),
            "performance_trends": [],
            "alerts": [],
        }

        durations = []
        operations_count = defaultdict(int)

        for log in logs:
            metadata = log.get("metadata", {})
            perf_metrics = metadata.get("performance_metrics", {})

            if perf_metrics:
                operation_name = perf_metrics.get("operation_name", "unknown")
                duration_ms = perf_metrics.get("duration_ms", 0)

                durations.append(duration_ms)
                operations_count[operation_name] += 1
                performance_data["operations_by_type"][operation_name].append(
                    duration_ms
                )

                # Operações mais lentas
                performance_data["slowest_operations"].append(
                    {
                        "operation": operation_name,
                        "duration_ms": duration_ms,
                        "timestamp": log.get("timestamp"),
                        "request_id": log.get("request_id"),
                    }
                )

        if durations:
            performance_data["total_operations"] = len(durations)
            performance_data["avg_duration_ms"] = sum(durations) / len(durations)

            # Top operações mais lentas
            performance_data["slowest_operations"].sort(
                key=lambda x: x["duration_ms"], reverse=True
            )
            performance_data["slowest_operations"] = performance_data[
                "slowest_operations"
            ][:10]

            # Alertas de performance
            if performance_data["avg_duration_ms"] > 1000:
                performance_data["alerts"].append(
                    {
                        "type": "slow_performance",
                        "message": f"Performance média degradada: {performance_data['avg_duration_ms']:.2f}ms",
                        "severity": "warning",
                    }
                )

            slow_operations = [op for op in durations if op > 5000]
            if slow_operations:
                performance_data["alerts"].append(
                    {
                        "type": "very_slow_operations",
                        "message": f"{len(slow_operations)} operações muito lentas (>5s) detectadas",
                        "severity": "critical",
                    }
                )

        return performance_data

    async def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Analisar erros das últimas horas"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        error_logs = await self.get_recent_logs(
            limit=500, level_filter="ERROR", start_time=start_time, end_time=end_time
        )

        critical_logs = await self.get_recent_logs(
            limit=100, level_filter="CRITICAL", start_time=start_time, end_time=end_time
        )

        error_analysis = {
            "total_errors": len(error_logs),
            "total_critical": len(critical_logs),
            "error_rate_per_hour": 0,
            "top_error_types": [],
            "recent_errors": [],
            "error_categories": defaultdict(int),
            "error_trends": [],
        }

        if hours > 0:
            error_analysis["error_rate_per_hour"] = len(error_logs) / hours

        # Analisar tipos de erro
        error_types = Counter()

        for log in error_logs + critical_logs:
            exception = log.get("exception", {})
            error_type = exception.get("type", "Unknown")
            category = log.get("category", "system")

            error_types[error_type] += 1
            error_analysis["error_categories"][category] += 1

            # Erros recentes
            if len(error_analysis["recent_errors"]) < 10:
                error_analysis["recent_errors"].append(
                    {
                        "timestamp": log.get("timestamp"),
                        "level": log.get("level"),
                        "message": log.get("message", "")[:200],
                        "error_type": error_type,
                        "category": category,
                        "request_id": log.get("request_id"),
                        "operation": log.get("operation"),
                    }
                )

        error_analysis["top_error_types"] = [
            {"type": error_type, "count": count}
            for error_type, count in error_types.most_common(10)
        ]

        return error_analysis

    async def get_business_insights(self, hours: int = 24) -> Dict[str, Any]:
        """Analisar eventos de negócio das últimas horas"""

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        business_logs = await self.get_recent_logs(
            limit=1000,
            category_filter="business",
            start_time=start_time,
            end_time=end_time,
        )

        insights = {
            "total_business_events": len(business_logs),
            "events_by_type": defaultdict(int),
            "revenue_events": [],
            "conversion_metrics": {},
            "user_activity": defaultdict(int),
        }

        total_value = 0

        for log in business_logs:
            metadata = log.get("metadata", {})
            business_event = metadata.get("business_event", {})

            if business_event:
                event_type = business_event.get("event_type", "unknown")
                entity_type = business_event.get("entity_type", "unknown")
                action = business_event.get("action", "unknown")
                value = business_event.get("value", 0)

                insights["events_by_type"][f"{event_type}_{action}"] += 1

                if value and value > 0:
                    total_value += value
                    insights["revenue_events"].append(
                        {
                            "event_type": event_type,
                            "entity_type": entity_type,
                            "action": action,
                            "value": value,
                            "timestamp": log.get("timestamp"),
                        }
                    )

                # Atividade por usuário
                user_id = log.get("user_id")
                if user_id:
                    insights["user_activity"][user_id] += 1

        insights["total_revenue"] = total_value
        insights["top_active_users"] = [
            {"user_id": user_id, "event_count": count}
            for user_id, count in Counter(insights["user_activity"]).most_common(10)
        ]

        return insights


# Instância global do analisador
log_analyzer = LogAnalyzer()


@router.get("/dashboard")
async def get_apm_dashboard(
    hours: int = Query(24, ge=1, le=168, description="Período em horas para análise"),
    current_admin: dict = Depends(require_admin),
):
    """Dashboard principal de APM com visão geral do sistema"""

    try:
        # Coletar métricas em paralelo
        performance_task = log_analyzer.get_performance_metrics(hours)
        error_task = log_analyzer.get_error_analysis(hours)
        business_task = log_analyzer.get_business_insights(hours)

        performance_data, error_data, business_data = await asyncio.gather(
            performance_task, error_task, business_task
        )

        # Compilar dashboard
        dashboard = {
            "period": {
                "hours": hours,
                "start_time": (
                    datetime.now(timezone.utc) - timedelta(hours=hours)
                ).isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            },
            "system_health": {
                "total_operations": performance_data.get("total_operations", 0),
                "avg_response_time_ms": performance_data.get("avg_duration_ms", 0),
                "total_errors": error_data.get("total_errors", 0),
                "error_rate": error_data.get("error_rate_per_hour", 0),
                "status": (
                    "healthy"
                    if error_data.get("error_rate_per_hour", 0) < 5
                    else "degraded"
                ),
            },
            "performance": performance_data,
            "errors": error_data,
            "business": business_data,
            "alerts": [],
        }

        # Compilar alertas de todos os módulos
        all_alerts = []
        all_alerts.extend(performance_data.get("alerts", []))

        if error_data.get("total_critical", 0) > 0:
            all_alerts.append(
                {
                    "type": "critical_errors",
                    "message": f"{error_data['total_critical']} erros críticos detectados",
                    "severity": "critical",
                }
            )

        if error_data.get("error_rate_per_hour", 0) > 10:
            all_alerts.append(
                {
                    "type": "high_error_rate",
                    "message": f"Taxa de erro elevada: {error_data['error_rate_per_hour']:.1f} erros/hora",
                    "severity": "warning",
                }
            )

        dashboard["alerts"] = all_alerts
        dashboard["alerts_count"] = {
            "critical": len([a for a in all_alerts if a.get("severity") == "critical"]),
            "warning": len([a for a in all_alerts if a.get("severity") == "warning"]),
            "info": len([a for a in all_alerts if a.get("severity") == "info"]),
        }

        logger.info(
            f"Dashboard APM gerado: {performance_data.get('total_operations', 0)} ops, "
            f"{error_data.get('total_errors', 0)} erros, {len(all_alerts)} alertas"
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": dashboard,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error("Erro ao gerar dashboard APM", exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao gerar dashboard")


@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = Query(50, ge=1, le=500, description="Número máximo de logs"),
    level: Optional[str] = Query(
        None, description="Filtro por nível (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    ),
    category: Optional[str] = Query(None, description="Filtro por categoria"),
    service: Optional[str] = Query(None, description="Filtro por serviço"),
    hours: int = Query(24, ge=1, le=168, description="Período em horas"),
    current_admin: dict = Depends(require_admin),
):
    """Obter logs recentes com filtros avançados"""

    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        logs = await log_analyzer.get_recent_logs(
            limit=limit,
            level_filter=level,
            category_filter=category,
            service_filter=service,
            start_time=start_time,
            end_time=end_time,
        )

        # Estatísticas dos logs retornados
        stats = {
            "total_logs": len(logs),
            "levels": Counter(log.get("level", "unknown") for log in logs),
            "categories": Counter(log.get("category", "unknown") for log in logs),
            "services": Counter(log.get("service", "unknown") for log in logs),
        }

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "logs": logs,
                    "statistics": dict(stats["levels"]),  # Converter Counter para dict
                    "metadata": {
                        "period": f"{hours} hours",
                        "filters_applied": {
                            "level": level,
                            "category": category,
                            "service": service,
                        },
                        "total_returned": len(logs),
                    },
                },
            },
        )

    except Exception as e:
        logger.error("Erro ao obter logs recentes", exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao obter logs")


@router.get("/performance/metrics")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168, description="Período em horas"),
    operation_filter: Optional[str] = Query(None, description="Filtro por operação"),
    current_admin: dict = Depends(require_admin),
):
    """Métricas detalhadas de performance"""

    try:
        metrics = await log_analyzer.get_performance_metrics(hours)

        # Filtrar por operação se especificado
        if operation_filter:
            filtered_ops = {}
            for op_name, durations in metrics["operations_by_type"].items():
                if operation_filter.lower() in op_name.lower():
                    filtered_ops[op_name] = durations
            metrics["operations_by_type"] = filtered_ops

            metrics["slowest_operations"] = [
                op
                for op in metrics["slowest_operations"]
                if operation_filter.lower() in op["operation"].lower()
            ]

        return JSONResponse(status_code=200, content={"success": True, "data": metrics})

    except Exception as e:
        logger.error("Erro ao obter métricas de performance", exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao obter métricas")


@router.get("/errors/analysis")
async def get_error_analysis(
    hours: int = Query(24, ge=1, le=168, description="Período em horas"),
    error_type: Optional[str] = Query(None, description="Filtro por tipo de erro"),
    current_admin: dict = Depends(require_admin),
):
    """Análise detalhada de erros"""

    try:
        analysis = await log_analyzer.get_error_analysis(hours)

        # Filtrar por tipo de erro se especificado
        if error_type:
            analysis["top_error_types"] = [
                error
                for error in analysis["top_error_types"]
                if error_type.lower() in error["type"].lower()
            ]

            analysis["recent_errors"] = [
                error
                for error in analysis["recent_errors"]
                if error_type.lower() in error["error_type"].lower()
            ]

        return JSONResponse(
            status_code=200, content={"success": True, "data": analysis}
        )

    except Exception as e:
        logger.error("Erro ao obter análise de erros", exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao obter análise")


@router.get("/business/insights")
async def get_business_insights(
    hours: int = Query(24, ge=1, le=168, description="Período em horas"),
    current_admin: dict = Depends(require_admin),
):
    """Insights de eventos de negócio"""

    try:
        insights = await log_analyzer.get_business_insights(hours)

        return JSONResponse(
            status_code=200, content={"success": True, "data": insights}
        )

    except Exception as e:
        logger.error("Erro ao obter insights de negócio", exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao obter insights")


@router.get("/context/current")
async def get_current_apm_context(current_admin: dict = Depends(require_admin)):
    """Obter contexto APM atual da requisição"""

    try:
        context = get_current_context()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "current_context": context,
                    "context_variables": {
                        "available": [
                            "request_id",
                            "trace_id",
                            "span_id",
                            "user_id",
                            "session_id",
                            "operation",
                        ],
                        "populated": [k for k, v in context.items() if v],
                    },
                },
            },
        )

    except Exception as e:
        logger.error("Erro ao obter contexto APM", exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao obter contexto")


@router.get("/export/logs")
async def export_logs(
    hours: int = Query(24, ge=1, le=168, description="Período em horas"),
    format: str = Query(
        "json", regex="^(json|csv)$", description="Formato de exportação"
    ),
    level: Optional[str] = Query(None, description="Filtro por nível"),
    category: Optional[str] = Query(None, description="Filtro por categoria"),
    current_admin: dict = Depends(require_admin),
):
    """Exportar logs em formato JSON ou CSV"""

    try:
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        logs = await log_analyzer.get_recent_logs(
            limit=1000,
            level_filter=level,
            category_filter=category,
            start_time=start_time,
            end_time=end_time,
        )

        if format == "json":
            content = json.dumps(
                {
                    "export_info": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "period_hours": hours,
                        "filters": {"level": level, "category": category},
                        "total_logs": len(logs),
                    },
                    "logs": logs,
                },
                indent=2,
                ensure_ascii=False,
            )

            return StreamingResponse(
                io.BytesIO(content.encode("utf-8")),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=logs_{hours}h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                },
            )

        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Cabeçalho
            writer.writerow(
                [
                    "timestamp",
                    "level",
                    "service",
                    "category",
                    "message",
                    "request_id",
                    "user_id",
                    "operation",
                    "logger_name",
                ]
            )

            # Dados
            for log in logs:
                writer.writerow(
                    [
                        log.get("timestamp", ""),
                        log.get("level", ""),
                        log.get("service", ""),
                        log.get("category", ""),
                        log.get("message", "")[:200],  # Truncar mensagem
                        log.get("request_id", ""),
                        log.get("user_id", ""),
                        log.get("operation", ""),
                        log.get("logger_name", ""),
                    ]
                )

            output.seek(0)

            return StreamingResponse(
                io.BytesIO(output.getvalue().encode("utf-8")),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=logs_{hours}h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                },
            )

    except Exception as e:
        logger.error("Erro ao exportar logs", exception=e)
        raise HTTPException(status_code=500, detail="Erro interno ao exportar logs")
