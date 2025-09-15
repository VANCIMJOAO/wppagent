"""
🔌 Router WebSocket Real-Time Avançado
====================================

Router FastAPI otimizado para WebSocket com:
- Autenticação JWT robusta
- Gerenciamento de conexões inteligente
- Broadcasting por tópicos/salas
- Reconexão automática
- Monitoring em tempo real
- Integração com modelos de dados
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from ..auth.jwt_manager import SimpleJWTManager
from ..database import get_db
from ..models.database import Appointment, Conversation, Message, User
from ..services.realtime_websocket_manager import (
    RealtimeEventType,
    RealtimeWebSocketManager,
    get_realtime_manager,
)
from ..services.structured_apm import get_structured_logger
from ..utils.logger import get_logger

router = APIRouter()
logger = get_structured_logger(__name__)
jwt_manager = SimpleJWTManager()


class WebSocketAuthError(Exception):
    """Erro de autenticação WebSocket"""

    pass


async def get_websocket_user(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Token"),
    db: Session = Depends(get_db),
) -> User:
    """
    Autentica usuário WebSocket via JWT token

    Args:
        websocket: Instância WebSocket
        token: JWT token
        db: Sessão do banco de dados

    Returns:
        User: Usuário autenticado

    Raises:
        WebSocketAuthError: Erro de autenticação
    """
    try:
        # Decode JWT token
        payload = jwt_manager.verify_token(token)
        if not payload:
            raise WebSocketAuthError("Token inválido")

        user_id = payload.get("user_id")
        if not user_id:
            raise WebSocketAuthError("User ID não encontrado no token")

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise WebSocketAuthError("Usuário não encontrado")

        if not user.is_active:
            raise WebSocketAuthError("Usuário inativo")

        return user

    except Exception as e:
        logger.error(f"❌ Erro de autenticação WebSocket: {e}")
        raise WebSocketAuthError(f"Erro de autenticação: {e}")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Authentication token"),
    subscriptions: str = Query("", description="Comma-separated list of subscriptions"),
    room: str = Query(None, description="Room to join"),
    db: Session = Depends(get_db),
):
    """
    Endpoint principal WebSocket com autenticação JWT

    Query Parameters:
        - token: JWT token para autenticação
        - subscriptions: Lista de tópicos separados por vírgula (dashboard,appointments,messages)
        - room: Sala específica para entrar (opcional)

    Example:
        ws://localhost:8000/ws?token=eyJ0eXAi...&subscriptions=dashboard,messages&room=chat_123
    """
    manager = get_realtime_manager()
    connection_id = None
    user = None

    try:
        # Authenticate user
        try:
            user = await get_websocket_user(websocket, token, db)
        except WebSocketAuthError as e:
            await websocket.accept()
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "auth_error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            )
            await websocket.close(code=4001, reason="Authentication failed")
            return

        # Parse subscriptions
        subscription_list = [s.strip() for s in subscriptions.split(",") if s.strip()]

        # Get client IP and user agent
        client_ip = (
            getattr(websocket.client, "host", "unknown")
            if websocket.client
            else "unknown"
        )
        user_agent = websocket.headers.get("user-agent", "unknown")

        # Connect to WebSocket manager
        connection_id = await manager.connect(
            websocket=websocket,
            user_id=str(user.id),
            subscriptions=subscription_list,
            room=room,
            metadata={
                "user_name": user.nome,
                "user_email": user.email or "",
                "user_role": "user",
                "ip_address": client_ip,
                "user_agent": user_agent,
                "connected_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(
            f"🔌 WebSocket conectado: {user.nome} ({user.id}) -> {subscription_list}"
        )

        # Send initial data based on subscriptions
        await send_initial_data(connection_id, subscription_list, user, db, manager)

        # Handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Process client message
                await manager.handle_client_message(connection_id, message_data)

                # Handle specific message types
                await handle_specific_message_types(
                    connection_id, message_data, user, db, manager
                )

            except WebSocketDisconnect:
                logger.info(f"🔌 Cliente desconectado: {user.nome} ({user.id})")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON inválido recebido de {user.id}: {e}")
                await manager._send_to_connection(
                    connection_id,
                    RealtimeEventType.SYSTEM_ALERT,
                    {"error": "JSON inválido", "details": str(e)},
                )
            except Exception as e:
                logger.error(f"❌ Erro ao processar mensagem de {user.id}: {e}")
                await manager._send_to_connection(
                    connection_id,
                    RealtimeEventType.SYSTEM_ALERT,
                    {"error": "Erro interno", "details": str(e)},
                )

    except Exception as e:
        logger.error(f"❌ Erro no WebSocket endpoint: {e}")

    finally:
        # Cleanup connection
        if connection_id:
            await manager.disconnect(connection_id, "Connection closed")


async def send_initial_data(
    connection_id: str,
    subscriptions: List[str],
    user: User,
    db: Session,
    manager: RealtimeWebSocketManager,
):
    """Envia dados iniciais baseados nas inscrições do usuário"""
    try:
        # Dashboard data
        if "dashboard" in subscriptions:
            dashboard_stats = await get_dashboard_stats(db)
            await manager._send_to_connection(
                connection_id, RealtimeEventType.DASHBOARD_STATS_UPDATE, dashboard_stats
            )

        # Recent appointments
        if "appointments" in subscriptions:
            appointments = await get_recent_appointments(db, user)
            await manager._send_to_connection(
                connection_id,
                RealtimeEventType.APPOINTMENT_UPDATED,
                {"appointments": appointments},
            )

        # Recent messages
        if "messages" in subscriptions:
            messages = await get_recent_messages(db, user)
            await manager._send_to_connection(
                connection_id, RealtimeEventType.NEW_MESSAGE, {"messages": messages}
            )

        # System status
        system_status = await get_system_status()
        await manager._send_to_connection(
            connection_id,
            RealtimeEventType.SYSTEM_NOTIFICATION,
            {"status": system_status, "message": "Sistema conectado com sucesso"},
        )

        logger.info(f"📤 Dados iniciais enviados para {user.nome}: {subscriptions}")

    except Exception as e:
        logger.error(f"❌ Erro ao enviar dados iniciais: {e}")


async def handle_specific_message_types(
    connection_id: str,
    message_data: Dict[str, Any],
    user: User,
    db: Session,
    manager: RealtimeWebSocketManager,
):
    """Processa tipos específicos de mensagens do cliente"""
    message_type = message_data.get("type")

    try:
        if message_type == "send_message":
            await handle_send_message(connection_id, message_data, user, db, manager)

        elif message_type == "mark_message_read":
            await handle_mark_message_read(
                connection_id, message_data, user, db, manager
            )

        elif message_type == "update_appointment":
            await handle_update_appointment(
                connection_id, message_data, user, db, manager
            )

        elif message_type == "get_dashboard_data":
            dashboard_stats = await get_dashboard_stats(db)
            await manager._send_to_connection(
                connection_id, RealtimeEventType.DASHBOARD_STATS_UPDATE, dashboard_stats
            )

        elif message_type == "refresh_data":
            # Force refresh all subscribed data
            connection_info = manager.get_connection_info(connection_id)
            if connection_info:
                subscriptions = connection_info.get("subscriptions", [])
                await send_initial_data(connection_id, subscriptions, user, db, manager)

    except Exception as e:
        logger.error(f"❌ Erro ao processar mensagem específica {message_type}: {e}")
        await manager._send_to_connection(
            connection_id,
            RealtimeEventType.SYSTEM_ALERT,
            {"error": f"Erro ao processar {message_type}", "details": str(e)},
        )


async def handle_send_message(
    connection_id: str,
    message_data: Dict[str, Any],
    user: User,
    db: Session,
    manager: RealtimeWebSocketManager,
):
    """Processa envio de nova mensagem"""
    try:
        # Extract message data
        content = message_data.get("content", "").strip()
        client_phone = message_data.get("client_phone", "").strip()
        conversation_id = message_data.get("conversation_id")

        if not content:
            raise ValueError("Conteúdo da mensagem é obrigatório")

        if not client_phone:
            raise ValueError("Telefone do cliente é obrigatório")

        # Create message in database
        new_message = Message(
            content=content,
            user_id=user.id,
            conversation_id=conversation_id,
            direction="out",
            message_type="text",
            created_at=datetime.utcnow(),
        )

        db.add(new_message)
        db.commit()
        db.refresh(new_message)

        # Prepare message data for broadcast
        message_broadcast_data = {
            "id": new_message.id,
            "content": new_message.content,
            "client_phone": client_phone,
            "conversation_id": new_message.conversation_id,
            "user_id": new_message.user_id,
            "user_name": user.nome,
            "direction": new_message.direction,
            "message_type": new_message.message_type,
            "created_at": new_message.created_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Broadcast to all users subscribed to messages
        await manager.broadcast_to_subscriptions(
            "messages", RealtimeEventType.NEW_MESSAGE, message_broadcast_data
        )

        # Broadcast to conversation room if exists
        if conversation_id:
            await manager.broadcast_to_room(
                f"conversation_{conversation_id}",
                RealtimeEventType.NEW_MESSAGE,
                message_broadcast_data,
            )

        # Send confirmation to sender
        await manager._send_to_connection(
            connection_id,
            RealtimeEventType.MESSAGE_SENT,
            {
                "message_id": new_message.id,
                "status": "sent",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"💬 Nova mensagem enviada: {user.nome} -> {client_phone}")

    except Exception as e:
        logger.error(f"❌ Erro ao processar envio de mensagem: {e}")
        await manager._send_to_connection(
            connection_id,
            RealtimeEventType.SYSTEM_ALERT,
            {"error": "Erro ao enviar mensagem", "details": str(e)},
        )


async def handle_mark_message_read(
    connection_id: str,
    message_data: Dict[str, Any],
    user: User,
    db: Session,
    manager: RealtimeWebSocketManager,
):
    """Processa marcação de mensagem como lida"""
    try:
        message_id = message_data.get("message_id")
        if not message_id:
            raise ValueError("ID da mensagem é obrigatório")

        # Update message status
        message = db.query(Message).filter(Message.id == message_id).first()
        if message:
            # Add read_at timestamp if column exists
            message.updated_at = datetime.utcnow()
            db.commit()

            # Broadcast read status
            read_data = {
                "message_id": message.id,
                "status": "read",
                "read_by": user.id,
                "read_by_name": user.nome,
                "read_at": datetime.utcnow().isoformat(),
            }

            await manager.broadcast_to_subscriptions(
                "messages", RealtimeEventType.MESSAGE_READ, read_data
            )

            logger.info(f"📖 Mensagem marcada como lida: {message_id} por {user.nome}")

    except Exception as e:
        logger.error(f"❌ Erro ao marcar mensagem como lida: {e}")


async def handle_update_appointment(
    connection_id: str,
    message_data: Dict[str, Any],
    user: User,
    db: Session,
    manager: RealtimeWebSocketManager,
):
    """Processa atualização de agendamento"""
    try:
        appointment_id = message_data.get("appointment_id")
        status = message_data.get("status")

        if not appointment_id:
            raise ValueError("ID do agendamento é obrigatório")

        appointment = (
            db.query(Appointment).filter(Appointment.id == appointment_id).first()
        )
        if appointment:
            if status:
                appointment.status = status
            appointment.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(appointment)

            # Broadcast appointment update
            appointment_data = {
                "id": appointment.id,
                "client_id": appointment.client_id,
                "service_type": appointment.service_type,
                "status": appointment.status,
                "scheduled_for": appointment.scheduled_for.isoformat(),
                "updated_at": appointment.updated_at.isoformat(),
                "updated_by": user.nome,
            }

            await manager.broadcast_to_subscriptions(
                "appointments", RealtimeEventType.APPOINTMENT_UPDATED, appointment_data
            )

            logger.info(f"📅 Agendamento atualizado: {appointment_id} por {user.nome}")

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar agendamento: {e}")


async def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Obtém estatísticas do dashboard"""
    try:
        # Count active appointments today
        today = datetime.utcnow().date()
        appointments_today = (
            db.query(Appointment)
            .filter(
                Appointment.scheduled_for >= today,
                Appointment.scheduled_for < today + timedelta(days=1),
            )
            .count()
        )

        # Count unread messages (simplified)
        unread_messages = 0

        # Count total users instead of clients
        total_users = db.query(User).count()

        # Count messages today
        messages_today = db.query(Message).filter(Message.created_at >= today).count()

        return {
            "appointments_today": appointments_today,
            "unread_messages": unread_messages,
            "total_users": total_users,
            "messages_today": messages_today,
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas do dashboard: {e}")
        return {
            "error": "Erro ao carregar estatísticas",
            "last_updated": datetime.utcnow().isoformat(),
        }


async def get_recent_appointments(
    db: Session, user: User, limit: int = 10
) -> List[Dict[str, Any]]:
    """Obtém agendamentos recentes"""
    try:
        appointments = (
            db.query(Appointment)
            .order_by(Appointment.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": apt.id,
                "client_id": apt.client_id,
                "service_type": apt.service_type,
                "status": apt.status,
                "scheduled_for": apt.scheduled_for.isoformat(),
                "created_at": apt.created_at.isoformat(),
            }
            for apt in appointments
        ]

    except Exception as e:
        logger.error(f"❌ Erro ao obter agendamentos recentes: {e}")
        return []


async def get_recent_messages(
    db: Session, user: User, limit: int = 20
) -> List[Dict[str, Any]]:
    """Obtém mensagens recentes"""
    try:
        messages = (
            db.query(Message).order_by(Message.created_at.desc()).limit(limit).all()
        )

        return [
            {
                "id": msg.id,
                "content": msg.content,
                "client_phone": msg.client_phone,
                "direction": msg.direction,
                "status": msg.status.value,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

    except Exception as e:
        logger.error(f"❌ Erro ao obter mensagens recentes: {e}")
        return []


async def get_system_status() -> Dict[str, Any]:
    """Obtém status do sistema"""
    try:
        manager = get_realtime_manager()
        stats = manager.get_stats()

        return {
            "websocket_healthy": stats["system_healthy"],
            "active_connections": stats["active_connections"],
            "active_users": stats["active_users"],
            "uptime": stats["uptime_human"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Erro ao obter status do sistema: {e}")
        return {
            "error": "Erro ao carregar status",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Health check endpoint
@router.get("/ws/health")
async def websocket_health():
    """Endpoint de health check para WebSocket"""
    try:
        manager = get_realtime_manager()
        stats = manager.get_stats()

        return {
            "status": "healthy" if stats["system_healthy"] else "unhealthy",
            "active_connections": stats["active_connections"],
            "active_users": stats["active_users"],
            "total_messages": stats["messages_sent"],
            "uptime": stats["uptime_human"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Erro no health check WebSocket: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Stats endpoint for monitoring
@router.get("/ws/stats")
async def websocket_stats():
    """Endpoint de estatísticas detalhadas"""
    try:
        manager = get_realtime_manager()
        return manager.get_stats()

    except Exception as e:
        logger.error(f"❌ Erro ao obter stats WebSocket: {e}")
        return {"error": str(e)}


# Connection info endpoint
@router.get("/ws/connections/{connection_id}")
async def get_connection_info(connection_id: str):
    """Endpoint para obter informações de uma conexão específica"""
    try:
        manager = get_realtime_manager()
        info = manager.get_connection_info(connection_id)

        if not info:
            raise HTTPException(status_code=404, detail="Conexão não encontrada")

        return info

    except Exception as e:
        logger.error(f"❌ Erro ao obter info da conexão {connection_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


logger.info("🔌 Router WebSocket Real-Time carregado com sucesso")
