"""
🚀 Database Optimizer - Sistema de Otimização de Performance de Banco
Implementa connection pooling avançado, cache de queries e monitoramento
"""

import asyncio
import hashlib
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, QueuePool

from app.config import settings
from app.services.cache_service import CacheService, CacheType
from app.utils.logger import get_logger

logger = get_logger(__name__)

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Métricas de performance de queries"""

    query_hash: str
    execution_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    last_executed: datetime = field(default_factory=datetime.now)
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class ConnectionPoolMetrics:
    """Métricas do pool de conexões"""

    size: int = 0
    checked_in: int = 0
    checked_out: int = 0
    overflow: int = 0
    invalidated: int = 0
    total_connections_created: int = 0
    peak_connections: int = 0


class DatabaseOptimizer:
    """
    🚀 Otimizador de Performance de Banco de Dados

    Funcionalidades:
    - Connection pooling otimizado
    - Cache inteligente de queries
    - Monitoramento de performance
    - Query optimization hints
    - Dead connection detection
    - Adaptive pooling
    """

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service

        # Métricas
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.pool_metrics = ConnectionPoolMetrics()

        # Configurações otimizadas do pool
        self.pool_config = {
            "pool_size": getattr(settings, "db_pool_size", 20),
            "max_overflow": getattr(settings, "db_max_overflow", 30),
            "pool_pre_ping": True,
            "pool_recycle": getattr(settings, "db_pool_recycle", 3600),
            "pool_timeout": getattr(settings, "db_pool_timeout", 30),
            "pool_reset_on_return": "commit",
            "poolclass": AsyncAdaptedQueuePool,
            # Configurações específicas do PostgreSQL
            "connect_args": {
                "command_timeout": 60,
                "server_settings": {
                    "jit": "off",  # Desabilita JIT para queries simples
                    "application_name": "whatsapp_agent",
                },
            },
        }

        # Engine otimizado
        self.optimized_engine = None
        self.optimized_session_factory = None

        # Cache de queries preparadas
        self.prepared_queries: Dict[str, str] = {}

        # Configurações de cache
        self.cache_ttl = {
            "user_lookup": 3600,  # 1 hora
            "business_data": 7200,  # 2 horas
            "conversation_history": 1800,  # 30 min
            "appointment_slots": 300,  # 5 min
            "system_config": 14400,  # 4 horas
        }

        logger.info("🚀 DatabaseOptimizer inicializado")

    async def initialize(self):
        """Inicializa o otimizador com engine otimizado"""
        try:
            # Obter DATABASE_URL com fallback para asyncpg
            import os

            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                # Construir URL a partir de variáveis individuais
                db_host = os.getenv("PGHOST", "localhost")
                db_port = os.getenv("PGPORT", "5432")
                db_name = os.getenv("PGDATABASE", "whatsapp_agent")
                db_user = os.getenv("PGUSER", "postgres")
                db_pass = os.getenv("PGPASSWORD", "")
                database_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            else:
                # Garantir que usa asyncpg
                if database_url.startswith("postgresql://"):
                    database_url = database_url.replace(
                        "postgresql://", "postgresql+asyncpg://", 1
                    )
                elif database_url.startswith("postgres://"):
                    database_url = database_url.replace(
                        "postgres://", "postgresql+asyncpg://", 1
                    )

            logger.info(
                f"DatabaseOptimizer usando: {database_url.split('@')[0] if '@' in database_url else 'Invalid URL'}@***"
            )

            # Criar engine otimizado
            self.optimized_engine = create_async_engine(
                database_url, **self.pool_config, echo=False  # Reduzir logs
            )

            # Session factory otimizada
            self.optimized_session_factory = sessionmaker(
                self.optimized_engine, class_=AsyncSession, expire_on_commit=False
            )

            # Configurar eventos para monitoramento
            self._setup_monitoring()

            # Inicializar cache se disponível
            if self.cache_service:
                await self.cache_service.initialize()

            logger.info("✅ DatabaseOptimizer inicializado com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar DatabaseOptimizer: {e}")
            raise

    def _setup_monitoring(self):
        """Configura monitoramento de queries e conexões"""

        @event.listens_for(self.optimized_engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = time.time()

        @event.listens_for(self.optimized_engine.sync_engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total_time = time.time() - context._query_start_time
            self._record_query_metrics(statement, total_time)

        @event.listens_for(self.optimized_engine.sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            self.pool_metrics.total_connections_created += 1
            current_connections = self.optimized_engine.pool.size()
            if current_connections > self.pool_metrics.peak_connections:
                self.pool_metrics.peak_connections = current_connections

    def _record_query_metrics(self, statement: str, execution_time: float):
        """Registra métricas de performance das queries"""
        query_hash = hashlib.md5(statement.encode()).hexdigest()

        if query_hash not in self.query_metrics:
            self.query_metrics[query_hash] = QueryMetrics(query_hash=query_hash)

        metrics = self.query_metrics[query_hash]
        metrics.execution_count += 1
        metrics.total_time += execution_time
        metrics.avg_time = metrics.total_time / metrics.execution_count
        metrics.min_time = min(metrics.min_time, execution_time)
        metrics.max_time = max(metrics.max_time, execution_time)
        metrics.last_executed = datetime.now()

    @asynccontextmanager
    async def get_optimized_session(self):
        """Context manager para sessões otimizadas"""
        async with self.optimized_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def execute_cached_query(
        self,
        query: str,
        params: Dict[str, Any] = None,
        cache_key: Optional[str] = None,
        cache_ttl: int = 3600,
    ) -> List[Dict]:
        """
        Executa query com cache automático
        """
        if not cache_key:
            cache_key = f"query_{hashlib.md5(f'{query}{params}'.encode()).hexdigest()}"

        # Tentar buscar no cache primeiro
        if self.cache_service:
            cached_result = await self.cache_service.get(
                cache_key, CacheType.BUSINESS_DATA
            )
            if cached_result:
                query_hash = hashlib.md5(query.encode()).hexdigest()
                if query_hash in self.query_metrics:
                    self.query_metrics[query_hash].cache_hits += 1
                return cached_result

        # Executar query
        async with self.get_optimized_session() as session:
            start_time = time.time()

            if params:
                result = await session.execute(text(query), params)
            else:
                result = await session.execute(text(query))

            rows = result.fetchall()

            # Converter para dict
            data = [dict(row._mapping) for row in rows]

            execution_time = time.time() - start_time
            self._record_query_metrics(query, execution_time)

            # Cache do resultado
            if self.cache_service:
                await self.cache_service.set(
                    cache_key, data, CacheType.BUSINESS_DATA, cache_ttl
                )
                query_hash = hashlib.md5(query.encode()).hexdigest()
                if query_hash in self.query_metrics:
                    self.query_metrics[query_hash].cache_misses += 1

            return data

    async def get_user_by_wa_id_cached(self, wa_id: str) -> Optional[Dict]:
        """Busca usuário com cache otimizado"""
        cache_key = f"user_{wa_id}"

        query = """
            SELECT id, wa_id, nome, telefone, email, created_at, updated_at
            FROM users 
            WHERE wa_id = :wa_id
        """

        result = await self.execute_cached_query(
            query, {"wa_id": wa_id}, cache_key, self.cache_ttl["user_lookup"]
        )

        return result[0] if result else None

    async def get_conversation_history_cached(
        self, user_id: int, limit: int = 50
    ) -> List[Dict]:
        """Busca histórico de conversa com cache"""
        cache_key = f"conversation_history_{user_id}_{limit}"

        query = """
            SELECT m.id, m.content, m.message_type, m.timestamp, c.status
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.user_id = :user_id
            ORDER BY m.timestamp DESC
            LIMIT :limit
        """

        return await self.execute_cached_query(
            query,
            {"user_id": user_id, "limit": limit},
            cache_key,
            self.cache_ttl["conversation_history"],
        )

    async def get_available_slots_cached(
        self, date: str, business_id: int = 1
    ) -> List[Dict]:
        """Busca slots disponíveis com cache"""
        cache_key = f"available_slots_{date}_{business_id}"

        query = """
            SELECT slot_time, is_available
            FROM available_slots
            WHERE date = :date AND business_id = :business_id AND is_available = true
            ORDER BY slot_time
        """

        return await self.execute_cached_query(
            query,
            {"date": date, "business_id": business_id},
            cache_key,
            self.cache_ttl["appointment_slots"],
        )

    async def invalidate_user_cache(self, wa_id: str):
        """Invalida cache específico do usuário"""
        if self.cache_service:
            cache_keys = [
                f"user_{wa_id}",
                f"conversation_history_{wa_id}*",  # Pattern matching
            ]

            for key in cache_keys:
                await self.cache_service.delete(key)

    async def get_pool_status(self) -> Dict[str, Any]:
        """Retorna status atual do pool de conexões"""
        if not self.optimized_engine:
            return {"status": "not_initialized"}

        pool = self.optimized_engine.pool

        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalidated(),
            "total_created": self.pool_metrics.total_connections_created,
            "peak_connections": self.pool_metrics.peak_connections,
            "pool_config": {
                "size": self.pool_config["pool_size"],
                "max_overflow": self.pool_config["max_overflow"],
                "timeout": self.pool_config["pool_timeout"],
                "recycle": self.pool_config["pool_recycle"],
            },
        }

    async def get_query_performance_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de performance das queries"""
        if not self.query_metrics:
            return {"total_queries": 0, "metrics": []}

        # Top 10 queries mais lentas
        slow_queries = sorted(
            self.query_metrics.values(), key=lambda x: x.avg_time, reverse=True
        )[:10]

        # Top 10 queries mais executadas
        frequent_queries = sorted(
            self.query_metrics.values(), key=lambda x: x.execution_count, reverse=True
        )[:10]

        return {
            "total_queries": len(self.query_metrics),
            "total_executions": sum(
                m.execution_count for m in self.query_metrics.values()
            ),
            "total_time": sum(m.total_time for m in self.query_metrics.values()),
            "cache_efficiency": {
                "total_hits": sum(m.cache_hits for m in self.query_metrics.values()),
                "total_misses": sum(
                    m.cache_misses for m in self.query_metrics.values()
                ),
            },
            "slow_queries": [
                {
                    "hash": q.query_hash[:8],
                    "avg_time": round(q.avg_time, 4),
                    "max_time": round(q.max_time, 4),
                    "execution_count": q.execution_count,
                }
                for q in slow_queries
            ],
            "frequent_queries": [
                {
                    "hash": q.query_hash[:8],
                    "execution_count": q.execution_count,
                    "avg_time": round(q.avg_time, 4),
                    "cache_hits": q.cache_hits,
                    "cache_misses": q.cache_misses,
                }
                for q in frequent_queries
            ],
        }

    async def optimize_tables(self):
        """Executa otimizações nas tabelas"""
        optimization_queries = [
            # Reindex tabelas principais
            "REINDEX TABLE users;",
            "REINDEX TABLE conversations;",
            "REINDEX TABLE messages;",
            "REINDEX TABLE appointments;",
            # Atualizar estatísticas
            "ANALYZE users;",
            "ANALYZE conversations;",
            "ANALYZE messages;",
            "ANALYZE appointments;",
            # Limpar dead tuples
            "VACUUM (ANALYZE) users;",
            "VACUUM (ANALYZE) conversations;",
            "VACUUM (ANALYZE) messages;",
            "VACUUM (ANALYZE) appointments;",
        ]

        async with self.get_optimized_session() as session:
            for query in optimization_queries:
                try:
                    await session.execute(text(query))
                    logger.info(f"✅ Executado: {query}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao executar {query}: {e}")

        logger.info("🚀 Otimizações de tabela concluídas")

    async def cleanup_old_data(self, days: int = 90):
        """Remove dados antigos para manter performance"""
        cleanup_queries = [
            # Remover mensagens antigas (manter apenas conversas ativas)
            f"""
            DELETE FROM messages 
            WHERE timestamp < NOW() - INTERVAL '{days} days'
            AND conversation_id IN (
                SELECT id FROM conversations WHERE status = 'closed'
            );
            """,
            # Remover sessões expiradas
            "DELETE FROM login_sessions WHERE expires_at < NOW();",
            # Remover logs antigos
            f"DELETE FROM meta_logs WHERE created_at < NOW() - INTERVAL '{days} days';",
        ]

        async with self.get_optimized_session() as session:
            for query in cleanup_queries:
                try:
                    result = await session.execute(text(query))
                    logger.info(
                        f"✅ Limpeza executada: {result.rowcount} registros removidos"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Erro na limpeza: {e}")

        logger.info(f"🧹 Limpeza de dados antigos concluída ({days} dias)")


# Instância global do otimizador
db_optimizer = DatabaseOptimizer()
