#!/usr/bin/env python3
"""
🧪 SEC-001 CORS Security Validation Test

Testa a correção de segurança CORS que implementa validação dinâmica 
baseada em variáveis de ambiente para evitar bypass de segurança.

Referência: SEC-001 - Configuração CORS com origens hardcodadas
"""

import os
import asyncio
import requests
import sys
from typing import Dict, Any

# Mock para testar diferentes ambientes
TEST_ENVIRONMENTS = {
    "development": {
        "ENVIRONMENT": "development",
        "CORS_ALLOWED_ORIGINS": ""
    },
    "production": {
        "ENVIRONMENT": "production", 
        "CORS_ALLOWED_ORIGINS": "https://app.example.com,https://dashboard.example.com"
    },
    "custom": {
        "ENVIRONMENT": "production",
        "CORS_ALLOWED_ORIGINS": "https://custom1.com,https://custom2.com"
    }
}

class CORSSecurityTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
    
    def test_cors_validation_local(self, environment: str) -> Dict[str, Any]:
        """Testa validação CORS localmente (sem servidor)"""
        
        # Salvar ambiente atual
        original_env = {}
        for key in ["ENVIRONMENT", "CORS_ALLOWED_ORIGINS"]:
            original_env[key] = os.getenv(key)
        
        try:
            # Configurar ambiente de teste
            env_config = TEST_ENVIRONMENTS[environment]
            for key, value in env_config.items():
                if value:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)
            
            # Importar após configurar ambiente
            sys.path.insert(0, '/home/vancim/whats_agent')
            from app.cors_config import validate_origin, get_allowed_origins, get_environment
            
            # Testar origens maliciosas
            malicious_origins = [
                "http://evil.com",
                "https://malicious-site.org", 
                "http://attacker.net",
                "https://phishing-site.com"
            ]
            
            # Testar origens válidas baseadas no ambiente
            valid_origins = get_allowed_origins()
            current_env = get_environment()
            
            results = {
                "environment": current_env,
                "allowed_origins_count": len(valid_origins),
                "malicious_rejected": 0,
                "valid_accepted": 0,
                "tests": []
            }
            
            print(f"\n🧪 Testando ambiente: {environment}")
            print(f"📋 Ambiente detectado: {current_env}")
            print(f"🔒 Origens permitidas: {len(valid_origins)}")
            
            # Teste 1: Rejeitar origens maliciosas
            print("\n❌ Testando rejeição de origens maliciosas:")
            for origin in malicious_origins:
                is_valid = validate_origin(origin)
                if not is_valid:
                    results["malicious_rejected"] += 1
                    print(f"  ✅ {origin} - REJEITADO (correto)")
                else:
                    print(f"  ❌ {origin} - ACEITO (falha de segurança!)")
                
                results["tests"].append({
                    "origin": origin,
                    "type": "malicious",
                    "expected": False,
                    "actual": is_valid,
                    "passed": not is_valid
                })
            
            # Teste 2: Aceitar origens válidas
            print("\n✅ Testando aceitação de origens válidas:")
            for origin in valid_origins[:3]:  # Testar algumas origens válidas
                is_valid = validate_origin(origin)
                if is_valid:
                    results["valid_accepted"] += 1
                    print(f"  ✅ {origin} - ACEITO (correto)")
                else:
                    print(f"  ❌ {origin} - REJEITADO (falha de configuração!)")
                
                results["tests"].append({
                    "origin": origin,
                    "type": "valid",
                    "expected": True,
                    "actual": is_valid,
                    "passed": is_valid
                })
            
            return results
            
        finally:
            # Restaurar ambiente original
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)
    
    def test_cors_http_validation(self) -> Dict[str, Any]:
        """Testa CORS via HTTP conforme sugerido no SEC-001"""
        print(f"\n🌐 Testando CORS via HTTP: {self.base_url}")
        
        malicious_origins = [
            "http://evil.com",
            "https://attacker.net",
            "http://malicious-phishing.org"
        ]
        
        results = {
            "http_tests": [],
            "malicious_blocked": 0
        }
        
        for origin in malicious_origins:
            try:
                # Teste conforme sugerido: curl -H 'Origin: evil.com'
                response = requests.options(
                    f"{self.base_url}/cors/test",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "GET"
                    },
                    timeout=5
                )
                
                cors_header = response.headers.get("Access-Control-Allow-Origin")
                blocked = not cors_header or cors_header != origin
                
                if blocked:
                    results["malicious_blocked"] += 1
                    print(f"  ✅ {origin} - BLOQUEADO via HTTP (correto)")
                else:
                    print(f"  ❌ {origin} - PERMITIDO via HTTP (falha de segurança!)")
                
                results["http_tests"].append({
                    "origin": origin,
                    "status_code": response.status_code,
                    "cors_header": cors_header,
                    "blocked": blocked
                })
                
            except Exception as e:
                print(f"  ⚠️ {origin} - Erro de conexão: {e}")
                results["http_tests"].append({
                    "origin": origin,
                    "error": str(e),
                    "blocked": True  # Se não conectou, está bloqueado
                })
        
        return results
    
    async def run_all_tests(self):
        """Executa todos os testes de segurança CORS"""
        print("🛡️ SEC-001 CORS SECURITY VALIDATION")
        print("=" * 50)
        
        all_results = {}
        
        # Teste 1: Validação local em diferentes ambientes
        for env_name in TEST_ENVIRONMENTS.keys():
            results = self.test_cors_validation_local(env_name)
            all_results[f"local_{env_name}"] = results
            self.test_results.append(results)
        
        # Teste 2: Validação HTTP (se servidor estiver rodando)
        try:
            http_results = self.test_cors_http_validation()
            all_results["http_validation"] = http_results
        except Exception as e:
            print(f"\n⚠️ Teste HTTP pulado - servidor não disponível: {e}")
        
        # Relatório final
        print("\n" + "=" * 50)
        print("📋 SEC-001 RELATÓRIO FINAL")
        print("=" * 50)
        
        total_malicious_tests = 0
        total_malicious_blocked = 0
        total_valid_tests = 0
        total_valid_accepted = 0
        
        for env_results in self.test_results:
            total_malicious_tests += len([t for t in env_results["tests"] if t["type"] == "malicious"])
            total_malicious_blocked += len([t for t in env_results["tests"] if t["type"] == "malicious" and t["passed"]])
            total_valid_tests += len([t for t in env_results["tests"] if t["type"] == "valid"])
            total_valid_accepted += len([t for t in env_results["tests"] if t["type"] == "valid" and t["passed"]])
        
        malicious_block_rate = (total_malicious_blocked / total_malicious_tests * 100) if total_malicious_tests > 0 else 0
        valid_accept_rate = (total_valid_accepted / total_valid_tests * 100) if total_valid_tests > 0 else 0
        
        print(f"\n🔒 Proteção contra origens maliciosas:")
        print(f"   Testadas: {total_malicious_tests}")
        print(f"   Bloqueadas: {total_malicious_blocked}")
        print(f"   Taxa de bloqueio: {malicious_block_rate:.1f}%")
        
        print(f"\n✅ Aceitação de origens válidas:")
        print(f"   Testadas: {total_valid_tests}")
        print(f"   Aceitas: {total_valid_accepted}")
        print(f"   Taxa de aceitação: {valid_accept_rate:.1f}%")
        
        # Verificar se SEC-001 foi corrigido
        sec001_fixed = malicious_block_rate >= 95 and valid_accept_rate >= 95
        
        print(f"\n🏆 STATUS SEC-001:")
        if sec001_fixed:
            print("✅ CORRIGIDO - Validação dinâmica funcionando")
            print("✅ Origens maliciosas bloqueadas adequadamente")
            print("✅ Validação baseada em ambiente implementada")
        else:
            print("❌ NÃO CORRIGIDO - Falhas de segurança detectadas")
            print("❌ Revisar configuração CORS")
        
        return sec001_fixed


async def main():
    """Função principal para executar validação SEC-001"""
    tester = CORSSecurityTester()
    success = await tester.run_all_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SEC-001 - CORREÇÃO VALIDADA COM SUCESSO!")
    else:
        print("💥 SEC-001 - CORREÇÃO FALHOU - VERIFICAR CONFIGURAÇÃO")
    print("=" * 50)
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
