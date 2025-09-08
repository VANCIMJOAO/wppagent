"""
📋 Schemas Unificados - API Contracts
===================================

DTOs padronizados para eliminar divergências entre backend e frontend.

Funcionalidades:
- ✅ Aliases para compatibilidade com nomes de campos existentes
- ✅ Padronização de nomenclatura entre sistemas
- ✅ Validação consistente de tipos
- ✅ Suporte a population_by_field_name para flexibilidade

Autor: Claude AI
Data: 2025-09-07
Status: Implementação crítica para unificação de APIs
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

# Enums para padronização
class AppointmentStatus(str, Enum):
    """Status padronizados de agendamentos"""
    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    REALIZADO = "realizado"
    CANCELADO = "cancelado"
    PENDENTE = "pendente"

class MessageDirection(str, Enum):
    """Direção padronizada de mensagens"""
    IN = "in"   # Mensagem recebida
    OUT = "out" # Mensagem enviada

class ConversationStatus(str, Enum):
    """Status padronizados de conversas"""
    ACTIVE = "active"
    CLOSED = "closed"
    PENDING = "pending"

class AppointmentResponseUnified(BaseModel):
    """
    📅 Schema unificado para agendamentos
    
    Resolve divergências entre backend e frontend usando aliases.
    Campos principais mapeados para nomes padronizados.
    """
    id: int
    user_id: int
    business_id: int
    service_id: Optional[int] = None
    
    # ✅ Campos padronizados (backend → frontend)
    data_agendamento: datetime = Field(alias="date_time", description="Data e hora do agendamento")
    horario: str = Field(alias="time_slot", description="Horário formatado HH:MM")
    duracao_minutos: int = Field(alias="duration_minutes", description="Duração em minutos")
    valor: float = Field(alias="price", description="Valor do serviço")
    status: AppointmentStatus = Field(description="Status do agendamento")
    observacoes: Optional[str] = Field(alias="notes", default=None, description="Observações do agendamento")
    
    # ✅ Dados relacionados padronizados
    cliente_nome: str = Field(alias="user_name", description="Nome do cliente")
    cliente_telefone: str = Field(alias="user_phone", description="Telefone do cliente")
    cliente_email: Optional[str] = Field(alias="user_email", default=None, description="Email do cliente")
    servico_nome: str = Field(alias="service_name", description="Nome do serviço")
    servico_descricao: Optional[str] = Field(alias="service_description", default=None, description="Descrição do serviço")
    business_name: str = Field(description="Nome da empresa")
    
    # ✅ Timestamps padronizados
    created_at: datetime = Field(description="Data de criação")
    updated_at: Optional[datetime] = Field(default=None, description="Data de atualização")
    
    class Config:
        populate_by_name = True  # ✅ Pydantic v2 syntax
        from_attributes = True  # ✅ Suporte a SQLAlchemy objects
        use_enum_values = True  # ✅ Usa valores string dos enums
        json_encoders = {
            datetime: lambda dt: dt.isoformat()  # ✅ ISO 8601 format
        }

class ConversationResponseUnified(BaseModel):
    """
    💬 Schema unificado para conversas
    
    Padroniza campos de conversas com dados relacionados.
    """
    id: int
    user_id: int
    status: ConversationStatus = Field(description="Status da conversa")
    last_message_at: Optional[datetime] = Field(default=None, description="Timestamp da última mensagem")
    created_at: datetime = Field(description="Data de criação")
    updated_at: Optional[datetime] = Field(default=None, description="Data de atualização")
    
    # ✅ Dados relacionados padronizados
    user_name: str = Field(description="Nome do usuário")
    user_phone: Optional[str] = Field(default=None, description="Telefone do usuário")
    total_messages: int = Field(default=0, description="Total de mensagens na conversa")
    unread_messages: int = Field(default=0, description="Mensagens não lidas")
    last_message: Optional[str] = Field(default=None, description="Conteúdo da última mensagem")
    
    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class MessageResponseUnified(BaseModel):
    """
    💬 Schema unificado para mensagens
    
    Padroniza direção e campos de mensagens.
    """
    id: int
    conversation_id: int
    content: str = Field(description="Conteúdo da mensagem")
    message_type: str = Field(description="Tipo da mensagem (text, image, etc.)")
    direction: MessageDirection = Field(description="Direção: 'in' (recebida) ou 'out' (enviada)")
    created_at: datetime = Field(description="Data de criação")
    whatsapp_id: Optional[str] = Field(alias="message_id", default=None, description="ID do WhatsApp")
    
    # ✅ Campos adicionais para compatibilidade
    sender_type: Optional[str] = Field(default=None, description="Tipo do remetente")
    is_read: bool = Field(default=False, description="Mensagem foi lida")
    
    class Config:
        populate_by_name = True
        from_attributes = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ConversationWithMessagesUnified(ConversationResponseUnified):
    """
    💬 Schema unificado para conversa com mensagens
    
    Extend a conversa base com lista de mensagens.
    """
    messages: List[MessageResponseUnified] = Field(default_factory=list, description="Lista de mensagens")

# ✅ Schemas para listagem paginada
class AppointmentsListResponseUnified(BaseModel):
    """📅 Response unificado para lista de agendamentos"""
    appointments: List[AppointmentResponseUnified]
    total: int = Field(description="Total de registros")
    page: int = Field(description="Página atual")
    per_page: int = Field(description="Registros por página")
    has_more: bool = Field(description="Há mais páginas")
    
class ConversationsListResponseUnified(BaseModel):
    """💬 Response unificado para lista de conversas"""
    conversations: List[ConversationResponseUnified]
    total: int = Field(description="Total de registros")
    limit: int = Field(description="Limite de registros")
    offset: int = Field(description="Offset atual")
    has_more: bool = Field(description="Há mais registros")

# ✅ Schemas para criação/atualização
class AppointmentCreateRequest(BaseModel):
    """📅 Schema para criação de agendamentos"""
    user_id: int
    business_id: int
    service_id: Optional[int] = None
    date_time: datetime
    duration_minutes: int = 60
    price: float = 0.0
    notes: Optional[str] = None
    
class AppointmentUpdateRequest(BaseModel):
    """📅 Schema para atualização de agendamentos"""
    date_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class MessageCreateRequest(BaseModel):
    """💬 Schema para criação de mensagens"""
    conversation_id: int
    content: str
    message_type: str = "text"
    direction: MessageDirection = MessageDirection.OUT
    whatsapp_id: Optional[str] = None

# ✅ Utilitários para transformação de dados
class SchemaTransformer:
    """
    🔄 Utilitários para transformar dados entre formatos
    """
    
    @staticmethod
    def appointment_row_to_unified(row) -> dict:
        """
        Transforma row de SQLAlchemy para dict compatível com AppointmentResponseUnified
        
        Suporta múltiplos formatos de row:
        - Row com objetos (row.Appointment, row.User, etc.)
        - Row com colunas diretas (row.appointment_id, row.user_name, etc.)
        - Row com aliases antigos (row.cliente_nome, row.servico_nome, etc.)
        """
        # Helper para acessar atributos de forma segura
        def safe_get(row, *attrs, default=None):
            for attr in attrs:
                try:
                    if hasattr(row, attr):
                        value = getattr(row, attr)
                        if value is not None:
                            return value
                except:
                    continue
            return default
        
        # Helper para normalizar status
        def normalize_status(status):
            if not status:
                return 'agendado'
            status_map = {
                'cancelled': 'cancelado',
                'confirmed': 'confirmado',
                'completed': 'realizado',
                'pending': 'pendente',
                'scheduled': 'agendado',
                # Manter valores já corretos
                'agendado': 'agendado',
                'confirmado': 'confirmado',
                'realizado': 'realizado',
                'cancelado': 'cancelado',
                'pendente': 'pendente'
            }
            return status_map.get(status.lower(), 'agendado')
        
        # Acessar objeto Appointment se disponível
        appointment = safe_get(row, 'Appointment')
        if appointment:
            # Row com objetos separados
            return {
                "id": appointment.id,
                "user_id": appointment.user_id,
                "business_id": appointment.business_id,
                "service_id": appointment.service_id,
                "date_time": appointment.date_time,
                "time_slot": appointment.date_time.strftime('%H:%M') if appointment.date_time else '',
                "duration_minutes": appointment.duration_minutes or 60,
                "price": float(appointment.price) if appointment.price else 0.0,
                "status": normalize_status(appointment.status),
                "notes": appointment.notes,
                "user_name": safe_get(row, 'user_name', 'cliente_nome', default=''),
                "user_phone": safe_get(row, 'user_phone', 'cliente_telefone', default=''),
                "user_email": safe_get(row, 'user_email', 'cliente_email'),
                "service_name": safe_get(row, 'service_name', 'servico_nome', default=''),
                "service_description": safe_get(row, 'service_description', 'servico_descricao'),
                "business_name": safe_get(row, 'business_name', default=''),
                "created_at": appointment.created_at,
                "updated_at": appointment.updated_at
            }
        else:
            # Row com colunas diretas
            return {
                "id": safe_get(row, 'appointment_id', 'id'),
                "user_id": safe_get(row, 'user_id'),
                "business_id": safe_get(row, 'business_id'),
                "service_id": safe_get(row, 'service_id'),
                "date_time": safe_get(row, 'date_time'),
                "time_slot": safe_get(row, 'date_time').strftime('%H:%M') if safe_get(row, 'date_time') else '',
                "duration_minutes": safe_get(row, 'duration_minutes', default=60),
                "price": float(safe_get(row, 'price', default=0.0)),
                "status": normalize_status(safe_get(row, 'status')),
                "notes": safe_get(row, 'notes'),
                "user_name": safe_get(row, 'user_name', 'cliente_nome', default=''),
                "user_phone": safe_get(row, 'user_phone', 'cliente_telefone', default=''),
                "user_email": safe_get(row, 'user_email', 'cliente_email'),
                "service_name": safe_get(row, 'service_name', 'servico_nome', default=''),
                "service_description": safe_get(row, 'service_description', 'servico_descricao'),
                "business_name": safe_get(row, 'business_name', default=''),
                "created_at": safe_get(row, 'created_at'),
                "updated_at": safe_get(row, 'updated_at')
            }
    
    @staticmethod
    def conversation_row_to_unified(row) -> dict:
        """
        Transforma row de SQLAlchemy para dict compatível com ConversationResponseUnified
        """
        return {
            "id": row.id,
            "user_id": row.user_id,
            "status": row.status or 'active',
            "last_message_at": row.last_message_at,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "user_name": getattr(row, 'user_name', ''),
            "user_phone": getattr(row, 'user_phone', None),
            "total_messages": getattr(row, 'total_messages', 0),
            "unread_messages": getattr(row, 'unread_messages', 0),
            "last_message": getattr(row, 'last_message', None)
        }
