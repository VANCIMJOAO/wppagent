"""
🔄 Database Service - REFATORADO para usar API REST
==================================================

MUDANÇA CRÍTICA: Este serviço agora usa APIService ao invés de SQL direto.

❌ ANTES: Conexão direta PostgreSQL + psycopg2
✅ AGORA: Chamadas REST autenticadas via APIService

Mantém compatibilidade com callbacks existentes.

Autor: Claude AI
Data: 2025-09-03
Status: 🔥 REFATORAÇÃO CRÍTICA - CORREÇÃO DE ARQUITETURA
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

# MUDANÇA CRÍTICA: Importa do database_service refatorado
try:
    # Importa a versão refatorada que usa API
    from .database_service import DatabaseService as RefactoredDatabaseService, get_db_service
    
    # Usa a versão refatorada
    DatabaseService = RefactoredDatabaseService
    
except ImportError as e:
    print(f"⚠️  Import relativo falhou: {e}")
    try:
        # Tenta import absoluto
        import database_service
        DatabaseService = database_service.DatabaseService
        get_db_service = database_service.get_db_service
    except ImportError as e2:
        print(f"⚠️  Import absoluto também falhou: {e2}")
        
        # Fallback: classe básica compatível
        class DatabaseService:
            def __init__(self):
                print("⚠️  DatabaseService em modo fallback - usando dados mock")
                self.engine = None  # Para compatibilidade
                
                # Tenta importar APIService diretamente
                try:
                    from api_service import sync_api
                    self.api = sync_api
                    print("✅ APIService carregado no fallback")
                except ImportError:
                    print("❌ APIService não disponível no fallback")
                    self.api = None
            
            def get_conversations(self):
                if self.api:
                    return self.api.get_conversations()
                return []
            
            def get_conversation_messages(self, conv_id):
                if self.api:
                    return self.api.get_conversation_messages(conv_id)
                return []
                
            def test_connection(self):
                return self.api is not None
        
        def get_db_service():
            return DatabaseService()

# Mantém compatibilidade com imports existentes
__all__ = ['DatabaseService', 'get_db_service']
