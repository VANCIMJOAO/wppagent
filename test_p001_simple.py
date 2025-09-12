#!/usr/bin/env python3
"""
🔍 P001: Teste para identificar N+1 queries em appointments - Versão Simplificada

Problema: N+1 queries em appointments
Solução: Implementar joinedload para relacionamentos
Meta: Query count < 5 para 100 appointments
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import select

from app.database import AsyncSessionLocal
from app.models.database import Appointment, User, Business, Service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_current_implementation(session: AsyncSession, limit: int = 20) -> tuple:
    """
    Testa a implementação atual (com JOINs mas sem joinedload)
    """
    print(f"\n🧪 Testando implementação ATUAL com {limit} appointments...")
    
    start_time = time.time()
    
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
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"✅ Busca atual: {len(appointments)} appointments em {execution_time:.3f}s")
    return appointments, execution_time, "1 query complexa com JOINs"

async def test_with_joinedload(session: AsyncSession, limit: int = 20) -> tuple:
    """
    Testa implementação otimizada com joinedload
    """
    print(f"\n🚀 Testando implementação OTIMIZADA com {limit} appointments...")
    
    start_time = time.time()
    
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
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"✅ Busca otimizada: {len(appointments)} appointments em {execution_time:.3f}s")
    return appointments, execution_time, "1 query com joinedload"

async def test_with_selectinload(session: AsyncSession, limit: int = 20) -> tuple:
    """
    Testa implementação com selectinload (alternativa ao joinedload)
    """
    print(f"\n🔄 Testando implementação com SELECTINLOAD com {limit} appointments...")
    
    start_time = time.time()
    
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
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"✅ Busca selectinload: {len(appointments)} appointments em {execution_time:.3f}s")
    return appointments, execution_time, "4 queries (1 principal + 3 selectinload)"

async def test_naive_with_relationships(session: AsyncSession, limit: int = 20) -> tuple:
    """
    Testa abordagem que CAUSARIA N+1 queries (acessando relacionamentos sem eager loading)
    """
    print(f"\n⚠️  Testando abordagem que CAUSARIA N+1 com {limit} appointments...")
    
    start_time = time.time()
    
    # Query simples sem JOINs ou joinedload
    query = select(Appointment).order_by(Appointment.date_time.desc()).limit(limit)
    result = await session.execute(query)
    appointments_orm = result.scalars().all()
    
    appointments = []
    for appointment in appointments_orm:
        # Isso dispararia lazy loading para cada appointment!
        appointment_data = {
            "id": appointment.id,
            "user_id": appointment.user_id,
            "business_id": appointment.business_id,
            "service_id": appointment.service_id,
            "date_time": appointment.date_time,
            "status": appointment.status,
            # Acessos que disparariam N+1:
            "user_name": appointment.user.nome if appointment.user else None,
            "user_phone": appointment.user.telefone if appointment.user else None,
            "business_name": appointment.business.name if appointment.business else None,
            "service_name": appointment.service.name if appointment.service else None,
        }
        appointments.append(appointment_data)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"⚠️  Busca N+1: {len(appointments)} appointments em {execution_time:.3f}s")
    return appointments, execution_time, f"1 + 3*{len(appointments)} queries potenciais (N+1)"

async def run_performance_tests():
    """
    Executa todos os testes de performance
    """
    print("🚀 Iniciando testes de performance P001...")
    print("=" * 60)
    
    # Get database session
    async with AsyncSessionLocal() as session:
        try:
            # Count total appointments
            count_result = await session.execute(select(text("COUNT(*) FROM appointments")))
            total_appointments = count_result.scalar()
            print(f"📊 Total appointments na base: {total_appointments}")
            
            if total_appointments == 0:
                print("⚠️  Não há appointments na base!")
                print("💡 Execute primeiro: python -c \"from app.main import *; import asyncio; asyncio.run(create_initial_data())\"")
                return
            
            test_sizes = [5, 10, 20] if total_appointments < 50 else [10, 20, 50]
            
            for limit in test_sizes:
                print(f"\n{'=' * 20} TESTE COM {limit} APPOINTMENTS {'=' * 20}")
                
                # Test 1: Current implementation 
                current_results, current_time, current_desc = await test_current_implementation(session, limit)
                
                # Test 2: Optimized with joinedload
                optimized_results, optimized_time, optimized_desc = await test_with_joinedload(session, limit)
                
                # Test 3: Alternative with selectinload
                selectin_results, selectin_time, selectin_desc = await test_with_selectinload(session, limit)
                
                # Test 4: Naive approach (that would cause N+1)
                naive_results, naive_time, naive_desc = await test_naive_with_relationships(session, limit)
                
                # Summary
                print(f"\n📊 RESUMO para {limit} appointments:")
                print(f"   Current (JOINs):     {current_time:.3f}s - {current_desc}")
                print(f"   Joinedload:          {optimized_time:.3f}s - {optimized_desc}")
                print(f"   Selectinload:        {selectin_time:.3f}s - {selectin_desc}")
                print(f"   Naive (N+1):         {naive_time:.3f}s - {naive_desc}")
                
                # Performance comparison
                if optimized_time < current_time:
                    improvement = ((current_time - optimized_time) / current_time) * 100
                    print(f"✅ Joinedload é {improvement:.1f}% mais rápido que implementação atual")
                
                if selectin_time < current_time:
                    improvement = ((current_time - selectin_time) / current_time) * 100
                    print(f"✅ Selectinload é {improvement:.1f}% mais rápido que implementação atual")
                
                # Verify data consistency
                if len(current_results) == len(optimized_results) == len(selectin_results):
                    print("✅ Todas as implementações retornam o mesmo número de resultados")
                else:
                    print("❌ Inconsistência no número de resultados!")
                    
        except Exception as e:
            print(f"❌ Erro durante teste: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
