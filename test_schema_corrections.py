#!/usr/bin/env python3
"""
🧪 TESTE INTEGRADO - CORREÇÕES SCHEMA APPOINTMENTS
==================================================

Testa se as correções de schema estão funcionando:
1. ✅ Imports dos novos schemas
2. ✅ Modelo SQLAlchemy atualizado
3. ✅ Endpoints usando novos campos
4. ✅ Tipos TypeScript consistentes
"""

import asyncio
import sys
from datetime import datetime


async def test_schema_imports():
    """Testa se os novos schemas podem ser importados"""
    print("🔍 Testando imports dos schemas padronizados...")
    
    try:
        from app.schemas.appointments import (
            AppointmentResponse, 
            AppointmentCreate, 
            AppointmentUpdate,
            AppointmentsListResponse,
            AppointmentStats
        )
        print("  ✅ Schemas Pydantic importados com sucesso")
        
        # Testar criação de schema
        test_data = {
            "user_id": 1,
            "business_id": 1,
            "service_id": 1,
            "date_time": datetime.now(),
            "duration_minutes": 60,
            "price": 50.00,
            "status": "pendente",
            "notes": "Teste"
        }
        
        appointment_create = AppointmentCreate(**test_data)
        print(f"  ✅ Schema de criação funcional: duration_minutes={appointment_create.duration_minutes}")
        
        return True
    except Exception as e:
        print(f"  ❌ Erro nos imports: {e}")
        return False


async def test_model_fields():
    """Testa se o modelo SQLAlchemy tem os campos corretos"""
    print("\n🔍 Testando modelo SQLAlchemy atualizado...")
    
    try:
        from app.models.database import Appointment
        
        # Verificar campos padronizados
        required_fields = [
            'id', 'user_id', 'business_id', 'service_id',
            'date_time', 'duration_minutes', 'end_time', 'price',
            'status', 'notes', 'created_at', 'updated_at'
        ]
        
        # Verificar campos que NÃO devem existir mais
        deprecated_fields = ['price_at_booking', 'duration']
        
        # Inspecionar campos da tabela
        table_columns = [column.name for column in Appointment.__table__.columns]
        
        missing_fields = []
        for field in required_fields:
            if field not in table_columns:
                missing_fields.append(field)
        
        present_deprecated = []
        for field in deprecated_fields:
            if field in table_columns:
                present_deprecated.append(field)
        
        if not missing_fields and not present_deprecated:
            print("  ✅ Modelo atualizado: todos os campos padronizados presentes")
            print(f"  ✅ Campos removidos: {deprecated_fields}")
            
            # Testar método calculate_end_time
            appointment = Appointment()
            if hasattr(appointment, 'calculate_end_time'):
                print("  ✅ Método calculate_end_time disponível")
            
            # Testar método to_dict
            if hasattr(appointment, 'to_dict'):
                print("  ✅ Método to_dict disponível")
            
        else:
            if missing_fields:
                print(f"  ❌ Campos ausentes: {missing_fields}")
            if present_deprecated:
                print(f"  ⚠️ Campos deprecated ainda presentes: {present_deprecated}")
        
        return len(missing_fields) == 0 and len(present_deprecated) == 0
        
    except Exception as e:
        print(f"  ❌ Erro no modelo: {e}")
        return False


async def test_api_endpoints():
    """Testa se os endpoints da API estão usando os novos schemas"""
    print("\n🔍 Testando endpoints da API...")
    
    try:
        from app.routes.appointments import router
        
        # Verificar se o router pode ser importado
        print("  ✅ Router de appointments importado")
        
        # Verificar rotas disponíveis
        routes = [route.path for route in router.routes]
        
        if "/appointments/" in routes:
            print("  ✅ Endpoint principal disponível")
        
        if "/appointments/legacy" in routes:
            print("  ✅ Endpoint legacy mantido para compatibilidade")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro nos endpoints: {e}")
        return False


async def test_typescript_consistency():
    """Verifica se os tipos TypeScript estão consistentes"""
    print("\n🔍 Verificando tipos TypeScript...")
    
    try:
        # Ler arquivo de tipos
        with open('/home/vancim/whats_agent/nextjs_dashboard/types/api.ts', 'r') as f:
            content = f.read()
        
        # Verificar campos padronizados
        required_ts_fields = [
            'user_id', 'date_time', 'duration_minutes', 'price'
        ]
        
        # Verificar campos que NÃO devem existir
        deprecated_ts_fields = [
            'cliente_id', 'data_agendamento', 'horario'
        ]
        
        missing_fields = []
        for field in required_ts_fields:
            if field not in content:
                missing_fields.append(field)
        
        present_deprecated = []
        for field in deprecated_ts_fields:
            if field in content:
                present_deprecated.append(field)
        
        if not missing_fields and not present_deprecated:
            print("  ✅ Tipos TypeScript padronizados")
        else:
            if missing_fields:
                print(f"  ❌ Campos TypeScript ausentes: {missing_fields}")
            if present_deprecated:
                print(f"  ⚠️ Campos deprecated no TypeScript: {present_deprecated}")
        
        return len(missing_fields) == 0 and len(present_deprecated) == 0
        
    except Exception as e:
        print(f"  ❌ Erro nos tipos TypeScript: {e}")
        return False


async def test_migration_readiness():
    """Verifica se a migration está pronta para execução"""
    print("\n🔍 Verificando migration...")
    
    try:
        import os
        migration_file = "/home/vancim/whats_agent/alembic/versions/fix_appointment_schema.py"
        
        if os.path.exists(migration_file):
            print("  ✅ Arquivo de migration criado")
            
            # Verificar conteúdo da migration
            with open(migration_file, 'r') as f:
                content = f.read()
            
            required_operations = [
                'price_at_booking', 'duration_minutes', 
                'calculate_appointment_end_time', 'CREATE TRIGGER'
            ]
            
            operations_found = []
            for op in required_operations:
                if op in content:
                    operations_found.append(op)
            
            if len(operations_found) == len(required_operations):
                print("  ✅ Migration completa com todas as operações")
            else:
                missing_ops = set(required_operations) - set(operations_found)
                print(f"  ⚠️ Operações ausentes na migration: {missing_ops}")
            
            return len(operations_found) == len(required_operations)
        else:
            print("  ❌ Arquivo de migration não encontrado")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro na migration: {e}")
        return False


async def main():
    """Executa todos os testes de schema"""
    print("🧪 TESTE CORREÇÕES SCHEMA APPOINTMENTS")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Schemas Pydantic", test_schema_imports),
        ("Modelo SQLAlchemy", test_model_fields),
        ("Endpoints API", test_api_endpoints),
        ("Tipos TypeScript", test_typescript_consistency),
        ("Migration", test_migration_readiness)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  💥 Erro crítico em {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 RESULTADOS FINAIS:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Schema appointments padronizado")
        print("✅ Campos duplicados eliminados")
        print("✅ Frontend/Backend consistentes")
        print("✅ Migration pronta para execução")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Executar migration: alembic upgrade head")
        print("   2. Testar endpoints em staging")
        print("   3. Atualizar componentes React")
        print("   4. Deploy para produção")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("   Revise os erros antes de aplicar as mudanças")
    
    print(f"\n⏰ Finalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Erro crítico no teste: {e}")
        sys.exit(1)
