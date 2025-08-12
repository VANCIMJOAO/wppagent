"""
Sistema de Configuração Robusto por Ambiente
WhatsApp Agent - Configuração Segura e Escalável
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from pydantic.types import SecretStr
import os
import secrets
import logging


class Environment(str, Enum):
    """Ambientes suportados"""
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Formatos de log"""
    JSON = "json"
    PLAIN = "plain"


class BaseConfig(BaseSettings):
    """Configuração base para todos os ambientes"""
    
    # ==============================
    # CONFIGURAÇÃO DE AMBIENTE
    # ==============================
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        env="ENVIRONMENT",
        description="Ambiente de execução"
    )
    
    debug: bool = Field(
        default=True,
        env="DEBUG",
        description="Modo debug"
    )
    
    # ==============================
    # APLICAÇÃO
    # ==============================
    app_name: str = Field(
        default="WhatsApp Agent",
        env="APP_NAME"
    )
    
    app_version: str = Field(
        default="1.0.0",
        env="APP_VERSION"
    )
    
    host: str = Field(
        default="0.0.0.0",
        env="HOST"
    )
    
    port: int = Field(
        default=8000,
        env="PORT",
        ge=1024,
        le=65535
    )
    
    reload: bool = Field(
        default=True,
        env="RELOAD"
    )
    
    workers: int = Field(
        default=1,
        env="WORKERS",
        ge=1,
        le=16
    )
    
    # ==============================
    # SEGURANÇA
    # ==============================
    secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32)),
        env="SECRET_KEY",
        description="Chave secreta para JWT e criptografia"
    )
    
    algorithm: str = Field(
        default="HS256",
        env="ALGORITHM"
    )
    
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        ge=1,
        le=1440
    )
    
    webhook_secret: Optional[SecretStr] = Field(
        default=None,
        env="WEBHOOK_SECRET",
        description="Segredo para validação de webhooks"
    )
    
    admin_username: str = Field(
        default="admin",
        env="ADMIN_USERNAME",
        description="Nome de usuário do administrador"
    )
    
    admin_password: Optional[SecretStr] = Field(
        default=None,
        env="ADMIN_PASSWORD",
        description="Senha do administrador"
    )
    
    security_level: str = Field(
        default="medium",
        env="SECURITY_LEVEL",
        description="Nível de segurança do sistema"
    )
    
    # ==============================
    # WHATSAPP
    # ==============================
    whatsapp_api_url: str = Field(
        default="https://graph.facebook.com/v18.0",
        env="WHATSAPP_API_URL"
    )
    
    whatsapp_token: Optional[SecretStr] = Field(
        default=None,
        env="WHATSAPP_TOKEN",
        description="Token de acesso do WhatsApp"
    )
    
    whatsapp_phone_id: Optional[str] = Field(
        default=None,
        env="WHATSAPP_PHONE_ID"
    )
    
    whatsapp_verify_token: Optional[SecretStr] = Field(
        default=None,
        env="WHATSAPP_VERIFY_TOKEN"
    )
    
    meta_access_token: Optional[SecretStr] = Field(
        default=None,
        env="META_ACCESS_TOKEN",
        description="Token de acesso da Meta API"
    )
    
    meta_api_version: str = Field(
        default="v18.0",
        env="META_API_VERSION",
        description="Versão da Meta API"
    )
    
    whatsapp_webhook_secret: Optional[SecretStr] = Field(
        default=None,
        env="WHATSAPP_WEBHOOK_SECRET",
        description="Secret para validação do webhook"
    )
    
    webhook_verify_token: Optional[SecretStr] = Field(
        default=None,
        env="WEBHOOK_VERIFY_TOKEN",
        description="Token para verificação do webhook"
    )
    
    webhook_url: str = Field(
        default="http://localhost:8000/webhook",
        env="WEBHOOK_URL",
        description="URL do webhook para o WhatsApp"
    )
    
    # ==============================
    # BANCO DE DADOS
    # ==============================
    database_url: str = Field(
        default="sqlite:///./whatsapp_agent.db",
        env="DATABASE_URL",
        description="URL de conexão com o banco de dados"
    )
    
    database_dsn: Optional[str] = Field(
        default=None,
        env="DATABASE_DSN",
        description="DSN do banco de dados"
    )
    
    db_host: str = Field(
        default="localhost",
        env="DB_HOST",
        description="Host do banco de dados"
    )
    
    db_port: int = Field(
        default=5432,
        env="DB_PORT",
        description="Porta do banco de dados"
    )
    
    db_name: str = Field(
        default="whatsapp_agent",
        env="DB_NAME",
        description="Nome do banco de dados"
    )
    
    db_user: str = Field(
        default="whatsapp",
        env="DB_USER",
        description="Usuário do banco de dados"
    )
    
    db_password: SecretStr = Field(
        default=SecretStr(""),
        env="DB_PASSWORD",
        description="Senha do banco de dados"
    )
    
    database_echo: bool = Field(
        default=False,
        env="DATABASE_ECHO"
    )
    
    database_pool_size: int = Field(
        default=5,
        env="DATABASE_POOL_SIZE",
        ge=1,
        le=20
    )
    
    database_max_overflow: int = Field(
        default=10,
        env="DATABASE_MAX_OVERFLOW",
        ge=0,
        le=50
    )
    
    # ==============================
    # REDIS/CACHE
    # ==============================
    redis_enabled: bool = Field(
        default=True,
        env="REDIS_ENABLED",
        description="Habilitar Redis"
    )
    
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    cache_ttl: int = Field(
        default=300,
        env="CACHE_TTL",
        ge=60,
        le=3600,
        description="TTL do cache em segundos"
    )
    
    # ==============================
    # RATE LIMITING
    # ==============================
    rate_limit_enabled: bool = Field(
        default=True,
        env="RATE_LIMIT_ENABLED"
    )
    
    rate_limit_requests: int = Field(
        default=100,
        env="RATE_LIMIT_REQUESTS",
        ge=1,
        le=10000
    )
    
    rate_limit_window: int = Field(
        default=60,
        env="RATE_LIMIT_WINDOW",
        ge=1,
        le=3600,
        description="Janela de rate limit em segundos"
    )
    
    # ==============================
    # LOGGING
    # ==============================
    log_dir: str = Field(
        default="logs",
        env="LOG_DIR",
        description="Diretório dos logs"
    )
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        env="LOG_LEVEL"
    )
    
    log_format: LogFormat = Field(
        default=LogFormat.PLAIN,
        env="LOG_FORMAT"
    )
    
    log_third_party_level: LogLevel = Field(
        default=LogLevel.WARNING,
        env="LOG_THIRD_PARTY_LEVEL",
        description="Nível de log para bibliotecas third party"
    )
    
    log_file: Optional[str] = Field(
        default=None,
        env="LOG_FILE"
    )
    
    log_max_size_mb: int = Field(
        default=50,
        env="LOG_MAX_SIZE_MB",
        ge=1,
        le=1000
    )
    
    log_rotation_size: str = Field(
        default="50MB",
        env="LOG_ROTATION_SIZE",
        description="Tamanho máximo do arquivo de log antes da rotação"
    )
    
    log_backup_count: int = Field(
        default=5,
        env="LOG_BACKUP_COUNT",
        ge=1,
        le=50
    )
    
    log_request_id: bool = Field(
        default=True,
        env="LOG_REQUEST_ID",
        description="Incluir request ID nos logs"
    )
    
    log_user_context: bool = Field(
        default=True,
        env="LOG_USER_CONTEXT",
        description="Incluir contexto do usuário nos logs"
    )
    
    # ==============================
    # MONITORING & METRICS
    # ==============================
    health_check_enabled: bool = Field(
        default=True,
        env="HEALTH_CHECK_ENABLED",
        description="Habilitar health checks"
    )
    
    metrics_enabled: bool = Field(
        default=False,
        env="METRICS_ENABLED",
        description="Habilitar coleta de métricas"
    )
    
    prometheus_enabled: bool = Field(
        default=False,
        env="PROMETHEUS_ENABLED",
        description="Habilitar métricas Prometheus"
    )
    
    prometheus_port: int = Field(
        default=9090,
        env="PROMETHEUS_PORT",
        ge=1024,
        le=65535
    )
    
    grafana_enabled: bool = Field(
        default=False,
        env="GRAFANA_ENABLED",
        description="Habilitar dashboards Grafana"
    )
    
    # ==============================
    # SLA MONITORING
    # ==============================
    sla_response_time_ms: float = Field(
        default=2000.0,
        env="SLA_RESPONSE_TIME_MS",
        ge=100.0,
        le=30000.0,
        description="SLA de tempo de resposta em ms"
    )
    
    sla_uptime_percentage: float = Field(
        default=99.5,
        env="SLA_UPTIME_PERCENTAGE",
        ge=90.0,
        le=100.0,
        description="SLA de uptime em porcentagem"
    )
    
    sla_error_rate_percentage: float = Field(
        default=1.0,
        env="SLA_ERROR_RATE_PERCENTAGE",
        ge=0.1,
        le=10.0,
        description="SLA de taxa de erro em porcentagem"
    )
    
    health_check_interval_seconds: int = Field(
        default=30,
        env="HEALTH_CHECK_INTERVAL_SECONDS",
        ge=5,
        le=300,
        description="Intervalo de health check em segundos"
    )
    
    metrics_retention_days: int = Field(
        default=30,
        env="METRICS_RETENTION_DAYS",
        ge=1,
        le=365,
        description="Retenção de métricas em dias"
    )
    
    # ==============================
    # ALERTING SYSTEM
    # ==============================
    alerting_enabled: bool = Field(
        default=False,
        env="ALERTING_ENABLED",
        description="Habilitar sistema de alertas"
    )
    
    alert_email: Optional[str] = Field(
        default=None,
        env="ALERT_EMAIL",
        description="Email para receber alertas"
    )
    
    alert_slack_webhook: Optional[str] = Field(
        default=None,
        env="ALERT_SLACK_WEBHOOK",
        description="Webhook do Slack para alertas"
    )
    
    alert_response_time_threshold_ms: float = Field(
        default=3000.0,
        env="ALERT_RESPONSE_TIME_THRESHOLD_MS",
        ge=500.0,
        le=30000.0,
        description="Threshold de tempo de resposta para alertas"
    )
    
    alert_error_rate_threshold: float = Field(
        default=5.0,
        env="ALERT_ERROR_RATE_THRESHOLD",
        ge=0.1,
        le=50.0,
        description="Threshold de taxa de erro para alertas"
    )
    
    alert_cooldown_minutes: int = Field(
        default=30,
        env="ALERT_COOLDOWN_MINUTES",
        ge=1,
        le=1440,
        description="Cooldown entre alertas do mesmo tipo"
    )
    
    # ==============================
    # BUSINESS METRICS
    # ==============================
    business_metrics_enabled: bool = Field(
        default=True,
        env="BUSINESS_METRICS_ENABLED",
        description="Habilitar métricas de negócio"
    )
    
    conversion_tracking_enabled: bool = Field(
        default=True,
        env="CONVERSION_TRACKING_ENABLED",
        description="Rastrear conversões"
    )
    
    customer_satisfaction_tracking: bool = Field(
        default=True,
        env="CUSTOMER_SATISFACTION_TRACKING",
        description="Rastrear satisfação do cliente"
    )
    
    # ==============================
    # LLM/AI
    # ==============================
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        env="OPENAI_API_KEY"
    )
    
    openai_model: str = Field(
        default="gpt-3.5-turbo",
        env="OPENAI_MODEL"
    )
    
    max_tokens: int = Field(
        default=150,
        env="MAX_TOKENS",
        ge=50,
        le=4000
    )
    
    temperature: float = Field(
        default=0.7,
        env="TEMPERATURE",
        ge=0.0,
        le=2.0
    )
    
    # ==============================
    # CORS
    # ==============================
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    
    cors_credentials: bool = Field(
        default=True,
        env="CORS_CREDENTIALS"
    )
    
    cors_methods: List[str] = Field(
        default=["*"],
        env="CORS_METHODS"
    )
    
    cors_headers: List[str] = Field(
        default=["*"],
        env="CORS_HEADERS"
    )
    
    # ==============================
    # TIMEOUTS
    # ==============================
    request_timeout: int = Field(
        default=30,
        env="REQUEST_TIMEOUT",
        ge=5,
        le=300
    )
    
    llm_timeout: int = Field(
        default=30,
        env="LLM_TIMEOUT",
        ge=5,
        le=120
    )
    
    webhook_timeout: int = Field(
        default=10,
        env="WEBHOOK_TIMEOUT",
        ge=1,
        le=60
    )
    
    # ==============================
    # BACKUP & RECOVERY
    # ==============================
    backup_enabled: bool = Field(
        default=False,
        env="BACKUP_ENABLED"
    )
    
    backup_interval_hours: int = Field(
        default=24,
        env="BACKUP_INTERVAL_HOURS",
        ge=1,
        le=168
    )
    
    backup_retention_days: int = Field(
        default=30,
        env="BACKUP_RETENTION_DAYS",
        ge=1,
        le=365
    )
    
    # ==============================
    # FEATURE FLAGS
    # ==============================
    feature_conversation_memory: bool = Field(
        default=True,
        env="FEATURE_CONVERSATION_MEMORY"
    )
    
    feature_sentiment_analysis: bool = Field(
        default=True,
        env="FEATURE_SENTIMENT_ANALYSIS"
    )
    
    feature_auto_responses: bool = Field(
        default=True,
        env="FEATURE_AUTO_RESPONSES"
    )
    
    feature_booking_integration: bool = Field(
        default=True,
        env="FEATURE_BOOKING_INTEGRATION"
    )
    
    # ==============================
    # VALIDAÇÕES
    # ==============================
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        if isinstance(v, str):
            try:
                return Environment(v.lower())
            except ValueError:
                raise ValueError(f"Invalid environment: {v}")
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        if isinstance(v, str):
            try:
                return LogLevel(v.upper())
            except ValueError:
                raise ValueError(f"Invalid log level: {v}")
        return v
    
    @field_validator('log_format')
    @classmethod
    def validate_log_format(cls, v):
        if isinstance(v, str):
            try:
                return LogFormat(v.lower())
            except ValueError:
                raise ValueError(f"Invalid log format: {v}")
        return v
    
    @field_validator('alert_email')
    @classmethod
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('cors_origins')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('cors_methods')
    @classmethod
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip().upper() for method in v.split(',')]
        return v
    
    @field_validator('cors_headers')
    @classmethod
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(',')]
        return v
    
    @model_validator(mode='after')
    def validate_config_consistency(self):
        """Validar consistência da configuração"""
        
        # Validações de produção
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                self.debug = False
                
            if self.log_level == LogLevel.DEBUG:
                self.log_level = LogLevel.INFO
                
            if not self.secret_key or self.secret_key.get_secret_value() == 'your-secret-key':
                raise ValueError("Secret key must be set for production")
        
        # Validações de SLA
        if self.alert_response_time_threshold_ms < self.sla_response_time_ms:
            raise ValueError("Alert threshold must be >= SLA response time")
        
        # Validações de alerting (apenas se alerting estiver habilitado)
        if self.alerting_enabled and not (self.alert_email or self.alert_slack_webhook):
            # Em desenvolvimento/teste, desabilitar alerting automaticamente
            if self.environment in [Environment.DEVELOPMENT, Environment.TEST]:
                self.alerting_enabled = False
            else:
                raise ValueError("At least one alert channel must be configured when alerting is enabled")
            raise ValueError("At least one alert channel must be configured")
        
        return self
    
    # ==============================
    # MÉTODOS DE CONVENIÊNCIA
    # ==============================
    @property
    def is_development(self) -> bool:
        """Verifica se está em ambiente de desenvolvimento"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em ambiente de produção"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_test(self) -> bool:
        """Verifica se está em ambiente de teste"""
        return self.environment == Environment.TEST
    
    @property
    def is_staging(self) -> bool:
        """Verifica se está em ambiente de staging"""
        return self.environment == Environment.STAGING
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "ignore"


class DevelopmentConfig(BaseConfig):
    """Configuração para ambiente de desenvolvimento"""
    
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: LogLevel = LogLevel.DEBUG
    log_format: LogFormat = LogFormat.PLAIN
    database_echo: bool = True
    reload: bool = True
    
    # Webhook token explícito para desenvolvimento
    webhook_verify_token: Optional[SecretStr] = Field(
        default=SecretStr("dev-webhook-token"),
        env="WEBHOOK_VERIFY_TOKEN",
        description="Token para verificação do webhook"
    )
    
    # Métricas habilitadas em dev
    metrics_enabled: bool = True
    business_metrics_enabled: bool = True
    
    # SLA relaxado para desenvolvimento
    sla_response_time_ms: float = 5000.0
    sla_error_rate_percentage: float = 5.0
    
    # Alert threshold deve ser >= SLA
    alert_response_time_threshold_ms: float = 6000.0
    alert_error_rate_threshold: float = 10.0
    
    # Rate limiting desabilitado em desenvolvimento
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 1000
    
    # CORS aberto para desenvolvimento
    cors_origins: List[str] = ["*"]


class TestConfig(BaseConfig):
    """Configuração para ambiente de testes"""
    
    environment: Environment = Environment.TEST
    debug: bool = False
    log_level: LogLevel = LogLevel.WARNING
    log_format: LogFormat = LogFormat.JSON
    database_url: str = "sqlite:///:memory:"
    
    # Webhook token explícito para testes
    webhook_verify_token: Optional[SecretStr] = Field(
        default=SecretStr("test-webhook-token"),
        env="WEBHOOK_VERIFY_TOKEN",
        description="Token para verificação do webhook"
    )
    
    # Desabilitar features externas em testes
    metrics_enabled: bool = False
    alerting_enabled: bool = False
    backup_enabled: bool = False
    rate_limit_enabled: bool = False
    
    # Timeouts reduzidos para testes
    request_timeout: int = 5
    llm_timeout: int = 5
    webhook_timeout: int = 2


class StagingConfig(BaseConfig):
    """Configuração para ambiente de staging"""
    
    environment: Environment = Environment.STAGING
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.JSON
    
    # Webhook token explícito para staging
    webhook_verify_token: Optional[SecretStr] = Field(
        default=SecretStr("staging-webhook-token"),
        env="WEBHOOK_VERIFY_TOKEN",
        description="Token para verificação do webhook"
    )
    
    # Métricas habilitadas
    metrics_enabled: bool = True
    business_metrics_enabled: bool = True
    prometheus_enabled: bool = True
    
    # SLA similar à produção
    sla_response_time_ms: float = 2500.0
    sla_uptime_percentage: float = 99.0
    sla_error_rate_percentage: float = 2.0
    
    # Alerting desabilitado até que canais sejam configurados
    alerting_enabled: bool = False
    alert_response_time_threshold_ms: float = 4000.0
    alert_error_rate_threshold: float = 10.0


class ProductionConfig(BaseConfig):
    """Configuração para ambiente de produção"""
    
    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.JSON
    reload: bool = False
    
    # Webhook token obrigatório para produção
    webhook_verify_token: Optional[SecretStr] = Field(
        default=None,
        env="WEBHOOK_VERIFY_TOKEN",
        description="Token para verificação do webhook (obrigatório em produção)"
    )
    workers: int = 4
    
    # Logging otimizado para produção
    log_max_size_mb: int = 100
    log_backup_count: int = 20
    
    # Métricas completas
    metrics_enabled: bool = True
    business_metrics_enabled: bool = True
    prometheus_enabled: bool = True
    grafana_enabled: bool = True
    
    # SLA rigoroso
    sla_response_time_ms: float = 2000.0
    sla_uptime_percentage: float = 99.5
    sla_error_rate_percentage: float = 1.0
    
    # Alerting desabilitado até que canais sejam configurados
    alerting_enabled: bool = False
    alert_response_time_threshold_ms: float = 3000.0
    alert_error_rate_threshold: float = 5.0
    alert_cooldown_minutes: int = 15
    
    # Rate limiting rigoroso
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Backup habilitado
    backup_enabled: bool = True
    backup_interval_hours: int = 6
    
    # CORS restritivo
    cors_origins: List[str] = Field(default_factory=list)
    
    # Health check mais frequente
    health_check_interval_seconds: int = 15


# Mapeamento de configurações por ambiente
CONFIG_MAPPING = {
    Environment.DEVELOPMENT: DevelopmentConfig,
    Environment.TEST: TestConfig,
    Environment.STAGING: StagingConfig,
    Environment.PRODUCTION: ProductionConfig
}


def get_config_class(environment: str = None) -> type[BaseConfig]:
    """Obter classe de configuração baseada no ambiente"""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    try:
        env_enum = Environment(environment.lower())
        return CONFIG_MAPPING[env_enum]
    except (ValueError, KeyError):
        return DevelopmentConfig
