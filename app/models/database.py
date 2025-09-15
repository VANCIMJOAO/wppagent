from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Modelos SQLAlchemy para o banco de dados
"""
import hashlib
from datetime import datetime
from typing import Optional

import bcrypt
from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, Numeric, String, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Verifica se a senha está correta"""
        password_bytes = password.encode("utf-8")
        hash_bytes = self.password_hash.encode("utf-8")
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


class RefreshToken(Base):
    """Modelo para refresh tokens JWT"""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    admin_user_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos
    admin_user = relationship("AdminUser")


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
    last_message_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
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
    message_type = Column(
        String(20), default="text", index=True
    )  # text, audio, interactive, etc
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
    business_hours = Column(
        JSON,
        default={
            "monday": {"open": "09:00", "close": "18:00", "closed": False},
            "tuesday": {"open": "09:00", "close": "18:00", "closed": False},
            "wednesday": {"open": "09:00", "close": "18:00", "closed": False},
            "thursday": {"open": "09:00", "close": "18:00", "closed": False},
            "friday": {"open": "09:00", "close": "18:00", "closed": False},
            "saturday": {"open": "09:00", "close": "16:00", "closed": False},
            "sunday": {"open": "09:00", "close": "16:00", "closed": True},
        },
    )

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
    price = Column(Numeric(10, 2))  # Preço como decimal
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
    duration_minutes = Column(Integer, default=60, nullable=False)  # ✅ Padronizado
    end_time = Column(DateTime(timezone=True))  # Calculado automaticamente via trigger

    # Status do agendamento
    # ✅ C001: Enum unificado - agendado, confirmado, realizado, cancelado, pendente
    status = Column(String(20), default="agendado", index=True)

    # Informações adicionais
    notes = Column(Text)
    customer_notes = Column(Text)  # Observações do cliente
    admin_notes = Column(Text)  # Observações internas

    # Dados de cancelamento
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(String(255))
    cancelled_by = Column(String(20))  # 'customer', 'admin', 'system'

    # Dados de confirmação
    confirmed_at = Column(DateTime(timezone=True))
    confirmed_by = Column(String(20))  # 'customer', 'admin', 'auto'

    # ✅ PREÇO UNIFICADO - Removidos campos duplicados
    price = Column(Numeric(10, 2), default=0.00, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacionamentos
    user = relationship("User", back_populates="appointments")
    business = relationship("Business", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")

    def calculate_end_time(self):
        """Calcula automaticamente o end_time baseado em date_time + duration_minutes"""
        if self.date_time and self.duration_minutes:
            from datetime import timedelta

            self.end_time = self.date_time + timedelta(minutes=self.duration_minutes)
        return self.end_time

    def to_dict(self):
        """Converte o appointment para dict com campos padronizados"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "business_id": self.business_id,
            "service_id": self.service_id,
            "date_time": self.date_time.isoformat() if self.date_time else None,
            "duration_minutes": self.duration_minutes,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "price": float(self.price) if self.price else 0.00,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BlockedTime(Base):
    """Modelo para horários bloqueados"""

    __tablename__ = "blocked_times"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)

    # Datas e horários do bloqueio
    start_date = Column(DateTime(timezone=True), nullable=False)  # Data de início
    end_date = Column(DateTime(timezone=True), nullable=False)  # Data de fim
    start_time = Column(DateTime(timezone=True), nullable=False)  # Horário de início
    end_time = Column(DateTime(timezone=True), nullable=False)  # Horário de fim
    reason = Column(String(255))  # Ex: "Almoço", "Reunião", "Manutenção"

    # Tipo de bloqueio
    block_type = Column(String(20), default="manual")  # manual, automatic, recurring

    # Para bloqueios recorrentes
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(
        JSON
    )  # Ex: {"type": "weekly", "days": ["monday", "friday"]}

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


# MODELO ADMIN DUPLICADO REMOVIDO
# O modelo Admin (tabela "admins") foi removido pois:
# 1. Estava duplicado com AdminUser (tabela "admin_users")
# 2. AdminUser é o modelo ativo usado em toda aplicação
# 3. Tabela "admins" tem 0 registros no banco
# 4. AdminUser tem funcionalidades completas (hash senha, sessions, etc.)


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
    welcome_message = Column(
        Text, default="Olá! 👋 Bem-vindo à nossa empresa! Como posso ajudá-lo hoje?"
    )
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

    template_key = Column(
        String(100), nullable=False
    )  # Ex: "booking_confirmation", "welcome", etc
    template_name = Column(String(255))
    template_content = Column(Text, nullable=False)

    # Variáveis disponíveis (JSON array)
    available_variables = Column(
        JSON, default=[]
    )  # Ex: ["{customer_name}", "{service}", "{date}", "{time}"]

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
    min_advance_booking_hours = Column(
        Integer, default=2
    )  # Antecedência mínima em horas
    max_advance_booking_days = Column(
        Integer, default=30
    )  # Máximo de dias para agendamento
    max_appointments_per_day = Column(Integer, default=20)
    appointment_buffer_minutes = Column(Integer, default=15)
    auto_confirm_bookings = Column(Boolean, default=False)

    # Configurações de horários
    slot_duration_minutes = Column(
        Integer, default=30
    )  # Duração dos slots de agendamento
    break_between_appointments_minutes = Column(
        Integer, default=0
    )  # Intervalo entre agendamentos

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
    collection_status = Column(
        String(20), default="incomplete"
    )  # incomplete, complete, in_progress

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
    current_state = Column(
        String(50), default="initial"
    )  # initial, collecting_data, booking, confirming, etc
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


class PushSubscription(Base):
    """
    🔔 Push Notification Subscriptions

    Gerencia subscriptions de push notifications para admins.
    Cada admin pode ter múltiplas subscriptions (diferentes dispositivos/browsers).
    """

    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(
        Integer, ForeignKey("admin_users.id"), nullable=False, index=True
    )

    # Dados da subscription (formato Web Push Protocol)
    endpoint = Column(String(500), nullable=False, unique=True)  # URL do endpoint
    p256dh_key = Column(String(255), nullable=False)  # Chave pública do cliente
    auth_key = Column(String(255), nullable=False)  # Token de autenticação

    # Metadados
    user_agent = Column(String(500))  # Browser/device info
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamento
    admin_user = relationship("AdminUser", back_populates="push_subscriptions")


# Adicionar relacionamento reverso no AdminUser
AdminUser.push_subscriptions = relationship(
    "PushSubscription", back_populates="admin_user"
)


class PushNotification(Base):
    """
    📱 Log de Push Notifications Enviadas

    Histórico de notificações enviadas para auditoria e analytics.
    """

    __tablename__ = "push_notifications"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(
        Integer, ForeignKey("push_subscriptions.id"), nullable=False
    )

    # Conteúdo da notificação
    title = Column(String(255), nullable=False)
    body = Column(Text)
    data = Column(JSON)  # Dados adicionais

    # Status
    status = Column(String(50), default="sent")  # sent, delivered, failed, expired
    error_message = Column(Text)

    # Timestamps
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamento
    subscription = relationship("PushSubscription")


# =============================================================================
# MODELOS PARA TABELAS ÓRFÃS - RESOLUÇÃO DE SCHEMA DRIFT
# =============================================================================


class LoginAttempt(Base):
    """
    Modelo para tabela login_attempts órfã
    Sistema de rate limiting e auditoria de tentativas de login
    """

    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45))  # Suporte IPv4 e IPv6
    success = Column(Boolean, nullable=False)
    attempted_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    error_message = Column(Text)


class UserSession(Base):
    """
    Modelo para tabela user_sessions órfã
    Sistema de sessões de usuários (não admin)
    """

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relacionamento
    user = relationship("User")


class BusinessHours(Base):
    """
    Modelo para tabela business_hours órfã
    Sistema de horários estruturado (alternativa ao JSON em businesses)
    """

    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(
        Integer, ForeignKey("businesses.id"), nullable=False, default=1
    )
    day_of_week = Column(Integer, nullable=False)  # 0=domingo, 1=segunda, ..., 6=sábado
    is_open = Column(Boolean, nullable=False, default=True)
    open_time = Column(String(5))  # Usando String para compatibilidade (formato HH:MM)
    close_time = Column(String(5))
    break_start_time = Column(String(5))
    break_end_time = Column(String(5))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relacionamento
    business = relationship("Business")


class BusinessPolicy(Base):
    """
    Modelo para tabela business_policies órfã
    Sistema de políticas de negócio
    """

    __tablename__ = "business_policies"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(
        Integer, ForeignKey("businesses.id"), nullable=False, default=1
    )
    policy_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rules = Column(JSON)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relacionamento
    business = relationship("Business")


class PaymentMethod(Base):
    """
    Modelo para tabela payment_methods órfã
    Sistema de métodos de pagamento
    """

    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(
        Integer, ForeignKey("businesses.id"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    description = Column(Text)
    additional_info = Column(Text)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relacionamento
    business = relationship("Business")


class AuthUser(Base):
    """
    Modelo para tabela auth_users órfã
    Sistema de autenticação alternativo (verificar se conflita com AdminUser)
    """

    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    company_id = Column(Integer)
    phone = Column(String(20))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login = Column(DateTime(timezone=True))
