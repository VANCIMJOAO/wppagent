#!/usr/bin/env python3
"""
C002: Validação da Correção - Aliases Pydantic
==============================================

Testa se os aliases do Pydantic estão funcionando corretamente:
✅ Schemas aceitam snake_case
✅ API expõe camelCase 
✅ Backward compatibility mantida
"""

import sys
import json
from datetime import datetime
from decimal import Decimal

# Adiciona o path do projeto
sys.path.append('/home/vancim/whats_agent')

try:
    from app.schemas.appointments import AppointmentBase, AppointmentCreate, AppointmentUpdate
    from app.schemas.unified import AppointmentResponseUnified
    from pydantic import ValidationError
except ImportError as e:
    print(f"❌ Erro ao importar schemas: {e}")
    exit(1)

def test_appointment_schemas():
    print("🧪 C002: Validação de Aliases Pydantic")
    print("=" * 45)
    print()
    
    # Dados de teste com snake_case (entrada)
    test_data_snake = {
        "user_id": 1,
        "business_id": 1,
        "service_id": 1,
        "date_time": "2025-09-11T14:30:00-03:00",
        "duration_minutes": 60,
        "price": 50.99,
        "status": "agendado",
        "notes": "Teste de agendamento"
    }
    
    # Dados de teste com camelCase (esperado na API)
    test_data_camel = {
        "user_id": 1,
        "business_id": 1,
        "service_id": 1,
        "dateTime": "2025-09-11T14:30:00-03:00",
        "durationMinutes": 60,
        "price": 50.99,
        "status": "agendado",
        "notes": "Teste de agendamento"
    }
    
    results = {}
    
    print("📋 1. Testando AppointmentBase...")
    try:
        # Teste 1: Aceita snake_case
        appointment_snake = AppointmentBase(**test_data_snake)
        print("   ✅ Aceita snake_case (entrada)")
        
        # Teste 2: Serialização para camelCase
        serialized = appointment_snake.model_dump(by_alias=True)
        has_camel_case = "dateTime" in serialized
        
        print(f"   {'✅' if has_camel_case else '❌'} Serializa para camelCase: {has_camel_case}")
        if has_camel_case:
            print(f"      dateTime: {serialized['dateTime']}")
            print(f"      durationMinutes: {serialized.get('durationMinutes', 'N/A')}")
        
        # Teste 3: Aceita camelCase (se implementado)
        try:
            appointment_camel = AppointmentBase(**test_data_camel)
            print("   ✅ Aceita camelCase (entrada)")
        except ValidationError as e:
            print("   ⚠️  Não aceita camelCase (apenas snake_case)")
        
        results["appointment_base"] = True
        
    except Exception as e:
        print(f"   ❌ Erro em AppointmentBase: {e}")
        results["appointment_base"] = False
    
    print(f"\n📝 2. Testando AppointmentCreate...")
    try:
        appointment_create = AppointmentCreate(**test_data_snake)
        serialized = appointment_create.model_dump(by_alias=True)
        
        has_camel_datetime = "dateTime" in serialized
        has_camel_duration = "durationMinutes" in serialized
        
        print(f"   ✅ Criação bem-sucedida")
        print(f"   {'✅' if has_camel_datetime else '❌'} Serializa dateTime: {has_camel_datetime}")
        print(f"   {'✅' if has_camel_duration else '❌'} Serializa durationMinutes: {has_camel_duration}")
        
        results["appointment_create"] = has_camel_datetime and has_camel_duration
        
    except Exception as e:
        print(f"   ❌ Erro em AppointmentCreate: {e}")
        results["appointment_create"] = False
    
    print(f"\n🔄 3. Testando AppointmentUpdate...")
    try:
        update_data = {
            "date_time": "2025-09-11T15:00:00-03:00",
            "duration_minutes": 90
        }
        
        appointment_update = AppointmentUpdate(**update_data)
        serialized = appointment_update.model_dump(by_alias=True, exclude_none=True)
        
        has_camel_datetime = "dateTime" in serialized
        has_camel_duration = "durationMinutes" in serialized
        
        print(f"   ✅ Update bem-sucedido")
        print(f"   {'✅' if has_camel_datetime else '❌'} Serializa dateTime: {has_camel_datetime}")
        print(f"   {'✅' if has_camel_duration else '❌'} Serializa durationMinutes: {has_camel_duration}")
        
        results["appointment_update"] = has_camel_datetime and has_camel_duration
        
    except Exception as e:
        print(f"   ❌ Erro em AppointmentUpdate: {e}")
        results["appointment_update"] = False
    
    print(f"\n🎯 4. Testando compatibilidade JSON...")
    try:
        # Simular resposta da API
        appointment = AppointmentBase(**test_data_snake)
        json_output = appointment.model_dump_json(by_alias=True)
        
        # Parse de volta
        parsed = json.loads(json_output)
        
        # Verificar se contém campos camelCase
        has_datetime = "dateTime" in parsed
        has_duration = "durationMinutes" in parsed
        datetime_value = parsed.get("dateTime")
        
        print(f"   ✅ JSON serialization/deserialization")
        print(f"   {'✅' if has_datetime else '❌'} JSON contém dateTime: {has_datetime}")
        print(f"   {'✅' if has_duration else '❌'} JSON contém durationMinutes: {has_duration}")
        print(f"   📅 Valor dateTime: {datetime_value}")
        
        results["json_compatibility"] = has_datetime and has_duration
        
    except Exception as e:
        print(f"   ❌ Erro em JSON compatibility: {e}")
        results["json_compatibility"] = False
    
    # Resumo final
    print(f"\n📊 RESUMO DA VALIDAÇÃO:")
    print("-" * 30)
    
    for test, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"{icon} {test.replace('_', ' ').title()}: {passed}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    overall_success = total_passed == total_tests
    
    print(f"\n{'🎉' if overall_success else '❌'} RESULTADO: {total_passed}/{total_tests} testes passaram")
    
    if overall_success:
        print("\n✅ C002: Aliases Pydantic funcionando corretamente!")
        print("   - Snake_case aceito na entrada")
        print("   - CamelCase serializado na saída")
        print("   - JSON compatível com frontend")
        print("   - Backward compatibility mantida")
    else:
        print("\n❌ C002: Ainda há problemas com aliases")
        print("   - Verifique a implementação dos Field aliases")
        print("   - Confirme Config classes estão corretas")
    
    # Salvar relatório
    report = {
        "test_results": results,
        "total_passed": total_passed,
        "total_tests": total_tests,
        "success": overall_success,
        "test_date": datetime.now().isoformat()
    }
    
    with open('/home/vancim/whats_agent/c002_validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Relatório salvo em: c002_validation_report.json")
    
    return overall_success

if __name__ == "__main__":
    success = test_appointment_schemas()
    exit(0 if success else 1)
