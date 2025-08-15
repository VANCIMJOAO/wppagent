#!/usr/bin/env python3
"""
🔧 TESTE DIRETO - Funções de Formatação
======================================
Testa as funções de formatação diretamente
"""

import asyncio
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.append('/home/vancim/whats_agent')

async def test_formatting_functions():
    """Testa as funções de formatação diretamente"""
    
    print("🔧 TESTE DIRETO DAS FUNÇÕES DE FORMATAÇÃO")
    print("=" * 50)
    
    try:
        # Importar e testar get_database_services_formatted
        print("📋 Testando get_database_services_formatted...")
        from app.services.business_data import get_database_services_formatted
        
        result = await get_database_services_formatted()
        print(f"✅ Função executada com sucesso!")
        print(f"📄 Resultado ({len(result)} caracteres):")
        print("-" * 40)
        print(result[:300] + "..." if len(result) > 300 else result)
        print("-" * 40)
        
        # Verificar formatação
        elements_check = {
            "💰": "Emoji preço",
            "⏰": "Emoji duração",
            "📋": "Emoji lista",
            "1.": "Numeração",
            "*": "Negrito",
            "_": "Itálico"
        }
        
        found_elements = []
        for element, desc in elements_check.items():
            if element in result:
                found_elements.append(desc)
        
        print(f"🎯 Elementos de formatação encontrados: {len(found_elements)}/{len(elements_check)}")
        for element in found_elements:
            print(f"   ✅ {element}")
        
        if len(found_elements) >= 3:
            print("🎉 Formatação funcionando!")
            return True
        else:
            print("⚠️ Formatação insuficiente")
            return False
            
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_business_data_service():
    """Testa o business_data_service diretamente"""
    
    print("\n🏢 TESTE DIRETO DO BUSINESS_DATA_SERVICE")
    print("=" * 50)
    
    try:
        from app.services.business_data import business_data_service
        
        print("📋 Testando get_active_services...")
        services = await business_data_service.get_active_services()
        print(f"✅ {len(services)} serviços encontrados")
        
        if services:
            print("📄 Primeiros 3 serviços:")
            for i, service in enumerate(services[:3], 1):
                print(f"   {i}. {service.name} - {service.price}")
        
        print("\n🕘 Testando get_business_hours_formatted_text...")
        hours_text = await business_data_service.get_business_hours_formatted_text()
        print(f"✅ Horários formatados ({len(hours_text)} caracteres):")
        print(hours_text[:200] + "..." if len(hours_text) > 200 else hours_text)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🧪 DIAGNÓSTICO DAS FUNÇÕES DE FORMATAÇÃO")
    print("=" * 60)
    
    # Teste 1: Função de formatação de serviços
    test1_success = await test_formatting_functions()
    
    # Teste 2: Business data service
    test2_success = await test_business_data_service()
    
    print("\n📊 RESULTADO FINAL:")
    print("=" * 30)
    
    if test1_success and test2_success:
        print("🎉 TODAS AS FUNÇÕES FUNCIONANDO!")
        print("✅ O problema pode estar na integração")
    elif test1_success:
        print("🔧 Formatação funciona, problema no service")
    elif test2_success:
        print("🔧 Service funciona, problema na formatação")
    else:
        print("❌ PROBLEMAS DETECTADOS NAS FUNÇÕES")
        print("🛠️ Necessário revisar implementação")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n💥 Erro geral: {e}")
        import traceback
        traceback.print_exc()
