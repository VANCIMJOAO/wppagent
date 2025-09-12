"""
🔄 CF001 - Teste de Padronização naming BE↔FE
============================================

Valida que:
1. API aceita requests em snake_case E camelCase
2. API sempre retorna responses em camelCase
3. Aliases Pydantic funcionam corretamente
4. 15 campos críticos mapeados conforme tabela
"""

import pytest
import asyncio
from datetime import datetime
from app.schemas.unified import (
    UnifiedAppointmentResponse,
    UnifiedAppointmentRequest,
    UnifiedConversationResponse,
    UnifiedMessageResponse,
    convert_snake_to_camel,
    convert_camel_to_snake,
    CF001_FIELD_MAPPING
)

def test_cf001_appointment_response_aliases():
    """Testa serialization_alias nos responses CF001"""
    
    # Dados em snake_case (backend)
    appointment_data = {
        "id": 1,
        "user_id": 123,
        "business_id": 456,
        "service_id": 789,
        "date_time": datetime(2025, 9, 12, 14, 0),
        "duration_minutes": 60,
        "created_at": datetime(2025, 9, 12, 10, 0),
        "updated_at": datetime(2025, 9, 12, 11, 0),
        "status": "agendado",
        "notes": "Teste CF001",
        "client_name": "João Silva",
        "client_phone": "+55 11 99999-8888"
    }
    
    # Criar response schema
    response = UnifiedAppointmentResponse(**appointment_data)
    
    # Serializar para dict (simulando JSON response)
    response_dict = response.model_dump(by_alias=True)
    
    # Validar que campos críticos estão em camelCase
    assert "userId" in response_dict
    assert "businessId" in response_dict
    assert "serviceId" in response_dict
    assert "dateTime" in response_dict
    assert "durationMinutes" in response_dict
    assert "createdAt" in response_dict
    assert "updatedAt" in response_dict
    assert "clientName" in response_dict
    assert "clientPhone" in response_dict
    
    # Validar que snake_case NÃO está presente
    assert "user_id" not in response_dict
    assert "business_id" not in response_dict
    assert "date_time" not in response_dict
    assert "duration_minutes" not in response_dict
    assert "created_at" not in response_dict
    
    print("✅ CF001 - Appointment response aliases working")

def test_cf001_appointment_request_both_formats():
    """Testa que request aceita ambos formatos CF001"""
    
    # Request em camelCase
    camel_request = {
        "userId": 123,
        "businessId": 456,
        "dateTime": "2025-09-12T14:00:00",
        "durationMinutes": 60,
        "clientName": "João Silva"
    }
    
    # Request em snake_case  
    snake_request = {
        "user_id": 123,
        "business_id": 456,
        "date_time": "2025-09-12T14:00:00",
        "duration_minutes": 60,
        "client_name": "João Silva"
    }
    
    # Ambos devem funcionar
    camel_schema = UnifiedAppointmentRequest(**camel_request)
    snake_schema = UnifiedAppointmentRequest(**snake_request)
    
    # Validar que dados foram parseados corretamente
    assert camel_schema.user_id == 123
    assert camel_schema.business_id == 456
    assert camel_schema.duration_minutes == 60
    
    assert snake_schema.user_id == 123
    assert snake_schema.business_id == 456
    assert snake_schema.duration_minutes == 60
    
    print("✅ CF001 - Request accepts both camelCase and snake_case")

def test_cf001_conversation_response_aliases():
    """Testa aliases em conversation responses CF001"""
    
    conversation_data = {
        "id": 1,
        "user_id": 123,
        "business_id": 456,
        "status": "active",
        "last_message_at": datetime(2025, 9, 12, 15, 30),
        "created_at": datetime(2025, 9, 12, 10, 0),
        "updated_at": datetime(2025, 9, 12, 15, 30),
        "total_messages": 25,
        "unread_messages": 3
    }
    
    response = UnifiedConversationResponse(**conversation_data)
    response_dict = response.model_dump(by_alias=True)
    
    # Validar campos críticos CF001
    assert "userId" in response_dict
    assert "businessId" in response_dict
    assert "lastMessageAt" in response_dict
    assert "createdAt" in response_dict
    assert "updatedAt" in response_dict
    assert "totalMessages" in response_dict
    assert "unreadMessages" in response_dict
    # Note: lastInteraction is a computed property, not in serialized output
    
    print("✅ CF001 - Conversation response aliases working")

