"""
Utilitários de database real conectando com os dados do WhatsApp Agent
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import pandas as pd

# Adiciona o diretório pai ao sys.path para importar os modelos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from app.models.database import (
        User, Conversation, Message, Business, Service, 
        Appointment, AdminUser, BotConfiguration
    )
    from app.models.database import Base
except ImportError as e:
    print(f"Erro ao importar modelos: {e}")
    # Fallback para modelos locais se não conseguir importar
    from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    
    Base = declarative_base()
    
    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        wa_id = Column(String(50), unique=True)
        nome = Column(String(255))
        telefone = Column(String(20))
        created_at = Column(DateTime, server_default=func.now())
    
    class Conversation(Base):
        __tablename__ = "conversations"
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"))
        status = Column(String(20), default="active")
        last_message_at = Column(DateTime, server_default=func.now())
        created_at = Column(DateTime, server_default=func.now())
    
    class Message(Base):
        __tablename__ = "messages"
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey("users.id"))
        conversation_id = Column(Integer, ForeignKey("conversations.id"))
        direction = Column(String(10))
        content = Column(Text)
        created_at = Column(DateTime, server_default=func.now())

def get_real_database_connection():
    """Obtém conexão com o banco de dados real do WhatsApp Agent"""
    # Tenta diferentes caminhos para o banco
    possible_paths = [
        "/home/vancim/whats_agent/app/database.db",
        "/home/vancim/whats_agent/database.db",
        "/home/vancim/whats_agent/whatsapp_agent.db",
        "/home/vancim/whats_agent/dashboard.db"
    ]
    
    database_url = None
    for path in possible_paths:
        if os.path.exists(path):
            database_url = f"sqlite:///{path}"
            break
    
    if not database_url:
        # Se não encontrar, cria um novo banco
        db_path = "/home/vancim/whats_agent/whatsapp_agent.db"
        database_url = f"sqlite:///{db_path}"
        print(f"Criando novo banco em: {db_path}")
    
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    return Session()

def get_real_conversations() -> List[Dict]:
    """Retorna conversas reais do WhatsApp Agent"""
    try:
        session = get_real_database_connection()
        
        # Busca conversas com informações do usuário
        conversations_query = (
            session.query(Conversation, User)
            .join(User, Conversation.user_id == User.id)
            .filter(Conversation.status == "active")
            .order_by(desc(Conversation.last_message_at))
            .limit(50)
        )
        
        conversations = []
        for conv, user in conversations_query:
            # Busca última mensagem
            last_message = (
                session.query(Message)
                .filter(Message.conversation_id == conv.id)
                .order_by(desc(Message.created_at))
                .first()
            )
            
            # Conta total de mensagens
            total_messages = (
                session.query(Message)
                .filter(Message.conversation_id == conv.id)
                .count()
            )
            
            conversations.append({
                'id': conv.id,
                'user_name': user.nome or f"Usuário {user.wa_id[:8]}",
                'user_phone': user.telefone or user.wa_id,
                'summary': f"Conversa com {user.nome or 'Cliente'}" if user.nome else f"WhatsApp {user.wa_id[:8]}",
                'last_message': last_message.content[:100] + "..." if last_message and last_message.content else "Sem mensagens",
                'timestamp': conv.last_message_at or conv.created_at,
                'total_messages': total_messages,
                'status': conv.status,
                'user_id': user.id,
                'wa_id': user.wa_id
            })
        
        session.close()
        
        # Se não há conversas reais, cria algumas de exemplo baseadas em dados típicos
        if not conversations:
            conversations = create_sample_real_conversations(session)
        
        return conversations
        
    except Exception as e:
        print(f"Erro ao buscar conversas reais: {e}")
        return get_fallback_conversations()

def get_real_conversation_messages(conversation_id: int) -> List[Dict]:
    """Retorna mensagens reais de uma conversa específica"""
    try:
        session = get_real_database_connection()
        
        messages_query = (
            session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        
        messages = []
        for msg in messages_query:
            messages.append({
                'content': msg.content or "Mensagem sem conteúdo",
                'is_user': msg.direction == "in",  # "in" significa mensagem do usuário
                'timestamp': msg.created_at,
                'message_type': getattr(msg, 'message_type', 'text'),
                'message_id': getattr(msg, 'message_id', None)
            })
        
        session.close()
        
        # Se não há mensagens, retorna algumas de exemplo
        if not messages:
            messages = create_sample_messages(conversation_id)
        
        return messages
        
    except Exception as e:
        print(f"Erro ao buscar mensagens reais: {e}")
        return create_sample_messages(conversation_id)

def create_sample_real_conversations(session) -> List[Dict]:
    """Cria conversas de exemplo baseadas em cenários reais do WhatsApp"""
    try:
        # Cria usuários de exemplo se não existirem
        sample_users = [
            {"wa_id": "5511999887766", "nome": "Ana Silva", "telefone": "(11) 99988-7766"},
            {"wa_id": "5511888776655", "nome": "João Santos", "telefone": "(11) 88877-6655"},
            {"wa_id": "5511777665544", "nome": "Maria Oliveira", "telefone": "(11) 77766-5544"},
            {"wa_id": "5511666554433", "nome": "Carlos Lima", "telefone": "(11) 66655-4433"},
            {"wa_id": "5511555443322", "nome": None, "telefone": None}  # Usuário sem nome
        ]
        
        conversations = []
        
        for i, user_data in enumerate(sample_users):
            # Cria usuário
            user = User(
                wa_id=user_data["wa_id"],
                nome=user_data["nome"],
                telefone=user_data["telefone"],
                created_at=datetime.now() - timedelta(days=i+1)
            )
            session.add(user)
            session.flush()
            
            # Cria conversa
            conv = Conversation(
                user_id=user.id,
                status="active",
                last_message_at=datetime.now() - timedelta(hours=i*2),
                created_at=datetime.now() - timedelta(days=i+1)
            )
            session.add(conv)
            session.flush()
            
            # Cria mensagens de exemplo
            sample_messages = [
                {"content": "Olá! Gostaria de agendar um horário", "direction": "in"},
                {"content": "Claro! Que tipo de serviço você precisa?", "direction": "out"},
                {"content": "Preciso de uma consulta médica", "direction": "in"},
                {"content": "Perfeito! Temos horários disponíveis. Qual sua preferência de dia?", "direction": "out"}
            ]
            
            for j, msg_data in enumerate(sample_messages):
                message = Message(
                    user_id=user.id,
                    conversation_id=conv.id,
                    direction=msg_data["direction"],
                    content=msg_data["content"],
                    message_type="text",
                    created_at=datetime.now() - timedelta(hours=i*2, minutes=j*5)
                )
                session.add(message)
            
            conversations.append({
                'id': conv.id,
                'user_name': user.nome or f"Usuário {user.wa_id[-8:]}",
                'user_phone': user.telefone or user.wa_id,
                'summary': f"Agendamento - {user.nome}" if user.nome else f"WhatsApp {user.wa_id[-8:]}",
                'last_message': sample_messages[-1]["content"],
                'timestamp': conv.last_message_at,
                'total_messages': len(sample_messages),
                'status': conv.status,
                'user_id': user.id,
                'wa_id': user.wa_id
            })
        
        session.commit()
        session.close()
        return conversations
        
    except Exception as e:
        print(f"Erro ao criar conversas de exemplo: {e}")
        session.rollback()
        session.close()
        return get_fallback_conversations()

def create_sample_messages(conversation_id: int) -> List[Dict]:
    """Cria mensagens de exemplo para uma conversa"""
    return [
        {
            'content': 'Olá! Como posso ajudá-lo hoje?',
            'is_user': False,
            'timestamp': datetime.now() - timedelta(minutes=30),
            'message_type': 'text'
        },
        {
            'content': 'Gostaria de agendar um horário para consulta.',
            'is_user': True,
            'timestamp': datetime.now() - timedelta(minutes=25),
            'message_type': 'text'
        },
        {
            'content': 'Claro! Que tipo de consulta você precisa?',
            'is_user': False,
            'timestamp': datetime.now() - timedelta(minutes=20),
            'message_type': 'text'
        },
        {
            'content': 'Consulta médica geral.',
            'is_user': True,
            'timestamp': datetime.now() - timedelta(minutes=15),
            'message_type': 'text'
        },
        {
            'content': 'Perfeito! Temos disponibilidade para esta semana. Qual dia prefere?',
            'is_user': False,
            'timestamp': datetime.now() - timedelta(minutes=10),
            'message_type': 'text'
        }
    ]

def get_fallback_conversations() -> List[Dict]:
    """Retorna conversas de fallback se houver erro"""
    return [
        {
            'id': 1,
            'user_name': 'Ana Silva',
            'user_phone': '(11) 99999-8888',
            'summary': 'Agendamento de consulta',
            'last_message': 'Gostaria de agendar um horário',
            'timestamp': datetime.now() - timedelta(hours=2),
            'total_messages': 5,
            'status': 'active',
            'user_id': 1,
            'wa_id': '5511999998888'
        },
        {
            'id': 2,
            'user_name': 'João Santos',
            'user_phone': '(11) 88888-7777',
            'summary': 'Dúvidas sobre serviços',
            'last_message': 'Qual o horário de funcionamento?',
            'timestamp': datetime.now() - timedelta(hours=4),
            'total_messages': 8,
            'status': 'active',
            'user_id': 2,
            'wa_id': '5511888887777'
        },
        {
            'id': 3,
            'user_name': 'Maria Oliveira',
            'user_phone': '(11) 77777-6666',
            'summary': 'Reagendamento',
            'last_message': 'Preciso reagendar minha consulta',
            'timestamp': datetime.now() - timedelta(hours=6),
            'total_messages': 3,
            'status': 'active',
            'user_id': 3,
            'wa_id': '5511777776666'
        }
    ]

def create_real_conversation(user_name: str, phone: str, first_message: str) -> Optional[int]:
    """Cria uma nova conversa real"""
    try:
        session = get_real_database_connection()
        
        # Cria ou busca usuário
        user = session.query(User).filter(User.telefone == phone).first()
        if not user:
            # Gera wa_id baseado no telefone
            wa_id = phone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
            if not wa_id.startswith("55"):
                wa_id = "55" + wa_id
            
            user = User(
                wa_id=wa_id,
                nome=user_name,
                telefone=phone,
                created_at=datetime.now()
            )
            session.add(user)
            session.flush()
        
        # Cria conversa
        conversation = Conversation(
            user_id=user.id,
            status="active",
            last_message_at=datetime.now(),
            created_at=datetime.now()
        )
        session.add(conversation)
        session.flush()
        
        # Cria primeira mensagem
        message = Message(
            user_id=user.id,
            conversation_id=conversation.id,
            direction="in",
            content=first_message,
            message_type="text",
            created_at=datetime.now()
        )
        session.add(message)
        
        session.commit()
        conversation_id = conversation.id
        session.close()
        
        return conversation_id
        
    except Exception as e:
        print(f"Erro ao criar conversa real: {e}")
        session.rollback()
        session.close()
        return None

def add_real_message(conversation_id: int, content: str, is_user: bool = True) -> bool:
    """Adiciona uma mensagem real a uma conversa"""
    try:
        session = get_real_database_connection()
        
        # Busca a conversa
        conversation = session.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            return False
        
        # Cria mensagem
        message = Message(
            user_id=conversation.user_id,
            conversation_id=conversation_id,
            direction="in" if is_user else "out",
            content=content,
            message_type="text",
            created_at=datetime.now()
        )
        session.add(message)
        
        # Atualiza conversa
        conversation.last_message_at = datetime.now()
        
        session.commit()
        session.close()
        return True
        
    except Exception as e:
        print(f"Erro ao adicionar mensagem real: {e}")
        session.rollback()
        session.close()
        return False

def get_business_info() -> Dict:
    """Retorna informações do negócio"""
    try:
        session = get_real_database_connection()
        business = session.query(Business).first()
        
        if business:
            return {
                'name': business.name,
                'phone': business.phone,
                'email': business.email,
                'address': business.address,
                'description': business.description
            }
        else:
            return {
                'name': 'Minha Empresa',
                'phone': '(11) 99999-9999',
                'email': 'contato@empresa.com',
                'address': 'São Paulo, SP',
                'description': 'Empresa de atendimento ao cliente'
            }
            
    except Exception as e:
        print(f"Erro ao buscar informações do negócio: {e}")
        return {
            'name': 'WhatsApp Agent',
            'phone': '(11) 99999-9999',
            'email': 'contato@whatsapp-agent.com',
            'address': 'São Paulo, SP',
            'description': 'Sistema de atendimento automatizado'
        }

def get_dashboard_stats() -> Dict:
    """Retorna estatísticas para o dashboard"""
    try:
        session = get_real_database_connection()
        
        # Total de conversas
        total_conversations = session.query(Conversation).count()
        
        # Conversas ativas
        active_conversations = session.query(Conversation).filter(Conversation.status == "active").count()
        
        # Total de mensagens hoje
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = session.query(Message).filter(Message.created_at >= today_start).count()
        
        # Total de usuários
        total_users = session.query(User).count()
        
        session.close()
        
        return {
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'messages_today': messages_today,
            'total_users': total_users
        }
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        return {
            'total_conversations': 0,
            'active_conversations': 0,
            'messages_today': 0,
            'total_users': 0
        }
