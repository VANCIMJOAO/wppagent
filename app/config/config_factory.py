"""
Factory de Configuração Inteligente
WhatsApp Agent - Gerenciamento Automático de Configurações
"""
import os
from typing import Type, Dict, Any, Optional
from functools import lru_cache

from .environment_config import (
    BaseConfig, 
    Environment,
    DevelopmentConfig,
    TestConfig as TestingConfig,
    StagingConfig,
    ProductionConfig
)

# Logger será inicializado após a configuração estar disponível
_logger = None

def get_logger():
    """Lazy loading do logger para evitar dependência circular"""
    global _logger
    if _logger is None:
        import logging
        _logger = logging.getLogger(__name__)
    return _logger


class ConfigurationError(Exception):
    """Erro de configuração"""
    pass


class ConfigFactory:
    """Factory para criação de configurações por ambiente"""
    
    _config_classes: Dict[Environment, Type[BaseConfig]] = {
        Environment.DEVELOPMENT: DevelopmentConfig,
        Environment.TEST: TestingConfig,
        Environment.STAGING: StagingConfig,
        Environment.PRODUCTION: ProductionConfig
    }
    
    _instance: Optional[BaseConfig] = None
    
    @classmethod
    def get_config_class(cls, environment: Environment) -> Type[BaseConfig]:
        """Obter classe de configuração para ambiente"""
        config_class = cls._config_classes.get(environment)
        if not config_class:
            raise ConfigurationError(f"Configuração não encontrada para ambiente: {environment}")
        return config_class
    
    @classmethod
    def create_config(cls, environment: Optional[Environment] = None) -> BaseConfig:
        """Criar configuração para ambiente especificado"""
        if environment is None:
            environment = cls._detect_environment()
        
        config_class = cls.get_config_class(environment)
        
        try:
            config = config_class()
            cls._validate_configuration(config)
            import logging
            logging.getLogger(__name__).info(f"✅ Configuração carregada para ambiente: {environment}")
            return config
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"❌ Erro ao carregar configuração para {environment}: {e}")
            raise ConfigurationError(f"Falha ao criar configuração: {e}")
    
    @classmethod
    def _detect_environment(cls) -> Environment:
        """Detectar ambiente automaticamente"""
        env_var = os.getenv('ENVIRONMENT', '').lower()
        
        # Mapeamento de valores comuns
        env_mapping = {
            'dev': Environment.DEVELOPMENT,
            'develop': Environment.DEVELOPMENT,
            'development': Environment.DEVELOPMENT,
            'test': Environment.TEST,
            'testing': Environment.TEST,
            'stage': Environment.STAGING,
            'staging': Environment.STAGING,
            'prod': Environment.PRODUCTION,
            'production': Environment.PRODUCTION
        }
        
        environment = env_mapping.get(env_var, Environment.DEVELOPMENT)
        
        # Log da detecção
        import logging
        logging.getLogger(__name__).info(f"🔍 Ambiente detectado: {environment} (de ENVIRONMENT={env_var})")
        
        return environment
    
    @classmethod
    def _validate_configuration(cls, config: BaseConfig) -> None:
        """Validar configuração carregada"""
        issues = []
        
        # Validar APIs obrigatórias para produção
        if config.environment == Environment.PRODUCTION:
            required_secrets = [
                ('openai_api_key', config.openai_api_key),
                ('whatsapp_token', config.whatsapp_token),
                ('webhook_secret', config.webhook_secret)
            ]
            
            for name, secret in required_secrets:
                if not secret or not secret.get_secret_value():
                    issues.append(f"❌ {name} não configurado para produção")
        
        # Validar senhas fracas
        if config.environment in [Environment.STAGING, Environment.PRODUCTION]:
            admin_password = config.admin_password.get_secret_value()
            weak_passwords = ['admin', 'os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")', 'password', '123456', 'qwerty']
            if admin_password.lower() in weak_passwords:
                issues.append("❌ Senha do admin muito fraca para ambiente seguro")
        
        # Validar debug em produção
        if config.environment == Environment.PRODUCTION and config.debug:
            issues.append("❌ Debug não pode estar ativo em produção")
        
        if issues:
            error_msg = "Problemas de configuração encontrados:\n" + "\n".join(issues)
            raise ConfigurationError(error_msg)
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_singleton_config(cls) -> BaseConfig:
        """Obter configuração singleton (cached)"""
        if cls._instance is None:
            cls._instance = cls.create_config()
        return cls._instance
    
    @classmethod
    def reload_config(cls) -> BaseConfig:
        """Recarregar configuração (limpar cache)"""
        cls.get_singleton_config.cache_clear()
        cls._instance = None
        return cls.get_singleton_config()
    
    @classmethod
    def get_config_summary(cls, config: BaseConfig) -> Dict[str, Any]:
        """Obter resumo da configuração (sem secrets)"""
        return {
            "environment": config.environment,
            "debug": config.debug,
            "security_level": config.security_level,
            "app_name": config.app_name,
            "app_version": config.app_version,
            "workers": config.workers,
            "rate_limit_enabled": config.rate_limit_enabled,
            "metrics_enabled": config.metrics_enabled,
            "health_check_enabled": config.health_check_enabled,
            "redis_enabled": config.redis_enabled,
            "log_level": config.log_level,
            "log_format": config.log_format
        }


