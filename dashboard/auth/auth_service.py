"""
Serviço de Autenticação
======================

Classe principal para gerenciar autenticação, sessões e permissões.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import psycopg2
import psycopg2.extras

# Carrega variáveis do .env
from dotenv import load_dotenv
load_dotenv()

from .models import User, UserRole, UserSession, LoginAttempt

class AuthService:
    """Serviço principal de autenticação"""
    
    def __init__(self):
        """Inicializa o serviço de autenticação"""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            # Em desenvolvimento, use uma URL de exemplo ou SQLite
            print("⚠️  DATABASE_URL não encontrada, usando modo desenvolvimento")
            self.database_url = None
        
        self.session_duration = timedelta(hours=8)  # Sessão expira em 8 horas
        self.max_failed_attempts = 5  # Máximo de tentativas de login
        self.lockout_duration = timedelta(minutes=15)  # Bloqueio por 15 minutos
    
    def get_connection(self):
        """Obtém conexão com o banco de dados"""
        if not self.database_url:
            raise Exception("DATABASE_URL não configurada")
        
        try:
            # Configura SSL se necessário (Railway requer SSL)
            if 'railway' in self.database_url or 'postgres://' in self.database_url:
                conn = psycopg2.connect(
                    self.database_url,
                    sslmode='require' if 'railway' in self.database_url else 'prefer'
                )
            else:
                conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            print(f"Erro ao conectar com database: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Gera hash seguro da senha"""
        # Adiciona salt aleatório
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return f"{salt}${password_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica se a senha está correta"""
        try:
            salt, hash_hex = password_hash.split('$')
            password_hash_check = hashlib.pbkdf2_hmac('sha256',
                                                    password.encode('utf-8'),
                                                    salt.encode('utf-8'),
                                                    100000)
            return password_hash_check.hex() == hash_hex
        except Exception:
            return False
    
    def create_session(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """Cria nova sessão para o usuário"""
        session_id = secrets.token_urlsafe(32)
        created_at = datetime.utcnow()
        expires_at = created_at + self.session_duration
        
        if self.database_url:
            try:
                with self.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO user_sessions 
                            (session_id, user_id, created_at, expires_at, ip_address, user_agent, is_active)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (session_id, user_id, created_at, expires_at, ip_address, user_agent, True))
                        conn.commit()
            except Exception as e:
                print(f"Erro ao criar sessão: {e}")
                # Em caso de erro, continua sem persistir a sessão
        
        return session_id
    
    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """Obtém usuário pela sessão ativa"""
        if not self.database_url:
            # Modo desenvolvimento - retorna usuário de exemplo
            return self._get_demo_user()
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT u.* FROM auth_users u
                        JOIN user_sessions s ON u.id = s.user_id
                        WHERE s.session_id = %s 
                        AND s.is_active = true 
                        AND s.expires_at > %s
                        AND u.is_active = true
                    """, (session_id, datetime.utcnow()))
                    
                    row = cursor.fetchone()
                    if row:
                        return User(
                            id=row['id'],
                            email=row['email'],
                            name=row['name'],
                            role=UserRole(row['role']),
                            is_active=row['is_active'],
                            created_at=row['created_at'],
                            updated_at=row['updated_at'],
                            last_login=row['last_login'],
                            company_id=row['company_id'],
                            phone=row['phone'],
                            avatar_url=row['avatar_url']
                        )
        except Exception as e:
            print(f"Erro ao obter usuário por sessão: {e}")
        
        return None
    
    def authenticate(self, email: str, password: str, ip_address: str = None) -> Optional[tuple[User, str]]:
        """
        Autentica usuário e retorna tupla (User, session_id) se bem-sucedido
        """
        # Registra tentativa de login
        self._log_login_attempt(email, ip_address, False)
        
        # Verifica se usuário está bloqueado
        if self._is_user_locked(email):
            raise Exception("Muitas tentativas de login. Tente novamente em 15 minutos.")
        
        if not self.database_url:
            # Modo desenvolvimento - autenticação simples
            if email == "admin@exemplo.com" and password == "admin123":
                user = self._get_demo_user()
                session_id = self.create_session(user.id, ip_address)
                self._log_login_attempt(email, ip_address, True)
                return user, session_id
            else:
                raise Exception("Credenciais inválidas")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # Busca usuário por email
                    cursor.execute("""
                        SELECT * FROM auth_users 
                        WHERE email = %s AND is_active = true
                    """, (email,))
                    
                    row = cursor.fetchone()
                    if not row:
                        raise Exception("Credenciais inválidas")
                    
                    # Verifica senha
                    if not self.verify_password(password, row['password_hash']):
                        raise Exception("Credenciais inválidas")
                    
                    # Cria usuário
                    user = User(
                        id=row['id'],
                        email=row['email'],
                        name=row['name'],
                        role=UserRole(row['role']),
                        is_active=row['is_active'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        last_login=row['last_login'],
                        company_id=row['company_id'],
                        phone=row['phone'],
                        avatar_url=row['avatar_url']
                    )
                    
                    # Atualiza último login
                    cursor.execute("""
                        UPDATE auth_users SET last_login = %s WHERE id = %s
                    """, (datetime.utcnow(), user.id))
                    conn.commit()
                    
                    # Cria sessão
                    session_id = self.create_session(user.id, ip_address)
                    
                    # Registra tentativa bem-sucedida
                    self._log_login_attempt(email, ip_address, True)
                    
                    return user, session_id
        
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            raise
    
    def logout(self, session_id: str) -> bool:
        """Encerra sessão do usuário"""
        if not self.database_url:
            return True
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE user_sessions 
                        SET is_active = false 
                        WHERE session_id = %s
                    """, (session_id,))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao fazer logout: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Remove sessões expiradas do banco"""
        if not self.database_url:
            return
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE user_sessions 
                        SET is_active = false 
                        WHERE expires_at < %s OR is_active = false
                    """, (datetime.utcnow(),))
                    conn.commit()
        except Exception as e:
            print(f"Erro ao limpar sessões: {e}")
    
    def create_user(self, email: str, password: str, name: str, role: UserRole, 
                   company_id: int = None, phone: str = None) -> User:
        """Cria novo usuário"""
        if not self.database_url:
            raise Exception("Criação de usuários não disponível em modo desenvolvimento")
        
        password_hash = self.hash_password(password)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        INSERT INTO auth_users 
                        (email, password_hash, name, role, company_id, phone, is_active, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING *
                    """, (email, password_hash, name, role.value, company_id, phone, True, datetime.utcnow()))
                    
                    row = cursor.fetchone()
                    conn.commit()
                    
                    return User(
                        id=row['id'],
                        email=row['email'],
                        name=row['name'],
                        role=UserRole(row['role']),
                        is_active=row['is_active'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        last_login=row['last_login'],
                        company_id=row['company_id'],
                        phone=row['phone'],
                        avatar_url=row['avatar_url']
                    )
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
            raise
    
    def _log_login_attempt(self, email: str, ip_address: str, success: bool, error_message: str = None):
        """Registra tentativa de login"""
        if not self.database_url:
            return
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO login_attempts 
                        (email, ip_address, success, attempted_at, error_message)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (email, ip_address, success, datetime.utcnow(), error_message))
                    conn.commit()
        except Exception as e:
            print(f"Erro ao registrar tentativa de login: {e}")
    
    def _is_user_locked(self, email: str) -> bool:
        """Verifica se usuário está bloqueado por muitas tentativas"""
        if not self.database_url:
            return False
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Conta tentativas falhas nos últimos 15 minutos
                    cursor.execute("""
                        SELECT COUNT(*) as attempts FROM login_attempts
                        WHERE email = %s 
                        AND success = false 
                        AND attempted_at > %s
                    """, (email, datetime.utcnow() - self.lockout_duration))
                    
                    result = cursor.fetchone()
                    return result[0] >= self.max_failed_attempts
        except Exception as e:
            print(f"Erro ao verificar bloqueio: {e}")
            return False
    
    def _get_demo_user(self) -> User:
        """Retorna usuário de demonstração para desenvolvimento"""
        return User(
            id=1,
            email="admin@exemplo.com",
            name="Admin Demonstração",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow(),
            company_id=1
        )
    
    def init_database(self):
        """Inicializa tabelas de autenticação no banco"""
        if not self.database_url:
            print("⚠️  Modo desenvolvimento: tabelas não serão criadas")
            return
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Tabela de usuários de autenticação (separada dos usuários WhatsApp)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS auth_users (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            role VARCHAR(50) NOT NULL DEFAULT 'viewer',
                            company_id INTEGER,
                            phone VARCHAR(50),
                            avatar_url TEXT,
                            is_active BOOLEAN DEFAULT true,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP
                        )
                    """)
                    
                    # Tabela de sessões
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_sessions (
                            id SERIAL PRIMARY KEY,
                            session_id VARCHAR(255) UNIQUE NOT NULL,
                            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL,
                            ip_address INET,
                            user_agent TEXT,
                            is_active BOOLEAN DEFAULT true
                        )
                    """)
                    
                    # Tabela de tentativas de login
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS login_attempts (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(255) NOT NULL,
                            ip_address INET,
                            success BOOLEAN NOT NULL,
                            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            error_message TEXT
                        )
                    """)
                    
                    # Índices para performance
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_attempts_attempted_at ON login_attempts(attempted_at)")
                    
                    conn.commit()
                    print("✅ Tabelas de autenticação criadas com sucesso")
        
        except Exception as e:
            print(f"❌ Erro ao criar tabelas de autenticação: {e}")
            raise
    
    def create_default_admin(self, email: str = "admin@exemplo.com", password: str = "admin123", name: str = "Administrador"):
        """Cria usuário administrador padrão"""
        if not self.database_url:
            print("⚠️  Modo desenvolvimento: usuário padrão não será criado no banco")
            return
        
        try:
            # Verifica se já existe
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM auth_users WHERE email = %s", (email,))
                    if cursor.fetchone():
                        print(f"✅ Usuário {email} já existe")
                        return
            
            # Cria usuário admin
            admin = self.create_user(
                email=email,
                password=password,
                name=name,
                role=UserRole.ADMIN,
                company_id=1
            )
            print(f"✅ Usuário administrador criado: {admin.email}")
        
        except Exception as e:
            print(f"❌ Erro ao criar usuário administrador: {e}")
