"""
Middleware de Autenticação
=========================

Intercepta requests e verifica se o usuário está autenticado.
"""

import os
from functools import wraps
from dash import callback_context, no_update
from typing import Optional
from .auth_service import AuthService
from .models import User, UserRole

class AuthMiddleware:
    """Middleware para interceptar e validar autenticação"""
    
    def __init__(self):
        self.auth_service = AuthService()
        self.public_paths = ['/login', '/logout', '/session-expired']
    
    def get_current_user(self, session_id: str = None) -> Optional[User]:
        """Obtém usuário atual baseado na sessão"""
        if not session_id:
            return None
        
        try:
            return self.auth_service.get_user_by_session(session_id)
        except Exception as e:
            print(f"Erro ao obter usuário atual: {e}")
            return None
    
    def is_authenticated(self, session_id: str = None) -> bool:
        """Verifica se usuário está autenticado"""
        return self.get_current_user(session_id) is not None
    
    def check_page_access(self, user: User, page_path: str) -> bool:
        """Verifica se usuário tem acesso à página"""
        if not user:
            return False
        
        # Remove barra inicial se existir
        page = page_path.lstrip('/')
        
        # Páginas públicas
        if page in ['login', 'logout', 'session-expired']:
            return True
        
        return user.can_access_page(page or 'home')
    
    def require_auth(self, redirect_to_login: bool = True):
        """Decorator para endpoints que requerem autenticação"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Obtém session_id dos cookies (implementar conforme necessário)
                session_id = self._get_session_from_context()
                
                if not self.is_authenticated(session_id):
                    if redirect_to_login:
                        return self._redirect_to_login()
                    return None
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_role(self, required_role: UserRole):
        """Decorator para endpoints que requerem role específica"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                session_id = self._get_session_from_context()
                user = self.get_current_user(session_id)
                
                if not user or not user.has_permission(required_role):
                    return self._access_denied()
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _get_session_from_context(self) -> Optional[str]:
        """Obtém session_id do contexto atual (cookies, etc)"""
        # Esta implementação depende de como você vai armazenar a sessão
        # Por enquanto, vamos usar uma abordagem simples com dcc.Store
        try:
            ctx = callback_context
            # Implementar lógica para obter session_id
            # Por exemplo, de um dcc.Store com id 'session-store'
            return None  # Placeholder
        except:
            return None
    
    def _redirect_to_login(self):
        """Redireciona para página de login"""
        return '/login'
    
    def _access_denied(self):
        """Retorna resposta de acesso negado"""
        return '/access-denied'

# Instância global do middleware
auth_middleware = AuthMiddleware()
