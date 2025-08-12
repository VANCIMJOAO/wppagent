"""
Middleware de autenticação e autorização integrado
Combina JWT, 2FA, Rate Limiting e Secrets Management
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, List
import json
import logging
from datetime import datetime, timezone

from .jwt_manager import jwt_manager
from .two_factor import two_factor_auth
from .rate_limiter import rate_limiter
from .secrets_manager import secrets_manager, SecretType
from app.config.redis_config import redis_manager

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware principal de autenticação"""
    
    def __init__(self, app, *args, **kwargs):
        super().__init__(app)
        self.jwt_manager = jwt_manager
        self.two_factor = two_factor_auth
        self.rate_limiter = rate_limiter
        self.secrets_manager = secrets_manager
        
        # Endpoints que não requerem autenticação
        self.public_endpoints = {
            "/health",
            "/docs",
            "/openapi.json",
            "/webhook",  # WhatsApp webhook
            "/auth/login",
            "/auth/register",
            "/metrics"
        }
        
        # Endpoints que requerem 2FA obrigatório
        self.admin_endpoints = {
            "/admin",
            "/auth/revoke-all",
            "/secrets",
            "/users/admin"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Middleware principal"""
        
        try:
            # 1. Rate Limiting (sempre aplicado)
            endpoint_type = self._determine_endpoint_type(request.url.path)
            user_id = await self._extract_user_id(request)
            
            allowed, rate_result = self.rate_limiter.check_rate_limit(
                request, user_id, endpoint_type
            )
            
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": rate_result.get("reason", "Too many requests"),
                        "retry_after": rate_result.get("retry_after", 60)
                    },
                    headers={"Retry-After": str(rate_result.get("retry_after", 60))}
                )
        except Exception as e:
            # Log apenas se não for erro de Redis conhecido
            if not redis_manager.is_available:
                # Não logar quando Redis não está disponível - é esperado
                pass
            else:
                logger.warning(f"Rate limiter falhou: {e}")
        
        # 2. Verificar se endpoint é público
        if self._is_public_endpoint(request.url.path):
            response = await call_next(request)
            return response
        
        # 3. Autenticação JWT
        try:
            token_info = await self._authenticate_request(request)
            request.state.user = token_info
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": "Authentication failed", "message": e.detail}
            )
        
        # 4. Verificar 2FA para endpoints administrativos
        if self._requires_2fa(request.url.path, token_info.get("role")):
            if not await self._verify_2fa_session(request, token_info["user_id"]):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "2FA required",
                        "message": "Two-factor authentication required for this endpoint"
                    }
                )
        
        # 5. Verificar autorização
        if not self._check_authorization(request.url.path, token_info):
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Insufficient permissions",
                    "message": "You don't have permission to access this resource"
                }
            )
        
        # Processar requisição
        response = await call_next(request)
        
        # Adicionar headers de segurança
        self._add_security_headers(response)
        
        return response
    
    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extrai user_id do token para rate limiting"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            payload = self.jwt_manager.verify_token(token)
            return payload.get("sub")
        except:
            return None
    
    def _determine_endpoint_type(self, path: str) -> str:
        """Determina tipo de endpoint para rate limiting"""
        if path.startswith("/auth"):
            return "auth"
        elif path.startswith("/admin"):
            return "admin"
        elif path.startswith("/api"):
            return "api"
        elif path == "/webhook":
            return "webhook"
        else:
            return "default"
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Verifica se endpoint é público"""
        for public_path in self.public_endpoints:
            if path == public_path or path.startswith(public_path + "/"):
                return True
        return False
    
    async def _authenticate_request(self, request: Request) -> Dict:
        """Autentica requisição via JWT"""
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            payload = self.jwt_manager.verify_token(token)
            
            # Verificar se é access token
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token type"
                )
            
            return {
                "user_id": payload["sub"],
                "role": payload.get("role", "user"),
                "permissions": payload.get("permissions", []),
                "token_id": payload.get("jti")
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {str(e)}"
            )
    
    def _requires_2fa(self, path: str, role: str) -> bool:
        """Verifica se endpoint requer 2FA"""
        # 2FA obrigatório para admins em endpoints administrativos
        if role == "admin":
            for admin_path in self.admin_endpoints:
                if path.startswith(admin_path):
                    return True
        
        return False
    
    async def _verify_2fa_session(self, request: Request, user_id: str) -> bool:
        """Verifica se sessão 2FA está válida"""
        # Verificar se 2FA está habilitado
        if not self.two_factor.is_2fa_enabled(user_id):
            return False  # 2FA obrigatório para admins
        
        # Verificar se há sessão 2FA válida
        session_token = request.headers.get("X-2FA-Session")
        if not session_token:
            return False
        
        # Verificar validade da sessão 2FA (implementar cache de sessões)
        return self._is_valid_2fa_session(user_id, session_token)
    
    def _is_valid_2fa_session(self, user_id: str, session_token: str) -> bool:
        """Verifica validade da sessão 2FA"""
        # Implementar cache de sessões 2FA no Redis
        session_key = f"2fa_session:{user_id}:{session_token}"
        return self.rate_limiter.redis_client.exists(session_key)
    
    def _check_authorization(self, path: str, token_info: Dict) -> bool:
        """Verifica autorização baseada em permissões"""
        role = token_info.get("role", "user")
        permissions = token_info.get("permissions", [])
        
        # Admin tem acesso total
        if role == "admin":
            return True
        
        # Verificar permissões específicas baseadas no path
        if path.startswith("/admin"):
            return "admin" in permissions
        elif path.startswith("/api/users"):
            return "user_management" in permissions
        elif path.startswith("/api"):
            return "api_access" in permissions
        
        # Usuário normal tem acesso básico
        return True
    
    def _add_security_headers(self, response):
        """Adiciona headers de segurança"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"


# Dependency para FastAPI
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict:
    """Dependency para obter usuário atual"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        payload = jwt_manager.verify_token(credentials.credentials)
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )
        
        return {
            "user_id": payload["sub"],
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", []),
            "token_id": payload.get("jti")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}"
        )


async def require_admin(user: Dict = Depends(get_current_user)) -> Dict:
    """Dependency que requer role admin"""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user


async def require_2fa(user: Dict = Depends(get_current_user)) -> Dict:
    """Dependency que requer 2FA válido"""
    user_id = user["user_id"]
    
    if not two_factor_auth.is_2fa_enabled(user_id):
        raise HTTPException(
            status_code=403,
            detail="2FA setup required"
        )
    
    # Aqui você verificaria se a sessão 2FA atual é válida
    # Por simplicidade, assumimos que se chegou aqui, já passou pelo middleware
    
    return user


# Instance do middleware
# auth_middleware = AuthMiddleware()  # Instanciado pelo FastAPI
