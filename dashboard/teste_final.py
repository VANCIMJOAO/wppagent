#!/usr/bin/env python3
import os
import sys

os.chdir('/home/vancim/whats_agent/dashboard')
sys.path.append('.')

print("🔧 TESTE APÓS CORREÇÃO DE IMPORTS")
print("=" * 40)

try:
    print("1. Testando import do layout...")
    from layout.conversas import create_conversas_layout
    print("✅ Layout importado com sucesso")
    
    print("2. Testando criação do layout...")
    layout = create_conversas_layout()
    print("✅ Layout criado com sucesso")
    
    print("3. Testando callbacks...")
    from callbacks.conversas_callbacks import register_all_conversas_callbacks
    print("✅ Callbacks importados com sucesso")
    
    print("\n🎉 TODAS AS CORREÇÕES FUNCIONANDO!")
    print("Execute: python app.py")
    
except Exception as e:
    print(f"❌ Erro: {e}")
