"""
Configuração do banco de dados
"""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
# Configurar DATABASE_URL com fallback
database_url = os.getenv("DATABASE_URL")
if not database_url:
    # Construir URL a partir de variáveis individuais
    db_host = os.getenv("PGHOST", "localhost")
    db_port = os.getenv("PGPORT", "5432")
    db_name = os.getenv("PGDATABASE", "whatsapp_agent")
    db_user = os.getenv("PGUSER", "postgres")
    db_pass = os.getenv("PGPASSWORD", "")
    database_url = (
        f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )
else:
    # Para Railway, usar URL diretamente com +asyncpg
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Log da URL de conexão (sem senha)
connection_info = database_url.split("@")[0] if "@" in database_url else "Invalid URL"
logger.info(f"Tentando conectar ao banco: {connection_info}@***")

# Debug adicional
logger.info(f"PGHOST: {os.getenv('PGHOST', 'NOT_SET')}")
logger.info(f"PGPORT: {os.getenv('PGPORT', 'NOT_SET')}")
logger.info(f"PGDATABASE: {os.getenv('PGDATABASE', 'NOT_SET')}")
logger.info(f"DATABASE_URL presente: {'Sim' if os.getenv('DATABASE_URL') else 'Não'}")

# Engine assíncrono otimizado para performance
engine = create_async_engine(
    database_url,
    echo=False,  # Reduzir logs em produção
    pool_pre_ping=True,
    pool_recycle=1800,  # Reduzir para 30 minutos
    pool_size=10,  # Aumentar pool size
    max_overflow=20,  # Aumentar overflow
    pool_timeout=30,  # Timeout de conexão
    connect_args={
        "command_timeout": 30,  # Timeout de comando
        "server_settings": {
            "application_name": "whats_agent",
            "jit": "off",  # Desabilitar JIT para queries simples
        }
    }
)

# Engine síncrono otimizado (para dashboard e outras operações síncronas)
sync_database_url = database_url.replace(
    "postgresql+asyncpg://", "postgresql://"
).replace("+asyncpg", "")
sync_engine = create_engine(
    sync_database_url,
    echo=False,  # Reduzir logs em produção
    pool_pre_ping=True,
    pool_recycle=1800,  # Reduzir para 30 minutos
    pool_size=10,  # Aumentar pool size
    max_overflow=20,  # Aumentar overflow
    pool_timeout=30,  # Timeout de conexão
    connect_args={
        "command_timeout": 30,  # Timeout de comando
        "application_name": "whats_agent_sync",
    }
)

# Session maker assíncrono
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Session maker síncrono
SessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)


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
    Inicializa o banco de dados criando as tabelas e admin inicial
    """
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            from app.models.database import Base

            # Teste de conectividade primeiro
            logger.info(
                f"🔄 Tentativa {retry_count + 1}/{max_retries} - Conectando ao banco..."
            )

            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version_info = result.scalar()
                logger.info(
                    f"✅ Conexão estabelecida - PostgreSQL: {version_info[:50]}..."
                )

                # Criar tabelas
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Tabelas criadas/verificadas")

            # Criar admin inicial se não existir
            await create_initial_admin()
            logger.info("✅ Banco de dados inicializado com sucesso")
            return

        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Erro na tentativa {retry_count}: {e}")
            logger.error(f"❌ Tipo do erro: {type(e).__name__}")

            if retry_count >= max_retries:
                logger.error("❌ Falha definitiva na inicialização do banco")
                # Em produção, pode ser melhor continuar sem banco
                if os.getenv("SKIP_DB_INIT_ON_ERROR", "false").lower() == "true":
                    logger.warning(
                        "⚠️  Continuando sem inicialização do banco (SKIP_DB_INIT_ON_ERROR=true)"
                    )
                    return
                else:
                    raise
            else:
                import asyncio

                logger.info(f"⏳ Aguardando 2 segundos antes da próxima tentativa...")
                await asyncio.sleep(2)


async def create_initial_admin():
    """
    Cria o admin inicial se não existir
    """
    try:
        # Verificar se as variáveis de admin estão configuradas
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if not admin_password:
            logger.warning(
                "⚠️ ADMIN_PASSWORD não configurada - pulando criação do admin inicial"
            )
            return

        from passlib.context import CryptContext
        from sqlalchemy import select

        from app.models.database import AdminUser

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        async with AsyncSessionLocal() as session:
            # Verificar se já existe admin
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == admin_username)
            )
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                logger.info(f"✅ Admin '{admin_username}' já existe")
                return

            # Criar novo admin
            admin_user = AdminUser(
                username=admin_username,
                email=f"{admin_username}@sistema.local",
                password_hash=pwd_context.hash(admin_password),
                full_name="Administrador",
                is_active=True,
                is_super_admin=True,
            )

            session.add(admin_user)
            await session.commit()

            logger.info(f"✅ Admin inicial criado: {admin_username}")

    except Exception as e:
        logger.error(f"❌ Erro ao criar admin inicial: {e}")
        # Não re-raise para não falhar a inicialização se admin der erro


def init_sync_db():
    """
    Inicializa o banco de dados criando as tabelas (versão síncrona)
    """
    from app.models.database import Base

    Base.metadata.create_all(bind=sync_engine)
