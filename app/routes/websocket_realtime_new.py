# app/routes/websocket_realtime.py
"""
🌐 Advanced WebSocket Router - Real-time Updates System
=====================================================

Complete WebSocket implementation with:
- Advanced subscription management
- Event broadcasting
- Connection health monitoring
- Automatic cleanup
- Real-time dashboard updates
"""

import logging
from datetime import datetime
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

from app.auth.jwt_manager import verify_token
from app.routes.admin_auth import get_current_admin_user
from app.services.websocket_manager import WebSocketEventType, websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_current_admin_user_ws(token: str):
    """Validate WebSocket token and return user"""
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Mock user for now - replace with actual user lookup
        class MockUser:
            def __init__(self, user_id: str):
                self.id = user_id
                self.username = f"admin_{user_id}"

        return MockUser(payload.get("sub", "unknown"))
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    subscriptions: str = Query(
        "dashboard,appointments,conversations"
    ),  # comma-separated
):
    """
    🌐 Advanced WebSocket endpoint with subscription management

    Available Subscriptions:
    - dashboard: Real-time stats, KPI updates, analytics
    - appointments: CRUD events, status changes, notifications
    - conversations: New messages, status changes, client interactions
    - clients: Client CRUD events, profile updates
    - system: System status, alerts, WhatsApp connectivity
    - analytics: Advanced analytics updates, business intelligence

    Usage:
    wss://your-domain.com/ws?token=JWT_TOKEN&subscriptions=dashboard,appointments
    """
    user_id = None

    try:
        # Validate token and get user
        current_user = await get_current_admin_user_ws(token)
        user_id = f"admin_{current_user.id}"

        # Parse subscriptions
        subscription_list = [s.strip() for s in subscriptions.split(",") if s.strip()]

        # Connect WebSocket
        connected = await websocket_manager.connect(
            websocket, user_id, subscription_list
        )

        if not connected:
            await websocket.close(code=1008, reason="Connection failed")
            return

        logger.info(f"🔌 WebSocket connected: {user_id} -> {subscription_list}")

        try:
            # Keep connection alive and handle client messages
            while True:
                try:
                    # Wait for message from client
                    data = await websocket.receive_json()

                    # Handle client-side events (heartbeat, subscription changes, etc.)
                    await websocket_manager.handle_client_message(user_id, data)

                except Exception as msg_error:
                    logger.warning(
                        f"Message processing error for {user_id}: {msg_error}"
                    )
                    # Don't break connection for message processing errors
                    continue

        except WebSocketDisconnect:
            logger.info(f"🔌 WebSocket disconnected: {user_id}")

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1008, reason="Connection error")
        except:
            pass
    finally:
        if user_id:
            await websocket_manager.disconnect(user_id)


@router.get("/ws/stats")
async def get_websocket_stats(current_user=Depends(get_current_admin_user)):
    """
    📊 Get comprehensive WebSocket connection statistics

    Returns detailed metrics about:
    - Active connections
    - Topic subscriptions
    - Connection health
    - Event history
    """
    stats = websocket_manager.get_connection_stats()

    return {
        "websocket_stats": stats,
        "status": "active" if stats["active_connections"] > 0 else "inactive",
        "health": {
            "total_connections": stats["total_connections"],
            "active_connections": stats["active_connections"],
            "stale_connections": stats["stale_connections"],
            "topics": list(stats["connections_by_topic"].keys()),
            "event_history_size": stats["event_history_size"],
        },
        "server_time": datetime.utcnow().isoformat(),
    }


@router.post("/ws/broadcast")
async def broadcast_test_message(
    topic: str,
    message: str,
    event_type: str = "system_alert",
    current_user=Depends(get_current_admin_user),
):
    """
    🔊 Broadcast test message via WebSocket

    Useful for:
    - Testing WebSocket connectivity
    - Debugging client implementations
    - Sending system-wide alerts

    Example:
    POST /ws/broadcast
    {
        "topic": "dashboard",
        "message": "System maintenance in 5 minutes",
        "event_type": "system_alert"
    }
    """
    try:
        event_type_enum = WebSocketEventType(event_type)
    except ValueError:
        available_types = [e.value for e in WebSocketEventType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event type: {event_type}. Available: {available_types}",
        )

    sent_count = await websocket_manager.broadcast_to_topic(
        topic=topic,
        event_type=event_type_enum,
        data={
            "message": message,
            "sender": getattr(current_user, "username", "system"),
            "test_broadcast": True,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return {
        "success": True,
        "message": f"Broadcasted to {sent_count} clients on topic '{topic}'",
        "recipients": sent_count,
        "event_type": event_type,
        "topic": topic,
        "broadcast_time": datetime.utcnow().isoformat(),
    }


@router.post("/ws/cleanup")
async def cleanup_stale_connections(current_user=Depends(get_current_admin_user)):
    """
    🧹 Manually trigger cleanup of stale WebSocket connections

    Removes connections that:
    - Haven't sent heartbeat in >2 minutes
    - Are marked as not alive
    - Have WebSocket errors
    """
    stats_before = websocket_manager.get_connection_stats()
    cleaned = await websocket_manager.cleanup_stale_connections()
    stats_after = websocket_manager.get_connection_stats()

    return {
        "success": True,
        "message": f"Cleaned up {cleaned} stale connections",
        "cleanup_details": {
            "cleaned_count": cleaned,
            "connections_before": stats_before["total_connections"],
            "connections_after": stats_after["total_connections"],
            "active_connections": stats_after["active_connections"],
        },
        "cleanup_time": datetime.utcnow().isoformat(),
    }


@router.get("/ws/health")
async def websocket_health_check():
    """
    🏥 WebSocket service health check

    Returns service status and basic metrics.
    Used by monitoring systems and load balancers.
    """
    stats = websocket_manager.get_connection_stats()

    # Determine overall health
    health_status = "healthy"
    if stats["stale_connections"] > stats["active_connections"]:
        health_status = "degraded"
    elif stats["active_connections"] == 0 and stats["total_connections"] > 0:
        health_status = "warning"

    return {
        "status": health_status,
        "websocket_service": "running",
        "metrics": {
            "active_connections": stats["active_connections"],
            "total_connections": stats["total_connections"],
            "stale_connections": stats["stale_connections"],
            "topics_active": len(
                [t for t, count in stats["connections_by_topic"].items() if count > 0]
            ),
        },
        "server_time": datetime.utcnow().isoformat(),
        "uptime": "running",
    }


@router.get("/ws/events/types")
async def get_available_event_types():
    """
    📋 Get list of available WebSocket event types

    Returns all supported event types for client reference.
    """
    event_types = [
        {
            "name": event.name,
            "value": event.value,
            "category": event.value.split("_")[0] if "_" in event.value else "general",
        }
        for event in WebSocketEventType
    ]

    # Group by category
    categories = {}
    for event in event_types:
        category = event["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append({"name": event["name"], "value": event["value"]})

    return {
        "event_types": event_types,
        "categories": categories,
        "total_types": len(event_types),
    }
