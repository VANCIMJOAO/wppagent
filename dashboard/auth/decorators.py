"""
Decorators para Autenticação
============================

Decorators para proteger callbacks e funções.
"""

from functools import wraps
from typing import Callable, Any
from .models import UserRole
from .middleware import auth_middleware

def login_required(func: Callable) -> Callable:
    """
    Decorator que requer que o usuário esteja logado.
    
    Usage:
        @login_required
        def my_callback(...):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # A lógica de verificação será implementada no middleware
        return auth_middleware.require_auth()(func)(*args, **kwargs)
    
    return wrapper

def role_required(required_role: UserRole):
    """
    Decorator que requer uma role específica.
    
    Usage:
        @role_required(UserRole.ADMIN)
        def admin_callback(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return auth_middleware.require_role(required_role)(func)(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(func: Callable) -> Callable:
    """Shortcut para @role_required(UserRole.ADMIN)"""
    return role_required(UserRole.ADMIN)(func)

def manager_required(func: Callable) -> Callable:
    """Shortcut para @role_required(UserRole.MANAGER)"""
    return role_required(UserRole.MANAGER)(func)

def operator_required(func: Callable) -> Callable:
    """Shortcut para @role_required(UserRole.OPERATOR)"""
    return role_required(UserRole.OPERATOR)(func)
