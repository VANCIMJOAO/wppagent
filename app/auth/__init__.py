# Auth module - Sistema de Autenticação e Autorização Completo

from .jwt_manager import SimpleJWTManager as JWTManager
from .jwt_manager import get_current_user_from_token, jwt_manager
from .middleware import AuthMiddleware
from .rate_limiter import RateLimiter
from .secrets_manager import SecretsManager
from .two_factor import TwoFactorAuth

__all__ = [
    "JWTManager",
    "jwt_manager",
    "get_current_user_from_token",
    "TwoFactorAuth",
    "RateLimiter",
    "SecretsManager",
    "AuthMiddleware",
]
