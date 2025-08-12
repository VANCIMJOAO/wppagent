"""
Middleware de Rate Limiting para Dashboard WhatsApp Agent
========================================================

Este módulo implementa middleware específico para integrar o sistema de rate limiting
com o dashboard Dash/Flask, fornecendo proteção transparente para todos os endpoints.

Recursos:
- Integração automática com Dash callbacks
- Middleware para Flask routes
- Proteção de endpoints específicos
- Logs detalhados de tentativas bloqueadas
- Interface de monitoramento
- Configuração dinâmica por endpoint
"""

import json
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from flask import Flask, request, jsonify, g
import dash
from dash import html, dcc, callback, Input, Output, State
from dash.exceptions import PreventUpdate

from app.utils.rate_limiter import (
    rate_limiter, RateLimitException, RateLimitConfig, 
    RateLimitLevel, RateLimitStrategy, get_client_ip_from_request,
    create_rate_limit_response
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Configurar logging
logger = logging.getLogger(__name__)

class DashRateLimitMiddleware:
    """Middleware para proteger aplicações Dash com rate limiting"""
    
    def __init__(self, app: dash.Dash, limiter=None):
        self.app = app
        self.limiter = limiter or rate_limiter
        self.protected_callbacks = {}
        self.setup_middleware()
    
    def setup_middleware(self):
        """Configurar middleware no app Dash"""
        # Interceptar requisições antes do processamento
        self.app.server.before_request(self.before_request)
        self.app.server.after_request(self.after_request)
        
        # Configurar rate limiting para diferentes tipos de callback
        self._setup_callback_protection()
    
    def before_request(self):
        """Executar antes de cada requisição"""
        start_time = time.time()
        g.start_time = start_time
        
        # Obter informações da requisição
        ip = get_client_ip_from_request(request)
        endpoint = request.endpoint or 'unknown'
        method = request.method
        path = request.path
        
        # Determinar tipo de endpoint
        endpoint_type = self._classify_endpoint(path, method)
        
        try:
            # Verificar rate limiting
            result = self.limiter.check_rate_limit(ip, endpoint_type)
            
            if not result.allowed:
                logger.warning(
                    f"🚫 Rate limit blocked - IP: {ip}, Endpoint: {endpoint_type}, "
                    f"Path: {path}, Reason: {result.reason}"
                )
                
                # Retornar resposta de erro
                if path.startswith('/_dash'):
                    # Resposta para callbacks Dash
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': result.reason,
                        'retry_after': result.retry_after
                    }), 429
                else:
                    # Resposta para outras requisições
                    return jsonify(create_rate_limit_response(result)), 429
            
            # Armazenar informações para logging
            g.rate_limit_info = {
                'ip': ip,
                'endpoint_type': endpoint_type,
                'remaining': result.remaining,
                'allowed': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no middleware de rate limiting: {e}")
            # Em caso de erro, permitir a requisição
            g.rate_limit_info = {'error': str(e)}
    
    def after_request(self, response):
        """Executar após cada requisição"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Log da requisição
            rate_info = getattr(g, 'rate_limit_info', {})
            if rate_info.get('allowed'):
                logger.info(
                    f"✅ Request processed - IP: {rate_info.get('ip')}, "
                    f"Type: {rate_info.get('endpoint_type')}, "
                    f"Duration: {duration:.3f}s, "
                    f"Remaining: {rate_info.get('remaining')}"
                )
        
        return response
    
    def _classify_endpoint(self, path: str, method: str) -> str:
        """Classificar tipo de endpoint para aplicar rate limiting apropriado"""
        # Callbacks Dash
        if path.startswith('/_dash'):
            if 'component-suites' in path:
                return 'dashboard_assets'
            elif 'dependencies' in path:
                return 'dashboard_callback'
            else:
                return 'dashboard'
        
        # Endpoints de autenticação
        if any(auth_path in path.lower() for auth_path in ['/login', '/auth', '/signin']):
            return 'auth_login'
        
        # APIs
        if path.startswith('/api'):
            if method == 'POST' and 'message' in path:
                return 'send_message'
            elif method == 'POST' and 'upload' in path:
                return 'file_upload'
            else:
                return 'api_public'
        
        # Assets estáticos
        if any(ext in path for ext in ['.css', '.js', '.png', '.jpg', '.ico']):
            return 'static_assets'
        
        # Dashboard padrão
        return 'dashboard'
    
    def _setup_callback_protection(self):
        """Configurar proteção específica para callbacks"""
        # Configurações específicas para diferentes tipos de callback
        callback_configs = {
            'dashboard_callback': RateLimitConfig(
                requests_per_window=150,
                window_size=60,
                burst_limit=30,
                level=RateLimitLevel.MEDIUM
            ),
            'dashboard_assets': RateLimitConfig(
                requests_per_window=500,
                window_size=60,
                burst_limit=100,
                level=RateLimitLevel.LOW
            ),
            'static_assets': RateLimitConfig(
                requests_per_window=1000,
                window_size=60,
                burst_limit=200,
                level=RateLimitLevel.LOW
            )
        }
        
        for endpoint, config in callback_configs.items():
            self.limiter.add_config(endpoint, config)
    
    def protect_callback(self, endpoint_type: str = 'dashboard_callback'):
        """Decorator para proteger callbacks específicos"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    ip = get_client_ip_from_request()
                    result = self.limiter.check_rate_limit(ip, endpoint_type)
                    
                    if not result.allowed:
                        logger.warning(f"🚫 Callback blocked - {endpoint_type}: {result.reason}")
                        raise PreventUpdate
                    
                    return func(*args, **kwargs)
                except RateLimitException:
                    raise PreventUpdate
                except Exception as e:
                    logger.error(f"❌ Erro em callback protegido: {e}")
                    raise PreventUpdate
            
            return wrapper
        return decorator

class FlaskRateLimitMiddleware:
    """Middleware para proteger aplicações Flask com rate limiting"""
    
    def __init__(self, app: Flask, limiter=None):
        self.app = app
        self.limiter = limiter or rate_limiter
        self.setup_middleware()
    
    def setup_middleware(self):
        """Configurar middleware no app Flask"""
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        self.app.errorhandler(429)(self.handle_rate_limit_error)
    
    def before_request(self):
        """Executar antes de cada requisição"""
        ip = get_client_ip_from_request(request)
        endpoint = request.endpoint or 'unknown'
        
        try:
            result = self.limiter.check_rate_limit(ip, endpoint)
            
            if not result.allowed:
                return jsonify(create_rate_limit_response(result)), 429
                
        except Exception as e:
            logger.error(f"❌ Erro no middleware Flask: {e}")
    
    def after_request(self, response):
        """Executar após cada requisição"""
        return response
    
    def handle_rate_limit_error(self, error):
        """Tratar erros de rate limiting"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests'
        }), 429

class RateLimitMonitor:
    """Monitor para visualizar estatísticas de rate limiting no dashboard"""
    
    def __init__(self, limiter=None):
        self.limiter = limiter or rate_limiter
    
    def create_monitoring_layout(self):
        """Criar layout para monitoramento de rate limiting"""
        return html.Div([
            html.H2("🛡️ Monitor de Rate Limiting", className="mb-4"),
            
            # Estatísticas gerais
            html.Div([
                html.H4("📊 Estatísticas Gerais"),
                html.Div(id="rate-limit-stats", children=[
                    self._create_stats_cards()
                ])
            ], className="mb-4"),
            
            # IPs bloqueados
            html.Div([
                html.H4("🔒 IPs Bloqueados"),
                html.Div(id="blocked-ips-list")
            ], className="mb-4"),
            
            # Violações recentes
            html.Div([
                html.H4("⚠️ Violações Recentes"),
                html.Div(id="recent-violations")
            ], className="mb-4"),
            
            # Configurações
            html.Div([
                html.H4("⚙️ Configurações de Rate Limiting"),
                html.Div(id="rate-limit-configs")
            ]),
            
            # Auto-refresh
            dcc.Interval(
                id='rate-limit-refresh',
                interval=30*1000,  # 30 segundos
                n_intervals=0
            )
        ])
    
    def _create_stats_cards(self):
        """Criar cards com estatísticas"""
        stats = self.limiter.get_stats()
        
        return html.Div([
            html.Div([
                html.H5("Total de Violações"),
                html.H3(str(stats.get('total_violations', 0)), 
                       className="text-danger")
            ], className="card p-3 m-2", style={"width": "200px", "display": "inline-block"}),
            
            html.Div([
                html.H5("IPs Bloqueados"),
                html.H3(str(stats.get('blocked_ips', 0)), 
                       className="text-warning")
            ], className="card p-3 m-2", style={"width": "200px", "display": "inline-block"}),
            
            html.Div([
                html.H5("Endpoints Protegidos"),
                html.H3(str(len(stats.get('configs', {}))), 
                       className="text-info")
            ], className="card p-3 m-2", style={"width": "200px", "display": "inline-block"})
        ])
    
    def setup_callbacks(self, app):
        """Configurar callbacks para o monitor"""
        
        @app.callback(
            [Output('rate-limit-stats', 'children'),
             Output('blocked-ips-list', 'children'),
             Output('recent-violations', 'children'),
             Output('rate-limit-configs', 'children')],
            [Input('rate-limit-refresh', 'n_intervals')]
        )
        def update_monitor(n_intervals):
            try:
                stats = self.limiter.get_stats()
                
                # Atualizar estatísticas
                stats_cards = self._create_stats_cards()
                
                # Lista de IPs bloqueados
                blocked_ips = html.Ul([
                    html.Li(f"🔒 {ip}") 
                    for ip in stats.get('blocked_ip_list', [])
                ]) if stats.get('blocked_ip_list') else html.P("Nenhum IP bloqueado")
                
                # Violações por IP
                violations_by_ip = stats.get('violation_by_ip', {})
                recent_violations = html.Ul([
                    html.Li(f"⚠️ {ip}: {count} violações")
                    for ip, count in violations_by_ip.items()
                    if count > 0
                ]) if violations_by_ip else html.P("Nenhuma violação recente")
                
                # Configurações
                configs = stats.get('configs', {})
                config_list = html.Ul([
                    html.Li([
                        html.Strong(f"{endpoint}: "),
                        f"{config.get('requests_per_window', 0)} req/{config.get('window_size', 0)}s"
                    ])
                    for endpoint, config in configs.items()
                ])
                
                return stats_cards, blocked_ips, recent_violations, config_list
                
            except Exception as e:
                logger.error(f"❌ Erro ao atualizar monitor: {e}")
                error_msg = html.Div([
                    html.P(f"Erro ao carregar dados: {str(e)}", className="text-danger")
                ])
                return error_msg, error_msg, error_msg, error_msg

def setup_advanced_rate_limiting(app, app_type='dash'):
    """
    Configurar rate limiting avançado para aplicação
    
    Args:
        app: Aplicação Dash ou Flask
        app_type: Tipo da aplicação ('dash' ou 'flask')
    
    Returns:
        Middleware configurado
    """
    logger.info(f"🛡️ Configurando rate limiting avançado para {app_type}")
    
    if app_type == 'dash':
        middleware = DashRateLimitMiddleware(app)
        
        # Configurar proteções específicas para o dashboard (AJUSTADO PARA PRODUÇÃO)
        dashboard_configs = {
            'dashboard_heavy': RateLimitConfig(
                requests_per_window=200,  # Aumentado de 50 para 200
                window_size=60,
                burst_limit=50,           # Aumentado de 10 para 50
                level=RateLimitLevel.MEDIUM  # Reduzido de HIGH para MEDIUM
            ),
            'dashboard_export': RateLimitConfig(
                requests_per_window=10,   # Aumentado de 5 para 10
                window_size=300,  # 5 minutos
                burst_limit=5,            # Aumentado de 2 para 5
                block_duration=300,       # Reduzido de 600 para 300 segundos
                level=RateLimitLevel.HIGH # Reduzido de CRITICAL para HIGH
            ),
            'dashboard_auth': RateLimitConfig(
                requests_per_window=100,  # Novo: específico para autenticação
                window_size=60,
                burst_limit=20,
                block_duration=60,        # Bloqueio curto para auth
                level=RateLimitLevel.LOW  # Mais permissivo para auth
            )
        }
        
        for endpoint, config in dashboard_configs.items():
            rate_limiter.add_config(endpoint, config)
        
    elif app_type == 'flask':
        middleware = FlaskRateLimitMiddleware(app)
    else:
        raise ValueError(f"Tipo de app não suportado: {app_type}")
    
    logger.info("✅ Rate limiting configurado com sucesso")
    return middleware

# Decorators específicos para diferentes tipos de proteção
def protect_auth_endpoint(func):
    """Proteger endpoints de autenticação com rate limiting rigoroso"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        ip = get_client_ip_from_request()
        result = rate_limiter.check_rate_limit(ip, 'auth_login')
        
        if not result.allowed:
            raise RateLimitException(
                f"Muitas tentativas de login. Tente novamente em {result.retry_after} segundos.",
                retry_after=result.retry_after
            )
        
        return func(*args, **kwargs)
    return wrapper

def protect_api_endpoint(endpoint_type='api_public'):
    """Proteger endpoints de API com rate limiting configurável"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ip = get_client_ip_from_request()
            result = rate_limiter.check_rate_limit(ip, endpoint_type)
            
            if not result.allowed:
                raise RateLimitException(
                    f"Rate limit excedido para {endpoint_type}",
                    retry_after=result.retry_after
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def protect_heavy_operation(func):
    """Proteger operações pesadas com rate limiting específico"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        ip = get_client_ip_from_request()
        result = rate_limiter.check_rate_limit(ip, 'dashboard_heavy')
        
        if not result.allowed:
            raise RateLimitException(
                "Operação temporariamente indisponível. Muitas requisições pesadas.",
                retry_after=result.retry_after
            )
        
        return func(*args, **kwargs)
    return wrapper

if __name__ == "__main__":
    # Teste do monitor
    monitor = RateLimitMonitor()
    layout = monitor.create_monitoring_layout()
    logger.info("✅ Monitor de rate limiting criado com sucesso")
