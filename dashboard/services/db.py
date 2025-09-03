"""
Database Connection Service
==========================

Gerencia conexão com PostgreSQL do Railway usando pool de conexões.
Fornece engine SQLAlchemy e funções utilitárias para queries.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import asyncio
from datetime import datetime

import psycopg2
from psycopg2 import pool
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Serviço de conexão e operações com PostgreSQL.
    
    Features:
    - Pool de conexões para performance
    - Health check automático
    - Tratamento de erros
    - Queries parametrizadas
    - Suporte a transações
    """
    
    def __init__(self):
        # Força carregamento do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        self.database_url = os.getenv('DATABASE_URL')
        self.pool: Optional[pool.SimpleConnectionPool] = None
        self.engine = None
        self.SessionLocal = None
        
        if not self.database_url:
            raise ValueError("❌ DATABASE_URL não encontrada! Verifique o arquivo .env")
        
        print(f"🔗 Conectando ao Railway PostgreSQL: {self.database_url[:30]}...")
        self._initialize_connections()
    
    def _build_default_url(self) -> str:
        """Constrói URL de desenvolvimento se não houver DATABASE_URL"""
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'postgres')
        database = os.getenv('DB_NAME', 'wppagent')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _initialize_connections(self):
        """Inicializa pool de conexões e engine SQLAlchemy"""
        try:
            # Engine SQLAlchemy (para queries complexas e ORM)
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Validação automática de conexões
                pool_recycle=3600,   # Recicla conexões a cada hora
                echo=False  # True para debug SQL
            )
            
            # Session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Pool de conexões psycopg2 (para operações rápidas) - opcional
            try:
                self.pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=20,
                    dsn=self.database_url
                )
            except Exception as pool_error:
                logger.warning(f"Pool psycopg2 não disponível: {pool_error}")
                self.pool = None
            
            logger.info("✅ Conexão com banco de dados REAL inicializada com sucesso")
            
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO ao conectar ao banco: {e}")
            raise ConnectionError(f"Não foi possível conectar ao banco Railway: {e}")
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexão psycopg2"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro na conexão: {e}")
            raise
        finally:
            if conn:
                self.pool.putconn(conn)
    
    @contextmanager
    def get_session(self):
        """Context manager para sessão SQLAlchemy"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Erro na sessão: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Executa query SELECT e retorna resultados como lista de dicts.
        
        Args:
            query: SQL query com placeholders nomeados (:param)
            params: Dicionário com valores dos parâmetros
            
        Returns:
            Lista de dicionários com resultados
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                
                # Verifica se é uma query que retorna dados (SELECT, INSERT...RETURNING)
                if result.returns_rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in result.fetchall()]
                else:
                    # Para UPDATE, DELETE, etc que não retornam dados
                    return []
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao executar query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return []
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return []
    
    def execute_non_query(self, query: str, params: Dict[str, Any] = None) -> bool:
        """
        Executa query que não retorna dados (UPDATE, DELETE, INSERT sem RETURNING).
        
        Args:
            query: SQL query com placeholders nomeados (:param)
            params: Dicionário com valores dos parâmetros
            
        Returns:
            True se executou com sucesso, False caso contrário
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                # Para queries UPDATE/DELETE, podemos verificar rowcount
                return result.rowcount >= 0  # Retorna True mesmo se 0 linhas afetadas
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao executar non-query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            return False

    def execute_query_df(self, query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Executa query e retorna resultado como DataFrame pandas.
        Útil para análises e visualizações.
        """
        try:
            return pd.read_sql_query(query, self.engine, params=params)
        except Exception as e:
            logger.error(f"Erro ao executar query para DataFrame: {e}")
            return pd.DataFrame()
    
    def execute_scalar(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Executa query que retorna um único valor.
        Útil para COUNTs, SUMs, etc.
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                return result.scalar()
        except Exception as e:
            logger.error(f"Erro ao executar scalar query: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saúde da conexão com o banco.
        
        Returns:
            Dict com status da conexão
        """
        try:
            start_time = datetime.now()
            
            # Testa conexão simples
            result = self.execute_scalar("SELECT 1 as test")
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if result == 1:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "timestamp": datetime.now().isoformat(),
                    "pool_info": {
                        "pool_size": self.pool.minconn if self.pool else 0,
                        "max_pool": self.pool.maxconn if self.pool else 0
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Query test failed",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Retorna informações sobre uma tabela específica.
        Útil para debugging e validação.
        """
        try:
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
            
            columns = self.execute_query(query, {"table_name": table_name})
            
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            total_rows = self.execute_scalar(count_query)
            
            return {
                "table_name": table_name,
                "columns": columns,
                "total_rows": total_rows,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter info da tabela {table_name}: {e}")
            return {"error": str(e)}
    
    def close_connections(self):
        """Fecha todas as conexões"""
        try:
            if self.pool:
                self.pool.closeall()
            if self.engine:
                self.engine.dispose()
            logger.info("Conexões fechadas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao fechar conexões: {e}")

# Instância global do serviço
db_service = DatabaseService()

# Funções de conveniência para importação direta
def get_db_connection():
    """Retorna context manager para conexão"""
    return db_service.get_connection()

def get_db_session():
    """Retorna context manager para sessão SQLAlchemy"""
    return db_service.get_session()

def execute_non_query(query: str, params: Dict[str, Any] = None) -> bool:
    """Executa query que não retorna dados (UPDATE, DELETE, INSERT sem RETURNING)"""
    return db_service.execute_non_query(query, params)

def execute_query(query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Executa query e retorna resultados"""
    return db_service.execute_query(query, params)

def execute_query_df(query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
    """Executa query e retorna DataFrame"""
    return db_service.execute_query_df(query, params)

def execute_scalar(query: str, params: Dict[str, Any] = None) -> Any:
    """Executa scalar query"""
    return db_service.execute_scalar(query, params)

def db_health_check() -> Dict[str, Any]:
    """Verifica saúde do banco"""
    return db_service.health_check()
