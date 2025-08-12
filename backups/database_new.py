"""
Configuração otimizada do banco de dados com connection pooling avançado
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# URLs do banco
DATABASE_URL_ASYNC = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
DATABASE_URL_SYNC = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

DEBUG = getattr(settings, "debug", False)

# Configurações otimizadas do pool de conexões (sem poolclass para async)
ASYNC_POOL_SETTINGS = {
    "pool_size": getattr(settings, "db_pool_size", 20),
    "max_overflow": getattr(settings, "db_max_overflow", 30),
    "pool_pre_ping": True,
    "pool_recycle": getattr(settings, "db_pool_recycle", 3600),
    "pool_timeout": getattr(settings, "db_pool_timeout", 30),
    "pool_reset_on_return": "commit",
}

# Configurações para engine síncrono
SYNC_POOL_SETTINGS = {
    "pool_size": getattr(settings, "db_pool_size", 20),
    "max_overflow": getattr(settings, "db_max_overflow", 30),
    "pool_pre_ping": True,
    "pool_recycle": getattr(settings, "db_pool_recycle", 3600),
    "pool_timeout": getattr(settings, "db_pool_timeout", 30),
    "pool_reset_on_return": "commit",
    "poolclass": QueuePool,
}

# Engines - aqui que a mágica acontece! 🎭
engine = create_async_engine(
    DATABASE_URL_ASYNC,
    echo=DEBUG,
    echo_pool=DEBUG,
    **ASYNC_POOL_SETTINGS
)

# Engine síncrono para operações especiais
sync_engine = create_engine(
    DATABASE_URL_SYNC,
    echo=DEBUG,
    echo_pool=DEBUG,
    **SYNC_POOL_SETTINGS
)

# Sessions
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

sync_session_factory = sessionmaker(
    sync_engine,
    expire_on_commit=False
)

# Dependency para FastAPI
async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()

def get_sync_db():
    with sync_session_factory() as session:
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Sync database error: {e}")
            raise
        finally:
            session.close()

# Monitoramento de performance
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine.sync_engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # Log queries lentas
        logger.warning(f"Slow query: {total:.4f}s - {statement[:100]}...")

# Health check
async def check_database_health():
    """Verifica a saúde do banco de dados"""
    try:
        async with async_session_factory() as session:
            await session.execute("SELECT 1")
            return {
                "status": "healthy",
                "pool_size": engine.pool.size(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "invalid": engine.pool.invalid(),
                "config": ASYNC_POOL_SETTINGS
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

def check_sync_database_health():
    """Verifica a saúde do banco de dados síncrono"""
    try:
        with sync_session_factory() as session:
            session.execute("SELECT 1")
            return {
                "status": "healthy",
                "pool_size": sync_engine.pool.size(),
                "checked_out": sync_engine.pool.checkedout(),
                "overflow": sync_engine.pool.overflow(),
                "invalid": sync_engine.pool.invalid()
            }
    except Exception as e:
        logger.error(f"Sync database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Otimizações específicas do PostgreSQL
async def optimize_postgresql_settings():
    """Aplica otimizações específicas do PostgreSQL"""
    optimizations = [
        "SET work_mem = '256MB';",
        "SET maintenance_work_mem = '256MB';",
        "SET effective_cache_size = '4GB';",
        "SET random_page_cost = 1.1;",
        "SET effective_io_concurrency = 200;",
        "SET checkpoint_completion_target = 0.9;",
        "SET wal_buffers = '16MB';",
        "SET default_statistics_target = 100;",
    ]
    
    try:
        async with async_session_factory() as session:
            for opt in optimizations:
                await session.execute(opt)
            logger.info("PostgreSQL optimizations applied successfully")
    except Exception as e:
        logger.error(f"Failed to apply PostgreSQL optimizations: {e}")

import time
