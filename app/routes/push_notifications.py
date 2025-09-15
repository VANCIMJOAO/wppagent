"""
🔔 Push Notifications API Routes

Endpoints para gerenciamento de push notifications:
- Subscribe/Unsubscribe admins
- Envio de notificações
- Estatísticas e gerenciamento
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.middleware import get_current_user, require_admin
from ..database import get_db
from ..models.database import AdminUser
from ..services.push_service import push_service, send_alert_notification

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/push", tags=["push-notifications"])


# 📝 Pydantic Models
class PushSubscriptionRequest(BaseModel):
    """Request para subscription de push notifications"""

    endpoint: str
    keys: Dict[str, str]  # p256dh e auth
    user_agent: Optional[str] = None


class PushNotificationRequest(BaseModel):
    """Request para envio de notificação"""

    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    badge: Optional[str] = None
    tag: Optional[str] = None
    require_interaction: bool = False


class AlertNotificationRequest(BaseModel):
    """Request para notificação de alerta"""

    level: str  # HIGH, CRITICAL
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None


# 📝 Routes
@router.post("/subscribe")
async def subscribe_push_notifications(
    request: PushSubscriptionRequest,
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(require_admin),
):
    """
    🔔 Registra admin para receber push notifications

    Body:
    ```json
    {
        "endpoint": "https://fcm.googleapis.com/fcm/send/...",
        "keys": {
            "p256dh": "BG3OGHrl3YJ5PHpl0GSqtVEUx...",
            "auth": "I6lVOFt2TbCaNF3pYqve_g"
        },
        "user_agent": "Mozilla/5.0..."
    }
    ```
    """
    try:
        subscription_data = {"endpoint": request.endpoint, "keys": request.keys}

        subscription = await push_service.subscribe_admin(
            db=db,
            admin_user_id=admin_user.id,
            subscription_data=subscription_data,
            user_agent=request.user_agent,
        )

        return {
            "success": True,
            "message": "Push notifications ativadas com sucesso",
            "subscription_id": subscription.id,
        }

    except Exception as e:
        logger.error(f"Erro ao ativar push notifications: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/unsubscribe")
async def unsubscribe_push_notifications(
    endpoint: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(require_admin),
):
    """
    ❌ Remove subscription de push notifications

    Query params:
    - endpoint (opcional): Remove subscription específica, senão remove todas
    """
    try:
        count = await push_service.unsubscribe_admin(
            db=db, admin_user_id=admin_user.id, endpoint=endpoint
        )

        return {
            "success": True,
            "message": f"Push notifications desativadas ({count} subscriptions removidas)",
        }

    except Exception as e:
        logger.error(f"Erro ao desativar push notifications: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions")
async def list_admin_subscriptions(
    db: Session = Depends(get_db), admin_user: Dict = Depends(require_admin)
):
    """
    📋 Lista subscriptions ativas do admin
    """
    try:
        subscriptions = await push_service.get_admin_subscriptions(
            db=db, admin_user_id=admin_user.id
        )

        return {
            "subscriptions": [
                {
                    "id": sub.id,
                    "endpoint": (
                        sub.endpoint[:50] + "..."
                        if len(sub.endpoint) > 50
                        else sub.endpoint
                    ),
                    "user_agent": sub.user_agent,
                    "created_at": sub.created_at,
                    "last_used_at": sub.last_used_at,
                }
                for sub in subscriptions
            ]
        }

    except Exception as e:
        logger.error(f"Erro ao listar subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_push_notification(
    request: PushNotificationRequest,
    admin_user_id: Optional[int] = None,
    send_to_all: bool = False,
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(require_admin),
):
    """
    📤 Envia push notification

    Body:
    ```json
    {
        "title": "Nova mensagem",
        "body": "Você tem uma nova conversa",
        "data": {"conversation_id": 123},
        "require_interaction": false
    }
    ```

    Query params:
    - admin_user_id: ID do admin de destino (opcional)
    - send_to_all: Enviar para todos os admins (default: false)
    """
    try:
        if send_to_all:
            # Enviar para todos os admins
            count = await push_service.send_to_all_admins(
                db=db,
                title=request.title,
                body=request.body,
                data=request.data,
                icon=request.icon,
                badge=request.badge,
                tag=request.tag,
                require_interaction=request.require_interaction,
            )

            return {
                "success": True,
                "message": f"Notificação enviada para todos os admins ({count} notificações)",
            }

        elif admin_user_id:
            # Enviar para admin específico
            count = await push_service.send_to_admin(
                db=db,
                admin_user_id=admin_user_id,
                title=request.title,
                body=request.body,
                data=request.data,
                icon=request.icon,
                badge=request.badge,
                tag=request.tag,
                require_interaction=request.require_interaction,
            )

            return {
                "success": True,
                "message": f"Notificação enviada para admin {admin_user_id} ({count} notificações)",
            }

        else:
            # Enviar para o próprio admin
            count = await push_service.send_to_admin(
                db=db,
                admin_user_id=admin_user.id,
                title=request.title,
                body=request.body,
                data=request.data,
                icon=request.icon,
                badge=request.badge,
                tag=request.tag,
                require_interaction=request.require_interaction,
            )

            return {
                "success": True,
                "message": f"Notificação enviada ({count} notificações)",
            }

    except Exception as e:
        logger.error(f"Erro ao enviar notificação: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-alert")
async def send_alert_push_notification(
    request: AlertNotificationRequest,
    db: Session = Depends(get_db),
    admin_user: Dict = Depends(require_admin),
):
    """
    🚨 Envia push notification para alerta HIGH/CRITICAL

    Body:
    ```json
    {
        "level": "CRITICAL",
        "title": "Sistema Offline",
        "message": "O WhatsApp Web foi desconectado",
        "data": {"alert_type": "connection_lost"}
    }
    ```
    """
    try:
        if request.level not in ["HIGH", "CRITICAL"]:
            raise HTTPException(
                status_code=400, detail="Level deve ser HIGH ou CRITICAL"
            )

        await send_alert_notification(
            db=db,
            alert_level=request.level,
            title=request.title,
            message=request.message,
            data=request.data,
        )

        return {
            "success": True,
            "message": f"Alerta {request.level} enviado para todos os admins",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar alerta: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_push_notification_stats(
    db: Session = Depends(get_db), admin_user: Dict = Depends(require_admin)
):
    """
    📊 Estatísticas de push notifications
    """
    try:
        stats = await push_service.get_notification_stats(db)
        return stats

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_push_notification(
    db: Session = Depends(get_db), admin_user: Dict = Depends(require_admin)
):
    """
    🧪 Envia notificação de teste para o admin atual
    """
    try:
        count = await push_service.send_to_admin(
            db=db,
            admin_user_id=admin_user.id,
            title="🧪 Teste de Push Notification",
            body="Se você está vendo isso, as push notifications estão funcionando!",
            data={"test": True},
            tag="test-notification",
        )

        return {
            "success": True,
            "message": f"Notificação de teste enviada ({count} subscriptions)",
        }

    except Exception as e:
        logger.error(f"Erro ao enviar teste: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_invalid_subscriptions(
    db: Session = Depends(get_db), admin_user: Dict = Depends(require_admin)
):
    """
    🧹 Remove subscriptions inválidas (apenas super admin)
    """
    try:
        # Verificar se é super admin
        if not admin_user.is_super_admin:
            raise HTTPException(
                status_code=403, detail="Apenas super admins podem executar cleanup"
            )

        count = await push_service.cleanup_invalid_subscriptions(db)

        return {
            "success": True,
            "message": f"Cleanup concluído ({count} subscriptions removidas)",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 🔔 VAPID Public Key endpoint (para frontend)
@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """
    🔑 Retorna VAPID public key para o frontend

    Não requer autenticação pois é chave pública.
    """
    from ..config import get_settings

    settings = get_settings()

    return {"vapid_public_key": settings.VAPID_PUBLIC_KEY_FRONTEND}
