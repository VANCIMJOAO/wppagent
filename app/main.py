"""
Aplicação principal# 🔒 Sistema de Autenticação e Autorização
from app.auth import AuthMiddlewareastAPI
"""
import logging
import uvicorn
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.utils.logger import get_logger
from app.routes.webhook import router as webhook_router
from app.database import init_db
from app.services.health_checker import health_checker, HealthStatus
from app.middleware.rate_limit import RateLimitMiddleware, get_rate_limit_stats
from app.services.alert_manager import alert_manager
from app.services.llm_advanced import advanced_llm_service
from app.services.strategy_compatibility import hybrid_service
from app.services.lead_scoring import lead_scoring_service
from app.services.conversation_flow import conversation_flow_service
from app.services.cache_service import cache_service

# Sistema de Autenticação e Autorização
from app.auth import AuthMiddleware

# Prometheus Metrics Integration
from app.utils.metrics import metrics_collector, get_metrics_response
from app.middleware.metrics import MetricsMiddleware

# �🚀 Sistemas de Performance e Escalabilidade
from app.services.database_optimizer import DatabaseOptimizer
from app.services.cache_service_optimized import OptimizedCacheService
from app.services.cdn_manager import CDNManager
from app.utils.logger import init_logging, get_logger

# Inicializar sistema de logging estruturado
init_logging()
logger = get_logger(__name__)

# 🔒 Sistema de Segurança HTTPS - Verificar disponibilidade
try:
    from app.security.https_middleware import HTTPSMiddleware
    HTTPS_MIDDLEWARE_AVAILABLE = True
    logger.info("✅ HTTPS Middleware carregado")
