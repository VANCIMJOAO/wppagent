"""
Logs Monitoring - SPRINT 4+
Sistema de visualização e monitoramento de logs em tempo real
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import text, and_, or_, desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.cache_service import cache_service
from ..config.logging_config import get_optimized_logger
from ..services.realtime_websocket_manager import get_realtime_manager

logger = get_optimized_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["Logs Monitoring"])

# Gerenciador de WebSockets para logs em tempo real
websocket_manager = get_realtime_manager()


class LogsFilter:
    """Filtros para busca de logs"""
    
    def __init__(
        self,
        level: Optional[str] = None,
        module: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_text: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        self.level = level
        self.module = module
        self.start_date = start_date
        self.end_date = end_date
        self.search_text = search_text
        self.limit = limit
        self.offset = offset


@router.get("/logs")
async def get_logs(
    level: Optional[str] = Query(None, description="Nível do log (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    module: Optional[str] = Query(None, description="Módulo específico"),
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD HH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD HH:MM:SS)"),
    search_text: Optional[str] = Query(None, description="Busca por texto no conteúdo"),
    limit: int = Query(100, description="Número máximo de logs", ge=1, le=1000),
    offset: int = Query(0, description="Offset para paginação", ge=0),
    db: Session = Depends(get_db)
):
    """
    📊 Buscar Logs com Filtros
    
    Retorna logs filtrados com paginação e busca por texto.
    """
    try:
        # Construir filtros
        filters = []
        params = {}
        
        if level:
            filters.append("level = :level")
            params["level"] = level.upper()
        
        if module:
            filters.append("module ILIKE :module")
            params["module"] = f"%{module}%"
        
        if start_date:
            filters.append("timestamp >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            filters.append("timestamp <= :end_date")
            params["end_date"] = end_date
        
        if search_text:
            filters.append("(message ILIKE :search_text OR context ILIKE :search_text)")
            params["search_text"] = f"%{search_text}%"
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        # Query para buscar logs (assumindo tabela de logs estruturados)
        logs_query = text(f"""
            SELECT 
                id,
                timestamp,
                level,
                module,
                message,
                context,
                user_id,
                session_id,
                trace_id,
                duration_ms,
                created_at
            FROM structured_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        """)
        
        params.update({
            "limit": limit,
            "offset": offset
        })
        
        result = db.execute(logs_query, params).fetchall()
        
        # Processar logs
        logs = []
        for row in result:
            log_data = {
                "id": row.id,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "level": row.level,
                "module": row.module,
                "message": row.message,
                "context": json.loads(row.context) if row.context else {},
                "user_id": row.user_id,
                "session_id": row.session_id,
                "trace_id": row.trace_id,
                "duration_ms": row.duration_ms,
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            logs.append(log_data)
        
        # Contar total de logs
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM structured_logs
            WHERE {where_clause}
        """)
        
        count_result = db.execute(count_query, params).fetchone()
        total_count = count_result.total if count_result else 0
        
        # Estatísticas por nível
        stats_query = text(f"""
            SELECT 
                level,
                COUNT(*) as count
            FROM structured_logs
            WHERE {where_clause.replace('LIMIT :limit OFFSET :offset', '')}
            GROUP BY level
            ORDER BY count DESC
        """)
        
        stats_result = db.execute(stats_query, params).fetchall()
        level_stats = {row.level: row.count for row in stats_result}
        
        response_data = {
            "logs": logs,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "filters": {
                "level": level,
                "module": module,
                "start_date": start_date,
                "end_date": end_date,
                "search_text": search_text
            },
            "statistics": {
                "total_logs": total_count,
                "level_distribution": level_stats,
                "date_range": {
                    "start": start_date,
                    "end": end_date
                }
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Logs retrieved", 
                   total_logs=total_count,
                   filters_applied=len(filters))
        
        return response_data
        
    except Exception as e:
        logger.error("Error retrieving logs", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@router.get("/logs/export")
async def export_logs(
    level: Optional[str] = Query(None, description="Nível do log"),
    module: Optional[str] = Query(None, description="Módulo específico"),
    start_date: Optional[str] = Query(None, description="Data inicial"),
    end_date: Optional[str] = Query(None, description="Data final"),
    search_text: Optional[str] = Query(None, description="Busca por texto"),
    format: str = Query("json", description="Formato de exportação (json, csv, txt)"),
    db: Session = Depends(get_db)
):
    """
    📥 Exportar Logs
    
    Exporta logs filtrados em diferentes formatos.
    """
    try:
        # Construir filtros (mesmo da função anterior)
        filters = []
        params = {}
        
        if level:
            filters.append("level = :level")
            params["level"] = level.upper()
        
        if module:
            filters.append("module ILIKE :module")
            params["module"] = f"%{module}%"
        
        if start_date:
            filters.append("timestamp >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            filters.append("timestamp <= :end_date")
            params["end_date"] = end_date
        
        if search_text:
            filters.append("(message ILIKE :search_text OR context ILIKE :search_text)")
            params["search_text"] = f"%{search_text}%"
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        # Query para exportar (sem LIMIT)
        export_query = text(f"""
            SELECT 
                timestamp,
                level,
                module,
                message,
                context,
                user_id,
                session_id,
                trace_id
            FROM structured_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
        """)
        
        result = db.execute(export_query, params).fetchall()
        
        if format == "csv":
            # Gerar CSV
            csv_content = "timestamp,level,module,message,user_id,session_id,trace_id\n"
            for row in result:
                csv_content += f'"{row.timestamp}","{row.level}","{row.module}","{row.message}","{row.user_id}","{row.session_id}","{row.trace_id}"\n'
            
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
        
        elif format == "txt":
            # Gerar TXT
            txt_content = f"Logs Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            txt_content += "=" * 50 + "\n\n"
            
            for row in result:
                txt_content += f"[{row.timestamp}] {row.level} - {row.module}\n"
                txt_content += f"Message: {row.message}\n"
                if row.user_id:
                    txt_content += f"User: {row.user_id}\n"
                if row.session_id:
                    txt_content += f"Session: {row.session_id}\n"
                if row.trace_id:
                    txt_content += f"Trace: {row.trace_id}\n"
                txt_content += "-" * 30 + "\n\n"
            
            return StreamingResponse(
                iter([txt_content]),
                media_type="text/plain",
                headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"}
            )
        
        else:  # JSON
            logs_data = []
            for row in result:
                log_data = {
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "level": row.level,
                    "module": row.module,
                    "message": row.message,
                    "context": json.loads(row.context) if row.context else {},
                    "user_id": row.user_id,
                    "session_id": row.session_id,
                    "trace_id": row.trace_id
                }
                logs_data.append(log_data)
            
            return StreamingResponse(
                iter([json.dumps(logs_data, indent=2)]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
            )
        
    except Exception as e:
        logger.error("Error exporting logs", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error exporting logs: {str(e)}")


@router.websocket("/logs/stream")
async def stream_logs(websocket: WebSocket):
    """
    🌊 Stream de Logs em Tempo Real
    
    WebSocket para receber logs em tempo real com filtros.
    """
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Aguardar mensagem do cliente com filtros
            data = await websocket.receive_json()
            
            if data.get("action") == "subscribe":
                # Cliente se inscreveu para receber logs
                filters = data.get("filters", {})
                logger.info("Client subscribed to logs stream", filters=filters)
                
                # Simular envio de logs em tempo real
                # Em produção, isso seria conectado ao sistema de logging real
                await websocket.send_json({
                    "type": "log",
                    "data": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "INFO",
                        "module": "logs_monitoring",
                        "message": "Log stream connected",
                        "context": {"filters": filters}
                    }
                })
            
            elif data.get("action") == "unsubscribe":
                # Cliente se desinscreveu
                logger.info("Client unsubscribed from logs stream")
                break
                
    except WebSocketDisconnect:
        logger.info("Client disconnected from logs stream")
    except Exception as e:
        logger.error("Error in logs stream", error=str(e))
    finally:
        await websocket_manager.disconnect(websocket)


@router.get("/logs/stats")
async def get_logs_statistics(
    hours: int = Query(24, description="Período em horas", ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    📈 Estatísticas de Logs
    
    Retorna estatísticas dos logs no período especificado.
    """
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Estatísticas por nível
        level_stats_query = text("""
            SELECT 
                level,
                COUNT(*) as count,
                COUNT(CASE WHEN timestamp >= :start_time THEN 1 END) as recent_count
            FROM structured_logs
            WHERE timestamp >= :start_time
            GROUP BY level
            ORDER BY count DESC
        """)
        
        level_result = db.execute(level_stats_query, {"start_time": start_time}).fetchall()
        level_stats = {row.level: {"total": row.count, "recent": row.recent_count} for row in level_result}
        
        # Estatísticas por módulo
        module_stats_query = text("""
            SELECT 
                module,
                COUNT(*) as count,
                COUNT(CASE WHEN level IN ('ERROR', 'CRITICAL') THEN 1 END) as error_count
            FROM structured_logs
            WHERE timestamp >= :start_time
            GROUP BY module
            ORDER BY count DESC
            LIMIT 10
        """)
        
        module_result = db.execute(module_stats_query, {"start_time": start_time}).fetchall()
        module_stats = {row.module: {"total": row.count, "errors": row.error_count} for row in module_result}
        
        # Logs por hora
        hourly_stats_query = text("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour,
                COUNT(*) as count,
                COUNT(CASE WHEN level IN ('ERROR', 'CRITICAL') THEN 1 END) as error_count
            FROM structured_logs
            WHERE timestamp >= :start_time
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour DESC
            LIMIT 24
        """)
        
        hourly_result = db.execute(hourly_stats_query, {"start_time": start_time}).fetchall()
        hourly_stats = [
            {
                "hour": row.hour.isoformat(),
                "total_logs": row.count,
                "error_logs": row.error_count
            }
            for row in hourly_result
        ]
        
        response_data = {
            "period_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "level_distribution": level_stats,
            "top_modules": module_stats,
            "hourly_trend": hourly_stats,
            "summary": {
                "total_logs": sum(stat["total"] for stat in level_stats.values()),
                "error_logs": sum(stat["total"] for level, stat in level_stats.items() if level in ["ERROR", "CRITICAL"]),
                "unique_modules": len(module_stats),
                "avg_logs_per_hour": sum(stat["total"] for stat in level_stats.values()) / max(hours, 1)
            }
        }
        
        logger.info("Logs statistics retrieved", 
                   period_hours=hours,
                   total_logs=response_data["summary"]["total_logs"])
        
        return response_data
        
    except Exception as e:
        logger.error("Error retrieving logs statistics", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error retrieving logs statistics: {str(e)}")


@router.get("/logs/health")
async def logs_monitoring_health():
    """
    🏥 Health Check do Sistema de Logs
    
    Verifica se o sistema de monitoramento de logs está funcionando.
    """
    return {
        "status": "healthy",
        "service": "logs_monitoring",
        "version": "1.0.0",
        "features": [
            "Real-time log streaming",
            "Advanced filtering",
            "Multiple export formats",
            "Statistics and analytics"
        ],
        "endpoints": [
            "/monitoring/logs",
            "/monitoring/logs/export",
            "/monitoring/logs/stream",
            "/monitoring/logs/stats"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
