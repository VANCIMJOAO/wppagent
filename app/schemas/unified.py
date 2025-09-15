"""
� CF001 - Schemas Unificados com Padronização snake_case ↔ camelCase
========================================================================

Sistema de aliases Pydantic que permite:
- Backend: mantém snake_case internamente
- Frontend: recebe camelCase nas responses
- API: aceita ambos formatos nas requests (backward compatibility)

Funcionalidades CF001:
- ✅ serialization_alias para response camelCase automático
- ✅ field alias para aceitar camelCase em requests
- ✅ populate_by_name para backward compatibility
- ✅ 15 campos críticos padronizados conforme tabela de mapeamento

Autor: GitHub Copilot
Data: 2025-09-12
Status: CF001 Implementation - Naming Standardization
"""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field
from pydantic.functional_serializers import field_serializer


# CF001 - Enums padronizados
class AppointmentStatus(str, Enum):
    """CF001 - Status padronizados de agendamentos"""

    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    REALIZADO = "realizado"
    CANCELADO = "cancelado"
    PENDENTE = "pendente"


class MessageDirection(str, Enum):
    """CF001 - Direção padronizada de mensagens"""

    IN = "in"  # Mensagem recebida
    OUT = "out"  # Mensagem enviada


class ConversationStatus(str, Enum):
    """CF001 - Status padronizados de conversas"""

    ACTIVE = "active"
    CLOSED = "closed"
    PENDING = "pending"


class UnifiedAppointmentResponse(BaseModel):
    """
    📅 CF001 - Schema unificado para appointments com aliases snake↔camel

    Implementa os 15 campos críticos da tabela de mapeamento CF001:
    - serialization_alias: Backend snake_case → Frontend camelCase
    - populate_by_name: Aceita ambos formatos em requests
    """

    id: int
    user_id: int = Field(serialization_alias="userId")
    business_id: int = Field(serialization_alias="businessId")
    service_id: Optional[int] = Field(None, serialization_alias="serviceId")

    # CF001 - Campos críticos com aliases
    date_time: datetime = Field(serialization_alias="dateTime")
    duration_minutes: int = Field(serialization_alias="durationMinutes")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: Optional[datetime] = Field(None, serialization_alias="updatedAt")

    # Status unificado
    status: AppointmentStatus = Field(
        description="Status: agendado|confirmado|realizado|cancelado|pendente"
    )

    # Campos opcionais
    notes: Optional[str] = None
    price: Optional[float] = None
    client_name: Optional[str] = Field(None, serialization_alias="clientName")
    client_phone: Optional[str] = Field(None, serialization_alias="clientPhone")
    service_name: Optional[str] = Field(None, serialization_alias="serviceName")
    business_name: Optional[str] = Field(None, serialization_alias="businessName")

    model_config = ConfigDict(
        populate_by_name=True,  # CF001 - Aceita tanto snake_case quanto camelCase
        from_attributes=True,  # Suporte a SQLAlchemy objects
        use_enum_values=True,  # Usa valores string dos enums
    )

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, dt: datetime, _info):
        return dt.isoformat() if dt else None


class UnifiedAppointmentRequest(BaseModel):
    """CF001 - Schema de request que aceita ambos formatos"""

    user_id: Optional[int] = Field(None, alias="userId")
    business_id: Optional[int] = Field(None, alias="businessId")
    service_id: Optional[int] = Field(None, alias="serviceId")

    # CF001 - Aceita ambos os formatos
    date_time: Optional[datetime] = Field(None, alias="dateTime")
    duration_minutes: Optional[int] = Field(None, alias="durationMinutes")

    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    price: Optional[float] = None
    client_name: Optional[str] = Field(None, alias="clientName")
    client_phone: Optional[str] = Field(None, alias="clientPhone")

    class Config:
        populate_by_name = True


