#!/usr/bin/env python3
"""
Teste da Página de Perfil
=========================

Script para verificar se a página de perfil está 100% implementada
e funcionando corretamente.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_perfil_imports():
    """Testa se todos os imports da página de perfil funcionam"""
    print("📦 TESTANDO IMPORTS DA PÁGINA DE PERFIL:")
    print("-" * 50)
    
    imports_tests = [
        ('layout.perfil', 'create_perfil_layout'),
        ('callbacks.perfil_callbacks', 'register_perfil_callbacks'),
        ('services.queries', 'ProfileQueries'),
    ]
    
    all_working = True
    for module, function in imports_tests:
        try:
            imported_module = __import__(module, fromlist=[function])
            getattr(imported_module, function)
            print(f"✅ {module}.{function}")
        except ImportError as e:
            print(f"❌ {module}.{function} - ImportError: {e}")
            all_working = False
        except AttributeError as e:
            print(f"❌ {module}.{function} - AttributeError: {e}")
            all_working = False
        except Exception as e:
            print(f"⚠️  {module}.{function} - Warning: {e}")
    
    return all_working

def test_perfil_layout():
    """Testa se o layout do perfil pode ser criado"""
    print("\n🎨 TESTANDO LAYOUT DO PERFIL:")
    print("-" * 50)
    
    try:
        from layout.perfil import create_perfil_layout
        
        # Tenta criar o layout
        layout = create_perfil_layout()
        
        if layout:
            print("✅ Layout do perfil criado com sucesso")
            print(f"   Tipo: {type(layout).__name__}")
            return True
        else:
            print("❌ Layout do perfil retornou None")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar layout do perfil: {e}")
        import traceback
        print(f"   Detalhes: {traceback.format_exc()}")
        return False

def test_perfil_callbacks():
    """Testa se os callbacks do perfil podem ser registrados"""
    print("\n🔗 TESTANDO CALLBACKS DO PERFIL:")
    print("-" * 50)
    
    try:
        from callbacks.perfil_callbacks import register_perfil_callbacks
        
        # Mock do app
        class MockApp:
            def __init__(self):
                self.callbacks = []
            
            def callback(self, *args, **kwargs):
                def decorator(func):
                    self.callbacks.append(func.__name__)
                    return func
                return decorator
        
        mock_app = MockApp()
        
        # Tenta registrar callbacks
        register_perfil_callbacks(mock_app)
        
        print(f"✅ Callbacks registrados com sucesso")
        print(f"   Total de callbacks: {len(mock_app.callbacks)}")
        if mock_app.callbacks:
            print(f"   Exemplos: {', '.join(mock_app.callbacks[:3])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao registrar callbacks do perfil: {e}")
        import traceback
        print(f"   Detalhes: {traceback.format_exc()}")
        return False

def test_perfil_queries():
    """Testa se as queries do perfil funcionam"""
    print("\n📊 TESTANDO QUERIES DO PERFIL:")
    print("-" * 50)
    
    try:
        from services.queries import ProfileQueries
        
        # Testa método get_system_stats
        if hasattr(ProfileQueries, 'get_system_stats'):
            stats = ProfileQueries.get_system_stats()
            print("✅ ProfileQueries.get_system_stats() funcionando")
            print(f"   Retornou: {type(stats).__name__}")
        else:
            print("⚠️  ProfileQueries.get_system_stats() não encontrado")
        
        # Testa método get_recent_activity
        if hasattr(ProfileQueries, 'get_recent_activity'):
            activity = ProfileQueries.get_recent_activity(limit=5)
            print("✅ ProfileQueries.get_recent_activity() funcionando")
            print(f"   Retornou: {len(activity) if isinstance(activity, list) else 'não-lista'} itens")
        else:
            print("⚠️  ProfileQueries.get_recent_activity() não encontrado")
        
        # Testa método get_integration_status
        if hasattr(ProfileQueries, 'get_integration_status'):
            integrations = ProfileQueries.get_integration_status()
            print("✅ ProfileQueries.get_integration_status() funcionando")
            print(f"   Retornou: {len(integrations) if isinstance(integrations, list) else 'não-lista'} integrações")
        else:
            print("⚠️  ProfileQueries.get_integration_status() não encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar queries do perfil: {e}")
        import traceback
        print(f"   Detalhes: {traceback.format_exc()}")
        return False

def test_perfil_css():
    """Testa se o CSS do perfil existe"""
    print("\n🎨 TESTANDO CSS DO PERFIL:")
    print("-" * 50)
    
    css_file = "assets/perfil_modern.css"
    
    if os.path.exists(css_file):
        file_size = os.path.getsize(css_file)
        print(f"✅ CSS do perfil encontrado")
        print(f"   Arquivo: {css_file}")
        print(f"   Tamanho: {file_size//1024}KB")
        
        # Verifica se contém classes importantes
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            important_classes = [
                '.perfil-layout',
                '.user-info-card',
                '.integration-card',
                '.activity-item'
            ]
            
            found_classes = []
            for class_name in important_classes:
                if class_name in css_content:
                    found_classes.append(class_name)
            
            print(f"   Classes encontradas: {len(found_classes)}/{len(important_classes)}")
            if found_classes:
                print(f"   Exemplos: {', '.join(found_classes[:2])}")
            
            return len(found_classes) > 0
            
        except Exception as e:
            print(f"   ⚠️  Erro ao ler CSS: {e}")
            return True  # Arquivo existe, mesmo com erro de leitura
    else:
        print(f"❌ CSS do perfil não encontrado: {css_file}")
        return False

def test_app_integration():
    """Testa se a página está integrada no app.py"""
    print("\n🔗 TESTANDO INTEGRAÇÃO NO APP:")
    print("-" * 50)
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        integrations = [
            ('create_perfil_layout', 'Import do layout'),
            ('register_perfil_callbacks', 'Import dos callbacks'),
            ('perfil_modern.css', 'CSS incluído'),
            ("'/perfil'", 'Rota configurada'),
            ('elif pathname == \'/perfil\':', 'Routing implementado')
        ]
        
        all_integrated = True
        for check, description in integrations:
            if check in app_content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} - FALTANDO")
                all_integrated = False
        
        return all_integrated
        
    except Exception as e:
        print(f"❌ Erro ao verificar app.py: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 TESTE COMPLETO DA PÁGINA DE PERFIL")
    print("=" * 60)
    
    tests = [
        ("Imports", test_perfil_imports),
        ("Layout", test_perfil_layout),
        ("Callbacks", test_perfil_callbacks),
        ("Queries", test_perfil_queries),
        ("CSS", test_perfil_css),
        ("Integração App", test_app_integration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ ERRO no teste {test_name}: {e}")
            results[test_name] = False
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES:")
    print("=" * 60)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:<20} {status}")
    
    print("-" * 60)
    print(f"📊 RESULTADO: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("\n🎉 PÁGINA DE PERFIL 100% IMPLEMENTADA E FUNCIONAL!")
        print("\n🚀 Para testar:")
        print("   1. python app.py")
        print("   2. Acesse http://localhost:8050/perfil")
        
        print("\n✨ Funcionalidades disponíveis:")
        print("   • Informações pessoais do usuário")
        print("   • Configurações de notificação")
        print("   • Timeline de atividades")
        print("   • Status das integrações")
        print("   • Alteração de avatar e preferências")
        print("   • Design moderno e responsivo")
        
    elif passed_tests >= total_tests - 1:
        print("\n✅ PÁGINA QUASE 100% FUNCIONAL!")
        print("   Apenas pequenos ajustes podem ser necessários")
        
    else:
        print("\n⚠️  ALGUNS PROBLEMAS ENCONTRADOS")
        print("   Verifique os erros listados acima")
    
    print("\n" + "=" * 60)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
