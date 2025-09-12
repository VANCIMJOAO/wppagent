#!/usr/bin/env python3
"""
🔍 P001: Teste para identificar N+1 queries em appointments

Problema: N+1 queries em appointments
Solução: Implementar joinedload para relacionamentos
Meta: Query count < 5 para 100 appointments
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import select

from app.database import AsyncSessionLocal
from app.models.database import Appointment, User, Business, Service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Query counter
query_count = 0
executed_queries = []

def count_queries(conn, cursor, statement, parameters, context, executemany):
    """Hook para contar queries executadas"""
    global query_count, executed_queries
    query_count += 1
    # Store query info (truncate for readability)
    query_info = {
        'count': query_count,
        'statement': str(statement)[:200] + '...' if len(str(statement)) > 200 else str(statement),
        'parameters': str(parameters)[:100] if parameters else None
    }
    executed_queries.append(query_info)
    print(f"🔍 Query #{query_count}: {query_info['statement']}")

def reset_query_counter():
    """Reset contador de queries"""
    global query_count, executed_queries
    query_count = 0
    executed_queries = []

async def test_current_implementation(session: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Testa a implementação atual (com JOINs mas sem joinedload)
    """
    print(f"\n🧪 Testando implementação ATUAL com {limit} appointments...")
    reset_query_counter()
    
    # Query atual (similar ao código de produção)
    query = select(
        Appointment,
        User.nome.label("user_name"),
        User.telefone.label("user_phone"),
        Business.name.label("business_name"),
        Service.name.label("service_name")
    ).select_from(
        Appointment
    ).join(
        User, Appointment.user_id == User.id
    ).join(
        Business, Appointment.business_id == Business.id
    ).outerjoin(
        Service, Appointment.service_id == Service.id
    ).order_by(Appointment.date_time.desc()).limit(limit)
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    appointments = []
    for row in rows:
        appointment = row.Appointment
        appointment_data = {
            "id": appointment.id,
            "user_id": appointment.user_id,
            "business_id": appointment.business_id,
            "service_id": appointment.service_id,
            "date_time": appointment.date_time,
            "status": appointment.status,
            "user_name": row.user_name,
            "user_phone": row.user_phone,
            "business_name": row.business_name,
            "service_name": row.service_name
        }
        appointments.append(appointment_data)
    
    print(f"✅ Busca atual: {len(appointments)} appointments com {query_count} queries")
    return appointments

