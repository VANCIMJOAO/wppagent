"""
WebSocket Integration Service
============================

Serviço para integrar eventos do WhatsApp com o sistema WebSocket,
enviando notificações em tempo real para o dashboard.

Este serviço atua como uma ponte entre:
- Webhook do WhatsApp (recebe mensagens)
- WebSocket Manager (envia para dashboard)
- Banco de dados (atualiza registros)
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WebSocketIntegrationService:
    """Serviço de integração WebSocket com eventos WhatsApp"""

    def __init__(self):
        self.websocket_manager = None
        self._initialized = False

    async def initialize(self):
        """Inicializa o serviço com o WebSocket Manager"""
        try:
            from app.services.realtime_websocket_manager import get_realtime_manager

            self.websocket_manager = get_realtime_manager()
            self._initialized = True
            logger.info("✅ WebSocketIntegrationService inicializado com sucesso")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar WebSocketIntegrationService: {e}")
            return False

    def is_initialized(self) -> bool:
        """Verifica se o serviço está inicializado"""
        return self._initialized and self.websocket_manager is not None

    async def notify_new_message(
        self,
        conversation_id: str,
        message_content: str,
        sender_name: str = "Cliente",
        sender_phone: str = None,
        message_type: str = "text",
        direction: str = "in",
        **kwargs,
    ):
        """
        Notifica dashboard sobre nova mensagem via WebSocket

        Args:
            conversation_id: ID da conversa
            message_content: Conteúdo da mensagem
            sender_name: Nome do remetente
            sender_phone: Telefone do remetente
            message_type: Tipo da mensagem (text, image, audio, etc.)
            direction: Direção (in/out)
        """
        if not self.is_initialized():
            logger.warning("⚠️ WebSocket não inicializado - notificação ignorada")
            return False

        try:
            data = {
                "conversation_id": str(conversation_id),
                "content": (
                    message_content[:200] + "..."
                    if len(message_content) > 200
                    else message_content
                ),
                "sender": sender_name,
                "sender_phone": sender_phone,
                "message_type": message_type,
                "direction": direction,
                "timestamp": datetime.now().isoformat(),
                **kwargs,
            }

            # Envia via WebSocket para subscribers do evento 'new_message'
            from app.services.realtime_websocket_manager import RealtimeEventType
            sent_count = await self.websocket_manager.broadcast_event(
                RealtimeEventType.NEW_MESSAGE, data
            )

            if sent_count > 0:
                logger.info(
                    f"📨 Notificação nova mensagem enviada para {sent_count} conexões"
                )
                logger.debug(f"   • Conversa: {conversation_id}")
                logger.debug(f"   • Remetente: {sender_name}")
                logger.debug(f"   • Conteúdo: {message_content[:50]}...")
                return True
            else:
                logger.debug(
                    "📨 Nenhuma conexão WebSocket para notificar sobre nova mensagem"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao notificar nova mensagem via WebSocket: {e}")
            return False

    async def notify_conversation_update(
        self, conversation_id: str, updates: Dict[str, Any], **kwargs
    ):
        """
        Notifica dashboard sobre atualização de conversa

        Args:
            conversation_id: ID da conversa
            updates: Dicionário com campos atualizados
        """
        if not self.is_initialized():
            logger.warning("⚠️ WebSocket não inicializado - atualização ignorada")
            return False

        try:
            data = {
                "conversation_id": str(conversation_id),
                "updates": updates,
                "timestamp": datetime.now().isoformat(),
                **kwargs,
            }

            from app.services.realtime_websocket_manager import RealtimeEventType
            sent_count = await self.websocket_manager.broadcast_event(
                RealtimeEventType.CONVERSATION_UPDATED, data
            )

            if sent_count > 0:
                logger.info(
                    f"🔄 Atualização de conversa enviada para {sent_count} conexões"
                )
                logger.debug(f"   • Conversa: {conversation_id}")
                logger.debug(f"   • Updates: {updates}")
                return True
            else:
                logger.debug(
                    "🔄 Nenhuma conexão WebSocket para notificar sobre atualização"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao notificar atualização de conversa: {e}")
            return False

    async def notify_appointment_update(
        self,
        appointment_id: str,
        status: str = None,
        datetime_appointment: str = None,
        customer_name: str = None,
        **kwargs,
    ):
        """
        Notifica dashboard sobre atualização de agendamento

        Args:
            appointment_id: ID do agendamento
            status: Novo status
            datetime_appointment: Data/hora do agendamento
            customer_name: Nome do cliente
        """
        if not self.is_initialized():
            logger.warning("⚠️ WebSocket não inicializado - agendamento ignorado")
            return False

        try:
            data = {
                "appointment_id": str(appointment_id),
                "status": status,
                "datetime": datetime_appointment,
                "customer_name": customer_name,
                "timestamp": datetime.now().isoformat(),
                **kwargs,
            }

            from app.services.realtime_websocket_manager import RealtimeEventType
            sent_count = await self.websocket_manager.broadcast_event(
                RealtimeEventType.APPOINTMENT_UPDATED, data
            )

            if sent_count > 0:
                logger.info(f"📅 Agendamento atualizado para {sent_count} conexões")
                logger.debug(f"   • Agendamento: {appointment_id}")
                logger.debug(f"   • Status: {status}")
                return True
            else:
                logger.debug(
                    "📅 Nenhuma conexão WebSocket para notificar sobre agendamento"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao notificar agendamento: {e}")
            return False

    async def notify_status_change(
        self,
        status_type: str,
        old_status: str,
        new_status: str,
        entity_id: str = None,
        **kwargs,
    ):
        """
        Notifica dashboard sobre mudança de status

        Args:
            status_type: Tipo do status (conversation, appointment, user, etc.)
            old_status: Status anterior
            new_status: Novo status
            entity_id: ID da entidade afetada
        """
        if not self.is_initialized():
            logger.warning("⚠️ WebSocket não inicializado - status ignorado")
            return False

        try:
            data = {
                "status_type": status_type,
                "old_status": old_status,
                "new_status": new_status,
                "entity_id": str(entity_id) if entity_id else None,
                "timestamp": datetime.now().isoformat(),
                **kwargs,
            }

            from app.services.realtime_websocket_manager import RealtimeEventType
            sent_count = await self.websocket_manager.broadcast_event(
                RealtimeEventType.WHATSAPP_STATUS_CHANGE, data
            )

            if sent_count > 0:
                logger.info(f"🔄 Mudança de status enviada para {sent_count} conexões")
                logger.debug(f"   • Tipo: {status_type}")
                logger.debug(f"   • {old_status} → {new_status}")
                return True
            else:
                logger.debug("🔄 Nenhuma conexão WebSocket para notificar sobre status")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao notificar mudança de status: {e}")
            return False

    async def notify_system_event(
        self, event_type: str, message: str, level: str = "info", **kwargs
    ):
        """
        Notifica dashboard sobre eventos do sistema

        Args:
            event_type: Tipo do evento (system, error, warning, etc.)
            message: Mensagem do evento
            level: Nível do evento (info, warning, error)
        """
        if not self.is_initialized():
            return False

        try:
            data = {
                "event_type": event_type,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                **kwargs,
            }

            # Usa broadcast geral para eventos de sistema
            sent_count = await self.websocket_manager.broadcast_to_all(
                {"type": "system_event", "payload": data}
            )

            if sent_count > 0:
                logger.info(f"🔔 Evento de sistema enviado para {sent_count} conexões")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao notificar evento de sistema: {e}")
            return False

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das conexões WebSocket"""
        if not self.is_initialized():
            return {"error": "WebSocket não inicializado"}

        try:
            return self.websocket_manager.get_stats()
        except Exception as e:
            logger.error(f"❌ Erro ao obter stats WebSocket: {e}")
            return {"error": str(e)}


