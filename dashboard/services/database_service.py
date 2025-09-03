"""
Serviço de database para conectar ao PostgreSQL da Railway
e buscar dados reais das conversas e mensagens
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        """Inicializa conexão com o banco PostgreSQL da Railway"""
        self.engine = None
        self._connect()
    
    def _connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            # Buscar DATABASE_URL do environment
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                # Construir URL a partir de variáveis individuais
                db_host = os.getenv('PGHOST', 'localhost')
                db_port = os.getenv('PGPORT', '5432')
                db_name = os.getenv('PGDATABASE', 'railway')
                db_user = os.getenv('PGUSER', 'postgres')
                db_pass = os.getenv('PGPASSWORD', '')
                database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
            
            # Garantir que usa o driver psycopg2 para conexões síncronas
            if database_url.startswith('postgresql+asyncpg://'):
                database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
            elif database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://')
            
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Testar conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("✅ Conexão com PostgreSQL estabelecida")
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com PostgreSQL: {e}")
            self.engine = None
    
    def get_conversations(self) -> List[Dict]:
        """Busca conversas reais do banco de dados"""
        try:
            if not self.engine:
                logger.warning("Sem conexão com banco - retornando dados mock")
                return self._get_mock_conversations()
            
            query = """
            SELECT 
                c.id,
                c.status,
                c.last_message_at,
                c.created_at,
                u.nome as contact_name,
                u.telefone as contact_phone,
                u.wa_id,
                COUNT(m.id) as total_messages,
                MAX(m.content) as last_message_content
            FROM conversations c
            LEFT JOIN users u ON c.user_id = u.id
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.status != 'closed'
            GROUP BY c.id, c.status, c.last_message_at, c.created_at, u.nome, u.telefone, u.wa_id
            ORDER BY c.last_message_at DESC
            LIMIT 50
            """
            
            df = pd.read_sql_query(query, self.engine)
            
            conversations = []
            for _, row in df.iterrows():
                contact_name = row['contact_name'] or f"Usuário {row['wa_id'] or 'Anônimo'}"
                
                # Criar resumo da conversa
                summary = f"Conversa com {contact_name}"
                if row['contact_phone']:
                    summary += f" ({row['contact_phone']})"
                
                conversations.append({
                    'id': row['id'],
                    'summary': summary,
                    'last_message': row['last_message_content'] or "Sem mensagens",
                    'timestamp': pd.to_datetime(row['last_message_at']) if row['last_message_at'] else pd.to_datetime(row['created_at']),
                    'total_messages': int(row['total_messages']) if row['total_messages'] else 0,
                    'status': row['status'],
                    'contact_name': contact_name,
                    'contact_phone': row['contact_phone'],
                    'wa_id': row['wa_id']
                })
            
            logger.info(f"✅ Carregadas {len(conversations)} conversas do banco")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar conversas: {e}")
            return self._get_mock_conversations()
    
    def get_conversation_messages(self, conversation_id: int) -> List[Dict]:
        """Busca mensagens reais de uma conversa específica"""
        try:
            if not self.engine:
                logger.warning("Sem conexão com banco - retornando dados mock")
                return self._get_mock_messages()
            
            query = """
            SELECT 
                m.id,
                m.content,
                m.direction,
                m.message_type,
                m.created_at,
                u.nome as user_name,
                u.telefone as user_phone
            FROM messages m
            LEFT JOIN users u ON m.user_id = u.id
            WHERE m.conversation_id = %(conversation_id)s
            ORDER BY m.created_at ASC
            """
            
            df = pd.read_sql_query(query, self.engine, params={'conversation_id': conversation_id})
            
            messages = []
            for _, row in df.iterrows():
                # 'in' = mensagem recebida (do usuário), 'out' = mensagem enviada (bot/sistema)
                is_user = row['direction'] == 'in'
                
                messages.append({
                    'id': row['id'],
                    'content': row['content'] or '[Mensagem sem conteúdo]',
                    'is_user': is_user,
                    'timestamp': pd.to_datetime(row['created_at']),
                    'message_type': row['message_type'],
                    'user_name': row['user_name'],
                    'user_phone': row['user_phone']
                })
            
            logger.info(f"✅ Carregadas {len(messages)} mensagens da conversa {conversation_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar mensagens da conversa {conversation_id}: {e}")
            return self._get_mock_messages()
    
    def get_conversation_stats(self) -> Dict:
        """Busca estatísticas das conversas"""
        try:
            if not self.engine:
                return self._get_mock_stats()
            
            query = """
            SELECT 
                COUNT(DISTINCT c.id) as total_conversations,
                COUNT(DISTINCT m.id) as total_messages,
                COUNT(DISTINCT u.id) as unique_users,
                COUNT(DISTINCT DATE(c.created_at)) as active_days,
                COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) as active_conversations,
                COUNT(DISTINCT CASE WHEN c.status = 'human' THEN c.id END) as human_conversations
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            LEFT JOIN users u ON c.user_id = u.id
            WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days'
            """
            
            result = pd.read_sql_query(query, self.engine).iloc[0]
            
            return {
                'total_conversations': int(result['total_conversations']),
                'total_messages': int(result['total_messages']),
                'unique_users': int(result['unique_users']),
                'active_days': int(result['active_days']),
                'active_conversations': int(result['active_conversations']),
                'human_conversations': int(result['human_conversations'])
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas: {e}")
            return self._get_mock_stats()
    
    def search_conversations(self, search_term: str) -> List[Dict]:
        """Busca conversas por termo de pesquisa"""
        try:
            if not self.engine:
                return []
            
            query = """
            SELECT DISTINCT
                c.id,
                c.status,
                c.last_message_at,
                c.created_at,
                u.nome as contact_name,
                u.telefone as contact_phone,
                u.wa_id,
                COUNT(m.id) as total_messages,
                MAX(m.content) as last_message_content
            FROM conversations c
            LEFT JOIN users u ON c.user_id = u.id
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE (
                LOWER(u.nome) LIKE LOWER(%(search_term)s) OR
                LOWER(u.telefone) LIKE LOWER(%(search_term)s) OR
                LOWER(m.content) LIKE LOWER(%(search_term)s)
            ) AND c.status != 'closed'
            GROUP BY c.id, c.status, c.last_message_at, c.created_at, u.nome, u.telefone, u.wa_id
            ORDER BY c.last_message_at DESC
            LIMIT 20
            """
            
            search_pattern = f"%{search_term}%"
            df = pd.read_sql_query(query, self.engine, params={'search_term': search_pattern})
            
            conversations = []
            for _, row in df.iterrows():
                contact_name = row['contact_name'] or f"Usuário {row['wa_id'] or 'Anônimo'}"
                
                conversations.append({
                    'id': row['id'],
                    'summary': f"Conversa com {contact_name}",
                    'last_message': row['last_message_content'] or "Sem mensagens",
                    'timestamp': pd.to_datetime(row['last_message_at']) if row['last_message_at'] else pd.to_datetime(row['created_at']),
                    'total_messages': int(row['total_messages']) if row['total_messages'] else 0,
                    'status': row['status'],
                    'contact_name': contact_name,
                    'contact_phone': row['contact_phone']
                })
            
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar conversas: {e}")
            return []
    
    def _get_mock_conversations(self) -> List[Dict]:
        """Retorna dados mock quando não há conexão com o banco"""
        return [
            {
                'id': 1,
                'summary': 'Conversa com João Silva (11999999999)',
                'last_message': 'Obrigado pelo atendimento!',
                'timestamp': datetime.now() - timedelta(minutes=30),
                'total_messages': 12,
                'status': 'active',
                'contact_name': 'João Silva',
                'contact_phone': '11999999999'
            },
            {
                'id': 2,
                'summary': 'Conversa com Maria Santos (11888888888)',
                'last_message': 'Gostaria de agendar um horário',
                'timestamp': datetime.now() - timedelta(hours=2),
                'total_messages': 8,
                'status': 'active',
                'contact_name': 'Maria Santos',
                'contact_phone': '11888888888'
            },
            {
                'id': 3,
                'summary': 'Conversa com Pedro Costa (11777777777)',
                'last_message': 'Qual o valor do serviço?',
                'timestamp': datetime.now() - timedelta(hours=5),
                'total_messages': 4,
                'status': 'human',
                'contact_name': 'Pedro Costa',
                'contact_phone': '11777777777'
            }
        ]
    
    def _get_mock_messages(self) -> List[Dict]:
        """Retorna mensagens mock quando não há conexão com o banco"""
        return [
            {
                'id': 1,
                'content': 'Olá! Como posso ajudá-lo hoje?',
                'is_user': False,
                'timestamp': datetime.now() - timedelta(minutes=30),
                'message_type': 'text'
            },
            {
                'id': 2,
                'content': 'Gostaria de saber mais sobre seus serviços',
                'is_user': True,
                'timestamp': datetime.now() - timedelta(minutes=25),
                'message_type': 'text'
            },
            {
                'id': 3,
                'content': 'Claro! Oferecemos diversos serviços. Qual seria do seu interesse?',
                'is_user': False,
                'timestamp': datetime.now() - timedelta(minutes=20),
                'message_type': 'text'
            }
        ]
    
    def _get_mock_stats(self) -> Dict:
        """Retorna estatísticas mock quando não há conexão com o banco"""
        return {
            'total_conversations': 25,
            'total_messages': 180,
            'unique_users': 18,
            'active_days': 15,
            'active_conversations': 12,
            'human_conversations': 3
        }

# Instância global do serviço
db_service = DatabaseService()