#!/bin/bash

# Script para organizar a estrutura do projeto WhatsApp Agent
# Organiza arquivos por categoria para manter a raiz limpa

set -e

echo "🧹 Organizando estrutura do projeto WhatsApp Agent"
echo "================================================="
echo ""

# Função para mover arquivo se existir
move_if_exists() {
    local source="$1"
    local target="$2"
    
    if [ -f "$source" ]; then
        echo "📁 Movendo: $source -> $target"
        mkdir -p "$(dirname "$target")"
        mv "$source" "$target"
    fi
}

# Navegar para raiz do projeto
cd "$(dirname "$0")"

echo "📋 Movendo documentação e relatórios..."
echo "======================================"

# Mover todos os relatórios markdown para documentation/
move_if_exists "ANALYTICS_INTEGRATION_REPORT.md" "documentation/reports/analytics-integration.md"
move_if_exists "API_CONTRACTS_REPORT.md" "documentation/reports/api-contracts.md"
move_if_exists "BACKUP_SYSTEM_REPORT.md" "documentation/reports/backup-system.md"
move_if_exists "CACHE_INVALIDATION_SISTEMA_COMPLETO.md" "documentation/reports/cache-invalidation-complete.md"
move_if_exists "E2E_TESTS_CRITICAL_IMPLEMENTATION.md" "documentation/reports/e2e-tests-implementation.md"
move_if_exists "ERROR_BOUNDARIES_IMPLEMENTADO_SUCESSO.md" "documentation/reports/error-boundaries-success.md"
move_if_exists "ERROR_RECOVERY_SISTEMA_COMPLETO.md" "documentation/reports/error-recovery-complete.md"
move_if_exists "MOBILE_RESPONSIVE_REPORT.md" "documentation/reports/mobile-responsive.md"
move_if_exists "PUSH_NOTIFICATIONS_COMPLETE.md" "documentation/reports/push-notifications-complete.md"
move_if_exists "PWA_IMPLEMENTATION_COMPLETE.md" "documentation/reports/pwa-implementation-complete.md"
move_if_exists "PWA_OFFLINE_IMPLEMENTATION_COMPLETE.md" "documentation/reports/pwa-offline-complete.md"
move_if_exists "RAILWAY_FIXES_REPORT.md" "documentation/reports/railway-fixes.md"
move_if_exists "RATE_LIMITING_IMPLEMENTADO_SUCESSO.md" "documentation/reports/rate-limiting-success.md"
move_if_exists "RBAC_SYSTEM_COMPLETE_FINAL.md" "documentation/reports/rbac-system-complete.md"
move_if_exists "REDIS_BCRYPT_FIXES_REPORT.md" "documentation/reports/redis-bcrypt-fixes.md"
move_if_exists "REDIS_RAILWAY_SETUP.md" "documentation/reports/redis-railway-setup.md"
move_if_exists "REFRESH_TOKENS_IMPLEMENTADO_SUCESSO.md" "documentation/reports/refresh-tokens-success.md"
move_if_exists "RELATORIO_COMPLETO_MELHORIAS.md" "documentation/reports/complete-improvements.md"
move_if_exists "REPORT_EXPORT_DOCUMENTATION.md" "documentation/reports/export-documentation.md"
move_if_exists "SISTEMA_ALERTAS_COMPLETADO.md" "documentation/reports/alert-system-complete.md"
move_if_exists "SQL_FIXES_REPORT.md" "documentation/reports/sql-fixes.md"
move_if_exists "SQL_N_PLUS_ONE_INTEGRATION_REPORT.md" "documentation/reports/sql-n-plus-one-integration.md"
move_if_exists "UNIFIED_ENDPOINTS_REPORT.md" "documentation/reports/unified-endpoints.md"
move_if_exists "PROXIMOS_PASSOS.md" "documentation/next-steps.md"

echo ""
echo "🧪 Movendo arquivos de teste..."
echo "==============================="

