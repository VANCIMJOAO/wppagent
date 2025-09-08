"""
Testes para o sistema de Rate Limiting por Usuário
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.user_rate_limit import UserRateLimitMiddleware, get_user_rate_limiter
from app.models.database import AdminUser  # Pydantic model do admin

# Configurar app de teste
app = FastAPI()
app.add_middleware(UserRateLimitMiddleware)

@app.get("/test")
async def test_endpoint():
    return {"message": "test"}

@app.post("/admin/test")
async def admin_test_endpoint():
    return {"message": "admin test"}

client = TestClient(app)

class TestUserRateLimitMiddleware:
    """Testes para o middleware de rate limiting"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock para Redis"""
        redis_mock = AsyncMock()
        redis_mock.ping = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock()
        redis_mock.incr = AsyncMock(return_value=1)
        redis_mock.expire = AsyncMock()
        return redis_mock
    
    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Fixture para rate limiter com Redis mockado"""
        limiter = get_user_rate_limiter()
        limiter.redis = mock_redis
        return limiter
    
    @pytest.mark.asyncio
    async def test_rate_limit_config_loading(self, rate_limiter):
        """Testar carregamento da configuração de rate limiting"""
        # Verificar configurações padrão
        assert "default" in rate_limiter.limits
        assert "GET /health" in rate_limiter.limits
        assert "POST /webhook" in rate_limiter.limits
        
        # Verificar multiplicadores de usuário
        assert rate_limiter.user_type_multipliers["admin"] == 2.0
        assert rate_limiter.user_type_multipliers["premium"] == 1.5
        assert rate_limiter.user_type_multipliers["regular"] == 1.0
        assert rate_limiter.user_type_multipliers["guest"] == 0.5
    
    @pytest.mark.asyncio
    async def test_get_limit_config(self, rate_limiter):
        """Testar obtenção de configuração de limite para endpoint"""
        # Endpoint específico
        config = rate_limiter._get_limit_config("GET /health", "regular")
        expected = rate_limiter.limits["GET /health"]
        assert config["requests"] == expected["requests"]
        assert config["window"] == expected["window"]
        
        # Endpoint não configurado (usar padrão)
        config = rate_limiter._get_limit_config("GET /unknown", "regular")
        expected = rate_limiter.limits["default"]
        assert config["requests"] == expected["requests"]
        assert config["window"] == expected["window"]
    
    @pytest.mark.asyncio
    async def test_user_type_multipliers(self, rate_limiter):
        """Testar multiplicadores por tipo de usuário"""
        # Admin (2x limite)
        config = rate_limiter._get_limit_config("default", "admin")
        base_limit = rate_limiter.limits["default"]["requests"]
        assert config["requests"] == int(base_limit * 2.0)
        
        # Premium (1.5x limite)
        config = rate_limiter._get_limit_config("default", "premium")
        assert config["requests"] == int(base_limit * 1.5)
        
        # Guest (0.5x limite)
        config = rate_limiter._get_limit_config("default", "guest")
        assert config["requests"] == int(base_limit * 0.5)
    
    @pytest.mark.asyncio
    async def test_redis_keys(self, rate_limiter):
        """Testar geração de chaves Redis"""
        # Chave principal
        key = rate_limiter._get_redis_key("user123", "GET /test", "main")
        assert key == "rate_limit:user123:GET /test:main"
        
        # Chave de burst
        key = rate_limiter._get_redis_key("user123", "GET /test", "burst")
        assert key == "rate_limit:user123:GET /test:burst"
        
        # Chave de IP
        key = rate_limiter._get_redis_key("192.168.1.1", "GET /test", "main", is_ip=True)
        assert key == "rate_limit:ip:192.168.1.1:GET /test:main"
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(self, rate_limiter, mock_redis):
        """Testar rate limiting quando não excedeu limite"""
        # Configurar Redis mock para retornar 0 requests atuais
        mock_redis.get.return_value = "0"
        
        config = {"requests": 10, "window": 60}
        result = await rate_limiter._check_rate_limit("user123", "GET /test", config)
        
        assert not result["exceeded"]
        assert result["current"] == 0
        assert result["limit"] == 10
        assert result["remaining"] == 10
        assert "reset_at" in result
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limiter, mock_redis):
        """Testar rate limiting quando excedeu limite"""
        # Configurar Redis mock para retornar requests acima do limite
        mock_redis.get.return_value = "11"
        
        config = {"requests": 10, "window": 60}
        result = await rate_limiter._check_rate_limit("user123", "GET /test", config)
        
        assert result["exceeded"]
        assert result["current"] == 11
        assert result["limit"] == 10
        assert result["remaining"] == 0
    
    @pytest.mark.asyncio
    async def test_increment_counter(self, rate_limiter, mock_redis):
        """Testar incremento do contador"""
        config = {"requests": 10, "window": 60}
        
        # Primeira chamada
        mock_redis.incr.return_value = 1
        await rate_limiter._increment_counter("user123", "GET /test", config)
        
        # Verificar chamadas Redis
        mock_redis.incr.assert_called()
        mock_redis.expire.assert_called()
    
    @pytest.mark.asyncio
    async def test_burst_protection(self, rate_limiter, mock_redis):
        """Testar proteção contra burst"""
        # Configurar burst limit
        config = {"requests": 10, "window": 60, "burst": 5}
        
        # Simular burst excedido
        mock_redis.get.side_effect = ["3", "6"]  # main, burst
        
        result = await rate_limiter._check_rate_limit("user123", "GET /test", config)
        
        # Deve exceder por burst
        assert result["exceeded"]
        assert result["violation_type"] == "burst_limit"
    
    @pytest.mark.asyncio
    async def test_redis_failure_graceful_degradation(self, rate_limiter, mock_redis):
        """Testar degradação graciosa quando Redis falha"""
        # Configurar Redis para falhar
        mock_redis.get.side_effect = Exception("Redis connection failed")
        
        config = {"requests": 10, "window": 60}
        result = await rate_limiter._check_rate_limit("user123", "GET /test", config)
        
        # Deve permitir quando Redis falha
        assert not result["exceeded"]
        assert result["current"] == 0
    
    @pytest.mark.asyncio
    async def test_get_user_rate_limit_status(self, rate_limiter, mock_redis):
        """Testar obtenção do status de rate limit para usuário"""
        # Configurar Redis mock
        mock_redis.get.side_effect = ["3", "1"]  # main, burst
        
        status = await rate_limiter.get_user_rate_limit_status("user123", "GET /test")
        
        assert len(status) >= 1
        assert "endpoint" in status[0]
        assert "current" in status[0]
        assert "limit" in status[0]
    
    @pytest.mark.asyncio
    async def test_reset_user_rate_limit(self, rate_limiter, mock_redis):
        """Testar reset de rate limit para usuário"""
        # Reset para endpoint específico
        await rate_limiter.reset_user_rate_limit("user123", "GET /test")
        
        # Verificar chamadas de delete no Redis
        assert mock_redis.delete.call_count >= 1
        
        # Reset para todos endpoints
        mock_redis.reset_mock()
        await rate_limiter.reset_user_rate_limit("user123")
        
        # Deve fazer scan para encontrar todas as chaves
        mock_redis.scan_iter.assert_called()

class TestRateLimitEndpoints:
    """Testes para endpoints de gerenciamento de rate limiting"""
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock para usuário admin"""
        return AdminUser(
            id=1,
            username="admin",
            email="admin@test.com",
            password_hash="$2b$12$test_hash",
            is_active=True
        )
    
    @pytest.fixture
    def auth_headers(self):
        """Headers de autenticação para testes"""
        return {"Authorization": "Bearer mock_admin_token"}
    
    def test_rate_limit_status_endpoint(self, auth_headers):
        """Testar endpoint de status de rate limiting"""
        with patch('app.routes.rate_limit.get_current_admin_user') as mock_auth:
            mock_auth.return_value = AdminUser(id=1, username="admin", email="admin@test.com")
            
            response = client.get("/admin/rate-limit/status", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "system_status" in data
            assert "timestamp" in data
    
    def test_rate_limit_config_endpoint(self, auth_headers):
        """Testar endpoint de configuração"""
        with patch('app.routes.rate_limit.get_current_admin_user') as mock_auth:
            mock_auth.return_value = AdminUser(id=1, username="admin", email="admin@test.com")
            
            response = client.get("/admin/rate-limit/config", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "endpoint_limits" in data
            assert "user_type_multipliers" in data
    
    def test_rate_limit_reset_endpoint(self, auth_headers):
        """Testar endpoint de reset de rate limiting"""
        with patch('app.routes.rate_limit.get_current_admin_user') as mock_auth:
            mock_auth.return_value = AdminUser(id=1, username="admin", email="admin@test.com")
            
            response = client.post(
                "/admin/rate-limit/reset?user_id=user123", 
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["user_id"] == "user123"
    
    def test_rate_limit_health_endpoint(self, auth_headers):
        """Testar endpoint de health do rate limiting"""
        with patch('app.routes.rate_limit.get_current_admin_user') as mock_auth:
            mock_auth.return_value = AdminUser(id=1, username="admin", email="admin@test.com")
            
            response = client.get("/admin/rate-limit/health", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "overall_status" in data
            assert "health_details" in data
    
    def test_unauthorized_access(self):
        """Testar acesso não autorizado aos endpoints"""
        response = client.get("/admin/rate-limit/status")
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

class TestRateLimitIntegration:
    """Testes de integração do sistema de rate limiting"""
    
    @pytest.mark.asyncio
    async def test_middleware_integration(self):
        """Testar integração do middleware com FastAPI"""
        # Criar app de teste com middleware
        test_app = FastAPI()
        test_app.add_middleware(UserRateLimitMiddleware)
        
        @test_app.get("/test")
        async def test_route():
            return {"message": "success"}
        
        # Testar que o middleware foi adicionado
        assert len(test_app.user_middleware) > 0
        middleware_found = any(
            "UserRateLimitMiddleware" in str(mw.__class__)
            for mw in test_app.user_middleware
        )
        assert middleware_found
    
    @pytest.mark.asyncio
    async def test_multiple_requests_simulation(self, mock_redis):
        """Simular múltiplas requisições para testar rate limiting"""
        rate_limiter = get_user_rate_limiter()
        rate_limiter.redis = mock_redis
        
        # Configurar limite baixo para teste
        config = {"requests": 3, "window": 60}
        
        # Simular múltiplas requisições
        request_results = []
        
        for i in range(5):
            # Simular contador incrementando
            mock_redis.get.return_value = str(i)
            
            result = await rate_limiter._check_rate_limit("test_user", "GET /test", config)
            request_results.append(result["exceeded"])
            
            if not result["exceeded"]:
                await rate_limiter._increment_counter("test_user", "GET /test", config)
        
        # Primeiras 3 requisições devem passar, 4ª e 5ª devem ser bloqueadas
        assert not request_results[0]  # 1ª requisição: OK
        assert not request_results[1]  # 2ª requisição: OK  
        assert not request_results[2]  # 3ª requisição: OK
        assert request_results[3]      # 4ª requisição: BLOQUEADA
        assert request_results[4]      # 5ª requisição: BLOQUEADA

@pytest.mark.asyncio
async def test_performance_large_user_base():
    """Testar performance com grande base de usuários"""
    rate_limiter = get_user_rate_limiter()
    
    # Mock Redis para responder rapidamente
    mock_redis = AsyncMock()
    mock_redis.get.return_value = "1"
    rate_limiter.redis = mock_redis
    
    config = {"requests": 100, "window": 60}
    
    # Testar 1000 usuários diferentes
    import time
    start_time = time.time()
    
    tasks = []
    for i in range(1000):
        user_id = f"user_{i}"
        task = rate_limiter._check_rate_limit(user_id, "GET /test", config)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Deve processar 1000 usuários em menos de 1 segundo
    assert execution_time < 1.0
    assert len(results) == 1000
    assert all(not result["exceeded"] for result in results)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
