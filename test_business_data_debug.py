#!/usr/bin/env python3
"""
🔧 TESTE DEBUG - Business Data
==============================
Testa cada parte do business_data.py separadamente
para identificar onde está o problema
"""

import asyncio
import logging
from app.services.business_data import BusinessDataService, get_database_services_formatted
from app.utils.dynamic_prompts import get_dynamic_system_prompt_with_database

# Configurar logging
logging.basicConfig(level=logging.INFO)

async def test_business_data_step_by_step():
    print("🔧 TESTE DEBUG - Business Data")
    print("=" * 50)
    
    # 1. Testar a classe BusinessDataService diretamente
    print("\n1️⃣ TESTANDO BusinessDataService diretamente:")
    try:
        service = BusinessDataService(business_id=3)
        services = await service.get_active_services()
        print(f"   ✅ Encontrados {len(services)} serviços")
        if services:
            print(f"   📋 Primeiro serviço: {services[0].name} - {services[0].price}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 2. Testar a função de formatação da classe
    print("\n2️⃣ TESTANDO get_services_formatted_text da classe:")
    try:
        formatted = await service.get_services_formatted_text()
        print(f"   ✅ Formatação gerada: {len(formatted)} caracteres")
        print(f"   📝 Preview: {formatted[:200]}...")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 3. Testar a função global
    print("\n3️⃣ TESTANDO get_database_services_formatted global:")
    try:
        global_formatted = await get_database_services_formatted()
        print(f"   ✅ Formatação global: {len(global_formatted)} caracteres")
        print(f"   📝 Preview: {global_formatted[:200]}...")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 4. Testar dynamic_prompts
    print("\n4️⃣ TESTANDO dynamic_prompts integration:")
    try:
        prompt = await get_dynamic_system_prompt_with_database()
        if "📋 *Nossos Serviços" in prompt:
            print("   ✅ Dynamic prompts está usando dados formatados!")
            print("   📝 Serviços encontrados no prompt")
        else:
            print("   ⚠️ Dynamic prompts NÃO está usando dados formatados")
            print(f"   📝 Preview do prompt: {prompt[:300]}...")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 DEBUG CONCLUÍDO")

if __name__ == "__main__":
    asyncio.run(test_business_data_step_by_step())
