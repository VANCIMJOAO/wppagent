"""
Sistema de Autenticação
=======================

Módulo completo para autenticação e autorização do dashboard.
Inclui login/logout, gestão de sessões e proteção de rotas.
"""

from .auth_service import AuthService
from .models import User, UserRole
from .middleware import AuthMiddleware
from .decorators import login_required, role_required

__all__ = [
    'AuthService',
    'User', 
    'UserRole',
    'AuthMiddleware',
    'login_required',
    'role_required'
]