# Mover testes da raiz para testing/
move_if_exists "test_alert_system.py" "testing/test_alert_system.py"
move_if_exists "test_analytics_integration.sh" "testing/test_analytics_integration.sh"
move_if_exists "test_appointments_api.py" "testing/test_appointments_api.py"
move_if_exists "test_auth_service_basic.py" "testing/test_auth_service_basic.py"
move_if_exists "test_cache_implementation.py" "testing/test_cache_implementation.py"
move_if_exists "test_cache_invalidation.py" "testing/test_cache_invalidation.py"
move_if_exists "test_cors.py" "testing/test_cors.py"
move_if_exists "test_csp_production_final.py" "testing/test_csp_production_final.py"
move_if_exists "test_csp_production_railway.py" "testing/test_csp_production_railway.py"
move_if_exists "test_csp_security_complete.py" "testing/test_csp_security_complete.py"
move_if_exists "test_monitoring_dashboard.py" "testing/test_monitoring_dashboard.py"
move_if_exists "test_performance_indexes.py" "testing/test_performance_indexes.py"
move_if_exists "test_production_refresh_tokens.py" "testing/test_production_refresh_tokens.py"
move_if_exists "test_production_validation.py" "testing/test_production_validation.py"
move_if_exists "test_public_health.py" "testing/test_public_health.py"
move_if_exists "test_push_notifications.py" "testing/test_push_notifications.py"
move_if_exists "test_pwa_offline_complete.py" "testing/test_pwa_offline_complete.py"
move_if_exists "test_pwa_system.py" "testing/test_pwa_system.py"
move_if_exists "test_rate_limiting_practical.py" "testing/test_rate_limiting_practical.py"
move_if_exists "test_refresh_deployment.py" "testing/test_refresh_deployment.py"
move_if_exists "test_refresh_tokens_e2e.py" "testing/test_refresh_tokens_e2e.py"
move_if_exists "test_report_system.py" "testing/test_report_system.py"
move_if_exists "test_schema_corrections.py" "testing/test_schema_corrections.py"
move_if_exists "test_schema_synthetic.py" "testing/test_schema_synthetic.py"
move_if_exists "test_sql_ambiguity.py" "testing/test_sql_ambiguity.py"
move_if_exists "test_sql_fix.py" "testing/test_sql_fix.py"
move_if_exists "test_sql_n_plus_one_optimization.py" "testing/test_sql_n_plus_one_optimization.py"
move_if_exists "test_unified_schemas.py" "testing/test_unified_schemas.py"
move_if_exists "test_unified_system.py" "testing/test_unified_system.py"

echo ""
echo "🔧 Movendo utilitários e scripts..."
echo "==================================="

# Mover scripts utilitários para utilities/
move_if_exists "analyze_schema_inconsistencies.py" "utilities/analyze_schema_inconsistencies.py"
move_if_exists "analyze_specific_bugs.py" "utilities/analyze_specific_bugs.py"
move_if_exists "analyze_sql_bugs.py" "utilities/analyze_sql_bugs.py"
move_if_exists "apply_schema_corrections.py" "utilities/apply_schema_corrections.py"
move_if_exists "create_refresh_tokens_table.py" "utilities/create_refresh_tokens_table.py"
move_if_exists "demo_cache_invalidation.py" "utilities/demo_cache_invalidation.py"
move_if_exists "demo_rate_limiting.py" "utilities/demo_rate_limiting.py"
move_if_exists "demo_refresh_tokens.py" "utilities/demo_refresh_tokens.py"
move_if_exists "deploy_cors_fix.sh" "utilities/deploy_cors_fix.sh"
move_if_exists "final_refresh_demo.py" "utilities/final_refresh_demo.py"
move_if_exists "final_sql_corrections_report.py" "utilities/final_sql_corrections_report.py"
move_if_exists "fix_rbac_schema.py" "utilities/fix_rbac_schema.py"
move_if_exists "integrate_csp_security.py" "utilities/integrate_csp_security.py"
move_if_exists "integrate_sql_optimizations.py" "utilities/integrate_sql_optimizations.py"
move_if_exists "schema_corrections_report.py" "utilities/schema_corrections_report.py"
move_if_exists "run-critical-e2e-tests.sh" "utilities/run-critical-e2e-tests.sh"
move_if_exists "e2e-implementation-report.sh" "utilities/e2e-implementation-report.sh"
move_if_exists "INSTRUCOES_CORS.py" "utilities/INSTRUCOES_CORS.py"

echo ""
echo "📦 Movendo arquivos temporários..."
echo "=================================="

# Mover arquivos temporários e de teste para temp/
move_if_exists "csp_production_test_results.json" "temp/csp_production_test_results.json"
move_if_exists "csp_security_test_results.json" "temp/csp_security_test_results.json"
move_if_exists "pwa_offline_test_results.json" "temp/pwa_offline_test_results.json"
move_if_exists "jwt-race-condition-demo.js" "temp/jwt-race-condition-demo.js"
move_if_exists "realtime-updates-demo.js" "temp/realtime-updates-demo.js"
move_if_exists "test.db" "temp/test.db"
move_if_exists "test_refresh_tokens.db" "temp/test_refresh_tokens.db"
move_if_exists "whatsapp_agent.db" "temp/whatsapp_agent.db"

