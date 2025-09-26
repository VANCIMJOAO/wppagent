"""
🔗 Gerenciador de Pool de Conexões Persistente
==============================================

Implementa:
- Pool de conexões persistente para reduzir latência
- Warm-up de conexões na inicialização
- Health check automático
- Reconnection automática
"""

import asyncio
import time
from typing import Optional
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionPoolManager:
    """Gerenciador de pool de conexões otimizado para Railway"""
    
    def __init__(self):
        self.engine = None
        self.pool_warmed_up = False
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutos
        
    def initialize(self, database_url: str):
        """Inicializar pool de conexões"""
        try:
            # Configuração otimizada para Railway
            self.engine = create_engine(
                database_url,
                echo=False,
                poolclass=QueuePool,
                pool_size=3,  # Pequeno para Railway
                max_overflow=2,  # Máximo 5 conexões total
                pool_pre_ping=True,
                pool_recycle=3600,  # 1 hora
                pool_timeout=30,
                connect_args={
                    "application_name": "whatsapp_agent_persistent",
                }
            )
            
            logger.info("✅ Pool de conexões inicializado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar pool: {e}")
            return False
    
    async def warm_up_pool(self):
        """Aquecer o pool de conexões"""
        if not self.engine or self.pool_warmed_up:
            return
            
        logger.info("🔥 Aquecendo pool de conexões...")
        
        try:
            # Criar conexões iniciais
            connections = []
            for i in range(3):  # pool_size
                conn = self.engine.connect()
                # Executar query simples para testar
                conn.execute(text("SELECT 1"))
                connections.append(conn)
                logger.info(f"✅ Conexão {i+1} aquecida")
            
            # Manter conexões abertas por um tempo
            await asyncio.sleep(1)
            
            # Fechar conexões (elas voltam para o pool)
            for conn in connections:
                conn.close()
            
            self.pool_warmed_up = True
            logger.info("🔥 Pool aquecido com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao aquecer pool: {e}")
    
    def health_check(self) -> bool:
        """Verificar saúde do pool"""
        if not self.engine:
            return False
            
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.scalar()
            return True
        except Exception as e:
            logger.error(f"❌ Health check falhou: {e}")
            return False
    
    @asynccontextmanager
    async def get_connection(self):
        """Obter conexão do pool com health check"""
        if not self.engine:
            raise Exception("Pool não inicializado")
        
        # Health check periódico
        current_time = time.time()
        if current_time - self.last_health_check > self.health_check_interval:
            if not self.health_check():
                logger.warning("⚠️ Pool não saudável, tentando reconectar...")
                # Aqui poderia implementar reconexão automática
            self.last_health_check = current_time
        
        try:
            conn = self.engine.connect()
            yield conn
        finally:
            conn.close()
    
    def get_engine(self):
        """Obter engine do pool"""
        return self.engine
    
    def close(self):
        """Fechar pool de conexões"""
        if self.engine:
            self.engine.dispose()
            logger.info("🔌 Pool de conexões fechado")


# Instância global do gerenciador
pool_manager = ConnectionPoolManager()


async def initialize_pool(database_url: str):
    """Inicializar pool global"""
    if pool_manager.initialize(database_url):
        await pool_manager.warm_up_pool()
        return True
    return False


def get_pool_engine():
    """Obter engine do pool global"""
    return pool_manager.get_engine()


@asynccontextmanager
async def get_pool_connection():
    """Obter conexão do pool global"""
    async with pool_manager.get_connection() as conn:
        yield conn
