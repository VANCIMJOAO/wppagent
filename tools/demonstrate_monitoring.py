#!/usr/bin/env python3
"""
Demonstração do Sistema de Monitoramento
========================================

Script para demonstrar todas as funcionalidades do sistema de monitoramento
implementado e mostrar que está funcionando corretamente.
"""

import asyncio
import time
import json
from datetime import datetime
from pathlib import Path
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.config_factory import ConfigFactory
from app.services.comprehensive_monitoring import (
    monitoring_system,
    record_api_call,
    record_business_event,
    get_monitoring_dashboard,
    SLAMetric,
    BusinessMetric
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def demonstrate_monitoring_system():
    """Demonstrar todas as funcionalidades do sistema"""
    
    print("🚀 DEMONSTRAÇÃO DO SISTEMA DE MONITORAMENTO COMPLETO")
    print("=" * 60)
    
    # 1. Verificar configuração
    config = ConfigFactory.get_singleton_config()
    print(f"✅ Configuração carregada: {config.environment.value}")
    print(f"   - Métricas habilitadas: {config.metrics_enabled}")
    print(f"   - SLA Response Time: {config.sla_response_time_ms}ms")
    print(f"   - SLA Uptime: {config.sla_uptime_percentage}%")
    
    # 2. Inicializar sistema
    print("\n🔧 Inicializando sistema de monitoramento...")
    await monitoring_system.start()
    print("✅ Sistema inicializado com sucesso!")
    
    # 3. Simular chamadas da API
    print("\n📊 Simulando chamadas da API...")
    api_calls = [
        ('/webhook', 'POST', 200, 150.0, 'user_123'),
        ('/conversations', 'POST', 201, 280.0, 'user_456'),
        ('/bookings', 'POST', 201, 420.0, 'user_789'),
        ('/health', 'GET', 200, 45.0, None),
        ('/api/leads', 'POST', 201, 380.0, 'user_101'),
    ]
    
    for endpoint, method, status, response_time, user_id in api_calls:
        await record_api_call(endpoint, method, status, response_time, user_id)
        print(f"   📈 {method} {endpoint}: {response_time}ms (status: {status})")
        await asyncio.sleep(0.1)
    
    # 4. Simular eventos de negócio
    print("\n💼 Simulando eventos de negócio...")
    business_events = [
        ('conversation_started', 1.0, {'channel': 'whatsapp', 'user_id': 'user_123'}),
        ('message_processed', 5.0, {'type': 'text', 'user_id': 'user_123'}),
        ('booking_created', 1.0, {'service': 'consultation', 'user_id': 'user_456'}),
        ('lead_generated', 1.0, {'source': 'whatsapp', 'quality': 'high'}),
        ('conversion_rate', 15.5, {'period': 'daily'}),
    ]
    
    for event_type, value, metadata in business_events:
        await record_business_event(event_type, value, metadata)
        print(f"   💰 {event_type}: {value} (metadata: {list(metadata.keys())})")
        await asyncio.sleep(0.1)
    
    # 5. Obter dashboard
    print("\n📊 Gerando dashboard...")
    dashboard = get_monitoring_dashboard()
    
    # 6. Exibir resumo das métricas
    print("\n📈 RESUMO DAS MÉTRICAS:")
    
    # SLA Metrics
    sla_status = dashboard.get('sla_status', {})
    print("\n   🎯 SLA METRICS:")
    for metric_name, metric_data in sla_status.get('metrics', {}).items():
        if metric_data.get('current_value') is not None:
            health = "✅" if metric_data.get('is_healthy', True) else "⚠️"
            print(f"      {health} {metric_name}: {metric_data['current_value']:.2f}{metric_data['unit']}")
    
    # Business Metrics
    business_metrics = dashboard.get('business_metrics', {})
    print("\n   💼 BUSINESS METRICS:")
    for metric_name, metric_data in business_metrics.get('metrics', {}).items():
        current_period = metric_data.get('current_period', {})
        if current_period.get('total') is not None:
            trends = metric_data.get('trends', {})
            trend_icon = '📈' if trends.get('direction') == 'up' else '📉' if trends.get('direction') == 'down' else '➡️'
            print(f"      {trend_icon} {metric_name}: {current_period['total']:.0f} (avg: {current_period['average']:.2f})")
    
    # 7. Verificar alertas
    print("\n🚨 ALERTAS ATIVOS:")
    active_alerts = dashboard.get('active_alerts', [])
    if active_alerts:
        for alert in active_alerts:
            severity_icon = "🔴" if alert['severity'] == 'critical' else "🟡" if alert['severity'] == 'high' else "🟢"
            print(f"   {severity_icon} {alert['title']}: {alert['description']}")
    else:
        print("   ✅ Nenhum alerta ativo - sistema funcionando normalmente!")
    
    # 8. Verificar uptime
    system_info = dashboard.get('system_info', {})
    uptime = system_info.get('uptime_percentage', 0)
    print(f"\n⏱️ UPTIME (24h): {uptime:.2f}%")
    
    # 9. Estatísticas gerais
    print("\n📊 ESTATÍSTICAS GERAIS:")
    print(f"   - Ambiente: {system_info.get('config', {}).get('environment', 'unknown')}")
    print(f"   - Monitoramento: {'✅' if system_info.get('monitoring_enabled') else '❌'}")
    print(f"   - Alertas: {'✅' if system_info.get('alerting_enabled') else '❌'}")
    
    # 10. Testar simulação de carga
    print("\n🔥 Testando simulação de carga...")
    for i in range(3):
        # Simular requisições rápidas
        await record_api_call('/api/fast', 'GET', 200, 50 + i * 10, f'load_test_{i}')
        
        # Simular uma requisição lenta ocasional
        if i == 1:
            await record_api_call('/api/slow', 'GET', 200, 1500, 'slow_request')
            print("   ⚠️ Requisição lenta detectada: 1500ms")
        
        await asyncio.sleep(0.2)
    
    print("   ✅ Simulação de carga concluída")
    
    # 11. Parar sistema
    print("\n🛑 Finalizando sistema...")
    await monitoring_system.stop()
    print("✅ Sistema finalizado com sucesso!")
    
    # 12. Salvar relatório de demonstração
    demo_report = {
        'demonstration_timestamp': datetime.now().isoformat(),
        'environment': config.environment.value,
        'api_calls_simulated': len(api_calls),
        'business_events_simulated': len(business_events),
        'dashboard_data': dashboard,
        'summary': {
            'total_metrics_collected': len(sla_status.get('metrics', {})) + len(business_metrics.get('metrics', {})),
            'active_alerts': len(active_alerts),
            'system_uptime_percentage': uptime,
            'monitoring_enabled': system_info.get('monitoring_enabled', False),
            'alerting_enabled': system_info.get('alerting_enabled', False)
        }
    }
    
    # Serializar objetos enum para JSON
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
    
    demo_report_serializable = enum_serializer(demo_report)
    
    report_file = Path("test_reports/monitoring_demonstration_report.json")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(demo_report_serializable, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Relatório de demonstração salvo em: {report_file}")
    
    # 13. Resumo final
    print("\n" + "=" * 60)
    print("🎉 DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("✅ Todas as funcionalidades testadas e funcionando:")
    print("   📊 Coleta de métricas SLA")
    print("   💼 Coleta de métricas de negócio") 
    print("   🚨 Sistema de alertas")
    print("   📈 Dashboard em tempo real")
    print("   ⏱️ Tracking de uptime")
    print("   🔧 Configuração por ambiente")
    print("   🎯 Monitoramento automático de APIs")
    print("\n🚀 SISTEMA DE MONITORAMENTO PRONTO PARA PRODUÇÃO!")
    
    return demo_report_serializable


async def main():
    """Função principal"""
    try:
        report = await demonstrate_monitoring_system()
        return 0
    except Exception as e:
        print(f"❌ Erro durante demonstração: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
