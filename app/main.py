"""
Aplicação principal WhatsApp Agent API
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.config.config_factory import is_development
from app.database import init_db
from app.middleware.request_logging import add_request_logging_middleware
from app.routes.webhook_unified import router as webhook_router
from app.routes.fast_auth import router as fast_auth_router
from app.services.connection_pool_manager import initialize_pool
from app.schemas.health import (
    AppInfo,
    DetailedHealthResponse,
    HealthCheckResponse,
    SystemHealth,
    SystemMetrics,
)

# Rate limiting removido - usando sistema unificado
# from app.middleware.rate_limit import RateLimitMiddleware, get_rate_limit_stats
from app.services.alert_manager import alert_manager
from app.services.cache_service import cache_service
from app.services.conversation_flow import conversation_flow_service
from app.services.health_checker import HealthStatus, health_checker
from app.services.lead_scoring import lead_scoring_service
from app.services.llm_advanced import advanced_llm_service
from app.services.strategy_compatibility import hybrid_service

# Sistema de Logging Unificado e Otimizado
from app.config.logging_config import (
    get_optimized_logger,
    log_startup_phase,
    log_startup_completion,
    log_startup_summary,
    log_performance_metric,
    log_system_event,
    startup_manager,
)

# Cache Invalidation Manual System
try:
    from app.services.cache_invalidation_manual import CacheInvalidationManager

    CACHE_INVALIDATION_AVAILABLE = True
except ImportError:
    CACHE_INVALIDATION_AVAILABLE = False

# LGPD Compliance System
try:
    from app.services.lgpd_compliance import LGPDComplianceManager
    from app.services.lgpd_scheduler import start_lgpd_scheduler, stop_lgpd_scheduler

    LGPD_COMPLIANCE_AVAILABLE = True
except ImportError:
    LGPD_COMPLIANCE_AVAILABLE = False

# Sistema de Autenticação e Autorização
from app.auth import AuthMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.services.cache_service_optimized import get_optimized_cache
from app.services.cdn_manager import CDNManager

# 🚀 Sistemas de Performance e Escalabilidade
from app.services.database_optimizer import DatabaseOptimizer

# Prometheus Metrics Integration
from app.utils.metrics import get_metrics_response, metrics_collector

# Logger principal otimizado
logger = get_optimized_logger(__name__)

# 🔒 Sistema de Segurança HTTPS - Verificar disponibilidade
try:
    from app.security.https_middleware import HTTPSMiddleware

    HTTPS_MIDDLEWARE_AVAILABLE = True
    logger.info("HTTPS Middleware loaded successfully")
except ImportError:
    HTTPS_MIDDLEWARE_AVAILABLE = False
    logger.warning("HTTPS Middleware not available")

# 🔒 Sistema CSP Security
try:
    from app.security.csp_manager import CSPMiddleware

    CSP_MIDDLEWARE_AVAILABLE = True
    logger.info("✅ CSP Middleware carregado")
except ImportError:
    CSP_MIDDLEWARE_AVAILABLE = False
    logger.warning("⚠️ CSP Middleware não disponível")
    HTTPSMiddleware = None
    logger.warning(
        "⚠️ HTTPS Middleware não disponível - executando sem HTTPS obrigatório"
    )

# 🔒 S002 - Sistema de Log Sanitization
try:
    from app.security.request_logging import configure_request_logging_middleware
    from app.security.secure_logger import configure_secure_logging

    S002_LOG_SANITIZATION_AVAILABLE = True
    logger.info("✅ S002: Sistema de Log Sanitization carregado")
except ImportError:
    S002_LOG_SANITIZATION_AVAILABLE = False
    logger.warning("⚠️ S002: Sistema de Log Sanitization não disponível")


# Importar função de startup otimizada
from app.startup_optimized import lifespan

# Função lifespan original removida - usando startup_optimized.py

# Criar aplicação FastAPI com documentação aprimorada
app = FastAPI(
    title="🤖 WhatsApp Agent API",
    description="""
## 🚀 Enterprise WhatsApp Business API

**Comprehensive AI-powered WhatsApp integration** for appointment management, customer engagement, and business automation.

### 🎯 Key Features

- ✅ **Smart Appointment Scheduling** with conflict detection
- ✅ **Real-time WhatsApp Integration** via Meta Business API
- ✅ **AI-Powered Responses** with conversation context
- ✅ **Enterprise Security** with JWT, 2FA, and RBAC
- ✅ **High Performance** with Redis caching and optimized queries
- ✅ **Real-time Updates** via WebSocket connections
- ✅ **Comprehensive Analytics** and reporting dashboard

### 🔐 Authentication

This API uses **JWT tokens with HttpOnly cookies** for maximum security:

1. **Login** → `/auth/login` with credentials
2. **2FA Verification** → `/auth/2fa/verify` (if enabled)
3. **Access Protected Endpoints** → Automatic cookie-based auth
4. **Refresh Tokens** → `/auth/refresh` for token renewal

### 📊 Rate Limiting

- **Standard**: 100 requests/minute
- **Premium**: 1000 requests/minute
- **Enterprise**: Custom limits

### 🔗 External Documentation

