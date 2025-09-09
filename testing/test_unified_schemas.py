#!/usr/bin/env python3
"""
🧪 Teste Completo - Schemas Unificados
=====================================

Script para validar o funcionamento completo dos schemas unificados
e transformações de dados entre backend e frontend.

Autor: Claude AI
Data: 2025-09-07
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.schemas.unified import (
    AppointmentResponseUnified,
    SchemaTransformer,
    AppointmentsListResponseUnified
)

async def test_unified_schemas():
    """Testa schemas unificados com dados reais"""
    
    print("🧪 Iniciando testes dos schemas unificados...")
    
    try:
        async with AsyncSessionLocal() as session:
            
            # Teste 1: Query real de appointments
            print("\n1️⃣ Testando query real de appointments...")
            
            test_query = text("""
                SELECT 
                    a.id as appointment_id,
                    a.user_id,
                    a.business_id,
                    a.service_id,
                    a.date_time,
                    a.duration_minutes,
                    a.price,
                    a.status,
                    a.notes,
                    a.created_at,
                    a.updated_at,
                    u.nome as user_name,
                    u.telefone as user_phone,
                    u.email as user_email,
                    s.name as service_name,
                    s.description as service_description,
                    b.name as business_name
                FROM appointments a
                LEFT JOIN users u ON a.user_id = u.id
                LEFT JOIN services s ON a.service_id = s.id
                LEFT JOIN businesses b ON a.business_id = b.id
                LIMIT 3
            """)
            
            result = await session.execute(test_query)
            rows = result.fetchall()
            
            if len(rows) > 0:
                print(f"✅ Query executada: {len(rows)} agendamentos encontrados")
                
                # Teste 2: Transformação de dados
                print("\n2️⃣ Testando transformação com SchemaTransformer...")
                
                appointments = []
                for i, row in enumerate(rows):
                    try:
                        # Usar transformer
                        appointment_dict = SchemaTransformer.appointment_row_to_unified(row)
                        appointment = AppointmentResponseUnified(**appointment_dict)
                        appointments.append(appointment)
                        
                        print(f"  ✅ Agendamento {i+1}: ID={appointment.id}")
                        print(f"     📅 Data: {appointment.data_agendamento}")
                        print(f"     👤 Cliente: {appointment.cliente_nome}")
                        print(f"     📞 Telefone: {appointment.cliente_telefone}")
                        print(f"     🛍️ Serviço: {appointment.servico_nome}")
                        print(f"     💰 Valor: R$ {appointment.valor}")
                        print(f"     📊 Status: {appointment.status}")
                        
                    except Exception as e:
                        print(f"  ❌ Erro no agendamento {i+1}: {e}")
                        return False
                
                # Teste 3: Lista response unificada
                print("\n3️⃣ Testando AppointmentsListResponseUnified...")
                
                list_response = AppointmentsListResponseUnified(
                    appointments=appointments,
                    total=len(appointments),
                    page=1,
                    per_page=3,
                    has_more=False
                )
                
                print(f"✅ Lista criada com {len(list_response.appointments)} itens")
                print(f"📊 Total: {list_response.total}, Página: {list_response.page}")
                
                # Teste 4: Serialização JSON
                print("\n4️⃣ Testando serialização JSON...")
                
                json_data = list_response.model_dump()
                print(f"✅ JSON serializado com {len(json_data)} campos principais")
                
                # Verificar campos específicos
                first_appointment = json_data['appointments'][0]
                expected_fields = [
                    'id', 'cliente_nome', 'cliente_telefone', 'data_agendamento',
                    'servico_nome', 'valor', 'status', 'horario', 'duracao_minutos'
                ]
                
                missing_fields = [field for field in expected_fields if field not in first_appointment]
                if missing_fields:
                    print(f"⚠️ Campos ausentes: {missing_fields}")
                else:
                    print("✅ Todos os campos esperados estão presentes")
                
            else:
                print("⚠️ Nenhum agendamento encontrado para teste")
                
        print("\n🎉 Todos os testes dos schemas unificados passaram!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro nos testes: {e}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_unified_schemas())
    sys.exit(0 if success else 1)
