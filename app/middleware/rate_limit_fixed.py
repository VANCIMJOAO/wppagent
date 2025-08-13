"""
Middleware de Rate Limiting para FastAPI - Versão Corrigida
"""
import time
import logging
from typing import Callable, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)

# Importações de rate limiters com fallback
try:
    from app.services.rate_limiter import rate_limiter, whatsapp_rate_limiter
    RATE_LIMITERS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import rate limiters: {e}")
    rate_limiter = None
    whatsapp_rate_limiter = None
    RATE_LIMITERS_AVAILABLE = False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware que aplica rate limiting automaticamente"""
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled and RATE_LIMITERS_AVAILABLE
        
        if not self.enabled:
            logger.warning("Rate limiting middleware disabled due to missing dependencies or explicit disable")
        
        # Mapeamento de rotas para configurações específicas
        self.route_configs = {}
        if self.enabled:
            self.route_configs = {
                "/webhook": {"limiter": whatsapp_rate_limiter, "endpoint": "webhook"},
                "/api/": {"limiter": rate_limiter, "endpoint": "api"},
                "/health": {"limiter": rate_limiter, "endpoint": "health"},
            }
    
    def _get_client_id(self, request: Request) -> str:
        """Extrai identificador único do cliente"""
        try:
            # 1. Header personalizado
            if "X-Client-ID" in request.headers:
                return f"custom_{request.headers['X-Client-ID']}"
            
            # 2. User agent + IP (para identificar bots específicos)
            user_agent = request.headers.get("user-agent", "unknown")
            if "WhatsApp" in user_agent:
                return f"whatsapp_{self._get_real_ip(request)}"
            
            # 3. IP real do cliente
            return f"ip_{self._get_real_ip(request)}"
        except Exception as e:
            logger.error(f"Error getting client ID: {e}")
            return "unknown"
    
    def _get_real_ip(self, request: Request) -> str:
        """Obtém IP real do cliente considerando proxies"""
        try:
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
        except Exception:
            return "unknown"
    
    def _get_route_config(self, path: str) -> Optional[dict]:
        """Determina configuração de rate limiting para a rota"""
        try:
            # Se middleware desabilitado, retornar None
            if not self.enabled:
                return None
                
            # Verificar rotas específicas
            for route_pattern, config in self.route_configs.items():
                if path.startswith(route_pattern):
                    # Validar que a configuração tem os campos necessários
                    if ("limiter" in config and "endpoint" in config and 
                        config["limiter"] is not None):
                        return config
                    else:
                        logger.warning(f"Invalid config for route {route_pattern}: {config}")
            
            # Configuração padrão - tentar usar o rate_limiter global
            if rate_limiter is not None:
                return {"limiter": rate_limiter, "endpoint": "default"}
            else:
                logger.warning("No rate limiter available for default configuration")
                return None
                
        except Exception as e:
            logger.error(f"Error getting route config for {path}: {e}")
            return None
    
    def _should_skip_rate_limit(self, request: Request) -> bool:
        """Determina se deve pular rate limiting para esta request"""
        try:
            # Pular apenas para metrics internos, mas não para health checks
            if request.url.path in ["/metrics"] and self._is_internal_request(request):
                return True
            
            # Pular rate limiting para o endpoint de teste de performance
            if (request.url.path == "/health" and 
                request.headers.get("X-Performance-Test") == "true"):
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking if should skip rate limit: {e}")
            return False
    
    def _is_internal_request(self, request: Request) -> bool:
        """Verifica se é uma request interna/local"""
        try:
            client_ip = self._get_real_ip(request)
            
            # IPs locais/privados
            local_ips = ["127.0.0.1", "localhost", "::1"]
            private_ranges = ["10.", "172.", "192.168."]
            
            if client_ip in local_ips:
                return True
            
            return any(client_ip.startswith(range_start) for range_start in private_ranges)
        except Exception as e:
            logger.error(f"Error checking if internal request: {e}")
            return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Processa a request aplicando rate limiting"""
        
        # Se middleware desabilitado ou deve pular, continuar normalmente
        if not self.enabled or self._should_skip_rate_limit(request):
            try:
                response = await call_next(request)
                # Garantir que temos uma resposta válida
                if response is None:
                    logger.error(f"call_next returned None for {request.url.path}")
                    return JSONResponse(
                        status_code=500,
                        content={"error": "no_response", "message": "No response generated"}
                    )
                return response
            except Exception as e:
                logger.error(f"Error in bypassed request: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "request_processing_failed", "message": str(e)}
                )
        
        start_time = time.time()
        
        try:
            # Obter configuração para esta rota
            route_config = self._get_route_config(request.url.path)
            if not route_config:
                logger.debug(f"No rate limit config for {request.url.path}, allowing request")
                response = await call_next(request)
                if response is None:
                    logger.error(f"call_next returned None for {request.url.path}")
                    return JSONResponse(
                        status_code=500,
                        content={"error": "no_response", "message": "No response generated"}
                    )
                return response
                
            limiter = route_config["limiter"]
            endpoint = route_config["endpoint"]
            
            # Validar que o limiter existe e tem método is_allowed
            if not hasattr(limiter, 'is_allowed'):
                logger.warning(f"Invalid limiter for {request.url.path}, allowing request")
                response = await call_next(request)
                if response is None:
                    logger.error(f"call_next returned None for {request.url.path}")
                    return JSONResponse(
                        status_code=500,
                        content={"error": "no_response", "message": "No response generated"}
                    )
                return response
            
            # Obter identificador do cliente
            client_id = self._get_client_id(request)
            
            # Verificar rate limit
            try:
                result = await limiter.is_allowed(
                    client_id=client_id,
                    endpoint=endpoint,
                    cost=1
                )
                # Verificar se o resultado é uma tupla válida
                if not isinstance(result, tuple) or len(result) != 2:
                    logger.error(f"Invalid rate limiter response: {result}")
                    response = await call_next(request)
                    if response is None:
                        return JSONResponse(
                            status_code=500,
                            content={"error": "no_response", "message": "No response generated"}
                        )
                    return response
                    
                is_allowed, limit_info = result
                
            except Exception as limiter_error:
                logger.error(f"Rate limiter error: {limiter_error}, allowing request")
                response = await call_next(request)
                if response is None:
                    logger.error(f"call_next returned None after limiter error for {request.url.path}")
                    return JSONResponse(
                        status_code=500,
                        content={"error": "no_response", "message": "No response generated"}
                    )
                return response
            
            if not is_allowed:
                logger.warning(
                    f"Rate limit exceeded for {client_id} on {request.url.path}: {limit_info}"
                )
                
                # Retornar erro de rate limit
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": limit_info.get("message", "Too many requests") if limit_info else "Too many requests",
                        "retry_after": limit_info.get("retry_after", 60) if limit_info else 60,
                        "details": limit_info
                    },
                    headers={
                        "Retry-After": str(limit_info.get("retry_after", 60) if limit_info else 60),
                        "X-RateLimit-Limit": str(limit_info.get("max_requests", "unknown") if limit_info else "unknown"),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(limit_info.get("window_reset", int(time.time() + 60)) if limit_info else int(time.time() + 60))
                    }
                )
            
            # Request permitida - processar normalmente
            response = await call_next(request)
            
            # Verificar se temos uma resposta válida
            if response is None:
                logger.error(f"call_next returned None for {request.url.path}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "no_response", "message": "No response generated"}
                )
            
            # Adicionar headers informativos se possível
            if limit_info and isinstance(limit_info, dict):
                try:
                    if "remaining_requests" in limit_info:
                        response.headers["X-RateLimit-Limit"] = str(limit_info.get("max_requests", "unknown"))
                        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining_requests"])
                        response.headers["X-RateLimit-Reset"] = str(limit_info.get("window_reset", "unknown"))
                except Exception as header_error:
                    logger.warning(f"Failed to add rate limit headers: {header_error}")
            
            # Log da request processada
            try:
                process_time = time.time() - start_time
                remaining = limit_info.get('remaining_requests', 'unknown') if limit_info else 'unknown'
                logger.info(
                    f"Request processed: {request.method} {request.url.path} "
                    f"from {client_id} in {process_time:.3f}s (remaining: {remaining})"
                )
            except Exception as log_error:
                logger.warning(f"Failed to log request processing: {log_error}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {e}", exc_info=True)
            # Em caso de erro no middleware, tentar permitir a request
            try:
                response = await call_next(request)
                if response is None:
                    logger.error(f"call_next returned None after middleware error for {request.url.path}")
                    return JSONResponse(
                        status_code=500,
                        content={"error": "no_response", "message": "No response generated after middleware error"}
                    )
                return response
            except Exception as call_error:
                logger.error(f"Failed to process request after middleware error: {call_error}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "middleware_error", 
                        "message": "Rate limiting middleware encountered an error"
                    }
                )


def get_rate_limit_stats():
    """Obtém estatísticas consolidadas de rate limiting"""
    try:
        if not RATE_LIMITERS_AVAILABLE:
            return {"error": "rate_limiters_not_available"}
        
        stats = {}
        if rate_limiter:
            stats["global_rate_limiter"] = rate_limiter.get_global_stats()
        if whatsapp_rate_limiter:
            stats["whatsapp_rate_limiter"] = whatsapp_rate_limiter.get_global_stats()
        
        stats["timestamp"] = time.time()
        return stats
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        return {"error": str(e)}