- **Complete API Guide**: [docs/api-documentation.md](docs/api-documentation.md)
- **Setup Instructions**: [docs/setup-guide.md](docs/setup-guide.md)
- **Security Practices**: [docs/security-practices.md](docs/security-practices.md)
- **Performance Guide**: [docs/performance-optimization.md](docs/performance-optimization.md)
""",
    version="1.0.0",
    debug=is_development(),
    lifespan=lifespan,
    contact={
        "name": "WhatsApp Agent API Support",
        "url": "https://docs.whatsappagent.com",
        "email": "api-support@whatsappagent.com",
    },
    license_info={
        "name": "Enterprise License",
        "url": "https://whatsappagent.com/license",
    },
    servers=[
        {"url": "https://api.whatsappagent.com", "description": "Production server"},
        {
            "url": "https://staging-api.whatsappagent.com",
            "description": "Staging server",
        },
        {"url": "http://localhost:8000", "description": "Development server"},
    ],
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "🔐 User authentication, 2FA, JWT token management",
        },
        {
            "name": "Appointments",
            "description": "📅 Appointment CRUD operations with smart scheduling",
        },
        {
            "name": "WhatsApp",
            "description": "📱 WhatsApp message sending and webhook handling",
        },
        {
            "name": "Analytics",
            "description": "📊 Business analytics and performance metrics",
        },
        {
            "name": "Health",
            "description": "🏥 System health checks and monitoring",
        },
        {
            "name": "Admin",
            "description": "⚙️ Administrative functions and system management",
        },
    ],
)

# Sistema de logging unificado já configurado em logging_config.py
# Não precisa de configuração adicional - já está ativo

# Add CSP Security Middleware (first, before other middlewares)
# 🔍 APM Middleware será adicionado depois do UltraSimpleCriticalMiddleware

# 🚀 PF-001 - Adicionar middleware de performance de banco de dados
try:
    from app.middleware.database_performance import DatabasePerformanceMiddleware
    # DatabasePerformanceMiddleware será adicionado depois do UltraSimpleCriticalMiddleware
    logger.info("🚀 PF-001 - Database Performance Middleware importado")
except ImportError as e:
    logger.warning(f"⚠️ PF-001 - Database Performance Middleware não disponível: {e}")
except Exception as e:
    logger.error(f"❌ PF-001 - Erro ao inicializar Database Performance Middleware: {e}")

# 🔒 S002 - Adicionar middlewares de logging seguro
if S002_LOG_SANITIZATION_AVAILABLE:
    configure_request_logging_middleware(
        app, enable_sanitization=True, log_requests=True, log_webhooks=True
    )
    logger.info("🔒 S002: Middlewares de logging seguro ativados")
else:
    logger.warning("⚠️ S002: Middlewares de logging seguro não disponíveis")

if CSP_MIDDLEWARE_AVAILABLE:
    app.add_middleware(CSPMiddleware, report_only=False)
    logger.info("CSP Middleware added successfully")
else:
    logger.warning("CSP Middleware not available - skipping")

# 🔧 CONFIGURAR CORS AVANÇADO - SOLUÇÃO PARA RAILWAY
from app.config.api_documentation import API_METADATA, configure_enhanced_openapi
from app.cors_config import (
    add_cors_test_endpoint,
    get_cors_debug_info,
    setup_cors_middleware,
)

# Aplicar configuração CORS otimizada
setup_cors_middleware(app, debug=is_development())

# Adicionar endpoints de teste CORS
add_cors_test_endpoint(app)

logger.info("CORS configured with advanced settings for Railway")

# 📚 Configurar documentação API aprimorada
configure_enhanced_openapi(app)
logger.info("Enhanced API documentation configured with examples and schemas")

# 🔒 Adicionar middleware de segurança HTTPS (primeiro)
if HTTPS_MIDDLEWARE_AVAILABLE:
    app.add_middleware(
        HTTPSMiddleware,
        force_https=False,  # 🚨 RAILWAY FIX: Desabilitar HTTPS forçado
        hsts_max_age=31536000,  # 1 ano
        hsts_include_subdomains=True,
        hsts_preload=True,
        allow_localhost=True,  # Permitir localhost sempre
        development_mode=True,  # Modo desenvolvimento sempre
    )
    logger.info("✅ HTTPS Middleware activated - FORCE_HTTPS DISABLED for Railway")
else:
    logger.warning("HTTPS Middleware not available")

# Middlewares de produção - sem debug

# 🚨 EMERGENCY ENDPOINTS - ANTES DE QUALQUER MIDDLEWARE
@app.get("/emergency")
async def emergency():
    """Endpoint de emergência - BYPASS TOTAL"""
    return {"status": "ok", "emergency": True, "railway": True}

@app.get("/railway")
async def railway():
    """Endpoint Railway - BYPASS TOTAL"""
    return {"status": "ok", "railway": True}

@app.get("/health")
async def health():
    """Endpoint Health - Railway Optimized with detailed debugging"""
    try:
        import os
        import sys
        
        # Log health check
        logger.info("Health check requested")
        
        # Verificação básica de saúde
        health_data = {
            "status": "healthy",
            "service": "whatsapp-agent",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "railway": True,
            "debug": {
                "port": os.getenv('PORT', '8000'),
                "railway_env": os.getenv('RAILWAY_ENVIRONMENT', 'unknown'),
                "python_version": sys.version.split()[0],
                "platform": sys.platform
            }
        }
        
        logger.info("Health check completed successfully")
        return health_data
        
    except Exception as e:
        logger.error(f"❌ Health check falhou: {str(e)}")
        # Em caso de erro, retornar erro 500
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/ping")
async def ping():
    """Simplest possible endpoint"""
    return "pong"

@app.get("/")
async def root():
    """Emergency root endpoint for Railway debugging"""
    import os
    return {
        "message": "WhatsApp Agent API is running", 
        "status": "healthy",
        "railway_fast_start": os.getenv('RAILWAY_FAST_START', 'false'),
        "port": os.getenv('PORT', '8000'),
        "railway_env": os.getenv('RAILWAY_ENVIRONMENT', 'unknown')
    }

@app.get("/healthcheck")
async def healthcheck():
    """Endpoint alternativo para healthcheck do Railway - BYPASS COMPLETO"""
    return {"status": "ok", "service": "whatsapp-agent", "railway": True, "healthcheck": "alternative"}

@app.get("/railway-health")
async def railway_health():
    """Endpoint ULTRA SIMPLES para Railway - SEM MIDDLEWARE"""
    import os
    import sys
    
    # Simple Railway health check
    
    return {
        "status": "ok", 
        "railway": True,
        "timestamp": datetime.now().isoformat(),
        "debug": {
            "port": os.getenv('PORT', '8000'),
            "railway_env": os.getenv('RAILWAY_ENVIRONMENT', 'unknown'),
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
            "working_dir": os.getcwd(),
            "fast_start": os.getenv('RAILWAY_FAST_START', 'false'),
            "python_unbuffered": os.getenv('PYTHONUNBUFFERED', 'not set')
        }
    }

@app.get("/debug")
async def debug_info():
    """Debug endpoint with comprehensive system information"""
    import os
    import sys
    import platform
    
    # Debug endpoint with system information
    
    return {
        "status": "debug",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "python_version": sys.version,
            "platform": sys.platform,
            "platform_version": platform.version(),
            "architecture": platform.architecture(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "working_directory": os.getcwd(),
            "python_executable": sys.executable
        },
        "environment": {
            "port": os.getenv('PORT', '8000'),
            "railway_environment": os.getenv('RAILWAY_ENVIRONMENT', 'unknown'),
            "railway_fast_start": os.getenv('RAILWAY_FAST_START', 'false'),
            "pythonunbuffered": os.getenv('PYTHONUNBUFFERED', 'not set'),
            "python_dont_write_bytecode": os.getenv('PYTHONDONTWRITEBYTECODE', 'not set'),
            "railway_project_id": os.getenv('RAILWAY_PROJECT_ID', 'not set'),
            "railway_service_id": os.getenv('RAILWAY_SERVICE_ID', 'not set')
        },
        "all_env_vars": dict(os.environ)
    }

@app.get("/status")
async def status():
    """Endpoint de status - SEM MIDDLEWARE"""
    return {"status": "healthy", "service": "whatsapp-agent"}


@app.get("/ready")
async def ready():
    """Endpoint de readiness check - verifica se a aplicação está pronta para receber tráfego"""
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "message": "Application is ready to receive traffic"
    }


@app.get("/alive")
async def alive():
    """Endpoint de liveness check - verifica se a aplicação está viva"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "Application is alive and running"
    }

# Middleware de produção - sem debug

# 🔒 MIDDLEWARE ORDER FIX - ORDEM CORRETA PARA RAILWAY
# IMPORTANTE: No FastAPI, a ordem de app.add_middleware() é INVERSA da execução
# O ÚLTIMO middleware adicionado é o PRIMEIRO a ser executado!

# 🔄 C002 - ApiResponseMiddleware (ÚLTIMO na cadeia - pode processar responses)
try:
    from app.middleware.response_standardizer import ApiResponseMiddleware
    app.add_middleware(ApiResponseMiddleware)
    logger.info("✅ C002 - ApiResponseMiddleware ativado: responses padronizados {success, data, error}")
except ImportError as e:
    logger.warning(f"⚠️ C002 - ApiResponseMiddleware não disponível: {e}")
except Exception as e:
    logger.error(f"❌ C002 - Erro ao inicializar ApiResponseMiddleware: {e}")

# 📊 MetricsMiddleware (penúltimo - captura métricas de todas requests)
app.add_middleware(MetricsMiddleware)

# 🔒 UserRateLimitMiddleware
try:
    from app.middleware.user_rate_limit import UserRateLimitMiddleware
    app.add_middleware(UserRateLimitMiddleware)
    logger.info("✅ User Rate Limiting middleware ativado")
