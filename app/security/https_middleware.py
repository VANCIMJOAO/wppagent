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
            
            # Content Security Policy - Rigoroso e Completo
            csp = self._build_csp_header()
            response.headers["Content-Security-Policy"] = csp
            
            # CSP Report-Only para monitoramento (apenas produção)
            if not self.development_mode:
                csp_report_only = self._build_csp_report_only()
                response.headers["Content-Security-Policy-Report-Only"] = csp_report_only
            
            # X-Frame-Options - Proteção contra clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # X-Content-Type-Options - Previne MIME sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # X-XSS-Protection - Proteção contra XSS
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Referrer Policy - Controle de informações de referrer
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Feature Policy / Permissions Policy - Controle de APIs do navegador
            permissions_policy = (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=(), "
                "accelerometer=(), ambient-light-sensor=(), "
                "autoplay=(), battery=(), display-capture=(), "
                "document-domain=(), encrypted-media=(), "
                "fullscreen=(self), midi=(), notifications=(), "
                "picture-in-picture=(), publickey-credentials-get=(), "
                "sync-xhr=(), wake-lock=(), web-share=()"
            )
            response.headers["Permissions-Policy"] = permissions_policy
            
            # X-Permitted-Cross-Domain-Policies - Controle de políticas cross-domain
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
            
            # Cross-Origin-Embedder-Policy - Isolamento de origem
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
            
            # Cross-Origin-Opener-Policy - Proteção contra Spectre
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
            
            # Cross-Origin-Resource-Policy - Controle de recursos
            response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
            
            # Clear-Site-Data (para logout e endpoints sensíveis)
            if request.url.path.endswith(("/logout", "/api/auth/logout")):
                response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage", "executionContexts"'
                
            # Cache-Control para endpoints de API sensíveis
            if request.url.path.startswith(("/api/auth/", "/api/admin/")):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar headers de segurança: {e}")
    
    def _has_https_proxy(self, request: Request) -> bool:
        """Verifica se há proxy HTTPS"""
        return request.headers.get("X-Forwarded-Proto", "").lower() == "https"
    
    def _build_csp_header(self) -> str:
        """Constrói header Content Security Policy rigoroso"""
        if self.development_mode:
            # CSP para desenvolvimento - mais permissivo mas ainda seguro
            csp_policy = """
                default-src 'self';
                script-src 'self' 'unsafe-inline' 'unsafe-eval' 
                           https://cdnjs.cloudflare.com 
                           https://vercel.live 
                           https://cdn.jsdelivr.net
                           https://unpkg.com;
                style-src 'self' 'unsafe-inline' 
                          https://fonts.googleapis.com 
                          https://cdnjs.cloudflare.com
                          https://cdn.jsdelivr.net;
                font-src 'self' 
                         https://fonts.gstatic.com 
                         https://cdnjs.cloudflare.com
                         data:;
                img-src 'self' 
                        data: 
                        https: 
                        blob:
                        https://images.unsplash.com
                        https://via.placeholder.com;
                connect-src 'self' 
                            ws://localhost:*
                            wss://localhost:*
                            http://localhost:*
                            https://wppagent-production.up.railway.app 
                            wss://wppagent-production.up.railway.app
                            https://api.whatsapp.com
                            https://graph.facebook.com;
                media-src 'self' 
                          data: 
                          blob:;
                object-src 'none';
                frame-src 'none';
                frame-ancestors 'none';
                base-uri 'self';
                form-action 'self';
                manifest-src 'self';
                worker-src 'self' 
                           blob:;
            """
        else:
            # CSP rigoroso para produção
            csp_policy = """
                default-src 'self';
                script-src 'self' 
                           'nonce-{nonce}' 
                           https://cdnjs.cloudflare.com 
                           https://vercel.live
                           'strict-dynamic';
                style-src 'self' 
                          'unsafe-inline' 
                          https://fonts.googleapis.com 
                          https://cdnjs.cloudflare.com;
                font-src 'self' 
                         https://fonts.gstatic.com 
                         https://cdnjs.cloudflare.com
                         data:;
                img-src 'self' 
                        data: 
                        https: 
                        blob:;
                connect-src 'self' 
                            https://wppagent-production.up.railway.app 
                            wss://wppagent-production.up.railway.app
                            https://api.whatsapp.com
                            https://graph.facebook.com;
                media-src 'none';
                object-src 'none';
                frame-src 'none';
                frame-ancestors 'none';
                base-uri 'self';
                form-action 'self';
                upgrade-insecure-requests;
                block-all-mixed-content;
                manifest-src 'self';
                worker-src 'self';
                child-src 'none';
                report-uri /api/security/csp-report;
            """
        
        # Limpar e retornar CSP como string única
        return ' '.join(csp_policy.split())
    
    def _build_csp_report_only(self) -> str:
        """Constrói CSP Report-Only para monitoramento de violações"""
        csp_report_only = """
            default-src 'self';
            script-src 'self' 'unsafe-inline';
            style-src 'self' 'unsafe-inline';
            img-src 'self' data: https:;
            connect-src 'self' https: wss:;
            font-src 'self' https: data:;
            media-src 'self' data: blob:;
            object-src 'none';
            frame-src 'none';
            frame-ancestors 'none';
            base-uri 'self';
            form-action 'self';
            report-uri /api/security/csp-report-only;
        """
        return ' '.join(csp_report_only.split())
    
    def _generate_nonce(self) -> str:
        """Gera nonce único para CSP"""
        import secrets
        return secrets.token_urlsafe(16)

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
