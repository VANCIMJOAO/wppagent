"""
Configuração otimizada do banco de dados com connect# Engine síncrono para operações especiais
sync_engine = create_engine(
    DATABASE_URL_SYNC,
    echo=DEBUG,
    echo_pool=DEBUG,
    **SYNC_POOL_SETTINGS
)oling avançado
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from app.config import settings
import logging

logger = logging.getLogger(__name__)

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

# Configurações específicas do PostgreSQL para performance
POSTGRES_CONNECT_ARGS = {
    "command_timeout": 60,
    "server_settings": {
        "jit": "off",  # Desabilita JIT para queries simples (melhora latência)
        "application_name": "whatsapp_agent_optimized",
        "tcp_keepalives_idle": "600",
        "tcp_keepalives_interval": "30",
        "tcp_keepalives_count": "3",
    }
}

# Engine assíncrono otimizado
# Engines - aqui que a mágica acontece! 🎭
engine = create_async_engine(
    DATABASE_URL_ASYNC,
    echo=DEBUG,
    echo_pool=DEBUG,
    **ASYNC_POOL_SETTINGS
)

# Engine síncrono otimizado
sync_database_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')
sync_engine = create_engine(
    sync_database_url,
    echo=settings.debug,
    connect_args=POSTGRES_CONNECT_ARGS,
    **POOL_SETTINGS
)

# Session makers otimizados
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False  # Controle manual do flush para performance
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False
)

# Eventos para monitoramento de conexões
@event.listens_for(sync_engine, "connect")
def set_postgresql_search_path(dbapi_connection, connection_record):
    """Otimizações específicas do PostgreSQL por conexão"""
    with dbapi_connection.cursor() as cursor:
        # Configurações de performance por sessão
        cursor.execute("SET statement_timeout = '30s'")
        cursor.execute("SET lock_timeout = '10s'")
        cursor.execute("SET idle_in_transaction_session_timeout = '30s'")
        cursor.execute("SET work_mem = '64MB'")
        cursor.execute("SET random_page_cost = 1.1")  # SSDs
        cursor.execute("SET effective_cache_size = '1GB'")

@event.listens_for(sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log quando uma conexão é retirada do pool"""
    logger.debug("Conexão retirada do pool")

@event.listens_for(sync_engine, "checkin") 
def receive_checkin(dbapi_connection, connection_record):
    """Log quando uma conexão retorna ao pool"""
    logger.debug("Conexão retornada ao pool")

async def get_db():
    """
    Dependency otimizada para sessão assíncrona do banco
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_db():
    """
    Dependency otimizada para sessão síncrona do banco
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

async def get_db_session():
    """
    Context manager para sessões assíncronas otimizadas
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_db_session():
    """
    Context manager para sessões síncronas otimizadas
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

async def init_db():
    """
    Inicializa o banco de dados criando as tabelas
    """
    from app.models.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Banco de dados inicializado (async)")

def init_sync_db():
    """
    Inicializa o banco de dados criando as tabelas (versão síncrona)
    """
    from app.models.database import Base
    Base.metadata.create_all(bind=sync_engine)
    logger.info("✅ Banco de dados inicializado (sync)")

async def get_pool_status():
    """
    Retorna status do pool de conexões
    """
    async_pool = engine.pool
    sync_pool = sync_engine.pool
    
    return {
        "async_pool": {
            "size": async_pool.size(),
            "checked_in": async_pool.checkedin(),
            "checked_out": async_pool.checkedout(),
            "overflow": async_pool.overflow(),
            "invalid": async_pool.invalidated(),
        },
        "sync_pool": {
            "size": sync_pool.size(),
            "checked_in": sync_pool.checkedin(), 
            "checked_out": sync_pool.checkedout(),
            "overflow": sync_pool.overflow(),
            "invalid": sync_pool.invalidated(),
        },
        "config": ASYNC_POOL_SETTINGS
    }

async def health_check_db():
    """
    Verifica saúde da conexão com o banco
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute("SELECT 1")
            return {"status": "healthy", "test_query": bool(result.scalar())}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Cleanup das conexões na finalização
async def close_db_connections():
    """
    Fecha todas as conexões do banco
    """
    await engine.dispose()
    sync_engine.dispose()
    logger.info("🔌 Conexões do banco fechadas")