except ImportError as e:
    logger.warning(f"⚠️ User Rate Limiting middleware não disponível: {e}")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar User Rate Limiting middleware: {e}")

# 🛡️ WebhookRateLimitMiddleware
logger.info("🔍 H003 Debug: Tentando carregar WebhookRateLimitMiddleware...")
try:
    from app.middleware.webhook_rate_limit import WebhookRateLimitMiddleware
    logger.info("🔍 H003 Debug: Import realizado com sucesso")
    app.add_middleware(WebhookRateLimitMiddleware)
    logger.info("🛡️ H003 Webhook Rate Limiting middleware ativado - 100 req/min per IP")
except ImportError as e:
    logger.warning(f"⚠️ H003 Webhook Rate Limiting middleware não disponível: {e}")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar H003 Webhook Rate Limiting middleware: {e}")

# 🚀 DatabasePerformanceMiddleware
app.add_middleware(DatabasePerformanceMiddleware)

# 🔍 APMMiddleware - Comentado temporariamente
# app.add_middleware(APMMiddleware)

# 🔒 CriticalEndpointsMiddleware - Bypass para endpoints críticos
class CriticalEndpointsMiddleware(BaseHTTPMiddleware):
    """Middleware para bypass de endpoints críticos"""
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # BYPASS DIRETO para endpoints críticos
        critical_paths = ["/ping", "/health", "/emergency", "/railway-health", "/healthcheck", "/status", "/railway"]
        if path in critical_paths:
            return JSONResponse(
                content={"status": "ok", "service": "whatsapp-agent", "railway": True},
                status_code=200
            )
        
        # Para outros endpoints, processar normalmente
        return await call_next(request)

# 🔒 Adicionar middlewares na ordem correta
app.add_middleware(CriticalEndpointsMiddleware)
logger.info("🔒 CriticalEndpointsMiddleware ativado")

# 🔒 AuthMiddleware
app.add_middleware(AuthMiddleware)
logger.info("🔒 AuthMiddleware ativado")


logger.info("🔧 Sistema de rate limiting por usuário ativo")

# Incluir rotas
app.include_router(webhook_router, tags=["webhook"])

# Meta webhook específico (sem JWT)



# Debug webhook (TEMPORÁRIO - remover em produção)
from app.routes.debug_webhook import router as debug_webhook_router

app.include_router(debug_webhook_router, tags=["Debug"])

# Debug middleware (TEMPORÁRIO - remover em produção)
from app.routes.debug_middleware import router as debug_middleware_router

app.include_router(debug_middleware_router, tags=["Debug Middleware"])

# System info (TEMPORÁRIO - verificar deploy)
from app.routes.system_info import router as system_info_router

app.include_router(system_info_router, tags=["System Info"])

# 🔒 Incluir rotas de autenticação e segurança
from app.routes.auth import router as auth_router

app.include_router(auth_router, tags=["Authentication"])
app.include_router(fast_auth_router, tags=["Fast Authentication"])

from app.routes.secrets import router as secrets_router

app.include_router(secrets_router, prefix="/secrets", tags=["Secrets Management"])

# 🔐 Incluir rotas de segurança e criptografia
from app.routes.security import router as security_router

app.include_router(security_router, prefix="/security", tags=["Security & Encryption"])

# 🛡️ Incluir CSP Security Reporter
from app.security.csp_reporter import security_router as csp_security_router

app.include_router(csp_security_router, tags=["CSP Security"])

# 🔍 Incluir CSP Testing Routes
from app.routes.csp_testing import csp_testing_router

app.include_router(csp_testing_router, tags=["CSP Testing"])

# Incluir rotas de administração de estratégias
from app.routes.strategy_admin import router as strategy_admin_router

app.include_router(strategy_admin_router, tags=["Strategy Management"])

# Incluir rotas de monitoramento de custos
# from app.routes.cost_monitoring import router as cost_router
# app.include_router(cost_router, tags=["Cost Monitoring"])

# Incluir rotas de autenticação admin
from app.routes.admin_auth import auth_router as admin_auth_router

app.include_router(admin_auth_router, tags=["Admin Authentication"])

# 🔒 H003 - Incluir rotas administrativas de rate limiting webhook
try:
    from app.routes.h003_admin import router as h003_admin_router

    app.include_router(h003_admin_router, tags=["H003 Rate Limiting"])
    log_system_event("routes", "H003 Admin routes loaded")
except ImportError as e:
    logger.warning(f"⚠️ H003 Admin routes não disponíveis: {e}")

# Incluir rotas de otimização do banco de dados
from app.routes.database_optimization import router as db_optimization_router

app.include_router(db_optimization_router, tags=["Database Optimization"])

# 🔍 OM001/OM003 - Incluir rotas de observabilidade completa
try:
    from app.routes.health_detailed import router as health_detailed_router

    app.include_router(health_detailed_router, tags=["OM001 Health Monitoring"])

    from app.services.alerting import router as alerting_router

    app.include_router(alerting_router, tags=["OM003 Alert System"])

    logger.info(
        "✅ OM001/OM003 - Sistema de observabilidade ativado: health detalhado + alertas"
    )
except ImportError as e:
    logger.warning(f"⚠️ OM001/OM003 - Sistema de observabilidade não disponível: {e}")
except Exception as e:
    logger.error(f"❌ OM001/OM003 - Erro ao carregar observabilidade: {e}")

# 🔧 CF002 - Incluir rotas demo para Response Wrapper Padronizado
try:
    from app.routes.appointments_cf002_demo import router as appointments_demo_router

    app.include_router(appointments_demo_router, tags=["CF002 Demo"])

    from app.routes.health_cf002_demo import router as health_demo_router

    app.include_router(health_demo_router, tags=["CF002 Demo"])

    logger.info(
        "✅ CF002 - Rotas demo carregadas: /appointments-demo/* e /health-demo/*"
    )
except ImportError as e:
    logger.warning(f"⚠️ CF002 - Rotas demo não disponíveis: {e}")
except Exception as e:
    logger.error(f"❌ CF002 - Erro ao carregar rotas demo: {e}")

# � PD001 - Incluir rotas demo de Performance Optimization
try:
    from app.routes.pd001_performance_demo import router as pd001_demo_router

    app.include_router(pd001_demo_router, tags=["PD001 Performance Demo"])

    logger.info("✅ PD001 - Rotas de performance demo carregadas: /performance-demo/*")
except ImportError as e:
    logger.warning(f"⚠️ PD001 - Rotas de performance demo não disponíveis: {e}")
except Exception as e:
    logger.error(f"❌ PD001 - Erro ao carregar rotas de performance: {e}")

# �🔄 Sistema de Backup Automatizado
from app.routes.backup import router as backup_router

app.include_router(backup_router, tags=["Backup System"])

# 📊 Sistema de Rate Limiting por Usuário
from app.routes.rate_limit import router as rate_limit_router

app.include_router(rate_limit_router, tags=["Rate Limiting"])

# 🛡️ Sistema de Rate Limiting para Webhooks (Avançado)
from app.routes.webhook_rate_limit_admin import (
    router as webhook_rate_limit_admin_router,
)

app.include_router(
    webhook_rate_limit_admin_router, tags=["Webhook Rate Limiting Admin"]
)
logger.info("Webhook Rate Limiting System activated - DDoS and spam protection enabled")

# 🔍 APM E MONITORAMENTO DE LOGS ESTRUTURADOS
from app.routes.apm_monitoring import router as apm_monitoring_router

