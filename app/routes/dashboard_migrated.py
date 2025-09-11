"""
🔄 Migração Prática do Dashboard - C002
======================================

Este arquivo demonstra a migração prática de endpoints do dashboard
para o novo padrão ApiResponse<T> usando decoradores e middleware.

Autor: Claude AI
Data: 2025-09-11
Status: Implementação C002 - Migração Prática
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from pydantic import BaseModel, Field

# ✅ Imports do novo padrão C002
from app.schemas.response import ApiResponse, CommonResponses
from app.decorators.response_wrapper import api_response_wrapper, paginated_response, created_response
from app.utils.http_status import HTTPStatus

# Imports originais
from app.database import get_db
from app.models.database import User, Conversation, Message, Appointment, Service
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.auth.middleware import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ========================================
# SCHEMAS MIGRADOS PARA C002
# ========================================

class ClientData(BaseModel):
    """Dados do cliente (conteúdo para ApiResponse.data)"""
    id: int
    nome: Optional[str]
    telefone: Optional[str] 
    email: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Estatísticas calculadas
    total_conversations: int = 0
    total_messages: int = 0
    total_appointments: int = 0
    confirmed_appointments: int = 0
    cancelled_appointments: int = 0
    total_spent: float = 0.0
    last_contact: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ClientStatsData(BaseModel):
    """Estatísticas de clientes (conteúdo para ApiResponse.data)"""
    total_clients: int
    active_clients: int  # últimos 7 dias
    new_clients: int     # últimos 30 dias
    avg_messages: float
    retention_rate: float = 0.0
    growth_rate: float = 0.0
    
    class Config:
        from_attributes = True


# ✅ Type aliases para responses padronizados
ClientResponse = ApiResponse[ClientData]
ClientListResponse = ApiResponse[List[ClientData]]
ClientStatsResponse = ApiResponse[ClientStatsData]

# Router para endpoints migrados
router = APIRouter(prefix="/dashboard/migrated", tags=["dashboard-migrated-c002"])


# ========================================
# ENDPOINTS MIGRADOS - USANDO DECORADORES C002
# ========================================

@router.get("/clients", response_model=ClientListResponse)
@paginated_response()  # ✅ Decorador C002 para paginação
async def get_clients_migrated(
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    search: Optional[str] = Query(None, description="Busca por nome, telefone ou email"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    ✅ MIGRADO C002: Lista clientes com estrutura {success, data, error, meta}
    
    Retorna:
    {
      "success": true,
      "data": [array de clientes],
      "error": null,
      "meta": {
        "timestamp": "2025-09-11T16:45:00.123Z",
        "request_id": "uuid",
        "execution_time_ms": 150,
        "pagination": {
          "total": 100,
          "limit": 10,
          "offset": 0,
          "page": 1,
          "pages": 10,
          "has_next": true,
          "has_prev": false
        }
      }
    }
    """
    try:
        # Query base para usuários
        query = select(User).where(
            and_(
                User.nome.is_not(None),
                User.nome != "",
                ~User.nome.like("%[DELETED]%")
            )
        )
        
        # Aplicar filtro de busca se fornecido
        if search:
            search_filter = or_(
                User.nome.ilike(f"%{search}%"),
                User.telefone.ilike(f"%{search}%"), 
                User.email.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        # Count total para paginação
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Aplicar paginação
        query = query.order_by(desc(User.created_at)).offset(offset).limit(limit)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Construir resposta com estatísticas para cada usuário
        clients_data = []
        for user in users:
            # Buscar estatísticas de conversas
            conv_stats = await db.execute(
                select(func.count(Conversation.id))
                .where(Conversation.user_id == user.id)
            )
            total_conversations = conv_stats.scalar() or 0
            
            # Buscar estatísticas de mensagens
            msg_stats = await db.execute(
                select(func.count(Message.id))
                .where(Message.user_id == user.id)
            )
            total_messages = msg_stats.scalar() or 0
            
            # Buscar último contato
            last_contact_query = await db.execute(
                select(func.max(Message.created_at))
                .where(Message.user_id == user.id)
            )
            last_contact = last_contact_query.scalar()
            
            client_data = ClientData(
                id=user.id,
                nome=user.nome,
                telefone=user.telefone,
                email=user.email,
                created_at=user.created_at,
                updated_at=user.updated_at,
                total_conversations=total_conversations,
                total_messages=total_messages,
                total_appointments=0,  # TODO: calcular agendamentos
                confirmed_appointments=0,
                cancelled_appointments=0,
                total_spent=0.0,
                last_contact=last_contact
            )
            clients_data.append(client_data)
        
        # ✅ O decorador @paginated_response() automaticamente cria:
        # ApiResponse.paginated_response(data, total, limit, offset)
        return clients_data, total, limit, offset
        
    except Exception as e:
        logger.error(f"Erro ao buscar clientes migrado: {e}")
        # ✅ O decorador automaticamente converte exceções
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar clientes"
        )