class UnifiedConversationResponse(BaseModel):
    """CF001 - Conversa unificada com aliases"""

    id: int
    user_id: int = Field(serialization_alias="userId")
    business_id: Optional[int] = Field(None, serialization_alias="businessId")
    status: ConversationStatus

    # CF001 - Timestamps com aliases
    last_message_at: Optional[datetime] = Field(
        None, serialization_alias="lastMessageAt"
    )
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: Optional[datetime] = Field(None, serialization_alias="updatedAt")

    # CF001 - Campos computados
    total_messages: int = Field(default=0, serialization_alias="totalMessages")
    unread_messages: int = Field(default=0, serialization_alias="unreadMessages")

    # CF001 - Computed field como property normal
    @property
    def last_interaction(self) -> Optional[datetime]:
        """CF001 - Última interação calculada"""
        return self.last_message_at or self.updated_at

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, use_enum_values=True
    )

    @field_serializer("last_message_at", "updated_at", when_used="json")
    def serialize_datetime_conv(self, dt: datetime, _info):
        return dt.isoformat() if dt else None


class UnifiedConversationRequest(BaseModel):
    """CF001 - Request schema para conversations"""

    user_id: Optional[int] = Field(None, alias="userId")
    business_id: Optional[int] = Field(None, alias="businessId")
    status: Optional[ConversationStatus] = None

    class Config:
        populate_by_name = True


class UnifiedMessageResponse(BaseModel):
    """CF001 - Mensagem unificada com aliases"""

    id: int
    conversation_id: int = Field(serialization_alias="conversationId")
    content: str
    message_type: str = Field(serialization_alias="messageType")
    direction: MessageDirection

    # CF001 - Flags com aliases
    is_read: bool = Field(serialization_alias="isRead")
    is_active: bool = Field(default=True, serialization_alias="isActive")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: Optional[datetime] = Field(None, serialization_alias="updatedAt")

    # Campos opcionais
    sender_name: Optional[str] = Field(None, serialization_alias="senderName")
    media_url: Optional[str] = Field(None, serialization_alias="mediaUrl")
    whatsapp_id: Optional[str] = Field(None, serialization_alias="whatsappId")

    class Config:
        populate_by_name = True
        from_attributes = True
        use_enum_values = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class UnifiedMessageRequest(BaseModel):
    """CF001 - Request schema para messages"""

    conversation_id: Optional[int] = Field(None, alias="conversationId")
    content: str
    message_type: Optional[str] = Field(None, alias="messageType")
    direction: Optional[MessageDirection] = None
    is_read: Optional[bool] = Field(None, alias="isRead")

    class Config:
        populate_by_name = True


class ConversationResponseUnified(BaseModel):
    """
    💬 Schema unificado para conversas

    Padroniza campos de conversas com dados relacionados.
    """

    id: int
    user_id: int
    status: ConversationStatus = Field(description="Status da conversa")
    last_message_at: Optional[datetime] = Field(
        default=None, description="Timestamp da última mensagem"
    )
    created_at: datetime = Field(description="Data de criação")
    updated_at: Optional[datetime] = Field(
        default=None, description="Data de atualização"
    )

    # ✅ Dados relacionados padronizados
    user_name: str = Field(description="Nome do usuário")
    user_phone: Optional[str] = Field(default=None, description="Telefone do usuário")
    total_messages: int = Field(default=0, description="Total de mensagens na conversa")
    unread_messages: int = Field(default=0, description="Mensagens não lidas")
    last_message: Optional[str] = Field(
        default=None, description="Conteúdo da última mensagem"
    )

    class Config:
        from_attributes = True
        use_enum_values = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class MessageResponseUnified(BaseModel):
    """
    💬 Schema unificado para mensagens

    ✅ Padronizado para usar apenas 'direction' ('in' | 'out')
    """

    id: int
    conversation_id: int
    content: str = Field(description="Conteúdo da mensagem")
    message_type: str = Field(description="Tipo da mensagem (text, image, etc.)")
    direction: MessageDirection = Field(
        description="Direção: 'in' (recebida) ou 'out' (enviada)"
    )
    created_at: datetime = Field(description="Data de criação")
    whatsapp_id: Optional[str] = Field(
        alias="message_id", default=None, description="ID do WhatsApp"
    )

    # ✅ Campos adicionais
    is_read: bool = Field(default=False, description="Mensagem foi lida")

    class Config:
        populate_by_name = True
        from_attributes = True
        use_enum_values = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}


