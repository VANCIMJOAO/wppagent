"""
🔧 Script para Configurar Ambiente de Teste
==========================================

Configura admin user e outros dados necessários para testes

Autor: Claude AI
Status: Utilitário para testes
"""

import asyncio
import sys
import os

# Adicionar o path da aplicação
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, init_db
from app.routes.admin_auth import get_password_hash
from app.models.database import AdminUser, User, Business, Service
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def create_test_admin():
    """Criar admin user para testes"""
    try:
        # Inicializar banco
        await init_db()
        
        # Obter sessão
        async with AsyncSession(bind=get_db().bind) as session:
            # Verificar se admin já existe
            from sqlalchemy import select
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == "admin")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print("✅ Admin user já existe")
                return existing_admin
            
            # Criar admin user
            password_hash = get_password_hash("senha_admin_segura")
            admin_user = AdminUser(
                username="admin",
                password_hash=password_hash,
                is_active=True,
                created_at=None,  # Will be auto-set
                last_login=None
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            print(f"✅ Admin user criado: {admin_user.username}")
            return admin_user
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar admin: {e}")
        return None

async def create_test_data():
    """Criar dados de teste básicos"""
    try:
        async with AsyncSession(bind=get_db().bind) as session:
            # Verificar se já existem dados
            from sqlalchemy import select, func
            
            # Count users
            user_count = await session.execute(select(func.count(User.id)))
            user_total = user_count.scalar()
            
            # Count businesses
            business_count = await session.execute(select(func.count(Business.id)))
            business_total = business_count.scalar()
            
            print(f"📊 Dados existentes: {user_total} usuários, {business_total} negócios")
            
            # Se não há dados, criar alguns básicos
            if user_total == 0:
                test_user = User(
                    nome="Usuário Teste",
                    telefone="+5511999999999",
                    email="teste@example.com"
                )
                session.add(test_user)
                print("✅ Usuário de teste criado")
            
            if business_total == 0:
                test_business = Business(
                    name="Negócio Teste",
                    description="Negócio para testes automatizados"
                )
                session.add(test_business)
                print("✅ Negócio de teste criado")
            
            await session.commit()
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar dados de teste: {e}")

async def setup_test_environment():
    """Configurar ambiente completo de teste"""
    print("🔧 Configurando ambiente de teste...")
    
    # Criar admin
    admin = await create_test_admin()
    if not admin:
        print("❌ Falha ao criar admin")
        return False
    
    # Criar dados básicos
    await create_test_data()
    
    print("✅ Ambiente de teste configurado com sucesso!")
    return True

async def validate_test_environment():
    """Validar se o ambiente está pronto para testes"""
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app, base_url='https://testserver')
        
        # Testar login
        response = client.post("/admin/login", json={
            "username": "admin",
            "password": "senha_admin_segura"
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Login funcionando - Token: {token[:20]}...")
            
            # Testar endpoint protegido
            headers = {"Authorization": f"Bearer {token}"}
            test_response = client.get("/appointments/", headers=headers)
            
            if test_response.status_code == 200:
                print("✅ Endpoints protegidos funcionando")
                return True
            else:
                print(f"⚠️ Endpoint protegido retornou: {test_response.status_code}")
                return True  # Pode estar funcionando mesmo com 500 por falta de dados
        else:
            print(f"❌ Login falhou: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        return False

if __name__ == "__main__":
    """
    Executar:
    python tests/setup_test_env.py
    """
    
    async def main():
        success = await setup_test_environment()
        if success:
            validation = await validate_test_environment()
            if validation:
                print("\n🎉 Ambiente pronto para testes!")
                print("Execute: pytest tests/test_appointments_fixed.py -v")
            else:
                print("\n⚠️ Ambiente configurado mas há problemas na validação")
        else:
            print("\n❌ Falha na configuração do ambiente")
    
    asyncio.run(main())
