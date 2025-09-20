"""
🧪 Rotas Públicas de Teste
==========================

Endpoints públicos para testes sem autenticação.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["Public Test"])


@router.get("/appointments")
async def get_test_appointments() -> Dict[str, Any]:
    """Endpoint de teste para appointments (sem autenticação)"""
    return {
        "success": True,
        "data": {
            "appointments": [
                {
                    "id": 1,
                    "client_name": "João Silva",
                    "service": "Consulta",
                    "date": "2025-09-20T10:00:00Z",
                    "status": "scheduled"
                },
                {
                    "id": 2,
                    "client_name": "Maria Santos",
                    "service": "Retorno",
                    "date": "2025-09-20T14:00:00Z",
                    "status": "confirmed"
                }
            ],
            "total": 2
        },
        "message": "Test appointments data",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/conversations")
async def get_test_conversations() -> Dict[str, Any]:
    """Endpoint de teste para conversations (sem autenticação)"""
    return {
        "success": True,
        "data": {
            "conversations": [
                {
                    "id": 1,
                    "client_name": "Ana Costa",
                    "last_message": "Olá, gostaria de agendar uma consulta",
                    "status": "active",
                    "unread_count": 2
                },
                {
                    "id": 2,
                    "client_name": "Carlos Lima",
                    "last_message": "Obrigado pela consulta!",
                    "status": "closed",
                    "unread_count": 0
                }
            ],
            "total": 2
        },
        "message": "Test conversations data",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/dashboard")
async def get_test_dashboard() -> Dict[str, Any]:
    """Endpoint de teste para dashboard (sem autenticação)"""
    return {
        "success": True,
        "data": {
            "stats": {
                "total_appointments": 15,
                "active_conversations": 8,
                "new_messages": 12,
                "revenue_today": 1250.50
            },
            "recent_activity": [
                {
                    "type": "appointment",
                    "description": "Nova consulta agendada",
                    "time": "10:30"
                },
                {
                    "type": "message",
                    "description": "Mensagem recebida de cliente",
                    "time": "10:15"
                }
            ]
        },
        "message": "Test dashboard data",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/analytics")
async def get_test_analytics() -> Dict[str, Any]:
    """Endpoint de teste para analytics (sem autenticação)"""
    return {
        "success": True,
        "data": {
            "metrics": {
                "appointments_today": 5,
                "conversations_today": 12,
                "response_time_avg": 2.5,
                "satisfaction_score": 4.8
            },
            "charts": {
                "appointments_by_hour": [2, 3, 1, 4, 2, 1, 0],
                "conversations_by_status": {"active": 8, "closed": 15, "pending": 3}
            }
        },
        "message": "Test analytics data",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/admin/debug-admin")
async def get_test_admin_debug() -> Dict[str, Any]:
    """Endpoint de teste para debug admin (sem autenticação)"""
    return {
        "success": True,
        "data": {
            "admin_info": {
                "username": "admin",
                "role": "administrator",
                "last_login": "2025-09-20T08:00:00Z",
                "permissions": ["read", "write", "admin"]
            },
            "system_status": "healthy",
            "database_connected": True,
            "redis_connected": True
        },
        "message": "Test admin debug data",
        "timestamp": datetime.now().isoformat()
    }
