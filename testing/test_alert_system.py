#!/usr/bin/env python3
"""
Script de teste para o Sistema de Alertas
"""
import asyncio
import sys
import os

# Adicionar o diretório root ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.alert_system import alert_manager, AlertType, AlertSeverity, test_alert_system

async def main():
    """Função principal de teste"""
    print("🚨 === TESTE DO SISTEMA DE ALERTAS === 🚨")
    print()
    
    # Teste básico do sistema
    await test_alert_system()
    
    print("\n" + "="*50)
    print("🔍 EXECUTANDO TESTES AVANÇADOS...")
    print("="*50)
    
    # Teste de múltiplos alertas
    print("\n1. 📝 Criando múltiplos alertas...")
    
    await alert_manager.create_alert(
        alert_id="high_cpu_test",
        alert_type=AlertType.PERFORMANCE,
        severity=AlertSeverity.HIGH,
        title="CPU Alta - Teste",
        message="Uso de CPU acima de 90% detectado",
        data={"cpu_usage": 95.5, "threshold": 90}
    )
    
    await alert_manager.create_alert(
        alert_id="api_slow_test",
        alert_type=AlertType.API_ERROR,
        severity=AlertSeverity.MEDIUM,
        title="API Lenta - Teste",
        message="Tempo de resposta da API WhatsApp elevado",
        data={"response_time": 3.2, "threshold": 2.0}
    )
    
    await alert_manager.create_alert(
        alert_id="critical_error_test",
        alert_type=AlertType.SYSTEM_ERROR,
        severity=AlertSeverity.CRITICAL,
        title="Erro Crítico - Teste",
        message="Falha crítica no sistema detectada",
        data={"error": "Database connection failed", "component": "database"}
    )
    
    print("✅ Alertas criados com sucesso!")
    
    # Mostrar resumo
    print("\n2. 📊 Resumo dos alertas:")
    summary = alert_manager.get_alert_summary()
    print(f"   Total: {summary['total']}")
    print(f"   🚨 Críticos: {summary['critical']}")
    print(f"   🔴 Altos: {summary['high']}")
    print(f"   🟡 Médios: {summary['medium']}")
    print(f"   🔵 Baixos: {summary['low']}")
    
    print(f"\n   Por tipo:")
    for alert_type, count in summary['by_type'].items():
        if count > 0:
            print(f"   - {alert_type.replace('_', ' ').title()}: {count}")
    
    # Listar alertas ativos
    print("\n3. 📋 Alertas ativos:")
    active_alerts = alert_manager.get_active_alerts()
    
    for i, alert in enumerate(active_alerts, 1):
        severity_emoji = {
            "critical": "🚨",
            "high": "🔴", 
            "medium": "🟡",
            "low": "🔵"
        }
        
        emoji = severity_emoji.get(alert.severity.value, "❓")
        print(f"   {i}. {emoji} [{alert.severity.value.upper()}] {alert.title}")
        print(f"      {alert.message}")
        print(f"      Tipo: {alert.type.value} | ID: {alert.id}")
        print(f"      Timestamp: {alert.timestamp.strftime('%H:%M:%S')}")
        if alert.data:
            print(f"      Dados: {alert.data}")
        print()
    
    # Testar filtros
    print("4. 🔍 Testando filtros:")
    
    critical_alerts = alert_manager.get_active_alerts(severity="critical")
    print(f"   Alertas críticos: {len(critical_alerts)}")
    
    high_alerts = alert_manager.get_active_alerts(severity="high")
    print(f"   Alertas altos: {len(high_alerts)}")
    
    # Resolver alguns alertas
    print("\n5. ✅ Resolvendo alertas...")
    
    await alert_manager.resolve_alert("high_cpu_test")
    print("   ✅ Alerta de CPU resolvido")
    
    await alert_manager.resolve_alert("api_slow_test")
    print("   ✅ Alerta de API lenta resolvido")
    
    # Mostrar estado final
    print("\n6. 📊 Estado final:")
    final_summary = alert_manager.get_alert_summary()
    final_alerts = alert_manager.get_active_alerts()
    
    print(f"   Total de alertas ativos: {final_summary['total']}")
    print(f"   Alertas restantes:")
    
    for alert in final_alerts:
        print(f"   - {alert.title} ({alert.severity.value})")
    
    print("\n" + "="*50)
    print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
    print("="*50)
    
    return True

async def test_monitoring_cycle():
    """Testar um ciclo completo de monitoramento"""
    print("\n🔄 === TESTE DE CICLO DE MONITORAMENTO === 🔄")
    
    print("Executando verificações de saúde...")
    
    # Executar todas as verificações como no monitoring_task
    await alert_manager.check_api_health()
    await alert_manager.check_message_failures()
    await alert_manager.check_performance_metrics()
    await alert_manager.check_database_health()
    
    # Mostrar resultados
    summary = alert_manager.get_alert_summary()
    print(f"Alertas gerados: {summary['total']}")
    
    if summary['total'] > 0:
        alerts = alert_manager.get_active_alerts()
        print("Alertas detectados:")
        for alert in alerts:
            print(f"  - {alert.title} ({alert.severity.value})")
    else:
        print("✅ Nenhum alerta gerado - sistema saudável!")
    
    print("🔄 Ciclo de monitoramento concluído!")

if __name__ == "__main__":
    try:
        # Executar teste principal
        success = asyncio.run(main())
        
        if success:
            print("\n🔄 Executando teste de monitoramento...")
            asyncio.run(test_monitoring_cycle())
            
            print("\n✨ Todos os testes passaram!")
            print("💡 Para executar o monitoramento contínuo, use:")
            print("   python -c 'from app.services.alert_system import start_monitoring; import asyncio; asyncio.run(start_monitoring())'")
        
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
