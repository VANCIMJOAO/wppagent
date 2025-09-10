"""
🔧 Script de Setup para E2E Test
================================

Cria o usuário admin inicial necessário para os testes E2E
"""

import asyncio
import sys
import os

# Adicionar path para encontrar os módulos da aplicação
sys.path.append('/home/vancim/whats_agent')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

try:
    from app.models.database import Base, AdminUser
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Certifique-se de que está no diretório correto da aplicação")
    sys.exit(1)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_initial_admin():
    """Criar usuário admin inicial para os testes"""
    
    print("🔧 Configurando usuário admin para teste E2E...")
    
    try:
        # Setup database de teste
        DATABASE_URL = "sqlite:///./test_e2e_auth_dashboard.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Criar tabelas
        Base.metadata.create_all(bind=engine)
        
        # Criar sessão
        db = SessionLocal()
        
        try:
            # Verificar se admin já existe
            existing_admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
            if existing_admin:
                print("⚠️ Admin já existe, removendo...")
                db.delete(existing_admin)
                db.commit()
            
            # Criar novo admin
            hashed_password = pwd_context.hash("Admin#123!")
            admin_user = AdminUser(
                username="admin",
                email="admin@example.com", 
                password_hash=hashed_password,
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print(f"✅ Admin user criado com sucesso!")
            print(f"   Username: admin")
            print(f"   Email: admin@example.com")
            print(f"   Password: Admin#123!")
            print(f"   ID: {admin_user.id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar admin: {e}")
            db.rollback()
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erro de configuração: {e}")
        return False

if __name__ == "__main__":
    success = create_initial_admin()
    sys.exit(0 if success else 1)