"""
🔍 PF-001: Database Query Performance Middleware
================================================

Middleware para monitoramento de performance de queries SQLAlchemy:
- Log de queries lentas (>500ms)
- Contagem de queries por request
- Detecção de N+1 queries
- Métricas de performance

Implementado para PF-001: Otimizar Queries N+1
"""

import time
import asyncio
from typing import Dict, List, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from threading import local
import logging
from contextvars import ContextVar

from app.utils.logger import get_logger
from app.config import settings
from app.config.config_factory import is_development

logger = get_logger(__name__)

# Context var para rastreamento de queries por request
request_queries: ContextVar[List[Dict]] = ContextVar('request_queries', default=[])
request_start_time: ContextVar[float] = ContextVar('request_start_time', default=0.0)

class QueryPerformanceMonitor:
    """Monitor de performance de queries SQLAlchemy"""
    
    def __init__(self):
        self.setup_sqlalchemy_events()
    
    def setup_sqlalchemy_events(self):
        """Configura eventos SQLAlchemy para monitoramento"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Captura início de execução de query"""
            context._query_start_time = time.time()
            context._query_statement = statement
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Captura fim de execução e calcula duração"""
            duration = time.time() - getattr(context, '_query_start_time', time.time())
            
            # Adicionar query ao contexto atual da request
            try:
                queries = request_queries.get([])
                query_info = {
                    'statement': statement.replace('\n', ' ').replace('\t', ' '),
                    'duration_ms': round(duration * 1000, 2),
                    'parameters': str(parameters) if parameters else None,
                    'timestamp': time.time()
                }
                queries.append(query_info)
                request_queries.set(queries)
                
                # Log queries lentas
                if duration > 0.5:  # >500ms
                    logger.warning(
                        "🐌 Slow query detected",
                        extra={
                            "query": statement.replace('\n', ' ')[:200] + "..." if len(statement) > 200 else statement,
                            "duration_ms": round(duration * 1000, 2),
                            "category": "performance"
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Erro ao capturar query info: {e}")


class DatabasePerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware para monitoramento de performance de database
    
    Features:
    - Contagem de queries por request
    - Detecção de queries lentas
    - Logging estruturado de métricas
    - Alertas para possíveis N+1 queries
    """
    
    def __init__(self, app, slow_query_threshold_ms: float = 500):
        super().__init__(app)
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_monitor = QueryPerformanceMonitor()
    
    async def dispatch(self, request: Request, call_next):
        """Process request com monitoramento de queries"""
        
        # Inicializar contexto da request
        request_queries.set([])
        start_time = time.time()
        request_start_time.set(start_time)
        
        # Processar request
        response = await call_next(request)
        
        # Calcular métricas
        total_duration = time.time() - start_time
        queries = request_queries.get([])
        query_count = len(queries)
        total_query_time = sum(q['duration_ms'] for q in queries) / 1000
        
        # Log métricas de performance
        self._log_performance_metrics(
            request, response, total_duration, 
            query_count, total_query_time, queries
        )
        
        # Adicionar headers de debug se habilitado
        if is_development():
            response.headers["X-DB-Query-Count"] = str(query_count)
            response.headers["X-DB-Query-Time"] = f"{total_query_time:.3f}s"
            response.headers["X-Total-Duration"] = f"{total_duration:.3f}s"
        
        return response
    
    def _log_performance_metrics(
        self, request: Request, response: Response, 
        total_duration: float, query_count: int, 
        total_query_time: float, queries: List[Dict]
    ):
        """Log métricas estruturadas de performance"""
        
        # Detectar possíveis N+1 queries
        n_plus_one_detected = self._detect_n_plus_one(queries)
        
        # Log básico de performance
        log_data = {
            "method": request.method,
            "url": str(request.url.path),
            "status_code": response.status_code,
            "total_duration_ms": round(total_duration * 1000, 2),
            "query_count": query_count,
            "total_query_time_ms": round(total_query_time * 1000, 2),
            "query_efficiency": round((total_query_time / total_duration) * 100, 1) if total_duration > 0 else 0,
            "category": "database_performance"
        }
        
        # Log warning para requests lentos
        if total_duration > 0.5:
            logger.warning(
                f"🐌 Slow request: {request.method} {request.url.path} took {total_duration:.3f}s",
                extra=log_data
            )
        
        # Log warning para muitas queries (possível N+1)
        if query_count > 10:
            logger.warning(
                f"🔢 High query count: {query_count} queries for {request.method} {request.url.path}",
                extra={**log_data, "possible_n_plus_one": True}
            )
        
        # Log N+1 detection
        if n_plus_one_detected:
            logger.error(
                f"⚠️  N+1 query pattern detected in {request.method} {request.url.path}",
                extra={
                    **log_data,
                    "n_plus_one_detected": True,
                    "similar_queries": n_plus_one_detected["count"],
                    "pattern": n_plus_one_detected["pattern"]
                }
            )
        
        # Log info normal para requests rápidos
        if total_duration <= 0.5 and query_count <= 10:
            logger.info(
                f"✅ Fast request: {request.method} {request.url.path}",
                extra=log_data
            )
    
    def _detect_n_plus_one(self, queries: List[Dict]) -> Optional[Dict]:
        """
        Detecta padrões de N+1 queries
        
        N+1 pattern: Uma query inicial seguida de N queries similares
        """
        if len(queries) < 3:
            return None
        
        # Agrupar queries similares
        query_patterns = {}
        for query in queries:
            # Normalizar query removendo valores específicos
            normalized = self._normalize_query(query['statement'])
            if normalized not in query_patterns:
                query_patterns[normalized] = []
            query_patterns[normalized].append(query)
        
        # Procurar padrões suspeitos (mesmo padrão repetido muitas vezes)
        for pattern, pattern_queries in query_patterns.items():
            if len(pattern_queries) > 5:  # Mais de 5 queries similares
                return {
                    "pattern": pattern[:100] + "..." if len(pattern) > 100 else pattern,
                    "count": len(pattern_queries),
                    "total_time_ms": sum(q['duration_ms'] for q in pattern_queries)
                }
        
        return None
    
    def _normalize_query(self, query: str) -> str:
        """
        Normaliza query removendo valores específicos para detectar padrões
        """
        import re
        
        # Remover valores numéricos
        normalized = re.sub(r'\b\d+\b', '?', query)
        # Remover strings entre aspas
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        # Remover múltiplos espaços
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip().lower()


# Instância global do middleware
database_performance_middleware = DatabasePerformanceMiddleware