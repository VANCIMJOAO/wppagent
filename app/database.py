"""
Configuração do banco de dados
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
# Engine assíncrono
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Engine síncrono (para dashboard e outras operações síncronas)
sync_database_url = settings.database_url.replace('postgresql+asyncpg://', 'postgresql://')
sync_engine = create_engine(
    sync_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Session maker assíncrono
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Session maker síncrono
SessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False
)


async def get_db():
    """
    Dependency para obter sessão do banco de dados (assíncrona)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    """
    Dependency para obter sessão do banco de dados (síncrona)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """
    Inicializa o banco de dados criando as tabelas
    """
    from app.models.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_sync_db():
    """
    Inicializa o banco de dados criando as tabelas (versão síncrona)
    """
    from app.models.database import Base
    Base.metadata.create_all(bind=sync_engine)
