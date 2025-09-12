# Pacote de configuração do WhatsApp Agent

from .config_factory import get_database_url, is_development, is_production
from .config_factory import ConfigFactory

# ✅ COH-001: Função simples para obter configuração original
def get_settings():
    """Retorna configuração original do factory"""
    try:
        return ConfigFactory.get_config()
    except Exception:
        # Fallback para configuração básica
        from .environments import DevelopmentConfig
        return DevelopmentConfig()

# ✅ COH-001: Proxy simples sem dependência circular
settings = get_settings()

__all__ = ['get_settings', 'get_database_url', 'is_development', 'is_production', 'settings']