# ==============================
# FUNÇÕES DE CONVENIÊNCIA
# ==============================

@lru_cache(maxsize=1)
def get_settings() -> BaseConfig:
    """Obter configurações da aplicação (função principal)"""
    return ConfigFactory.get_singleton_config()


def get_config_for_environment(environment: Environment) -> BaseConfig:
    """Obter configuração para ambiente específico"""
    return ConfigFactory.create_config(environment)


def reload_settings() -> BaseConfig:
    """Recarregar configurações"""
    get_settings.cache_clear()
    return ConfigFactory.reload_config()


def get_database_url() -> str:
    """Obter URL do banco de dados"""
    return get_settings().database_dsn


def get_redis_url() -> str:
    """Obter URL do Redis"""
    return get_settings().redis_url


def is_development() -> bool:
    """Verificar se está em desenvolvimento"""
    return get_settings().is_development


def is_production() -> bool:
    """Verificar se está em produção"""
    return get_settings().environment == Environment.PRODUCTION


def get_security_headers() -> Dict[str, str]:
    """Obter headers de segurança"""
    return get_settings().get_security_headers()


def get_cors_settings() -> Dict[str, Any]:
    """Obter configurações CORS"""
    return get_settings().get_cors_settings()


# ==============================
# HEALTH CHECK DA CONFIGURAÇÃO
# ==============================

def health_check_config() -> Dict[str, Any]:
    """Health check da configuração"""
    try:
        config = get_settings()
        summary = ConfigFactory.get_config_summary(config)
        
        # Verificar integridade
        issues = []
        
        # Verificar conexão com banco (se possível)
        try:
            # TODO: Implementar verificação real de conexão
            db_status = "unknown"
        except Exception as e:
            db_status = f"error: {e}"
            issues.append("Database connection failed")
        
        # Verificar APIs (sem expor secrets)
        api_status = {}
        if config.openai_api_key and config.openai_api_key.get_secret_value():
            api_status["openai"] = "configured"
        else:
            api_status["openai"] = "missing"
            if config.environment == Environment.PRODUCTION:
                issues.append("OpenAI API key missing in production")
        
        if config.whatsapp_token and config.whatsapp_token.get_secret_value():
            api_status["whatsapp"] = "configured"
        else:
            api_status["whatsapp"] = "missing"
            if config.environment == Environment.PRODUCTION:
                issues.append("WhatsApp token missing in production")
        
        status = "healthy" if not issues else "degraded"
        
        return {
            "status": status,
            "environment": config.environment,
            "config_summary": summary,
            "database_status": db_status,
            "api_status": api_status,
            "issues": issues,
            "timestamp": "2025-08-10T00:00:00Z"
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-08-10T00:00:00Z"
        }
