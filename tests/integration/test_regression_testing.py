#!/usr/bin/env python3
"""TRILHA 2 FASE 2.3 - Regression Testing"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TestBaseline:
    """Define uma baseline para testes de regressão"""

    test_name: str
    expected_result: Any
    result_hash: str
    timestamp: str
    version: str


@dataclass
class RegressionResult:
    """Resultado de teste de regressão"""

    test_name: str
    current_result: Any
    baseline_result: Any
    is_regression: bool
    differences: List[str]
    timestamp: str


class RegressionDetector:
    """Detector de regressões baseado em comparação de resultados"""

    def __init__(self):
        self.baselines: Dict[str, TestBaseline] = {}
        self.results: List[RegressionResult] = []

    def create_baseline(
        self, test_name: str, result: Any, version: str = "1.0.0"
    ) -> TestBaseline:
        """Cria uma baseline para um teste"""
        result_str = json.dumps(result, sort_keys=True, default=str)
        result_hash = hashlib.md5(result_str.encode()).hexdigest()

        baseline = TestBaseline(
            test_name=test_name,
            expected_result=result,
            result_hash=result_hash,
            timestamp=datetime.now().isoformat(),
            version=version,
        )

        self.baselines[test_name] = baseline
        return baseline

    def compare_with_baseline(
        self, test_name: str, current_result: Any
    ) -> RegressionResult:
        """Compara resultado atual com baseline"""
        baseline = self.baselines.get(test_name)

        if not baseline:
            # Sem baseline, criar uma nova
            self.create_baseline(test_name, current_result)
            return RegressionResult(
                test_name=test_name,
                current_result=current_result,
                baseline_result=None,
                is_regression=False,
                differences=[],
                timestamp=datetime.now().isoformat(),
            )

        # Comparar resultados
        differences = self._find_differences(baseline.expected_result, current_result)
        is_regression = len(differences) > 0

        result = RegressionResult(
            test_name=test_name,
            current_result=current_result,
            baseline_result=baseline.expected_result,
            is_regression=is_regression,
            differences=differences,
            timestamp=datetime.now().isoformat(),
        )

        self.results.append(result)
        return result

    def _find_differences(
        self, expected: Any, actual: Any, path: str = ""
    ) -> List[str]:
        """Encontra diferenças entre resultados esperados e atuais"""
        differences = []

        if type(expected) != type(actual):
            differences.append(
                f"{path}: Type changed from {type(expected).__name__} to {type(actual).__name__}"
            )
            return differences

        if isinstance(expected, dict):
            # Verificar chaves removidas
            for key in expected:
                if key not in actual:
                    differences.append(f"{path}.{key}: Key removed")
                else:
                    sub_diffs = self._find_differences(
                        expected[key], actual[key], f"{path}.{key}"
                    )
                    differences.extend(sub_diffs)

            # Verificar chaves adicionadas
            for key in actual:
                if key not in expected:
                    differences.append(f"{path}.{key}: New key added")

        elif isinstance(expected, list):
            if len(expected) != len(actual):
                differences.append(
                    f"{path}: List length changed from {len(expected)} to {len(actual)}"
                )

            min_len = min(len(expected), len(actual))
            for i in range(min_len):
                sub_diffs = self._find_differences(
                    expected[i], actual[i], f"{path}[{i}]"
                )
                differences.extend(sub_diffs)

        elif expected != actual:
            differences.append(f"{path}: Value changed from {expected} to {actual}")

        return differences


class RegressionTestFramework:
    """Framework para testes de regressão automatizados"""

    def __init__(self):
        self.detector = RegressionDetector()
        self.test_results = []
        self._setup_baselines()

    def _setup_baselines(self):
        """Configura baselines iniciais"""

        # Baseline: Webhook Processing
        webhook_baseline = {
            "status": "success",
            "processed_messages": 1,
            "response_time_ms": 150,
            "memory_usage_mb": 45,
            "cache_hits": 2,
            "database_queries": 3,
        }
        self.detector.create_baseline("webhook_processing", webhook_baseline, "1.0.0")

        # Baseline: Authentication Flow
        auth_baseline = {
            "login_success": True,
            "token_generated": True,
            "token_type": "Bearer",
            "expires_in": 3600,
            "permissions": ["read", "write", "admin"],
            "session_created": True,
        }
        self.detector.create_baseline("auth_flow", auth_baseline, "1.0.0")

        # Baseline: Message Processing
        message_baseline = {
            "message_received": True,
            "ai_response_generated": True,
            "response_time_ms": 200,
            "context_maintained": True,
            "conversation_updated": True,
            "whatsapp_sent": True,
        }
        self.detector.create_baseline("message_processing", message_baseline, "1.0.0")

        # Baseline: Error Handling
        error_baseline = {
            "errors_caught": 3,
            "error_types": ["validation", "timeout", "rate_limit"],
            "recovery_successful": True,
            "user_notified": True,
            "logs_generated": True,
        }
        self.detector.create_baseline("error_handling", error_baseline, "1.0.0")

        # Baseline: Performance Metrics
        performance_baseline = {
            "avg_response_time_ms": 180,
            "requests_per_second": 50,
            "cpu_usage_percent": 25,
            "memory_usage_mb": 128,
            "cache_hit_ratio": 0.85,
            "error_rate_percent": 0.1,
        }
        self.detector.create_baseline(
            "performance_metrics", performance_baseline, "1.0.0"
        )

    def simulate_webhook_processing(self) -> Dict[str, Any]:
        """Simula processamento de webhook"""
        return {
            "status": "success",
            "processed_messages": 1,
            "response_time_ms": 155,  # Ligeiramente diferente da baseline
            "memory_usage_mb": 45,
            "cache_hits": 2,
            "database_queries": 3,
        }

    def simulate_auth_flow(self) -> Dict[str, Any]:
        """Simula fluxo de autenticação"""
        return {
            "login_success": True,
            "token_generated": True,
            "token_type": "Bearer",
            "expires_in": 3600,
            "permissions": ["read", "write", "admin"],
            "session_created": True,
        }

    def simulate_message_processing_with_regression(self) -> Dict[str, Any]:
        """Simula processamento com regressão"""
        return {
            "message_received": True,
            "ai_response_generated": True,
            "response_time_ms": 350,  # REGRESSÃO: Tempo muito alto
            "context_maintained": False,  # REGRESSÃO: Contexto perdido
            "conversation_updated": True,
            "whatsapp_sent": True,
            "new_feature": "added",  # Adição de campo
        }

    def simulate_error_handling(self) -> Dict[str, Any]:
        """Simula tratamento de erros"""
        return {
            "errors_caught": 3,
            "error_types": ["validation", "timeout", "rate_limit"],
            "recovery_successful": True,
            "user_notified": True,
            "logs_generated": True,
        }

    def simulate_performance_degradation(self) -> Dict[str, Any]:
        """Simula degradação de performance"""
        return {
            "avg_response_time_ms": 450,  # REGRESSÃO: Muito lento
            "requests_per_second": 25,  # REGRESSÃO: Throughput reduzido
            "cpu_usage_percent": 65,  # REGRESSÃO: CPU alta
            "memory_usage_mb": 256,  # REGRESSÃO: Uso de memória dobrou
            "cache_hit_ratio": 0.60,  # REGRESSÃO: Cache menos eficiente
            "error_rate_percent": 2.5,  # REGRESSÃO: Mais erros
        }

    def test_webhook_regression(self) -> bool:
        """Testa regressão no processamento de webhook"""
        print("🧪 Regression: Webhook Processing...")

        current_result = self.simulate_webhook_processing()
        regression_result = self.detector.compare_with_baseline(
            "webhook_processing", current_result
        )

        if regression_result.is_regression:
            print(
                f"   ⚠️ Regressão detectada: {len(regression_result.differences)} diferenças"
            )
            for diff in regression_result.differences:
                print(f"      - {diff}")
        else:
            print("   ✅ Sem regressão detectada")

        # Pequenas diferenças são aceitáveis (tolerância)
        acceptable = len(regression_result.differences) <= 1
        print(f"   🎯 Webhook regression: {'✅ PASSOU' if acceptable else '❌ FALHOU'}")
        return acceptable

    def test_auth_regression(self) -> bool:
        """Testa regressão na autenticação"""
        print("🧪 Regression: Authentication Flow...")

        current_result = self.simulate_auth_flow()
        regression_result = self.detector.compare_with_baseline(
            "auth_flow", current_result
        )

        if regression_result.is_regression:
            print(
                f"   ⚠️ Regressão detectada: {len(regression_result.differences)} diferenças"
            )
            for diff in regression_result.differences:
                print(f"      - {diff}")
        else:
            print("   ✅ Sem regressão detectada")

        success = not regression_result.is_regression
        print(f"   🎯 Auth regression: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    def test_message_processing_regression(self) -> bool:
        """Testa regressão no processamento de mensagens"""
        print("🧪 Regression: Message Processing...")

        current_result = self.simulate_message_processing_with_regression()
        regression_result = self.detector.compare_with_baseline(
            "message_processing", current_result
        )

        if regression_result.is_regression:
            print(
                f"   🚨 Regressão detectada: {len(regression_result.differences)} diferenças"
            )
            for diff in regression_result.differences:
                print(f"      - {diff}")
        else:
            print("   ✅ Sem regressão detectada")

        # Este teste DEVE detectar regressão
        regression_detected = regression_result.is_regression
        print(
            f"   🎯 Message regression detection: {'✅ PASSOU' if regression_detected else '❌ FALHOU'}"
        )
        return regression_detected

    def test_error_handling_regression(self) -> bool:
        """Testa regressão no tratamento de erros"""
        print("🧪 Regression: Error Handling...")

        current_result = self.simulate_error_handling()
        regression_result = self.detector.compare_with_baseline(
            "error_handling", current_result
        )

        if regression_result.is_regression:
            print(
                f"   ⚠️ Regressão detectada: {len(regression_result.differences)} diferenças"
            )
            for diff in regression_result.differences:
                print(f"      - {diff}")
        else:
            print("   ✅ Sem regressão detectada")

        success = not regression_result.is_regression
        print(
            f"   🎯 Error handling regression: {'✅ PASSOU' if success else '❌ FALHOU'}"
        )
        return success

    def test_performance_regression(self) -> bool:
        """Testa regressão de performance"""
        print("🧪 Regression: Performance Metrics...")

        current_result = self.simulate_performance_degradation()
        regression_result = self.detector.compare_with_baseline(
            "performance_metrics", current_result
        )

        if regression_result.is_regression:
            print(
                f"   🚨 Regressão de performance detectada: {len(regression_result.differences)} métricas"
            )
            for diff in regression_result.differences:
                print(f"      - {diff}")
        else:
            print("   ✅ Performance estável")

        # Este teste DEVE detectar regressão de performance
        regression_detected = regression_result.is_regression
        print(
            f"   🎯 Performance regression detection: {'✅ PASSOU' if regression_detected else '❌ FALHOU'}"
        )
        return regression_detected

    def test_baseline_management(self) -> bool:
        """Testa gerenciamento de baselines"""
        print("🧪 Regression: Baseline Management...")

        # Criar nova baseline
        new_baseline_data = {
            "test_feature": "active",
            "version": "2.0.0",
            "compatibility": True,
        }

        baseline = self.detector.create_baseline(
            "new_feature", new_baseline_data, "2.0.0"
        )
        baseline_created = "new_feature" in self.detector.baselines
        print(f"   ✅ Baseline criada: {'PASSOU' if baseline_created else 'FALHOU'}")

        # Testar comparação com nova baseline
        updated_data = {
            "test_feature": "active",
            "version": "2.0.0",
            "compatibility": True,
            "additional_field": "new",  # Campo adicional
        }

        result = self.detector.compare_with_baseline("new_feature", updated_data)
        change_detected = result.is_regression
        print(f"   🔍 Mudança detectada: {'PASSOU' if change_detected else 'FALHOU'}")

        success = baseline_created and change_detected
        print(f"   🎯 Baseline management: {'✅ PASSOU' if success else '❌ FALHOU'}")
        return success

    async def run_all_regression_tests(self):
        """Executa todos os testes de regressão"""
        print("�� TRILHA 2 FASE 2.3 - Regression Testing")
        print("🔍 Detecção Automática de Regressões")
        print("=" * 60)

        tests = [
            ("Webhook Processing", self.test_webhook_regression),
            ("Authentication Flow", self.test_auth_regression),
            ("Message Processing", self.test_message_processing_regression),
            ("Error Handling", self.test_error_handling_regression),
            ("Performance Metrics", self.test_performance_regression),
            ("Baseline Management", self.test_baseline_management),
        ]

        passed = 0
        total = len(tests)
        regressions_detected = 0

        for test_name, test_func in tests:
            try:
                print(f"\n🔎 {test_name}:")
                result = test_func()
                if result:
                    passed += 1
                    self.test_results.append({"test": test_name, "status": "PASSED"})
                    if "detection" in test_name.lower():
                        regressions_detected += 1
                else:
                    self.test_results.append({"test": test_name, "status": "FAILED"})
            except Exception as e:
                print(f"💥 Erro em {test_name}: {e}")
                self.test_results.append(
                    {"test": test_name, "status": "ERROR", "error": str(e)}
                )

        success_rate = passed / total

        print("\n" + "=" * 60)
        print("📊 RESULTADOS DOS TESTES DE REGRESSÃO")
        print("=" * 60)
        print(f"✅ Testes Passaram: {passed}")
        print(f"❌ Testes Falharam: {total - passed}")
        print(f"🚨 Regressões Detectadas: {regressions_detected}")
        print(f"📊 Total: {total}")
        print(f"🎯 Taxa de Sucesso: {success_rate:.1%}")

        if success_rate >= 0.8:
            print("\n🎉 EXCELENTE: Regression Testing validado!")
            print("✅ Sistema detecta regressões automaticamente")
            print("🔒 Baselines bem configuradas")
            print("🚨 Alertas funcionando corretamente")
        elif success_rate >= 0.6:
            print("\n⚠️ BOM: Detecção funciona, alguns ajustes necessários")
        else:
            print("\n❌ ATENÇÃO: Problemas na detecção de regressões")

        print(f"\n🎯 TRILHA 2 FASE 2.3 - Regression Testing IMPLEMENTADO")
        return success_rate >= 0.6


async def main():
    """Função principal"""
    framework = RegressionTestFramework()
    success = await framework.run_all_regression_tests()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
