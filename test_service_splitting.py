#!/usr/bin/env python3
"""
Test script for WhatsApp service list splitting functionality
Validates auto-detection of 'mais serviços' request and proper 2-part division
"""
import asyncio
import sys
from app.services.business_data import business_data_service

async def test_service_splitting():
    """Test the service splitting functionality"""
    print("🔥 TESTE: Divisão Automática de Serviços WhatsApp")
    print("=" * 60)
    
    # Test 1: Normal service request (should show Part 1/2)
    print("\n📋 TESTE 1: Pedido normal de serviços (deve mostrar Parte 1/2)")
    print("-" * 50)
    
    user_message_1 = "Quais serviços vocês oferecem?"
    result_1 = await business_data_service.get_services_formatted_text(user_message_1)
    
    print(f"📨 Mensagem do usuário: {user_message_1}")
    print(f"🤖 Resposta do bot:")
    print(result_1)
    print(f"📏 Tamanho: {len(result_1)} caracteres")
    
    # Validation checks
    if "Parte 1/2" in result_1:
        print("✅ CORRETO: Mostra Parte 1/2")
    else:
        print("❌ ERRO: Não mostra Parte 1/2")
        
    if "mais serviços" in result_1:
        print("✅ CORRETO: Inclui instrução 'mais serviços'")
    else:
        print("❌ ERRO: Não inclui instrução 'mais serviços'")
    
    # Test 2: User requests more services (should show Part 2/2)  
    print("\n📋 TESTE 2: Usuário pede 'mais serviços' (deve mostrar Parte 2/2)")
    print("-" * 50)
    
    user_message_2 = "mais serviços"
    result_2 = await business_data_service.get_services_formatted_text(user_message_2)
    
    print(f"📨 Mensagem do usuário: {user_message_2}")
    print(f"🤖 Resposta do bot:")
    print(result_2)
    print(f"📏 Tamanho: {len(result_2)} caracteres")
    
    # Validation checks
    if "Parte 2/2" in result_2:
        print("✅ CORRETO: Mostra Parte 2/2")
    else:
        print("❌ ERRO: Não mostra Parte 2/2")
        
    if "mais serviços" not in result_2:
        print("✅ CORRETO: Parte 2 não inclui 'mais serviços'")
    else:
        print("⚠️  AVISO: Parte 2 ainda inclui 'mais serviços'")
    
    # Test 3: Alternative phrases
    print("\n📋 TESTE 3: Frases alternativas ('restante', 'ver o resto')")
    print("-" * 50)
    
    user_message_3 = "quero ver o restante dos serviços"
    result_3 = await business_data_service.get_services_formatted_text(user_message_3)
    
    print(f"📨 Mensagem do usuário: {user_message_3}")
    print(f"🤖 Resposta do bot:")
    print(result_3[:200] + "..." if len(result_3) > 200 else result_3)
    
    if "Parte 2/2" in result_3:
        print("✅ CORRETO: 'restante' também detectado")
    else:
        print("❌ ERRO: 'restante' não foi detectado")
    
    # Test 4: Character limit validation
    print("\n📏 TESTE 4: Validação de limites de caracteres")
    print("-" * 50)
    
    print(f"Parte 1: {len(result_1)} chars (limite WhatsApp: 4096)")
    print(f"Parte 2: {len(result_2)} chars (limite WhatsApp: 4096)")
    
    if len(result_1) <= 4096:
        print("✅ Parte 1 dentro do limite")
    else:
        print("❌ ERRO: Parte 1 excede limite WhatsApp")
        
    if len(result_2) <= 4096:
        print("✅ Parte 2 dentro do limite")  
    else:
        print("❌ ERRO: Parte 2 excede limite WhatsApp")
    
    # Summary
    print("\n🎯 RESUMO DOS TESTES")
    print("=" * 60)
    
    total_services = len(await business_data_service.get_active_services())
    mid_point = total_services // 2
    
    print(f"📊 Total de serviços na database: {total_services}")
    print(f"📊 Divisão automática: {mid_point} + {total_services - mid_point} serviços")
    print(f"📨 Detecção funcionando: {'✅' if 'Parte 2/2' in result_2 else '❌'}")
    print(f"📏 Limites respeitados: {'✅' if len(result_1) <= 4096 and len(result_2) <= 4096 else '❌'}")

if __name__ == "__main__":
    print("🚀 Iniciando teste de divisão de serviços...")
    try:
        asyncio.run(test_service_splitting())
        print("\n✅ Teste concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        sys.exit(1)
