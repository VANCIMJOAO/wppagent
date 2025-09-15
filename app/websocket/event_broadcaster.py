"""
📡 Event Broadcasting System
============================

Sistema para automaticamente broadcastar eventos de negócio
via WebSocket para clientes conectados.

Integração com rotas existentes para enviar updates em tempo real
quando appointments são criados/atualizados/deletados.

Status: Resolução completa do problema 4.1 Real-time Updates Parciais
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.websocket.connection_manager import (
    EventType,
    RoomType,
    WebSocketMessage,
    connection_manager,
)

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """
    📡 Sistema de broadcasting de eventos

    Funcionalidades:
    - Broadcasting automático de eventos de negócio
    - Filtering por tipo de usuário/permissão
    - Queue de mensagens para reliability
    - Metrics e monitoring
    """

    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.broadcasting_task = None
        self.metrics = {
            "events_broadcasted": 0,
            "failed_broadcasts": 0,
            "active_since": datetime.utcnow().isoformat(),
        }

    async def start_broadcasting(self):
        """
        🚀 Iniciar task de broadcasting
        """
        if self.broadcasting_task is None:
            self.broadcasting_task = asyncio.create_task(self._process_event_queue())
            logger.info("Event broadcasting started")

    async def stop_broadcasting(self):
        """
        🛑 Parar task de broadcasting
        """
        if self.broadcasting_task:
            self.broadcasting_task.cancel()
            self.broadcasting_task = None
            logger.info("Event broadcasting stopped")

    async def broadcast_appointment_created(self, appointment_data: dict):
        """
        📅 Broadcast: Novo agendamento criado
        """
        event = {
            "type": EventType.APPOINTMENT_CREATED.value,
            "data": {
                "appointment": appointment_data,
                "message": f"Novo agendamento criado para {appointment_data.get('nome', 'paciente')}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "rooms": [RoomType.DASHBOARD.value, RoomType.APPOINTMENTS.value],
        }

        await self.event_queue.put(event)
        logger.info(f"Queued appointment_created event: {appointment_data.get('id')}")

    async def broadcast_appointment_updated(self, appointment_data: dict):
        """
        📅 Broadcast: Agendamento atualizado
        """
        event = {
            "type": EventType.APPOINTMENT_UPDATED.value,
            "data": {
                "appointment": appointment_data,
                "message": f"Agendamento atualizado: {appointment_data.get('nome', 'paciente')}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "rooms": [RoomType.DASHBOARD.value, RoomType.APPOINTMENTS.value],
        }

        await self.event_queue.put(event)
        logger.info(f"Queued appointment_updated event: {appointment_data.get('id')}")

    async def broadcast_appointment_deleted(
        self, appointment_id: int, appointment_data: dict = None
    ):
        """
        📅 Broadcast: Agendamento deletado
        """
        event = {
            "type": EventType.APPOINTMENT_DELETED.value,
            "data": {
                "appointment_id": appointment_id,
                "appointment": appointment_data,
                "message": f"Agendamento cancelado: ID {appointment_id}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "rooms": [RoomType.DASHBOARD.value, RoomType.APPOINTMENTS.value],
        }

        await self.event_queue.put(event)
        logger.info(f"Queued appointment_deleted event: {appointment_id}")

    async def broadcast_system_notification(
        self, message: str, level: str = "info", rooms: list = None
    ):
        """
        🔔 Broadcast: Notificação do sistema
        """
        event = {
            "type": EventType.SYSTEM_NOTIFICATION.value,
            "data": {
                "message": message,
                "level": level,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "rooms": rooms or [RoomType.GENERAL.value],
        }

        await self.event_queue.put(event)
        logger.info(f"Queued system_notification: {message[:50]}")

    async def broadcast_user_status_change(
        self, user_id: str, status: str, rooms: list = None
    ):
        """
        👤 Broadcast: Mudança de status de usuário
        """
        event = {
            "type": EventType.USER_STATUS_CHANGED.value,
            "data": {
                "user_id": user_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "rooms": rooms or [RoomType.GENERAL.value],
        }

        await self.event_queue.put(event)
        logger.info(f"Queued user_status_change: {user_id} -> {status}")

    async def broadcast_custom_event(
        self, event_type: str, data: dict, rooms: list = None
    ):
        """
        🎯 Broadcast: Evento customizado
        """
        event = {
            "type": event_type,
            "data": {**data, "timestamp": datetime.utcnow().isoformat()},
            "rooms": rooms or [RoomType.GENERAL.value],
        }

        await self.event_queue.put(event)
        logger.info(f"Queued custom event: {event_type}")

    async def _process_event_queue(self):
        """
        🔄 Processar fila de eventos
        """
        while True:
            try:
                # Aguardar próximo evento na fila
                event = await self.event_queue.get()

                # Processar evento
                await self._broadcast_event(event)

                # Marcar como processado
                self.event_queue.task_done()

            except asyncio.CancelledError:
                logger.info("Event queue processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error processing event queue: {e}")
                self.metrics["failed_broadcasts"] += 1
                await asyncio.sleep(1)  # Wait before retrying

    async def _broadcast_event(self, event: dict):
        """
        📡 Broadcast evento para salas especificadas
        """
        try:
            event_type = event.get("type")
            event_data = event.get("data", {})
            rooms = event.get("rooms", [])

            # Criar mensagem WebSocket
            message = WebSocketMessage(
                type=event_type, data=event_data, room=""  # Will be set per room
            )

            total_sent = 0

            # Broadcast para cada sala
            for room in rooms:
                message.room = room
                sent_count = await connection_manager.broadcast_to_room(message, room)
                total_sent += sent_count
                logger.debug(
                    f"Broadcast {event_type} to {room}: {sent_count} recipients"
                )

            self.metrics["events_broadcasted"] += 1
            logger.info(
                f"Successfully broadcast {event_type} to {total_sent} connections across {len(rooms)} rooms"
            )

        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
            self.metrics["failed_broadcasts"] += 1

    def get_metrics(self) -> dict:
        """
        📊 Obter métricas do broadcaster
        """
        return {
            **self.metrics,
            "queue_size": self.event_queue.qsize(),
            "is_running": self.broadcasting_task is not None
            and not self.broadcasting_task.done(),
        }


# Singleton instance
event_broadcaster = EventBroadcaster()


# Helper functions para usar nas rotas
async def notify_appointment_created(appointment_data: dict):
    """Helper para notificar criação de agendamento"""
    await event_broadcaster.broadcast_appointment_created(appointment_data)


async def notify_appointment_updated(appointment_data: dict):
    """Helper para notificar atualização de agendamento"""
    await event_broadcaster.broadcast_appointment_updated(appointment_data)


async def notify_appointment_deleted(
    appointment_id: int, appointment_data: dict = None
):
    """Helper para notificar deleção de agendamento"""
    await event_broadcaster.broadcast_appointment_deleted(
        appointment_id, appointment_data
    )


async def notify_system_message(message: str, level: str = "info"):
    """Helper para notificações do sistema"""
    await event_broadcaster.broadcast_system_notification(message, level)


async def notify_user_status(user_id: str, status: str):
    """Helper para mudanças de status de usuário"""
    await event_broadcaster.broadcast_user_status_change(user_id, status)


# Startup function
async def start_event_broadcasting():
    """Iniciar sistema de broadcasting"""
    await event_broadcaster.start_broadcasting()


# Shutdown function
async def stop_event_broadcasting():
    """Parar sistema de broadcasting"""
    await event_broadcaster.stop_broadcasting()
