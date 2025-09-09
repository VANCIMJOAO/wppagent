"""
🔄 WebSocket Cache Synchronization Service
=========================================

Serviço para sincronização de cache em tempo real via WebSocket,
notificando frontend sobre invalidações para atualização automática.

Funcionalidades:
- Broadcast de eventos de cache invalidation
- Gerenciamento de conexões WebSocket
- Filtragem por tipo de evento
- Auto-reconnect handling
- Métricas de conexão

Autor: Claude AI
Status: Solução crítica para real-time cache consistency
"""

import json
import asyncio
from datetime import datetime
from typing import List, Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from app.services.cache_invalidation import CacheEvent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WebSocketCacheSync:
    """
    🔗 Serviço de Sincronização WebSocket para Cache
    
    Gerencia conexões WebSocket e broadcasts de eventos de invalidação
    para manter frontend sincronizado em tempo real.
    """
    
    def __init__(self):
        # Conexões ativas por ID
        self.connections: Dict[str, WebSocket] = {}
        
        # Subscriptions por tipo de evento
        self.event_subscriptions: Dict[str, Set[str]] = {}
        
        # Métricas
        self.metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "connection_errors": 0,
            "broadcasts_sent": 0
        }
        
        # Configurações
        self.max_connections = 1000
        self.heartbeat_interval = 30  # segundos
        
        logger.info("🔗 WebSocketCacheSync inicializado")
    
    async def connect(self, websocket: WebSocket, connection_id: str, 
                     subscriptions: Optional[List[str]] = None) -> bool:
        """
        🔌 Conecta novo WebSocket client
        
        Args:
            websocket: Instância do WebSocket
            connection_id: ID único da conexão
            subscriptions: Lista de eventos para se inscrever
        
        Returns:
            bool: True se conexão foi aceita
        """
        try:
            # Verificar limite de conexões
            if len(self.connections) >= self.max_connections:
                await websocket.close(code=1013, reason="Too many connections")
                return False
            
            # Aceitar conexão
            await websocket.accept()
            
            # Armazenar conexão
            self.connections[connection_id] = websocket
            
            # Configurar subscriptions
            if subscriptions:
                for event_type in subscriptions:
                    if event_type not in self.event_subscriptions:
                        self.event_subscriptions[event_type] = set()
                    self.event_subscriptions[event_type].add(connection_id)
            else:
                # Se não especificar, se inscrever em todos
                for event in CacheEvent:
                    if event.value not in self.event_subscriptions:
                        self.event_subscriptions[event.value] = set()
                    self.event_subscriptions[event.value].add(connection_id)
            
            # Atualizar métricas
            self.metrics["total_connections"] += 1
            self.metrics["active_connections"] = len(self.connections)
            
            # Enviar mensagem de boas-vindas
            await self.send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "subscriptions": subscriptions or "all",
                "server_time": datetime.utcnow().isoformat()
            })
            
            logger.info(f"🔌 WebSocket conectado: {connection_id} (Total: {len(self.connections)})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar WebSocket {connection_id}: {e}")
            return False
    
    async def disconnect(self, connection_id: str):
        """
        🔌 Desconecta WebSocket client
        
        Args:
            connection_id: ID da conexão a ser removida
        """
        try:
            # Remover conexão
            if connection_id in self.connections:
                del self.connections[connection_id]
            
            # Remover de subscriptions
            for event_subs in self.event_subscriptions.values():
                event_subs.discard(connection_id)
            
            # Atualizar métricas
            self.metrics["active_connections"] = len(self.connections)
            
            logger.info(f"🔌 WebSocket desconectado: {connection_id} (Total: {len(self.connections)})")
            
        except Exception as e:
            logger.error(f"❌ Erro ao desconectar WebSocket {connection_id}: {e}")
    
    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        📤 Envia mensagem para conexão específica
        
        Args:
            connection_id: ID da conexão
            message: Mensagem a ser enviada
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            if connection_id not in self.connections:
                return False
            
            websocket = self.connections[connection_id]
            await websocket.send_json(message)
            
            self.metrics["messages_sent"] += 1
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem para {connection_id}: {e}")
            self.metrics["connection_errors"] += 1
            await self.disconnect(connection_id)
            return False
    
    async def broadcast_cache_invalidation(self, event: CacheEvent, 
                                         entity_id: Optional[int] = None,
                                         context: Optional[Dict[str, Any]] = None):
        """
        📢 Faz broadcast de evento de cache invalidation
        
        Args:
            event: Tipo do evento de cache
            entity_id: ID da entidade afetada
            context: Context adicional do evento
        """
        try:
            # Preparar mensagem
            message = {
                "type": "cache_invalidated",
                "event": event.value,
                "entity_id": entity_id,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat(),
                "server_id": "whatsapp_agent_server"
            }
            
            # Encontrar conexões interessadas neste evento
            interested_connections = set()
            
            # Conexões inscritas especificamente neste evento
            if event.value in self.event_subscriptions:
                interested_connections.update(self.event_subscriptions[event.value])
            
            # Conexões inscritas em "all"
            if "all" in self.event_subscriptions:
                interested_connections.update(self.event_subscriptions["all"])
            
            # Enviar para todas as conexões interessadas
            successful_sends = 0
            failed_sends = 0
            
            send_tasks = []
            for connection_id in interested_connections:
                task = self.send_to_connection(connection_id, message)
                send_tasks.append(task)
            
            # Executar sends em paralelo
            if send_tasks:
                results = await asyncio.gather(*send_tasks, return_exceptions=True)
                successful_sends = sum(1 for r in results if r is True)
                failed_sends = len(results) - successful_sends
            
            # Atualizar métricas
            self.metrics["broadcasts_sent"] += 1
            
            logger.debug(f"📢 Cache invalidation broadcast: {event.value} "
                        f"(✅{successful_sends} ❌{failed_sends})")
            
            return {
                "event": event.value,
                "successful_sends": successful_sends,
                "failed_sends": failed_sends,
                "total_connections": len(interested_connections)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no broadcast de cache invalidation: {e}")
            return {
                "event": event.value,
                "error": str(e),
                "successful_sends": 0,
                "failed_sends": 0
            }
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> Dict[str, int]:
        """
        📢 Faz broadcast para todas as conexões ativas
        
        Args:
            message: Mensagem a ser enviada
            
        Returns:
            Dict com estatísticas do broadcast
        """
        successful = 0
        failed = 0
        
        send_tasks = []
        for connection_id in list(self.connections.keys()):
            task = self.send_to_connection(connection_id, message)
            send_tasks.append(task)
        
        if send_tasks:
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            successful = sum(1 for r in results if r is True)
            failed = len(results) - successful
        
        return {
            "successful_sends": successful,
            "failed_sends": failed,
            "total_attempts": len(send_tasks)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        🏥 Verifica saúde das conexões WebSocket
        
        Returns:
            Dict com informações de saúde
        """
        # Verificar conexões mortas
        dead_connections = []
        
        for connection_id, websocket in list(self.connections.items()):
            try:
                # Tentar ping
                await websocket.ping()
            except:
                dead_connections.append(connection_id)
        
        # Remover conexões mortas
        for connection_id in dead_connections:
            await self.disconnect(connection_id)
        
        return {
            "status": "healthy" if len(self.connections) > 0 else "no_connections",
            "active_connections": len(self.connections),
            "dead_connections_removed": len(dead_connections),
            "event_subscriptions": {
                event: len(subs) for event, subs in self.event_subscriptions.items()
            },
            "metrics": self.metrics.copy(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def start_heartbeat(self):
        """
        💗 Inicia heartbeat para manter conexões vivas
        """
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Enviar heartbeat para todas as conexões
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "server_uptime": "running"
                }
                
                result = await self.broadcast_to_all(heartbeat_message)
                logger.debug(f"💗 Heartbeat enviado: ✅{result['successful_sends']} "
                           f"❌{result['failed_sends']}")
                
            except asyncio.CancelledError:
                logger.info("💗 Heartbeat cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Erro no heartbeat: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        📊 Retorna métricas do serviço WebSocket
        """
        return {
            **self.metrics,
            "active_connections": len(self.connections),
            "event_subscriptions_count": len(self.event_subscriptions),
            "timestamp": datetime.utcnow().isoformat()
        }


# ===== SINGLETON INSTANCE =====

websocket_cache_sync = WebSocketCacheSync()


# ===== INTEGRATION HELPERS =====

async def notify_cache_invalidation(event: CacheEvent, 
                                  entity_id: Optional[int] = None,
                                  context: Optional[Dict[str, Any]] = None):
    """
    🔔 Helper para notificar cache invalidation via WebSocket
    
    Args:
        event: Evento de cache invalidation
        entity_id: ID da entidade afetada
        context: Context adicional
    """
    try:
        return await websocket_cache_sync.broadcast_cache_invalidation(
            event, entity_id, context
        )
    except Exception as e:
        logger.error(f"❌ Falha na notificação WebSocket: {e}")
        return {"error": str(e)}


async def setup_websocket_integration():
    """
    🔧 Configura integração do WebSocket com cache invalidation service
    """
    # Iniciar heartbeat em background
    asyncio.create_task(websocket_cache_sync.start_heartbeat())
    
    logger.info("🔧 WebSocket integration configurada")


# ===== LOGGING =====

def log_websocket_status():
    """📊 Log status das conexões WebSocket"""
    metrics = websocket_cache_sync.get_metrics()
    
    logger.info("📊 WebSocket Status:")
    logger.info(f"  🔌 Conexões ativas: {metrics['active_connections']}")
    logger.info(f"  📤 Mensagens enviadas: {metrics['messages_sent']}")
    logger.info(f"  📢 Broadcasts realizados: {metrics['broadcasts_sent']}")
    if metrics['connection_errors'] > 0:
        logger.warning(f"  ❌ Erros de conexão: {metrics['connection_errors']}")
