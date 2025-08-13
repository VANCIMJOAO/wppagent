"""
Middleware de Rate Limiting Simples e Robusto
"""
import time
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware simples de rate limiting que sempre retorna uma resposta"""
    
    def __init__(self, app, enabled: bool = False):  # Desabilitado por padrão
        super().__init__(app)
        self.enabled = enabled
        self.requests_count: Dict[str, Dict[str, Any]] = {}
        
        # Configurações simples
        self.max_requests = 100  # Limite alto para desenvolvimento
        self.time_window = 60    # 1 minuto
        
    def _get_client_id(self, request: Request) -> str:
        """Extrai identificador do cliente"""
        try:
            # IP real do cliente
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip
            
            return request.client.host if request.client else "unknown"
        except Exception:
            return "unknown"
    
    def _should_skip(self, request: Request) -> bool:
        """Verifica se deve pular rate limiting"""
        # Pular para rotas de sistema
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json"]
        return request.url.path in skip_paths
    
    def _check_rate_limit(self, client_id: str) -> tuple[bool, dict]:
        """Verifica se o cliente está dentro do limite"""
        try:
            current_time = time.time()
            
            # Limpar entradas antigas
            if client_id in self.requests_count:
                self.requests_count[client_id]["requests"] = [
                    req_time for req_time in self.requests_count[client_id]["requests"]
                    if current_time - req_time < self.time_window
                ]
            else:
                self.requests_count[client_id] = {"requests": []}
            
            # Verificar limite
            request_count = len(self.requests_count[client_id]["requests"])
            
            if request_count >= self.max_requests:
                return False, {
                    "message": "Rate limit exceeded",
                    "retry_after": 60,
                    "current_count": request_count,
                    "max_requests": self.max_requests
                }
            
            # Adicionar request atual
            self.requests_count[client_id]["requests"].append(current_time)
            
            return True, {
                "remaining": self.max_requests - request_count - 1,
                "total": self.max_requests,
                "reset_time": current_time + self.time_window
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Em caso de erro, permitir a request
            return True, {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa a request com rate limiting simples"""
        
        # Se desabilitado ou deve pular, continuar normalmente
        if not self.enabled or self._should_skip(request):
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "request_processing_failed"}
                )
        
        try:
            # Verificar rate limit
            client_id = self._get_client_id(request)
            is_allowed, limit_info = self._check_rate_limit(client_id)
            
            if not is_allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": limit_info.get("message", "Too many requests"),
                        "retry_after": limit_info.get("retry_after", 60)
                    },
                    headers={
                        "Retry-After": str(limit_info.get("retry_after", 60))
                    }
                )
            
            # Processar request
            response = await call_next(request)
            
            # Adicionar headers informativos
            if limit_info:
                response.headers["X-RateLimit-Remaining"] = str(limit_info.get("remaining", "unknown"))
                response.headers["X-RateLimit-Limit"] = str(self.max_requests)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in simple rate limit middleware: {e}")
            # Garantir que sempre retornamos uma resposta
            try:
                return await call_next(request)
            except Exception as final_error:
                logger.error(f"Final fallback error: {final_error}")
                return JSONResponse(
                    status_code=500,
                    content={"error": "middleware_error"}
                )
