#!/usr/bin/env python3
"""
Teste da correção do sistema de busca de serviços
Verifica se os problemas críticos foram resolvidos
"""

import asyncio
import sys
import os

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.business_data import business_data_service

async def test_service_search():
    """Testa busca de serviços com os termos problemáticos"""
    
    print("🧪 TESTE DA CORREÇÃO DO SISTEMA DE BUSCA")
    print("=" * 50)
    
    # Casos problemáticos identificados
    test_cases = [
        "limpeza de pele",
        "massagem relaxante", 
        "radiofrequência",
        "radiofrequencia",
        "hidrofacial",
        "criolipólise",
        "massagem",
        "corte",
        "manicure",
        "depilação",
        "peeling",
        "drenagem"
    ]
    
    print("\n🔍 TESTANDO BUSCA INTELIGENTE:")
    print("-" * 30)
    
    for term in test_cases:
        try:
            service = await business_data_service.find_service_by_name(term)
            if service:
                print(f"✅ '{term}' → Encontrou: {service.name} ({service.price})")
            else:
                print(f"❌ '{term}' → NÃO encontrado")
        except Exception as e:
            print(f"⚠️ '{term}' → Erro: {e}")
    
    print("\n📋 TESTANDO RESPOSTA FORMATADA:")
    print("-" * 30)
    
    critical_tests = ["limpeza de pele", "massagem relaxante", "radiofrequência"]
    
    for term in critical_tests:
        try:
            info = await business_data_service.get_service_info_formatted(term)
            print(f"\n🎯 TESTE: '{term}'")
            print(f"Resposta: {info[:100]}...")
        except Exception as e:
            print(f"⚠️ ERRO em '{term}': {e}")
    
    print("\n🏁 TESTE CONCLUÍDO")

if __name__ == "__main__":
    asyncio.run(test_service_search())
