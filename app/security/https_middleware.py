"""
🔒 Middleware de Segurança HTTPS
===============================

Middleware para forçar HTTPS e implementar cabeçalhos de segurança:
- HSTS (HTTP Strict Transport Security)
- Redirecionamento HTTP → HTTPS
- Headers de segurança modernos
- Proteção contra downgrade attacks
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

class HTTPSMiddleware(BaseHTTPMiddleware):
    """Middleware para forçar HTTPS e implementar HSTS"""
    
    def __init__(
        self,
        app: ASGIApp,
        force_https: bool = True,
        hsts_max_age: int = 31536000,  # 1 ano
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        allow_localhost: bool = True,
        development_mode: bool = False
    ):
        """
        Inicializa middleware HTTPS
        
        Args:
            app: Aplicação ASGI
            force_https: Forçar redirecionamento para HTTPS
            hsts_max_age: Duração HSTS em segundos
            hsts_include_subdomains: Incluir subdomínios no HSTS
            hsts_preload: Habilitar preload do HSTS
            allow_localhost: Permitir HTTP em localhost (desenvolvimento)
            development_mode: Modo de desenvolvimento (menos restritivo)
        """
        super().__init__(app)
        self.force_https = force_https
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.allow_localhost = allow_localhost
        self.development_mode = development_mode
        
        logger.info(f"✅ HTTPS Middleware configurado (força HTTPS: {force_https})")
    
    async def dispatch(self, request: Request, call_next):
        """Processar requisição e aplicar segurança HTTPS"""
        try:
            # Verificar se deve forçar HTTPS
            if self._should_force_https(request):
                return self._redirect_to_https(request)
            
            # Processar requisição
            response = await call_next(request)
            
            # Adicionar headers de segurança
            self._add_security_headers(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro no middleware HTTPS: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno de segurança"
            )
    
    def _should_force_https(self, request: Request) -> bool:
        """Determina se deve forçar HTTPS"""
        if not self.force_https:
            return False
        
        # Permitir health check sem HTTPS para containers Docker
        if request.url.path == "/health":
            return False
        
        # Verificar se já é HTTPS
        if request.url.scheme == "https":
            return False
        
        # Permitir localhost em desenvolvimento
        if self.allow_localhost and self._is_localhost(request):
            return False
        
        # Verificar headers de proxy (X-Forwarded-Proto)
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "").lower()
        if forwarded_proto == "https":
            return False
        
        # Modo desenvolvimento pode ser menos restritivo
        if self.development_mode:
            return False
        
        return True
    
    def _is_localhost(self, request: Request) -> bool:
        """Verifica se é localhost"""
        host = request.url.hostname
        return host in ["localhost", "127.0.0.1", "::1"]
    
    def _redirect_to_https(self, request: Request) -> RedirectResponse:
        """Redireciona para HTTPS"""
        # Construir URL HTTPS
        https_url = request.url.replace(scheme="https")
        
        # Ajustar porta se necessário
        if request.url.port == 80:
            https_url = https_url.replace(port=443)
        
        logger.info(f"🔒 Redirecionando para HTTPS: {https_url}")
        
        return RedirectResponse(
            url=str(https_url),
            status_code=status.HTTP_301_MOVED_PERMANENTLY
        )
    
    def _add_security_headers(self, request: Request, response):
        """Adiciona headers de segurança"""
        try:
            # HSTS - Forçar HTTPS no futuro
            if request.url.scheme == "https" or self._has_https_proxy(request):
                hsts_value = f"max-age={self.hsts_max_age}"
                
                if self.hsts_include_subdomains:
                    hsts_value += "; includeSubDomains"
                
                if self.hsts_preload:
                    hsts_value += "; preload"
                
                response.headers["Strict-Transport-Security"] = hsts_value
            
            # Content Security Policy
            csp = self._build_csp_header()
            response.headers["Content-Security-Policy"] = csp
            
            # X-Frame-Options
            response.headers["X-Frame-Options"] = "DENY"
            
            # X-Content-Type-Options
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # X-XSS-Protection
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer Policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Feature Policy / Permissions Policy
            response.headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
            
            # X-Permitted-Cross-Domain-Policies
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
            
            # Clear-Site-Data (para logout)
            if request.url.path.endswith("/logout"):
                response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar headers de segurança: {e}")
    
    def _has_https_proxy(self, request: Request) -> bool:
        """Verifica se há proxy HTTPS"""
        return request.headers.get("X-Forwarded-Proto", "").lower() == "https"
    
    def _build_csp_header(self) -> str:
        """Constrói header Content Security Policy"""
        if self.development_mode:
            # CSP mais permissivo para desenvolvimento
            return (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # CSP restritivo para produção
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests"
            )

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware adicional para headers de segurança específicos"""
    
    def __init__(self, app: ASGIApp, custom_headers: dict = None):
        """
        Inicializa middleware de headers de segurança
        
        Args:
            app: Aplicação ASGI
            custom_headers: Headers customizados adicionais
        """
        super().__init__(app)
        self.custom_headers = custom_headers or {}
        logger.info("✅ Security Headers Middleware configurado")
    
    async def dispatch(self, request: Request, call_next):
        """Adiciona headers de segurança customizados"""
        response = await call_next(request)
        
        # Headers personalizados
        for header, value in self.custom_headers.items():
            response.headers[header] = value
        
        # Server header
        response.headers["Server"] = "WhatsApp-Agent/1.0"
        
        # X-Content-Duration (para cache)
        response.headers["X-Content-Duration"] = "300"
        
        # X-Robots-Tag (para APIs)
        if request.url.path.startswith("/api/"):
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        
        return response

def create_https_middleware(
    force_https: bool = True,
    development_mode: bool = False,
    custom_headers: dict = None
) -> list:
    """
    Cria lista de middlewares de segurança HTTPS
    
    Args:
        force_https: Forçar HTTPS
        development_mode: Modo de desenvolvimento
        custom_headers: Headers customizados
        
    Returns:
        Lista de middlewares configurados
    """
    middlewares = []
    
    # Middleware HTTPS principal
    https_middleware = HTTPSMiddleware
    middlewares.append({
        "middleware": https_middleware,
        "force_https": force_https,
        "development_mode": development_mode,
        "allow_localhost": development_mode
    })
    
    # Middleware de headers adicionais
    if custom_headers:
        security_middleware = SecurityHeadersMiddleware
        middlewares.append({
            "middleware": security_middleware,
            "custom_headers": custom_headers
        })
    
    return middlewares
