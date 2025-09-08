"""
Migração do banco para Sistema RBAC
Adiciona tabelas necessárias para controle de acesso
"""
import asyncio
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from app.database import database_url
from app.models.rbac import Base
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def create_rbac_tables():
    """Criar tabelas RBAC no banco de dados"""
    try:
        # Criar engine síncrono para Alembic
        engine = create_engine(database_url.replace("asyncpg", "psycopg2"))
        
        # Criar todas as tabelas RBAC
        Base.metadata.create_all(engine)
        
        logger.info("✅ Tabelas RBAC criadas com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas RBAC: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(create_rbac_tables())
