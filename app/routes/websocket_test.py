#!/app/routes/websocket_test.py
"""
Rotas de teste para WebSocket em tempo real
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime

from app.auth.middleware import get_current_user
from app.services.websocket_manager import websocket_manager

router = APIRouter()

@router.post("/test-websocket-broadcast")
async def test_websocket_broadcast(
    message: str,
    event_type: str = "test_message",
    topic: str = "dashboard",
    current_user: Dict = Depends(get_current_user)
):
    """
    Endpoint de teste para broadcasting WebSocket
    """
    try:
        # Criar evento de teste
        test_event = {
            "event_type": event_type,
            "data": {
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "user": current_user.get("email", current_user.get("sub", "unknown")),
                "test": True
            },
            "timestamp": datetime.now().isoformat()
        }

        # Broadcast para o tópico especificado
        await websocket_manager.broadcast_to_topic(topic, test_event)
        
        return {
            "success": True,
            "message": f"Evento de teste enviado para tópico '{topic}'",
            "event": test_event,
            "connections": websocket_manager.get_topic_connections_count(topic)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar evento de teste: {str(e)}")

@router.post("/test-appointment-event")
async def test_appointment_event(
    appointment_id: int = 123,
    action: str = "created",
    current_user: Dict = Depends(get_current_user)
):
    """
    Simular evento de agendamento para teste
    """
    try:
        event_type = f"appointment_{action}"
        
        # Simular dados de agendamento
        appointment_data = {
            "id": appointment_id,
            "client_name": "Cliente Teste",
            "service_name": "Serviço Teste", 
            "appointment_date": "2024-01-15T14:30:00",
            "status": "confirmado" if action == "created" else "atualizado",
            "created_by": current_user.get("email", current_user.get("sub", "unknown")),
            "test": True
        }

        # Eventos para diferentes tópicos
        events_to_send = [
            {
                "topic": "appointments",
                "event": {
                    "event_type": event_type,
                    "data": appointment_data,
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "topic": "dashboard", 
                "event": {
                    "event_type": "dashboard_stats_updated",
                    "data": {
                        "appointments_today": 5,
                        "new_appointment": appointment_data,
                        "updated_at": datetime.now().isoformat()
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }
        ]

        results = []
        for item in events_to_send:
            await websocket_manager.broadcast_to_topic(item["topic"], item["event"])
            results.append({
                "topic": item["topic"],
                "connections": websocket_manager.get_topic_connections_count(item["topic"])
            })
            
        return {
            "success": True,
            "message": f"Evento de agendamento '{action}' simulado",
            "appointment_data": appointment_data,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao simular evento de agendamento: {str(e)}")

@router.post("/test-dashboard-stats")
async def test_dashboard_stats_update(
    current_user: Dict = Depends(get_current_user)
):
    """
    Simular atualização de estatísticas do dashboard
    """
    try:
        # Simular estatísticas do dashboard
        stats_data = {
            "messages_today": 45,
            "conversations_today": 12,
            "appointments_today": 8,
            "new_clients_today": 3,
            "updated_at": datetime.now().isoformat(),
            "test": True
        }

        dashboard_event = {
            "event_type": "dashboard_stats_updated",
            "data": stats_data,
            "timestamp": datetime.now().isoformat()
        }

        # Broadcast para dashboard
        await websocket_manager.broadcast_to_topic("dashboard", dashboard_event)
        
        return {
            "success": True,
            "message": "Estatísticas do dashboard atualizadas",
            "stats": stats_data,
            "connections": websocket_manager.get_topic_connections_count("dashboard")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar stats: {str(e)}")

@router.post("/test-system-alert")
async def test_system_alert(
    alert_message: str,
    alert_type: str = "info",
    current_user: Dict = Depends(get_current_user)
):
    """
    Simular alerta do sistema
    """
    try:
        alert_event = {
            "event_type": "system_alert", 
            "data": {
                "message": alert_message,
                "alert_type": alert_type,
                "timestamp": datetime.now().isoformat(),
                "user": current_user.get("email", current_user.get("sub", "unknown")),
                "test": True
            },
            "timestamp": datetime.now().isoformat()
        }

        # Broadcast para todos os tópicos relevantes
        topics = ["dashboard", "system"]
        results = []
        
        for topic in topics:
            await websocket_manager.broadcast_to_topic(topic, alert_event)
            results.append({
                "topic": topic,
                "connections": websocket_manager.get_topic_connections_count(topic)
            })
        
        return {
            "success": True,
            "message": "Alerta do sistema enviado",
            "alert": alert_event,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar alerta: {str(e)}")

@router.get("/websocket-status")
async def get_websocket_status(current_user: Dict = Depends(get_current_user)):
    """
    Status atual do sistema WebSocket
    """
    try:
        status = {
            "active_connections": websocket_manager.get_active_connections_count(),
            "topic_stats": {},
            "recent_events": websocket_manager.get_recent_events(limit=10),
            "uptime": websocket_manager.get_uptime(),
            "timestamp": datetime.now().isoformat()
        }

        # Stats por tópico
        topics = ["dashboard", "appointments", "conversations", "clients", "system"]
        for topic in topics:
            status["topic_stats"][topic] = {
                "connections": websocket_manager.get_topic_connections_count(topic),
                "subscribers": websocket_manager.get_topic_subscribers(topic)
            }

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")
