"""
🔄 Serviços do Dashboard - REFATORADOS
=====================================

MUDANÇA CRÍTICA: Agora usa API REST ao invés de SQL direto.

Módulo para importar serviços refatorados facilmente.
Mantém compatibilidade com código existente.

Autor: Claude AI
Data: 2025-09-03
Status: 🔥 REFATORAÇÃO CRÍTICA
"""

# SERVIÇOS PRINCIPAIS - REFATORADOS PARA API REST
from .database import DatabaseService, get_db_service
from .api_service import APIService, sync_api

__all__ = [
    'DatabaseService', 'get_db_service',  # Compatibilidade
    'APIService', 'sync_api'              # Nova arquitetura
]
