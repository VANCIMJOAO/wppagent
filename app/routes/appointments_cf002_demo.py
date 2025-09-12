"""
🔧 CF002 - Demo Routes para Response Wrapper Padronizado
=======================================================

Demonstra o antes e depois da padronização automática de responses.
Middleware aplica formato {success, data, error} automaticamente.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter(prefix="/appointments-demo", tags=["CF002 Demo"])


@router.get("/before")
async def appointments_before_cf002(db: AsyncSession = Depends(get_db)):
    """
    ANTES CF002 - Resposta sem padronização
    
    Problema: Estrutura inconsistente entre endpoints
    - Alguns retornam {appointments: [...], count: 10}
    - Outros retornam {data: [...], total: 10} 
    - Frontend precisa tratar cada caso específico
    """
    # Simula resposta inconsistente do padrão antigo
    return {
        "appointments": [
            {
                "id": 1,
                "user_id": 123,
                "date_time": "2025-09-12T14:00:00Z",
                "status": "agendado"
            },
            {
                "id": 2, 
                "user_id": 456,
                "date_time": "2025-09-12T15:00:00Z",
                "status": "confirmado"
            }
        ],
        "count": 2,
        "status": "ok",
        "message": "Success",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/after")  
async def appointments_after_cf002(db: AsyncSession = Depends(get_db)):
    """
    DEPOIS CF002 - Middleware aplica wrapper automaticamente
    
    Solução: Middleware converte automaticamente para:
    {
        "success": true,
        "data": {dados_originais},
        "error": null
    }
    
    Frontend sempre sabe onde encontrar os dados: result.data
    """
    # Retorna dados normalmente - middleware converte automaticamente
    appointments_data = {
        "appointments": [
            {
                "id": 1,
                "userId": 123,  # CF001 - camelCase automático
                "dateTime": "2025-09-12T14:00:00Z",
                "status": "agendado"
            },
            {
                "id": 2,
                "userId": 456,  # CF001 - camelCase automático  
                "dateTime": "2025-09-12T15:00:00Z",
                "status": "confirmado"
            }
        ],
        "total": 2,
        "page": 1,
        "per_page": 10,
        "has_next": False
    }
    
    return appointments_data


@router.get("/error-demo")
async def error_demo_cf002():
    """
    CF002 - Demonstra padronização automática de erros
    
    HTTPException é automaticamente convertida para:
    {
        "success": false,
        "data": null, 
        "error": "Appointment not found"
    }
    """
    raise HTTPException(
        status_code=404, 
        detail="Appointment not found"
    )


@router.get("/validation-error-demo")
async def validation_error_demo_cf002():
    """CF002 - Demonstra erro de validação padronizado"""
    raise HTTPException(
        status_code=400,
        detail="Invalid appointment data: date_time is required"
    )


@router.get("/server-error-demo")
async def server_error_demo_cf002():
    """CF002 - Demonstra erro interno padronizado"""
    # Simula erro interno
    raise HTTPException(
        status_code=500,
        detail="Internal server error: Database connection failed"
    )


@router.post("/create-demo")
async def create_appointment_demo_cf002(appointment_data: Dict[str, Any]):
    """
    CF002 - Demonstra POST com wrapper padronizado
    
    Response automático:
    {
        "success": true,
        "data": {appointment_created},
        "error": null  
    }
    """
    # Simula criação de appointment
    created_appointment = {
        "id": 999,
        "userId": appointment_data.get("userId", 123),
        "dateTime": appointment_data.get("dateTime", "2025-09-12T16:00:00Z"),
        "status": "agendado",
        "createdAt": datetime.now().isoformat()
    }
    
    return {
        "appointment": created_appointment,
        "message": "Appointment created successfully"
    }