class ConversationWithMessagesUnified(ConversationResponseUnified):
    """
    💬 Schema unificado para conversa com mensagens

    Extend a conversa base com lista de mensagens.
    """

    messages: List[MessageResponseUnified] = Field(
        default_factory=list, description="Lista de mensagens"
    )


# ✅ Schemas para listagem paginada
class AppointmentsListResponseUnified(BaseModel):
    """📅 Response unificado para lista de agendamentos"""

    appointments: List[UnifiedAppointmentResponse]
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
    """📅 Schema para criação de agendamentos - Nomenclatura brasileira padronizada"""

    user_id: int
    business_id: int
    service_id: Optional[int] = None
    data_agendamento: datetime = Field(
        alias="date_time", description="Data e hora do agendamento"
    )
    duracao_minutos: int = Field(
        alias="duration_minutes", default=60, description="Duração em minutos"
    )
    valor: float = Field(alias="price", default=0.0, description="Valor do serviço")
    observacoes: Optional[str] = Field(
        alias="notes", default=None, description="Observações do agendamento"
    )

    class Config:
        populate_by_name = True  # ✅ Aceita tanto data_agendamento quanto date_time
        from_attributes = True


class AppointmentUpdateRequest(BaseModel):
    """📅 Schema para atualização de agendamentos - Nomenclatura brasileira padronizada"""

    data_agendamento: Optional[datetime] = Field(
        alias="date_time", default=None, description="Data e hora do agendamento"
    )
    duracao_minutos: Optional[int] = Field(
        alias="duration_minutes", default=None, description="Duração em minutos"
    )
    valor: Optional[float] = Field(
        alias="price", default=None, description="Valor do serviço"
    )
    status: Optional[AppointmentStatus] = None
    observacoes: Optional[str] = Field(
        alias="notes", default=None, description="Observações do agendamento"
    )

    class Config:
        populate_by_name = True  # ✅ Aceita tanto data_agendamento quanto date_time
        from_attributes = True


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
        Transforma row de SQLAlchemy para dict compatível com UnifiedAppointmentResponse

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
                return "agendado"
            status_map = {
                "cancelled": "cancelado",
                "confirmed": "confirmado",
                "completed": "realizado",
                "pending": "pendente",
                "scheduled": "agendado",
                # Manter valores já corretos
                "agendado": "agendado",
                "confirmado": "confirmado",
                "realizado": "realizado",
                "cancelado": "cancelado",
                "pendente": "pendente",
            }
            return status_map.get(status.lower(), "agendado")

        # Acessar objeto Appointment se disponível
        appointment = safe_get(row, "Appointment")
        if appointment:
            # Row com objetos separados
            return {
                "id": appointment.id,
                "user_id": appointment.user_id,
                "business_id": appointment.business_id,
                "service_id": appointment.service_id,
                "date_time": appointment.date_time,
                "time_slot": (
                    appointment.date_time.strftime("%H:%M")
                    if appointment.date_time
                    else ""
                ),
                "duration_minutes": appointment.duration_minutes or 60,
                "price": float(appointment.price) if appointment.price else 0.0,
                "status": normalize_status(appointment.status),
                "notes": appointment.notes,
                "user_name": safe_get(row, "user_name", "cliente_nome", default=""),
                "user_phone": safe_get(
                    row, "user_phone", "cliente_telefone", default=""
                ),
                "user_email": safe_get(row, "user_email", "cliente_email"),
                "service_name": safe_get(
                    row, "service_name", "servico_nome", default=""
                ),
                "service_description": safe_get(
                    row, "service_description", "servico_descricao"
                ),
                "business_name": safe_get(row, "business_name", default=""),
                "created_at": appointment.created_at,
                "updated_at": appointment.updated_at,
            }
        else:
            # Row com colunas diretas
            return {
                "id": safe_get(row, "appointment_id", "id"),
                "user_id": safe_get(row, "user_id"),
                "business_id": safe_get(row, "business_id"),
                "service_id": safe_get(row, "service_id"),
                "date_time": safe_get(row, "date_time"),
                "time_slot": (
                    safe_get(row, "date_time").strftime("%H:%M")
                    if safe_get(row, "date_time")
                    else ""
                ),
                "duration_minutes": safe_get(row, "duration_minutes", default=60),
                "price": float(safe_get(row, "price", default=0.0)),
                "status": normalize_status(safe_get(row, "status")),
                "notes": safe_get(row, "notes"),
                "user_name": safe_get(row, "user_name", "cliente_nome", default=""),
                "user_phone": safe_get(
                    row, "user_phone", "cliente_telefone", default=""
                ),
                "user_email": safe_get(row, "user_email", "cliente_email"),
                "service_name": safe_get(
                    row, "service_name", "servico_nome", default=""
                ),
                "service_description": safe_get(
                    row, "service_description", "servico_descricao"
                ),
                "business_name": safe_get(row, "business_name", default=""),
                "created_at": safe_get(row, "created_at"),
                "updated_at": safe_get(row, "updated_at"),
            }

    @staticmethod
    def appointment_dict_to_unified(appointment_dict: dict) -> dict:
        """
        ✅ P001: Transforma dict de appointment para formato unificado

        Args:
            appointment_dict: Dict com dados do appointment (de ORM com relacionamentos)

        Returns:
            Dict compatível com UnifiedAppointmentResponse
        """
        return {
            "id": appointment_dict.get("id"),
            "user_id": appointment_dict.get("user_id"),
            "business_id": appointment_dict.get("business_id"),
            "service_id": appointment_dict.get("service_id"),
            "dateTime": (
                appointment_dict.get("date_time").isoformat()
                if appointment_dict.get("date_time")
                else None
            ),
            "status": appointment_dict.get("status", "agendado"),
            "notes": appointment_dict.get("notes", ""),
            "clientName": appointment_dict.get("user_name", ""),
            "clientPhone": appointment_dict.get("user_phone", ""),
            "businessName": appointment_dict.get("business_name", ""),
            "serviceName": appointment_dict.get("service_name", ""),
            "createdAt": (
                appointment_dict.get("created_at").isoformat()
                if appointment_dict.get("created_at")
                else None
            ),
            "updatedAt": (
                appointment_dict.get("updated_at").isoformat()
                if appointment_dict.get("updated_at")
                else None
            ),
        }

    @staticmethod
    def conversation_row_to_unified(row) -> dict:
        """
        Transforma row de SQLAlchemy para dict compatível com ConversationResponseUnified
        """
        return {
            "id": row.id,
            "user_id": row.user_id,
            "status": row.status or "active",
            "last_message_at": row.last_message_at,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "user_name": getattr(row, "user_name", ""),
            "user_phone": getattr(row, "user_phone", None),
            "total_messages": getattr(row, "total_messages", 0),
            "unread_messages": getattr(row, "unread_messages", 0),
            "last_message": getattr(row, "last_message", None),
        }


