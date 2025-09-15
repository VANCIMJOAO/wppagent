#!/usr/bin/env python3
"""
🔍 Observability Stack Validation
Valida configuração e funcionamento da stack 360° no CI/CD
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

import requests


class ObservabilityValidator:
    def __init__(self):
        self.validation_results = {}
        self.critical_components = [
            "logging_system",
            "metrics_collection",
            "health_checks",
            "error_tracking",
            "performance_monitoring",
        ]

    def validate_logging_configuration(self) -> Tuple[bool, str]:
        """Valida configuração do sistema de logs"""
        print("📝 Validating logging configuration...")

        try:
            # Check if logging config exists
            import app.config

            if hasattr(app.config, "LOGGING_CONFIG"):
                print("  ✅ Logging configuration found")
                return True, "Logging configuration is properly set up"
            else:
                return False, "Logging configuration not found"

        except Exception as e:
            return False, f"Error validating logging: {e}"

    def validate_metrics_collection(self) -> Tuple[bool, str]:
        """Valida coleta de métricas"""
        print("📊 Validating metrics collection...")

        try:
            # Check prometheus metrics endpoint
            from app.monitoring.metrics import get_metrics

            metrics = get_metrics()
            if metrics:
                print("  ✅ Metrics collection active")
                return True, f"Metrics collection working ({len(metrics)} metrics)"
            else:
                return False, "No metrics being collected"

        except ImportError:
            return False, "Metrics module not found"
        except Exception as e:
            return False, f"Error validating metrics: {e}"

    def validate_health_checks(self) -> Tuple[bool, str]:
        """Valida health checks"""
        print("🔍 Validating health check system...")

        try:
            # Check health check implementation
            from app.routes.health import health_check

            # Simulate health check
            health_status = health_check()
            if health_status.get("status") == "healthy":
                print("  ✅ Health checks functioning")
                return True, "Health check system operational"
            else:
                return False, f"Health check failed: {health_status}"

        except ImportError:
            return False, "Health check module not found"
        except Exception as e:
            return False, f"Error validating health checks: {e}"

    def validate_error_tracking(self) -> Tuple[bool, str]:
        """Valida rastreamento de erros"""
        print("🚨 Validating error tracking...")

        try:
            # Check error tracking configuration
            from app.monitoring.error_tracking import ErrorTracker

            tracker = ErrorTracker()
            if tracker.is_configured():
                print("  ✅ Error tracking configured")
                return True, "Error tracking system ready"
            else:
                return False, "Error tracking not configured"

        except ImportError:
            return False, "Error tracking module not found"
        except Exception as e:
            return False, f"Error validating error tracking: {e}"

    def validate_performance_monitoring(self) -> Tuple[bool, str]:
        """Valida monitoramento de performance"""
        print("📈 Validating performance monitoring...")

        try:
            # Check performance monitoring
            from app.monitoring.performance import PerformanceMonitor

            monitor = PerformanceMonitor()
            if monitor.is_active():
                print("  ✅ Performance monitoring active")
                return True, "Performance monitoring operational"
            else:
                return False, "Performance monitoring not active"

        except ImportError:
            return False, "Performance monitoring module not found"
        except Exception as e:
            return False, f"Error validating performance monitoring: {e}"

    def validate_ai_insights(self) -> Tuple[bool, str]:
        """Valida sistema de AI insights"""
        print("🧠 Validating AI insights system...")

        try:
            # Check AI insights module
            from app.monitoring.ai_insights import AIInsights

            ai_system = AIInsights()
            if ai_system.is_ready():
                print("  ✅ AI insights system ready")
                return True, "AI insights system operational"
            else:
                return False, "AI insights system not ready"

        except ImportError:
            return False, "AI insights module not found"
        except Exception as e:
            return False, f"Error validating AI insights: {e}"

    def validate_chaos_engineering(self) -> Tuple[bool, str]:
        """Valida sistema de chaos engineering"""
        print("🧪 Validating chaos engineering...")

        try:
            # Check chaos engineering setup
            from app.monitoring.chaos import ChaosExperiment

            chaos = ChaosExperiment()
            if chaos.is_configured():
                print("  ✅ Chaos engineering configured")
                return True, "Chaos engineering system ready"
            else:
                return False, "Chaos engineering not configured"

        except ImportError:
            return False, "Chaos engineering module not found"
        except Exception as e:
            return False, f"Error validating chaos engineering: {e}"

    def run_validation(self) -> Dict:
        """Executa validação completa"""
        print("\n" + "=" * 60)
        print("🔍 OBSERVABILITY STACK VALIDATION")
        print("=" * 60)

        validations = {
            "logging_system": self.validate_logging_configuration,
            "metrics_collection": self.validate_metrics_collection,
            "health_checks": self.validate_health_checks,
            "error_tracking": self.validate_error_tracking,
            "performance_monitoring": self.validate_performance_monitoring,
            "ai_insights": self.validate_ai_insights,
            "chaos_engineering": self.validate_chaos_engineering,
        }

        results = {}
        passed = 0
        total = len(validations)

        for component, validator in validations.items():
            try:
                success, message = validator()
                results[component] = {
                    "passed": success,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                }

                if success:
                    passed += 1
                    print(f"✅ {component.replace('_', ' ').title()}: PASSED")
                else:
                    print(
                        f"❌ {component.replace('_', ' ').title()}: FAILED - {message}"
                    )

            except Exception as e:
                results[component] = {
                    "passed": False,
                    "message": f"Validation error: {e}",
                    "timestamp": datetime.now().isoformat(),
                }
                print(f"❌ {component.replace('_', ' ').title()}: ERROR - {e}")

        # Calculate overall score
        score = (passed / total) * 100
        status = "PASSED" if passed == total else "PARTIAL" if passed > 0 else "FAILED"

        final_report = {
            "overall_status": status,
            "score": score,
            "passed_validations": passed,
            "total_validations": total,
            "details": results,
            "timestamp": datetime.now().isoformat(),
            "trilha2_compliance": passed >= 5,  # At least 5 components working
        }

        # Save report
        with open("observability_validation.json", "w") as f:
            json.dump(final_report, f, indent=2)

        print(f"\n📊 Validation Summary:")
        print(f"   Score: {score:.1f}% ({passed}/{total} components)")
        print(f"   Status: {status}")
        print(
            f"   TRILHA 2 Compliance: {'✅' if final_report['trilha2_compliance'] else '❌'}"
        )

        return final_report


if __name__ == "__main__":
    validator = ObservabilityValidator()
    report = validator.run_validation()

    # Exit based on results
    if report["overall_status"] == "PASSED":
        print("\n🎉 All observability components validated successfully!")
        sys.exit(0)
    elif report["overall_status"] == "PARTIAL":
        print(
            f"\n⚠️ Partial validation: {report['passed_validations']}/{report['total_validations']} components working"
        )
        sys.exit(0 if report["trilha2_compliance"] else 1)
    else:
        print("\n❌ Observability validation failed")
        sys.exit(1)
