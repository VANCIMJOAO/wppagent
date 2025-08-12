"""
Rate Limiting rigoroso com múltiplas estratégias e proteção DDoS
Implementa rate limiting por IP, usuário, endpoint e global
"""

import time
import hashlib
import json
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum
import redis
from fastapi import Request
from app.config import get_settings
from app.config.redis_config import redis_manager, execute_redis_safe

# Configurar logger
logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """Tipos de rate limiting"""
    IP = "ip"
    USER = "user" 
    ENDPOINT = "endpoint"
    GLOBAL = "global"
    ADMIN = "admin"

@dataclass
class RateLimit:
    """Configuração de rate limit"""
    requests: int
    window: int  # segundos
    block_duration: int  # segundos de bloqueio

class RateLimiter:
    """Sistema de Rate Limiting rigoroso"""
    
    def __init__(self):
        self.settings = get_settings()
        # Não inicializar Redis diretamente - usar redis_manager
        
        # Configurações de rate limit por tipo
        self.limits = {
            # Rate limits por IP
            RateLimitType.IP: {
                "default": RateLimit(100, 60, 300),      # 100 req/min, block 5min
                "auth": RateLimit(10, 60, 900),          # 10 auth/min, block 15min
                "admin": RateLimit(5, 60, 1800),         # 5 admin/min, block 30min
                "api": RateLimit(200, 60, 180),          # 200 api/min, block 3min
            },
            
            # Rate limits por usuário
            RateLimitType.USER: {
                "default": RateLimit(500, 60, 60),       # 500 req/min, block 1min
                "admin": RateLimit(1000, 60, 30),        # 1000 req/min, block 30s
                "upload": RateLimit(10, 300, 600),       # 10 uploads/5min, block 10min
                "message": RateLimit(50, 60, 120),       # 50 messages/min, block 2min
            },
            
            # Rate limits por endpoint
            RateLimitType.ENDPOINT: {
                "/auth/login": RateLimit(5, 300, 900),         # 5 login/5min
                "/auth/2fa": RateLimit(10, 300, 600),          # 10 2fa/5min
                "/auth/refresh": RateLimit(20, 60, 300),       # 20 refresh/min
                "/webhook": RateLimit(1000, 60, 60),           # 1000 webhook/min
                "/admin/*": RateLimit(100, 60, 300),           # 100 admin/min
            },
            
            # Rate limit global
            RateLimitType.GLOBAL: {
                "total": RateLimit(10000, 60, 30),       # 10k req/min global
                "auth": RateLimit(1000, 60, 60),         # 1k auth/min global
            }
        }
        
        # Configurações de proteção DDoS
        self.ddos_threshold = RateLimit(1000, 60, 3600)  # 1k req/min = DDoS
        self.suspicious_threshold = RateLimit(500, 60, 600)  # 500 req/min = suspeito
    
    def check_rate_limit(self, request: Request, user_id: Optional[str] = None,
                        endpoint_type: str = "default") -> Tuple[bool, Dict]:
        """Verifica todos os rate limits aplicáveis"""
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        
        results = {
            "allowed": True,
            "checks": [],
            "blocked_by": None,
            "retry_after": 0
        }
        
        # 1. Verificar DDoS protection
        ddos_result = self._check_ddos_protection(client_ip)
        if not ddos_result["allowed"]:
            results.update(ddos_result)
            return False, results
        
        # 2. Verificar rate limit por IP
        ip_result = self._check_ip_rate_limit(client_ip, endpoint_type)
        results["checks"].append(("IP", ip_result))
        if not ip_result["allowed"]:
            results.update(ip_result)
            return False, results
        
        # 3. Verificar rate limit por usuário (se autenticado)
        if user_id:
            user_result = self._check_user_rate_limit(user_id, endpoint_type)
            results["checks"].append(("USER", user_result))
            if not user_result["allowed"]:
                results.update(user_result)
                return False, results
        
        # 4. Verificar rate limit por endpoint
        endpoint_result = self._check_endpoint_rate_limit(endpoint)
        results["checks"].append(("ENDPOINT", endpoint_result))
        if not endpoint_result["allowed"]:
            results.update(endpoint_result)
            return False, results
        
        # 5. Verificar rate limit global
        global_result = self._check_global_rate_limit(endpoint_type)
        results["checks"].append(("GLOBAL", global_result))
        if not global_result["allowed"]:
            results.update(global_result)
            return False, results
        
        # Registrar requisição bem-sucedida
        self._record_request(client_ip, user_id, endpoint, endpoint_type)
        
        return True, results
    
    def _check_ddos_protection(self, client_ip: str) -> Dict:
        """Proteção contra DDoS"""
        if not redis_manager.is_available:
            # Quando Redis não está disponível, usar fallback mais permissivo
            return {"allowed": True, "message": "Redis unavailable, DDoS protection disabled"}
        
        key = f"ddos:ip:{client_ip}"
        current_time = int(time.time())
        window_start = current_time - self.ddos_threshold.window
        
        def ddos_check(client):
            # Limpar entradas antigas
            client.zremrangebyscore(key, 0, window_start)
            # Contar requisições na janela
            return client.zcard(key)
        
        request_count = execute_redis_safe(ddos_check)
        if request_count is None:
            return {"allowed": True, "message": "Redis operation failed, allowing request"}
        
        if request_count >= self.ddos_threshold.requests:
            # Bloquear IP por DDoS
            def block_ip(client):
                block_key = f"blocked:ddos:{client_ip}"
                client.setex(block_key, self.ddos_threshold.block_duration, "ddos")
            
            execute_redis_safe(block_ip)
            
            # Log de segurança
            self._log_security_event("ddos_detected", {
                "ip": client_ip,
                "request_count": request_count,
                "window": self.ddos_threshold.window
            })
            
            return {
                "allowed": False,
                "blocked_by": "DDoS Protection",
                "retry_after": self.ddos_threshold.block_duration,
                "reason": f"DDoS detected: {request_count} requests in {self.ddos_threshold.window}s"
            }
        
        # Adicionar requisição atual
        def add_request(client):
            client.zadd(key, {str(current_time): current_time})
            client.expire(key, self.ddos_threshold.window)
        
        execute_redis_safe(add_request)
        return {"allowed": True}
    
    def _check_ip_rate_limit(self, client_ip: str, endpoint_type: str) -> Dict:
        """Rate limit por IP"""
        if not redis_manager.is_available:
            return {"allowed": True, "message": "Redis unavailable, IP rate limiting disabled"}
        
        # Verificar se IP está bloqueado
        block_key = f"blocked:ip:{client_ip}"
        
        def check_blocked(client):
            if client.exists(block_key):
                return client.ttl(block_key)
            return None
        
        ttl = execute_redis_safe(check_blocked)
        if ttl and ttl > 0:
            return {
                "allowed": False,
                "blocked_by": "IP Rate Limit",
                "retry_after": ttl,
                "reason": "IP temporarily blocked"
            }
        
        # Obter configuração do rate limit
        limit_config = self.limits[RateLimitType.IP].get(
            endpoint_type, 
            self.limits[RateLimitType.IP]["default"]
        )
        
        return self._check_sliding_window_limit(
            f"rate:ip:{client_ip}:{endpoint_type}",
            limit_config,
            f"blocked:ip:{client_ip}"
        )
    
    def _check_user_rate_limit(self, user_id: str, endpoint_type: str) -> Dict:
        """Rate limit por usuário"""
        block_key = f"blocked:user:{user_id}"
        if self.redis_client.exists(block_key):
            ttl = self.redis_client.ttl(block_key)
            return {
                "allowed": False,
                "blocked_by": "User Rate Limit",
                "retry_after": ttl,
                "reason": "User temporarily blocked"
            }
        
        limit_config = self.limits[RateLimitType.USER].get(
            endpoint_type,
            self.limits[RateLimitType.USER]["default"]
        )
        
        return self._check_sliding_window_limit(
            f"rate:user:{user_id}:{endpoint_type}",
            limit_config,
            f"blocked:user:{user_id}"
        )
    
    def _check_endpoint_rate_limit(self, endpoint: str) -> Dict:
        """Rate limit por endpoint"""
        # Encontrar configuração matching
        limit_config = None
        for pattern, config in self.limits[RateLimitType.ENDPOINT].items():
            if pattern.endswith("*"):
                if endpoint.startswith(pattern[:-1]):
                    limit_config = config
                    break
            elif endpoint == pattern:
                limit_config = config
                break
        
        if not limit_config:
            return {"allowed": True}
        
        return self._check_sliding_window_limit(
            f"rate:endpoint:{endpoint}",
            limit_config,
            f"blocked:endpoint:{endpoint}"
        )
    
    def _check_global_rate_limit(self, endpoint_type: str) -> Dict:
        """Rate limit global"""
        limit_config = self.limits[RateLimitType.GLOBAL].get(
            endpoint_type,
            self.limits[RateLimitType.GLOBAL]["total"]
        )
        
        return self._check_sliding_window_limit(
            f"rate:global:{endpoint_type}",
            limit_config,
            "blocked:global"
        )
    
    def _check_sliding_window_limit(self, key: str, limit: RateLimit, 
                                   block_key: str) -> Dict:
        """Implementa sliding window rate limiting"""
        current_time = int(time.time())
        window_start = current_time - limit.window
        
        # Limpar entradas antigas
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Contar requisições na janela
        request_count = self.redis_client.zcard(key)
        
        if request_count >= limit.requests:
            # Bloquear
            self.redis_client.setex(block_key, limit.block_duration, "rate_limited")
            
            return {
                "allowed": False,
                "blocked_by": "Rate Limit",
                "retry_after": limit.block_duration,
                "reason": f"Rate limit exceeded: {request_count}/{limit.requests} in {limit.window}s"
            }
        
        # Adicionar requisição atual
        self.redis_client.zadd(key, {str(current_time): current_time})
        self.redis_client.expire(key, limit.window)
        
        return {
            "allowed": True,
            "remaining": limit.requests - request_count - 1,
            "reset_time": window_start + limit.window
        }
    
    def _record_request(self, client_ip: str, user_id: Optional[str], 
                       endpoint: str, endpoint_type: str):
        """Registra requisição para analytics"""
        timestamp = int(time.time())
        
        # Registrar métricas
        metrics_key = f"metrics:requests:{timestamp // 60}"  # Por minuto
        self.redis_client.hincrby(metrics_key, "total", 1)
        self.redis_client.hincrby(metrics_key, f"endpoint_type:{endpoint_type}", 1)
        self.redis_client.expire(metrics_key, 3600)  # 1 hora
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP real do cliente considerando proxies"""
        # Verificar headers de proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _log_security_event(self, event_type: str, data: Dict):
        """Log eventos de segurança"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "data": data
        }
        
        # Salvar no Redis para análise
        self.redis_client.lpush("security:events", json.dumps(event))
        self.redis_client.ltrim("security:events", 0, 10000)  # Manter últimos 10k eventos
    
    def unblock_ip(self, client_ip: str) -> bool:
        """Remove bloqueio de IP"""
        keys_to_delete = [
            f"blocked:ip:{client_ip}",
            f"blocked:ddos:{client_ip}"
        ]
        
        deleted = 0
        for key in keys_to_delete:
            if self.redis_client.delete(key):
                deleted += 1
        
        return deleted > 0
    
    def unblock_user(self, user_id: str) -> bool:
        """Remove bloqueio de usuário"""
        return self.redis_client.delete(f"blocked:user:{user_id}") > 0
    
    def get_rate_limit_status(self, request: Request, 
                             user_id: Optional[str] = None) -> Dict:
        """Retorna status atual dos rate limits"""
        client_ip = self._get_client_ip(request)
        
        status = {
            "ip": self._get_limit_status(f"rate:ip:{client_ip}", 
                                       self.limits[RateLimitType.IP]["default"]),
            "blocked_ips": [],
            "blocked_users": []
        }
        
        if user_id:
            status["user"] = self._get_limit_status(f"rate:user:{user_id}", 
                                                  self.limits[RateLimitType.USER]["default"])
        
        # Verificar bloqueios ativos
        if self.redis_client.exists(f"blocked:ip:{client_ip}"):
            status["blocked_ips"].append({
                "ip": client_ip,
                "ttl": self.redis_client.ttl(f"blocked:ip:{client_ip}")
            })
        
        return status
    
    def _get_limit_status(self, key: str, limit: RateLimit) -> Dict:
        """Obtém status de um rate limit específico"""
        current_time = int(time.time())
        window_start = current_time - limit.window
        
        # Limpar entradas antigas
        self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Contar requisições
        request_count = self.redis_client.zcard(key)
        
        return {
            "requests_made": request_count,
            "requests_limit": limit.requests,
            "window_seconds": limit.window,
            "remaining": max(0, limit.requests - request_count),
            "reset_time": window_start + limit.window
        }
    
    def get_security_events(self, limit: int = 100) -> List[Dict]:
        """Retorna eventos de segurança recentes"""
        events = self.redis_client.lrange("security:events", 0, limit - 1)
        return [json.loads(event.decode()) for event in events]


# Instance global
rate_limiter = RateLimiter()