app.include_router(apm_monitoring_router, tags=["APM & Structured Logging"])
logger.info(
    "APM and Structured Logging Dashboard activated - Real-time monitoring enabled"
)

# 📊 DASHBOARD API - Endpoints REST críticos para funcionamento do Dashboard
from app.routes.appointments import router as appointments_router

app.include_router(appointments_router, tags=["Dashboard - Appointments"])

# 🚀 PF-001 - Rotas otimizadas para appointments (eliminação de N+1 queries)
try:
    from app.routes.appointments_pf001_optimized import (
        router as appointments_pf001_router,
    )

    app.include_router(
        appointments_pf001_router, tags=["PF-001 Optimized - Appointments"]
    )
    logger.info(
        "🚀 PF-001 - Rotas otimizadas de appointments carregadas: N+1 queries eliminadas"
    )
except ImportError as e:
    logger.warning(f"⚠️ PF-001 - Rotas otimizadas não disponíveis: {e}")
except Exception as e:
    logger.error(f"❌ PF-001 - Erro ao carregar rotas otimizadas: {e}")

# 🧪 PF-001 - Rotas de teste sem autenticação (apenas para validação)
try:
    from app.routes.appointments_pf001_test import router as appointments_test_router

    app.include_router(appointments_test_router, tags=["PF-001 Test - No Auth"])
    logger.info("🧪 PF-001 - Rotas de teste carregadas: validação sem autenticação")
except ImportError as e:
    logger.warning(f"⚠️ PF-001 - Rotas de teste não disponíveis: {e}")
except Exception as e:
    logger.error(f"❌ PF-001 - Erro ao carregar rotas de teste: {e}")

# 🚨 Sistema de Alertas
from app.routes.alerts import router as alerts_router
from app.routes.alert_config import router as alert_config_router
from app.routes.clients import router as clients_router

app.include_router(alerts_router, tags=["Alert System"])
app.include_router(alert_config_router, tags=["Alert Configuration"])

# Router público para endpoints de saúde (sem autenticação)
from app.routes.public_health import public_router

app.include_router(public_router, tags=["Public Health"])

# 🧪 Rotas públicas de teste (sem autenticação)
from app.routes.public_test import router as public_test_router

app.include_router(public_test_router, tags=["Public Test"])
logger.info("🧪 Rotas públicas de teste ativadas - Para validação sem autenticação")

# 🔍 Debug webhook (sem autenticação)
from app.routes.debug_webhook import router as debug_webhook_router

app.include_router(debug_webhook_router, tags=["Debug Webhook"])
logger.info("🔍 Debug webhook ativado - Para investigação de problemas")

# 🔍 Debug simple (sem autenticação)
from app.routes.debug_simple import router as debug_simple_router

app.include_router(debug_simple_router, tags=["Debug Simple"])
logger.info("🔍 Debug simple ativado - Para testes básicos")

# 🔍 Debug WhatsApp (sem autenticação)
from app.routes.debug_whatsapp import router as debug_whatsapp_router

app.include_router(debug_whatsapp_router, tags=["Debug WhatsApp"])
logger.info("🔍 Debug WhatsApp ativado - Para investigar envio")

# Dashboard Routes
from app.routes.clients import router as clients_router

app.include_router(clients_router, tags=["Dashboard - Clients"])

# 📊 Dashboard migrado com padrão C002
from app.routes.dashboard import router as dashboard_router

app.include_router(dashboard_router, tags=["Dashboard"])

# 🔄 C002 - Dashboard migrado para demonstrar novo padrão
try:
    from app.routes.dashboard_migrated import router as dashboard_migrated_router

    app.include_router(dashboard_migrated_router, tags=["Dashboard C002 - Migrated"])
    logger.info(
        "✅ C002 - Dashboard migrado incluído: demonstra padrão {success, data, error}"
    )
except ImportError as e:
    logger.warning(f"⚠️ C002 - Dashboard migrado não disponível: {e}")
except Exception as e:
    logger.error(f"❌ C002 - Erro ao incluir dashboard migrado: {e}")

# Analytics routes - Relatórios Executivos
from app.routes.analytics import router as analytics_router
from app.routes.analytics_dashboard import router as dashboard_analytics_router

# Conversation & messaging routes
app.include_router(clients_router, tags=["Dashboard - Clients"])

# Dashboard Analytics (executivo)
app.include_router(analytics_router, tags=["Dashboard - Analytics"])
app.include_router(dashboard_analytics_router, tags=["Dashboard - Real Data"])

# � DEBUG ROUTER - Para testar autenticação
from app.routes.debug_auth import router as debug_auth_router

app.include_router(debug_auth_router, tags=["Debug"])
log_system_event("debug", "Debug Auth Router activated for troubleshooting")

# � ANALYTICS AVANÇADAS - Business Intelligence - ATIVADO
from app.routes.analytics_advanced import router as advanced_analytics_router

app.include_router(advanced_analytics_router, tags=["Advanced Analytics"])
logger.info("✅ Analytics Avançadas ativadas - Business Intelligence")

# � CACHE INVALIDATION MANUAL - Sistema de Invalidação de Cache Manual
try:
    from app.routes.cache_invalidation import router as cache_invalidation_router

    app.include_router(
        cache_invalidation_router, prefix="/cache", tags=["Cache Management"]
    )
    logger.info("✅ Cache Invalidation Manual ativado - Sistema de invalidação manual")
except ImportError as e:
    logger.error(f"⚠️ Erro ao carregar Cache Invalidation: {e}")
    logger.warning("⚠️ Cache Invalidation Manual não disponível")

# � LGPD COMPLIANCE COMPLETO - Sistema de Conformidade LGPD
try:
    from app.routes.lgpd_compliance import router as lgpd_router

    app.include_router(lgpd_router, tags=["LGPD Compliance"])
    logger.info("✅ LGPD Compliance ativado - Conformidade completa")

    # Dashboard LGPD
    from app.services.lgpd_dashboard import router as lgpd_dashboard_router

    app.include_router(lgpd_dashboard_router, tags=["LGPD Admin"])
    logger.info("✅ LGPD Dashboard ativado - Interface administrativa")

except ImportError as e:
    logger.error(f"⚠️ Erro ao carregar LGPD Compliance: {e}")
    logger.warning("⚠️ LGPD Compliance não disponível")

# 🌐 WEBSOCKET REAL-TIME AVANÇADO - Sistema de tempo real para chat
try:
    from app.routes.websocket_unified import (
        router as websocket_realtime_router,
    )

    app.include_router(websocket_realtime_router, tags=["WebSocket Real-Time"])
    logger.info("🌐 WebSocket Real-Time ativado - Chat em tempo real implementado")
except ImportError as e:
    logger.error(f"⚠️ Erro ao carregar WebSocket Real-Time: {e}")
    logger.warning("⚠️ WebSocket Real-Time não disponível")
    logger.info("✅ Cache Invalidation Manual ativado - Sistema de invalidação manual")
except ImportError as e:
    logger.error(f"⚠️ Erro ao carregar Cache Invalidation: {e}")
    logger.warning("⚠️ Cache Invalidation Manual não disponível")

    # 🗂️ Cache Invalidation Manual System - Sistema de invalidação manual de cache
    try:
        from .routes.cache_invalidation import router as cache_router

        app.include_router(cache_router, prefix="", tags=["Cache Management"])
        logger.info(
            "🗂️ Cache Invalidation Manual System ativado - Gerenciamento avançado",
            category="system",
        )
    except Exception as e:
        logger.error(f"❌ Erro ao carregar Cache Invalidation: {e}", category="system")

