from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema de Rate Limiting para proteger APIs
"""
import time
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    max_requests: int = 20  # Máximo de requests (reduzido para testes)
    time_window: int = 60   # Janela de tempo em segundos
    burst_limit: int = 5    # Limite de burst (reduzido para testes)


@dataclass
class ClientInfo:
    requests: list = field(default_factory=list)
    blocked_until: Optional[datetime] = None
    total_requests: int = 0
    blocked_count: int = 0


class RateLimiter:
    """Sistema de rate limiting com diferentes estratégias"""
    
    def __init__(self):
        self.clients: Dict[str, ClientInfo] = {}
        self.global_config = RateLimitConfig()
        self.specific_configs: Dict[str, RateLimitConfig] = {
            "webhook": RateLimitConfig(max_requests=120, time_window=60, burst_limit=20),
            "api": RateLimitConfig(max_requests=30, time_window=60, burst_limit=8),  # Equilibrado para API geral
            "health": RateLimitConfig(max_requests=200, time_window=60, burst_limit=100),  # Permissivo mas com limite
            "default": RateLimitConfig(max_requests=50, time_window=60, burst_limit=15)  # Equilibrado para outros endpoints
        }
    
    def _clean_old_requests(self, client: ClientInfo, time_window: int):
        """Remove requests antigas da janela de tempo"""
        cutoff_time = time.time() - time_window
        client.requests = [req_time for req_time in client.requests if req_time > cutoff_time]
    
    def _is_blocked(self, client: ClientInfo) -> bool:
        """Verifica se cliente está bloqueado"""
        if client.blocked_until is None:
            return False
        
        if datetime.now() > client.blocked_until:
            client.blocked_until = None
            return False
        
        return True
    
    def _block_client(self, client: ClientInfo, duration_seconds: int = 300):
        """Bloqueia cliente por tempo determinado"""
        client.blocked_until = datetime.now() + timedelta(seconds=duration_seconds)
        client.blocked_count += 1
        logger.warning(f"Cliente bloqueado por {duration_seconds}s (total bloqueios: {client.blocked_count})")
    
    async def is_allowed(self, 
                        client_id: str, 
                        endpoint: str = "default",
                        cost: int = 1) -> tuple[bool, dict]:
        """
        Verifica se request é permitida
        
        Args:
            client_id: Identificador do cliente (IP, user_id, etc)
            endpoint: Endpoint sendo acessado
            cost: "Custo" da requisição (algumas podem custar mais)
        
        Returns:
            (is_allowed, info_dict)
        """
        # Obter configuração para o endpoint
        config = self.specific_configs.get(endpoint, self.global_config)
        
        # Obter ou criar info do cliente
        if client_id not in self.clients:
            self.clients[client_id] = ClientInfo()
        
        client = self.clients[client_id]
        current_time = time.time()
        
        # Verificar se está bloqueado
        if self._is_blocked(client):
            return False, {
                "error": "rate_limit_exceeded",
                "message": "Client temporarily blocked",
                "blocked_until": client.blocked_until.isoformat(),
                "retry_after": int((client.blocked_until - datetime.now()).total_seconds())
            }
        
        # Limpar requests antigas
        self._clean_old_requests(client, config.time_window)
        
        # Verificar limite de burst (requests muito próximas)
        recent_requests = len([
            req_time for req_time in client.requests 
            if current_time - req_time < 10  # últimos 10 segundos
        ])
        
        if recent_requests >= config.burst_limit:
            self._block_client(client, duration_seconds=60)  # Bloquear por 1 minuto
            return False, {
                "error": "burst_limit_exceeded",
                "message": f"Too many requests in short time (max {config.burst_limit}/10s)",
                "retry_after": 60
            }
        
        # Verificar limite da janela de tempo
        if len(client.requests) >= config.max_requests:
            # Verificar se deve bloquear por abuso
            if len(client.requests) > config.max_requests * 1.5:
                self._block_client(client, duration_seconds=300)  # 5 minutos
                return False, {
                    "error": "rate_limit_abuse",
                    "message": "Excessive requests - temporarily blocked",
                    "retry_after": 300
                }
            
            # Limite normal atingido
            oldest_request = min(client.requests)
            retry_after = int(config.time_window - (current_time - oldest_request))
            
            return False, {
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded (max {config.max_requests}/{config.time_window}s)",
                "retry_after": max(retry_after, 1),
                "current_requests": len(client.requests),
                "max_requests": config.max_requests
            }
        
        # Request permitida - registrar
        for _ in range(cost):  # Custo pode ser > 1 para operações caras
            client.requests.append(current_time)
        
        client.total_requests += cost
        
        return True, {
            "allowed": True,
            "remaining_requests": config.max_requests - len(client.requests),
            "window_reset": int(current_time + config.time_window),
            "total_requests": client.total_requests
        }
    
    def get_client_stats(self, client_id: str) -> dict:
        """Obtém estatísticas de um cliente"""
        if client_id not in self.clients:
            return {"error": "client_not_found"}
        
        client = self.clients[client_id]
        current_time = time.time()
        
        # Limpar requests antigas para estatística atual
        self._clean_old_requests(client, self.global_config.time_window)
        
        return {
            "client_id": client_id,
            "current_requests": len(client.requests),
            "total_requests": client.total_requests,
            "blocked_count": client.blocked_count,
            "is_blocked": self._is_blocked(client),
            "blocked_until": client.blocked_until.isoformat() if client.blocked_until else None,
            "requests_in_window": len(client.requests)
        }
    
    def get_global_stats(self) -> dict:
        """Obtém estatísticas globais do rate limiter"""
        total_clients = len(self.clients)
        total_requests = sum(client.total_requests for client in self.clients.values())
        blocked_clients = sum(1 for client in self.clients.values() if self._is_blocked(client))
        
        return {
            "total_clients": total_clients,
            "total_requests": total_requests,
            "blocked_clients": blocked_clients,
            "active_clients": total_clients - blocked_clients,
            "configs": {
                name: {
                    "max_requests": config.max_requests,
                    "time_window": config.time_window,
                    "burst_limit": config.burst_limit
                }
                for name, config in self.specific_configs.items()
            }
        }
    
    async def cleanup_old_clients(self, max_age_hours: int = 24):
        """Remove dados de clientes antigos para economizar memória"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        clients_to_remove = []
        
        for client_id, client in self.clients.items():
            # Se não tem requests recentes e não está bloqueado
            if (not client.requests or max(client.requests) < cutoff_time) and not self._is_blocked(client):
                clients_to_remove.append(client_id)
        
        for client_id in clients_to_remove:
            del self.clients[client_id]
        
        if clients_to_remove:
            logger.info(f"Removidos {len(clients_to_remove)} clientes antigos do rate limiter")