echo ""
echo "🏗️ Ajustando estrutura de pastas existentes..."
echo "=============================================="

# Mover pasta temp_reports se existir
if [ -d "temp_reports" ]; then
    echo "📁 Movendo: temp_reports/ -> temp/reports/"
    mkdir -p temp/
    mv temp_reports temp/reports
fi

echo ""
echo "📄 Criando arquivo de estrutura..."
echo "=================================="

# Criar arquivo README da nova estrutura
cat > "PROJECT_STRUCTURE.md" << 'EOF'
# 📁 Estrutura do Projeto WhatsApp Agent

## 🏗️ Organização Limpa e Profissional

```
whats_agent/
├── 📱 **APLICAÇÃO PRINCIPAL**
│   ├── app/                     # Backend FastAPI
│   ├── nextjs_dashboard/        # Frontend Next.js
│   ├── alembic/                # Migrações de banco
│   └── config/                 # Configurações
│
├── 📚 **DOCUMENTAÇÃO**
│   ├── documentation/
│   │   ├── reports/           # Relatórios de implementação
│   │   └── next-steps.md      # Próximos passos
│   └── docs/                  # Documentação técnica
│
├── 🧪 **TESTES**
│   ├── testing/               # Testes da raiz organizados
│   ├── tests/                 # Suite principal de testes
│   └── pytest.ini            # Configuração pytest
│
├── 🔧 **UTILITÁRIOS**
│   ├── utilities/             # Scripts e ferramentas
│   ├── scripts/              # Scripts de automação
│   └── backups/              # Backups do sistema
│
├── 🐳 **INFRAESTRUTURA**
│   ├── docker-compose.yml     # Containers
│   ├── Dockerfile            # Imagem Docker
│   ├── prometheus/           # Monitoring
│   └── logs/                 # Arquivos de log
│
├── 📦 **TEMPORÁRIOS**
│   └── temp/                 # Arquivos temporários
│       ├── reports/          # Relatórios antigos
│       └── *.db             # Bancos de teste
│
└── 🔐 **CONFIGURAÇÕES**
    ├── .env                  # Variáveis de ambiente
    ├── requirements.txt      # Dependências Python
    ├── pyproject.toml       # Configuração do projeto
    └── README.md            # Documentação principal
```

## 🎯 Benefícios da Reorganização

### ✅ **Raiz Limpa**
- Apenas arquivos essenciais na raiz
- Fácil navegação e entendimento
- Estrutura profissional

### ✅ **Categorização Clara**
- **documentation/**: Todos os relatórios e docs
- **testing/**: Testes organizados por tipo
- **utilities/**: Scripts e ferramentas
- **temp/**: Arquivos temporários isolados

### ✅ **Manutenção Simplificada**
- Localização rápida de arquivos
- Separação clara de responsabilidades
- Facilita colaboração em equipe

## 🚀 Como Usar a Nova Estrutura

### Executar Aplicação:
```bash
# Backend
python -m app.main

# Frontend
cd nextjs_dashboard && npm run dev
```

### Executar Testes:
```bash
# Testes principais
pytest tests/

# Testes específicos
python testing/test_appointments_api.py
```

### Utilitários:
```bash
# Scripts organizados
./utilities/run-critical-e2e-tests.sh
python utilities/analyze_schema_inconsistencies.py
```

### Documentação:
```bash
# Consultar relatórios
ls documentation/reports/
cat documentation/next-steps.md
```

---

**Status:** ✅ **ESTRUTURA ORGANIZADA E LIMPA**  
**Atualizado:** 9 de setembro de 2025
EOF

echo ""
echo "🎉 ORGANIZAÇÃO CONCLUÍDA!"
echo "========================"
echo ""
echo "✅ Documentação: documentation/"
echo "✅ Testes: testing/"  
echo "✅ Utilitários: utilities/"
echo "✅ Temporários: temp/"
echo "✅ Estrutura documentada: PROJECT_STRUCTURE.md"
echo ""
echo "📁 Nova estrutura criada com sucesso!"
echo "🧹 Raiz do projeto agora está limpa e organizada!"
echo ""

# Mostrar estrutura resultante
echo "📂 Estrutura atual da raiz:"
echo "=========================="
ls -la | grep -E '^(d|-)' | awk '{print $9}' | grep -v '^\.$' | grep -v '^\.\.$' | head -20

echo ""
echo "🎯 Próximos comandos sugeridos:"
echo "=============================="
echo "git add ."
echo "git commit -m 'feat: organizar estrutura do projeto'"
echo "git push"
echo ""
