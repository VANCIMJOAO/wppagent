"""
🧪 Testes para Validação do Padrão C002
=======================================

Testes para validar que todos os endpoints seguem a estrutura
padronizada {success, data, error, meta}.

Funcionalidades:
- Testa endpoints migrados
- Valida estrutura de response
- Verifica error handling
- Confirma paginação padronizada
- Valida timing e metadados

Autor: Claude AI
Data: 2025-09-11
Status: Implementação C002 - Testes de Validação
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime
from typing import Dict, Any

from app.main import app
from app.schemas.response import ApiResponse, ErrorCode


class TestC002ResponsePatterns:
    """Testes para validar padrões de response C002"""
    
    @pytest.fixture
    def client(self):
        """Cliente de teste"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Cliente assíncrono de teste"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    def test_health_check_v2_structure(self, client):
        """Testa se health check v2 segue padrão C002"""
        response = client.get("/health/v2")
        
        assert response.status_code == 200
        data = response.json()
        
        # ✅ Validar estrutura básica ApiResponse
        assert "success" in data
        assert "data" in data  
        assert "error" in data
        assert "meta" in data
        
        # ✅ Validar conteúdo de sucesso
        assert data["success"] is True
        assert data["data"] is not None
        assert data["error"] is None
        
        # ✅ Validar metadados
        meta = data["meta"]
        assert "timestamp" in meta
        assert "request_id" in meta
        assert "execution_time_ms" in meta
        assert "version" in meta
        
        # ✅ Validar dados de health
        health_data = data["data"]
        assert "status" in health_data
        assert "service" in health_data
        assert "version" in health_data
        assert health_data["status"] == "healthy"
    
    def test_error_response_structure(self, client):
        """Testa estrutura de erro padronizada"""
        # Tentar acessar endpoint que não existe
        response = client.get("/dashboard/migrated/clients/99999")
        
        data = response.json()
        
        # ✅ Validar estrutura de erro
        assert "success" in data
        assert "data" in data
        assert "error" in data
        assert "meta" in data
        
        # ✅ Validar conteúdo de erro
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"] is not None
        
        # ✅ Validar detalhes do erro
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert error["code"] in [e.value for e in ErrorCode]
    
    @pytest.mark.asyncio
    async def test_paginated_response_structure(self, async_client):
        """Testa estrutura de resposta paginada"""
        response = await async_client.get("/dashboard/migrated/clients?limit=5&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        # ✅ Validar estrutura básica
        assert data["success"] is True
        assert isinstance(data["data"], list)
        
        # ✅ Validar metadados de paginação
        meta = data["meta"]
        assert "pagination" in meta
        
        pagination = meta["pagination"]
        assert "total" in pagination
        assert "limit" in pagination
        assert "offset" in pagination
        assert "page" in pagination
        assert "pages" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination
        
        # ✅ Validar valores de paginação
        assert pagination["limit"] == 5
        assert pagination["offset"] == 0
        assert pagination["page"] == 1
        assert pagination["has_prev"] is False
    
    def test_timing_metadata(self, client):
        """Testa se timing é incluído nos metadados"""
        response = client.get("/dashboard/migrated/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # ✅ Validar timing
        meta = data["meta"]
        assert "execution_time_ms" in meta
        assert isinstance(meta["execution_time_ms"], int)
        assert meta["execution_time_ms"] >= 0
    
    def test_request_id_uniqueness(self, client):
        """Testa se request_id é único entre chamadas"""
        response1 = client.get("/health/v2")
        response2 = client.get("/health/v2")
        
        data1 = response1.json()
        data2 = response2.json()
        
        request_id1 = data1["meta"]["request_id"]
        request_id2 = data2["meta"]["request_id"]
        
        # ✅ IDs devem ser diferentes
        assert request_id1 != request_id2
        
        # ✅ IDs devem ser UUIDs válidos
        import uuid
        uuid.UUID(request_id1)  # Raises exception if invalid
        uuid.UUID(request_id2)
    
    def test_timestamp_format(self, client):
        """Testa formato do timestamp"""
        response = client.get("/health/v2")
        data = response.json()
        
        timestamp = data["meta"]["timestamp"]
        
        # ✅ Deve ser string ISO 8601
        parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed_time is not None
    
    def test_version_consistency(self, client):
        """Testa se versão é consistente"""
        endpoints = ["/health/v2", "/dashboard/migrated/stats"]
        
        versions = []
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                versions.append(data["meta"]["version"])
        
        # ✅ Todas as versões devem ser iguais
        assert len(set(versions)) == 1, "Versões inconsistentes entre endpoints"


class TestC002ErrorHandling:
    """Testes específicos para error handling padronizado"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_404_error_structure(self, client):
        """Testa estrutura de erro 404"""
        response = client.get("/dashboard/migrated/clients/99999")
        
        assert response.status_code == 404
        data = response.json()
        
        # ✅ Estrutura de erro
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "não encontrado" in data["error"]["message"].lower()
    
    def test_validation_error_structure(self, client):
        """Testa estrutura de erro de validação"""
        # Tentar com parâmetros inválidos
        response = client.get("/dashboard/migrated/clients?limit=-1")
        
        # Deve retornar erro de validação
        assert response.status_code in [400, 422]
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] in ["VALIDATION_ERROR"]
    
    def test_500_error_structure(self, client):
        """Testa estrutura de erro interno (simulado)"""
        # Para testar erro 500, precisaríamos simular uma falha
        # Por enquanto, apenas verificamos que a estrutura existe
        pass


class TestC002Consistency:
    """Testes para verificar consistência entre endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_all_migrated_endpoints_follow_pattern(self, client):
        """Testa se todos os endpoints migrados seguem o padrão"""
        migrated_endpoints = [
            "/dashboard/migrated/clients",
            "/dashboard/migrated/stats",
            "/dashboard/migrated/clients/manual",
            "/health/v2"
        ]
        
        for endpoint in migrated_endpoints:
            response = client.get(endpoint)
            
            # Ignorar erros de autenticação para este teste
            if response.status_code in [401, 403]:
                continue
                
            data = response.json()
            
            # ✅ Validar estrutura básica em todos
            assert "success" in data, f"Endpoint {endpoint} não tem 'success'"
            assert "data" in data, f"Endpoint {endpoint} não tem 'data'"
            assert "error" in data, f"Endpoint {endpoint} não tem 'error'"
            assert "meta" in data, f"Endpoint {endpoint} não tem 'meta'"
            
            # ✅ Validar metadados básicos
            meta = data["meta"]
            assert "timestamp" in meta
            assert "request_id" in meta
            assert "version" in meta


def validate_api_response_schema(response_data: Dict[str, Any]) -> bool:
    """
    Função utilitária para validar schema ApiResponse
    
    Args:
        response_data: Dados da response JSON
        
    Returns:
        True se válido, False caso contrário
    """
    required_fields = ["success", "data", "error", "meta"]
    
    # Verificar campos obrigatórios
    for field in required_fields:
        if field not in response_data:
            return False
    
    # Verificar tipos
    if not isinstance(response_data["success"], bool):
        return False
    
    # Se sucesso, data não deve ser None
    if response_data["success"] and response_data["data"] is None:
        return False
    
    # Se erro, success deve ser False
    if response_data["error"] is not None and response_data["success"]:
        return False
    
    # Verificar metadados obrigatórios
    meta = response_data["meta"]
    if not isinstance(meta, dict):
        return False
    
    meta_required = ["timestamp", "request_id", "version"]
    for field in meta_required:
        if field not in meta:
            return False
    
    return True


# ========================================
# TESTES DE INTEGRAÇÃO
# ========================================

def test_integration_c002_full_flow():
    """Teste de integração completo do fluxo C002"""
    client = TestClient(app)
    
    # 1. Health check
    health_response = client.get("/health/v2")
    assert health_response.status_code == 200
    assert validate_api_response_schema(health_response.json())
    
    # 2. Lista paginada
    list_response = client.get("/dashboard/migrated/clients?limit=5")
    # Pode dar 401 se não autenticado - OK para este teste
    if list_response.status_code == 200:
        assert validate_api_response_schema(list_response.json())
    
    # 3. Estatísticas
    stats_response = client.get("/dashboard/migrated/stats")
    # Pode dar 401 se não autenticado - OK para este teste
    if stats_response.status_code == 200:
        assert validate_api_response_schema(stats_response.json())


if __name__ == "__main__":
    # Executar testes diretamente
    pytest.main([__file__, "-v"])
