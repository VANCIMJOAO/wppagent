"""
Função de Startup Otimizada
===========================

Versão otimizada da função lifespan com:
- Fases sequenciais de startup
- Métricas de performance
- Logs estruturados
- Zero duplicação
"""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.logging_config import (
    get_optimized_logger,
    log_startup_phase,
    log_startup_completion,
    log_startup_summary,
    log_performance_metric,
    log_system_event,
    startup_manager,
)
from app.database import init_db
from app.services.connection_pool_manager import initialize_pool
from app.services.cache_service import cache_service
from app.config import settings

logger = get_optimized_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação otimizado"""
    RAILWAY_FAST_START = os.getenv('RAILWAY_FAST_START', 'false').lower() == 'true'
    
    # Log detalhado de início do startup
    print("🚀 LIFESPAN: Iniciando WhatsApp Agent API...")
    print(f"🔍 LIFESPAN: RAILWAY_FAST_START = {RAILWAY_FAST_START}")
    print(f"🔍 LIFESPAN: PORT = {os.getenv('PORT', '8000')}")
    print(f"🔍 LIFESPAN: RAILWAY_ENVIRONMENT = {os.getenv('RAILWAY_ENVIRONMENT', 'unknown')}")
    print(f"🔍 LIFESPAN: PYTHONUNBUFFERED = {os.getenv('PYTHONUNBUFFERED', 'not set')}")
    
    log_system_event("startup", "WhatsApp Agent API starting", 
                    railway_fast_start=RAILWAY_FAST_START,
                    port=os.getenv('PORT', '8000'),
                    railway_env=os.getenv('RAILWAY_ENVIRONMENT', 'unknown'))

    try:
        # FASE 1: Database Initialization
        log_startup_phase("database", "Initializing database and connection pool")
        try:
            await init_db()
            log_startup_completion("database", "completed")
            
            # Inicializar pool de conexões persistente
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://").replace("+asyncpg", "")
                if await initialize_pool(sync_url):
                    log_system_event("database", "Connection pool initialized")
                else:
                    log_system_event("database", "Failed to initialize connection pool", level="warning")
            else:
                log_system_event("database", "DATABASE_URL not found for connection pool", level="warning")
                
        except Exception as e:
            log_startup_completion("database", "failed")
            log_system_event("database", f"Database initialization error: {e}", level="warning")
            if not RAILWAY_FAST_START:
                raise
            log_system_event("startup", "Continuing without database in Railway mode")

        # FASE 2: Cache Initialization
        log_startup_phase("cache", "Initializing cache service")
        try:
            await cache_service.initialize()
            log_startup_completion("cache", "completed")
        except Exception as e:
            log_startup_completion("cache", "failed")
            log_system_event("cache", f"Cache initialization error: {e}", level="warning")
            if not RAILWAY_FAST_START:
                raise
            log_system_event("startup", "Continuing without cache in Railway mode")

        if RAILWAY_FAST_START:
            # Fast startup for Railway - only essential services
            log_system_event("startup", "Railway fast mode: Skipping heavy services")
            log_system_event("startup", "WhatsApp Agent API started successfully - FAST MODE!")
            log_system_event("webhook", f"Webhook URL: {settings.webhook_url}")
            log_system_event("websocket", "WebSocket endpoint available at: /ws")
        else:
            # Full startup for production - all heavy services
            await _initialize_production_services()

        # Log de resumo final
        log_startup_summary()

    except Exception as e:
        log_system_event("startup", f"Startup failed: {e}", level="error")
        raise

    yield

    # Shutdown
    log_system_event("shutdown", "Shutting down WhatsApp Agent API...")
    await _shutdown_services()
    log_system_event("shutdown", "WhatsApp Agent API shutdown completed")


async def _initialize_production_services():
    """Inicializar serviços de produção"""
    
    # FASE 3: Cache Invalidation System
    log_startup_phase("cache_invalidation", "Initializing cache invalidation system")
    try:
        from app.services.cache_invalidation_manual import get_cache_invalidation_manager
        cache_invalidation_manager = get_cache_invalidation_manager()
        log_startup_completion("cache_invalidation", "completed")
    except Exception as e:
        log_startup_completion("cache_invalidation", "failed")
        log_system_event("cache_invalidation", f"Cache invalidation error: {e}", level="warning")

    # FASE 4: LGPD Compliance System
    log_startup_phase("lgpd", "Initializing LGPD compliance system")
    try:
        from app.services.lgpd_scheduler import start_lgpd_scheduler
        start_lgpd_scheduler()
        log_startup_completion("lgpd", "completed")
    except Exception as e:
        log_startup_completion("lgpd", "failed")
        log_system_event("lgpd", f"LGPD system error: {e}", level="error", 
                        error_type=type(e).__name__, 
                        error_details=str(e))
        # Em produção, falhar fast para problemas críticos
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise

    # FASE 5: WebSocket Real-Time Manager
    log_startup_phase("websocket", "Initializing WebSocket real-time manager")
    try:
        from app.services.realtime_websocket_manager import get_realtime_manager
        realtime_manager = get_realtime_manager()
        await realtime_manager.start_background_tasks()
        log_startup_completion("websocket", "completed")
    except Exception as e:
        log_startup_completion("websocket", "failed")
        log_system_event("websocket", f"WebSocket manager error: {e}", level="error")
        raise

    # FASE 6: Backup System
    log_startup_phase("backup", "Initializing backup scheduler")
    try:
        from app.services.backup_scheduler import backup_scheduler
        await backup_scheduler.start()
        log_startup_completion("backup", "completed")
    except Exception as e:
        log_startup_completion("backup", "failed")
        log_system_event("backup", f"Backup system error: {e}", level="warning")

    # FASE 7: Performance Systems
    log_startup_phase("performance", "Initializing performance optimization systems")
    try:
        from app.services.database_optimizer import DatabaseOptimizer
        from app.services.cache_service_optimized import get_optimized_cache
        from app.services.cdn_manager import CDNManager

        # Database Optimizer
        db_optimizer = DatabaseOptimizer()
        await db_optimizer.initialize()
        log_system_event("performance", "Database optimizer activated")

        # Cache Optimized
        optimized_cache = get_optimized_cache()
        await optimized_cache.initialize()
        log_system_event("performance", "Cache optimized activated")

        # CDN Manager
        cdn_manager = CDNManager()
        await cdn_manager.initialize()
        log_system_event("performance", "CDN manager activated")

        log_startup_completion("performance", "completed")
    except Exception as e:
        log_startup_completion("performance", "failed")
        log_system_event("performance", f"Performance systems error: {e}", level="warning")

    # FASE 8: RBAC System
    log_startup_phase("rbac", "Initializing RBAC system")
    try:
        from app.services.rbac_service import rbac_service
        rbac_initialized = await rbac_service.initialize_system()
        if rbac_initialized:
            log_startup_completion("rbac", "completed")
        else:
            log_startup_completion("rbac", "failed")
            log_system_event("rbac", "RBAC could not be initialized - limited functionality", level="warning")
    except Exception as e:
        log_startup_completion("rbac", "failed")
        log_system_event("rbac", f"RBAC initialization error: {e}", level="warning")

    # Iniciar limpeza periódica
    cleanup_task = asyncio.create_task(_periodic_cleanup())

    log_system_event("startup", "WhatsApp Agent API started successfully!")
    log_system_event("webhook", f"Webhook URL: {settings.webhook_url}")
    log_system_event("websocket", "WebSocket endpoint available at: /ws")
    log_system_event("websocket", "WebSocket real-time chat implemented")


async def _shutdown_services():
    """Encerrar serviços"""
    
    # WebSocket Real-Time Manager
    try:
        from app.services.realtime_websocket_manager import get_realtime_manager
        realtime_manager = get_realtime_manager()
        
        log_system_event("shutdown", "Stopping WebSocket background tasks...")
        await realtime_manager.stop_background_tasks()
        
        log_system_event("shutdown", "Cleaning up WebSocket connections...")
        cleaned_count = await realtime_manager.force_cleanup_all()
        log_system_event("shutdown", f"{cleaned_count} WebSocket connections cleaned")
        
    except Exception as e:
        log_system_event("shutdown", f"Error shutting down WebSocket manager: {e}", level="error")

    # LGPD Scheduler
    try:
        from app.services.lgpd_scheduler import stop_lgpd_scheduler
        stop_lgpd_scheduler()
        log_system_event("shutdown", "LGPD scheduler stopped")
    except Exception as e:
        log_system_event("shutdown", f"Error stopping LGPD scheduler: {e}", level="error")

    # Backup System
    try:
        from app.services.backup_scheduler import backup_scheduler
        await backup_scheduler.stop()
        log_system_event("shutdown", "Backup system finalized")
    except Exception as e:
        log_system_event("shutdown", f"Error finalizing backup system: {e}", level="warning")

    # Cache Service
    try:
        await cache_service.close()
        log_system_event("shutdown", "Cache service closed")
    except Exception as e:
        log_system_event("shutdown", f"Error closing cache service: {e}", level="warning")


async def _periodic_cleanup():
    """Limpeza periódica dos controles de resposta única"""
    while True:
        try:
            await asyncio.sleep(300)  # A cada 5 minutos
            from app.services.response_control import get_unified_response_control

            unified_response_control = get_unified_response_control()
            await unified_response_control.cleanup_expired()
            log_system_event("cleanup", "Periodic cleanup executed")
        except asyncio.CancelledError:
            log_system_event("cleanup", "Periodic cleanup cancelled")
            break
        except Exception as e:
            log_system_event("cleanup", f"Error in periodic cleanup: {e}", level="error")
            await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente
