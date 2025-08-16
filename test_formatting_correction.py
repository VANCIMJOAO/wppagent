#!/usr/bin/env python3
"""
🔧 TESTE DE CORREÇÃO - Formatação WhatsApp
========================================
Testa se as correções de formatação funcionaram
"""

import asyncio
import sys
import os

# Adicionar path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.services.business_data import business_data_service
from app.utils.whatsapp_sanitizer import WhatsAppSanitizer

async def test_formatting_correction():
    """
    Testa a correção de formatação implementada
    """
    print("🔧 TESTE DE CORREÇÃO - Formatação WhatsApp")
    print("=" * 50)
    
    try:
        # 1. Testar formatação de serviços
        print("\n1️⃣ TESTANDO FORMATAÇÃO DE SERVIÇOS:")
        services_text = await business_data_service.get_services_formatted_text()
        
        print(f"📊 Texto gerado ({len(services_text)} chars):")
        print("=" * 40)
        print(services_text)
        print("=" * 40)
        
        # Analisar quebras de linha
        line_count = services_text.count('\n')
        double_breaks = services_text.count('\n\n')
        
        print(f"📈 Análise:")
        print(f"  • Quebras simples: {line_count}")
        print(f"  • Quebras duplas: {double_breaks}")
        print(f"  • Comprimento: {len(services_text)} chars")
        
        # 2. Testar sanitização
        print("\n2️⃣ TESTANDO SANITIZAÇÃO PRESERVADORA:")
        sanitized = WhatsAppSanitizer.sanitize_message_content(services_text, "text")
        
        print(f"📊 Texto sanitizado ({len(sanitized)} chars):")
        print("=" * 40)
        print(sanitized)
        print("=" * 40)
        
        # Comparar antes e depois
        original_lines = services_text.count('\n')
        sanitized_lines = sanitized.count('\n')
        
        print(f"📈 Comparação:")
        print(f"  • Original: {original_lines} quebras")
        print(f"  • Sanitizado: {sanitized_lines} quebras")
        print(f"  • Diferença: {original_lines - sanitized_lines}")
        
        # 3. Testar horários
        print("\n3️⃣ TESTANDO FORMATAÇÃO DE HORÁRIOS:")
        hours_text = await business_data_service.get_business_hours_formatted_text()
        
        print(f"📊 Horários ({len(hours_text)} chars):")
        print("=" * 40)
        print(hours_text)
        print("=" * 40)
        
        # 4. Validação final
        print("\n🎯 VALIDAÇÃO FINAL:")
        
        tests = [
            ("Serviços têm quebras adequadas", line_count >= 15),
            ("Sanitização preserva quebras", sanitized_lines >= (original_lines * 0.8)),
            ("Texto não está vazio", len(sanitized) > 100),
            ("Emojis preservados", "📋" in sanitized and "💰" in sanitized),
            ("Formatação preservada", "*" in sanitized and "_" in sanitized)
        ]
        
        passed = 0
        for test_name, result in tests:
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
            if result:
                passed += 1
        
        # Resultado final
        success_rate = (passed / len(tests)) * 100
        print(f"\n🏆 RESULTADO: {success_rate:.1f}% ({passed}/{len(tests)} testes aprovados)")
        
        if success_rate >= 80:
            print("🎉 CORREÇÃO FUNCIONOU! Formatação preservada com sucesso!")
        else:
            print("⚠️ Correção parcial. Verificar problemas restantes.")
            
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_formatting_correction())
