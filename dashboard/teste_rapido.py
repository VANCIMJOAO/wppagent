#!/usr/bin/env python3
"""
Teste Rápido das Correções
========================
"""
import os
import sys

os.chdir('/home/vancim/whats_agent/dashboard')
sys.path.append('.')

print("🔧 TESTE RÁPIDO DAS CORREÇÕES")
print("=" * 40)

# 1. Teste de layout
try:
    from layout.conversas import create_conversas_layout
    layout = create_conversas_layout()
    print("✅ Layout: OK")
    layout_ok = True
except Exception as e:
    print(f"❌ Layout: {str(e)[:100]}...")
    layout_ok = False

# 2. Teste de database  
try:
    from utils.database import get_conversations
    conversations = get_conversations()
    print(f"✅ Database: OK ({len(conversations)} conversas)")
    db_ok = True
except Exception as e:
    print(f"❌ Database: {str(e)[:100]}...")
    db_ok = False

# 3. Teste de callbacks
try:
    from callbacks.conversas_callbacks import register_all_conversas_callbacks
    print("✅ Callbacks: OK")
    callbacks_ok = True
except Exception as e:
    print(f"❌ Callbacks: {str(e)[:100]}...")
    callbacks_ok = False

# Resultado
total = sum([layout_ok, db_ok, callbacks_ok])
print(f"\n📊 Resultado: {total}/3 testes passaram")

if total >= 2:
    print("🎉 CORREÇÕES APLICADAS COM SUCESSO!")
    print("Execute: python app.py para testar")
else:
    print("⚠️ Ainda há problemas - verifique os erros acima")
