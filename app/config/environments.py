"""
Configurações Específicas por Ambiente
WhatsApp Agent - Configuração de Desenvolvimento
"""
from pydantic.types import SecretStr
from .environment_config import BaseConfig, Environment, LogLevel, LogFormat


class DevelopmentConfig(BaseConfig):
    """Configuração para ambiente de desenvolvimento"""
    
    # Ambiente
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    
    # Logging mais verboso para desenvolvimento
    log_level: LogLevel = LogLevel.DEBUG
    log_format: LogFormat = LogFormat.PLAIN
    log_performance: bool = True
    log_business: bool = True
    log_third_party_level: str = "INFO"
    
    # Database local
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "whats_agent_dev"
    db_user: str = "postgres"
    
    # Redis local
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Admin com senha simples para dev
    admin_username: str = "admin"
    admin_email: str = "admin@localhost"
    
    # Rate limiting relaxado
    rate_limit_requests_per_minute: int = 1000
    rate_limit_burst_size: int = 50
    
    # Workers reduzido para dev
    workers: int = 1
    
    # Monitoring opcional
    metrics_enabled: bool = False
    prometheus_enabled: bool = False
    
    # Health check mais frequente
    health_check_interval: int = 10
    
    class Config:
        env_file = ".env.development"


class TestingConfig(BaseConfig):
    """Configuração para testes"""
    
    # Ambiente
    environment: Environment = Environment.TEST
    debug: bool = False
    
    # Logging para testes - menor verbosidade
    log_level: LogLevel = LogLevel.WARNING
    log_format: LogFormat = LogFormat.JSON
    log_performance: bool = False
    log_business: bool = False
    log_third_party_level: str = "ERROR"
    
    # Database de teste
    db_name: str = "whats_agent_test"
    
    # Redis separado para testes
    redis_db: int = 1
    
    # Admin para testes
    admin_username: str = "test_admin"
    admin_email: str = "test@localhost"
    
    # Rate limiting para testes
    rate_limit_requests_per_minute: int = 100
    
    # Sem workers para testes
    workers: int = 1
    
    # Monitoring desabilitado
    metrics_enabled: bool = False
    prometheus_enabled: bool = False
    health_check_enabled: bool = False
    
    class Config:
        env_file = ".env.testing"


class StagingConfig(BaseConfig):
    """Configuração para staging/homologação"""
    
    # Ambiente
    environment: Environment = Environment.STAGING
    debug: bool = False
    
    # Logging estruturado para staging
    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.JSON
    log_performance: bool = True
    log_business: bool = True
    log_third_party_level: str = "WARNING"
    log_backup_count: int = 5
    
    # Database staging
    db_name: str = "whats_agent_staging"
    
    # Redis com senha
    redis_db: int = 0
    
    # Admin seguro
    admin_username: str = "staging_admin"
    admin_password: SecretStr = SecretStr("staging_secure_password_123!")
    admin_email: str = "admin@staging.whatsagent.com"
    
    # Rate limiting moderado
    rate_limit_requests_per_minute: int = 120
    rate_limit_burst_size: int = 15
    
    # Workers moderado
    workers: int = 2
    
    # Monitoring habilitado
    metrics_enabled: bool = True
    prometheus_enabled: bool = True
    
    # Health check padrão
    health_check_interval: int = 30
    
    class Config:
        env_file = ".env.staging"


class ProductionConfig(BaseConfig):
    """Configuração para produção"""
    
    # Ambiente
    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    
    # Logging otimizado para produção
    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.JSON
    log_performance: bool = False  # Desabilita performance logs em produção
    log_business: bool = True
    log_third_party_level: str = "ERROR"  # Minimiza logs externos
    log_backup_count: int = 20  # Mais backups em produção
    log_rotation_size: str = "100MB"  # Arquivos maiores
    
    # Workers otimizado
    workers: int = 4
    
    # Rate limiting rigoroso
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10
    
    # Monitoring completo
    metrics_enabled: bool = True
    prometheus_enabled: bool = True
    health_check_enabled: bool = True
    health_check_interval: int = 30
    
    # Admin seguro
    admin_username: str = "admin"
    admin_email: str = "admin@whatsagent.com"
    
    class Config:
        env_file = ".env.production"