async def test_with_joinedload(session: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Testa implementação otimizada com joinedload
    """
    print(f"\n🚀 Testando implementação OTIMIZADA com {limit} appointments...")
    reset_query_counter()
    
    # Query otimizada com joinedload
    query = select(Appointment).options(
        joinedload(Appointment.user),
        joinedload(Appointment.business),
        joinedload(Appointment.service)
    ).order_by(Appointment.date_time.desc()).limit(limit)
    
    result = await session.execute(query)
    appointments_orm = result.scalars().unique().all()
    
    appointments = []
    for appointment in appointments_orm:
        appointment_data = {
            "id": appointment.id,
            "user_id": appointment.user_id,
            "business_id": appointment.business_id,
            "service_id": appointment.service_id,
            "date_time": appointment.date_time,
            "status": appointment.status,
            "user_name": appointment.user.nome if appointment.user else None,
            "user_phone": appointment.user.telefone if appointment.user else None,
            "business_name": appointment.business.name if appointment.business else None,
            "service_name": appointment.service.name if appointment.service else None
        }
        appointments.append(appointment_data)
    
    print(f"✅ Busca otimizada: {len(appointments)} appointments com {query_count} queries")
    return appointments

async def test_with_selectinload(session: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Testa implementação com selectinload (alternativa ao joinedload)
    """
    print(f"\n🔄 Testando implementação com SELECTINLOAD com {limit} appointments...")
    reset_query_counter()
    
    # Query com selectinload
    query = select(Appointment).options(
        selectinload(Appointment.user),
        selectinload(Appointment.business),
        selectinload(Appointment.service)
    ).order_by(Appointment.date_time.desc()).limit(limit)
    
    result = await session.execute(query)
    appointments_orm = result.scalars().all()
    
    appointments = []
    for appointment in appointments_orm:
        appointment_data = {
            "id": appointment.id,
            "user_id": appointment.user_id,
            "business_id": appointment.business_id,
            "service_id": appointment.service_id,
            "date_time": appointment.date_time,
            "status": appointment.status,
            "user_name": appointment.user.nome if appointment.user else None,
            "user_phone": appointment.user.telefone if appointment.user else None,
            "business_name": appointment.business.name if appointment.business else None,
            "service_name": appointment.service.name if appointment.service else None
        }
        appointments.append(appointment_data)
    
    print(f"✅ Busca selectinload: {len(appointments)} appointments com {query_count} queries")
    return appointments

async def test_naive_approach(session: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Testa abordagem ingênua que causaria N+1 queries
    """
    print(f"\n⚠️  Testando abordagem INGÊNUA (N+1) com {limit} appointments...")
    reset_query_counter()
    
    # Query simples sem JOINs ou joinedload
    query = select(Appointment).order_by(Appointment.date_time.desc()).limit(limit)
    result = await session.execute(query)
    appointments_orm = result.scalars().all()
    
    appointments = []
    for appointment in appointments_orm:
        # Isso dispararia lazy loading!
        appointment_data = {
            "id": appointment.id,
            "user_id": appointment.user_id,
            "business_id": appointment.business_id,
            "service_id": appointment.service_id,
            "date_time": appointment.date_time,
            "status": appointment.status,
            # Acessos que disparariam N+1:
            # "user_name": appointment.user.nome if appointment.user else None,
            # "business_name": appointment.business.name if appointment.business else None,
            # "service_name": appointment.service.name if appointment.service else None,
        }
        appointments.append(appointment_data)
    
    print(f"✅ Busca ingênua (sem acessos lazy): {len(appointments)} appointments com {query_count} queries")
    return appointments

async def run_performance_tests():
    """
    Executa todos os testes de performance
    """
    print("🚀 Iniciando testes de performance P001...")
    print("=" * 60)
    
    # Get database session
    async with AsyncSessionLocal() as session:
        # Hook query counting
        event.listen(session.bind, "before_cursor_execute", count_queries)
        
        try:
            # Count total appointments
            count_result = await session.execute(select(text("COUNT(*) FROM appointments")))
            total_appointments = count_result.scalar()
            print(f"📊 Total appointments na base: {total_appointments}")
            
            if total_appointments == 0:
                print("⚠️  Não há appointments na base! Criando alguns para teste...")
                await create_test_data(session)
                # Re-count
                count_result = await session.execute(select(text("COUNT(*) FROM appointments")))
                total_appointments = count_result.scalar()
            
            test_sizes = [5, 10, 20] if total_appointments < 50 else [10, 20, 50]
            
            for limit in test_sizes:
                print(f"\n{'=' * 20} TESTE COM {limit} APPOINTMENTS {'=' * 20}")
                
                # Test 1: Current implementation 
                current_results = await test_current_implementation(session, limit)
                current_queries = query_count
                
                # Test 2: Optimized with joinedload
                optimized_results = await test_with_joinedload(session, limit)
                optimized_queries = query_count
                
                # Test 3: Alternative with selectinload
                selectin_results = await test_with_selectinload(session, limit)
                selectin_queries = query_count
                
                # Test 4: Naive approach (without accessing relationships)
                naive_results = await test_naive_approach(session, limit)
                naive_queries = query_count
                
                # Summary
                print(f"\n📊 RESUMO para {limit} appointments:")
                print(f"   Current (JOINs):     {current_queries} queries")
                print(f"   Joinedload:          {optimized_queries} queries")
                print(f"   Selectinload:        {selectin_queries} queries")
                print(f"   Naive (sem lazy):    {naive_queries} queries")
                
                # Check if we meet the goal
                goal_queries = 5
                if optimized_queries <= goal_queries:
                    print(f"✅ Meta atingida! Joinedload usa {optimized_queries} ≤ {goal_queries} queries")
                else:
                    print(f"❌ Meta não atingida! Joinedload usa {optimized_queries} > {goal_queries} queries")
                
                if selectin_queries <= goal_queries:
                    print(f"✅ Meta atingida! Selectinload usa {selectin_queries} ≤ {goal_queries} queries")
                else:
                    print(f"❌ Meta não atingida! Selectinload usa {selectin_queries} > {goal_queries} queries")
                    
        except Exception as e:
            print(f"❌ Erro durante teste: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Remove event listener
            event.remove(session.bind, "before_cursor_execute", count_queries)

async def create_test_data(session: AsyncSession):
    """
    Cria dados de teste se não existirem
    """
    print("🔧 Criando dados de teste...")
    
    # Create test users, businesses, services if needed
    # This is a simplified version - in real scenario you'd check existing data
    from datetime import datetime, timedelta
    
    # Check if we have test data
    user_count = await session.execute(select(text("COUNT(*) FROM users")))
    if user_count.scalar() < 5:
        print("⚠️  Poucos usuários na base. Para teste completo, adicione mais dados.")
    
    business_count = await session.execute(select(text("COUNT(*) FROM businesses")))
    if business_count.scalar() < 1:
        print("⚠️  Poucos negócios na base. Para teste completo, adicione mais dados.")
    
    appointment_count = await session.execute(select(text("COUNT(*) FROM appointments"))) 
    if appointment_count.scalar() < 10:
        print("⚠️  Poucos agendamentos na base. Para teste completo, adicione mais dados.")

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
