"""
🔧 MODELOS SQLALCHEMY PARA TABELAS ÓRFÃS
Script para criar modelos para as tabelas órfãs identificadas no schema drift
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base

# =============================================================================
# MODELOS PARA TABELAS ÓRFÃS CRÍTICAS
# =============================================================================

class AuthUser(Base):
    """
    Modelo para tabela auth_users órfã
    Sistema de autenticação alternativo que precisa ser integrado ou removido
    """
    __tablename__ = "auth_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    company_id = Column(Integer)
    phone = Column(String(20))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))


class BusinessHours(Base):
    """
    Modelo para tabela business_hours órfã
    Sistema de horários estruturado (alternativa ao JSON em businesses)
    """
    __tablename__ = "business_hours"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, default=1)
    day_of_week = Column(Integer, nullable=False)  # 0=domingo, 1=segunda, ..., 6=sábado
    is_open = Column(Boolean, nullable=False, default=True)
    open_time = Column(Time)
    close_time = Column(Time)
    break_start_time = Column(Time)
    break_end_time = Column(Time)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamento
    business = relationship("Business")


class BusinessPolicy(Base):
    """
    Modelo para tabela business_policies órfã
    Sistema de políticas de negócio
    """
    __tablename__ = "business_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, default=1)
    policy_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rules = Column(JSON)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamento
    business = relationship("Business")


class LoginAttempt(Base):
    """
    Modelo para tabela login_attempts órfã  
    Sistema de rate limiting e auditoria de login
    """
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45))  # Suporte IPv4 e IPv6
    success = Column(Boolean, nullable=False)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    error_message = Column(Text)


class PaymentMethod(Base):
    """
    Modelo para tabela payment_methods órfã
    Sistema de métodos de pagamento
    """
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, default=1)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    description = Column(Text)
    additional_info = Column(Text)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relacionamento
    business = relationship("Business")


class UserSession(Base):
    """
    Modelo para tabela user_sessions órfã
    Sistema de sessões de usuários (não admin)
    """
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relacionamento
    user = relationship("User")


# =============================================================================
# MODELOS MELHORADOS PARA TABELAS RBAC DE ASSOCIAÇÃO
# =============================================================================

class RolePermission(Base):
    """
    Modelo melhorado para tabela role_permissions
    Relacionamento roles-permissions com metadados
    """
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey("rbac_roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("rbac_permissions.id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("rbac_users.id"))
    
    # Relacionamentos
    role = relationship("RBACRole")
    permission = relationship("RBACPermission")
    assigned_by_user = relationship("RBACUser")


class UserRole(Base):
    """
    Modelo melhorado para tabela user_roles  
    Relacionamento users-roles com metadados e expiração
    """
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("rbac_users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("rbac_roles.id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("rbac_users.id"))
    expires_at = Column(DateTime(timezone=True))
    
    # Relacionamentos
    user = relationship("RBACUser")
    role = relationship("RBACRole")
    assigned_by_user = relationship("RBACUser")


class RBACAuditLog(Base):
    """
    Modelo para tabela rbac_audit_logs órfã
    Sistema de auditoria RBAC
    """
    __tablename__ = "rbac_audit_logs"
    
    id = Column(String(36), primary_key=True)  # UUID como string
    user_id = Column(Integer, ForeignKey("rbac_users.id"))
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relacionamento
    user = relationship("RBACUser")


# =============================================================================
# INSTRUÇÕES DE USO
# =============================================================================

"""
📋 INSTRUÇÕES PARA IMPLEMENTAR OS MODELOS:

1. INTEGRAÇÃO NO PROJETO:
   - Adicionar os modelos necessários em app/models/database.py
   - Ou criar arquivo separado app/models/orphan_tables.py
   - Importar no __init__.py para registro no metadata

2. DECISÕES POR TABELA:

   🔴 CRÍTICAS (Implementar):
   - LoginAttempt: Rate limiting essencial para segurança
   - RBACAuditLog: Auditoria necessária para compliance  
   - UserSession: Gestão de sessões de usuários
   - RolePermission/UserRole: Modelos completos para RBAC

   🟡 REVISAR (Avaliar necessidade):
   - AuthUser: Verificar se conflita com AdminUser
   - BusinessHours: Decidir entre tabela estruturada vs JSON
   - BusinessPolicy: Se usado, implementar modelo
   - PaymentMethod: Se sistema de pagamento for necessário

3. MIGRAÇÃO ALEMBIC:
   - Criar migração para adicionar modelos escolhidos
   - Verificar se tabelas existentes têm dados
   - Planejar migração de dados se necessário

4. ATUALIZAÇÃO DE RELACIONAMENTOS:
   - Atualizar modelos existentes com novos relacionamentos
   - Verificar foreign keys e índices
   - Testar integridade referencial

5. TESTES:
   - Criar testes para novos modelos
   - Validar operações CRUD
   - Testar relacionamentos
"""
