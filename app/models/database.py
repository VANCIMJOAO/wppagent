from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Modelos SQLAlchemy para o banco de dados
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import bcrypt
import hashlib

Base = declarative_base()


class AdminUser(Base):
    """Modelo para usuários administradores do dashboard"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_super_admin = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    login_sessions = relationship("LoginSession", back_populates="admin_user")
    
    def set_password(self, password: str):
        """Hash e define a senha"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verifica se a senha está correta"""
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)


class LoginSession(Base):
    """Modelo para sessões de login"""
    __tablename__ = "login_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    admin_user_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    admin_user = relationship("AdminUser", back_populates="login_sessions")


class User(Base):
    """Modelo para usuários do WhatsApp"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    wa_id = Column(String(50), unique=True, nullable=False, index=True)
    nome = Column(String(255))
    telefone = Column(String(20))
    email = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    conversations = relationship("Conversation", back_populates="user")
    appointments = relationship("Appointment", back_populates="user")
    messages = relationship("Message", back_populates="user")


class Conversation(Base):
    """Modelo para conversas/chats"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="active", index=True)  # active, human, closed
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """Modelo para mensagens trocadas"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    direction = Column(String(10), nullable=False, index=True)  # 'in' ou 'out'
    message_id = Column(String(255), index=True)  # ID da mensagem no WhatsApp
    content = Column(Text)
    message_type = Column(String(20), default="text", index=True)  # text, audio, interactive, etc
    raw_payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relacionamentos
    user = relationship("User", back_populates="messages")
    conversation = relationship("Conversation", back_populates="messages")


class Business(Base):
    """Modelo para dados da empresa/negócio"""
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    address = Column(Text)
    description = Column(Text)
    
    # Horários de funcionamento (JSON)
    business_hours = Column(JSON, default={
        "monday": {"open": "09:00", "close": "18:00", "closed": False},
        "tuesday": {"open": "09:00", "close": "18:00", "closed": False},
        "wednesday": {"open": "09:00", "close": "18:00", "closed": False},
        "thursday": {"open": "09:00", "close": "18:00", "closed": False},
        "friday": {"open": "09:00", "close": "18:00", "closed": False},
        "saturday": {"open": "09:00", "close": "16:00", "closed": False},
        "sunday": {"open": "09:00", "close": "16:00", "closed": True}
    })
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    services = relationship("Service", back_populates="business")
    appointments = relationship("Appointment", back_populates="business")


class Service(Base):
    """Modelo para serviços oferecidos"""
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, default=60)  # Duração em minutos
    price = Column(String(20))  # Ex: "R$ 50,00"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    business = relationship("Business", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")


class Appointment(Base):
    """Modelo para agendamentos"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    # Data e horário
    date_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True))  # Calculado automaticamente
    
    # Status do agendamento
    status = Column(String(20), default="pendente", index=True)  # pendente, confirmado, cancelado, concluido, bloqueado
    
    # Informações adicionais
    notes = Column(Text)
    customer_notes = Column(Text)  # Observações do cliente
    admin_notes = Column(Text)     # Observações internas
    
    # Dados de cancelamento
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(String(255))
    cancelled_by = Column(String(20))  # 'customer', 'admin', 'system'
    
    # Dados de confirmação
    confirmed_at = Column(DateTime(timezone=True))
    confirmed_by = Column(String(20))  # 'customer', 'admin', 'auto'
    
    # Preço no momento do agendamento
    price_at_booking = Column(String(20))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    user = relationship("User", back_populates="appointments")
    business = relationship("Business", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")


class BlockedTime(Base):
    """Modelo para horários bloqueados"""
    __tablename__ = "blocked_times"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Datas e horários do bloqueio
    start_date = Column(DateTime(timezone=True), nullable=False)  # Data de início
    end_date = Column(DateTime(timezone=True), nullable=False)    # Data de fim
    start_time = Column(DateTime(timezone=True), nullable=False)  # Horário de início
    end_time = Column(DateTime(timezone=True), nullable=False)    # Horário de fim
    reason = Column(String(255))  # Ex: "Almoço", "Reunião", "Manutenção"
    
    # Tipo de bloqueio
    block_type = Column(String(20), default="manual")  # manual, automatic, recurring
    
    # Para bloqueios recorrentes
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON)  # Ex: {"type": "weekly", "days": ["monday", "friday"]}
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(50))  # admin username ou 'system'


class MetaLog(Base):
    """Modelo para logs das requisições da Meta API"""
    __tablename__ = "meta_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    direction = Column(String(10), nullable=False)  # 'in' ou 'out'
    endpoint = Column(String(255))
    method = Column(String(10))
    status_code = Column(Integer)
    headers = Column(JSON)
    payload = Column(JSON)
    response = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Admin(Base):
    """Modelo para usuários admin do dashboard"""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CompanyInfo(Base):
    """Modelo para informações dinâmicas da empresa"""
    __tablename__ = "company_info"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Informações básicas
    company_name = Column(String(255), nullable=False)
    slogan = Column(String(500))
    about_us = Column(Text)
    
    # Contatos
    whatsapp_number = Column(String(20))
    phone_secondary = Column(String(20))
    email_contact = Column(String(255))
    website = Column(String(255))
    
    # Endereço completo
    street_address = Column(String(500))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    country = Column(String(50), default="Brasil")
    
    # Redes sociais
    instagram = Column(String(255))
    facebook = Column(String(255))
    linkedin = Column(String(255))
    
    # Configurações do bot
    welcome_message = Column(Text, default="Olá! 👋 Bem-vindo à nossa empresa! Como posso ajudá-lo hoje?")
    auto_response_enabled = Column(Boolean, default=True)
    business_description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamento
    business = relationship("Business")


