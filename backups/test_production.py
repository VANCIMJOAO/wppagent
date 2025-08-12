#!/usr/bin/env python3
"""
Script de teste para verificar sistema de produção
"""

import sys
import os

# Adicionar path atual
sys.path.insert(0, '.')

print("🔍 Verificando Sistema de Produção...")
print("=" * 50)

try:
    # Testar imports
    print("📦 Testando imports...")
    
    from app.services.production_logger import setup_production_logging
    print("✅ Logger: OK")
    
    from app.services.business_metrics import metrics_collector
    print("✅ Metrics: OK")
    
    from app.services.automated_alerts import alert_manager
    print("✅ Alerts: OK")
    
    from app.services.performance_monitor import performance_monitor
    print("✅ Performance: OK")
    
    from app.services.backup_system import backup_manager
    print("✅ Backup: OK")
    
    print("\n🎉 TODOS OS SISTEMAS DE PRODUÇÃO CARREGADOS COM SUCESSO!")
    
    # Testar funcionalidades básicas
    print("\n🧪 Testando funcionalidades básicas...")
    
    # Setup do logger
    setup_production_logging()
    print("✅ Logger configurado")
    
    # Testar métrica
    metrics_collector.record_conversation_started("test", {"test": True})
    print("✅ Métrica registrada")
    
    # Testar alerta
    alert_manager.add_alert("test", "Sistema funcionando", "LOW", {"component": "test"})
    print("✅ Alerta criado")
    
    print("\n🚀 SISTEMA DE PRODUÇÃO TOTALMENTE FUNCIONAL!")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
