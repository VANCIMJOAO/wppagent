#!/usr/bin/env python3
"""
🔬 DIAGNÓSTICO ULTRA DETALHADO - Rastreando cada função
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.utils.whatsapp_sanitizer import WhatsAppSanitizer

def test_each_function_individually():
    """Testa cada função da sanitização individualmente"""
    
    test_text = """📋 *Teste:*

1. *Item Um*
   💰 R$ 100,00"""
    
    print("🔬 DIAGNÓSTICO ULTRA DETALHADO")
    print("=" * 50)
    print(f"✅ Texto original ({test_text.count(chr(10))} quebras):")
    print(repr(test_text))
    print()
    
    # Teste 1: _remove_dangerous_content
    print("🔍 TESTE 1: _remove_dangerous_content")
    step1 = WhatsAppSanitizer._remove_dangerous_content(test_text)
    print(f"📊 Resultado ({step1.count(chr(10))} quebras):")
    print(repr(step1))
    print()
    
    # Teste 2: _sanitize_text_message
    print("🔍 TESTE 2: _sanitize_text_message")
    step2 = WhatsAppSanitizer._sanitize_text_message(step1)
    print(f"📊 Resultado ({step2.count(chr(10))} quebras):")
    print(repr(step2))
    print()
    
    # Teste 3: _normalize_whitespace_preserve_formatting
    print("🔍 TESTE 3: _normalize_whitespace_preserve_formatting")
    step3 = WhatsAppSanitizer._normalize_whitespace_preserve_formatting(step2)
    print(f"📊 Resultado ({step3.count(chr(10))} quebras):")
    print(repr(step3))
    print()
    
    # Teste COMPLETO
    print("🔍 TESTE COMPLETO: sanitize_message_content")
    final = WhatsAppSanitizer.sanitize_message_content(test_text, "text")
    print(f"📊 Resultado final ({final.count(chr(10))} quebras):")
    print(repr(final))
    print()
    
    # Análise detalhada
    if step1.count('\n') != test_text.count('\n'):
        print("🚨 PROBLEMA EM: _remove_dangerous_content")
    elif step2.count('\n') != step1.count('\n'):
        print("🚨 PROBLEMA EM: _sanitize_text_message")  
    elif step3.count('\n') != step2.count('\n'):
        print("🚨 PROBLEMA EM: _normalize_whitespace_preserve_formatting")
    elif final.count('\n') != step3.count('\n'):
        print("🚨 PROBLEMA EM: sanitize_message_content (lógica geral)")
    else:
        print("✅ Todas as funções preservam quebras individualmente")
        print("❓ Problema pode estar na chamada ou em outra função")

if __name__ == "__main__":
    test_each_function_individually()
