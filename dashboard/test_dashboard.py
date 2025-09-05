#!/usr/bin/env python3
"""
Teste Rápido do Dashboard - Verificação de Erros
==============================================

Testa se o dashboard pode ser importado e inicializado sem erros.
"""

import sys
import os
import importlib

def test_imports():
    """Testa importações básicas"""
    print("🔍 Testando importações básicas...")
    
    try:
        import dash
        import dash_mantine_components as dmc
        from dash import html
        from dash_iconify import DashIconify
        print("✅ Imports básicos OK")
        return True
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False

def test_sidebar_import():
    """Testa importação do sidebar"""
    print("🔍 Testando importação do sidebar...")
    
    try:
        sys.path.append('/home/vancim/whats_agent/dashboard')
        from components.sidebar import create_sidebar, register_sidebar_callbacks
        print("✅ Sidebar importado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar sidebar: {e}")
        return False

def test_sidebar_creation():
    """Testa criação do sidebar"""
    print("🔍 Testando criação do sidebar...")
    
    try:
        from components.sidebar import create_sidebar
        
        # Teste sem user
        sidebar1 = create_sidebar()
        print("✅ Sidebar criado sem user")
        
        # Teste com user mock
        class MockRole:
            value = "admin"
        
        class MockUser:
            name = "Teste"
            email = "teste@test.com"
            role = MockRole()
            avatar_url = None
        
        sidebar2 = create_sidebar(MockUser())
        print("✅ Sidebar criado com user mock")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar sidebar: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_home_layout():
    """Testa layout home"""
    print("🔍 Testando layout home...")
    
    try:
        from layout.home import create_home_layout
        layout = create_home_layout()
        print("✅ Layout home criado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro no layout home: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Teste principal"""
    print("🧪 TESTE RÁPIDO DO DASHBOARD")
    print("=" * 40)
    
    # Mudar para diretório correto
    os.chdir('/home/vancim/whats_agent/dashboard')
    
    tests = [
        test_imports,
        test_sidebar_import,
        test_sidebar_creation,
        test_home_layout
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("📊 RESULTADOS:")
    print(f"   Testes passaram: {passed}/{total}")
    print(f"   Taxa de sucesso: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 Todos os testes passaram! Dashboard deve funcionar.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.")

if __name__ == "__main__":
    main()
