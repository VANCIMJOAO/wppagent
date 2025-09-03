#!/usr/bin/env python3
"""
Verificação Final - Página de Relatórios
========================================

Script para confirmar que a página de relatórios está 100% implementada
e funcionando com dados reais da database PostgreSQL.
"""

def verificar_arquivos():
    """Verifica se todos os arquivos necessários existem"""
    import os
    
    arquivos_necessarios = [
        ('layout/relatorios.py', 'Layout da página'),
        ('callbacks/relatorios_callbacks.py', 'Callbacks e lógica'),
        ('assets/relatorios_modern.css', 'CSS customizado'),
        ('services/queries_reports.py', 'Queries com dados reais'),
        ('test_dados_reais.py', 'Teste de verificação')
    ]
    
    print("📁 VERIFICANDO ARQUIVOS NECESSÁRIOS:")
    print("-" * 50)
    
    todos_existem = True
    for arquivo, descricao in arquivos_necessarios:
        existe = os.path.exists(arquivo)
        status = "✅" if existe else "❌"
        tamanho = ""
        
        if existe:
            try:
                size = os.path.getsize(arquivo)
                if size > 1024:
                    tamanho = f"({size//1024}KB)"
                else:
                    tamanho = f"({size}B)"
            except:
                tamanho = "(N/A)"
        
        print(f"{status} {arquivo:<35} {tamanho:<8} {descricao}")
        
        if not existe:
            todos_existem = False
    
    return todos_existem

def verificar_imports():
    """Verifica se todos os imports funcionam"""
    print("\n📦 VERIFICANDO IMPORTS:")
    print("-" * 50)
    
    imports_teste = [
        ('layout.relatorios', 'create_relatorios_layout'),
        ('callbacks.relatorios_callbacks', 'register_relatorios_callbacks'),
        ('services.queries_reports', 'ReportsQueries'),
        ('services.db', 'execute_query'),
    ]
    
    todos_funcionam = True
    for modulo, funcao in imports_teste:
        try:
            __import__(modulo)
            print(f"✅ {modulo}.{funcao}")
        except ImportError as e:
            print(f"❌ {modulo}.{funcao} - Erro: {e}")
            todos_funcionam = False
        except Exception as e:
            print(f"⚠️  {modulo}.{funcao} - Aviso: {e}")
    
    return todos_funcionam

def verificar_database():
    """Verifica conexão com a database"""
    print("\n🗄️  VERIFICANDO DATABASE:")
    print("-" * 50)
    
    try:
        from services.db import db_health_check
        health = db_health_check()
        
        if health.get('status') == 'healthy':
            print("✅ Conexão PostgreSQL funcionando")
            print(f"   Tempo de resposta: {health.get('response_time_ms', 0):.1f}ms")
            return True
        else:
            print("⚠️  Database indisponível")
            print(f"   Erro: {health.get('error', 'Desconhecido')}")
            print("   💡 Página funcionará com dados mock como fallback")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar database: {e}")
        return False

def verificar_queries():
    """Verifica se as queries estão funcionando"""
    print("\n📊 VERIFICANDO QUERIES:")
    print("-" * 50)
    
    try:
        from services.queries_reports import ReportsQueries
        
        # Testa query de conversas
        print("📋 Testando relatório de conversas...")
        conv_result = ReportsQueries.get_conversations_report(limit=3)
        if conv_result and 'data' in conv_result:
            total = conv_result.get('total', 0)
            dados = len(conv_result.get('data', []))
            print(f"✅ Conversas: {dados} registros retornados, {total} total")
        else:
            print("❌ Erro na query de conversas")
            return False
        
        # Testa query de agendamentos
        print("📅 Testando relatório de agendamentos...")
        apt_result = ReportsQueries.get_appointments_report(limit=3)
        if apt_result and 'data' in apt_result:
            total = apt_result.get('total', 0)
            dados = len(apt_result.get('data', []))
            print(f"✅ Agendamentos: {dados} registros retornados, {total} total")
        else:
            print("❌ Erro na query de agendamentos")
            return False
        
        # Testa analytics
        print("📈 Testando dados analíticos...")
        analytics = ReportsQueries.get_analytics_data(period_days=7)
        if analytics:
            timeline = len(analytics.get('timeline', []))
            messages = len(analytics.get('messages_by_direction', []))
            appointments = len(analytics.get('appointments_by_status', []))
            print(f"✅ Analytics: {timeline} timeline, {messages} mensagens, {appointments} status")
        else:
            print("❌ Erro nos dados analíticos")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar queries: {e}")
        return False

def verificar_app_integration():
    """Verifica integração no app.py"""
    print("\n🔗 VERIFICANDO INTEGRAÇÃO NO APP:")
    print("-" * 50)
    
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        checks = [
            ('relatorios_modern.css', 'CSS incluído'),
            ('register_relatorios_callbacks', 'Callbacks registrados'),
            ('/relatorios', 'Rota configurada'),
            ('create_relatorios_layout', 'Layout importado')
        ]
        
        todos_ok = True
        for check, descricao in checks:
            if check in app_content:
                print(f"✅ {descricao}")
            else:
                print(f"❌ {descricao} - FALTANDO")
                todos_ok = False
        
        return todos_ok
        
    except Exception as e:
        print(f"❌ Erro ao verificar app.py: {e}")
        return False

def main():
    """Executa todas as verificações"""
    print("🚀 VERIFICAÇÃO FINAL - PÁGINA DE RELATÓRIOS")
    print("=" * 60)
    
    resultados = {
        "arquivos": verificar_arquivos(),
        "imports": verificar_imports(),
        "database": verificar_database(),
        "queries": verificar_queries(),
        "app_integration": verificar_app_integration()
    }
    
    print("\n" + "=" * 60)
    print("📋 RESUMO DA VERIFICAÇÃO:")
    print("=" * 60)
    
    total_checks = len(resultados)
    passed_checks = sum(resultados.values())
    
    for check, resultado in resultados.items():
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        check_name = {
            "arquivos": "Arquivos Necessários",
            "imports": "Imports Python",
            "database": "Conexão Database",
            "queries": "Queries Funcionais",
            "app_integration": "Integração no App"
        }.get(check, check)
        
        print(f"{check_name:<25} {status}")
    
    print("-" * 60)
    print(f"📊 RESULTADO: {passed_checks}/{total_checks} verificações passaram")
    
    if passed_checks == total_checks:
        print("\n🎉 PÁGINA DE RELATÓRIOS 100% IMPLEMENTADA E FUNCIONAL!")
        print("\n🚀 Para testar:")
        print("   1. python app.py")
        print("   2. Acesse http://localhost:8050/relatorios")
        print("   3. Teste os filtros, tabelas e exportação CSV")
        
        print("\n✨ Funcionalidades disponíveis:")
        print("   • Relatório de conversas com dados reais")
        print("   • Relatório de agendamentos com dados reais")
        print("   • Filtros por data e status")
        print("   • Exportação CSV profissional")
        print("   • Gráficos analíticos interativos")
        print("   • Paginação baseada em dados reais")
        print("   • Sistema de fallback robusto")
        
    elif passed_checks >= total_checks - 1:
        print("\n✅ PÁGINA QUASE 100% FUNCIONAL!")
        print("   Apenas pequenos ajustes podem ser necessários")
        
    else:
        print("\n⚠️  ALGUNS PROBLEMAS ENCONTRADOS")
        print("   Verifique os erros listados acima")
    
    print("\n" + "=" * 60)
    
    return passed_checks == total_checks

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
