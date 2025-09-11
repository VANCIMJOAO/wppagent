"""
🔄 Exemplo de Migração para Novos Response Schemas - C002
========================================================

Este arquivo demonstra como migrar endpoints existentes para usar
o novo padrão ApiResponse<T> com estrutura {success, data, error}.

Autor: Claude AI
Data: 2025-09-11
Status: Implementação C002 - Exemplo de Migração
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from pydantic import BaseModel, Field

# ✅ Novos imports para padrão C002
from app.schemas.response import ApiResponse, CommonResponses, PaginatedResponse
from app.decorators.response_wrapper import api_response_wrapper, created_response, paginated_response
from app.utils.http_status import HTTPStatus

from app.database import get_db
from app.models.database import User, Conversation, Message, Appointment, Service
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.auth.middleware import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ========================================
# SCHEMAS MIGRADOS PARA NOVO PADRÃO
# ========================================

class ClientData(BaseModel):
    """Dados do cliente (sem wrapper ApiResponse)"""
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
    """Estatísticas de clientes (sem wrapper ApiResponse)"""
    total_clients: int
    active_clients: int  # últimos 7 dias
    new_clients: int     # últimos 30 dias
    avg_messages: float
    
    class Config:
        from_attributes = True


class CreateClientRequest(BaseModel):
    """Request para criação de cliente"""
    nome: str = Field(..., min_length=1, max_length=255)
    telefone: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')


# ========================================
# TYPE ALIASES PARA RESPONSES PADRONIZADOS
# ========================================

# ✅ Responses seguindo novo padrão
ClientResponse = ApiResponse[ClientData]
ClientListResponse = ApiResponse[List[ClientData]]
ClientStatsResponse = ApiResponse[ClientStatsData]

# Router para exemplos migrados
router = APIRouter(prefix="/dashboard/v2", tags=["dashboard-v2"])


# ========================================
# ENDPOINTS MIGRADOS - USANDO DECORADORES
# ========================================

@router.get("/clients", response_model=ClientListResponse)
@paginated_response()  # ✅ Decorador aplicado automaticamente
async def get_clients_v2(
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    search: Optional[str] = Query(None, description="Buscar por nome ou telefone"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    ✅ MIGRADO: Lista clientes com novo padrão ApiResponse
    
    Retorna: {success, data, error, meta}
    - success: true
    - data: [lista de clientes]
    - meta: {pagination, timing}
    """
    try:
        # Query base
        query = select(User)
        
        # Filtro de busca
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    User.nome.ilike(search_term),
                    User.telefone.ilike(search_term)
                )
            )
        
        # Count total para paginação
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Aplicar paginação
        query = query.offset(offset).limit(limit).order_by(desc(User.created_at))
        
        # Executar query
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Converter para ClientData
        clients_data = []
        for user in users:
            # Calcular estatísticas (simplificado para exemplo)
            client_data = ClientData(
                id=user.id,
                nome=user.nome,
                telefone=user.telefone,
                email=user.email,
                created_at=user.created_at,
                updated_at=user.updated_at,
                total_conversations=0,  # TODO: calcular
                total_messages=0,       # TODO: calcular
                total_appointments=0,   # TODO: calcular
                confirmed_appointments=0,
                cancelled_appointments=0,
                total_spent=0.0,
                last_contact=None
            )
            clients_data.append(client_data)
        
        # ✅ O decorador automaticamente cria ApiResponse.paginated_response()
        return clients_data, total, limit, offset
        
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {e}")
        # ✅ O decorador automaticamente converte exceções em ApiResponse.error_response()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar clientes"
        )


@router.get("/clients/{client_id}", response_model=ClientResponse)
@api_response_wrapper()  # ✅ Wrapper básico
async def get_client_by_id_v2(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    ✅ MIGRADO: Busca cliente por ID com novo padrão
    
    Retorna: {success, data, error, meta}
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
        
        # Converter para ClientData
        client_data = ClientData(
            id=user.id,
            nome=user.nome,
            telefone=user.telefone,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            # Estatísticas calculadas aqui...
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


@router.post("/clients", response_model=ClientResponse)
@created_response()  # ✅ Decorador para status 201
async def create_client_v2(
    request: CreateClientRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    ✅ MIGRADO: Cria novo cliente com novo padrão
    
    Retorna: {success, data, error, meta} com status 201
    """
    try:
        # Verificar se cliente já existe
        existing_query = select(User).where(User.telefone == request.telefone)
        existing_result = await db.execute(existing_query)
        existing_user = existing_result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cliente com telefone {request.telefone} já existe"
            )
        
        # Criar novo cliente
        new_user = User(
            nome=request.nome,
            telefone=request.telefone,
            email=request.email,
            created_at=datetime.utcnow()
        )
        
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        # Converter para ClientData
        client_data = ClientData(
            id=new_user.id,
            nome=new_user.nome,
            telefone=new_user.telefone,
            email=new_user.email,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
        )
        
        # ✅ O decorador automaticamente cria ApiResponse.success_response() com status 201
        return client_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar cliente: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar cliente"
        )


@router.get("/stats", response_model=ClientStatsResponse)
@api_response_wrapper(measure_time=True)  # ✅ Com medição de tempo
async def get_client_stats_v2(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    ✅ MIGRADO: Estatísticas de clientes com novo padrão
    
    Retorna: {success, data, error, meta}
    - meta.execution_time_ms: tempo de execução
    """
    try:
        # Contar clientes
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
        
        # Média de mensagens (placeholder)
        avg_messages = 0.0  # TODO: calcular real
        
        stats_data = ClientStatsData(
            total_clients=total_clients,
            active_clients=active_clients,
            new_clients=new_clients,
            avg_messages=avg_messages
        )
        
        # ✅ O decorador automaticamente adiciona timing em meta.execution_time_ms
        return stats_data
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao calcular estatísticas"
        )


# ========================================
# ENDPOINTS MANUAIS - SEM DECORADORES
# ========================================

@router.get("/clients/manual", response_model=ClientListResponse)
async def get_clients_manual_v2(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    ✅ MIGRADO: Exemplo manual sem decoradores
    
    Demonstra como criar ApiResponse manualmente quando necessário.
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
        
        return ApiResponse.paginated_response(
            data=clients_data,
            total=total,
            limit=limit,
            offset=offset,
            execution_time_ms=execution_time_ms
        )
        
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {e}")
        
        # ✅ Criar error response manualmente
        return CommonResponses.internal_error(
            message="Erro interno ao buscar clientes"
        )


# ========================================
# COMPARAÇÃO: ANTES vs DEPOIS
# ========================================

# ❌ ANTES (padrão antigo - inconsistente):
"""
GET /dashboard/clients
{
  "id": 1,
  "nome": "João",
  "telefone": "+5511999999999"
}

POST /dashboard/clients  
{
  "message": "Cliente criado com sucesso",
  "client_id": 123
}

GET /dashboard/stats
{
  "total_clients": 100,
  "active_clients": 80
}

// Erro inconsistente
{
  "detail": "Cliente não encontrado"
}
"""

# ✅ DEPOIS (padrão C002 - consistente):
"""
GET /dashboard/v2/clients
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

POST /dashboard/v2/clients (201 Created)
{
  "success": true,
  "data": {
    "id": 123,
    "nome": "Maria",
    "telefone": "+5511888888888"
  },
  "error": null,
  "meta": {
    "timestamp": "2025-09-11T16:45:01.456Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440001", 
    "execution_time_ms": 89,
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
