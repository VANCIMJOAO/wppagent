"""
Users Admin Routes - Endpoints para gerenciar usuários administradores
Implementação REAL com dados do PostgreSQL (tabela admin_users)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import logging

from app.database import get_db
from app.models.database import AdminUser
from app.auth.middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["admin-users"])


@router.get("")
@router.get("/")
async def list_admin_users(
    search: Optional[str] = Query(None, description="Buscar por nome ou email"),
    role: Optional[str] = Query(None, description="Filtrar por role"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Lista todos os usuários administradores com filtros opcionais
    
    Retorna usuários da tabela admin_users (usuários do dashboard)
    """
    try:
        logger.info(f"👥 Listando admin users - search: {search}, role: {role}, status: {status}")
        
        # Construir query
        query = select(AdminUser)
        
        # Aplicar filtros
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    AdminUser.username.ilike(search_pattern),
                    AdminUser.email.ilike(search_pattern),
                    AdminUser.full_name.ilike(search_pattern)
                )
            )
        
        # Filtro por status (is_active)
        if status:
            if status == 'ativo':
                query = query.where(AdminUser.is_active == True)
            elif status == 'inativo':
                query = query.where(AdminUser.is_active == False)
        
        # Ordenar por criação (mais recentes primeiro)
        query = query.order_by(AdminUser.created_at.desc())
        
        # Paginação
        query = query.limit(limit).offset(offset)
        
        # Executar query
        result = await db.execute(query)
        admin_users = result.scalars().all()
        
        # Contar total
        count_query = select(func.count(AdminUser.id))
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.where(
                or_(
                    AdminUser.username.ilike(search_pattern),
                    AdminUser.email.ilike(search_pattern),
                    AdminUser.full_name.ilike(search_pattern)
                )
            )
        if status:
            if status == 'ativo':
                count_query = count_query.where(AdminUser.is_active == True)
            elif status == 'inativo':
                count_query = count_query.where(AdminUser.is_active == False)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        logger.info(f"✅ {len(admin_users)} admin users encontrados (total: {total})")
        
        # Mapear para formato do frontend
        users_data = [
            {
                'id': user.id,
                'nome': user.full_name or user.username,
                'name': user.full_name or user.username,
                'email': user.email,
                'username': user.username,
                'role': 'admin' if user.is_super_admin else 'operator',
                'status': 'ativo' if user.is_active else 'inativo',
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'ultima_atividade': user.last_login.isoformat() if user.last_login else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active,
                'is_super_admin': user.is_super_admin
            }
            for user in admin_users
        ]
        
        return {
            "success": True,
            "data": users_data,
            "users": users_data,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + len(users_data)) < total
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar admin users: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar usuários: {str(e)}"
        )


@router.get("/{user_id}")
async def get_admin_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Buscar usuário admin específico por ID"""
    try:
        logger.info(f"🔍 Buscando admin user {user_id}")
        
        result = await db.execute(
            select(AdminUser).where(AdminUser.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        logger.info(f"✅ Admin user {user_id} encontrado")
        
        return {
            "success": True,
            "data": {
                'id': user.id,
                'nome': user.full_name or user.username,
                'name': user.full_name or user.username,
                'email': user.email,
                'username': user.username,
                'role': 'admin' if user.is_super_admin else 'operator',
                'status': 'ativo' if user.is_active else 'inativo',
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'ultima_atividade': user.last_login.isoformat() if user.last_login else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active,
                'is_super_admin': user.is_super_admin
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar admin user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Estatísticas (bonus)
@router.get("/stats/summary")
async def get_users_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Estatísticas dos usuários admin"""
    try:
        logger.info("📊 Buscando estatísticas de admin users")
        
        # Total geral
        total_result = await db.execute(select(func.count(AdminUser.id)))
        total = total_result.scalar()
        
        # Total ativos
        active_result = await db.execute(
            select(func.count(AdminUser.id)).where(AdminUser.is_active == True)
        )
        active = active_result.scalar()
        
        # Total super admins
        super_admin_result = await db.execute(
            select(func.count(AdminUser.id)).where(AdminUser.is_super_admin == True)
        )
        super_admins = super_admin_result.scalar()
        
        logger.info(f"✅ Estatísticas: {total} total, {active} ativos, {super_admins} super admins")
        
        return {
            "success": True,
            "data": {
                "total": total,
                "active": active,
                "inactive": total - active,
                "super_admins": super_admins,
                "operators": total - super_admins
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

