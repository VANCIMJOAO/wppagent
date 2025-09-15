# app/services/websocket_manager.py
import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketEventType(Enum):
    # Dashboard events
    DASHBOARD_STATS_UPDATE = "dashboard_stats_update"
    KPI_UPDATE = "kpi_update"
    ANALYTICS_UPDATE = "analytics_update"

    # Appointments events
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_UPDATED = "appointment_updated"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"

    # Conversations events
    NEW_MESSAGE = "new_message"
    CONVERSATION_STATUS_CHANGED = "conversation_status_changed"
    CONVERSATION_STARTED = "conversation_started"

    # Client events
    CLIENT_CREATED = "client_created"
    CLIENT_UPDATED = "client_updated"
    CLIENT_STATUS_CHANGED = "client_status_changed"

    # System events
    WHATSAPP_STATUS_CHANGE = "whatsapp_status_change"
    CACHE_INVALIDATED = "cache_invalidated"
    SYSTEM_ALERT = "system_alert"
    CONNECTION_STATUS = "connection_status"
    HEARTBEAT_RESPONSE = "heartbeat_response"


class WebSocketConnection:
    def __init__(
        self, websocket: WebSocket, user_id: str, subscriptions: Set[str] = None
    ):
        self.websocket = websocket
        self.user_id = user_id
        self.subscriptions = subscriptions or set()
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.is_alive = True

    async def send_event(self, event_type: WebSocketEventType, data: dict) -> bool:
        """Send event to this connection"""
        if not self.is_alive:
            return False

        try:
            message = {
                "type": event_type.value,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": self.user_id,
            }
            await self.websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message to {self.user_id}: {e}")
            self.is_alive = False
            return False

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()

    def is_stale(self, timeout_seconds: int = 120) -> bool:
        """Check if connection is stale (no heartbeat)"""
        return (datetime.utcnow() - self.last_heartbeat).seconds > timeout_seconds