class MessageTemplate(Base):
    """Modelo para templates de mensagens personalizáveis"""
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    template_key = Column(String(100), nullable=False)  # Ex: "booking_confirmation", "welcome", etc
    template_name = Column(String(255))
    template_content = Column(Text, nullable=False)
    
    # Variáveis disponíveis (JSON array)
    available_variables = Column(JSON, default=[])  # Ex: ["{customer_name}", "{service}", "{date}", "{time}"]
    
    # Configurações
    is_active = Column(Boolean, default=True)
    category = Column(String(50))  # Ex: "booking", "greeting", "information"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamento
    business = relationship("Business")


class BotConfiguration(Base):
    """Modelo para configurações específicas do bot"""
    __tablename__ = "bot_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Configurações gerais do bot
    auto_response_enabled = Column(Boolean, default=True)
    response_delay_min = Column(Integer, default=1)  # Delay mínimo em segundos
    response_delay_max = Column(Integer, default=3)  # Delay máximo em segundos
    max_retries = Column(Integer, default=3)
    language = Column(String(10), default="pt-BR")
    timezone = Column(String(50), default="America/Sao_Paulo")
    max_message_length = Column(Integer, default=1000)
    working_hours_only = Column(Boolean, default=True)
    weekend_support = Column(Boolean, default=False)
    
    # Configurações de agendamento
    appointment_enabled = Column(Boolean, default=True)
    min_advance_booking_hours = Column(Integer, default=2)  # Antecedência mínima em horas
    max_advance_booking_days = Column(Integer, default=30)  # Máximo de dias para agendamento
    max_appointments_per_day = Column(Integer, default=20)
    appointment_buffer_minutes = Column(Integer, default=15)
    auto_confirm_bookings = Column(Boolean, default=False)
    
    # Configurações de horários
    slot_duration_minutes = Column(Integer, default=30)  # Duração dos slots de agendamento
    break_between_appointments_minutes = Column(Integer, default=0)  # Intervalo entre agendamentos
    
    # Configurações de notificações
    notification_lead_time_hours = Column(Integer, default=24)
    send_confirmation_messages = Column(Boolean, default=True)
    send_reminder_messages = Column(Boolean, default=True)
    reminder_hours_before = Column(Integer, default=24)  # Horas antes para lembrete
    follow_up_enabled = Column(Boolean, default=True)
    follow_up_delay_minutes = Column(Integer, default=60)
    
    # Configurações do chatbot
    max_retries_data_collection = Column(Integer, default=3)
    timeout_minutes_user_response = Column(Integer, default=30)
    enable_human_handoff = Column(Boolean, default=True)
    
    # Configurações de coleta de dados
    data_collection_enabled = Column(Boolean, default=True)
    required_fields = Column(JSON, default=["nome", "telefone"])
    optional_fields = Column(JSON, default=["email", "endereco"])
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamento
    business = relationship("Business")


class AvailableSlot(Base):
    """Modelo para slots de horário disponíveis calculados dinamicamente"""
    __tablename__ = "available_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"))
    
    # Data e horários do slot
    date = Column(DateTime(timezone=True), nullable=False)  # Data do slot
    start_time = Column(DateTime(timezone=True), nullable=False)  # Horário de início
    end_time = Column(DateTime(timezone=True), nullable=False)  # Horário de fim
    duration_minutes = Column(Integer, nullable=False, default=60)
    
    # Status e disponibilidade
    is_available = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    blocked_reason = Column(String(255))
    max_appointments = Column(Integer, default=1)
    current_appointments = Column(Integer, default=0)
    
    # Cache para performance
    day_of_week = Column(Integer)  # 0=segunda, 6=domingo
    slot_time = Column(String(5))  # Ex: "14:30"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamentos
    business = relationship("Business")
    service = relationship("Service")


class CustomerDataCollection(Base):
    """Modelo para rastrear coleta de dados do cliente"""
    __tablename__ = "customer_data_collection"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Status da coleta
    collection_status = Column(String(20), default="incomplete")  # incomplete, complete, in_progress
    
    # Dados coletados
    has_name = Column(Boolean, default=False)
    has_email = Column(Boolean, default=False)
    has_phone = Column(Boolean, default=False)
    
    # Tentativas de coleta
    name_attempts = Column(Integer, default=0)
    email_attempts = Column(Integer, default=0)
    phone_attempts = Column(Integer, default=0)
    
    # Dados adicionais
    collection_method = Column(String(50))  # "whatsapp", "form", "manual"
    notes = Column(Text)
    
    last_attempt_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamento
    user = relationship("User")


class ConversationContext(Base):
    """Modelo para contexto das conversas (estado da conversa)"""
    __tablename__ = "conversation_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    
    # Estado atual da conversa
    current_state = Column(String(50), default="initial")  # initial, collecting_data, booking, confirming, etc
    previous_state = Column(String(50))
    
    # Dados temporários da conversa
    temp_data = Column(JSON, default={})  # Dados sendo coletados
    collected_data = Column(JSON, default={})  # Dados já validados
    
    # Contexto do agendamento em andamento
    booking_data = Column(JSON)  # Dados do agendamento em progresso
    
    # Controles de fluxo
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    awaiting_response = Column(Boolean, default=False)
    awaiting_response_for = Column(String(100))  # Ex: "email", "service_selection"
    
    # Timestamps
    state_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    last_interaction_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacionamento
    conversation = relationship("Conversation")
