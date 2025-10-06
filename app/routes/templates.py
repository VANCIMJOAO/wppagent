"""
Templates Routes - Endpoints para gerenciar templates de mensagens WhatsApp
Implementação REAL com dados do PostgreSQL
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.database import get_db
from app.models.database import Template
from app.auth.middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])


# Schemas Pydantic
class TemplateCreate(BaseModel):
    name: str
    category: str
    language: str = 'pt-BR'
    content: str
    status: str = 'pending'
    variables: List[str] = []


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    variables: Optional[List[str]] = None
    rejection_reason: Optional[str] = None


@router.get("")
@router.get("/")
async def list_templates(
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Buscar por nome ou conteúdo"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Lista todos os templates com filtros opcionais
    
    Filtros disponíveis:
    - category: agendamento, lembrete, marketing, autenticacao, transacional
    - status: aprovado, pendente, rejeitado
    - search: busca por nome ou conteúdo
    """
    try:
        logger.info(f"📋 Listando templates - category: {category}, status: {status}, search: {search}")
        
        # Construir query
        query = select(Template)
        
        # Aplicar filtros
        if category:
            query = query.where(Template.category == category)
        if status:
            query = query.where(Template.status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Template.name.ilike(search_pattern),
                    Template.content.ilike(search_pattern)
                )
            )
        
        # Ordenar por criação (mais recentes primeiro)
        query = query.order_by(Template.created_at.desc())
        
        # Paginação
        query = query.limit(limit).offset(offset)
        
        # Executar query
        result = await db.execute(query)
        templates = result.scalars().all()
        
        # Contar total (para paginação)
        count_query = select(func.count(Template.id))
        if category:
            count_query = count_query.where(Template.category == category)
        if status:
            count_query = count_query.where(Template.status == status)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        logger.info(f"✅ {len(templates)} templates encontrados (total: {total})")
        
        return {
            "success": True,
            "data": [template.to_dict() for template in templates],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + len(templates)) < total
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar templates: {str(e)}"
        )


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Buscar template específico por ID"""
    try:
        logger.info(f"🔍 Buscando template {template_id}")
        
        result = await db.execute(
            select(Template).where(Template.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        logger.info(f"✅ Template {template_id} encontrado")
        return {
            "success": True,
            "data": template.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@router.post("/")
async def create_template(
    template_data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Criar novo template"""
    try:
        logger.info(f"➕ Criando template: {template_data.name}")
        
        # Criar novo template
        new_template = Template(
            name=template_data.name,
            category=template_data.category,
            language=template_data.language,
            content=template_data.content,
            status=template_data.status,
            variables=template_data.variables
        )
        
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        
        logger.info(f"✅ Template {new_template.id} criado com sucesso")
        
        return {
            "success": True,
            "data": new_template.to_dict(),
            "message": "Template criado com sucesso"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Erro ao criar template: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar template: {str(e)}"
        )


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Atualizar template existente"""
    try:
        logger.info(f"✏️ Atualizando template {template_id}")
        
        # Buscar template
        result = await db.execute(
            select(Template).where(Template.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        # Atualizar campos fornecidos
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        # Atualizar timestamps de aprovação/rejeição
        if template_data.status == 'aprovado':
            template.approved_at = datetime.now()
            template.rejected_at = None
            template.rejection_reason = None
        elif template_data.status == 'rejeitado':
            template.rejected_at = datetime.now()
            template.approved_at = None
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"✅ Template {template_id} atualizado")
        
        return {
            "success": True,
            "data": template.to_dict(),
            "message": "Template atualizado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Erro ao atualizar template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Deletar template"""
    try:
        logger.info(f"🗑️ Deletando template {template_id}")
        
        # Buscar template
        result = await db.execute(
            select(Template).where(Template.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        await db.delete(template)
        await db.commit()
        
        logger.info(f"✅ Template {template_id} deletado")
        
        return {
            "success": True,
            "message": "Template deletado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Erro ao deletar template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint de estatísticas (bonus)
@router.get("/stats/summary")
async def get_templates_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Estatísticas dos templates"""
    try:
        logger.info("📊 Buscando estatísticas de templates")
        
        # Total por status
        result = await db.execute(
            select(
                Template.status,
                func.count(Template.id).label('count')
            )
            .group_by(Template.status)
        )
        
        stats_by_status = {row.status: row.count for row in result}
        
        # Total por categoria
        result = await db.execute(
            select(
                Template.category,
                func.count(Template.id).label('count')
            )
            .group_by(Template.category)
        )
        
        stats_by_category = {row.category: row.count for row in result}
        
        # Total geral
        total_result = await db.execute(select(func.count(Template.id)))
        total = total_result.scalar()
        
        logger.info(f"✅ Estatísticas calculadas: {total} templates total")
        
        return {
            "success": True,
            "data": {
                "total": total,
                "by_status": stats_by_status,
                "by_category": stats_by_category
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

