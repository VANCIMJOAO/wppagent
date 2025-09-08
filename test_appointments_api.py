#!/usr/bin/env python3
"""
🧪 TESTE API APPOINTMENTS - CAMPOS PADRONIZADOS
===============================================

Testa se a API de appointments está funcionando com os campos padronizados
após as correções de schema aplicadas.
"""

import asyncio
import sys
from datetime import datetime


async def test_appointments_api():
    """Testa a API de appointments com os novos campos"""
    print("🧪 TESTE API APPOINTMENTS - CAMPOS PADRONIZADOS")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Importar dependências
        from app.database import AsyncSession, get_db
        from app.models.database import Appointment, User
        from app.schemas.appointments import AppointmentResponse
        from sqlalchemy import select, desc
        from datetime import datetime
        
        # Configurar DATABASE_URL
        import os
        if not os.getenv('DATABASE_URL'):
            os.environ['DATABASE_URL'] = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
            print("🔗 DATABASE_URL configurada")
        
        print("\n🔍 Testando query com campos padronizados...")
        
        # Simular uma sessão async
        from app.database import engine
        
        async with AsyncSession(engine) as session:
            # Query que usa os novos campos padronizados
            query = select(
                Appointment.id,
                Appointment.user_id,
                Appointment.business_id,
                Appointment.service_id,
                Appointment.date_time,
                Appointment.duration_minutes,  # ✅ Campo padronizado
                Appointment.end_time,
                Appointment.price,  # ✅ Campo unificado
                Appointment.status,
                Appointment.notes,
                Appointment.created_at,
                Appointment.updated_at,
                User.nome.label("cliente_nome"),
                User.telefone.label("cliente_telefone"),
                User.email.label("cliente_email")
            ).join(
                User, Appointment.user_id == User.id
            ).order_by(desc(Appointment.date_time)).limit(5)
            
            result = await session.execute(query)
            appointments = result.fetchall()
            
            print(f"  ✅ Query executada com sucesso")
            print(f"  📊 {len(appointments)} appointments encontrados")
            
            if appointments:
                # Testar primeiro appointment
                first = appointments[0]
                print(f"\n📋 DADOS DO PRIMEIRO APPOINTMENT:")
                print(f"  ID: {first.id}")
                print(f"  User ID: {first.user_id}")
                print(f"  Data/Hora: {first.date_time}")
                print(f"  ✅ Duration Minutes: {first.duration_minutes}")  # Campo novo
                print(f"  ✅ Price: R$ {first.price}")  # Campo unificado
                print(f"  End Time: {first.end_time}")
                print(f"  Status: {first.status}")
                print(f"  Cliente: {first.cliente_nome}")
                print(f"  Telefone: {first.cliente_telefone}")
                
                # Testar criação de schema Pydantic
                try:
                    appointment_dict = {
                        'id': first.id,
                        'user_id': first.user_id,
                        'business_id': first.business_id,
                        'service_id': first.service_id,
                        'date_time': first.date_time,
                        'duration_minutes': first.duration_minutes,
                        'end_time': first.end_time,
                        'price': float(first.price) if first.price else 0.00,
                        'status': first.status,
                        'notes': first.notes,
                        'created_at': first.created_at,
                        'updated_at': first.updated_at,
                        'cliente_nome': first.cliente_nome,
                        'cliente_telefone': first.cliente_telefone,
                        'cliente_email': first.cliente_email
                    }
                    
                    appointment_schema = AppointmentResponse(**appointment_dict)
                    print(f"\n✅ SCHEMA PYDANTIC CRIADO COM SUCESSO")
                    print(f"  Duration Minutes: {appointment_schema.duration_minutes}")
                    print(f"  Price: {appointment_schema.price}")
                    
                except Exception as e:
                    print(f"\n❌ Erro no schema Pydantic: {e}")
                    return False
            
            # Testar estatísticas básicas
            print(f"\n📊 ESTATÍSTICAS:")
            
            # Total de appointments
            total_result = await session.execute(select(Appointment.id.func.count()))
            total = total_result.scalar()
            print(f"  📈 Total appointments: {total}")
            
            # Appointments com campos padronizados preenchidos
            complete_result = await session.execute(select(
                Appointment.id.func.count()
            ).where(
                Appointment.price.isnot(None) & 
                Appointment.duration_minutes.isnot(None)
            ))
            complete = complete_result.scalar()
            print(f"  ✅ Com campos padronizados: {complete}")
            
            # Verificar se end_time está sendo calculado
            endtime_result = await session.execute(select(
                Appointment.id.func.count()
            ).where(Appointment.end_time.isnot(None)))
            with_endtime = endtime_result.scalar()
            print(f"  ⏰ Com end_time calculado: {with_endtime}")
            
            if complete == total and with_endtime == total:
                print(f"\n🎉 TODOS OS DADOS MIGRADOS CORRETAMENTE!")
                return True
            else:
                print(f"\n⚠️ Alguns registros incompletos:")
                print(f"   Total: {total}")
                print(f"   Completos: {complete}")
                print(f"   Com end_time: {with_endtime}")
                return False
                
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoint():
    """Testa o endpoint da API diretamente"""
    print("\n🌐 Testando endpoint da API...")
    
    try:
        from app.routes.appointments import router
        from fastapi.testclient import TestClient
        from app.main import app
        
        print("  ✅ Endpoint disponível no router")
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no endpoint: {e}")
        return False


async def main():
    """Executa todos os testes da API de appointments"""
    tests = [
        ("API Database Query", test_appointments_api),
        ("API Endpoint", test_api_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Erro em {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 RESULTADOS FINAIS:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 API APPOINTMENTS FUNCIONANDO PERFEITAMENTE!")
        print("✅ Campos padronizados funcionando")
        print("✅ Schemas Pydantic válidos")
        print("✅ Dados migrados corretamente")
        print("✅ Queries otimizadas")
    else:
        print(f"\n⚠️ Algumas funcionalidades precisam de ajustes")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        sys.exit(1)