def test_cf001_message_response_aliases():
    """Testa aliases em message responses CF001"""
    
    message_data = {
        "id": 1,
        "conversation_id": 123,
        "content": "Teste CF001",
        "message_type": "text",
        "direction": "in",
        "is_read": True,
        "is_active": True,
        "created_at": datetime(2025, 9, 12, 15, 45),
        "sender_name": "João",
        "whatsapp_id": "msg_123"
    }
    
    response = UnifiedMessageResponse(**message_data)
    response_dict = response.model_dump(by_alias=True)
    
    # Validar campos críticos CF001
    assert "conversationId" in response_dict
    assert "messageType" in response_dict
    assert "isRead" in response_dict
    assert "isActive" in response_dict
    assert "createdAt" in response_dict
    assert "senderName" in response_dict
    assert "whatsappId" in response_dict
    
    print("✅ CF001 - Message response aliases working")

def test_cf001_field_mapping_coverage():
    """Testa se todos os 15 campos críticos estão mapeados"""
    
    expected_fields = {
        "date_time": "dateTime",
        "duration_minutes": "durationMinutes",
        "user_id": "userId",
        "business_id": "businessId",
        "service_id": "serviceId",
        "created_at": "createdAt",
        "updated_at": "updatedAt",
        "last_message_at": "lastMessageAt",
        "message_type": "messageType",
        "conversation_id": "conversationId",
        "is_active": "isActive",
        "is_read": "isRead",
        "total_messages": "totalMessages",
        "unread_messages": "unreadMessages",
        "last_interaction": "lastInteraction"
    }
    
    # Validar que CF001_FIELD_MAPPING tem todos os 15 campos
    assert len(CF001_FIELD_MAPPING) == 15
    
    for snake_case, camel_case in expected_fields.items():
        assert snake_case in CF001_FIELD_MAPPING
        assert CF001_FIELD_MAPPING[snake_case] == camel_case
    
    print("✅ CF001 - All 15 critical fields mapped correctly")

def test_cf001_utility_functions():
    """Testa funções utilitárias de conversão CF001"""
    
    # Teste snake_to_camel
    snake_data = {
        "user_id": 123,
        "business_id": 456,
        "date_time": "2025-09-12T14:00:00",
        "duration_minutes": 60,
        "is_active": True
    }
    
    camel_data = convert_snake_to_camel(snake_data)
    
    assert camel_data["userId"] == 123
    assert camel_data["businessId"] == 456
    assert camel_data["dateTime"] == "2025-09-12T14:00:00"
    assert camel_data["durationMinutes"] == 60
    assert camel_data["isActive"] == True
    
    # Teste camel_to_snake
    reversed_data = convert_camel_to_snake(camel_data)
    
    assert reversed_data["user_id"] == 123
    assert reversed_data["business_id"] == 456
    assert reversed_data["date_time"] == "2025-09-12T14:00:00"
    assert reversed_data["duration_minutes"] == 60
    assert reversed_data["is_active"] == True
    
    print("✅ CF001 - Utility functions working correctly")

def test_cf001_integration():
    """Teste de integração completo CF001"""
    try:
        test_cf001_appointment_response_aliases()
        test_cf001_appointment_request_both_formats()
        test_cf001_conversation_response_aliases()
        test_cf001_message_response_aliases()
        test_cf001_field_mapping_coverage()
        test_cf001_utility_functions()
        
        print("\\n🎉 CF001 - All tests passed!")
        print("✅ snake_case ↔ camelCase standardization working")
        print("✅ 15 critical fields mapped correctly")
        print("✅ Pydantic aliases functioning properly")
        print("✅ Backward compatibility maintained")
        
        return True
    except Exception as e:
        print(f"❌ CF001 - Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 CF001 Test Suite - Naming Standardization")
    print("=" * 50)
    
    result = test_cf001_integration()
    
    if result:
        print("\\n✅ CF001 VALIDATION PASSED")
    else:
        print("\\n❌ CF001 VALIDATION FAILED")
        exit(1)
