from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Configurações da aplicação usando Sistema Robusto por Ambiente
DEPRECATED: Este arquivo será substituído pelo novo sistema de configuração
"""

# Import do novo sistema
from .config.config_factory import get_settings, get_database_url, is_development, is_production

# Manter compatibilidade com código existente
settings = get_settings()

# Para compatibilidade, manter algumas propriedades
class CompatibilitySettings:
    """Wrapper para manter compatibilidade com código existente"""
    
    def __init__(self):
        self._config = get_settings()
    
    def __getattr__(self, name):
        # Mapeamento de nomes antigos para novos
        mapping = {
            'meta_access_token': lambda: self._config.meta_access_token.get_secret_value() if self._config.meta_access_token else None,
            'openai_api_key': lambda: self._config.openai_api_key.get_secret_value() if self._config.openai_api_key else None,
            'webhook_verify_token': lambda: self._config.webhook_verify_token.get_secret_value() if self._config.webhook_verify_token else None,
            'admin_password': lambda: self._config.admin_password.get_secret_value() if self._config.admin_password else None,
            'database_url': lambda: self._config.database_dsn,
            'meta_api_version': lambda: self._config.meta_api_version,
            'whatsapp_webhook_secret': lambda: self._config.whatsapp_webhook_secret.get_secret_value() if self._config.whatsapp_webhook_secret else None,
            'database_dsn': lambda: self._config.database_url,
        }
        
        if name in mapping:
            try:
                return mapping[name]()
            except Exception as e:
                # Se falhar, tentar acessar diretamente da variável de ambiente
                if name == 'openai_api_key':
                    import os
                    return os.getenv('OPENAI_API_KEY')
                return None
        
        # Tentar acessar diretamente no config
        if hasattr(self._config, name):
            attr = getattr(self._config, name)
            # Se for SecretStr, retornar o valor
            if hasattr(attr, 'get_secret_value'):
                try:
                    return attr.get_secret_value()
                except Exception:
                    # Fallback para variável de ambiente
                    import os
                    return os.getenv(name.upper())
            return attr
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


# Instância de compatibilidade
settings = CompatibilitySettings()
