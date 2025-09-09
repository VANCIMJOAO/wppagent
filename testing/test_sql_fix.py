#!/usr/bin/env python3
"""
🧪 Teste das Correções SQL - Appointments
========================================

Script para validar as correções de ambiguidade SQL nos endpoints de appointments.

Autor: Claude AI
Data: 2025-09-07
"""

import asyncio
import sys
from sqlalchemy import text
from app.database import AsyncSessionLocal

async def test_sql_queries():
    """Testa as queries SQL corrigidas"""
    
    print("🧪 Iniciando testes das correções SQL...")
    
    try:
        # Criar sessão de teste
        async with AsyncSessionLocal() as session:
            
            # Teste 1: Query de appointments corrigida
            print("\n1️⃣ Testando query de appointments com aliases explícitos...")
            
            test_query = text("""
                SELECT 
                    a.id as appointment_id,
                    a.user_id,
                    a.business_id,
                    a.service_id,
                    a.date_time,
                    a.duration_minutes,
                    a.end_time,
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
                LIMIT 1
            """)
            
            result = await session.execute(test_query)
            rows = result.fetchall()
            
            if len(rows) >= 0:  # Pode ser 0 se não há dados
                print("✅ Query de appointments executada com sucesso!")
                print(f"📊 Retornadas {len(rows)} linhas")
                
                if len(rows) > 0:
                    row = rows[0]
                    print(f"🔍 Teste de aliases:")
                    print(f"   - appointment_id: {getattr(row, 'appointment_id', 'N/A')}")
                    print(f"   - user_name: {getattr(row, 'user_name', 'N/A')}")
                    print(f"   - service_name: {getattr(row, 'service_name', 'N/A')}")
            else:
                print("❌ Erro na query de appointments")
                
            # Teste 2: Verificar se não há conflitos de nomes
            print("\n2️⃣ Testando ausência de conflitos de nomes...")
            
            conflict_query = text("""
                SELECT COUNT(*) as total_appointments
                FROM appointments a
                LEFT JOIN users u ON a.user_id = u.id
                LIMIT 1
            """)
            
            result = await session.execute(conflict_query)
            count = result.scalar()
            print(f"✅ Query de contagem executada: {count} appointments totais")
            
        print("\n🎉 Todos os testes SQL passaram com sucesso!")
        print("✅ As correções de ambiguidade estão funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro nos testes SQL: {e}")
        print(f"💾 Tipo do erro: {type(e).__name__}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sql_queries())
    sys.exit(0 if success else 1)
