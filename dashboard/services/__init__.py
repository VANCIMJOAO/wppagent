"""
Serviços do Dashboard
===================

Módulo para importar serviços facilmente.
"""

from .database import DatabaseService, get_db_service

__all__ = ['DatabaseService', 'get_db_service']
