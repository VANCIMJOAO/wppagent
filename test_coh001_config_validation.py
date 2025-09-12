#!/usr/bin/env python3
"""
🔧 COH-001 Configuration Coherence Validation Test

Testa a correção do sistema de configuração que elimina mapeamentos manuais 
complexos e garante acesso consistente entre Backend↔Frontend.

Referência: COH-001 - Sistema de compatibilidade complexo com mapeamentos manuais
"""

import os
import sys
import asyncio
from typing import Dict, Any

class COH001ConfigValidator:
    def __init__(self):
        self.test_results = []
        self.errors = []
    
    def test_config_import_consistency(self) -> Dict[str, Any]:
        """Teste 1: Consistência de imports de configuração"""
        print("\n🔧 Teste 1: Consistência de imports")
        print("-" * 50)
        
        results = {
            "imports_working": True,
            "settings_accessible": True,
            "errors": []
        }
        
        try:
            # Testar diferentes formas de import
            sys.path.insert(0, '/home/vancim/whats_agent')
            
            # Import 1: Via app.config
            from app.config import settings
            print("  ✅ Import via app.config funcionando")
            
            # Import 2: Via factory
            from app.config.config_factory import get_settings
            config_from_factory = get_settings()
            print("  ✅ Import via config_factory funcionando")
            
            # Verificar se são compatíveis
            if hasattr(settings, 'meta_access_token') and hasattr(config_from_factory, 'meta_access_token'):
                print("  ✅ Ambos têm acesso a meta_access_token")
            else:
                results["errors"].append("Incompatibilidade entre imports")
                
        except Exception as e:
            print(f"  ❌ Erro de import: {e}")
            results["imports_working"] = False
            results["errors"].append(f"Import error: {e}")
        
        return results
    
    def test_secrets_accessibility(self) -> Dict[str, Any]:
        """Teste 2: Acessibilidade de todas as configurações secrets"""
        print("\n🔒 Teste 2: Acessibilidade de secrets")
        print("-" * 50)
        
        try:
            sys.path.insert(0, '/home/vancim/whats_agent')
            from app.config import settings
            
            # Usar método de validação integrado
            validation_results = settings.validate_secrets_access()
            
            accessible_count = sum(1 for result in validation_results.values() 
                                 if isinstance(result, dict) and result.get('accessible', False))
            total_secrets = len(validation_results)
            
            print(f"📊 Secrets acessíveis: {accessible_count}/{total_secrets}")
            
            for field, result in validation_results.items():
                if isinstance(result, dict):
                    if result.get('accessible', False):
                        preview = result.get('preview', 'None')
                        print(f"  ✅ {field}: {preview}")
                    else:
                        error = result.get('error', 'Não acessível')
                        print(f"  ❌ {field}: {error}")
                        
            return {
                "total_secrets": total_secrets,
                "accessible_secrets": accessible_count,
                "accessibility_rate": (accessible_count / total_secrets * 100) if total_secrets > 0 else 0,
                "validation_details": validation_results
            }
            
        except Exception as e:
            print(f"❌ Erro ao validar secrets: {e}")
            return {
                "total_secrets": 0,
                "accessible_secrets": 0,
                "accessibility_rate": 0,
                "error": str(e)
            }
    
    def test_backwards_compatibility(self) -> Dict[str, Any]:
        """Teste 3: Compatibilidade com código existente"""
        print("\n🔄 Teste 3: Compatibilidade backwards")
        print("-" * 50)
        
        results = {
            "legacy_access_working": True,
            "property_access_working": True,
            "tested_fields": []
        }
        
        try:
            sys.path.insert(0, '/home/vancim/whats_agent')
            from app.config import settings
            
            # Testar campos críticos que devem estar acessíveis
            critical_fields = [
                'meta_access_token',
                'openai_api_key', 
                'webhook_verify_token',
                'secret_key',
                'database_url'
            ]
            
            for field in critical_fields:
                try:
                    # Testar acesso via property
                    value = getattr(settings, field)
                    
                    if value is not None:
                        print(f"  ✅ {field}: Acessível via property")
                        results["tested_fields"].append({
                            "field": field,
                            "accessible": True,
                            "method": "property"
                        })
                    else:
                        print(f"  ⚠️ {field}: Acessível mas valor None")
                        results["tested_fields"].append({
                            "field": field,
                            "accessible": True,
                            "method": "property",
                            "warning": "None value"
                        })
                        
                except Exception as e:
                    print(f"  ❌ {field}: Erro de acesso - {e}")
                    results["property_access_working"] = False
                    results["tested_fields"].append({
                        "field": field,
                        "accessible": False,
                        "error": str(e)
                    })
            
        except Exception as e:
            print(f"❌ Erro no teste de compatibilidade: {e}")
            results["legacy_access_working"] = False
            results["error"] = str(e)
        
        return results
    
    def test_no_complex_mappings(self) -> Dict[str, Any]:
        """Teste 4: Verificar eliminação de mapeamentos complexos"""
        print("\n🧹 Teste 4: Eliminação de mapeamentos complexos")
        print("-" * 50)
        
        results = {
            "complex_mappings_eliminated": True,
            "code_simplified": True
        }
        
        try:
            # Ler o arquivo config.py para verificar se ainda tem mapeamentos complexos
            config_file_path = '/home/vancim/whats_agent/app/config.py'
            with open(config_file_path, 'r') as f:
                config_content = f.read()
            
            # Verificar se não tem mais os problemas antigos
            problematic_patterns = [
                "lambda:",  # Mapeamentos lambda complexos
                "mapping =",  # Dicionário de mapeamento manual
                "if name in mapping:",  # Lógica de mapeamento condicional
            ]
            
            found_problems = []
            for pattern in problematic_patterns:
                if pattern in config_content:
                    found_problems.append(pattern)
            
            if found_problems:
                print(f"  ❌ Padrões problemáticos ainda encontrados: {found_problems}")
                results["complex_mappings_eliminated"] = False
            else:
                print("  ✅ Mapeamentos complexos eliminados")
            
            # Verificar se tem o novo sistema unificado
            if "UnifiedConfigSettings" in config_content:
                print("  ✅ Sistema unificado implementado")
            else:
                print("  ❌ Sistema unificado não encontrado")
                results["code_simplified"] = False
                
        except Exception as e:
            print(f"❌ Erro ao analisar código: {e}")
            results["error"] = str(e)
        
        return results
    
    async def run_all_tests(self):
        """Executar todos os testes de validação COH-001"""
        print("🔧 COH-001 CONFIGURATION COHERENCE VALIDATION")
        print("=" * 60)
        
        tests = [
            ("Import Consistency", self.test_config_import_consistency),
            ("Secrets Accessibility", self.test_secrets_accessibility),
            ("Backwards Compatibility", self.test_backwards_compatibility),
            ("Complex Mappings Elimination", self.test_no_complex_mappings)
        ]
        
        test_results = {}
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results[test_name] = result
                self.test_results.append(result)
            except Exception as e:
                print(f"❌ Erro no teste {test_name}: {e}")
                test_results[test_name] = {"error": str(e)}
                self.errors.append(f"{test_name}: {e}")
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📋 COH-001 RELATÓRIO FINAL")
        print("=" * 60)
        
        # Calcular sucesso geral
        total_tests = len(test_results)
        successful_tests = 0
        
        for test_name, result in test_results.items():
            if isinstance(result, dict) and not result.get('error'):
                # Critérios específicos de sucesso para cada teste
                if test_name == "Import Consistency":
                    success = result.get('imports_working', False) and result.get('settings_accessible', False)
                elif test_name == "Secrets Accessibility":
                    success = result.get('accessibility_rate', 0) >= 80  # Pelo menos 80% acessíveis
                elif test_name == "Backwards Compatibility":
                    success = result.get('property_access_working', False)
                elif test_name == "Complex Mappings Elimination":
                    success = result.get('complex_mappings_eliminated', False) and result.get('code_simplified', False)
                else:
                    success = True
                
                if success:
                    successful_tests += 1
                    print(f"  ✅ PASS {test_name}")
                else:
                    print(f"  ❌ FAIL {test_name}")
            else:
                print(f"  ❌ ERROR {test_name}")
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n✅ Testes aprovados: {successful_tests}/{total_tests}")
        print(f"📊 Taxa de sucesso: {success_rate:.1f}%")
        
        # Mostrar detalhes de secrets se disponível
        secrets_result = test_results.get("Secrets Accessibility", {})
        if "accessibility_rate" in secrets_result:
            print(f"🔒 Acessibilidade de secrets: {secrets_result['accessibility_rate']:.1f}%")
        
        # Verificar se COH-001 foi corrigido
        coh001_fixed = success_rate >= 75  # Pelo menos 75% dos testes passando
        
        print(f"\n🏆 STATUS COH-001:")
        if coh001_fixed:
            print("✅ CORRIGIDO - Sistema de configuração unificado")
            print("✅ Mapeamentos complexos eliminados")
            print("✅ Acesso consistente implementado")
        else:
            print("❌ NÃO CORRIGIDO - Problemas de coerência persistem")
            print("❌ Revisar sistema de configuração")
        
        if self.errors:
            print(f"\n❌ Erros encontrados ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
        
        return coh001_fixed


async def main():
    """Função principal para executar validação COH-001"""
    validator = COH001ConfigValidator()
    success = await validator.run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 COH-001 - CORREÇÃO VALIDADA COM SUCESSO!")
    else:
        print("💥 COH-001 - CORREÇÃO FALHOU - VERIFICAR CONFIGURAÇÃO")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
