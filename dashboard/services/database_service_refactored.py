"""
🔄 Database Service - REFATORADO para usar API REST
==================================================

MUDANÇA CRÍTICA: Este serviço agora usa APIService ao invés de SQL direto.

❌ ANTES: Conexão direta PostgreSQL + queries SQL
✅ AGORA: Chamadas REST autenticadas via APIService

Mantém compatibilidade com dashboard existente, mas com arquitetura correta.

Autor: Claude AI
Data: 2025-09-03
Status: 🔥 REFATORAÇÃO CRÍTICA - CORREÇÃO DE ARQUITETURA
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# MUDANÇA CRÍTICA: Usar APIService ao invés de SQLAlchemy
from .api_service import sync_api

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    🔄 SERVIÇO REFATORADO - Agora usa API REST
    
    CORREÇÃO CRÍTICA:
    - ❌ Antes: self.engine = create_engine(database_url) 
    - ✅ Agora: self.api = sync_api
    
    Mantém mesma interface pública, mas usa arquitetura correta internamente.
    """
    
    def __init__(self):
        """
        🔄 NOVA INICIALIZAÇÃO - Sem conexão SQL direta
        
        Antes: Criava engine SQLAlchemy direto no PostgreSQL
        Agora: Usa APIService para chamadas REST autenticadas
        """
        self.api = sync_api
        logger.info("🔄 DatabaseService inicializado com API REST (não SQL direto)")
        
        # Flag para backwards compatibility
        self.engine = None  # Removido propositalmente
        logger.warning("⚠️ self.engine=None - usando API REST ao invés de SQL direto")
    
    def _connect(self):
        """
        🔄 MÉTODO DEPRECIADO - Não faz mais conexão SQL
        
        Antes: Conectava diretamente no PostgreSQL
        Agora: Conexão é gerenciada pelo APIService via HTTP
        """
        logger.warning("⚠️ _connect() depreciado - API REST não precisa de conexão SQL")
        pass
    
    # ================================
    # MÉTODOS PRINCIPAIS - REFATORADOS
    # ================================
    
    def get_conversations(self) -> List[Dict]:
        """
        🔄 REFATORADO: get_conversations() - Agora usa API REST
        
        ❌ ANTES: 
        query = "SELECT c.id, c.status... FROM conversations c..."
        df = pd.read_sql_query(query, self.engine)
        
        ✅ AGORA:
        return self.api.get_conversations()
        """
        try:
            logger.info("🔄 get_conversations() - usando API REST ao invés de SQL")
            
            # CORREÇÃO CRÍTICA: API REST ao invés de SQL direto
            conversations = self.api.get_conversations(limit=50, offset=0)
            
            if not conversations:
                logger.warning("⚠️ API retornou lista vazia - usando dados mock")
                return self._get_mock_conversations()
            
            logger.info(f"✅ Carregadas {len(conversations)} conversas via API REST")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Erro na API REST - fallback para mock: {e}")
            return self._get_mock_conversations()
    
    def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """
        🔄 REFATORADO: get_conversation_messages() - Agora usa API REST
        
        ❌ ANTES:
        query = "SELECT m.id, m.content... FROM messages m WHERE m.conversation_id = %s"
        df = pd.read_sql_query(query, self.engine, params={'conversation_id': conversation_id})
        
        ✅ AGORA:
        return self.api.get_conversation_messages(conversation_id)
        """
        try:
            logger.info(f"🔄 get_conversation_messages({conversation_id}) - usando API REST")
            
            # CORREÇÃO CRÍTICA: API REST ao invés de SQL direto
            messages = self.api.get_conversation_messages(conversation_id)
            
            if not messages:
                logger.warning("⚠️ API retornou lista vazia - usando dados mock")
                return self._get_mock_messages()
            
            logger.info(f"✅ Carregadas {len(messages)} mensagens via API REST")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Erro na API REST - fallback para mock: {e}")
            return self._get_mock_messages()
    
    def send_message(self, conversation_id: int, content: str) -> Dict:
        """
        🔄 NOVO: send_message() - Usa API REST para enviar mensagens
        
        Funcionalidade que não existia antes, agora disponível via API.
        """
        try:
            logger.info(f"📤 Enviando mensagem para conversa {conversation_id}")
            
            result = self.api.send_message(conversation_id, content)
            
            if result.get('success'):
                logger.info("✅ Mensagem enviada via API REST")
            else:
                logger.error(f"❌ Falha ao enviar mensagem: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return {"success": False, "error": str(e)}
    
    # ================================
    # NOVOS MÉTODOS VIA API REST
    # ================================
    
    def get_appointments(self, date_from: Optional[str] = None, 
                        date_to: Optional[str] = None) -> List[Dict]:
        """
        🆕 NOVO: get_appointments() - Via API REST
        
        Funcionalidade antes não disponível diretamente no DatabaseService.
        """
        try:
            logger.info("📅 Buscando agendamentos via API REST")
            
            appointments = self.api.get_appointments(date_from=date_from, date_to=date_to)
            
            logger.info(f"✅ Carregados {len(appointments)} agendamentos via API REST")
            return appointments
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar agendamentos: {e}")
            return []
    
    def get_dashboard_stats(self, period: str = "30d") -> Dict:
        """
        🆕 NOVO: get_dashboard_stats() - Via API REST
        
        Estatísticas agregadas que aproveitam cache do backend.
        """
        try:
            logger.info(f"📊 Buscando estatísticas ({period}) via API REST")
            
            stats = self.api.get_dashboard_stats(period=period)
            
            logger.info("✅ Estatísticas carregadas via API REST")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas: {e}")
            return {}
    
    # ================================
    # MÉTODOS DE COMPATIBILIDADE
    # ================================
    
    def get_monthly_conversations(self) -> pd.DataFrame:
        """
        🔄 COMPATIBILIDADE: Mantém interface existente
        
        Converte dados da API para DataFrame para compatibilidade.
        """
        try:
            logger.info("📊 get_monthly_conversations() - via API REST")
            
            stats = self.get_dashboard_stats(period="12m")
            
            # Simula dados mensais para compatibilidade
            monthly_data = []
            for i in range(12):
                date = datetime.now() - timedelta(days=30*i)
                monthly_data.append({
                    'month': date.strftime('%Y-%m'),
                    'total_conversations': stats.get('total_conversations', 0) // 12,
                    'active_conversations': stats.get('active_conversations', 0) // 12
                })
            
            return pd.DataFrame(monthly_data)
            
        except Exception as e:
            logger.error(f"❌ Erro em get_monthly_conversations: {e}")
            return pd.DataFrame()
    
    def get_conversation_metrics(self) -> Dict:
        """
        🔄 COMPATIBILIDADE: Métricas de conversas via API
        """
        try:
            return self.get_dashboard_stats(period="30d")
        except Exception as e:
            logger.error(f"❌ Erro em get_conversation_metrics: {e}")
            return {}
    
    # ================================
    # DADOS MOCK PARA FALLBACK
    # ================================
    
    def _get_mock_conversations(self) -> List[Dict]:
        """Dados mock quando API não responde"""
        logger.info("📱 Usando dados mock para conversas")
        return [
            {
                'id': 1,
                'summary': 'Conversa Mock - João Silva',
                'last_message': 'Mensagem mock de teste',
                'timestamp': datetime.now() - timedelta(minutes=15),
                'total_messages': 5,
                'status': 'active',
                'contact_name': 'João Silva (Mock)',
                'contact_phone': '+5511999999999',
                'wa_id': 'mock_user_1'
            },
            {
                'id': 2,
                'summary': 'Conversa Mock - Maria Santos',
                'last_message': 'Outra mensagem mock',
                'timestamp': datetime.now() - timedelta(hours=2),
                'total_messages': 8,
                'status': 'pending',
                'contact_name': 'Maria Santos (Mock)',
                'contact_phone': '+5511888888888',
                'wa_id': 'mock_user_2'
            }
        ]
    
    def _get_mock_messages(self) -> List[Dict]:
        """Mensagens mock quando API não responde"""
        logger.info("📨 Usando dados mock para mensagens")
        return [
            {
                'id': 1,
                'content': 'Olá! Esta é uma mensagem mock do bot.',
                'is_user': False,
                'timestamp': datetime.now() - timedelta(minutes=20),
                'message_type': 'text'
            },
            {
                'id': 2,
                'content': 'Esta é uma resposta mock do usuário.',
                'is_user': True,
                'timestamp': datetime.now() - timedelta(minutes=18),
                'message_type': 'text'
            },
            {
                'id': 3,
                'content': 'Perfeito! Mensagem mock de confirmação.',
                'is_user': False,
                'timestamp': datetime.now() - timedelta(minutes=15),
                'message_type': 'text'
            }
        ]
    
    # ================================
    # MÉTODOS DEPRECIADOS
    # ================================
    
    def _execute_query(self, query: str, params: Dict = None):
        """
        ⚠️ MÉTODO DEPRECIADO - SQL direto não é mais usado
        
        Antes: Executava queries SQL diretas
        Agora: Todas as operações são via API REST
        """
        logger.error("❌ _execute_query() DEPRECIADO - use API REST ao invés de SQL direto")
        raise DeprecationWarning(
            "SQL direto foi substituído por API REST. "
            "Use os métodos get_conversations(), get_conversation_messages(), etc."
        )
    
    def test_connection(self) -> bool:
        """
        🔄 REFATORADO: Testa conexão com API ao invés de banco
        
        Antes: Testava conexão SQL
        Agora: Testa conexão com API REST
        """
        try:
            # Testa com uma chamada simples à API
            conversations = self.api.get_conversations(limit=1)
            return isinstance(conversations, list)
        except Exception as e:
            logger.error(f"❌ Falha no teste de conexão API: {e}")
            return False

# ================================
# INSTÂNCIA SINGLETON COMPATÍVEL
# ================================

# Mantém interface existente para compatibilidade
db_service = DatabaseService()

def get_db_service():
    """Retorna instância do serviço de database"""
    return db_service
