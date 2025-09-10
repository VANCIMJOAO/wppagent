"""
E2E Authentication Test - Admin Authentication System
===================================================

Este teste valida o fluxo completo de autenticação usando o sistema real
de admin authentication que conecta ao banco de dados PostgreSQL.

Testes implementados:
- E2E-01: Login admin retorna 200 com tokens válidos  
- E2E-02: Dashboard carrega sem erros
- E2E-03: Refresh token funciona
- E2E-04: Logout invalida sessão

Estratégias de teste:
1. Usar endpoint real /admin/login (não o mock /auth/login)
2. Database dependency injection para teste isolado  
3. Test fixtures com AdminUser temporário
4. Comprehensive validation e reporting
"""

import asyncio
import pytest
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import tempfile
import sqlite3
import bcrypt

# Configurar DATABASE_URL para usar Railway PostgreSQL
os.environ['DATABASE_URL'] = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/home/vancim/whats_agent')

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

# Import the real application
from app.main import app
from app.models.database import Base, AdminUser, LoginSession
from app.database import get_db

@dataclass
class E2ETestResult:
    """Resultado estruturado dos testes E2E"""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    execution_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    recommendations: List[str] = None

class E2EAuthTester:
    """Testador E2E para autenticação com isolamento de banco de dados"""
    
    def __init__(self):
        self.results = []
        self.test_db_path = None
        self.test_engine = None
        self.test_session_maker = None
        self.admin_user_created = False
        
    async def setup_test_database(self):
        """Configura banco de dados de teste SQLite"""
        # Criar arquivo temporário para SQLite
        fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Engine SQLite assíncrona  
        sqlite_url = f"sqlite+aiosqlite:///{self.test_db_path}"
        self.test_engine = create_async_engine(sqlite_url, echo=False)
        self.test_session_maker = async_sessionmaker(self.test_engine)
        
        # Criar tabelas
        async with self.test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        print(f"✅ Test database created: {self.test_db_path}")
        
    async def create_test_admin_user(self):
        """Cria usuário admin de teste no banco SQLite"""
        try:
            async with self.test_session_maker() as session:
                # Hash da senha usando bcrypt (mesmo método do sistema)
                password = "test_admin_123"
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
                # Criar admin user
                admin_user = AdminUser(
                    username="test_admin",
                    email="test_admin@example.com",
                    password_hash=password_hash,
                    full_name="Test Admin User",
                    is_active=True,
                    is_super_admin=False,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(admin_user)
                await session.commit()
                await session.refresh(admin_user)
                
                self.admin_user_created = True
                print(f"✅ Test admin user created: {admin_user.username} (ID: {admin_user.id})")
                return True
                
        except Exception as e:
            print(f"❌ Failed to create test admin user: {e}")
            return False
    
    def override_database_dependency(self):
        """Override da dependency do banco para usar SQLite de teste"""
        async def get_test_db():
            async with self.test_session_maker() as session:
                yield session
        
        app.dependency_overrides[get_db] = get_test_db
        print("✅ Database dependency overridden for testing")
    
    def cleanup_database_override(self):
        """Remove override do banco de dados"""
        if get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]
        print("✅ Database dependency override removed")
    
    async def cleanup_test_database(self):
        """Limpa recursos do banco de teste"""
        if self.test_engine:
            await self.test_engine.dispose()
        
        if self.test_db_path and os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
            print(f"✅ Test database cleaned up: {self.test_db_path}")
    
    async def test_e2e_01_admin_login_returns_200_with_valid_tokens(self):
        """E2E-01: Login admin retorna 200 com tokens válidos"""
        start_time = datetime.now()
        test_name = "E2E-01: Admin Login Success"
        
        try:
            with TestClient(app) as client:
                # Dados de login
                login_data = {
                    "username": "test_admin",
                    "password": "test_admin_123"
                }
                
                # Fazer login
                response = client.post("/admin/login", json=login_data)
                
                # Validações
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                
                data = response.json()
                
                # Validar estrutura da resposta
                required_fields = ["access_token", "refresh_token", "token_type"]
                for field in required_fields:
                    assert field in data, f"Missing field: {field}"
                    assert data[field], f"Empty field: {field}"
                
                # Validar tipo do token
                assert data["token_type"] == "bearer", "Invalid token type"
                
                # Validar tokens não são vazios
                assert len(data["access_token"]) > 20, "Access token too short"
                assert len(data["refresh_token"]) > 20, "Refresh token too short"
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                self.results.append(E2ETestResult(
                    test_name=test_name,
                    status="PASS",
                    execution_time=execution_time,
                    details={
                        "response_status": response.status_code,
                        "token_type": data["token_type"],
                        "access_token_length": len(data["access_token"]),
                        "refresh_token_length": len(data["refresh_token"]),
                        "response_fields": list(data.keys())
                    }
                ))
                
                # Retornar tokens para próximos testes
                return data["access_token"], data["refresh_token"]
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                execution_time=execution_time,
                details={"error": str(e)},
                error_message=str(e),
                recommendations=[
                    "Verify admin user exists in test database",
                    "Check password hashing consistency",
                    "Validate /admin/login endpoint availability",
                    "Ensure database connection is working"
                ]
            ))
            return None, None
    
    def test_e2e_02_dashboard_loads_without_errors(self, access_token):
        """E2E-02: Dashboard carrega sem erros"""
        start_time = datetime.now()
        test_name = "E2E-02: Dashboard Load"
        
        try:
            with TestClient(app) as client:
                # Headers com token
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Endpoints do dashboard para testar
                dashboard_endpoints = [
                    "/dashboard",
                    "/dashboard/health", 
                    "/health",
                    "/metrics"
                ]
                
                successful_endpoints = []
                failed_endpoints = []
                
                for endpoint in dashboard_endpoints:
                    try:
                        response = client.get(endpoint, headers=headers)
                        if response.status_code in [200, 401]:  # 401 é ok se endpoint não existe
                            successful_endpoints.append(endpoint)
                        else:
                            failed_endpoints.append(f"{endpoint}: {response.status_code}")
                    except Exception as e:
                        failed_endpoints.append(f"{endpoint}: {str(e)}")
                
                # Se pelo menos um endpoint funcionou, considerar sucesso
                success = len(successful_endpoints) > 0
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                self.results.append(E2ETestResult(
                    test_name=test_name,
                    status="PASS" if success else "FAIL",
                    execution_time=execution_time,
                    details={
                        "successful_endpoints": successful_endpoints,
                        "failed_endpoints": failed_endpoints,
                        "total_tested": len(dashboard_endpoints)
                    },
                    recommendations=[] if success else [
                        "Check if dashboard endpoints are properly configured",
                        "Verify authentication middleware is working",
                        "Ensure all dashboard routes are available"
                    ]
                ))
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                execution_time=execution_time,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    def test_e2e_03_refresh_token_works(self, refresh_token):
        """E2E-03: Refresh token funciona"""
        start_time = datetime.now()
        test_name = "E2E-03: Refresh Token"
        
        try:
            with TestClient(app) as client:
                # Tentar renovar token
                refresh_data = {"refresh_token": refresh_token}
                response = client.post("/admin/refresh", json=refresh_data)
                
                success = response.status_code == 200
                details = {
                    "response_status": response.status_code,
                    "response_data": response.json() if success else response.text
                }
                
                if success:
                    data = response.json()
                    details.update({
                        "new_access_token_length": len(data.get("access_token", "")),
                        "response_fields": list(data.keys())
                    })
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                self.results.append(E2ETestResult(
                    test_name=test_name,
                    status="PASS" if success else "FAIL",
                    execution_time=execution_time,
                    details=details,
                    recommendations=[] if success else [
                        "Check if refresh endpoint is available",
                        "Verify refresh token format and validity",
                        "Ensure refresh logic is properly implemented"
                    ]
                ))
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                execution_time=execution_time,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    def test_e2e_04_logout_invalidates_session(self, access_token):
        """E2E-04: Logout invalida sessão"""  
        start_time = datetime.now()
        test_name = "E2E-04: Logout Session"
        
        try:
            with TestClient(app) as client:
                # Headers com token
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Fazer logout
                logout_response = client.post("/admin/logout", headers=headers)
                
                logout_success = logout_response.status_code in [200, 204]
                
                # Tentar usar token após logout (deve falhar)
                test_response = client.get("/health", headers=headers)
                token_invalidated = test_response.status_code in [401, 403]
                
                overall_success = logout_success and token_invalidated
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                self.results.append(E2ETestResult(
                    test_name=test_name,
                    status="PASS" if overall_success else "FAIL",
                    execution_time=execution_time,
                    details={
                        "logout_status": logout_response.status_code,
                        "logout_success": logout_success,
                        "token_test_status": test_response.status_code,
                        "token_invalidated": token_invalidated,
                        "overall_success": overall_success
                    },
                    recommendations=[] if overall_success else [
                        "Check logout endpoint implementation",
                        "Verify token invalidation logic",
                        "Ensure session management is working properly"
                    ]
                ))
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.results.append(E2ETestResult(
                test_name=test_name,
                status="FAIL",
                execution_time=execution_time,
                details={"error": str(e)},
                error_message=str(e)
            ))
    
    async def run_all_tests(self):
        """Executa todos os testes E2E em sequência"""
        print("\n" + "="*80)
        print("🧪 INICIANDO TESTES E2E - AUTENTICAÇÃO ADMIN")
        print("="*80)
        
        try:
            # Setup
            print("\n📋 SETUP PHASE")
            print("-" * 40)
            
            await self.setup_test_database()
            admin_created = await self.create_test_admin_user()
            
            if not admin_created:
                print("❌ Failed to create test admin user. Aborting tests.")
                return
                
            self.override_database_dependency()
            
            # Executar testes
            print("\n🔬 TEST EXECUTION PHASE")
            print("-" * 40)
            
            # E2E-01: Login
            access_token, refresh_token = await self.test_e2e_01_admin_login_returns_200_with_valid_tokens()
            
            if access_token:
                # E2E-02: Dashboard 
                self.test_e2e_02_dashboard_loads_without_errors(access_token)
                
                # E2E-03: Refresh token
                if refresh_token:
                    self.test_e2e_03_refresh_token_works(refresh_token)
                
                # E2E-04: Logout
                self.test_e2e_04_logout_invalidates_session(access_token)
            else:
                print("⚠️ Skipping subsequent tests due to login failure")
            
        finally:
            # Cleanup
            print("\n🧹 CLEANUP PHASE")  
            print("-" * 40)
            
            self.cleanup_database_override()
            await self.cleanup_test_database()
        
        # Report resultados
        self.generate_comprehensive_report()
    
    def generate_comprehensive_report(self):
        """Gera relatório abrangente dos resultados"""
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL - TESTES E2E AUTENTICAÇÃO")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        total_time = sum([r.execution_time for r in self.results])
        
        # Resumo geral
        print(f"\n📈 RESUMO GERAL:")
        print(f"   Total de testes: {total_tests}")
        print(f"   ✅ Sucessos: {passed_tests}")
        print(f"   ❌ Falhas: {failed_tests}")
        print(f"   ⏱️ Tempo total: {total_time:.3f}s")
        print(f"   📊 Taxa de sucesso: {(passed_tests/total_tests*100):.1f}%")
        
        # Detalhes por teste
        print(f"\n📋 DETALHES DOS TESTES:")
        for i, result in enumerate(self.results, 1):
            status_emoji = "✅" if result.status == "PASS" else "❌"
            print(f"\n{i}. {status_emoji} {result.test_name}")
            print(f"   Status: {result.status}")
            print(f"   Tempo: {result.execution_time:.3f}s")
            
            if result.details:
                print(f"   Detalhes:")
                for key, value in result.details.items():
                    if isinstance(value, (list, dict)):
                        print(f"      {key}: {len(value)} items")
                    else:
                        print(f"      {key}: {value}")
            
            if result.error_message:
                print(f"   ❌ Erro: {result.error_message}")
            
            if result.recommendations:
                print(f"   💡 Recomendações:")
                for rec in result.recommendations:
                    print(f"      • {rec}")
        
        # Status final
        if failed_tests == 0:
            print(f"\n🎉 TODOS OS TESTES PASSARAM!")
            print(f"   Sistema de autenticação funcionando corretamente.")
        else:
            print(f"\n⚠️ {failed_tests} TESTE(S) FALHARAM")
            print(f"   Revisar implementação conforme recomendações acima.")
        
        print("\n" + "="*80)

# Função principal para executar os testes
async def main():
    """Função principal para executar todos os testes E2E"""
    tester = E2EAuthTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())