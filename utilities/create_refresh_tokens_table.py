"""
Script para criar tabela RefreshToken
"""

from sqlalchemy import create_engine
from app.models.database import Base
from app.config import settings
import os

# Usar engine síncrono para criar tabelas
database_url = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
if database_url.startswith('postgresql'):
    database_url = database_url.replace('postgresql+asyncpg', 'postgresql')

engine = create_engine(database_url)

print(f"Conectando ao banco: {database_url}")
print('Criando tabela refresh_tokens...')

# Criar apenas a tabela RefreshToken
Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables.get('refresh_tokens')])

print('✅ Tabela refresh_tokens criada com sucesso!')