@router.get("/clients/{client_id}", response_model=ClientResponse)
@api_response_wrapper()  # ✅ Decorador C002 básico
async def get_client_by_id_migrated(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    ✅ MIGRADO C002: Busca cliente por ID com estrutura padronizada
    
    Retorna:
    {
      "success": true,
      "data": {dados do cliente},
      "error": null,
      "meta": {
        "timestamp": "2025-09-11T16:45:00.123Z",
        "request_id": "uuid",
        "execution_time_ms": 89
      }
    }
    """
    try:
        # Buscar cliente
        query = select(User).where(User.id == client_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # ✅ O decorador automaticamente converte em ApiResponse.error_response()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente {client_id} não encontrado"
            )
        
        # Buscar estatísticas detalhadas
        conv_stats = await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user.id)
        )
        total_conversations = conv_stats.scalar() or 0
        
        msg_stats = await db.execute(
            select(func.count(Message.id))
            .where(Message.user_id == user.id)
        )
        total_messages = msg_stats.scalar() or 0
        
        client_data = ClientData(
            id=user.id,
            nome=user.nome,
            telefone=user.telefone,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            total_conversations=total_conversations,
            total_messages=total_messages,
        )
        
        # ✅ O decorador automaticamente cria ApiResponse.success_response()
        return client_data
        
    except HTTPException:
        raise  # Re-raise HTTPException para o decorador tratar
    except Exception as e:
        logger.error(f"Erro ao buscar cliente {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar cliente"
        )


@router.get("/stats", response_model=ClientStatsResponse)
@api_response_wrapper(measure_time=True)  # ✅ Com medição de tempo
async def get_client_stats_migrated(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    ✅ MIGRADO C002: Estatísticas de clientes com timing
    
    Retorna:
    {
      "success": true,
      "data": {estatísticas},
      "error": null,
      "meta": {
        "timestamp": "2025-09-11T16:45:00.123Z",
        "request_id": "uuid",
        "execution_time_ms": 245
      }
    }
    """
    try:
        # Contar clientes totais
        total_query = select(func.count(User.id))
        total_result = await db.execute(total_query)
        total_clients = total_result.scalar() or 0
        
        # Clientes ativos (últimos 7 dias)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_query = select(func.count(User.id)).where(
            User.updated_at >= seven_days_ago
        )
        active_result = await db.execute(active_query)
        active_clients = active_result.scalar() or 0
        
        # Novos clientes (últimos 30 dias)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_query = select(func.count(User.id)).where(
            User.created_at >= thirty_days_ago
        )
        new_result = await db.execute(new_query)
        new_clients = new_result.scalar() or 0
        
        # Calcular métricas avançadas
        retention_rate = (active_clients / total_clients * 100) if total_clients > 0 else 0
        growth_rate = (new_clients / (total_clients - new_clients) * 100) if (total_clients - new_clients) > 0 else 0
        
        # Média de mensagens por cliente
        avg_messages_query = select(func.avg(
            select(func.count(Message.id)).where(Message.user_id == User.id).scalar_subquery()
        ))
        avg_result = await db.execute(avg_messages_query)
        avg_messages = float(avg_result.scalar() or 0)
        
        stats_data = ClientStatsData(
            total_clients=total_clients,
            active_clients=active_clients,
            new_clients=new_clients,
            avg_messages=avg_messages,
            retention_rate=retention_rate,
            growth_rate=growth_rate
        )
        
        # ✅ O decorador automaticamente adiciona timing em meta.execution_time_ms
        return stats_data
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas migradas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao calcular estatísticas"
        )


# ========================================
# ENDPOINTS MANUAIS - DEMONSTRAÇÃO SEM DECORADORES
# ========================================

@router.get("/clients/manual", response_model=ClientListResponse)
async def get_clients_manual_migrated(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    ✅ MIGRADO C002: Exemplo manual sem decoradores
    
    Demonstra como criar ApiResponse manualmente quando necessário.
    Útil para casos onde você precisa de controle total sobre a response.
    """
    try:
        start_time = datetime.utcnow()
        
        # Buscar clientes
        query = select(User).offset(offset).limit(limit).order_by(desc(User.created_at))
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Count total
        count_query = select(func.count(User.id))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Converter para ClientData
        clients_data = [
            ClientData(
                id=user.id,
                nome=user.nome,
                telefone=user.telefone,
                email=user.email,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]
        
        # ✅ Criar response paginado manualmente
        execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        response = ApiResponse.paginated_response(
            data=clients_data,
            total=total,
            limit=limit,
            offset=offset,
            execution_time_ms=execution_time_ms
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao buscar clientes manual: {e}")
        
        # ✅ Criar error response manualmente
        return CommonResponses.internal_error(
            message="Erro interno ao buscar clientes"
        )


# ========================================
# COMPARAÇÃO: ANTES vs DEPOIS
# ========================================

"""
❌ ANTES (padrão antigo - inconsistente):

GET /dashboard/clients
[
  {
    "id": 1,
    "nome": "João",
    "telefone": "+5511999999999"
  }
]

POST /dashboard/clients
{
  "message": "Cliente criado com sucesso",
  "client_id": 123
}

// Erro inconsistente
{
  "detail": "Cliente não encontrado"
}

✅ DEPOIS (padrão C002 - consistente):

GET /dashboard/migrated/clients
{
  "success": true,
  "data": [
    {
      "id": 1,
      "nome": "João", 
      "telefone": "+5511999999999"
    }
  ],
  "error": null,
  "meta": {
    "timestamp": "2025-09-11T16:45:00.123Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "execution_time_ms": 150,
    "pagination": {
      "total": 100,
      "limit": 10,
      "offset": 0,
      "page": 1,
      "pages": 10,
      "has_next": true,
      "has_prev": false
    },
    "version": "1.0"
  }
}

// Erro padronizado
{
  "success": false,
  "data": null,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Cliente não encontrado",
    "field": null,
    "details": null
  },
  "meta": {
    "timestamp": "2025-09-11T16:45:02.789Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440002",
    "version": "1.0"
  }
}
"""
