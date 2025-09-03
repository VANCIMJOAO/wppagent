#!/usr/bin/env python3
"""
Teste Fix Loop de Callbacks
===========================
"""
import os
import sys

os.chdir('/home/vancim/whats_agent/dashboard')
sys.path.append('.')

print("🔧 FIX APLICADO - LOOP DE CALLBACKS")
print("=" * 40)

print("✅ Correções aplicadas:")
print("   • Adicionado State para active-conversation-id")  
print("   • Verificação se conversa já está ativa")
print("   • Logs reduzidos para debug mais limpo")

print("\n🔍 Agora ao clicar em diferentes conversas deve ver:")
print("   Debug: Mudando para conversa ID 10")
print("   Debug: Cliente: Nome do Cliente")
print("   Debug: Chat criado para conversa 10")
print("   Debug: Conversa 10 já ativa - ignorando (se clicar novamente)")

print("\n🚀 Execute: python app.py")
print("📋 Teste clicando em diferentes conversas")
print("   Cada conversa diferente deve abrir apenas UMA vez")
print("   Clicar na mesma conversa deve ser ignorado")

print("\n✨ As conversas devem trocar corretamente agora!")