# CF001 - Funções utilitárias para conversão de naming
def convert_snake_to_camel(data: dict) -> dict:
    """CF001 - Converte dict snake_case para camelCase"""
    converted = {}
    for key, value in data.items():
        camel_key = key
        if "_" in key:
            parts = key.split("_")
            camel_key = parts[0] + "".join(word.capitalize() for word in parts[1:])
        converted[camel_key] = value
    return converted


def convert_camel_to_snake(data: dict) -> dict:
    """CF001 - Converte dict camelCase para snake_case"""
    import re

    converted = {}
    for key, value in data.items():
        snake_key = re.sub("([A-Z])", r"_\1", key).lower()
        converted[snake_key] = value
    return converted


# CF001 - Mapeamento dos 15 campos críticos
CF001_FIELD_MAPPING = {
    # Backend snake_case -> Frontend camelCase
    "date_time": "dateTime",
    "duration_minutes": "durationMinutes",
    "user_id": "userId",
    "business_id": "businessId",
    "service_id": "serviceId",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "last_message_at": "lastMessageAt",
    "message_type": "messageType",
    "conversation_id": "conversationId",
    "is_active": "isActive",
    "is_read": "isRead",
    "total_messages": "totalMessages",
    "unread_messages": "unreadMessages",
    "last_interaction": "lastInteraction",
}
