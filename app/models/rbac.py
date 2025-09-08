"""
Sistema RBAC (Role-Based Access Control) - Item 2
Controle granular de permissões para escalabilidade de equipe
"""

from enum import Enum
from typing import List, Dict, Set, Optional, Union
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Tabela de associação many-to-many para usuários e roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('rbac_users.id')),
    Column('role_id', Integer, ForeignKey('rbac_roles.id'))
)

# Tabela de associação many-to-many para roles e permissões
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('rbac_roles.id')),
    Column('permission_id', Integer, ForeignKey('rbac_permissions.id'))
)

class PermissionType(str, Enum):
    """Tipos de permissões disponíveis no sistema"""
    
    # Dashboard e Visualização
    DASHBOARD_VIEW = "dashboard:view"
    DASHBOARD_ADMIN = "dashboard:admin"
    
    # Agendamentos
    APPOINTMENTS_VIEW = "appointments:view"
    APPOINTMENTS_CREATE = "appointments:create"
    APPOINTMENTS_UPDATE = "appointments:update"
    APPOINTMENTS_DELETE = "appointments:delete"
    APPOINTMENTS_ADMIN = "appointments:admin"
    
    # Conversas WhatsApp
    CONVERSATIONS_VIEW = "conversations:view"
    CONVERSATIONS_RESPOND = "conversations:respond"
    CONVERSATIONS_DELETE = "conversations:delete"
    CONVERSATIONS_ADMIN = "conversations:admin"
    
    # Clientes
    CLIENTS_VIEW = "clients:view"
    CLIENTS_CREATE = "clients:create"
    CLIENTS_UPDATE = "clients:update"
    CLIENTS_DELETE = "clients:delete"
    CLIENTS_ADMIN = "clients:admin"
    
    # Relatórios
    REPORTS_VIEW = "reports:view"
    REPORTS_EXPORT = "reports:export"
    REPORTS_ADMIN = "reports:admin"
    
    # Sistema e Administração
    SYSTEM_ADMIN = "system:admin"
    USER_MANAGEMENT = "users:manage"
    ROLE_MANAGEMENT = "roles:manage"
    PERMISSIONS_MANAGEMENT = "permissions:manage"
    
    # Monitoramento
    MONITORING_VIEW = "monitoring:view"
    MONITORING_ADMIN = "monitoring:admin"
    
    # Backup e Manutenção
    BACKUP_CREATE = "backup:create"
    BACKUP_RESTORE = "backup:restore"
    BACKUP_ADMIN = "backup:admin"

class RoleType(str, Enum):
    """Roles predefinidos do sistema"""
    
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"

@dataclass
class PermissionDefinition:
    """Definição de uma permissão com metadados"""
    
    permission: PermissionType
    description: str
    category: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    requires_2fa: bool = False

