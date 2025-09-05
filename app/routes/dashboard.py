"""
📊 API REST - Dashboard
=======================

Endpoints REST para alimentar o Dashboard com dados dos callbacks.

Funcionalidades:
- Lista de clientes/usuários
- Estatísticas mensais e relatórios
- Exportação de dados
- Dados agregados para gráficos
- Autenticação JWT obrigatória

Autor: Claude AI
Status: Implementação crítica para Dashboard Callbacks
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.database import User, Conversation, Message, Appointment
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Schemas Pydantic
class ClientResponse(BaseModel):
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


class ClientStatsResponse(BaseModel):
    total_clients: int
    active_clients: int  # últimos 7 dias
    new_clients: int     # últimos 30 dias
    avg_messages: float
    
    class Config:
        from_attributes = True


class MonthlyStatsResponse(BaseModel):
    month: str
    year: int
    total_conversations: int
    total_messages: int
    total_appointments: int
    revenue: float
    new_clients: int
    
    class Config:
        from_attributes = True


# Router
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/clients", response_model=List[ClientResponse])
async def get_clients(
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    search: Optional[str] = Query(None, description="Busca por nome, telefone ou email"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Lista clientes/usuários com suas estatísticas.
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
        
        # Aplicar paginação
        query = query.order_by(desc(User.created_at)).offset(offset).limit(limit)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        # Construir resposta com estatísticas para cada usuário
        clients = []
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
            last_contact_result = await db.execute(
                select(func.max(Conversation.last_message_at))
                .where(Conversation.user_id == user.id)
            )
            last_contact = last_contact_result.scalar()
            
            # Buscar estatísticas de agendamentos
            appt_stats = await db.execute(
                select(
                    func.count(Appointment.id).label('total'),
                    func.count(Appointment.id).filter(Appointment.status == 'confirmed').label('confirmed'),
                    func.count(Appointment.id).filter(Appointment.status == 'cancelled').label('cancelled'),
                    func.sum(Appointment.price).label('total_spent')
                )
                .where(Appointment.user_id == user.id)
            )
            appt_data = appt_stats.first()
            
            client = ClientResponse(
                id=user.id,
                nome=user.nome,
                telefone=user.telefone,
                email=user.email,
                created_at=user.created_at,
                updated_at=user.updated_at,
                total_conversations=total_conversations,
                total_messages=total_messages,
                total_appointments=appt_data.total or 0,
                confirmed_appointments=appt_data.confirmed or 0,
                cancelled_appointments=appt_data.cancelled or 0,
                total_spent=float(appt_data.total_spent or 0),
                last_contact=last_contact
            )
            clients.append(client)
        
        logger.info(f"Retornando {len(clients)} clientes para dashboard")
        return clients
        
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/clients/stats", response_model=ClientStatsResponse)
async def get_client_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Busca estatísticas gerais dos clientes.
    """
    try:
        # Total de clientes
        total_result = await db.execute(
            select(func.count(User.id))
            .where(
                and_(
                    User.nome.is_not(None),
                    User.nome != "",
                    ~User.nome.like("%[DELETED]%")
                )
            )
        )
        total_clients = total_result.scalar() or 0
        
        # Clientes ativos (últimos 7 dias)
        week_ago = datetime.now() - timedelta(days=7)
        active_result = await db.execute(
            select(func.count(User.id.distinct()))
            .select_from(User.join(Conversation, User.id == Conversation.user_id))
            .where(
                and_(
                    User.nome.is_not(None),
                    User.nome != "",
                    ~User.nome.like("%[DELETED]%"),
                    Conversation.last_message_at >= week_ago
                )
            )
        )
        active_clients = active_result.scalar() or 0
        
        # Novos clientes (últimos 30 dias)
        month_ago = datetime.now() - timedelta(days=30)
        new_result = await db.execute(
            select(func.count(User.id))
            .where(
                and_(
                    User.nome.is_not(None),
                    User.nome != "",
                    ~User.nome.like("%[DELETED]%"),
                    User.created_at >= month_ago
                )
            )
        )
        new_clients = new_result.scalar() or 0
        
        # Média de mensagens por usuário
        avg_result = await db.execute(
            select(func.avg(func.count(Message.id)))
            .select_from(Message)
            .join(User, Message.user_id == User.id)
            .where(
                and_(
                    User.nome.is_not(None),
                    User.nome != "",
                    ~User.nome.like("%[DELETED]%")
                )
            )
            .group_by(Message.user_id)
        )
        avg_messages = float(avg_result.scalar() or 0)
        
        stats = ClientStatsResponse(
            total_clients=total_clients,
            active_clients=active_clients,
            new_clients=new_clients,
            avg_messages=avg_messages
        )
        
        logger.info(f"Estatísticas de clientes calculadas: {stats.dict()}")
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas de clientes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/stats/monthly", response_model=List[MonthlyStatsResponse])
async def get_monthly_stats(
    months: int = Query(12, ge=1, le=24, description="Número de meses para retornar"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Estatísticas mensais para relatórios.
    """
    try:
        # Calcular data de início
        start_date = datetime.now() - timedelta(days=months * 30)
        
        # Query para estatísticas mensais (usando SQL raw por complexidade)
        monthly_query = text("""
            SELECT 
                EXTRACT(MONTH FROM u.created_at) as month,
                EXTRACT(YEAR FROM u.created_at) as year,
                COUNT(DISTINCT c.id) as total_conversations,
                COUNT(DISTINCT m.id) as total_messages,
                COUNT(DISTINCT a.id) as total_appointments,
                COALESCE(SUM(a.price), 0) as revenue,
                COUNT(DISTINCT u.id) as new_clients
            FROM users u
            LEFT JOIN conversations c ON u.id = c.user_id 
                AND c.created_at >= :start_date
            LEFT JOIN messages m ON u.id = m.user_id 
                AND m.created_at >= :start_date
            LEFT JOIN appointments a ON u.id = a.user_id 
                AND a.created_at >= :start_date
            WHERE u.created_at >= :start_date
                AND u.nome IS NOT NULL 
                AND u.nome != ''
                AND u.nome NOT LIKE '%[DELETED]%'
            GROUP BY EXTRACT(YEAR FROM u.created_at), EXTRACT(MONTH FROM u.created_at)
            ORDER BY year DESC, month DESC
            LIMIT :limit_months
        """)
        
        result = await db.execute(
            monthly_query, 
            {
                "start_date": start_date,
                "limit_months": months
            }
        )
        
        monthly_data = []
        for row in result:
            stats = MonthlyStatsResponse(
                month=f"{int(row.month):02d}",
                year=int(row.year),
                total_conversations=int(row.total_conversations or 0),
                total_messages=int(row.total_messages or 0), 
                total_appointments=int(row.total_appointments or 0),
                revenue=float(row.revenue or 0),
                new_clients=int(row.new_clients or 0)
            )
            monthly_data.append(stats)
        
        logger.info(f"Retornando estatísticas mensais para {len(monthly_data)} meses")
        return monthly_data
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas mensais: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/reports/export")
async def export_report(
    type: str = Query(..., description="Tipo de relatório: clients, conversations, appointments"),
    format: str = Query("json", description="Formato: json, csv"),
    start_date: Optional[date] = Query(None, description="Data inicial"),
    end_date: Optional[date] = Query(None, description="Data final"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Exporta relatórios em diferentes formatos.
    """
    try:
        # Validar tipo de relatório
        if type not in ["clients", "conversations", "appointments"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de relatório inválido. Use: clients, conversations, appointments"
            )
        
        # Definir datas padrão se não fornecidas
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now().date()
        
        data = []
        
        if type == "clients":
            # Exportar dados de clientes
            result = await db.execute(
                select(User)
                .where(
                    and_(
                        User.nome.is_not(None),
                        User.nome != "",
                        ~User.nome.like("%[DELETED]%"),
                        User.created_at >= start_date,
                        User.created_at <= end_date
                    )
                )
                .order_by(desc(User.created_at))
            )
            users = result.scalars().all()
            
            for user in users:
                data.append({
                    "id": user.id,
                    "nome": user.nome,
                    "telefone": user.telefone,
                    "email": user.email,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                })
        
        elif type == "conversations":
            # Exportar dados de conversas
            result = await db.execute(
                select(Conversation)
                .join(User, Conversation.user_id == User.id)
                .where(
                    and_(
                        Conversation.created_at >= start_date,
                        Conversation.created_at <= end_date,
                        User.nome.is_not(None),
                        User.nome != "",
                        ~User.nome.like("%[DELETED]%")
                    )
                )
                .order_by(desc(Conversation.created_at))
            )
            conversations = result.scalars().all()
            
            for conv in conversations:
                data.append({
                    "id": conv.id,
                    "user_id": conv.user_id,
                    "status": conv.status,
                    "created_at": conv.created_at.isoformat(),
                    "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None
                })
        
        elif type == "appointments":
            # Exportar dados de agendamentos
            result = await db.execute(
                select(Appointment)
                .join(User, Appointment.user_id == User.id)
                .where(
                    and_(
                        Appointment.created_at >= start_date,
                        Appointment.created_at <= end_date,
                        User.nome.is_not(None),
                        User.nome != "",
                        ~User.nome.like("%[DELETED]%")
                    )
                )
                .order_by(desc(Appointment.created_at))
            )
            appointments = result.scalars().all()
            
            for appt in appointments:
                data.append({
                    "id": appt.id,
                    "user_id": appt.user_id,
                    "date_time": appt.date_time.isoformat(),
                    "status": appt.status,
                    "price": float(appt.price) if appt.price else 0.0,
                    "notes": appt.notes,
                    "created_at": appt.created_at.isoformat()
                })
        
        logger.info(f"Exportando {len(data)} registros do tipo '{type}' em formato '{format}'")
        
        # Por enquanto retornamos apenas JSON
        # TODO: Implementar exportação CSV se necessário
        if format == "csv":
            # Placeholder para implementação futura de CSV
            return {"message": "Exportação CSV em desenvolvimento", "data": data}
        
        return {
            "type": type,
            "format": format,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_records": len(data),
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Erro ao exportar relatório: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )
