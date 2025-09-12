from app.utils.logger import get_logger
import os

logger = get_logger(__name__)
"""
🔧 COH-001 FIX: Sistema de Configuração Unificado
Configurações da aplicação com acesso consistente para Backend↔Frontend
"""

class UnifiedConfigSettings:
    """
    🔧 COH-001 - Sistema de configuração unificado
    Elimina mapeamentos manuais complexos e garante acesso consistente
    """
    
    def __init__(self):
        self._cached_secrets = {}  # Cache para evitar múltiplas chamadas
        logger.info("🔧 COH-001: Sistema de configuração unificado inicializado")
    
    def _get_env_safely(self, env_key: str, default=None):
        """Método seguro para obter variáveis de ambiente"""
        try:
            value = os.getenv(env_key, default)
            return value
        except Exception as e:
            logger.warning(f"🔧 COH-001: Erro ao acessar env {env_key}: {e}")
            return default
    
    # ✅ Propriedades principais com acesso unificado baseado em variáveis de ambiente
    @property
    def meta_access_token(self):
        return self._get_env_safely('META_ACCESS_TOKEN')
    
    @property
    def openai_api_key(self):
        return self._get_env_safely('OPENAI_API_KEY')
    
    @property
    def webhook_verify_token(self):
        return self._get_env_safely('WEBHOOK_VERIFY_TOKEN')
    
    @property
    def admin_password(self):
        return self._get_env_safely('ADMIN_PASSWORD', 'admin123')  # Default para desenvolvimento
    
    @property
    def whatsapp_webhook_secret(self):
        return self._get_env_safely('WHATSAPP_WEBHOOK_SECRET')
    
    @property
    def secret_key(self):
        return self._get_env_safely('SECRET_KEY', 'your-secret-key-here')  # Default para desenvolvimento
    
    # ✅ Configurações não-secretas
    @property
    def database_url(self):
        return self._get_env_safely('DATABASE_URL')
    
    @property
    def database_dsn(self):
        return self.database_url  # Alias para compatibilidade
    
    @property
    def meta_api_version(self):
        return self._get_env_safely('META_API_VERSION', 'v17.0')
    
    # ✅ VAPID configuration
    @property
    def VAPID_PRIVATE_KEY(self):
        return self._get_env_safely('VAPID_PRIVATE_KEY')
    
    @property
    def VAPID_PUBLIC_KEY(self):
        return self._get_env_safely('VAPID_PUBLIC_KEY')
    
    @property
    def VAPID_PUBLIC_KEY_FRONTEND(self):
        return self._get_env_safely('VAPID_PUBLIC_KEY_FRONTEND')
    
    @property
    def VAPID_SUBJECT(self):
        return self._get_env_safely('VAPID_SUBJECT')
    
    # ✅ App configuration
    @property
    def app_host(self):
        return "0.0.0.0"
    
    @property  
    def app_port(self):
        return 8000
    
    @property
    def debug(self):
        return self._get_env_safely('ENVIRONMENT', 'development').lower() == 'development'
    
    @property
    def log_level(self):
        return "INFO"
    
    # ✅ Método de diagnóstico para validação
    def validate_secrets_access(self) -> dict:
        """COH-001: Validar que todas as configurações secrets são acessíveis"""
        validation_results = {}
        
        secret_fields = [
            'meta_access_token', 'openai_api_key', 'webhook_verify_token',
            'admin_password', 'whatsapp_webhook_secret', 'secret_key',
            'VAPID_PRIVATE_KEY'
        ]
        
        for field in secret_fields:
            try:
                value = getattr(self, field)
                validation_results[field] = {
                    'accessible': value is not None,
                    'length': len(value) if value else 0,
                    'preview': value[:8] + "..." if value and len(value) > 8 else "None"
                }
            except Exception as e:
                validation_results[field] = {
                    'accessible': False,
                    'error': str(e)
                }
        
        return validation_results
    
    def __getattr__(self, name):
        """Fallback para acessos legacy"""
        # Tentar variável de ambiente
        env_value = self._get_env_safely(name.upper())
        if env_value:
            return env_value
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

# ✅ COH-001: Instância unificada de configuração
settings = UnifiedConfigSettings()

# ✅ Para compatibilidade com imports existentes
def get_settings():
    """Função de compatibilidade que retorna a instância unificada"""
    return settings

def get_database_url():
    """Função de compatibilidade para database URL"""
    return settings.database_url

def is_development():
    """Função de compatibilidade para verificar ambiente de desenvolvimento"""
    return settings.debug

def is_production():
    """Função de compatibilidade para verificar ambiente de produção"""
    return not settings.debug