# Definições detalhadas das permissões
PERMISSION_DEFINITIONS = {
    # Dashboard
    PermissionType.DASHBOARD_VIEW: PermissionDefinition(
        PermissionType.DASHBOARD_VIEW,
        "Visualizar dashboard principal",
        "Dashboard",
        "LOW"
    ),
    PermissionType.DASHBOARD_ADMIN: PermissionDefinition(
        PermissionType.DASHBOARD_ADMIN,
        "Administrar configurações do dashboard",
        "Dashboard",
        "MEDIUM"
    ),
    
    # Agendamentos
    PermissionType.APPOINTMENTS_VIEW: PermissionDefinition(
        PermissionType.APPOINTMENTS_VIEW,
        "Visualizar agendamentos",
        "Agendamentos",
        "LOW"
    ),
    PermissionType.APPOINTMENTS_CREATE: PermissionDefinition(
        PermissionType.APPOINTMENTS_CREATE,
        "Criar novos agendamentos",
        "Agendamentos",
        "MEDIUM"
    ),
    PermissionType.APPOINTMENTS_UPDATE: PermissionDefinition(
        PermissionType.APPOINTMENTS_UPDATE,
        "Editar agendamentos existentes",
        "Agendamentos",
        "MEDIUM"
    ),
    PermissionType.APPOINTMENTS_DELETE: PermissionDefinition(
        PermissionType.APPOINTMENTS_DELETE,
        "Excluir agendamentos",
        "Agendamentos",
        "HIGH",
        requires_2fa=True
    ),
    PermissionType.APPOINTMENTS_ADMIN: PermissionDefinition(
        PermissionType.APPOINTMENTS_ADMIN,
        "Administração completa de agendamentos",
        "Agendamentos",
        "HIGH",
        requires_2fa=True
    ),
    
    # Conversas
    PermissionType.CONVERSATIONS_VIEW: PermissionDefinition(
        PermissionType.CONVERSATIONS_VIEW,
        "Visualizar conversas WhatsApp",
        "Conversas",
        "LOW"
    ),
    PermissionType.CONVERSATIONS_RESPOND: PermissionDefinition(
        PermissionType.CONVERSATIONS_RESPOND,
        "Responder conversas WhatsApp",
        "Conversas",
        "MEDIUM"
    ),
    PermissionType.CONVERSATIONS_DELETE: PermissionDefinition(
        PermissionType.CONVERSATIONS_DELETE,
        "Excluir conversas",
        "Conversas",
        "HIGH",
        requires_2fa=True
    ),
    PermissionType.CONVERSATIONS_ADMIN: PermissionDefinition(
        PermissionType.CONVERSATIONS_ADMIN,
        "Administração completa de conversas",
        "Conversas",
        "HIGH"
    ),
    
    # Clientes
    PermissionType.CLIENTS_VIEW: PermissionDefinition(
        PermissionType.CLIENTS_VIEW,
        "Visualizar dados de clientes",
        "Clientes",
        "LOW"
    ),
    PermissionType.CLIENTS_CREATE: PermissionDefinition(
        PermissionType.CLIENTS_CREATE,
        "Criar novos clientes",
        "Clientes",
        "MEDIUM"
    ),
    PermissionType.CLIENTS_UPDATE: PermissionDefinition(
        PermissionType.CLIENTS_UPDATE,
        "Editar dados de clientes",
        "Clientes",
        "MEDIUM"
    ),
    PermissionType.CLIENTS_DELETE: PermissionDefinition(
        PermissionType.CLIENTS_DELETE,
        "Excluir clientes",
        "Clientes",
        "HIGH",
        requires_2fa=True
    ),
    PermissionType.CLIENTS_ADMIN: PermissionDefinition(
        PermissionType.CLIENTS_ADMIN,
        "Administração completa de clientes",
        "Clientes",
        "HIGH"
    ),
    
    # Relatórios
    PermissionType.REPORTS_VIEW: PermissionDefinition(
        PermissionType.REPORTS_VIEW,
        "Visualizar relatórios",
        "Relatórios",
        "LOW"
    ),
    PermissionType.REPORTS_EXPORT: PermissionDefinition(
        PermissionType.REPORTS_EXPORT,
        "Exportar relatórios (CSV/Excel/PDF)",
        "Relatórios",
        "MEDIUM"
    ),
    PermissionType.REPORTS_ADMIN: PermissionDefinition(
        PermissionType.REPORTS_ADMIN,
        "Administração de relatórios",
        "Relatórios",
        "HIGH"
    ),
    
    # Sistema
    PermissionType.SYSTEM_ADMIN: PermissionDefinition(
        PermissionType.SYSTEM_ADMIN,
        "Administração completa do sistema",
        "Sistema",
        "CRITICAL",
        requires_2fa=True
    ),
    PermissionType.USER_MANAGEMENT: PermissionDefinition(
        PermissionType.USER_MANAGEMENT,
        "Gerenciar usuários",
        "Sistema",
        "HIGH",
        requires_2fa=True
    ),
    PermissionType.ROLE_MANAGEMENT: PermissionDefinition(
        PermissionType.ROLE_MANAGEMENT,
        "Gerenciar roles",
        "Sistema",
        "CRITICAL",
        requires_2fa=True
    ),
    PermissionType.PERMISSIONS_MANAGEMENT: PermissionDefinition(
        PermissionType.PERMISSIONS_MANAGEMENT,
        "Gerenciar permissões",
        "Sistema",
        "CRITICAL",
        requires_2fa=True
    ),
    
    # Monitoramento
    PermissionType.MONITORING_VIEW: PermissionDefinition(
        PermissionType.MONITORING_VIEW,
        "Visualizar métricas de monitoramento",
        "Monitoramento",
        "LOW"
    ),
    PermissionType.MONITORING_ADMIN: PermissionDefinition(
        PermissionType.MONITORING_ADMIN,
        "Administrar sistema de monitoramento",
        "Monitoramento",
        "HIGH"
    ),
    
    # Backup
    PermissionType.BACKUP_CREATE: PermissionDefinition(
        PermissionType.BACKUP_CREATE,
        "Criar backups",
        "Backup",
        "MEDIUM"
    ),
    PermissionType.BACKUP_RESTORE: PermissionDefinition(
        PermissionType.BACKUP_RESTORE,
        "Restaurar backups",
        "Backup",
        "CRITICAL",
        requires_2fa=True
    ),
    PermissionType.BACKUP_ADMIN: PermissionDefinition(
        PermissionType.BACKUP_ADMIN,
        "Administração completa de backup",
        "Backup",
        "HIGH",
        requires_2fa=True
    ),
}