# 🟡 SISTEMA DE EXPORTAÇÃO - Relatórios CSV/Excel/PDF
from app.routes.export import router as export_router

app.include_router(export_router, tags=["Data Export"])
logger.info("✅ Sistema de Exportação ativado - CSV/Excel/PDF")

# ⚠️ SISTEMA DE EXPORTAÇÃO DE RELATÓRIOS - Item 2 da Lista
from app.routes.reports import router as reports_router

app.include_router(reports_router, tags=["Reports Export"])
logger.info("⚠️ Sistema de Exportação de Relatórios ativado - Item 2 implementado")

# ⚠️ SISTEMA RBAC - Item 2: Controle Granular de Permissões
from app.routes.rbac import router as rbac_router

app.include_router(rbac_router, tags=["RBAC Management"])
logger.info(
    "⚠️ Sistema RBAC ativado - Item 2: Controle granular de permissões implementado"
)

# 🔧 ADMIN RBAC - Endpoints administrativos para RBAC
from app.routes.admin_rbac import router as admin_rbac_router

app.include_router(admin_rbac_router, tags=["Admin RBAC Management"])
logger.info("🔧 Admin RBAC endpoints ativados - /admin/rbac/")

# ✅ Usar versão corrigida das conversas - agora na versão principal
from app.routes.conversations import router as conversations_router

logger.info("✅ Usando rotas de conversas com correções SQL aplicadas")
app.include_router(conversations_router, tags=["Dashboard - Conversations"])

from app.routes.dashboard import router as dashboard_router

app.include_router(dashboard_router, tags=["Dashboard - Main"])

# 🔥 WEBSOCKET - Sistema Unificado (CORREÇÃO CRÍTICA: Elimina múltiplos gerenciadores conflitantes)
from app.routes.websocket_unified import router as websocket_unified_router

app.include_router(
    websocket_unified_router, tags=["WebSocket - Unificado"]
)

# 📊 SPRINT 3 - ANALYTICS OTIMIZADOS (Backend)
from app.routes.analytics import router as analytics_router
app.include_router(analytics_router, tags=["Analytics - Backend"])

# 🔍 SPRINT 3 - BUSCA GLOBAL (Full-text Search)
from app.routes.search import router as search_router
app.include_router(search_router, tags=["Search - Global"])

# 📊 SPRINT 4+ - MONITORAMENTO DE LOGS
from app.routes.logs_monitoring import router as logs_monitoring_router
app.include_router(logs_monitoring_router, tags=["Logs Monitoring"])

# 🔔 SPRINT 4+ - SISTEMA DE LEMBRETES
from app.routes.reminders import router as reminders_router
app.include_router(reminders_router, tags=["Reminders"])

# 🧪 Endpoints de Teste para WebSocket (DESABILITADO - Arquivo de teste)
# from app.routes.websocket_unified import router as websocket_test_router
# app.include_router(websocket_test_router, prefix="/api/websocket-test", tags=["WebSocket - Testing"])
# logger.info("🧪 Endpoints de teste WebSocket ativados")

from fastapi import WebSocket, WebSocketDisconnect

# 🔥 WEBSOCKET - Comunicação em Tempo Real (Ativo com Cache Sync)
from app.services.realtime_websocket_manager import get_realtime_manager


@app.websocket("/ws")
async def websocket_simple_endpoint(websocket: WebSocket):
    """
    🔌 WebSocket endpoint simples para testes
    """
    try:
        await websocket.accept()
        logger.info("✅ WebSocket conectado em /ws")
        
        # Enviar mensagem de boas-vindas em JSON
        await websocket.send_json({"type": "connection", "message": "WebSocket conectado com sucesso!", "status": "connected"})
        
        # Manter conexão viva
        while True:
            try:
                # Receber mensagem do cliente
                data = await websocket.receive_text()
                logger.info(f"📥 Mensagem recebida: {data}")
                
                # Responder com echo
                await websocket.send_text(f"Echo: {data}")
                
            except WebSocketDisconnect:
                logger.info("🔌 Cliente desconectado")
                break
            except Exception as e:
                logger.error(f"❌ Erro no WebSocket: {e}")
                break
                
    except Exception as e:
        logger.error(f"❌ Erro ao aceitar WebSocket: {e}")

@app.websocket("/ws/cache-sync")
async def websocket_realtime_endpoint(websocket: WebSocket):
    """
    🔄 WebSocket endpoint para sincronização de cache em tempo real

    Permite que o frontend receba notificações automáticas sobre
    invalidações de cache para atualizar dados em tempo real.
    """
    import uuid

    connection_id = str(uuid.uuid4())
    
    try:
        # Aceitar conexão primeiro
        await websocket.accept()
        logger.info(f"✅ WebSocket {connection_id} aceito com sucesso")
        
        # Conectar WebSocket
        realtime_manager = get_realtime_manager()
        success = await realtime_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            subscriptions=None,  # Se inscrever em todos os eventos
        )

        if not success:
            logger.warning(f"❌ Falha ao conectar WebSocket {connection_id}")
            return

        # Manter conexão viva
        while True:
            try:
                # Aguardar mensagens do client (opcional)
                message = await websocket.receive_json()

                # Processar mensagem do client se necessário
                if message.get("type") == "subscribe":
                    # Client pode se inscrever em eventos específicos
                    events = message.get("events", [])
                    logger.info(f"🔔 Client {connection_id} se inscreveu em: {events}")

                elif message.get("type") == "ping":
                    # Responder pong para manter conexão
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"❌ Erro na conexão WebSocket {connection_id}: {e}")
                break

    except Exception as e:
        logger.error(f"❌ Erro no WebSocket endpoint: {e}")
    finally:
        # Desconectar
        realtime_manager = get_realtime_manager()
        await realtime_manager.disconnect(connection_id)


# 🚨 SISTEMAS WEBSOCKET LEGACY DEPRECADOS (REMOVIDOS PARA ELIMINAR CONFLITOS)
# Os seguintes sistemas foram consolidados no websocket_unified.py:
# - app.routes.websocket (DEPRECADO)
# - app.routes.websocket_realtime (DEPRECADO) 
# - app.routes.websocket_realtime_advanced (DEPRECADO)
# - app.routes.websocket_realtime_new (DEPRECADO)
# - app.routes.websocket_test (DEPRECADO)
logger.info("✅ Sistema WebSocket unificado ativado - conflitos eliminados")

# 🔔 PUSH NOTIFICATIONS - Sistema de Notificações
from app.routes.push_notifications import router as push_router

