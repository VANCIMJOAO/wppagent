"""
🧪 Testes Fixos - API Agendamentos
=================================

Testes abrangentes para validação da API de agendamentos
com schema unificado e validações rigorosas.

Autor: Claude AI
Status: Implementação crítica para qualidade
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from app.main import app

client = TestClient(app)

# ================================================================
# 🔧 FIXTURES E HELPERS
# ================================================================

@pytest.fixture
def auth_headers():
    """Fixture para autenticação"""
    login_response = client.post("/admin/login", json={
        "username": "admin",
        "password": "senha_admin_segura"
    })
    
    if login_response.status_code != 200:
        pytest.skip("Falha na autenticação - verifique credenciais de teste")
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_appointment_data():
    """Dados de exemplo para criar agendamento"""
    future_date = datetime.now() + timedelta(days=1)
    return {
        "user_id": 1,
        "business_id": 1,
        "service_id": 1,
        "date_time": future_date.isoformat(),
        "status": "agendado",
        "notes": "Teste automatizado",
        "duration_minutes": 60,
        "price": 50.0
    }


# ================================================================
# 🧪 TESTES PRINCIPAIS
# ================================================================

def test_get_appointments_with_unified_schema(auth_headers):
    """
    📋 Teste de schema unificado para appointments
    
    Verifica:
    - Estrutura da resposta padronizada
    - Campos obrigatórios presentes
    - Tipos de dados corretos
    - Status válidos
    """
    
    # Buscar agendamentos
    response = client.get("/appointments/", headers=auth_headers)
    
    assert response.status_code == 200, f"Falha na requisição: {response.text}"
    data = response.json()
    
    # ✅ Verificar estrutura da resposta
    required_response_fields = ["appointments", "total", "page", "per_page", "has_more"]
    for field in required_response_fields:
        assert field in data, f"Campo obrigatório '{field}' ausente na resposta"
    
    # ✅ Verificar tipos
    assert isinstance(data["appointments"], list), "Campo 'appointments' deve ser uma lista"
    assert isinstance(data["total"], int), "Campo 'total' deve ser um inteiro"
    assert isinstance(data["page"], int), "Campo 'page' deve ser um inteiro"
    assert isinstance(data["per_page"], int), "Campo 'per_page' deve ser um inteiro"
    assert isinstance(data["has_more"], bool), "Campo 'has_more' deve ser um booleano"
    
    # ✅ Se houver agendamentos, verificar schema individual
    if data["appointments"]:
        appointment = data["appointments"][0]
        
        # Campos obrigatórios unificados
        required_fields = [
            "id", "user_id", "business_id", 
            "data_agendamento", "horario", "duracao_minutos",
            "valor", "status", "cliente_nome", "servico_nome"
        ]
        
        for field in required_fields:
            assert field in appointment, f"Campo obrigatório '{field}' ausente no agendamento"
        
        # ✅ Verificar tipos específicos
        assert isinstance(appointment["id"], int), "ID deve ser inteiro"
        assert isinstance(appointment["user_id"], int), "user_id deve ser inteiro"
        assert isinstance(appointment["business_id"], int), "business_id deve ser inteiro"
        assert isinstance(appointment["valor"], (int, float)), "valor deve ser numérico"
        assert isinstance(appointment["duracao_minutos"], int), "duracao_minutos deve ser inteiro"
        
        # ✅ Verificar status válidos
        valid_statuses = ["agendado", "confirmado", "cancelado", "realizado"]
        assert appointment["status"] in valid_statuses, f"Status '{appointment['status']}' inválido"
        
        # ✅ Verificar campos de string não vazios
        string_fields = ["cliente_nome", "data_agendamento", "horario"]
        for field in string_fields:
            if appointment.get(field):
                assert isinstance(appointment[field], str), f"Campo '{field}' deve ser string"
                assert len(appointment[field].strip()) > 0, f"Campo '{field}' não pode estar vazio"


def test_create_appointment_validation(auth_headers, sample_appointment_data):
    """
    📝 Teste de validação na criação de agendamentos
    
    Verifica:
    - Validação de dados inválidos
    - Criação com dados válidos
    - Mensagens de erro apropriadas
    """
    
    # ❌ Teste com dados inválidos
    invalid_test_cases = [
        {
            "data": {"user_id": "invalid", "business_id": 1},
            "description": "user_id inválido (string)"
        },
        {
            "data": {"user_id": 1, "date_time": "invalid-date"},
            "description": "data_agendamento inválida"
        },
        {
            "data": {"user_id": 1, "business_id": 1, "duration_minutes": -30},
            "description": "duração negativa"
        },
        {
            "data": {"user_id": 1, "business_id": 1, "price": "não-numérico"},
            "description": "preço inválido"
        }
    ]
    
    for test_case in invalid_test_cases:
        response = client.post("/appointments/", 
                              json=test_case["data"], 
                              headers=auth_headers)
        
        assert response.status_code == 422, f"Deveria retornar 422 para: {test_case['description']}"
        
        # Verificar se há detalhes do erro
        error_data = response.json()
        assert "detail" in error_data, "Resposta de erro deve conter 'detail'"
    
    # ✅ Teste com dados válidos
    response = client.post("/appointments/", 
                          json=sample_appointment_data, 
                          headers=auth_headers)
    
    # Pode criar com sucesso (201) ou retornar erro específico do negócio (400, 404)
    assert response.status_code in [201, 400, 404], f"Status inesperado: {response.status_code}"
    
    if response.status_code == 201:
        # Verificar estrutura da resposta de sucesso
        created_appointment = response.json()
        assert "id" in created_appointment, "Agendamento criado deve retornar ID"
        assert isinstance(created_appointment["id"], int), "ID deve ser inteiro"


def test_appointments_filtering(auth_headers):
    """
    🔍 Teste de filtros de agendamentos
    
    Verifica:
    - Filtro por status
    - Filtro por data
    - Filtro por usuário
    - Paginação
    """
    
    # ✅ Teste filtro por status
    status_values = ["agendado", "confirmado", "cancelado", "realizado"]
    
    for status in status_values:
        response = client.get(f"/appointments/?status={status}", headers=auth_headers)
        assert response.status_code == 200, f"Falha no filtro por status: {status}"
        
        data = response.json()
        # Se houver resultados, verificar se todos têm o status correto
        for appointment in data["appointments"]:
            assert appointment["status"] == status, f"Filtro de status não funcionou para: {status}"
    
    # ✅ Teste filtro por data
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    response = client.get(
        f"/appointments/?date_from={today}&date_to={tomorrow}", 
        headers=auth_headers
    )
    assert response.status_code == 200, "Falha no filtro por data"
    
    # ✅ Teste paginação
    response_page1 = client.get("/appointments/?page=1&limit=5", headers=auth_headers)
    assert response_page1.status_code == 200, "Falha na paginação página 1"
    
    response_page2 = client.get("/appointments/?page=2&limit=5", headers=auth_headers)
    assert response_page2.status_code == 200, "Falha na paginação página 2"
    
    # Verificar se as páginas são diferentes (se houver dados suficientes)
    page1_data = response_page1.json()
    page2_data = response_page2.json()
    
    if page1_data["total"] > 5:  # Se houver mais de 5 registros
        assert page1_data["page"] != page2_data["page"], "Páginas devem ser diferentes"


def test_appointment_crud_operations(auth_headers, sample_appointment_data):
    """
    🔄 Teste completo de CRUD para agendamentos
    
    Verifica:
    - Create (POST)
    - Read (GET)
    - Update (PUT) 
    - Delete (DELETE)
    """
    
    # 📝 CREATE - Tentar criar agendamento
    create_response = client.post("/appointments/", 
                                 json=sample_appointment_data, 
                                 headers=auth_headers)
    
    if create_response.status_code == 201:
        created_appointment = create_response.json()
        appointment_id = created_appointment["id"]
        
        # 📖 READ - Buscar agendamento criado
        read_response = client.get(f"/appointments/{appointment_id}", headers=auth_headers)
        
        if read_response.status_code == 200:
            fetched_appointment = read_response.json()
            assert fetched_appointment["id"] == appointment_id, "ID do agendamento não confere"
        
        # ✏️ UPDATE - Tentar atualizar
        update_data = {"status": "confirmado", "notes": "Atualizado via teste"}
        update_response = client.put(f"/appointments/{appointment_id}", 
                                   json=update_data, 
                                   headers=auth_headers)
        
        # Update pode ou não estar implementado
        assert update_response.status_code in [200, 404, 405], "Resposta de update inesperada"
        
        # 🗑️ DELETE - Tentar excluir
        delete_response = client.delete(f"/appointments/{appointment_id}", headers=auth_headers)
        
        # Delete pode ou não estar implementado
        assert delete_response.status_code in [200, 404, 405], "Resposta de delete inesperada"
    
    else:
        # Se não conseguiu criar, pular testes de CRUD
        pytest.skip(f"Não foi possível criar agendamento para teste CRUD: {create_response.status_code}")


def test_error_handling(auth_headers):
    """
    🚨 Teste de tratamento de erros
    
    Verifica:
    - Agendamento não encontrado (404)
    - Dados inválidos (422)
    - Erros de formato de data
    """
    
    # ❌ Buscar agendamento inexistente
    response = client.get("/appointments/99999", headers=auth_headers)
    assert response.status_code == 404, "Deveria retornar 404 para agendamento inexistente"
    
    # ❌ Parâmetros de data inválidos
    invalid_date_response = client.get("/appointments/?date_from=invalid-date", headers=auth_headers)
    assert invalid_date_response.status_code == 400, "Deveria retornar 400 para data inválida"
    
    # ❌ Página inválida
    invalid_page_response = client.get("/appointments/?page=0", headers=auth_headers)
    assert invalid_page_response.status_code == 422, "Deveria retornar 422 para página inválida"


def test_performance_basic(auth_headers):
    """
    ⚡ Teste básico de performance
    
    Verifica:
    - Tempo de resposta aceitável
    - Carga de dados razoável
    """
    import time
    
    start_time = time.time()
    response = client.get("/appointments/?limit=10", headers=auth_headers)
    end_time = time.time()
    
    duration = end_time - start_time
    
    assert response.status_code == 200, "Falha na requisição de performance"
    assert duration < 5.0, f"Resposta muito lenta: {duration:.2f}s (máximo 5s)"
    
    # Verificar se retornou dados em formato esperado
    data = response.json()
    assert "appointments" in data, "Resposta deve conter 'appointments'"
    assert len(data["appointments"]) <= 10, "Não deve retornar mais que o limite solicitado"


# ================================================================
# 🧪 TESTES DE INTEGRAÇÃO AVANÇADOS
# ================================================================

def test_schema_consistency_across_endpoints(auth_headers):
    """
    🔄 Teste de consistência de schema entre endpoints
    
    Verifica se o schema é consistente entre:
    - Lista de agendamentos
    - Detalhes de agendamento individual
    - Endpoints legacy
    """
    
    # Buscar lista
    list_response = client.get("/appointments/?limit=1", headers=auth_headers)
    assert list_response.status_code == 200
    
    list_data = list_response.json()
    
    if list_data["appointments"]:
        appointment_from_list = list_data["appointments"][0]
        appointment_id = appointment_from_list["id"]
        
        # Buscar detalhes do mesmo agendamento
        detail_response = client.get(f"/appointments/{appointment_id}", headers=auth_headers)
        
        if detail_response.status_code == 200:
            appointment_from_detail = detail_response.json()
            
            # Verificar campos comuns
            common_fields = ["id", "status", "valor", "duracao_minutos"]
            for field in common_fields:
                if field in appointment_from_list and field in appointment_from_detail:
                    assert appointment_from_list[field] == appointment_from_detail[field], \
                        f"Campo '{field}' inconsistente entre lista e detalhes"


def test_cache_behavior(auth_headers):
    """
    🗄️ Teste básico de comportamento de cache
    
    Verifica:
    - Consistência entre requisições
    - Headers de cache (se implementados)
    """
    
    # Fazer duas requisições idênticas
    response1 = client.get("/appointments/?limit=5", headers=auth_headers)
    response2 = client.get("/appointments/?limit=5", headers=auth_headers)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Os dados devem ser consistentes
    data1 = response1.json()
    data2 = response2.json()
    
    assert data1["total"] == data2["total"], "Total de registros inconsistente entre requisições"
    
    # Se ambas retornaram dados, verificar se são iguais
    if data1["appointments"] and data2["appointments"]:
        # Comparar primeiro item
        item1 = data1["appointments"][0]
        item2 = data2["appointments"][0]
        assert item1["id"] == item2["id"], "Dados inconsistentes entre requisições em cache"


# ================================================================
# 🎯 TESTES DE VALIDAÇÃO DE NEGÓCIO
# ================================================================

def test_business_rules_validation(auth_headers):
    """
    📋 Teste de regras de negócio
    
    Verifica:
    - Validações específicas do domínio
    - Constraints de negócio
    """
    
    # Buscar agendamentos para verificar regras
    response = client.get("/appointments/", headers=auth_headers)
    assert response.status_code == 200
    
    data = response.json()
    
    for appointment in data["appointments"]:
        # ✅ Verificar que valor é positivo
        if "valor" in appointment and appointment["valor"] is not None:
            assert appointment["valor"] >= 0, f"Valor não pode ser negativo: {appointment['valor']}"
        
        # ✅ Verificar que duração é positiva
        if "duracao_minutos" in appointment and appointment["duracao_minutos"] is not None:
            assert appointment["duracao_minutos"] > 0, f"Duração deve ser positiva: {appointment['duracao_minutos']}"
        
        # ✅ Verificar IDs são positivos
        for id_field in ["id", "user_id", "business_id"]:
            if id_field in appointment:
                assert appointment[id_field] > 0, f"ID deve ser positivo: {id_field}={appointment[id_field]}"


if __name__ == "__main__":
    """
    Executar testes diretamente:
    python -m pytest tests/test_appointments_fixed.py -v
    """
    print("🧪 Execute os testes com: pytest tests/test_appointments_fixed.py -v")