class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.topic_subscriptions: Dict[str, Set[str]] = {}  # topic -> set of user_ids
        self.event_history: List[Dict] = []  # Store recent events for reconnection
        self.max_history_size = 100

    async def connect(
        self, websocket: WebSocket, user_id: str, subscriptions: List[str] = None
    ) -> bool:
        """Connect a new WebSocket client"""
        try:
            # Start cleanup task if not already started
            start_cleanup_task()

            await websocket.accept()

            connection = WebSocketConnection(
                websocket=websocket,
                user_id=user_id,
                subscriptions=set(subscriptions or []),
            )

            # Disconnect any existing connection for this user
            if user_id in self.connections:
                await self.disconnect(user_id)

            self.connections[user_id] = connection

            # Add to topic subscriptions
            for topic in connection.subscriptions:
                if topic not in self.topic_subscriptions:
                    self.topic_subscriptions[topic] = set()
                self.topic_subscriptions[topic].add(user_id)

            logger.info(
                f"✅ WebSocket connected: {user_id} with subscriptions: {connection.subscriptions}"
            )

            # Send initial connection success message
            await connection.send_event(
                WebSocketEventType.CONNECTION_STATUS,
                {
                    "connected": True,
                    "user_id": user_id,
                    "subscriptions": list(connection.subscriptions),
                    "server_time": datetime.utcnow().isoformat(),
                },
            )

            return True

        except Exception as e:
            logger.error(f"Failed to connect WebSocket for {user_id}: {e}")
            return False

    async def disconnect(self, user_id: str):
        """Disconnect a WebSocket client"""
        if user_id in self.connections:
            connection = self.connections[user_id]

            # Remove from topic subscriptions
            for topic in connection.subscriptions:
                if topic in self.topic_subscriptions:
                    self.topic_subscriptions[topic].discard(user_id)

            # Close WebSocket connection
            try:
                if connection.websocket and connection.is_alive:
                    await connection.websocket.close()
            except:
                pass

            del self.connections[user_id]
            logger.info(f"❌ WebSocket disconnected: {user_id}")

    async def broadcast_to_topic(
        self,
        topic: str,
        event_type: WebSocketEventType,
        data: dict,
        exclude_user: str = None,
    ) -> int:
        """Broadcast event to all subscribers of a topic"""
        if topic not in self.topic_subscriptions:
            return 0

        user_ids = list(self.topic_subscriptions[topic])
        if exclude_user:
            user_ids = [uid for uid in user_ids if uid != exclude_user]

        disconnected = []
        successful_sends = 0

        # Store event in history
        self._store_event(topic, event_type, data)

        for user_id in user_ids:
            if user_id in self.connections:
                success = await self.connections[user_id].send_event(event_type, data)
                if success:
                    successful_sends += 1
                else:
                    disconnected.append(user_id)

        # Clean up disconnected clients
        for user_id in disconnected:
            await self.disconnect(user_id)

        if successful_sends > 0:
            logger.info(
                f"📡 Broadcasted {event_type.value} to {successful_sends} clients on topic: {topic}"
            )

        return successful_sends

    async def send_to_user(
        self, user_id: str, event_type: WebSocketEventType, data: dict
    ) -> bool:
        """Send event to specific user"""
        if user_id in self.connections:
            success = await self.connections[user_id].send_event(event_type, data)
            if not success:
                await self.disconnect(user_id)
            return success
        return False

    async def broadcast_to_all(self, event_type: WebSocketEventType, data: dict) -> int:
        """Broadcast event to all connected clients"""
        user_ids = list(self.connections.keys())
        disconnected = []
        successful_sends = 0

        # Store event in history
        self._store_event("global", event_type, data)

        for user_id in user_ids:
            success = await self.connections[user_id].send_event(event_type, data)
            if success:
                successful_sends += 1
            else:
                disconnected.append(user_id)

        # Clean up disconnected clients
        for user_id in disconnected:
            await self.disconnect(user_id)

        if successful_sends > 0:
            logger.info(
                f"📡 Broadcasted {event_type.value} to {successful_sends} clients"
            )

        return successful_sends

    async def handle_client_message(self, user_id: str, data: dict):
        """Handle messages sent from client to server"""
        message_type = data.get("type")

        if user_id not in self.connections:
            return

        connection = self.connections[user_id]

        if message_type == "heartbeat":
            connection.update_heartbeat()
            # Respond to heartbeat
            await connection.send_event(
                WebSocketEventType.HEARTBEAT_RESPONSE,
                {
                    "heartbeat_response": True,
                    "server_time": datetime.utcnow().isoformat(),
                    "connection_duration": int(
                        (datetime.utcnow() - connection.connected_at).total_seconds()
                    ),
                },
            )

        elif message_type == "subscribe":
            # Handle dynamic subscription changes
            new_topics = set(data.get("topics", []))
            old_topics = connection.subscriptions.copy()

            # Remove from old topics
            for topic in old_topics - new_topics:
                if topic in self.topic_subscriptions:
                    self.topic_subscriptions[topic].discard(user_id)

            # Add to new topics
            for topic in new_topics - old_topics:
                if topic not in self.topic_subscriptions:
                    self.topic_subscriptions[topic] = set()
                self.topic_subscriptions[topic].add(user_id)

            connection.subscriptions = new_topics

            await connection.send_event(
                WebSocketEventType.CONNECTION_STATUS,
                {
                    "subscriptions_updated": True,
                    "new_subscriptions": list(new_topics),
                    "added": list(new_topics - old_topics),
                    "removed": list(old_topics - new_topics),
                },
            )

            logger.info(f"User {user_id} updated subscriptions: {new_topics}")

        elif message_type == "request_stats":
            # Client requesting immediate stats update
            try:
                # Import here to avoid circular imports
                from app.database import get_db
                from app.services.analytics_engine_advanced import \
                    AdvancedAnalyticsEngine

                # Get basic dashboard stats
                basic_stats = {
                    "messages_today": 150,  # Mock data - replace with actual logic
                    "conversations_today": 45,
                    "appointments_today": 12,
                    "new_clients_today": 8,
                    "last_updated": datetime.utcnow().isoformat(),
                }

                await connection.send_event(
                    WebSocketEventType.DASHBOARD_STATS_UPDATE,
                    {"stats": basic_stats, "requested": True},
                )
            except Exception as e:
                logger.error(f"Error getting stats for WebSocket request: {e}")

        elif message_type == "request_history":
            # Send recent events history to client (for reconnection recovery)
            recent_events = self._get_recent_events_for_user(connection.subscriptions)
            await connection.send_event(
                WebSocketEventType.CONNECTION_STATUS,
                {"history": recent_events, "history_count": len(recent_events)},
            )

    def _store_event(self, topic: str, event_type: WebSocketEventType, data: dict):
        """Store event in history for reconnection recovery"""
        event_record = {
            "topic": topic,
            "type": event_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.event_history.append(event_record)

        # Keep only recent events
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size :]

    def _get_recent_events_for_user(
        self, subscriptions: Set[str], minutes: int = 5
    ) -> List[Dict]:
        """Get recent events relevant to user's subscriptions"""
        cutoff_time = datetime.utcnow().replace(microsecond=0) - timedelta(
            minutes=minutes
        )

        recent_events = []
        for event in reversed(self.event_history):
            try:
                event_time = datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                )
                if event_time < cutoff_time:
                    break

                if event["topic"] in subscriptions or event["topic"] == "global":
                    recent_events.append(event)
            except:
                continue

        return list(reversed(recent_events))  # Chronological order

    async def cleanup_stale_connections(self):
        """Clean up stale connections (should be called periodically)"""
        stale_users = []

        for user_id, connection in self.connections.items():
            if connection.is_stale():
                stale_users.append(user_id)

        for user_id in stale_users:
            logger.warning(f"Cleaning up stale WebSocket connection: {user_id}")
            await self.disconnect(user_id)

        return len(stale_users)

    def get_connection_stats(self) -> dict:
        """Get statistics about WebSocket connections"""
        active_connections = sum(
            1 for conn in self.connections.values() if conn.is_alive
        )

        topic_stats = {}
        for topic, users in self.topic_subscriptions.items():
            active_users = [
                uid
                for uid in users
                if uid in self.connections and self.connections[uid].is_alive
            ]
            topic_stats[topic] = len(active_users)

        return {
            "total_connections": len(self.connections),
            "active_connections": active_connections,
            "stale_connections": len(self.connections) - active_connections,
            "connections_by_topic": topic_stats,
            "active_users": [
                uid for uid, conn in self.connections.items() if conn.is_alive
            ],
            "event_history_size": len(self.event_history),
            "uptime_stats": {
                user_id: {
                    "connected_at": conn.connected_at.isoformat(),
                    "last_heartbeat": conn.last_heartbeat.isoformat(),
                    "subscriptions": list(conn.subscriptions),
                    "is_alive": conn.is_alive,
                }
                for user_id, conn in self.connections.items()
            },
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# Background task to clean up stale connections
async def cleanup_stale_connections_task():
    """Background task to periodically clean up stale connections"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            cleaned = await websocket_manager.cleanup_stale_connections()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} stale WebSocket connections")
        except Exception as e:
            logger.error(f"Error in WebSocket cleanup task: {e}")


# Global variable to track if cleanup task has been started
_cleanup_task_started = False


def start_cleanup_task():
    """Start the cleanup task if not already started"""
    global _cleanup_task_started
    if not _cleanup_task_started:
        try:
            asyncio.create_task(cleanup_stale_connections_task())
            _cleanup_task_started = True
            logger.info("WebSocket cleanup task started")
        except RuntimeError:
            # No event loop running, will be started later
            pass