# Configuração de roles predefinidos
ROLE_CONFIGURATIONS = {
    RoleType.SUPER_ADMIN: {
        "name": "Super Administrador",
        "description": "Acesso total ao sistema",
        "permissions": list(PermissionType),  # Todas as permissões
        "is_system_role": True,
        "can_be_deleted": False
    },
    
    RoleType.ADMIN: {
        "name": "Administrador",
        "description": "Administrador geral com amplas permissões",
        "permissions": [
            # Dashboard
            PermissionType.DASHBOARD_VIEW,
            PermissionType.DASHBOARD_ADMIN,
            # Agendamentos
            PermissionType.APPOINTMENTS_VIEW,
            PermissionType.APPOINTMENTS_CREATE,
            PermissionType.APPOINTMENTS_UPDATE,
            PermissionType.APPOINTMENTS_DELETE,
            PermissionType.APPOINTMENTS_ADMIN,
            # Conversas
            PermissionType.CONVERSATIONS_VIEW,
            PermissionType.CONVERSATIONS_RESPOND,
            PermissionType.CONVERSATIONS_ADMIN,
            # Clientes
            PermissionType.CLIENTS_VIEW,
            PermissionType.CLIENTS_CREATE,
            PermissionType.CLIENTS_UPDATE,
            PermissionType.CLIENTS_ADMIN,
            # Relatórios
            PermissionType.REPORTS_VIEW,
            PermissionType.REPORTS_EXPORT,
            PermissionType.REPORTS_ADMIN,
            # Monitoramento
            PermissionType.MONITORING_VIEW,
            PermissionType.MONITORING_ADMIN,
            # Backup
            PermissionType.BACKUP_CREATE,
            PermissionType.BACKUP_ADMIN,
            # Gestão de usuários
            PermissionType.USER_MANAGEMENT
        ],
        "is_system_role": True,
        "can_be_deleted": False
    },
    
    RoleType.MANAGER: {
        "name": "Gerente",
        "description": "Gerente de operações com permissões de supervisão",
        "permissions": [
            # Dashboard
            PermissionType.DASHBOARD_VIEW,
            # Agendamentos
            PermissionType.APPOINTMENTS_VIEW,
            PermissionType.APPOINTMENTS_CREATE,
            PermissionType.APPOINTMENTS_UPDATE,
            # Conversas
            PermissionType.CONVERSATIONS_VIEW,
            PermissionType.CONVERSATIONS_RESPOND,
            # Clientes
            PermissionType.CLIENTS_VIEW,
            PermissionType.CLIENTS_CREATE,
            PermissionType.CLIENTS_UPDATE,
            # Relatórios
            PermissionType.REPORTS_VIEW,
            PermissionType.REPORTS_EXPORT,
            # Monitoramento
            PermissionType.MONITORING_VIEW,
            # Backup
            PermissionType.BACKUP_CREATE
        ],
        "is_system_role": True,
        "can_be_deleted": False
    },
    
    RoleType.OPERATOR: {
        "name": "Operador",
        "description": "Operador do dia-a-dia com permissões operacionais",
        "permissions": [
            # Dashboard
            PermissionType.DASHBOARD_VIEW,
            # Agendamentos
            PermissionType.APPOINTMENTS_VIEW,
            PermissionType.APPOINTMENTS_CREATE,
            PermissionType.APPOINTMENTS_UPDATE,
            # Conversas
            PermissionType.CONVERSATIONS_VIEW,
            PermissionType.CONVERSATIONS_RESPOND,
            # Clientes
            PermissionType.CLIENTS_VIEW,
            PermissionType.CLIENTS_CREATE,
            PermissionType.CLIENTS_UPDATE,
            # Relatórios
            PermissionType.REPORTS_VIEW
        ],
        "is_system_role": True,
        "can_be_deleted": False
    },
    
    RoleType.VIEWER: {
        "name": "Visualizador",
        "description": "Acesso somente leitura",
        "permissions": [
            # Dashboard
            PermissionType.DASHBOARD_VIEW,
            # Agendamentos
            PermissionType.APPOINTMENTS_VIEW,
            # Conversas
            PermissionType.CONVERSATIONS_VIEW,
            # Clientes
            PermissionType.CLIENTS_VIEW,
            # Relatórios
            PermissionType.REPORTS_VIEW,
            # Monitoramento
            PermissionType.MONITORING_VIEW
        ],
        "is_system_role": True,
        "can_be_deleted": False
    },
    
    RoleType.GUEST: {
        "name": "Convidado",
        "description": "Acesso muito limitado para demonstrações",
        "permissions": [
            # Dashboard
            PermissionType.DASHBOARD_VIEW,
        ],
        "is_system_role": True,
        "can_be_deleted": False
    }
}

