"""
Sistema de Error Handling - Dashboard WppAgent
============================================

Manipulação centralizada de erros com feedback visual para usuário.
Converte exceções técnicas em mensagens amigáveis com ações sugeridas.
"""

import logging
from typing import Optional, Any, Dict
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class ErrorSeverity:
    """Níveis de severidade dos erros"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory:
    """Categorias de erro"""
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    PERMISSION = "permission"
    DATA = "data"
    GENERIC = "generic"

def handle_api_error(error: Exception, context: str = "operação", component_id: str = None) -> dmc.Alert:
    """
    Manipula erros de API com feedback visual
    
    Args:
        error: Exception capturada
        context: Contexto da operação (ex: "carregamento de conversas")
        component_id: ID do componente para callbacks específicos
        
    Returns:
        dmc.Alert: Componente de erro com feedback visual
    """
    error_str = str(error).lower()
    error_type = _classify_error(error_str)
    severity = _determine_severity(error_type)
    
    # Log detalhado do erro
    logger.error(f"🚨 Erro na {context}: {str(error)}")
    logger.debug(f"Stack trace: {traceback.format_exc()}")
    
    # Métricas de erro (para futuros dashboards de monitoramento)
    _record_error_metrics(error_type, context, severity)
    
    # Retornar componente visual apropriado
    return _create_error_component(error_type, context, component_id, severity)

def _classify_error(error_str: str) -> str:
    """Classifica o tipo de erro baseado na mensagem"""
    
    if any(word in error_str for word in ["connection", "network", "unreachable", "refused"]):
        return ErrorCategory.CONNECTION
        
    elif any(word in error_str for word in ["401", "unauthorized", "authentication", "token", "login"]):
        return ErrorCategory.AUTHENTICATION
        
    elif any(word in error_str for word in ["timeout", "timed out", "deadline exceeded"]):
        return ErrorCategory.TIMEOUT
        
    elif any(word in error_str for word in ["403", "forbidden", "permission", "access denied"]):
        return ErrorCategory.PERMISSION
        
    elif any(word in error_str for word in ["400", "validation", "invalid", "required"]):
        return ErrorCategory.VALIDATION
        
    elif any(word in error_str for word in ["404", "not found", "missing", "empty"]):
        return ErrorCategory.DATA
        
    else:
        return ErrorCategory.GENERIC

def _determine_severity(error_type: str) -> str:
    """Determina a severidade baseada no tipo de erro"""
    
    severity_map = {
        ErrorCategory.CONNECTION: ErrorSeverity.HIGH,
        ErrorCategory.AUTHENTICATION: ErrorSeverity.MEDIUM,
        ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
        ErrorCategory.PERMISSION: ErrorSeverity.HIGH,
        ErrorCategory.VALIDATION: ErrorSeverity.LOW,
        ErrorCategory.DATA: ErrorSeverity.LOW,
        ErrorCategory.GENERIC: ErrorSeverity.MEDIUM
    }
    
    return severity_map.get(error_type, ErrorSeverity.MEDIUM)

def _create_error_component(error_type: str, context: str, component_id: str, severity: str) -> dmc.Alert:
    """Cria o componente visual de erro apropriado"""
    
    component_creators = {
        ErrorCategory.CONNECTION: create_connection_error_component,
        ErrorCategory.AUTHENTICATION: create_auth_error_component,
        ErrorCategory.TIMEOUT: create_timeout_error_component,
        ErrorCategory.PERMISSION: create_permission_error_component,
        ErrorCategory.VALIDATION: create_validation_error_component,
        ErrorCategory.DATA: create_data_error_component,
        ErrorCategory.GENERIC: create_generic_error_component
    }
    
    creator = component_creators.get(error_type, create_generic_error_component)
    return creator(context, component_id, severity)

def create_connection_error_component(context: str = "operação", component_id: str = None, severity: str = ErrorSeverity.HIGH) -> html.Div:
    """Componente de erro de conexão compatível com DMC 0.12.1"""
    
    retry_id = f"retry-connection-btn-{component_id}" if component_id else "retry-connection-btn"
    
    return html.Div([
        dmc.Alert(
            children=[
                html.Div([
                    html.P("Não foi possível conectar ao servidor. Verifique sua conexão com a internet.", 
                           style={"margin": "0 0 10px 0"}),
                    html.P("💡 Tente recarregar a página ou aguarde alguns segundos.", 
                           style={"margin": "0 0 15px 0", "fontSize": "14px", "color": "#666"})
                ])
            ],
            title=f"Erro de Conexão - {context.title()}",
            icon=DashIconify(icon="tabler:wifi-off", width=20),
            color="red",
            variant="filled" if severity == ErrorSeverity.CRITICAL else "light"
        ),
        dmc.Button(
            "Tentar Novamente", 
            id=retry_id,
            variant="light", 
            color="red",
            leftIcon=DashIconify(icon="tabler:refresh", width=16),
            style={"marginTop": "10px"}
        )
    ])

def create_auth_error_component(context: str = "operação", component_id: str = None, severity: str = ErrorSeverity.MEDIUM) -> html.Div:
    """Componente de erro de autenticação compatível com DMC 0.12.1"""
    
    login_id = f"goto-login-btn-{component_id}" if component_id else "goto-login-btn"
    
    return html.Div([
        dmc.Alert(
            children=[
                html.Div([
                    html.P("Sua sessão expirou ou você não tem permissão para acessar este recurso.", 
                           style={"margin": "0 0 10px 0"}),
                    html.P("🔐 Faça login novamente para continuar.", 
                           style={"margin": "0 0 15px 0", "fontSize": "14px", "color": "#666"})
                ])
            ],
            title=f"Autenticação Necessária - {context.title()}",
            icon=DashIconify(icon="tabler:lock", width=20),
            color="yellow",
            variant="filled" if severity == ErrorSeverity.HIGH else "light"
        ),
        dmc.Button(
            "Fazer Login", 
            id=login_id,
            variant="light", 
            color="yellow",
            leftIcon=DashIconify(icon="tabler:login", width=16),
            style={"marginTop": "10px"}
        )
    ])

def create_timeout_error_component(context: str = "operação", component_id: str = None, severity: str = ErrorSeverity.MEDIUM) -> html.Div:
    """Componente de erro de timeout compatível com DMC 0.12.1"""
    
    retry_id = f"retry-timeout-btn-{component_id}" if component_id else "retry-timeout-btn"
    
    return html.Div([
        dmc.Alert(
            children=[
                html.Div([
                    html.P("A operação demorou mais que o esperado e foi cancelada.", 
                           style={"margin": "0 0 10px 0"}),
                    html.P("⏱️ Isso pode acontecer em momentos de alta demanda.", 
                           style={"margin": "0 0 15px 0", "fontSize": "14px", "color": "#666"})
                ])
            ],
            title=f"Timeout - {context.title()}",
            icon=DashIconify(icon="tabler:clock-x", width=20),
            color="orange"
        ),
        dmc.Button(
            "Tentar Novamente", 
            id=retry_id,
            variant="light", 
            color="orange",
            leftIcon=DashIconify(icon="tabler:refresh", width=16),
            style={"marginTop": "10px"}
        )
    ])

def create_permission_error_component(context: str = "operação", component_id: str = None, severity: str = ErrorSeverity.HIGH) -> dmc.Alert:
    """Componente de erro de permissão"""
    
    return dmc.Alert(
        children=[
            html.Div([
                html.P("Você não tem permissão para realizar esta operação.", 
                       style={"margin": "0 0 10px 0"}),
                html.P("🛡️ Entre em contato com o administrador se precisar de acesso.", 
                       style={"margin": "0", "fontSize": "14px", "color": "#666"})
            ])
        ],
        title=f"Acesso Negado - {context.title()}",
        icon=DashIconify(icon="tabler:shield-x", width=20),
        color="red",
        variant="light"
    )

def create_validation_error_component(context: str = "operação", component_id: str = None, severity: str = ErrorSeverity.LOW) -> dmc.Alert:
    """Componente de erro de validação"""
    
    return dmc.Alert(
        children=[
            html.Div([
                html.P("Alguns dados fornecidos são inválidos ou estão faltando.", 
                       style={"margin": "0 0 10px 0"}),
                html.P("📋 Verifique os campos obrigatórios e tente novamente.", 
                       style={"margin": "0", "fontSize": "14px", "color": "#666"})
            ])
        ],
        title=f"Dados Inválidos - {context.title()}",
        icon=DashIconify(icon="tabler:alert-triangle", width=20),
        color="yellow",
        variant="light"
    )

def create_data_error_component(context: str = "operação", component_id: str = None, severity: str = ErrorSeverity.LOW) -> dmc.Alert:
    """Componente de erro de dados não encontrados"""
    
    return dmc.Alert(
        children=[
            html.Div([
                html.P("Os dados solicitados não foram encontrados ou estão indisponíveis.", 
                       style={"margin": "0 0 10px 0"}),
                html.P("📄 Tente recarregar ou verificar se os dados existem.", 
                       style={"margin": "0", "fontSize": "14px", "color": "#666"})
            ])
        ],
        title=f"Dados Não Encontrados - {context.title()}",
        icon=DashIconify(icon="tabler:database-x", width=20),
        color="gray",
        variant="light"
    )

def create_generic_error_component(context: str = "operação", component_id: str = None, severity: str = ErrorSeverity.MEDIUM) -> html.Div:
    """Componente de erro genérico compatível com DMC 0.12.1"""
    
    retry_id = f"retry-generic-btn-{component_id}" if component_id else "retry-generic-btn"
    
    return html.Div([
        dmc.Alert(
            children=[
                html.Div([
                    html.P(f"Ocorreu um erro inesperado durante {context}.", 
                           style={"margin": "0 0 10px 0"}),
                    html.P("🔧 Tente novamente ou contate o suporte se o problema persistir.", 
                           style={"margin": "0 0 15px 0", "fontSize": "14px", "color": "#666"})
                ])
            ],
            title=f"Erro Inesperado - {context.title()}",
            icon=DashIconify(icon="tabler:exclamation-circle", width=20),
            color="red",
            variant="light"
        ),
        dmc.Button(
            "Tentar Novamente", 
            id=retry_id,
            variant="light", 
            color="red",
            leftIcon=DashIconify(icon="tabler:refresh", width=16),
            style={"marginTop": "10px"}
        )
    ])

def create_loading_error_fallback(context: str = "carregamento") -> dmc.Alert:
    """Componente de fallback para erros durante loading"""
    
    return dmc.Alert(
        children=[
            html.Div([
                html.P(f"Erro durante {context}. Alguns dados podem não estar atualizados.", 
                       style={"margin": "0 0 10px 0"}),
                html.P("⚡ A página continuará funcionando com os dados em cache.", 
                       style={"margin": "0", "fontSize": "14px", "color": "#666"})
            ])
        ],
        title="Atenção",
        icon=DashIconify(icon="tabler:alert-circle", width=20),
        color="yellow",
        variant="light"
    )

def _record_error_metrics(error_type: str, context: str, severity: str):
    """Registra métricas de erro para monitoramento"""
    
    timestamp = datetime.now().isoformat()
    
    # Log estruturado para futura integração com sistemas de monitoramento
    logger.info(f"ERROR_METRIC: {{'type': '{error_type}', 'context': '{context}', 'severity': '{severity}', 'timestamp': '{timestamp}'}}")

def safe_execute(func, *args, fallback_value=None, context="operação", component_id=None, **kwargs):
    """
    Executa função com error handling seguro
    
    Args:
        func: Função a ser executada
        *args: Argumentos posicionais
        fallback_value: Valor retornado em caso de erro
        context: Contexto da operação
        component_id: ID do componente
        **kwargs: Argumentos nomeados
        
    Returns:
        Resultado da função ou componente de erro
    """
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"🚨 Erro em safe_execute ({context}): {str(e)}")
        
        if fallback_value is not None:
            return fallback_value
        else:
            return handle_api_error(e, context, component_id)

# Decorator para métodos que precisam de error handling
def with_error_handling(context: str = "operação", fallback_value=None):
    """
    Decorator para adicionar error handling automático a funções
    
    Usage:
        @with_error_handling("carregamento de conversas", fallback_value=[])
        def get_conversations():
            return db_service.get_conversations()
    """
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            return safe_execute(func, *args, fallback_value=fallback_value, context=context, **kwargs)
        return wrapper
    return decorator
