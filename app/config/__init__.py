# Pacote de configuração do WhatsApp Agent

from .config_factory import get_settings, get_database_url, is_development, is_production

# Exportar settings para compatibilidade
settings = get_settings()

__all__ = ['get_settings', 'get_database_url', 'is_development', 'is_production', 'settings']
