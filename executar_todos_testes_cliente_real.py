#!/usr/bin/env python3
"""
🚀 EXECUTOR COMPLETO - TODOS OS TESTES CLIENTE REAL
Executa todos os testes de cliente real em sequência
"""

import subprocess
import sys
import time
from datetime import datetime

def print_separator(title: str, char: str = "="):
    print(f"\n{char * 80}")
    print(f"🚀 {title}")
    print(f"{char * 80}")

def run_test(test_name: str, test_file: str) -> bool:
    """Executa um teste específico"""
    print_separator(f"EXECUTANDO: {test_name}")
    
    try:
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {test_name} - SUCESSO")
            print(f"📊 Output: {result.stdout[-200:]}...")  # Últimas 200 chars
            return True
        else:
            print(f"❌ {test_name} - FALHA")
            print(f"📊 Error: {result.stderr[-200:]}...")  # Últimas 200 chars
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {test_name} - ERRO: {str(e)}")
        return False

def main():
    """Executa todos os testes de cliente real"""
    print_separator("INICIANDO EXECUÇÃO COMPLETA DE TESTES")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("🎯 Executando todos os testes de cliente real em sequência...")
    
    # Lista de testes para executar
    tests = [
        ("Teste Cliente Real Completo", "tests/teste_cliente_real_completo.py"),
        ("Teste Meta Token Fix", "tests/teste_meta_token_fix.py"),
        ("Teste Cliente Real Autenticado", "tests/teste_cliente_real_autenticado.py")
    ]
    
    results = {}
    total_tests = len(tests)
    
    print_separator("EXECUTANDO TESTES")
    
    for i, (test_name, test_file) in enumerate(tests, 1):
        print(f"\n🔄 Teste {i}/{total_tests}: {test_name}")
        success = run_test(test_name, test_file)
        results[test_name] = success
        
        if i < total_tests:
            print("⏳ Aguardando 3 segundos antes do próximo teste...")
            time.sleep(3)
    
    # Relatório Final
    print_separator("RELATÓRIO FINAL - TODOS OS TESTES")
    
    passed_tests = sum(1 for success in results.values() if success)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"🔥 {'✅ TODOS OS TESTES CONCLUÍDOS!' if success_rate >= 80 else '⚠️ ALGUNS TESTES FALHARAM!'}")
    print(f"📈 Taxa de sucesso geral: {success_rate:.1f}%")
    print(f"✅ Testes passaram: {passed_tests}/{total_tests}")
    print(f"🕐 Conclusão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    print(f"\n📋 Resultados por Teste:")
    for test_name, success in results.items():
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"  {status} {test_name}")
    
    print(f"\n📁 Relatórios salvos em: temp_reports/")
    print(f"📄 Relatório consolidado: RELATORIO_TESTES_CLIENTE_REAL_FINAL.md")
    
    print_separator("EXECUÇÃO COMPLETA FINALIZADA")
    print("🎉 Todos os testes de cliente real foram executados!")
    print("✨ Sistema testado como cliente real completo!")
    
    return results

if __name__ == "__main__":
    main()
