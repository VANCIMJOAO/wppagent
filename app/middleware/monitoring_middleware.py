"""
Middleware de Monitoramento
==========================

Middleware que integra automaticamente o sistema de monitoramento
nas rotas da API, registrando métricas de performance, SLA e negócio.
"""

import time
import asyncio
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.logger import get_logger, set_request_context, clear_request_context
from app.services.comprehensive_monitoring import monitoring_system, record_api_call, record_business_event
from app.config.config_factory import ConfigFactory

logger = get_logger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware que monitora automaticamente todas as requisições HTTP
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.config = ConfigFactory.get_singleton_config()
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processar requisição com monitoramento completo"""
        
        # Gerar ID único para requisição
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Configurar contexto para logging
        request_context = {
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url),
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
        
        set_request_context(request_context)
        
        try:
            # Log da requisição de entrada
            logger.info(f"Request started: {request.method} {request.url.path}", {
                'endpoint': request.url.path,
                'method': request.method,
                'query_params': dict(request.query_params),
                'headers': dict(request.headers)
            })
            
            # Processar requisição
            response = await call_next(request)
            
            # Calcular tempo de resposta
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Registrar métricas se monitoramento estiver habilitado
            if self.config.metrics_enabled:
                await self._record_metrics(
                    request, response, response_time_ms, request_context
                )
            
            # Log da resposta
            logger.info(f"Request completed: {request.method} {request.url.path}", {
                'status_code': response.status_code,
                'response_time_ms': round(response_time_ms, 2),
                'content_length': response.headers.get('content-length', 0)
            })
            
            # Adicionar headers de monitoramento
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Response-Time'] = f"{response_time_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Calcular tempo de resposta mesmo em caso de erro
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Log do erro
            logger.error(f"Request failed: {request.method} {request.url.path}", {
                'error': str(e),
                'response_time_ms': round(response_time_ms, 2)
            }, exc_info=True)
            
            # Registrar métricas de erro
            if self.config.metrics_enabled:
                await self._record_error_metrics(
                    request, response_time_ms, request_context, str(e)
                )
            
            # Retornar resposta de erro
            error_response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )
            error_response.headers['X-Request-ID'] = request_id
            error_response.headers['X-Response-Time'] = f"{response_time_ms:.2f}ms"
            
            return error_response
            
        finally:
            # Limpar contexto
            clear_request_context()
    
    async def _record_metrics(self, request: Request, response: Response, 
                            response_time_ms: float, request_context: Dict[str, Any]):
        """Registrar métricas da requisição"""
        
        try:
            endpoint = request.url.path
            method = request.method
            status_code = response.status_code
            user_id = self._extract_user_id(request)
            
            # Registrar métricas básicas da API
            await record_api_call(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                user_id=user_id
            )
            
            # Registrar eventos de negócio baseados no endpoint
            await self._record_business_metrics(request, response, user_id)
            
        except Exception as e:
            logger.error(f"Error recording metrics: {e}")
    
    async def _record_error_metrics(self, request: Request, response_time_ms: float,
                                  request_context: Dict[str, Any], error: str):
        """Registrar métricas de erro"""
        
        try:
            await record_api_call(
                endpoint=request.url.path,
                method=request.method,
                status_code=500,
                response_time_ms=response_time_ms,
                user_id=self._extract_user_id(request)
            )
            
        except Exception as e:
            logger.error(f"Error recording error metrics: {e}")
    
    async def _record_business_metrics(self, request: Request, response: Response, user_id: str):
        """Registrar métricas de negócio baseadas no endpoint"""
        
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        
        # Só registrar para requisições bem-sucedidas
        if status_code >= 400:
            return
        
        metadata = {
            'endpoint': endpoint,
            'method': method,
            'user_id': user_id or 'anonymous',
            'status_code': str(status_code)
        }
        
        try:
            # Webhook do WhatsApp - mensagem processada
            if endpoint.startswith('/webhook') and method == 'POST':
                await record_business_event('message_processed', 1.0, metadata)
            
            # Endpoints de conversa
            elif endpoint.startswith('/conversations'):
                if method == 'POST':
                    await record_business_event('conversation_started', 1.0, metadata)
            
            # Endpoints de agendamento
            elif endpoint.startswith('/bookings'):
                if method == 'POST':
                    await record_business_event('booking_created', 1.0, metadata)
            
            # Endpoints de leads
            elif endpoint.startswith('/leads'):
                if method == 'POST':
                    await record_business_event('lead_generated', 1.0, metadata)
            
        except Exception as e:
            logger.error(f"Error recording business metrics: {e}")
    
    def _extract_user_id(self, request: Request) -> str:
        """Extrair ID do usuário da requisição"""
        
        # Tentar extrair de headers de autenticação
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            # Em uma implementação real, decodificar o JWT
            return 'authenticated_user'
        
        # Tentar extrair de query params
        user_id = request.query_params.get('user_id')
        if user_id:
            return user_id
        
        # Tentar extrair do body (para webhooks)
        if hasattr(request, 'json') and request.url.path.startswith('/webhook'):
            return 'whatsapp_user'
        
        return 'anonymous'


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware focado especificamente em performance
    """
    
    def __init__(self, app: ASGIApp, slow_request_threshold_ms: float = 1000.0):
        super().__init__(app)
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.config = ConfigFactory.get_singleton_config()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitorar performance da requisição"""
        
        start_time = time.time()
        
        response = await call_next(request)
        
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Log de requisições lentas
        if response_time_ms > self.slow_request_threshold_ms:
            logger.warning(f"Slow request detected: {request.method} {request.url.path}", {
                'response_time_ms': round(response_time_ms, 2),
                'threshold_ms': self.slow_request_threshold_ms,
                'endpoint': request.url.path,
                'method': request.method
            })
        
        # Adicionar header de performance
        response.headers['X-Performance-Warning'] = (
            'slow' if response_time_ms > self.slow_request_threshold_ms else 'normal'
        )
        
        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware para health checks
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.startup_time = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processar health checks"""
        
        # Health check simples
        if request.url.path == '/health':
            uptime_seconds = time.time() - self.startup_time
            
            health_data = {
                'status': 'healthy',
                'uptime_seconds': round(uptime_seconds, 2),
                'timestamp': time.time(),
                'version': ConfigFactory.get_singleton_config().app_version
            }
            
            return JSONResponse(health_data)
        
        # Health check detalhado
        elif request.url.path == '/health/detailed':
            return await self._detailed_health_check()
        
        return await call_next(request)
    
    async def _detailed_health_check(self) -> JSONResponse:
        """Health check detalhado com métricas"""
        
        try:
            uptime_seconds = time.time() - self.startup_time
            config = ConfigFactory.get_singleton_config()
            
            # Obter dashboard de monitoramento se disponível
            monitoring_data = None
            if config.metrics_enabled:
                try:
                    from app.services.comprehensive_monitoring import get_monitoring_dashboard
                    monitoring_data = get_monitoring_dashboard()
                except Exception as e:
                    logger.error(f"Error getting monitoring dashboard: {e}")
            
            health_data = {
                'status': 'healthy',
                'timestamp': time.time(),
                'uptime_seconds': round(uptime_seconds, 2),
                'version': config.app_version,
                'environment': config.environment.value,
                'features': {
                    'metrics_enabled': config.metrics_enabled,
                    'alerting_enabled': config.alerting_enabled,
                    'business_metrics_enabled': config.business_metrics_enabled,
                    'prometheus_enabled': config.prometheus_enabled
                },
                'configuration': {
                    'sla_response_time_ms': config.sla_response_time_ms,
                    'sla_uptime_percentage': config.sla_uptime_percentage,
                    'rate_limit_requests': config.rate_limit_requests
                }
            }
            
            if monitoring_data:
                health_data['monitoring'] = monitoring_data
            
            return JSONResponse(health_data)
            
        except Exception as e:
            logger.error(f"Error in detailed health check: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': time.time()
                }
            )


# Função para adicionar middlewares à aplicação
def setup_monitoring_middlewares(app):
    """Configurar middlewares de monitoramento na aplicação"""
    
    config = ConfigFactory.get_singleton_config()
    
    # Health check middleware (sempre habilitado)
    app.add_middleware(HealthCheckMiddleware)
    
    # Performance middleware
    slow_threshold = config.alert_response_time_threshold_ms * 0.8  # 80% do threshold de alerta
    app.add_middleware(PerformanceMiddleware, slow_request_threshold_ms=slow_threshold)
    
    # Middleware principal de monitoramento
    if config.metrics_enabled:
        app.add_middleware(MonitoringMiddleware)
        logger.info("Monitoring middleware enabled")
    else:
        logger.info("Monitoring middleware disabled")
    
    return app
