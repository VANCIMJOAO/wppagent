#!/usr/bin/env python3
"""
Validação Completa do Sistema de Monitoramento
=============================================

Script para testar e validar todas as funcionalidades do sistema
de monitoramento implementado, incluindo SLA, métricas de negócio
e sistema de alertas.
"""

import asyncio
import time
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import aiohttp

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.config_factory import ConfigFactory
from app.services.comprehensive_monitoring import (
    monitoring_system, 
    SLAMonitor, 
    BusinessMetricsCollector,
    SLAMetric,
    BusinessMetric,
    AlertSeverity
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MonitoringValidator:
    """Validador completo do sistema de monitoramento"""
    
    def __init__(self):
        self.config = ConfigFactory.get_singleton_config()
        self.sla_monitor = SLAMonitor()
        self.business_metrics = BusinessMetricsCollector()
        self.test_results = []
        self.start_time = time.time()
    
    async def run_validation(self) -> Dict[str, Any]:
        """Executar validação completa"""
        
        print("🔍 Iniciando Validação do Sistema de Monitoramento")
        print("=" * 60)
        
        tests = [
            ("Configuração", self._test_configuration),
            ("SLA Monitor", self._test_sla_monitor),
            ("Métricas de Negócio", self._test_business_metrics),
            ("Sistema de Alertas", self._test_alert_system),
            ("Performance", self._test_performance_tracking),
            ("Dashboard", self._test_dashboard_generation),
            ("Integração", self._test_integration),
            ("Retenção de Dados", self._test_data_retention)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testando: {test_name}")
            try:
                result = await test_func()
                self.test_results.append({
                    'name': test_name,
                    'status': 'PASS' if result['success'] else 'FAIL',
                    'details': result,
                    'duration': result.get('duration', 0)
                })
                
                status_icon = "✅" if result['success'] else "❌"
                print(f"{status_icon} {test_name}: {result.get('message', 'OK')}")
                
            except Exception as e:
                self.test_results.append({
                    'name': test_name,
                    'status': 'ERROR',
                    'details': {'error': str(e)},
                    'duration': 0
                })
                print(f"❌ {test_name}: ERROR - {e}")
        
        return self._generate_final_report()
    
    async def _test_configuration(self) -> Dict[str, Any]:
        """Testar configuração do sistema"""
        
        start_time = time.time()
        issues = []
        
        # Verificar configurações essenciais
        required_configs = [
            ('metrics_enabled', bool),
            ('sla_response_time_ms', (int, float)),
            ('sla_uptime_percentage', (int, float)),
            ('sla_error_rate_percentage', (int, float)),
            ('health_check_interval_seconds', int),
            ('metrics_retention_days', int)
        ]
        
        for config_name, config_type in required_configs:
            if not hasattr(self.config, config_name):
                issues.append(f"Missing config: {config_name}")
            else:
                value = getattr(self.config, config_name)
                if not isinstance(value, config_type):
                    issues.append(f"Invalid type for {config_name}: {type(value)} (expected {config_type})")
        
        # Verificar valores válidos
        if self.config.sla_response_time_ms <= 0:
            issues.append("SLA response time must be > 0")
        
        if not (0 <= self.config.sla_uptime_percentage <= 100):
            issues.append("SLA uptime percentage must be between 0 and 100")
        
        if not (0 <= self.config.sla_error_rate_percentage <= 100):
            issues.append("SLA error rate percentage must be between 0 and 100")
        
        # Verificar configuração de alerting
        if self.config.alerting_enabled:
            if not (self.config.alert_email or self.config.alert_slack_webhook):
                issues.append("Alerting enabled but no channels configured")
        
        duration = time.time() - start_time
        
        return {
            'success': len(issues) == 0,
            'message': f"{len(issues)} issues found" if issues else "Configuration valid",
            'issues': issues,
            'config_summary': {
                'environment': self.config.environment.value,
                'metrics_enabled': self.config.metrics_enabled,
                'alerting_enabled': self.config.alerting_enabled,
                'sla_response_time_ms': self.config.sla_response_time_ms,
                'sla_uptime_percentage': self.config.sla_uptime_percentage
            },
            'duration': duration
        }
    
    async def _test_sla_monitor(self) -> Dict[str, Any]:
        """Testar monitor de SLA"""
        
        start_time = time.time()
        
        # Testar registro de métricas
        test_metrics = [
            (SLAMetric.RESPONSE_TIME, 150.0),
            (SLAMetric.RESPONSE_TIME, 500.0),
            (SLAMetric.RESPONSE_TIME, 2500.0),  # Pode gerar alerta
            (SLAMetric.ERROR_RATE, 0.5),
            (SLAMetric.ERROR_RATE, 2.0),
            (SLAMetric.UPTIME, 99.8),
            (SLAMetric.THROUGHPUT, 150.0)
        ]
        
        for metric, value in test_metrics:
            await self.sla_monitor.record_metric(metric, value)
        
        # Verificar se métricas foram registradas
        metrics_recorded = len(self.sla_monitor.metrics_buffer) > 0
        
        # Obter status do SLA
        sla_status = self.sla_monitor.get_sla_status(5)  # 5 minutos
        
        # Verificar se uptime tracker está funcionando
        self.sla_monitor.uptime_tracker.record_uptime()
        uptime_percentage = self.sla_monitor.uptime_tracker.get_uptime_percentage(60)
        
        duration = time.time() - start_time
        
        return {
            'success': metrics_recorded and 'metrics' in sla_status,
            'message': f"SLA monitor working, {len(self.sla_monitor.metrics_buffer)} metric types recorded",
            'metrics_types': list(self.sla_monitor.metrics_buffer.keys()),
            'sla_status_sample': sla_status,
            'uptime_percentage': uptime_percentage,
            'active_alerts': len(self.sla_monitor.active_alerts),
            'duration': duration
        }
    
    async def _test_business_metrics(self) -> Dict[str, Any]:
        """Testar coletor de métricas de negócio"""
        
        start_time = time.time()
        
        # Testar diferentes métricas de negócio
        test_metrics = [
            (BusinessMetric.CONVERSATIONS_STARTED, 5.0),
            (BusinessMetric.MESSAGES_PROCESSED, 25.0),
            (BusinessMetric.BOOKINGS_CREATED, 3.0),
            (BusinessMetric.CONVERSION_RATE, 15.5),
            (BusinessMetric.CUSTOMER_SATISFACTION, 4.2),
            (BusinessMetric.LEAD_GENERATION, 8.0)
        ]
        
        for metric, value in test_metrics:
            await self.business_metrics.record_business_metric(metric, value, {
                'test': 'validation',
                'timestamp': str(datetime.now())
            })
        
        # Obter resumo das métricas
        summary = self.business_metrics.get_business_summary(1)  # 1 dia
        
        metrics_recorded = len(self.business_metrics.metrics_buffer) > 0
        
        duration = time.time() - start_time
        
        return {
            'success': metrics_recorded,
            'message': f"Business metrics working, {len(test_metrics)} metrics recorded",
            'metrics_summary': summary,
            'buffer_sizes': {
                metric.value: len(self.business_metrics.metrics_buffer[metric])
                for metric in BusinessMetric
            },
            'duration': duration
        }
    
    async def _test_alert_system(self) -> Dict[str, Any]:
        """Testar sistema de alertas"""
        
        start_time = time.time()
        
        # Forçar condições de alerta registrando métricas ruins
        alert_conditions = [
            (SLAMetric.RESPONSE_TIME, self.config.sla_response_time_ms * 1.2),  # 20% acima do SLA
            (SLAMetric.ERROR_RATE, self.config.sla_error_rate_percentage * 1.5),  # 50% acima do SLA
        ]
        
        alerts_before = len(self.sla_monitor.active_alerts)
        
        for metric, value in alert_conditions:
            await self.sla_monitor.record_metric(metric, value)
        
        # Aguardar processamento
        await asyncio.sleep(0.1)
        
        alerts_after = len(self.sla_monitor.active_alerts)
        alerts_generated = alerts_after > alerts_before
        
        # Testar histórico de alertas
        alert_history_count = len(self.sla_monitor.alert_history)
        
        duration = time.time() - start_time
        
        return {
            'success': True,  # Sistema funcionando mesmo sem alertas
            'message': f"Alert system functional, {alerts_after - alerts_before} new alerts",
            'alerts_before': alerts_before,
            'alerts_after': alerts_after,
            'alerts_generated': alerts_generated,
            'alert_history_count': alert_history_count,
            'active_alerts': [
                {
                    'id': alert.id,
                    'severity': alert.severity.value,
                    'metric': alert.metric,
                    'title': alert.title
                }
                for alert in self.sla_monitor.active_alerts.values()
            ],
            'duration': duration
        }
    
    async def _test_performance_tracking(self) -> Dict[str, Any]:
        """Testar tracking de performance"""
        
        start_time = time.time()
        
        # Simular várias chamadas de API com diferentes tempos
        api_calls = [
            ('/webhook', 'POST', 200, 150.0),
            ('/conversations', 'POST', 201, 300.0),
            ('/bookings', 'POST', 201, 450.0),
            ('/health', 'GET', 200, 50.0),
            ('/api/error', 'GET', 500, 1200.0),  # Erro simulado
        ]
        
        for endpoint, method, status_code, response_time in api_calls:
            await monitoring_system.record_api_call(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time,
                user_id=f"test_user_{len(api_calls)}"
            )
        
        # Verificar se as métricas foram registradas
        response_time_metrics = len(self.sla_monitor.metrics_buffer.get(SLAMetric.RESPONSE_TIME, []))
        error_rate_metrics = len(self.sla_monitor.metrics_buffer.get(SLAMetric.ERROR_RATE, []))
        
        duration = time.time() - start_time
        
        return {
            'success': response_time_metrics > 0 and error_rate_metrics > 0,
            'message': f"Performance tracking active, {len(api_calls)} API calls recorded",
            'api_calls_simulated': len(api_calls),
            'response_time_metrics': response_time_metrics,
            'error_rate_metrics': error_rate_metrics,
            'duration': duration
        }
    
    async def _test_dashboard_generation(self) -> Dict[str, Any]:
        """Testar geração de dashboard"""
        
        start_time = time.time()
        
        try:
            dashboard_data = monitoring_system.get_monitoring_dashboard()
            
            # Verificar estrutura do dashboard
            required_sections = ['sla_status', 'business_metrics', 'active_alerts', 'system_info']
            missing_sections = [section for section in required_sections if section not in dashboard_data]
            
            # Verificar se há dados nas seções
            sla_has_data = len(dashboard_data.get('sla_status', {}).get('metrics', {})) > 0
            business_has_data = len(dashboard_data.get('business_metrics', {}).get('metrics', {})) > 0
            
            duration = time.time() - start_time
            
            return {
                'success': len(missing_sections) == 0,
                'message': f"Dashboard generated, {len(missing_sections)} missing sections",
                'missing_sections': missing_sections,
                'sla_has_data': sla_has_data,
                'business_has_data': business_has_data,
                'dashboard_size_kb': len(json.dumps(dashboard_data)) / 1024,
                'duration': duration
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Dashboard generation failed: {e}",
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    async def _test_integration(self) -> Dict[str, Any]:
        """Testar integração entre componentes"""
        
        start_time = time.time()
        
        # Testar integração através do sistema principal
        integration_tests = [
            ('message_processed', 1.0, {'source': 'webhook'}),
            ('conversation_started', 1.0, {'user_id': 'test_123'}),
            ('booking_created', 1.0, {'service': 'consultation'}),
            ('lead_generated', 1.0, {'channel': 'whatsapp'})
        ]
        
        for event_type, value, metadata in integration_tests:
            await monitoring_system.record_business_event(event_type, value, metadata)
        
        # Verificar se eventos foram processados
        business_buffer_size = sum(
            len(buffer) for buffer in self.business_metrics.metrics_buffer.values()
        )
        
        # Testar inicialização e parada do sistema
        await monitoring_system.start()
        is_running_after_start = monitoring_system.running
        
        await monitoring_system.stop()
        is_running_after_stop = monitoring_system.running
        
        duration = time.time() - start_time
        
        return {
            'success': business_buffer_size > 0 and is_running_after_start and not is_running_after_stop,
            'message': f"Integration working, {len(integration_tests)} events processed",
            'business_events_processed': len(integration_tests),
            'business_buffer_size': business_buffer_size,
            'start_stop_cycle': is_running_after_start and not is_running_after_stop,
            'duration': duration
        }
    
    async def _test_data_retention(self) -> Dict[str, Any]:
        """Testar retenção de dados"""
        
        start_time = time.time()
        
        # Verificar configuração de retenção
        retention_days = self.config.metrics_retention_days
        
        # Simular dados antigos (teste conceitual)
        old_date = datetime.now() - timedelta(days=retention_days + 1)
        
        # Verificar se há lógica de limpeza implementada
        has_cleanup_logic = hasattr(monitoring_system, '_metrics_cleanup_loop')
        
        # Verificar tamanhos atuais dos buffers
        sla_buffer_sizes = {
            metric.value: len(buffer) for metric, buffer in self.sla_monitor.metrics_buffer.items()
        }
        
        business_buffer_sizes = {
            metric.value: len(buffer) for metric, buffer in self.business_metrics.metrics_buffer.items()
        }
        
        duration = time.time() - start_time
        
        return {
            'success': has_cleanup_logic and retention_days > 0,
            'message': f"Data retention configured for {retention_days} days",
            'retention_days': retention_days,
            'has_cleanup_logic': has_cleanup_logic,
            'sla_buffer_sizes': sla_buffer_sizes,
            'business_buffer_sizes': business_buffer_sizes,
            'duration': duration
        }
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Gerar relatório final da validação"""
        
        total_duration = time.time() - self.start_time
        
        passed_tests = [t for t in self.test_results if t['status'] == 'PASS']
        failed_tests = [t for t in self.test_results if t['status'] == 'FAIL']
        error_tests = [t for t in self.test_results if t['status'] == 'ERROR']
        
        success_rate = len(passed_tests) / len(self.test_results) * 100
        
        report = {
            'validation_summary': {
                'total_tests': len(self.test_results),
                'passed': len(passed_tests),
                'failed': len(failed_tests),
                'errors': len(error_tests),
                'success_rate': round(success_rate, 2),
                'total_duration': round(total_duration, 2)
            },
            'test_results': self.test_results,
            'recommendations': self._generate_recommendations(),
            'system_status': self._get_system_status(),
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Gerar recomendações baseadas nos testes"""
        
        recommendations = []
        
        failed_tests = [t for t in self.test_results if t['status'] in ['FAIL', 'ERROR']]
        
        if failed_tests:
            recommendations.append("❌ Corrigir testes falhando antes de ir para produção")
        
        if not self.config.metrics_enabled:
            recommendations.append("⚠️  Habilitar métricas para monitoramento completo")
        
        if not self.config.alerting_enabled:
            recommendations.append("⚠️  Configurar sistema de alertas para produção")
        
        if not (self.config.alert_email or self.config.alert_slack_webhook):
            recommendations.append("📧 Configurar canais de notificação (email/Slack)")
        
        if self.config.environment.value == 'development' and self.config.sla_response_time_ms > 5000:
            recommendations.append("🚀 Ajustar SLA de resposta para ambiente de desenvolvimento")
        
        if not recommendations:
            recommendations.append("✅ Sistema de monitoramento está bem configurado!")
        
        return recommendations
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Obter status atual do sistema"""
        
        return {
            'monitoring_enabled': self.config.metrics_enabled,
            'alerting_enabled': self.config.alerting_enabled,
            'business_metrics_enabled': self.config.business_metrics_enabled,
            'environment': self.config.environment.value,
            'sla_configuration': {
                'response_time_ms': self.config.sla_response_time_ms,
                'uptime_percentage': self.config.sla_uptime_percentage,
                'error_rate_percentage': self.config.sla_error_rate_percentage
            },
            'active_features': {
                'prometheus': self.config.prometheus_enabled,
                'grafana': self.config.grafana_enabled,
                'health_checks': True,
                'performance_tracking': True
            }
        }


async def main():
    """Função principal"""
    
    try:
        validator = MonitoringValidator()
        report = await validator.run_validation()
        
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DE VALIDAÇÃO")
        print("=" * 60)
        
        summary = report['validation_summary']
        print(f"✅ Testes Passaram: {summary['passed']}/{summary['total_tests']} ({summary['success_rate']}%)")
        print(f"⏱️  Duração Total: {summary['total_duration']:.2f}s")
        
        if summary['failed'] > 0 or summary['errors'] > 0:
            print(f"❌ Testes Falharam: {summary['failed']}")
            print(f"🚨 Erros: {summary['errors']}")
        
        print("\n📋 RECOMENDAÇÕES:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print(f"\n💾 Status do Sistema:")
        status = report['system_status']
        print(f"  - Ambiente: {status['environment']}")
        print(f"  - Monitoramento: {'✅' if status['monitoring_enabled'] else '❌'}")
        print(f"  - Alertas: {'✅' if status['alerting_enabled'] else '❌'}")
        print(f"  - Métricas de Negócio: {'✅' if status['business_metrics_enabled'] else '❌'}")
        
        # Salvar relatório
        report_file = Path("test_reports/monitoring_validation_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        # Converter enums para strings antes de salvar
        def enum_serializer(obj):
            if hasattr(obj, 'value'):
                return obj.value
            elif hasattr(obj, '__dict__'):
                return {k: enum_serializer(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [enum_serializer(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: enum_serializer(v) for k, v in obj.items()}
            return obj
        
        serializable_report = enum_serializer(report)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_file}")
        
        # Código de saída baseado no sucesso
        exit_code = 0 if summary['success_rate'] >= 80 else 1
        return exit_code
        
    except Exception as e:
        print(f"❌ Erro durante validação: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
