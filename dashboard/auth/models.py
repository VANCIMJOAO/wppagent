"""
Modelos de Dados para Autenticação
==================================

Define as estruturas de dados para usuários, permissões e sessões.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

class UserRole(Enum):
    """Níveis de permissão do sistema"""
    SUPER_ADMIN = "super_admin"      # Acesso total ao sistema
    ADMIN = "admin"                  # Administrador da empresa
    MANAGER = "manager"              # Gerente - acesso a relatórios e configurações
    OPERATOR = "operator"            # Operador - acesso a conversas e clientes
    VIEWER = "viewer"                # Apenas visualização

@dataclass
class User:
    """Modelo de usuário do sistema"""
    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    company_id: Optional[int] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte usuário para dicionário"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'company_id': self.company_id,
            'phone': self.phone,
            'avatar_url': self.avatar_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Cria usuário a partir de dicionário"""
        return cls(
            id=data['id'],
            email=data['email'],
            name=data['name'],
            role=UserRole(data['role']),
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            company_id=data.get('company_id'),
            phone=data.get('phone'),
            avatar_url=data.get('avatar_url')
        )
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Verifica se usuário tem permissão necessária"""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.OPERATOR: 2,
            UserRole.MANAGER: 3,
            UserRole.ADMIN: 4,
            UserRole.SUPER_ADMIN: 5
        }
        
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
    
    def can_access_page(self, page: str) -> bool:
        """Verifica se usuário pode acessar uma página específica"""
        page_permissions = {
            'home': UserRole.VIEWER,
            'conversas': UserRole.OPERATOR,
            'clientes': UserRole.OPERATOR,
            'agendamentos': UserRole.OPERATOR,
            'relatorios': UserRole.MANAGER,
            'configuracoes': UserRole.ADMIN,
            'perfil': UserRole.VIEWER,
            'suporte': UserRole.VIEWER,
        }
        
        required_role = page_permissions.get(page, UserRole.ADMIN)
        return self.has_permission(required_role)

@dataclass
class UserSession:
    """Modelo de sessão do usuário"""
    session_id: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    
    def is_expired(self) -> bool:
        """Verifica se a sessão expirou"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte sessão para dicionário"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active
        }

@dataclass
class LoginAttempt:
    """Modelo para tentativas de login"""
    email: str
    ip_address: str
    success: bool
    attempted_at: datetime
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte tentativa para dicionário"""
        return {
            'email': self.email,
            'ip_address': self.ip_address,
            'success': self.success,
            'attempted_at': self.attempted_at.isoformat(),
            'error_message': self.error_message
        }
