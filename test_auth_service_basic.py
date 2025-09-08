"""
🧪 Teste Simples do Sistema de Refresh Tokens
=============================================

Teste básico para validar se o sistema está funcionando.
"""

import asyncio
from unittest.mock import AsyncMock
from app.services.auth_service import AuthService
from app.models.database import AdminUser

async def test_basic_auth_service():
    """Teste básico do AuthService"""
    
    # Mock da session
    mock_session = AsyncMock()
    
    # Mock do usuário
    mock_user = AdminUser(
        id=1,
        username="test_admin",
        email="test@admin.com",
        is_active=True
    )
    
    # Criar AuthService
    auth_service = AuthService(mock_session)
    
    # Mock das queries do banco - simplificado
    mock_session.query = lambda x: mock_session
    mock_session.filter = lambda x: mock_session
    mock_session.order_by = lambda x: mock_session
    mock_session.offset = lambda x: mock_session
    mock_session.all = lambda: []  # Retorna lista vazia (sem tokens antigos)
    mock_session.add = lambda x: None
    mock_session.commit = lambda: None
    
    # Testar criação de token pair
    try:
        token_pair = await auth_service.create_token_pair(mock_user)
        
        print("✅ Token pair criado com sucesso:")
        print(f"   - Access Token: {token_pair['access_token'][:50]}...")
        print(f"   - Refresh Token: {token_pair['refresh_token'][:50]}...")
        print(f"   - Token Type: {token_pair['token_type']}")
        print(f"   - Expires In: {token_pair['expires_in']} segundos")
        
        # Verificar se tem estrutura correta
        assert 'access_token' in token_pair
        assert 'refresh_token' in token_pair
        assert 'token_type' in token_pair
        assert 'expires_in' in token_pair
        assert token_pair['expires_in'] == 900  # 15 minutos
        
        print("✅ Teste básico passou!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_basic_auth_service())