# Instância global do serviço
websocket_integration_service = WebSocketIntegrationService()


async def initialize_websocket_integration():
    """Inicializa o serviço de integração WebSocket"""
    return await websocket_integration_service.initialize()


# Funções de conveniência para uso em outros módulos


async def notify_new_whatsapp_message(
    conversation_id: str,
    message_content: str,
    sender_name: str = "Cliente",
    sender_phone: str = None,
):
    """Função de conveniência para notificar nova mensagem WhatsApp"""
    return await websocket_integration_service.notify_new_message(
        conversation_id=conversation_id,
        message_content=message_content,
        sender_name=sender_name,
        sender_phone=sender_phone,
        direction="in",
        source="whatsapp",
    )


async def notify_message_sent(
    conversation_id: str, message_content: str, sender_name: str = "Atendente"
):
    """Função de conveniência para notificar mensagem enviada"""
    return await websocket_integration_service.notify_new_message(
        conversation_id=conversation_id,
        message_content=message_content,
        sender_name=sender_name,
        direction="out",
        source="dashboard",
    )


async def notify_message_delivered(
    message_id: str,
    conversation_id: str = None,
    user_id: str = None,
    delivered_at: datetime = None
):
    """
    CORREÇÃO: Função de conveniência para notificar mensagem entregue
    
    Args:
        message_id: ID da mensagem
        conversation_id: ID da conversa (opcional)
        user_id: ID do usuário (opcional)
        delivered_at: Timestamp de entrega (padrão: agora)
    """
    if not websocket_integration_service.is_initialized():
        logger.warning("⚠️ WebSocket não inicializado - notificação de entrega ignorada")
        return False
    
    try:
        from app.services.realtime_websocket_manager import get_realtime_manager
        realtime_manager = get_realtime_manager()
        
        return await realtime_manager.mark_message_as_delivered(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            delivered_at=delivered_at
        )
    except Exception as e:
        logger.error(f"❌ Erro ao notificar entrega da mensagem {message_id}: {e}")
        return False


async def notify_message_read(
    message_id: str,
    conversation_id: str = None,
    user_id: str = None,
    read_at: datetime = None
):
    """
    CORREÇÃO: Função de conveniência para notificar mensagem lida
    
    Args:
        message_id: ID da mensagem
        conversation_id: ID da conversa (opcional)
        user_id: ID do usuário (opcional)
        read_at: Timestamp de leitura (padrão: agora)
    """
    if not websocket_integration_service.is_initialized():
        logger.warning("⚠️ WebSocket não inicializado - notificação de leitura ignorada")
        return False
    
    try:
        from app.services.realtime_websocket_manager import get_realtime_manager
        realtime_manager = get_realtime_manager()
        
        return await realtime_manager.mark_message_as_read(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            read_at=read_at
        )
    except Exception as e:
        logger.error(f"❌ Erro ao notificar leitura da mensagem {message_id}: {e}")
        return False


async def notify_conversation_status_change(
    conversation_id: str, old_status: str, new_status: str
):
    """Função de conveniência para notificar mudança de status de conversa"""
    updates = {"status": new_status}

    # Notifica atualização de conversa
    await websocket_integration_service.notify_conversation_update(
        conversation_id=conversation_id, updates=updates
    )

    # Notifica mudança de status
    return await websocket_integration_service.notify_status_change(
        status_type="conversation",
        old_status=old_status,
        new_status=new_status,
        entity_id=conversation_id,
    )
