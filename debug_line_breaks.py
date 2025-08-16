#!/usr/bin/env python3
"""
🔬 DIAGNÓSTICO DETALHADO - Onde as quebras de linha são perdidas
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.utils.whatsapp_sanitizer import WhatsAppSanitizer

def test_line_breaks_step_by_step():
    """Testa cada etapa da sanitização para identificar onde as quebras são perdidas"""
    
    test_text = """📋 *Teste:*

1. *Item Um*
   💰 R$ 100,00
   ℹ️ _Descrição_

2. *Item Dois*
   💰 R$ 200,00"""
    
    print("🔬 DIAGNÓSTICO DETALHADO - Quebras de linha")
    print("=" * 50)
    print(f"✅ Texto original ({test_text.count(chr(10))} quebras):")
    print(repr(test_text))
    print()
    
    # Testar cada etapa da sanitização manualmente
    print("🔍 ETAPA 1: Validação de caracteres permitidos")
    safe_text_pattern = r'^[a-zA-Z0-9\s\u00C0-\u024F\u1E00-\u1EFF\U0001F000-\U0001F9FF\U00002000-\U000027BF\U0000FE00-\U0000FE0F.,!?:;\-_@#$%&*()\[\]{}="\'\/\\+\n\r\t•]{0,4096}$'
    
    if re.match(safe_text_pattern, test_text):
        print("✅ Texto passou na validação")
        step1_text = test_text
    else:
        print("❌ Texto falhou na validação, aplicando regex de limpeza")
        step1_text = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF\U0001F000-\U0001F9FF\U00002000-\U000027BF\U0000FE00-\U0000FE0F.,!?:;\-_@#$%&*()\[\]{}="\'\/\\+\n\r\t•]', '', test_text)
    
    print(f"📊 Após etapa 1 ({step1_text.count(chr(10))} quebras):")
    print(repr(step1_text))
    print()
    
    print("🔍 ETAPA 2: Normalização de espaços")
    step2_text = WhatsAppSanitizer._normalize_whitespace_preserve_formatting(step1_text)
    print(f"📊 Após etapa 2 ({step2_text.count(chr(10))} quebras):")
    print(repr(step2_text))
    print()
    
    print("🔍 ETAPA 3: Sanitização completa")
    final_text = WhatsAppSanitizer.sanitize_message_content(test_text, "text")
    print(f"📊 Resultado final ({final_text.count(chr(10))} quebras):")
    print(repr(final_text))
    print()
    
    # Análise do problema
    if final_text.count('\n') == 0:
        print("🚨 PROBLEMA IDENTIFICADO: Todas as quebras foram removidas!")
        
        # Testar se o problema está no padrão safe_text
        print("\n🔬 TESTE DO PADRÃO SAFE_TEXT:")
        simple_test = "Linha 1\nLinha 2"
        if re.match(safe_text_pattern, simple_test):
            print("✅ Padrão safe_text aceita quebras de linha")
        else:
            print("❌ Padrão safe_text rejeita quebras de linha!")
            
        # Testar manualmente o regex de limpeza
        print("\n🔬 TESTE DO REGEX DE LIMPEZA:")
        cleaned = re.sub(r'[^\w\s\u00C0-\u024F\u1E00-\u1EFF\U0001F000-\U0001F9FF\U00002000-\U000027BF\U0000FE00-\U0000FE0F.,!?:;\-_@#$%&*()\[\]{}="\'\/\\+\n\r\t•]', '', simple_test)
        print(f"Resultado: {repr(cleaned)}")
        
        if '\n' in cleaned:
            print("✅ Regex de limpeza preserva quebras")
        else:
            print("❌ Regex de limpeza remove quebras!")

if __name__ == "__main__":
    test_line_breaks_step_by_step()
