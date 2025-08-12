#!/usr/bin/env python3
"""
Validador do Sistema de Logging
===============================

Valida a configuração e funcionamento do sistema de logging estruturado.
Testa diferentes níveis, formatos e funcionalidades.
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# Adicionar o diretório app ao Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.logger import (
    init_logging, 
    get_logger, 
    get_performance_timer,
    LogLevel,
    RequestContext,
    log_performance,
    log_function_call
)
from app.config.config_factory import ConfigFactory


def test_basic_logging():
    """Testar logging básico em todos os níveis"""
    logger = get_logger("test_basic")
    
    logger.debug("Mensagem de debug - detalhes técnicos")
    logger.info("Mensagem de info - operação normal")
    logger.warning("Mensagem de warning - algo pode estar errado")
    logger.error("Mensagem de error - erro detectado")
    logger.critical("Mensagem critical - falha grave do sistema")
    
    return True


def test_structured_logging():
    """Testar logging estruturado com dados extras"""
    logger = get_logger("test_structured")
    
    extra_data = {
        "user_id": "user_123",
        "operation": "test_operation",
        "duration_ms": 150.5,
        "success": True
    }
    
    logger.info("Operação realizada com sucesso", extra_data)
    logger.error("Falha na operação", {
        "error_code": "E001",
        "user_id": "user_456",
        "retry_count": 3
    })
    
    return True


def test_performance_logging():
    """Testar logging de performance"""
    logger = get_logger("test_performance")
    
    # Teste com context manager
    with get_performance_timer("operacao_teste"):
        time.sleep(0.1)  # Simula operação
    
    # Teste manual
    logger.performance("operacao_manual", 250.7, {
        "cache_hit": True,
        "db_queries": 3
    })
    
    return True


def test_context_logging():
    """Testar logging com contexto de requisição"""
    logger = get_logger("test_context")
    
    # Teste sem contexto
    logger.info("Mensagem sem contexto")
    
    # Teste com contexto
    with RequestContext(
        request_id="req_12345",
        user_id="user_789",
        session_id="sess_abc"
    ):
        logger.info("Mensagem com contexto completo")
        logger.warning("Warning com contexto")
    
    return True


def test_exception_logging():
    """Testar logging de exceções"""
    logger = get_logger("test_exception")
    
    try:
        # Forçar uma exceção
        1 / 0
    except Exception as e:
        logger.exception("Erro capturado com traceback automático")
        logger.error("Erro sem traceback", {"error": str(e)})
    
    return True


@log_performance("decorador_performance")
def test_function_with_performance():
    """Função decorada para teste de performance"""
    time.sleep(0.05)
    return "resultado_teste"


@log_function_call(include_args=True, include_result=True)
def test_function_with_logging(param1: str, param2: int = 42):
    """Função decorada para teste de logging"""
    return f"processado: {param1} - {param2}"


def test_decorators():
    """Testar decorators de logging"""
    logger = get_logger("test_decorators")
    
    logger.info("Testando decorator de performance")
    result1 = test_function_with_performance()
    
    logger.info("Testando decorator de function call")
    result2 = test_function_with_logging("teste", 100)
    
    return True


def test_log_file_creation():
    """Testar criação de arquivos de log"""
    config = ConfigFactory.get_singleton_config()
    log_dir = Path(config.log_dir)
    
    expected_files = ["app.log", "error.log"]
    
    if config.log_business:
        expected_files.append("business.log")
    
    if config.log_performance:
        expected_files.append("performance.log")
    
    existing_files = []
    missing_files = []
    
    for file_name in expected_files:
        file_path = log_dir / file_name
        if file_path.exists():
            existing_files.append(file_name)
        else:
            missing_files.append(file_name)
    
    return {
        "existing": existing_files,
        "missing": missing_files,
        "all_exist": len(missing_files) == 0
    }


def test_configuration_loading():
    """Testar carregamento de configuração"""
    config = ConfigFactory.get_singleton_config()
    
    config_info = {
        "environment": config.environment.value,
        "log_level": config.log_level,
        "log_format": config.log_format,
        "log_dir": config.log_dir,
        "log_performance": config.log_performance,
        "log_business": config.log_business,
        "log_third_party_level": config.log_third_party_level,
    }
    
    return config_info


def run_comprehensive_test():
    """Executar suite completa de testes"""
    print("🚀 Iniciando Validação do Sistema de Logging")
    print("=" * 60)
    
    # Inicializar sistema de logging
    init_logging()
    
    tests = [
        ("Configuração", test_configuration_loading),
        ("Logging Básico", test_basic_logging),
        ("Logging Estruturado", test_structured_logging),
        ("Performance Logging", test_performance_logging),
        ("Context Logging", test_context_logging),
        ("Exception Logging", test_exception_logging),
        ("Decorators", test_decorators),
        ("Arquivos de Log", test_log_file_creation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Executando: {test_name}")
        try:
            result = test_func()
            results[test_name] = {"status": "✅ PASS", "result": result}
            print(f"   ✅ {test_name}: OK")
            
            if isinstance(result, dict) and "all_exist" in result:
                if result["all_exist"]:
                    print(f"   📁 Arquivos: {', '.join(result['existing'])}")
                else:
                    print(f"   📁 Existentes: {', '.join(result['existing'])}")
                    print(f"   ❌ Faltando: {', '.join(result['missing'])}")
            
            elif isinstance(result, dict) and "environment" in result:
                print(f"   🌍 Ambiente: {result['environment']}")
                print(f"   📊 Nível: {result['log_level']}")
                print(f"   📝 Formato: {result['log_format']}")
                
        except Exception as e:
            results[test_name] = {"status": "❌ FAIL", "error": str(e)}
            print(f"   ❌ {test_name}: FALHA - {e}")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE VALIDAÇÃO DO LOGGING")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if "✅" in r["status"])
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"📈 Taxa de sucesso: {success_rate:.1f}% ({passed}/{total})")
    print(f"🌍 Ambiente atual: {ConfigFactory.get_singleton_config().environment.value}")
    
    print("\n📋 Detalhes dos testes:")
    for test_name, result in results.items():
        status = result["status"]
        print(f"   {status} {test_name}")
        if "error" in result:
            print(f"      Erro: {result['error']}")
    
    # Recomendações
    print("\n💡 RECOMENDAÇÕES:")
    
    config = ConfigFactory.get_singleton_config()
    if config.environment.value == "development":
        print("   🔧 Ambiente de desenvolvimento detectado")
        print("   📝 Logs em formato plain para melhor legibilidade")
        print("   🐛 Debug logging habilitado")
    elif config.environment.value == "production":
        print("   🏭 Ambiente de produção detectado")
        print("   📊 Logs em formato JSON para análise automatizada")
        print("   ⚡ Performance logging desabilitado para melhor performance")
    
    if config.log_format == "json":
        print("   📊 Use ferramentas como jq, ELK stack ou Grafana para análise")
    
    print("   📁 Verifique regularmente o tamanho dos arquivos de log")
    print("   🔄 Configure logrotate para rotação automática")
    
    print(f"\n{'🎉 SISTEMA DE LOGGING VALIDADO COM SUCESSO!' if success_rate == 100 else '⚠️ ALGUMAS VALIDAÇÕES FALHARAM'}")
    
    return success_rate == 100


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