# Rate limiter específico para WhatsApp (baseado no wa_id)
class WhatsAppRateLimiter(RateLimiter):
    """Rate limiter específico para mensagens do WhatsApp"""
    
    def __init__(self):
        super().__init__()
        self.specific_configs = {
            "incoming_message": RateLimitConfig(max_requests=20, time_window=60, burst_limit=5),
            "outgoing_message": RateLimitConfig(max_requests=15, time_window=60, burst_limit=3),
            "webhook": RateLimitConfig(max_requests=100, time_window=60, burst_limit=10)
        }
        
        # Configurações específicas por tipo de mensagem
        self.message_type_limits = {
            "audio": {"max_requests": 5, "time_window": 60, "burst_limit": 2},     # 5 áudios por minuto
            "image": {"max_requests": 10, "time_window": 60, "burst_limit": 3},    # 10 imagens por minuto  
            "text": {"max_requests": 30, "time_window": 60, "burst_limit": 8},      # 30 textos por minuto
            "document": {"max_requests": 3, "time_window": 60, "burst_limit": 1},  # 3 documentos por minuto
            "video": {"max_requests": 2, "time_window": 60, "burst_limit": 1},     # 2 vídeos por minuto
            "voice": {"max_requests": 5, "time_window": 60, "burst_limit": 2},     # 5 voices por minuto
            "sticker": {"max_requests": 15, "time_window": 60, "burst_limit": 5},  # 15 stickers por minuto
            "location": {"max_requests": 8, "time_window": 60, "burst_limit": 2},  # 8 localizações por minuto
            "contact": {"max_requests": 5, "time_window": 60, "burst_limit": 2},   # 5 contatos por minuto
            "interactive": {"max_requests": 20, "time_window": 60, "burst_limit": 5} # 20 interações por minuto
        }
    
    async def check_message_type_limit(self, user_id: str, message_type: str) -> tuple[bool, dict]:
        """
        Verifica limites específicos por tipo de mensagem
        
        Args:
            user_id: ID do usuário (wa_id)
            message_type: Tipo da mensagem (text, audio, image, etc.)
            
        Returns:
            tuple[bool, dict]: (is_allowed, limit_info)
        """
        # Obter limites para o tipo de mensagem
        type_limits = self.message_type_limits.get(message_type, self.message_type_limits["text"])
        
        # Criar chave única para o tipo de mensagem do usuário
        client_key = f"user_{user_id}_type_{message_type}"
        
        # Obter ou criar info do cliente
        if client_key not in self.clients:
            self.clients[client_key] = ClientInfo()
        
        client = self.clients[client_key]
        current_time = time.time()
        
        # Verificar se está bloqueado
        if self._is_blocked(client):
            return False, {
                "error": "message_type_rate_limit_exceeded",
                "message": f"Message type '{message_type}' temporarily blocked",
                "message_type": message_type,
                "blocked_until": client.blocked_until.isoformat(),
                "retry_after": int((client.blocked_until - datetime.now()).total_seconds())
            }
        
        # Limpar requests antigas
        self._clean_old_requests(client, type_limits["time_window"])
        
        # Verificar limite de burst (mensagens muito próximas)
        recent_requests = len([
            req_time for req_time in client.requests 
            if current_time - req_time < 10  # últimos 10 segundos
        ])
        
        if recent_requests >= type_limits["burst_limit"]:
            self._block_client(client, duration_seconds=30)  # Bloquear por 30 segundos para tipo específico
            return False, {
                "error": "message_type_burst_limit_exceeded",
                "message": f"Too many {message_type} messages in short time (max {type_limits['burst_limit']}/10s)",
                "message_type": message_type,
                "retry_after": 30,
                "burst_limit": type_limits["burst_limit"]
            }
        
        # Verificar limite da janela de tempo para o tipo
        if len(client.requests) >= type_limits["max_requests"]:
            # Verificar se deve bloquear por abuso
            if len(client.requests) > type_limits["max_requests"] * 2:
                self._block_client(client, duration_seconds=180)  # 3 minutos para abuso de tipo
                return False, {
                    "error": "message_type_abuse",
                    "message": f"Excessive {message_type} messages - temporarily blocked",
                    "message_type": message_type,
                    "retry_after": 180
                }
            
            # Limite normal atingido para o tipo
            oldest_request = min(client.requests)
            retry_after = int(type_limits["time_window"] - (current_time - oldest_request))
            
            return False, {
                "error": "message_type_rate_limit_exceeded",
                "message": f"Rate limit exceeded for {message_type} messages (max {type_limits['max_requests']}/{type_limits['time_window']}s)",
                "message_type": message_type,
                "retry_after": max(retry_after, 1),
                "current_requests": len(client.requests),
                "max_requests": type_limits["max_requests"],
                "time_window": type_limits["time_window"]
            }
        
        # Request permitida - registrar
        client.requests.append(current_time)
        client.total_requests += 1
        
        return True, {
            "allowed": True,
            "message_type": message_type,
            "remaining_requests": type_limits["max_requests"] - len(client.requests),
            "window_reset": int(current_time + type_limits["time_window"]),
            "total_requests": client.total_requests,
            "limits": type_limits
        }
    
    async def check_combined_message_limits(self, user_id: str, message_type: str) -> tuple[bool, dict]:
        """
        Verifica tanto o limite geral de usuário quanto o limite específico do tipo
        
        Args:
            user_id: ID do usuário (wa_id)
            message_type: Tipo da mensagem
            
        Returns:
            tuple[bool, dict]: (is_allowed, combined_info)
        """
        # Verificar limite geral do usuário primeiro
        general_allowed, general_info = await self.check_user_message_limit(user_id)
        
        if not general_allowed:
            # Adicionar informação sobre tipo de mensagem ao erro geral
            general_info["message_type"] = message_type
            general_info["limit_type"] = "general_user_limit"
            return False, general_info
        
        # Verificar limite específico do tipo
        type_allowed, type_info = await self.check_message_type_limit(user_id, message_type)
        
        if not type_allowed:
            # Adicionar informação sobre limite combinado
            type_info["limit_type"] = "message_type_limit"
            return False, type_info
        
        # Combinar informações de sucesso
        combined_info = {
            "allowed": True,
            "message_type": message_type,
            "general_limit": general_info,
            "type_limit": type_info
        }
        
        return True, combined_info
    
    def get_message_type_stats(self, user_id: str, message_type: str = None) -> dict:
        """
        Obtém estatísticas de uso por tipo de mensagem
        
        Args:
            user_id: ID do usuário
            message_type: Tipo específico (opcional, se None retorna todos)
            
        Returns:
            dict: Estatísticas de uso
        """
        stats = {}
        
        if message_type:
            # Estatísticas para tipo específico
            client_key = f"user_{user_id}_type_{message_type}"
            if client_key in self.clients:
                client = self.clients[client_key]
                type_limits = self.message_type_limits.get(message_type, self.message_type_limits["text"])
                
                # Limpar requests antigas para estatística atual
                self._clean_old_requests(client, type_limits["time_window"])
                
                stats[message_type] = {
                    "current_requests": len(client.requests),
                    "total_requests": client.total_requests,
                    "remaining_requests": type_limits["max_requests"] - len(client.requests),
                    "limits": type_limits,
                    "is_blocked": self._is_blocked(client),
                    "blocked_until": client.blocked_until.isoformat() if client.blocked_until else None
                }
            else:
                # Usuário ainda não usou este tipo
                type_limits = self.message_type_limits.get(message_type, self.message_type_limits["text"])
                stats[message_type] = {
                    "current_requests": 0,
                    "total_requests": 0,
                    "remaining_requests": type_limits["max_requests"],
                    "limits": type_limits,
                    "is_blocked": False,
                    "blocked_until": None
                }
        else:
            # Estatísticas para todos os tipos
            for msg_type in self.message_type_limits.keys():
                client_key = f"user_{user_id}_type_{msg_type}"
                type_limits = self.message_type_limits[msg_type]
                
                if client_key in self.clients:
                    client = self.clients[client_key]
                    self._clean_old_requests(client, type_limits["time_window"])
                    
                    stats[msg_type] = {
                        "current_requests": len(client.requests),
                        "total_requests": client.total_requests,
                        "remaining_requests": type_limits["max_requests"] - len(client.requests),
                        "limits": type_limits,
                        "is_blocked": self._is_blocked(client),
                        "blocked_until": client.blocked_until.isoformat() if client.blocked_until else None
                    }
                else:
                    stats[msg_type] = {
                        "current_requests": 0,
                        "total_requests": 0,
                        "remaining_requests": type_limits["max_requests"],
                        "limits": type_limits,
                        "is_blocked": False,
                        "blocked_until": None
                    }
        
        return {
            "user_id": user_id,
            "message_types": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    async def check_user_message_limit(self, wa_id: str) -> tuple[bool, dict]:
        """Verifica limite para mensagens de usuários específicos"""
        return await self.is_allowed(
            client_id=f"user_{wa_id}",
            endpoint="incoming_message",
            cost=1
        )
    
    async def check_outgoing_limit(self, wa_id: str) -> tuple[bool, dict]:
        """Verifica limite para mensagens enviadas"""
        return await self.is_allowed(
            client_id=f"outgoing_{wa_id}",
            endpoint="outgoing_message",
            cost=1
        )


# Instâncias globais
rate_limiter = RateLimiter()
whatsapp_rate_limiter = WhatsAppRateLimiter()