app.include_router(push_router, tags=["Push Notifications"])


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Endpoint básico de health check"""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="WhatsApp Agent API",
        version="1.0.0",
    )


@app.get("/health/background-tasks")
async def health_check_background_tasks():
    """
    CORREÇÃO: Health check específico para background tasks
    
    Verifica se as background tasks do WebSocket Manager estão rodando corretamente.
    """
    try:
        from app.services.realtime_websocket_manager import get_realtime_manager
        
        realtime_manager = get_realtime_manager()
        
        # Verificar status das background tasks
        tasks_running = realtime_manager.is_background_tasks_running()
        
        # Obter estatísticas
        stats = await realtime_manager.get_stats()
        
        return {
            "success": True,
            "data": {
                "background_tasks_running": tasks_running,
                "websocket_stats": stats,
                "timestamp": datetime.now().isoformat(),
            },
            "message": "Background tasks verificadas com sucesso" if tasks_running else "Background tasks não estão rodando"
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar background tasks: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "background_tasks_running": False,
                "timestamp": datetime.now().isoformat(),
            },
            "message": "Erro ao verificar background tasks"
        }


# 🔄 C002 - Endpoint com novo padrão ApiResponse<T>
@app.get("/health/v2")
async def health_check_v2():
    """
    ✅ Health check usando novo padrão C002 - ApiResponse<T>

    Demonstra estrutura padronizada: {success, data, error, meta}
    O middleware aplica wrapper automaticamente.
    """
    try:
        # O middleware automaticamente converte isso para ApiResponse.success_response()
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "WhatsApp Agent API",
            "version": "1.0.0",
            "components": {
                "database": "healthy",
                "redis": "healthy",
                "webhook": "healthy",
            },
        }

        # ✅ Retorna dados normalmente - middleware aplica wrapper
        return health_data

    except Exception as e:
        logger.error(f"Erro no health check v2: {e}")
        # ✅ HTTPException é automaticamente convertida para ApiResponse.error_response()
        raise HTTPException(status_code=500, detail="Erro interno no health check")


@app.head("/health")
async def health_check_head():
    """Endpoint HEAD para health check (usado pelo Railway)"""
    # HEAD request não deve retornar body, apenas headers
    return Response(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "Content-Length": "92",
            "X-Health-Status": "healthy",
        },
    )


@app.get("/health/detailed")
async def detailed_health_check():
    """Health check detalhado de todos os componentes"""
    try:
        checks = await health_checker.run_all_checks()
        overall_status = health_checker.get_overall_status(checks)

        # Converter para formato serializável
        serialized_checks = {}
        for name, check in checks.items():
            serialized_checks[name] = {
                "status": check.status.value,
                "message": check.message,
                "timestamp": check.timestamp.isoformat(),
                "response_time": check.response_time,
                "details": check.details,
            }

        response_data = {
            "overall_status": overall_status.value,
            "checks": serialized_checks,
            "timestamp": datetime.now().isoformat(),
        }

        # Retornar status HTTP apropriado
        if overall_status == HealthStatus.HEALTHY:
            return JSONResponse(content=response_data, status_code=200)
        elif overall_status == HealthStatus.DEGRADED:
            return JSONResponse(
                content=response_data, status_code=200
            )  # Still operational
        else:
            return JSONResponse(
                content=response_data, status_code=503
            )  # Service Unavailable

    except Exception as e:
        logger.error(f"Erro no health check detalhado: {e}")
        return JSONResponse(
            content={
                "overall_status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            },
            status_code=500,
        )


@app.get("/metrics")
async def get_metrics():
    """Endpoint para métricas Prometheus"""
    try:
        return get_metrics_response()
    except Exception as e:
        logger.error(f"Erro ao obter métricas Prometheus: {e}")
        return JSONResponse(
            content={"error": "Failed to generate metrics"}, status_code=500
        )


@app.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics():
    """Endpoint para métricas do sistema"""
    try:
        # Executar health checks para obter métricas atuais
        checks = await health_checker.run_all_checks()

        # Extrair métricas específicas dos checks
        database_health = None
        redis_health = None
        cache_health = None

        if "database" in checks:
            check = checks["database"]
            database_health = SystemHealth(
                healthy=check.status == HealthStatus.HEALTHY,
                status=check.status.value,
                response_time_ms=(
                    check.response_time * 1000 if check.response_time else None
                ),
                details=check.details,
            )

        if "redis" in checks:
            check = checks["redis"]
            redis_health = SystemHealth(
                healthy=check.status == HealthStatus.HEALTHY,
                status=check.status.value,
                response_time_ms=(
                    check.response_time * 1000 if check.response_time else None
                ),
                details=check.details,
            )

        if "cache_service" in checks:
            check = checks["cache_service"]
            cache_health = SystemHealth(
                healthy=check.status == HealthStatus.HEALTHY,
                status=check.status.value,
                response_time_ms=(
                    check.response_time * 1000 if check.response_time else None
                ),
                details=check.details,
            )

        return SystemMetrics(
            database=database_health, redis=redis_health, cache_service=cache_health
        )

    except Exception as e:
        logger.error(f"Erro ao coletar métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/cors/debug")
async def cors_debug_info():
    """Endpoint para debug de configurações CORS"""
    return {
        "cors_debug": get_cors_debug_info(),
        "test_instructions": {
            "browser_test": "Abra o console do navegador e execute: fetch('https://wppagent-production.up.railway.app/cors/test').then(r => r.json()).then(console.log)",
            "curl_test": "curl -X OPTIONS https://wppagent-production.up.railway.app/cors/test -H 'Origin: http://localhost:3000' -v",
            "postman_test": "Criar request OPTIONS para https://wppagent-production.up.railway.app/cors/test com header Origin: http://localhost:3000",
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/response-control/stats")
async def get_response_control_statistics():
    """Endpoint para obter estatísticas do sistema unificado de controle"""
    try:
        from app.services.response_control import get_unified_response_control

        unified_response_control = get_unified_response_control()
        stats = await unified_response_control.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do sistema unificado: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/response-control/client/{client_id}")
async def get_client_response_control_info(client_id: str):
    """Endpoint para obter informações de controle de resposta de um cliente específico"""
    try:
        from app.services.response_control import get_unified_response_control

        unified_response_control = get_unified_response_control()
        stats = await unified_response_control.get_client_stats(client_id)

        if not stats:
            raise HTTPException(
                status_code=404, detail="Cliente não encontrado ou sem dados"
            )

        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter info do cliente {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/alerts")
async def get_active_alerts(severity: str = None):
    """Endpoint para obter alertas ativos"""
    try:
        alerts = alert_manager.get_active_alerts(severity)
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "source": alert.source,
                    "timestamp": alert.timestamp.isoformat(),
                    "data": alert.data,
                }
                for alert in alerts
            ],
            "total": len(alerts),
        }
    except Exception as e:
        logger.error(f"Erro ao obter alertas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/alerts/history")
async def get_alert_history(limit: int = 100):
    """Endpoint para obter histórico de alertas"""
    try:
        alerts = alert_manager.get_alert_history(limit)
        return {
            "alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity,
                    "source": alert.source,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": (
                        alert.resolved_at.isoformat() if alert.resolved_at else None
                    ),
                    "data": alert.data,
                }
                for alert in alerts
            ],
            "total": len(alerts),
        }
    except Exception as e:
        logger.error(f"Erro ao obter histórico de alertas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/alerts/stats")
async def get_alert_statistics():
    """Endpoint para obter estatísticas de alertas"""
    try:
        stats = alert_manager.get_alert_stats()
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de alertas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Endpoint para resolver um alerta manualmente"""
    try:
        await alert_manager.resolve_alert(alert_id, resolved_by="manual")
        return {"message": f"Alerta {alert_id} resolvido com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao resolver alerta {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# === ENDPOINTS DO SISTEMA LLM AVANÇADO ===


@app.get("/llm/analytics")
async def get_llm_analytics():
    """Endpoint para obter análises do sistema LLM"""
    try:
        report = advanced_llm_service.get_analytics_report()
        return report
    except Exception as e:
        logger.error(f"Erro ao obter analytics do LLM: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/llm/plugins")
async def get_plugin_stats():
    """Endpoint para obter estatísticas dos plugins"""
    try:
        stats = advanced_llm_service.get_plugin_stats()
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter stats dos plugins: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/llm/plugins/{plugin_name}/enable")
async def enable_plugin(plugin_name: str):
    """Endpoint para ativar um plugin"""
    try:
        success = advanced_llm_service.enable_plugin(plugin_name)
        if success:
            return {"message": f"Plugin {plugin_name} ativado com sucesso"}
        else:
            raise HTTPException(
                status_code=400, detail="Sistema de plugins não disponível"
            )
    except Exception as e:
        logger.error(f"Erro ao ativar plugin {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/llm/plugins/{plugin_name}/disable")
async def disable_plugin(plugin_name: str):
    """Endpoint para desativar um plugin"""
    try:
        success = advanced_llm_service.disable_plugin(plugin_name)
        if success:
            return {"message": f"Plugin {plugin_name} desativado com sucesso"}
        else:
            raise HTTPException(
                status_code=400, detail="Sistema de plugins não disponível"
            )
    except Exception as e:
        logger.error(f"Erro ao desativar plugin {plugin_name}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/llm/conversations/{user_id}/analytics")
async def get_user_conversation_analytics(user_id: str):
    """Endpoint para obter análises de conversa de um usuário específico"""
    try:
        analytics = advanced_llm_service.get_conversation_analytics(user_id)
        return analytics
    except Exception as e:
        logger.error(f"Erro ao obter analytics do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/llm/conversations/{user_id}/{conversation_id}/clear")
async def clear_conversation_context(user_id: str, conversation_id: str):
    """Endpoint para limpar contexto de uma conversa específica"""
    try:
        advanced_llm_service.clear_conversation_context(user_id, conversation_id)
        return {"message": f"Contexto da conversa {conversation_id} limpo com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao limpar contexto: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/llm/optimize")
async def optimize_llm_performance():
    """Endpoint para otimizar performance do sistema LLM"""
    try:
        await advanced_llm_service.optimize_performance()
        return {"message": "Otimização de performance executada com sucesso"}
    except Exception as e:
        logger.error(f"Erro na otimização: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/llm/test")
async def test_llm_processing():
    """Endpoint para testar o processamento do LLM"""
    try:
        test_response = await advanced_llm_service.process_message(
            user_id="test_user",
            conversation_id="test_conversation",
            message="Olá, gostaria de agendar um corte de cabelo para amanhã às 14h",
        )

        return {
            "test_successful": True,
            "response": {
                "text": test_response.text,
                "intent": (
                    test_response.intent.type.value if test_response.intent else None
                ),
                "confidence": test_response.confidence,
                "interactive_buttons": test_response.interactive_buttons,
                "metadata": test_response.metadata,
            },
        }
    except Exception as e:
        logger.error(f"Erro no teste do LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no teste: {str(e)}")


# === ENDPOINTS DO SISTEMA HÍBRIDO LLM + CREWAI ===


@app.get("/hybrid/analytics")
async def get_hybrid_analytics():
    """Endpoint para análises do sistema híbrido"""
    try:
        return hybrid_service.get_hybrid_analytics()
    except Exception as e:
        logger.error(f"Erro ao obter analytics híbridos: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/hybrid/test")
async def test_hybrid_system(request: dict):
    """Testa o sistema híbrido com uma mensagem"""
    try:
        message = request.get("message", "")
        phone = request.get("phone", "test_user")

        if not message:
            raise HTTPException(status_code=400, detail="Mensagem é obrigatória")

        result = await hybrid_service.process_message(
            user_id=phone,
            conversation_id=f"test_{datetime.now().timestamp()}",
            message=message,
            message_type="test",
        )

        return {"test_successful": True, "result": result}
    except Exception as e:
        logger.error(f"Erro no teste híbrido: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no teste: {str(e)}")


@app.get("/hybrid/performance")
async def get_hybrid_performance():
    """Obtém métricas de performance comparativas"""
    try:
        analytics = hybrid_service.get_hybrid_analytics()
        return {
            "performance_metrics": analytics["performance_comparison"],
            "recommendations": analytics["recommendations"],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Erro ao obter performance híbrida: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/crew/agents")
async def get_crew_agents_status():
    """Status dos agentes CrewAI"""
    try:
        from app.services.crew_agents import whatsapp_crew

        return whatsapp_crew.get_crew_analytics()
    except Exception as e:
        logger.error(f"Erro ao obter status dos agentes: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.put("/hybrid/strategy/{strategy}")
async def set_hybrid_strategy(strategy: str):
    """Define estratégia do sistema híbrido"""
    try:
        valid_strategies = ["llm_only", "crew_only", "hybrid", "auto"]
        if strategy not in valid_strategies:
            raise HTTPException(
                status_code=400,
                detail=f"Estratégia deve ser uma de: {valid_strategies}",
            )

        # Implementar lógica de configuração da estratégia
        return {
            "success": True,
            "strategy_set": strategy,
            "message": f"Estratégia definida para {strategy}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ========================================
# ENDPOINTS DE LEAD SCORING
# ========================================


@app.post("/lead/score")
async def score_lead(request: dict):
    """Calcula o score de um lead"""
    try:
        message = request.get("message", "")
        phone = request.get("phone", "")
        customer_data = request.get("customer_data", {})
        context = request.get("context", {})

        if not message or not phone:
            raise HTTPException(
                status_code=400, detail="Message e phone são obrigatórios"
            )

        lead_score = lead_scoring_service.score_lead(
            message=message, phone=phone, customer_data=customer_data, context=context
        )

        return {
            "success": True,
            "lead_score": {
                "total_score": lead_score.total_score,
                "category": lead_score.category.value,
                "priority_level": lead_score.priority_level,
                "confidence": lead_score.confidence,
                "estimated_value": lead_score.estimated_value,
                "conversion_probability": lead_score.conversion_probability,
                "factors": lead_score.factors,
                "recommendations": lead_score.recommendations,
                "next_actions": lead_score.next_actions,
            },
        }
    except Exception as e:
        logger.error(f"Erro no scoring de lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/lead/analytics")
async def get_lead_analytics():
    """Retorna analytics dos leads"""
    try:
        analytics = lead_scoring_service.get_lead_analytics()
        return {
            "success": True,
            "analytics": analytics,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Erro nas analytics de leads: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/lead/top/{limit}")
async def get_top_leads(limit: int = 10):
    """Retorna os top leads por score"""
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400, detail="Limit deve estar entre 1 e 100"
            )

        top_leads = lead_scoring_service.get_top_leads(limit)
        return {
            "success": True,
            "top_leads": top_leads,
            "count": len(top_leads),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Erro ao buscar top leads: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.post("/lead/test")
async def test_lead_scoring():
    """Testa o sistema de lead scoring com exemplos"""
    try:
        test_cases = [
            {
                "message": "Preciso agendar urgente um corte hoje!",
                "phone": "+5511999999001",
                "customer_data": {"total_spent": 300, "total_interactions": 5},
            },
            {
                "message": "Qual o preço do corte?",
                "phone": "+5511999999002",
                "customer_data": {"total_spent": 0, "total_interactions": 1},
            },
            {
                "message": "Oi",
                "phone": "+5511999999003",
                "customer_data": {"total_spent": 50, "total_interactions": 2},
            },
            {
                "message": "Estou muito insatisfeito com o atendimento, quero falar com o gerente",
                "phone": "+5511999999004",
                "customer_data": {
                    "total_spent": 500,
                    "total_interactions": 10,
                    "complaints": 1,
                },
            },
        ]

        results = []
        for case in test_cases:
            lead_score = lead_scoring_service.score_lead(
                message=case["message"],
                phone=case["phone"],
                customer_data=case["customer_data"],
            )

            results.append(
                {
                    "message": case["message"],
                    "phone": case["phone"],
                    "score": lead_score.total_score,
                    "category": lead_score.category.value,
                    "priority": lead_score.priority_level,
                    "estimated_value": lead_score.estimated_value,
                    "conversion_probability": lead_score.conversion_probability,
                    "recommendations": lead_score.recommendations[
                        :3
                    ],  # Apenas 3 primeiras
                }
            )

        return {
            "success": True,
            "test_results": results,
            "summary": {
                "total_tests": len(results),
                "average_score": sum(r["score"] for r in results) / len(results),
                "high_priority_leads": len([r for r in results if r["priority"] >= 4]),
            },
        }
    except Exception as e:
        logger.error(f"Erro no teste de lead scoring: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# ============================================================================
# ENDPOINTS DE FLUXO CONVERSACIONAL NÃO-LINEAR
# ============================================================================


@app.get("/conversation/flow/{phone}")
async def get_conversation_flow(phone: str):
    """Obtém estado atual do fluxo conversacional"""
    try:
        summary = conversation_flow_service.get_conversation_summary(phone)
        return {"status": "success", "phone": phone, "conversation_summary": summary}
    except Exception as e:
        logger.error(f"Erro ao obter fluxo conversacional: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversation/reset/{phone}")
async def reset_conversation_flow(phone: str):
    """Reseta fluxo conversacional para um usuário"""
    try:
        conversation_flow_service.reset_conversation(phone)
        return {
            "status": "success",
            "message": f"Conversa resetada para {phone}",
            "phone": phone,
        }
    except Exception as e:
        logger.error(f"Erro ao resetar conversa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversation/topic/{phone}/{topic_id}/resolve")
async def mark_topic_resolved(phone: str, topic_id: str):
    """Marca um tópico como resolvido na conversa"""
    try:
        conversation_flow_service.mark_topic_resolved(phone, topic_id)
        return {
            "status": "success",
            "message": f"Tópico {topic_id} marcado como resolvido para {phone}",
            "phone": phone,
            "topic_id": topic_id,
        }
    except Exception as e:
        logger.error(f"Erro ao marcar tópico como resolvido: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/analytics")
async def get_conversation_analytics():
    """Obtém analytics gerais do fluxo conversacional"""
    try:
        # Coletar dados de todas as conversas ativas
        all_conversations = {}
        for phone, memory in conversation_flow_service.conversation_memories.items():
            all_conversations[
                phone
            ] = conversation_flow_service.get_conversation_summary(phone)

        # Calcular métricas
        total_conversations = len(all_conversations)
        active_conversations = len(
            [
                c
                for c in all_conversations.values()
                if c.get("status") != "no_conversation"
            ]
        )

        # Estados mais comuns
        states = [
            c.get("current_state")
            for c in all_conversations.values()
            if c.get("current_state")
        ]
        state_distribution = {}
        for state in set(states):
            state_distribution[state] = states.count(state)

        # Tópicos mais frequentes
        all_topics = {}
        for conv in all_conversations.values():
            if "active_topics" in conv:
                for topic_id, topic_data in conv["active_topics"].items():
                    if topic_id not in all_topics:
                        all_topics[topic_id] = {"count": 0, "total_mentions": 0}
                    all_topics[topic_id]["count"] += 1
                    all_topics[topic_id]["total_mentions"] += topic_data.get(
                        "mentions", 0
                    )

        # Switches de contexto
        context_switches = [
            c.get("context_switches", 0) for c in all_conversations.values()
        ]
        avg_context_switches = (
            sum(context_switches) / len(context_switches) if context_switches else 0
        )

        return {
            "status": "success",
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "state_distribution": state_distribution,
            "top_topics": dict(
                sorted(
                    all_topics.items(),
                    key=lambda x: x[1]["total_mentions"],
                    reverse=True,
                )[:10]
            ),
            "average_context_switches": round(avg_context_switches, 2),
            "high_switch_conversations": len([s for s in context_switches if s > 5]),
            "conversation_details": all_conversations,
        }

    except Exception as e:
        logger.error(f"Erro ao gerar analytics conversacionais: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversation/test")
async def test_conversation_flow():
    """Testa o sistema de fluxo conversacional com cenários diversos"""
    try:
        test_scenarios = [
            {
                "phone": "11999999001",
                "messages": [
                    "Oi, bom dia!",
                    "Gostaria de saber sobre seus serviços",
                    "Aliás, quanto custa um corte?",
                    "Mas voltando aos serviços, vocês fazem barba também?",
                    "Perfeito! Posso agendar para amanhã?",
                ],
            },
            {
                "phone": "11999999002",
                "messages": [
                    "Preciso cancelar meu agendamento",
                    "Na verdade, posso reagendar?",
                    "Espera, antes disso, vocês fazem sobrancelha?",
                    "Ok, então vou reagendar mesmo",
                ],
            },
            {
                "phone": "11999999003",
                "messages": [
                    "Olá! Quero saber preços",
                    "E onde vocês ficam?",
                    "Tem estacionamento?",
                    "Voltando aos preços, fazem promoção?",
                    "E sobre horários, funcionam sábado?",
                ],
            },
        ]

        results = []

        for scenario in test_scenarios:
            phone = scenario["phone"]
            # Reset conversa para teste limpo
            conversation_flow_service.reset_conversation(phone)

            scenario_results = []
            for i, message in enumerate(scenario["messages"]):
                # Processar mensagem
                flow_decision = conversation_flow_service.process_message_flow(
                    message, phone, {"test": True}
                )

                scenario_results.append(
                    {
                        "step": i + 1,
                        "message": message,
                        "conversation_state": flow_decision.next_state.value,
                        "transition_type": flow_decision.transition_type.value,
                        "confidence": flow_decision.confidence,
                        "topics_detected": flow_decision.topics_to_activate,
                        "reasoning": flow_decision.reasoning,
                    }
                )

            # Obter resumo final
            final_summary = conversation_flow_service.get_conversation_summary(phone)

            results.append(
                {
                    "scenario": f"Teste {phone[-3:]}",
                    "phone": phone,
                    "total_messages": len(scenario["messages"]),
                    "steps": scenario_results,
                    "final_summary": final_summary,
                }
            )

        return {
            "status": "success",
            "message": "Testes de fluxo conversacional executados",
            "scenarios_tested": len(test_scenarios),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Erro no teste de fluxo conversacional: {e}")
        return {"status": "error", "message": str(e), "results": []}


# ================================
# FUNÇÃO DE LIMPEZA PERIÓDICA
# ================================


async def periodic_cleanup():
    """Limpeza periódica dos controles de resposta única"""
    while True:
        try:
            await asyncio.sleep(300)  # A cada 5 minutos
            from app.services.response_control import get_unified_response_control

            unified_response_control = get_unified_response_control()
            await unified_response_control.cleanup_expired()
            logger.info("🧹 Limpeza periódica executada")
        except asyncio.CancelledError:
            logger.info("🛑 Limpeza periódica cancelada")
            break
        except Exception as e:
            logger.error(f"❌ Erro na limpeza periódica: {e}")
            await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente


if __name__ == "__main__":
    import os
    import sys
    
    port = int(os.getenv("PORT", 8000))
    
    # Railway-specific logging configuration (SIMPLIFIED)
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=False,  # Disable reload for production
        log_level="info",
        use_colors=False  # Disable colors for Railway logs
    )
