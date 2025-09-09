# Auth module - Sistema de Autenticação e Autorização Completo

from .jwt_manager import SimpleJWTManager as JWTManager, jwt_manager, get_current_user_from_token
from .two_factor import TwoFactorAuth
from .rate_limiter import RateLimiter
from .secrets_manager import SecretsManager
from .middleware import AuthMiddleware

__all__ = [
    "JWTManager",
    "jwt_manager",
    "get_current_user_from_token",
    "TwoFactorAuth", 
    "RateLimiter",
    "SecretsManager",
    "AuthMiddleware"
]
