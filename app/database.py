"""
Configuração do banco de dados
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
# Configurar DATABASE_URL com fallback
database_url = os.getenv('DATABASE_URL')
if not database_url:
    # Construir URL a partir de variáveis individuais
    db_host = os.getenv('PGHOST', 'localhost')
    db_port = os.getenv('PGPORT', '5432')
    db_name = os.getenv('PGDATABASE', 'whatsapp_agent')
    db_user = os.getenv('PGUSER', 'postgres')
    db_pass = os.getenv('PGPASSWORD', '')
    database_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
else:
    # Garantir que usa asyncpg
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    elif database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)

# Log da URL de conexão (sem senha)
connection_info = database_url.split('@')[0] if '@' in database_url else 'Invalid URL'
logger.info(f"Tentando conectar ao banco: {connection_info}@***")

# Debug adicional
logger.info(f"PGHOST: {os.getenv('PGHOST', 'NOT_SET')}")
logger.info(f"PGPORT: {os.getenv('PGPORT', 'NOT_SET')}")
logger.info(f"PGDATABASE: {os.getenv('PGDATABASE', 'NOT_SET')}")
logger.info(f"DATABASE_URL presente: {'Sim' if os.getenv('DATABASE_URL') else 'Não'}")

# Engine assíncrono
engine = create_async_engine(
    database_url,
    echo=False,  # Reduzir logs em produção
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)

# Engine síncrono (para dashboard e outras operações síncronas)
sync_database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://').replace('+asyncpg', '')
sync_engine = create_engine(
    sync_database_url,
    echo=False,  # Reduzir logs em produção
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
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
    try:
        from app.models.database import Base
        # Teste de conectividade primeiro
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info("✅ Conexão com banco de dados estabelecida")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Tabelas criadas/verificadas")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar banco: {e}")
        logger.error(f"❌ Tipo do erro: {type(e).__name__}")
        # Re-raise para falhar o startup se necessário
        raise


def init_sync_db():
    """
    Inicializa o banco de dados criando as tabelas (versão síncrona)
    """
    from app.models.database import Base
    Base.metadata.create_all(bind=sync_engine)