except ImportError:
    HTTPS_MIDDLEWARE_AVAILABLE = False
    HTTPSMiddleware = None
    logger.warning("⚠️ HTTPS Middleware não disponível - executando sem HTTPS obrigatório")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação"""
    # Startup
    logger.info("Iniciando WhatsApp Agent API...")
    
    try:
        # Inicializar banco de dados
        await init_db()
        logger.info("Banco de dados inicializado")
        
        # Inicializar cache service
        await cache_service.initialize()
        logger.info("Cache service inicializado")
        
        # 🚀 Inicializar sistemas de performance (com tratamento de erro)
        try:
            db_optimizer = DatabaseOptimizer()
            await db_optimizer.initialize()
            logger.info("🚀 Database Optimizer ativado")
        except Exception as e:
            logger.warning(f"⚠️ Database Optimizer não pôde ser inicializado: {e}")
        
        try:
            optimized_cache = OptimizedCacheService()
            await optimized_cache.initialize()
            logger.info("🚀 Cache Optimized ativado")
        except Exception as e:
            logger.warning(f"⚠️ Cache Optimized não pôde ser inicializado: {e}")
        
        try:
            cdn_manager = CDNManager()
            await cdn_manager.initialize()
            logger.info("🚀 CDN Manager ativado")
        except Exception as e:
            logger.warning(f"⚠️ CDN Manager não pôde ser inicializado: {e}")
        
        logger.info("✅ WhatsApp Agent API iniciado com sucesso!")
        logger.info(f"📱 Webhook URL: {settings.webhook_url}")
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Encerrando WhatsApp Agent API...")
    await cache_service.close()
    
    # Shutdown
    logger.info("Finalizando WhatsApp Agent API...")


# Criar aplicação FastAPI
app = FastAPI(
    title="WhatsApp Agent API",
    description="API para agente inteligente de WhatsApp",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔒 Adicionar middleware de segurança HTTPS (primeiro)
if HTTPS_MIDDLEWARE_AVAILABLE:
    app.add_middleware(
        HTTPSMiddleware,
        force_https=not settings.debug,  # Forçar HTTPS apenas em produção
        hsts_max_age=31536000,  # 1 ano
        hsts_include_subdomains=True,
        hsts_preload=True,
        allow_localhost=settings.debug,  # Permitir localhost apenas em desenvolvimento
        development_mode=settings.debug
    )
    logger.info("✅ HTTPS Middleware ativado")
else:
    logger.warning("⚠️ HTTPS Middleware não disponível")

# 🔒 Adicionar middleware de autenticação e autorização
app.add_middleware(AuthMiddleware)

# Adicionar rate limiting middleware baseado na configuração
# Usar middleware corrigido que garante sempre retornar uma resposta
try:
    if hasattr(settings, 'rate_limit_enabled') and settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware, enabled=True)
        logger.info("Rate limiting middleware added and enabled")
    else:
        app.add_middleware(RateLimitMiddleware, enabled=False)
        logger.info("Rate limiting middleware added but disabled")
except Exception as e:
    logger.error(f"Failed to add rate limiting middleware: {e}")
    # Adicionar middleware desabilitado como fallback
    app.add_middleware(RateLimitMiddleware, enabled=False)

# Adicionar middleware de métricas (último para capturar todas as requests)
app.add_middleware(MetricsMiddleware)

# Incluir rotas
app.include_router(webhook_router, tags=["webhook"])

# � Debug webhook (TEMPORÁRIO - remover em produção)
from app.routes.debug_webhook import router as debug_webhook_router
app.include_router(debug_webhook_router, tags=["Debug"])

# �🔒 Incluir rotas de autenticação e segurança
from app.routes.auth import router as auth_router
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

from app.routes.secrets import router as secrets_router  
app.include_router(secrets_router, prefix="/secrets", tags=["Secrets Management"])

# 🔐 Incluir rotas de segurança e criptografia
from app.routes.security import router as security_router
app.include_router(security_router, prefix="/security", tags=["Security & Encryption"])

# Incluir rotas de administração de estratégias
from app.routes.strategy_admin import router as strategy_admin_router
app.include_router(strategy_admin_router, tags=["Strategy Management"])

# Incluir rotas de monitoramento de custos
# from app.routes.cost_monitoring import router as cost_router
# app.include_router(cost_router, tags=["Cost Monitoring"])

# Incluir rotas de autenticação admin
from app.routes.admin_auth import auth_router
app.include_router(auth_router, tags=["Admin Authentication"])

# Incluir rotas de otimização do banco de dados
from app.routes.database_optimization import router as db_optimization_router
app.include_router(db_optimization_router, tags=["Database Optimization"])


@app.get("/health")
async def health_check():
    """Endpoint básico de health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "WhatsApp Agent API"
    }


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
                "details": check.details
            }
        
        response_data = {
            "overall_status": overall_status.value,
            "checks": serialized_checks,
            "timestamp": datetime.now().isoformat()
        }
        
        # Retornar status HTTP apropriado
        if overall_status == HealthStatus.HEALTHY:
            return JSONResponse(content=response_data, status_code=200)
        elif overall_status == HealthStatus.DEGRADED:
            return JSONResponse(content=response_data, status_code=200)  # Still operational
        else:
            return JSONResponse(content=response_data, status_code=503)  # Service Unavailable
            
    except Exception as e:
        logger.error(f"Erro no health check detalhado: {e}")
        return JSONResponse(
            content={
                "overall_status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=500
        )


@app.get("/metrics")
async def get_metrics():
    """Endpoint para métricas Prometheus"""
    try:
        return get_metrics_response()
    except Exception as e:
        logger.error(f"Erro ao obter métricas Prometheus: {e}")
        return JSONResponse(
            content={"error": "Failed to generate metrics"},
            status_code=500
        )


@app.get("/metrics/system")
async def get_system_metrics():
    """Endpoint para métricas do sistema (legacy)"""
    try:
        # Executar health checks para obter métricas atuais
        checks = await health_checker.run_all_checks()
        
        # Coletar métricas adicionais
        from app.services.retry_handler import retry_handler
        circuit_breaker_stats = retry_handler.get_circuit_breaker_status("whatsapp_api")
        
        metrics = {
            "system": {
                "uptime": datetime.now().isoformat(),
                "service": "WhatsApp Agent API",
                "version": "1.0.0"
            },
            "health_checks": {
                name: {
                    "status": check.status.value,
                    "response_time": check.response_time,
                    "last_check": check.timestamp.isoformat()
                }
                for name, check in checks.items()
            },
            "circuit_breakers": {
                "whatsapp_api": circuit_breaker_stats
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Erro ao coletar métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "WhatsApp Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/rate-limit/stats")
async def get_rate_limit_statistics():
    """Endpoint para obter estatísticas de rate limiting"""
    try:
        stats = get_rate_limit_stats()
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de rate limit: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/rate-limit/client/{client_id}")
async def get_client_rate_limit_info(client_id: str):
    """Endpoint para obter informações de rate limit de um cliente específico"""
    try:
        from app.services.rate_limiter import rate_limiter
        stats = rate_limiter.get_client_stats(client_id)
        
        if "error" in stats:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
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
                    "data": alert.data
                }
                for alert in alerts
            ],
            "total": len(alerts)
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
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                    "data": alert.data
                }
                for alert in alerts
            ],
            "total": len(alerts)
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
            raise HTTPException(status_code=400, detail="Sistema de plugins não disponível")
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
            raise HTTPException(status_code=400, detail="Sistema de plugins não disponível")
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
            message="Olá, gostaria de agendar um corte de cabelo para amanhã às 14h"
        )
        
        return {
            "test_successful": True,
            "response": {
                "text": test_response.text,
                "intent": test_response.intent.type.value if test_response.intent else None,
                "confidence": test_response.confidence,
                "interactive_buttons": test_response.interactive_buttons,
                "metadata": test_response.metadata
            }
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
            message_type="test"
        )
        
        return {
            "test_successful": True,
            "result": result
        }
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
            "timestamp": datetime.now().isoformat()
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
            raise HTTPException(status_code=400, detail=f"Estratégia deve ser uma de: {valid_strategies}")
        
        # Implementar lógica de configuração da estratégia
        return {"success": True, "strategy_set": strategy, "message": f"Estratégia definida para {strategy}"}
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
            raise HTTPException(status_code=400, detail="Message e phone são obrigatórios")
        
        lead_score = lead_scoring_service.score_lead(
            message=message,
            phone=phone,
            customer_data=customer_data,
            context=context
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
                "next_actions": lead_score.next_actions
            }
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
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro nas analytics de leads: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@app.get("/lead/top/{limit}")
async def get_top_leads(limit: int = 10):
    """Retorna os top leads por score"""
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit deve estar entre 1 e 100")
        
        top_leads = lead_scoring_service.get_top_leads(limit)
        return {
            "success": True,
            "top_leads": top_leads,
            "count": len(top_leads),
            "timestamp": datetime.now().isoformat()
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
                "customer_data": {"total_spent": 300, "total_interactions": 5}
            },
            {
                "message": "Qual o preço do corte?",
                "phone": "+5511999999002",
                "customer_data": {"total_spent": 0, "total_interactions": 1}
            },
            {
                "message": "Oi",
                "phone": "+5511999999003",
                "customer_data": {"total_spent": 50, "total_interactions": 2}
            },
            {
                "message": "Estou muito insatisfeito com o atendimento, quero falar com o gerente",
                "phone": "+5511999999004",
                "customer_data": {"total_spent": 500, "total_interactions": 10, "complaints": 1}
            }
        ]
        
        results = []
        for case in test_cases:
            lead_score = lead_scoring_service.score_lead(
                message=case["message"],
                phone=case["phone"],
                customer_data=case["customer_data"]
            )
            
            results.append({
                "message": case["message"],
                "phone": case["phone"],
                "score": lead_score.total_score,
                "category": lead_score.category.value,
                "priority": lead_score.priority_level,
                "estimated_value": lead_score.estimated_value,
                "conversion_probability": lead_score.conversion_probability,
                "recommendations": lead_score.recommendations[:3]  # Apenas 3 primeiras
            })
        
        return {
            "success": True,
            "test_results": results,
            "summary": {
                "total_tests": len(results),
                "average_score": sum(r["score"] for r in results) / len(results),
                "high_priority_leads": len([r for r in results if r["priority"] >= 4])
            }
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
        return {
            "status": "success",
            "phone": phone,
            "conversation_summary": summary
        }
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
            "phone": phone
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
            "topic_id": topic_id
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
            all_conversations[phone] = conversation_flow_service.get_conversation_summary(phone)
        
        # Calcular métricas
        total_conversations = len(all_conversations)
        active_conversations = len([c for c in all_conversations.values() if c.get("status") != "no_conversation"])
        
        # Estados mais comuns
        states = [c.get("current_state") for c in all_conversations.values() if c.get("current_state")]
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
                    all_topics[topic_id]["total_mentions"] += topic_data.get("mentions", 0)
        
        # Switches de contexto
        context_switches = [c.get("context_switches", 0) for c in all_conversations.values()]
        avg_context_switches = sum(context_switches) / len(context_switches) if context_switches else 0
        
        return {
            "status": "success",
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "state_distribution": state_distribution,
            "top_topics": dict(sorted(all_topics.items(), key=lambda x: x[1]["total_mentions"], reverse=True)[:10]),
            "average_context_switches": round(avg_context_switches, 2),
            "high_switch_conversations": len([s for s in context_switches if s > 5]),
            "conversation_details": all_conversations
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
                    "Perfeito! Posso agendar para amanhã?"
                ]
            },
            {
                "phone": "11999999002", 
                "messages": [
                    "Preciso cancelar meu agendamento",
                    "Na verdade, posso reagendar?",
                    "Espera, antes disso, vocês fazem sobrancelha?",
                    "Ok, então vou reagendar mesmo"
                ]
            },
            {
                "phone": "11999999003",
                "messages": [
                    "Olá! Quero saber preços",
                    "E onde vocês ficam?", 
                    "Tem estacionamento?",
                    "Voltando aos preços, fazem promoção?",
                    "E sobre horários, funcionam sábado?"
                ]
            }
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
                
                scenario_results.append({
                    "step": i + 1,
                    "message": message,
                    "conversation_state": flow_decision.next_state.value,
                    "transition_type": flow_decision.transition_type.value,
                    "confidence": flow_decision.confidence,
                    "topics_detected": flow_decision.topics_to_activate,
                    "reasoning": flow_decision.reasoning
                })
            
            # Obter resumo final
            final_summary = conversation_flow_service.get_conversation_summary(phone)
            
            results.append({
                "scenario": f"Teste {phone[-3:]}",
                "phone": phone,
                "total_messages": len(scenario["messages"]),
                "steps": scenario_results,
                "final_summary": final_summary
            })
        
        return {
            "status": "success",
            "message": "Testes de fluxo conversacional executados",
            "scenarios_tested": len(test_scenarios),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Erro no teste de fluxo conversacional: {e}")
        return {
            "status": "error",
            "message": str(e),
            "results": []
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
