"""
Middleware de Rate Limiting para FastAPI
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.rate_limiter import rate_limiter, whatsapp_rate_limiter
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware que aplica rate limiting automaticamente"""
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        
        # Mapeamento de rotas para configurações específicas
        self.route_configs = {
            "/webhook": {"limiter": whatsapp_rate_limiter, "endpoint": "webhook"},
            "/api/": {"limiter": rate_limiter, "endpoint": "api"},
            "/health": {"limiter": rate_limiter, "endpoint": "health"},  # Rate limiting ativo para health
        }
    
    def _get_client_id(self, request: Request) -> str:
        """Extrai identificador único do cliente"""
        # Tentar diferentes métodos de identificação
        
        # 1. Header personalizado
        if "X-Client-ID" in request.headers:
            return f"custom_{request.headers['X-Client-ID']}"
        
        # 2. User agent + IP (para identificar bots específicos)
        user_agent = request.headers.get("user-agent", "unknown")
        if "WhatsApp" in user_agent:
            return f"whatsapp_{self._get_real_ip(request)}"
        
        # 3. IP real do cliente
        return f"ip_{self._get_real_ip(request)}"
    
    def _get_real_ip(self, request: Request) -> str:
        """Obtém IP real do cliente considerando proxies"""
        # Verificar headers de proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Pegar o primeiro IP (cliente original)
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback para IP da conexão
        return request.client.host if request.client else "unknown"
    
    def _get_route_config(self, path: str) -> dict:
        """Determina configuração de rate limiting para a rota"""
        # Verificar rotas específicas
        for route_pattern, config in self.route_configs.items():
            if path.startswith(route_pattern):
                return config
        
        # Configuração padrão
        return {"limiter": rate_limiter, "endpoint": "default"}
    
    def _should_skip_rate_limit(self, request: Request) -> bool:
        """Determina se deve pular rate limiting para esta request"""
        # Pular apenas para metrics internos, mas não para health checks
        if request.url.path in ["/metrics"] and self._is_internal_request(request):
            return True
        
        # Pular rate limiting para o endpoint de teste de performance
        if request.url.path == "/health" and request.headers.get("X-Performance-Test") == "true":
            return True
        
        # Não pular mais para requests de desenvolvimento - sempre aplicar rate limiting
        return False
    
    def _is_internal_request(self, request: Request) -> bool:
        """Verifica se é uma request interna/local"""
        client_ip = self._get_real_ip(request)
        
        # IPs locais/privados
        local_ips = ["127.0.0.1", "localhost", "::1"]
        private_ranges = ["10.", "172.", "192.168."]
        
        if client_ip in local_ips:
            return True
        
        return any(client_ip.startswith(range_start) for range_start in private_ranges)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa a request aplicando rate limiting"""
        
        if not self.enabled or self._should_skip_rate_limit(request):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            # Obter configuração para esta rota
            route_config = self._get_route_config(request.url.path)
            limiter = route_config["limiter"]
            endpoint = route_config["endpoint"]
            
            # Obter identificador do cliente
            client_id = self._get_client_id(request)
            
            # Verificar rate limit
            is_allowed, limit_info = await limiter.is_allowed(
                client_id=client_id,
                endpoint=endpoint,
                cost=1
            )
            
            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded for {client_id} on {request.url.path}: {limit_info}"
                )
                
                # Retornar erro de rate limit
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": limit_info.get("message", "Too many requests"),
                        "retry_after": limit_info.get("retry_after", 60),
                        "details": limit_info
                    },
                    headers={
                        "Retry-After": str(limit_info.get("retry_after", 60)),
                        "X-RateLimit-Limit": str(limit_info.get("max_requests", "unknown")),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(limit_info.get("window_reset", int(time.time() + 60)))
                    }
                )
            
            # Request permitida - processar normalmente
            response = await call_next(request)
            
            # Adicionar headers informativos
            if "remaining_requests" in limit_info:
                response.headers["X-RateLimit-Limit"] = str(limit_info.get("max_requests", "unknown"))
                response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining_requests"])
                response.headers["X-RateLimit-Reset"] = str(limit_info.get("window_reset", "unknown"))
            
            # Log da request processada
            process_time = time.time() - start_time
            logger.info(
                f"Request processed: {request.method} {request.url.path} "
                f"from {client_id} in {process_time:.3f}s "
                f"(remaining: {limit_info.get('remaining_requests', 'unknown')})"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {e}")
            # Em caso de erro no middleware, permitir a request
            return await call_next(request)


def get_rate_limit_stats():
    """Obtém estatísticas consolidadas de rate limiting"""
    return {
        "global_rate_limiter": rate_limiter.get_global_stats(),
        "whatsapp_rate_limiter": whatsapp_rate_limiter.get_global_stats(),
        "timestamp": time.time()
    }
