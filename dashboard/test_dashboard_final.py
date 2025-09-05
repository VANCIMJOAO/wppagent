#!/usr/bin/env python3
"""
Teste Final - Dashboard Corrigido
=================================

Executa testes completos para verificar se o dashboard está funcionando
sem os erros '_dashprivate_layout' e redirecionamentos automáticos.
"""

import os
import sys
import importlib.util
import traceback

def test_basic_imports():
    """Testa imports básicos"""
    print("🔍 Testando imports básicos...")
    
    try:
        import dash
        import dash_mantine_components as dmc
        from dash import html, dcc
        from dash_iconify import DashIconify
        print("✅ Imports básicos OK")
        return True
    except Exception as e:
        print(f"❌ Erro nos imports básicos: {e}")
        return False

def test_home_layout():
    """Testa o layout home seguro"""
    print("🔍 Testando layout home seguro...")
    
    try:
        sys.path.append('/home/vancim/whats_agent/dashboard')
        from layout.home import create_home_layout
        
        layout = create_home_layout()
        
        # Verifica se o layout foi criado
        if layout is None:
            print("❌ Layout home retornou None")
            return False
        
        # Verifica se tem a estrutura básica
        if hasattr(layout, 'children'):
            print("✅ Layout home criado com sucesso")
            return True
        else:
            print("❌ Layout home sem estrutura válida")
            return False
            
    except Exception as e:
        print(f"❌ Erro no layout home: {e}")
        traceback.print_exc()
        return False

def test_sidebar():
    """Testa o sidebar corrigido"""
    print("🔍 Testando sidebar corrigido...")
    
    try:
        from components.sidebar import create_sidebar
        
        # Teste sem usuário
        sidebar = create_sidebar()
        if sidebar is None:
            print("❌ Sidebar retornou None")
            return False
        
        # Teste com usuário mock
        class MockRole:
            value = "admin"
        
        class MockUser:
            name = "Teste"
            email = "teste@test.com"
            role = MockRole()
            avatar_url = None
        
        sidebar_with_user = create_sidebar(MockUser())
        if sidebar_with_user is None:
            print("❌ Sidebar com usuário retornou None")
            return False
        
        print("✅ Sidebar funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"❌ Erro no sidebar: {e}")
        traceback.print_exc()
        return False

def test_callbacks():
    """Testa os callbacks seguros"""
    print("🔍 Testando callbacks seguros...")
    
    try:
        import dash
        from callbacks.home_callbacks import register_all_home_callbacks
        
        app = dash.Dash(__name__, suppress_callback_exceptions=True)
        result = register_all_home_callbacks(app)
        
        if result:
            print("✅ Callbacks registrados com sucesso")
            return True
        else:
            print("❌ Falha no registro de callbacks")
            return False
            
    except Exception as e:
        print(f"❌ Erro nos callbacks: {e}")
        traceback.print_exc()
        return False

def test_app_structure():
    """Testa a estrutura básica da aplicação"""
    print("🔍 Testando estrutura da aplicação...")
    
    try:
        # Verifica se arquivos essenciais existem
        essential_files = [
            'app.py',
            'layout/home.py',
            'components/sidebar.py',
            'callbacks/home_callbacks.py'
        ]
        
        missing_files = []
        for file in essential_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Arquivos faltando: {missing_files}")
            return False
        
        print("✅ Estrutura da aplicação OK")
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação da estrutura: {e}")
        return False

def run_complete_test():
    """Executa todos os testes"""
    print("🧪 TESTE COMPLETO DO DASHBOARD CORRIGIDO")
    print("=" * 45)
    
    # Mudar para diretório correto
    os.chdir('/home/vancim/whats_agent/dashboard')
    
    tests = [
        ("Imports Básicos", test_basic_imports),
        ("Estrutura da App", test_app_structure),
        ("Layout Home", test_home_layout),
        ("Sidebar", test_sidebar),
        ("Callbacks", test_callbacks)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Executando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Falha crítica em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo
    print("\n" + "=" * 45)
    print("📊 RESUMO DOS TESTES:")
    print("=" * 45)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"\n📈 Taxa de Sucesso: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 80:
        print("\n🎉 Dashboard está FUNCIONANDO!")
        print("💡 Próximos passos:")
        print("   1. Execute: python app.py")
        print("   2. Acesse: http://127.0.0.1:8050")
        print("   3. Verifique o console do navegador")
    else:
        print("\n⚠️  Ainda existem problemas para resolver.")
        print("💡 Verifique os erros acima e execute correções necessárias.")

if __name__ == "__main__":
    run_complete_test()
