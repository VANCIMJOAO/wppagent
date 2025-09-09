"""
🔔 Push Notification Service

Serviço completo para gerenciamento de web push notifications.
Inclui subscription management, envio de notificações e integração com alertas.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.database import PushSubscription, PushNotification, AdminUser
from ..database import get_db
from ..config import get_settings

# 🛡️ Safe import - não quebra a API se pywebpush não estiver disponível
PYWEBPUSH_AVAILABLE = False
WebPushException = None
webpush = None

try:
    from pywebpush import webpush, WebPushException
    PYWEBPUSH_AVAILABLE = True
    print("📱 pywebpush module loaded successfully")
except ImportError as e:
    print(f"⚠️ pywebpush not available: {e}")
    print("🔄 Push notifications will be disabled until dependencies are installed")
    
    # Mock classes para não quebrar a aplicação
    class WebPushException(Exception):
        pass
    
    def webpush(*args, **kwargs):
        print("🚫 webpush() called but pywebpush not available")
        return None

logger = logging.getLogger(__name__)
settings = get_settings()


class PushNotificationService:
    """
    🔔 Serviço de Push Notifications
    
    Features:
    - Gerenciamento de subscriptions
    - Envio de notificações individuais/em lote
    - Cleanup automático de subscriptions inválidas
    - Integração com sistema de alertas
    """
    
    def __init__(self):
        self.vapid_claims = {
            "sub": getattr(settings, 'VAPID_SUBJECT', 'mailto:admin@whatsapp-agent.com')
        }
        self.vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        self.vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    
    async def subscribe_admin(
        self,
        db: Session,
        admin_user_id: int,
        subscription_data: Dict[str, Any],
        user_agent: Optional[str] = None
    ) -> PushSubscription:
        """
        📝 Registra nova subscription de admin
        
        Args:
            admin_user_id: ID do admin
            subscription_data: Dados da subscription do browser
            user_agent: Info do browser/device
        
        Returns:
            PushSubscription criada
        """
        try:
            # Validar dados da subscription
            endpoint = subscription_data.get("endpoint")
            keys = subscription_data.get("keys", {})
            p256dh_key = keys.get("p256dh")
            auth_key = keys.get("auth")
            
            if not all([endpoint, p256dh_key, auth_key]):
                raise ValueError("Dados de subscription inválidos")
            
            # Verificar se subscription já existe (mesmo endpoint)
            existing = db.query(PushSubscription).filter_by(endpoint=endpoint).first()
            if existing:
                # Atualizar subscription existente
                existing.admin_user_id = admin_user_id
                existing.p256dh_key = p256dh_key
                existing.auth_key = auth_key
                existing.user_agent = user_agent
                existing.is_active = True
                existing.last_used_at = datetime.utcnow()
                db.commit()
                logger.info(f"Subscription atualizada para admin {admin_user_id}")
                return existing
            
            # Criar nova subscription
            subscription = PushSubscription(
                admin_user_id=admin_user_id,
                endpoint=endpoint,
                p256dh_key=p256dh_key,
                auth_key=auth_key,
                user_agent=user_agent
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"Nova subscription criada para admin {admin_user_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Erro ao criar subscription: {str(e)}")
            db.rollback()
            raise
    
    async def unsubscribe_admin(
        self,
        db: Session,
        admin_user_id: int,
        endpoint: Optional[str] = None
    ) -> int:
        """
        ❌ Remove subscriptions de um admin
        
        Args:
            admin_user_id: ID do admin
            endpoint: Endpoint específico (opcional, remove todas se None)
        
        Returns:
            Número de subscriptions removidas
        """
        try:
            query = db.query(PushSubscription).filter_by(admin_user_id=admin_user_id)
            
            if endpoint:
                query = query.filter_by(endpoint=endpoint)
            
            subscriptions = query.all()
            count = len(subscriptions)
            
            for subscription in subscriptions:
                db.delete(subscription)
            
            db.commit()
            logger.info(f"Removidas {count} subscriptions do admin {admin_user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Erro ao remover subscriptions: {str(e)}")
            db.rollback()
            raise
    
    async def send_notification(
        self,
        db: Session,
        subscription: PushSubscription,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        tag: Optional[str] = None,
        require_interaction: bool = False
    ) -> bool:
        """
        📤 Envia push notification para uma subscription
        
        Args:
            subscription: PushSubscription de destino
            title: Título da notificação
            body: Corpo da notificação
            data: Dados adicionais
            icon: URL do ícone
            badge: URL do badge
            tag: Tag para agrupamento
            require_interaction: Requer interação do usuário
        
        Returns:
            True se enviada com sucesso, False caso contrário
        """
        
        # 🛡️ Verificar se pywebpush está disponível
        if not PYWEBPUSH_AVAILABLE:
            logger.warning("🚫 Push notification request ignored - pywebpush not available")
            logger.info(f"📄 Would send: '{title}' - '{body}' to {subscription.endpoint}")
            return False
            
        try:
            # Preparar payload
            payload = {
                "title": title,
                "body": body,
                "icon": icon or "/icons/notification-icon.png",
                "badge": badge or "/icons/badge-icon.png",
                "tag": tag or "whatsapp-agent",
                "requireInteraction": require_interaction,
                "data": data or {},
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            }
            
            # Dados da subscription
            subscription_info = {
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh_key,
                    "auth": subscription.auth_key
                }
            }
            
            # Enviar push notification
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims
            )
            
            # Log da notificação
            notification_log = PushNotification(
                subscription_id=subscription.id,
                title=title,
                body=body,
                data=data,
                status="sent"
            )
            db.add(notification_log)
            
            # Atualizar last_used_at
            subscription.last_used_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Push notification enviada: {title} -> {subscription.endpoint[:50]}...")
            return True
            
        except WebPushException as e:
            error_msg = f"WebPush error: {str(e)}"
            logger.error(error_msg)
            
            # Log do erro
            notification_log = PushNotification(
                subscription_id=subscription.id,
                title=title,
                body=body,
                data=data,
                status="failed",
                error_message=error_msg
            )
            db.add(notification_log)
            
            # Se subscription inválida, desativar
            if e.response and e.response.status_code in [410, 404]:
                subscription.is_active = False
                logger.info(f"Subscription inválida desativada: {subscription.id}")
            
            db.commit()
            return False
            
        except Exception as e:
            error_msg = f"Erro interno: {str(e)}"
            logger.error(error_msg)
            
            # Log do erro
            notification_log = PushNotification(
                subscription_id=subscription.id,
                title=title,
                body=body,
                data=data,
                status="failed",
                error_message=error_msg
            )
            db.add(notification_log)
            db.commit()
            return False
    
    async def send_to_admin(
        self,
        db: Session,
        admin_user_id: int,
        title: str,
        body: str,
        **kwargs
    ) -> int:
        """
        📤 Envia push notification para todas as subscriptions de um admin
        
        Returns:
            Número de notificações enviadas com sucesso
        """
        try:
            subscriptions = db.query(PushSubscription).filter(
                and_(
                    PushSubscription.admin_user_id == admin_user_id,
                    PushSubscription.is_active == True
                )
            ).all()
            
            if not subscriptions:
                logger.warning(f"Nenhuma subscription ativa para admin {admin_user_id}")
                return 0
            
            success_count = 0
            tasks = []
            
            # Enviar em paralelo
            for subscription in subscriptions:
                task = self.send_notification(
                    db, subscription, title, body, **kwargs
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for result in results if result is True)
            
            logger.info(f"Enviadas {success_count}/{len(subscriptions)} notificações para admin {admin_user_id}")
            return success_count
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificações para admin {admin_user_id}: {str(e)}")
            return 0
    
    async def send_to_all_admins(
        self,
        db: Session,
        title: str,
        body: str,
        **kwargs
    ) -> int:
        """
        📢 Envia push notification para todos os admins
        
        Returns:
            Número total de notificações enviadas
        """
        try:
            subscriptions = db.query(PushSubscription).filter(
                PushSubscription.is_active == True
            ).all()
            
            if not subscriptions:
                logger.warning("Nenhuma subscription ativa encontrada")
                return 0
            
            success_count = 0
            tasks = []
            
            # Enviar em paralelo (batches de 50 para evitar sobrecarga)
            batch_size = 50
            for i in range(0, len(subscriptions), batch_size):
                batch = subscriptions[i:i + batch_size]
                
                for subscription in batch:
                    task = self.send_notification(
                        db, subscription, title, body, **kwargs
                    )
                    tasks.append(task)
                
                # Processar batch
                if len(tasks) >= batch_size or i + batch_size >= len(subscriptions):
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    success_count += sum(1 for result in results if result is True)
                    tasks = []
                    
                    # Pequena pausa entre batches
                    await asyncio.sleep(0.1)
            
            logger.info(f"Enviadas {success_count}/{len(subscriptions)} notificações para todos os admins")
            return success_count
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificações para todos os admins: {str(e)}")
            return 0
    
    async def cleanup_invalid_subscriptions(self, db: Session) -> int:
        """
        🧹 Remove subscriptions inativas ou expiradas
        
        Returns:
            Número de subscriptions removidas
        """
        try:
            # Remover subscriptions marcadas como inativas há mais de 7 dias
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            inactive_subscriptions = db.query(PushSubscription).filter(
                and_(
                    PushSubscription.is_active == False,
                    PushSubscription.last_used_at < cutoff_date
                )
            ).all()
            
            count = len(inactive_subscriptions)
            for subscription in inactive_subscriptions:
                db.delete(subscription)
            
            db.commit()
            logger.info(f"Cleanup: removidas {count} subscriptions inativas")
            return count
            
        except Exception as e:
            logger.error(f"Erro no cleanup de subscriptions: {str(e)}")
            db.rollback()
            return 0
    
    async def get_admin_subscriptions(
        self,
        db: Session,
        admin_user_id: int
    ) -> List[PushSubscription]:
        """
        📋 Lista subscriptions de um admin
        """
        return db.query(PushSubscription).filter(
            and_(
                PushSubscription.admin_user_id == admin_user_id,
                PushSubscription.is_active == True
            )
        ).all()
    
    async def get_notification_stats(self, db: Session) -> Dict[str, Any]:
        """
        📊 Estatísticas de push notifications
        """
        try:
            from sqlalchemy import func, desc
            from datetime import timedelta
            
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            
            # Subscriptions ativas
            active_subscriptions = db.query(PushSubscription).filter(
                PushSubscription.is_active == True
            ).count()
            
            # Notificações últimas 24h
            notifications_24h = db.query(PushNotification).filter(
                PushNotification.sent_at >= last_24h
            ).count()
            
            # Notificações últimos 7 dias
            notifications_7d = db.query(PushNotification).filter(
                PushNotification.sent_at >= last_7d
            ).count()
            
            # Taxa de sucesso últimas 24h
            success_24h = db.query(PushNotification).filter(
                and_(
                    PushNotification.sent_at >= last_24h,
                    PushNotification.status == "sent"
                )
            ).count()
            
            success_rate = (success_24h / notifications_24h * 100) if notifications_24h > 0 else 0
            
            # Top admins por notificações recebidas
            top_admins = db.query(
                AdminUser.username,
                func.count(PushNotification.id).label('notification_count')
            ).join(
                PushSubscription, AdminUser.id == PushSubscription.admin_user_id
            ).join(
                PushNotification, PushSubscription.id == PushNotification.subscription_id
            ).filter(
                PushNotification.sent_at >= last_7d
            ).group_by(AdminUser.id, AdminUser.username).order_by(
                desc('notification_count')
            ).limit(5).all()
            
            return {
                "active_subscriptions": active_subscriptions,
                "notifications_24h": notifications_24h,
                "notifications_7d": notifications_7d,
                "success_rate": round(success_rate, 2),
                "top_admins": [
                    {"username": admin.username, "count": admin.notification_count}
                    for admin in top_admins
                ]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {}


# 🔔 Instância global do serviço
push_service = PushNotificationService()


# 🚨 Integração com Sistema de Alertas
async def send_alert_notification(
    db: Session,
    alert_level: str,
    title: str,
    message: str,
    data: Optional[Dict[str, Any]] = None
):
    """
    🚨 Envia push notification para alertas HIGH/CRITICAL
    
    Integra com o sistema de alertas existente.
    """
    if alert_level not in ["HIGH", "CRITICAL"]:
        return  # Só envia para alertas importantes
    
    try:
        # Ícones e configurações por nível
        config = {
            "HIGH": {
                "icon": "/icons/alert-high.png",
                "badge": "/icons/badge-warning.png",
                "tag": "alert-high",
                "require_interaction": False
            },
            "CRITICAL": {
                "icon": "/icons/alert-critical.png",
                "badge": "/icons/badge-error.png",
                "tag": "alert-critical",
                "require_interaction": True  # Requer ação do admin
            }
        }
        
        # Enviar para todos os admins
        await push_service.send_to_all_admins(
            db=db,
            title=f"🚨 {alert_level}: {title}",
            body=message,
            data=data,
            **config[alert_level]
        )
        
        logger.info(f"Push notification enviada para alerta {alert_level}: {title}")
        
    except Exception as e:
        logger.error(f"Erro ao enviar push notification para alerta: {str(e)}")


# 📝 Helper para integração fácil
def get_push_service() -> PushNotificationService:
    """
    🔔 Obtém instância do serviço de push notifications
    """
    return push_service
