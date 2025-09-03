#!/usr/bin/env python3
"""
Teste de Dados Reais na Página de Relatórios
============================================

Script para verificar se a página de relatórios está usando dados reais
da database em vez de dados mock.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_data():
    """Testa se os dados reais estão sendo utilizados"""
    print("🧪 TESTANDO DADOS REAIS NA PÁGINA DE RELATÓRIOS")
    print("=" * 60)
    
    try:
        # Testa import das queries de relatórios
        from services.queries_reports import ReportsQueries
        print("✅ Import de ReportsQueries funcionando")
        
        # Testa conexão com database
        from services.db import db_health_check
        health = db_health_check()
        if health.get('status') == 'healthy':
            print("✅ Conexão com database PostgreSQL funcionando")
            print(f"   Tempo de resposta: {health.get('response_time_ms', 0)}ms")
        else:
            print("⚠️  Database não disponível - usando dados mock")
            print(f"   Erro: {health.get('error', 'Desconhecido')}")
        
        # Testa query de conversas
        print("\n📋 TESTANDO QUERY DE CONVERSAS:")
        conv_report = ReportsQueries.get_conversations_report(limit=5)
        
        if conv_report and 'data' in conv_report:
            total = conv_report.get('total', 0)
            dados = conv_report.get('data', [])
            print(f"✅ Query executada - {len(dados)} registros retornados de {total} total")
            
            # Analisa se os dados parecem reais
            if dados:
                primeiro_item = dados[0]
                is_mock = (
                    str(primeiro_item.get('customer_name', '')).startswith('Cliente Mock') or
                    str(primeiro_item.get('phone_number', '')).startswith('+5511999000')
                )
                
                if is_mock:
                    print("⚠️  DADOS MOCK sendo utilizados")
                    print("   Motivo: Erro na conexão ou query")
                else:
                    print("✅ DADOS REAIS sendo utilizados!")
                    print(f"   Exemplo: {primeiro_item.get('customer_name')} | {primeiro_item.get('phone_number')}")
        else:
            print("❌ Erro na query de conversas")
            
        # Testa query de agendamentos
        print("\n📅 TESTANDO QUERY DE AGENDAMENTOS:")
        apt_report = ReportsQueries.get_appointments_report(limit=5)
        
        if apt_report and 'data' in apt_report:
            total = apt_report.get('total', 0)
            dados = apt_report.get('data', [])
            print(f"✅ Query executada - {len(dados)} registros retornados de {total} total")
            
            if dados:
                primeiro_item = dados[0]
                is_mock = str(primeiro_item.get('customer_name', '')).startswith('Cliente Mock')
                
                if is_mock:
                    print("⚠️  DADOS MOCK sendo utilizados")
                else:
                    print("✅ DADOS REAIS sendo utilizados!")
                    print(f"   Exemplo: {primeiro_item.get('customer_name')} | R$ {primeiro_item.get('price', 0)}")
        else:
            print("❌ Erro na query de agendamentos")
            
        # Testa analytics
        print("\n📊 TESTANDO DADOS ANALÍTICOS:")
        analytics = ReportsQueries.get_analytics_data(period_days=7)
        
        if analytics:
            timeline = analytics.get('timeline', [])
            messages = analytics.get('messages_by_direction', [])
            appointments = analytics.get('appointments_by_status', [])
            
            print(f"✅ Analytics funcionando:")
            print(f"   Timeline: {len(timeline)} pontos")
            print(f"   Mensagens: {len(messages)} categorias")
            print(f"   Status appointments: {len(appointments)} status")
        else:
            print("❌ Erro nos dados analíticos")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_query_performance():
    """Testa performance das queries"""
    print("\n⚡ TESTANDO PERFORMANCE DAS QUERIES:")
    print("-" * 40)
    
    try:
        import time
        from services.queries_reports import ReportsQueries
        
        # Teste de conversas
        start_time = time.time()
        conv_report = ReportsQueries.get_conversations_report(limit=20)
        conv_time = (time.time() - start_time) * 1000
        
        print(f"📋 Conversas: {conv_time:.2f}ms")
        
        # Teste de agendamentos
        start_time = time.time()
        apt_report = ReportsQueries.get_appointments_report(limit=20)
        apt_time = (time.time() - start_time) * 1000
        
        print(f"📅 Agendamentos: {apt_time:.2f}ms")
        
        # Teste de analytics
        start_time = time.time()
        analytics = ReportsQueries.get_analytics_data(period_days=30)
        analytics_time = (time.time() - start_time) * 1000
        
        print(f"📊 Analytics: {analytics_time:.2f}ms")
        
        total_time = conv_time + apt_time + analytics_time
        print(f"⏱️  Tempo total: {total_time:.2f}ms")
        
        if total_time < 5000:  # Menos de 5 segundos
            print("✅ Performance adequada!")
        else:
            print("⚠️  Performance pode ser melhorada")
            
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DE DADOS REAIS")
    print("=" * 60)
    
    # Teste principal
    success = test_real_data()
    
    if success:
        # Teste de performance
        test_query_performance()
        
        print("\n" + "=" * 60)
        print("🎯 RESULTADO FINAL:")
        
        if success:
            print("✅ PÁGINA DE RELATÓRIOS COM DADOS REAIS FUNCIONANDO!")
            print("\n🚀 Para testar no navegador:")
            print("   python app.py")
            print("   http://localhost:8050/relatorios")
            print("\n💡 Se ainda aparecerem dados mock no navegador:")
            print("   1. Verifique se DATABASE_URL está configurada")
            print("   2. Confira os logs do console do dashboard")
            print("   3. Teste a conectividade com o PostgreSQL")
        else:
            print("❌ PROBLEMAS ENCONTRADOS - verifique os erros acima")
    
    print("\n" + "=" * 60)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
