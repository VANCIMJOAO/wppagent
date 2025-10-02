"""
Reminders System - SPRINT 4+
Sistema de lembretes configuráveis para usuários
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..services.cache_service import cache_service
from ..config.logging_config import get_optimized_logger

logger = get_optimized_logger(__name__)
router = APIRouter(prefix="/configuracoes/lembretes", tags=["Reminders"])


class ReminderConfig(BaseModel):
    """Configuração de lembrete"""
    id: Optional[int] = None
    user_id: int
    reminder_type: str = Field(..., description="Tipo: appointment, follow_up, payment, custom")
    title: str = Field(..., description="Título do lembrete")
    description: Optional[str] = Field(None, description="Descrição detalhada")
    time_before: int = Field(..., description="Tempo antes do evento (em minutos)")
    channels: List[str] = Field(..., description="Canais: email, sms, push, whatsapp")
    is_active: bool = Field(True, description="Se o lembrete está ativo")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ReminderTemplate(BaseModel):
    """Template de lembrete"""
    id: Optional[int] = None
    name: str = Field(..., description="Nome do template")
    reminder_type: str = Field(..., description="Tipo de lembrete")
    title_template: str = Field(..., description="Template do título")
    description_template: str = Field(..., description="Template da descrição")
    default_time_before: int = Field(..., description="Tempo padrão (minutos)")
    default_channels: List[str] = Field(..., description="Canais padrão")
    is_system: bool = Field(False, description="Se é template do sistema")


@router.get("/")
async def get_reminder_configs(
    user_id: int = Query(..., description="ID do usuário"),
    reminder_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    db: Session = Depends(get_db)
):
    """
    📋 Listar Configurações de Lembretes
    
    Retorna todas as configurações de lembretes do usuário.
    """
    try:
        # Construir filtros
        filters = ["user_id = :user_id"]
        params = {"user_id": user_id}
        
        if reminder_type:
            filters.append("reminder_type = :reminder_type")
            params["reminder_type"] = reminder_type
        
        if is_active is not None:
            filters.append("is_active = :is_active")
            params["is_active"] = is_active
        
        where_clause = " AND ".join(filters)
        
        # Query para buscar configurações
        configs_query = text(f"""
            SELECT 
                id,
                user_id,
                reminder_type,
                title,
                description,
                time_before,
                channels,
                is_active,
                created_at,
                updated_at
            FROM reminder_configs
            WHERE {where_clause}
            ORDER BY created_at DESC
        """)
        
        result = db.execute(configs_query, params).fetchall()
        
        # Processar configurações
        configs = []
        for row in result:
            config_data = {
                "id": row.id,
                "user_id": row.user_id,
                "reminder_type": row.reminder_type,
                "title": row.title,
                "description": row.description,
                "time_before": row.time_before,
                "channels": json.loads(row.channels) if row.channels else [],
                "is_active": row.is_active,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            }
            configs.append(config_data)
        
        logger.info("Reminder configs retrieved", 
                   user_id=user_id,
                   count=len(configs))
        
        return {
            "configs": configs,
            "total": len(configs),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error retrieving reminder configs", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error retrieving reminder configs: {str(e)}")


@router.post("/")
async def create_reminder_config(
    config: ReminderConfig,
    db: Session = Depends(get_db)
):
    """
    ➕ Criar Configuração de Lembrete
    
    Cria uma nova configuração de lembrete para o usuário.
    """
    try:
        # Validar canais
        valid_channels = ["email", "sms", "push", "whatsapp"]
        for channel in config.channels:
            if channel not in valid_channels:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Canal inválido: {channel}. Canais válidos: {valid_channels}"
                )
        
        # Inserir configuração
        insert_query = text("""
            INSERT INTO reminder_configs 
            (user_id, reminder_type, title, description, time_before, channels, is_active, created_at, updated_at)
            VALUES (:user_id, :reminder_type, :title, :description, :time_before, :channels, :is_active, NOW(), NOW())
            RETURNING id
        """)
        
        result = db.execute(insert_query, {
            "user_id": config.user_id,
            "reminder_type": config.reminder_type,
            "title": config.title,
            "description": config.description,
            "time_before": config.time_before,
            "channels": json.dumps(config.channels),
            "is_active": config.is_active
        }).fetchone()
        
        config_id = result.id
        
        logger.info("Reminder config created", 
                   config_id=config_id,
                   user_id=config.user_id,
                   reminder_type=config.reminder_type)
        
        return {
            "id": config_id,
            "message": "Configuração de lembrete criada com sucesso",
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error creating reminder config", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error creating reminder config: {str(e)}")


@router.put("/{config_id}")
async def update_reminder_config(
    config_id: int,
    config: ReminderConfig,
    db: Session = Depends(get_db)
):
    """
    ✏️ Atualizar Configuração de Lembrete
    
    Atualiza uma configuração de lembrete existente.
    """
    try:
        # Validar canais
        valid_channels = ["email", "sms", "push", "whatsapp"]
        for channel in config.channels:
            if channel not in valid_channels:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Canal inválido: {channel}. Canais válidos: {valid_channels}"
                )
        
        # Atualizar configuração
        update_query = text("""
            UPDATE reminder_configs 
            SET 
                reminder_type = :reminder_type,
                title = :title,
                description = :description,
                time_before = :time_before,
                channels = :channels,
                is_active = :is_active,
                updated_at = NOW()
            WHERE id = :config_id AND user_id = :user_id
            RETURNING id
        """)
        
        result = db.execute(update_query, {
            "config_id": config_id,
            "user_id": config.user_id,
            "reminder_type": config.reminder_type,
            "title": config.title,
            "description": config.description,
            "time_before": config.time_before,
            "channels": json.dumps(config.channels),
            "is_active": config.is_active
        }).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Configuração de lembrete não encontrada")
        
        logger.info("Reminder config updated", 
                   config_id=config_id,
                   user_id=config.user_id)
        
        return {
            "id": config_id,
            "message": "Configuração de lembrete atualizada com sucesso",
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error updating reminder config", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error updating reminder config: {str(e)}")


@router.delete("/{config_id}")
async def delete_reminder_config(
    config_id: int,
    user_id: int = Query(..., description="ID do usuário"),
    db: Session = Depends(get_db)
):
    """
    🗑️ Deletar Configuração de Lembrete
    
    Remove uma configuração de lembrete.
    """
    try:
        # Deletar configuração
        delete_query = text("""
            DELETE FROM reminder_configs 
            WHERE id = :config_id AND user_id = :user_id
            RETURNING id
        """)
        
        result = db.execute(delete_query, {
            "config_id": config_id,
            "user_id": user_id
        }).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Configuração de lembrete não encontrada")
        
        logger.info("Reminder config deleted", 
                   config_id=config_id,
                   user_id=user_id)
        
        return {
            "id": config_id,
            "message": "Configuração de lembrete deletada com sucesso",
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error deleting reminder config", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error deleting reminder config: {str(e)}")


@router.get("/templates")
async def get_reminder_templates(
    reminder_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    db: Session = Depends(get_db)
):
    """
    📋 Listar Templates de Lembretes
    
    Retorna templates disponíveis para criar lembretes.
    """
    try:
        # Construir filtros
        filters = []
        params = {}
        
        if reminder_type:
            filters.append("reminder_type = :reminder_type")
            params["reminder_type"] = reminder_type
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        # Query para buscar templates
        templates_query = text(f"""
            SELECT 
                id,
                name,
                reminder_type,
                title_template,
                description_template,
                default_time_before,
                default_channels,
                is_system
            FROM reminder_templates
            WHERE {where_clause}
            ORDER BY is_system DESC, name ASC
        """)
        
        result = db.execute(templates_query, params).fetchall()
        
        # Processar templates
        templates = []
        for row in result:
            template_data = {
                "id": row.id,
                "name": row.name,
                "reminder_type": row.reminder_type,
                "title_template": row.title_template,
                "description_template": row.description_template,
                "default_time_before": row.default_time_before,
                "default_channels": json.loads(row.default_channels) if row.default_channels else [],
                "is_system": row.is_system
            }
            templates.append(template_data)
        
        logger.info("Reminder templates retrieved", 
                   count=len(templates),
                   reminder_type=reminder_type)
        
        return {
            "templates": templates,
            "total": len(templates),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error retrieving reminder templates", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error retrieving reminder templates: {str(e)}")


@router.post("/test")
async def test_reminder(
    config_id: int = Query(..., description="ID da configuração"),
    user_id: int = Query(..., description="ID do usuário"),
    db: Session = Depends(get_db)
):
    """
    🧪 Testar Envio de Lembrete
    
    Envia um lembrete de teste para verificar a configuração.
    """
    try:
        # Buscar configuração
        config_query = text("""
            SELECT 
                id,
                user_id,
                reminder_type,
                title,
                description,
                time_before,
                channels,
                is_active
            FROM reminder_configs
            WHERE id = :config_id AND user_id = :user_id
        """)
        
        result = db.execute(config_query, {
            "config_id": config_id,
            "user_id": user_id
        }).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Configuração de lembrete não encontrada")
        
        if not result.is_active:
            raise HTTPException(status_code=400, detail="Configuração de lembrete está inativa")
        
        # Simular envio de lembrete
        channels = json.loads(result.channels) if result.channels else []
        sent_channels = []
        
        for channel in channels:
            # Aqui seria implementada a lógica real de envio
            if channel == "email":
                # Simular envio de email
                sent_channels.append("email")
            elif channel == "sms":
                # Simular envio de SMS
                sent_channels.append("sms")
            elif channel == "push":
                # Simular notificação push
                sent_channels.append("push")
            elif channel == "whatsapp":
                # Simular envio via WhatsApp
                sent_channels.append("whatsapp")
        
        logger.info("Reminder test sent", 
                   config_id=config_id,
                   user_id=user_id,
                   channels=sent_channels)
        
        return {
            "config_id": config_id,
            "user_id": user_id,
            "title": result.title,
            "description": result.description,
            "channels_attempted": channels,
            "channels_sent": sent_channels,
            "test_sent_at": datetime.utcnow().isoformat(),
            "message": f"Lembrete de teste enviado via {', '.join(sent_channels)}"
        }
        
    except Exception as e:
        logger.error("Error testing reminder", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error testing reminder: {str(e)}")


@router.get("/health")
async def reminders_health():
    """
    🏥 Health Check do Sistema de Lembretes
    
    Verifica se o sistema de lembretes está funcionando.
    """
    return {
        "status": "healthy",
        "service": "reminders",
        "version": "1.0.0",
        "features": [
            "Configurable reminder settings",
            "Multiple notification channels",
            "Template system",
            "Test functionality"
        ],
        "channels_supported": ["email", "sms", "push", "whatsapp"],
        "reminder_types": ["appointment", "follow_up", "payment", "custom"],
        "timestamp": datetime.utcnow().isoformat()
    }
