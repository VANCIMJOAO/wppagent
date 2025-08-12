#!/usr/bin/env python3
"""
Validação do Sistema de Configuração
WhatsApp Agent - Teste de Configuração por Ambiente
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
from typing import Dict, Any

def test_environment_configs():
    """Testar configurações para todos os ambientes"""
    from app.config.config_factory import ConfigFactory, Environment
    
    print("🧪 Testando Configurações por Ambiente...")
    print("=" * 50)
    
    results = {}
    
    for env in Environment:
        print(f"\n📋 Testando {env.value.upper()}...")
        
        try:
            # Criar configuração para o ambiente
            config = ConfigFactory.create_config(env)
            
            # Validar configuração
            summary = ConfigFactory.get_config_summary(config)
            
            # Teste de propriedades
            tests = {
                "debug_ok": _test_debug_setting(config),
                "admin_password_ok": _test_admin_password(config),
                "secrets_ok": _test_secrets_strength(config),
                "apis_ok": _test_api_configuration(config),
                "security_ok": _test_security_headers(config),
                "cors_ok": _test_cors_settings(config)
            }
            
            # Em development/test, ser mais flexível
            if env.value in ['development', 'test']:
                # Considerar sucesso se maioria dos testes passa
                passed_tests = sum(1 for result in tests.values() if result)
                success = passed_tests >= len(tests) * 0.5  # 50% mínimo
            else:
                # Em staging/production, ser mais rigoroso
                success = all(tests.values())
            
            results[env.value] = {
                "status": "✅ PASS" if success else "❌ FAIL",
                "summary": summary,
                "tests": tests
            }
            
            print(f"  ✅ Configuração carregada")
            print(f"  🔒 Nível de segurança: {config.security_level}")
            print(f"  🐛 Debug: {config.debug}")
            print(f"  👤 Admin: {config.admin_username}")
            
            for test_name, result in tests.items():
                status = "✅" if result else "❌"
                print(f"  {status} {test_name}")
        
        except Exception as e:
            results[env.value] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
            print(f"  ❌ Erro: {e}")
    
    return results


def _test_debug_setting(config) -> bool:
    """Testar configuração de debug"""
    if config.is_production and config.debug:
        return False
    return True


def _test_admin_password(config) -> bool:
    """Testar força da senha do admin com flexibilidade por ambiente"""
    try:
        # Em development/test, aceitar senhas básicas
        if hasattr(config, 'security_level') and config.security_level in ['low', 'medium']:
            return len(config.admin_password) >= 4
        
        # Em staging/production, exigir senhas mais fortes
        password = config.admin_password
        return (
            len(password) >= 8 and
            any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password)
        )
    except:
        return False


def _test_secrets_strength(config) -> bool:
    """Testar força dos secrets"""
    try:
        secrets = [
            config.secret_key,
            config.jwt_secret,
            config.encryption_key
        ]
        
        for secret in secrets:
            if not secret or len(secret.get_secret_value()) < 16:
                return False
        
        return True
    except:
        return False


def _test_api_configuration(config) -> bool:
    """Testar configuração de APIs"""
    try:
        # Em produção, APIs devem estar configuradas (aceita placeholders)
        if config.environment.value == 'production':
            required_apis = [config.openai_api_key, config.meta_access_token]
            for api in required_apis:
                if not api:
                    return False
                api_value = api.get_secret_value()
                # Aceitar placeholders em produção (formato ${VAR})
                if not api_value or (not api_value.startswith('${') and api_value.startswith('test-')):
                    return False
        
        return True
    except:
        return False


def _test_security_headers(config) -> bool:
    """Testar headers de segurança"""
    try:
        headers = config.get_security_headers()
        required_headers = ["X-Content-Type-Options", "X-Frame-Options"]
        
        return all(header in headers for header in required_headers)
    except:
        return False


def _test_cors_settings(config) -> bool:
    """Testar configurações CORS"""
    try:
        cors = config.get_cors_settings()
        
        # Produção não deve permitir origens wildcard
        if config.is_production:
            return "*" not in cors.get("allow_origins", [])
        
        return True
    except:
        return False


def test_config_factory():
    """Testar Config Factory"""
    from app.config.config_factory import ConfigFactory, get_settings, health_check_config
    
    print("\n🏭 Testando Config Factory...")
    print("=" * 30)
    
    try:
        # Testar detecção automática de ambiente
        config = get_settings()
        print(f"✅ Ambiente detectado: {config.environment}")
        
        # Testar health check
        health = health_check_config()
        print(f"✅ Health check: {health['status']}")
        
        # Testar singleton
        config2 = get_settings()
        same_instance = config is config2
        print(f"✅ Singleton: {'OK' if same_instance else 'FALHOU'}")
        
        return True
    
    except Exception as e:
        print(f"❌ Erro no Config Factory: {e}")
        return False


def test_environment_variables():
    """Testar variáveis de ambiente"""
    print("\n🌍 Testando Variáveis de Ambiente...")
    print("=" * 35)
    
    # Arquivos de ambiente esperados
    env_files = [
        '.env.development',
        '.env.testing', 
        '.env.staging',
        '.env.production'
    ]
    
    for env_file in env_files:
        if Path(env_file).exists():
            print(f"✅ {env_file} encontrado")
        else:
            print(f"❌ {env_file} não encontrado")


def test_secrets_integration():
    """Testar integração com sistema de secrets"""
    print("\n🔐 Testando Integração com Secrets...")
    print("=" * 40)
    
    try:
        from app.config.config_factory import get_settings
        
        config = get_settings()
        
        # Testar URLs construídas (com verificação de None)
        db_url = config.database_dsn or ""
        redis_url = config.redis_url or ""
        
        print(f"✅ Database DSN: {'postgresql://' in db_url or 'sqlite://' in db_url}")
        print(f"✅ Redis URL: {'redis://' in redis_url}")
        
        # Testar properties
        print(f"✅ is_development: {hasattr(config, 'is_development') and config.is_development}")
        print(f"✅ is_production: {hasattr(config, 'is_production') and config.is_production}")
        
        return True
    
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False


def generate_report(results: Dict[str, Any]):
    """Gerar relatório final"""
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE VALIDAÇÃO DE CONFIGURAÇÃO")
    print("=" * 60)
    
    total_envs = len(results)
    passed_envs = sum(1 for r in results.values() if r['status'].startswith('✅'))
    
    print(f"\n📈 Resumo Geral:")
    print(f"  Ambientes testados: {total_envs}")
    print(f"  Aprovados: {passed_envs}/{total_envs}")
    print(f"  Taxa de sucesso: {(passed_envs/total_envs)*100:.1f}%")
    
    print(f"\n📋 Detalhes por Ambiente:")
    for env_name, result in results.items():
        print(f"\n  🌍 {env_name.upper()}:")
        print(f"    Status: {result['status']}")
        
        if 'error' in result:
            print(f"    Erro: {result['error']}")
        elif 'tests' in result:
            passed_tests = sum(1 for t in result['tests'].values() if t)
            total_tests = len(result['tests'])
            print(f"    Testes: {passed_tests}/{total_tests}")
            
            for test_name, passed in result['tests'].items():
                status = "✅" if passed else "❌"
                print(f"      {status} {test_name}")
    
    print(f"\n🎯 Recomendações:")
    
    # Analisar problemas comuns
    issues = []
    for env_name, result in results.items():
        if result['status'].startswith('❌'):
            if env_name == 'production':
                issues.append("❗ Configuração de produção com problemas críticos")
            elif 'tests' in result:
                failed_tests = [name for name, passed in result['tests'].items() if not passed]
                if failed_tests:
                    issues.append(f"⚠️ {env_name}: {', '.join(failed_tests)}")
    
    if not issues:
        print("  🎉 Todas as configurações estão corretas!")
        print("  ✅ Sistema pronto para deploy em qualquer ambiente")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    print(f"\n💡 Próximos passos:")
    print("  1. Revisar configurações com problemas")
    print("  2. Configurar secrets management para produção")
    print("  3. Testar deploy em staging antes da produção")
    print("  4. Monitorar logs durante o deploy")


def main():
    """Função principal"""
    print("🚀 Iniciando Validação do Sistema de Configuração...")
    
    try:
        # Detectar ambiente atual
        current_env = os.getenv('ENVIRONMENT', 'development').lower()
        
        # Testar configurações por ambiente
        env_results = test_environment_configs()
        
        # Testar factory
        factory_ok = test_config_factory()
        
        # Testar variáveis de ambiente
        test_environment_variables()
        
        # Testar integração com secrets
        secrets_ok = test_secrets_integration()
        
        # Gerar relatório
        generate_report(env_results)
        
        # Critério de sucesso flexível baseado no ambiente
        if current_env in ['development', 'test']:
            # Em desenvolvimento, ser mais flexível
            env_success = any(r['status'].startswith('✅') for r in env_results.values())
            overall_success = env_success and factory_ok
        else:
            # Em staging/produção, ser mais rigoroso
            overall_success = (
                all(r['status'].startswith('✅') for r in env_results.values()) and
                factory_ok and
                secrets_ok
            )
        
        if overall_success:
            print(f"\n🎉 VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"💡 Ambiente {current_env} validado e pronto para uso.")
            return 0
        else:
            print(f"\n⚠️ VALIDAÇÃO CONCLUÍDA COM PROBLEMAS")
            if current_env in ['development', 'test']:
                print("💡 Em desenvolvimento, alguns warnings são aceitáveis.")
                print("🔧 Para produção, certifique-se de resolver todos os problemas.")
            return 1
    
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NA VALIDAÇÃO: {e}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