class RBACUser(Base):
    """Modelo de usuário para RBAC"""
    __tablename__ = "rbac_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    requires_2fa = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    roles = relationship("RBACRole", secondary=user_roles, back_populates="users")
    
    def has_permission(self, permission: PermissionType) -> bool:
        """Verificar se o usuário tem uma permissão específica"""
        for role in self.roles:
            if role.has_permission(permission):
                return True
        return False
    
    def has_any_permission(self, permissions: List[PermissionType]) -> bool:
        """Verificar se o usuário tem pelo menos uma das permissões"""
        return any(self.has_permission(perm) for perm in permissions)
    
    def has_all_permissions(self, permissions: List[PermissionType]) -> bool:
        """Verificar se o usuário tem todas as permissões"""
        return all(self.has_permission(perm) for perm in permissions)
    
    def get_all_permissions(self) -> Set[PermissionType]:
        """Obter todas as permissões do usuário"""
        all_permissions = set()
        for role in self.roles:
            all_permissions.update(role.get_permissions())
        return all_permissions
    
    def is_super_admin(self) -> bool:
        """Verificar se é super administrador"""
        return any(role.role_type == RoleType.SUPER_ADMIN for role in self.roles)

class RBACRole(Base):
    """Modelo de role/função"""
    __tablename__ = "rbac_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    role_type = Column(SQLEnum(RoleType), nullable=True)  # Para roles predefinidos
    is_active = Column(Boolean, default=True)
    is_system_role = Column(Boolean, default=False)  # Roles do sistema não podem ser deletados
    can_be_deleted = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    users = relationship("RBACUser", secondary=user_roles, back_populates="roles")
    permissions = relationship("RBACPermission", secondary=role_permissions, back_populates="roles")
    
    def has_permission(self, permission: PermissionType) -> bool:
        """Verificar se o role tem uma permissão específica"""
        return any(perm.permission_type == permission for perm in self.permissions)
    
    def get_permissions(self) -> Set[PermissionType]:
        """Obter todas as permissões do role"""
        return {perm.permission_type for perm in self.permissions}

class RBACPermission(Base):
    """Modelo de permissão"""
    __tablename__ = "rbac_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    permission_type = Column(SQLEnum(PermissionType), unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    requires_2fa = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    roles = relationship("RBACRole", secondary=role_permissions, back_populates="permissions")

# Modelos de resposta para API
@dataclass
class UserResponse:
    """Resposta de usuário para API"""
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    requires_2fa: bool
    last_login: Optional[datetime]
    roles: List[str]
    permissions: List[str]
    created_at: datetime

@dataclass
class RoleResponse:
    """Resposta de role para API"""
    id: int
    name: str
    description: Optional[str]
    role_type: Optional[str]
    is_active: bool
    is_system_role: bool
    can_be_deleted: bool
    permissions_count: int
    users_count: int
    permissions: List[str]
    created_at: datetime

@dataclass
class PermissionResponse:
    """Resposta de permissão para API"""
    id: int
    permission_type: str
    name: str
    description: Optional[str]
    category: str
    risk_level: str
    requires_2fa: bool
    is_active: bool
