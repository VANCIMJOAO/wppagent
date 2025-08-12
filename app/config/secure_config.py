"""
Configuração avançada de secrets para WhatsApp Agent
Integração com FastAPI e startup da aplicação
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from typing import Dict, Any, Optional

from app.services.secrets_manager import secrets_manager, SecretsConfig, SecretProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger = logging.getLogger(__name__)


class SecretsConfigManager:
    """Gerenciador de configuração usando secrets seguros"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self._loaded = False
    
    async def load_configuration(self) -> bool:
        """Carregar configuração completa da aplicação"""
        try:
            logger.info("🔧 Carregando configuração da aplicação...")
            
            # Configurar secrets manager baseado no ambiente
            env = os.getenv('ENVIRONMENT', 'development')
            secrets_config = self._get_secrets_config(env)
            
            # Inicializar secrets manager
            global secrets_manager
            secrets_manager.config = secrets_config
            
            if not await secrets_manager.initialize():
                logger.error("❌ Falha ao inicializar Secrets Manager")
                return False
            
            # Carregar configurações específicas
            await self._load_database_config()
            await self._load_api_config()
            await self._load_app_config()
            await self._load_security_config()
            
            self._loaded = True
            logger.info("✅ Configuração carregada com sucesso")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configuração: {e}")
            return False
    
    def _get_secrets_config(self, environment: str) -> SecretsConfig:
        """Configuração de secrets baseada no ambiente"""
        if environment == "production":
            return SecretsConfig(
                provider_priority=[
                    SecretProvider.VAULT,
                    SecretProvider.DOCKER,
                    SecretProvider.ENVIRONMENT
                ],
                vault_enabled=True,
                docker_enabled=True,
                env_fallback=True,
                cache_enabled=True,
                cache_ttl=300
            )
        
        elif environment == "staging":
            return SecretsConfig(
                provider_priority=[
                    SecretProvider.DOCKER,
                    SecretProvider.VAULT,
                    SecretProvider.ENVIRONMENT
                ],
                vault_enabled=False,  # Vault opcional em staging
                docker_enabled=True,
                env_fallback=True,
                cache_enabled=True,
                cache_ttl=600
            )
        
        else:  # development
            return SecretsConfig(
                provider_priority=[
                    SecretProvider.ENVIRONMENT,
                    SecretProvider.DOCKER
                ],
                vault_enabled=False,
                docker_enabled=False,  # Opcional em dev
                env_fallback=True,
                cache_enabled=False  # Sem cache em dev
            )
    
    async def _load_database_config(self):
        """Carregar configuração do banco de dados"""
        db_config = await secrets_manager.get_database_config()
        
        # Construir URL de conexão
        if all(key in db_config for key in ['host', 'port', 'name', 'user', 'password']):
            db_url = (
                f"postgresql://{db_config['user']}:{db_config['password']}"
                f"@{db_config['host']}:{db_config['port']}/{db_config['name']}"
            )
            self.config['database_url'] = db_url
            self.config['database'] = db_config
            logger.info("✅ Configuração de banco carregada")
        else:
            logger.error("❌ Configuração de banco incompleta")
            # Fallback para ambiente local
            self.config['database_url'] = os.getenv(
                'DATABASE_URL', 
                'postgresql://user:password@localhost:5432/whats_agent'
            )
    
    async def _load_api_config(self):
        """Carregar configuração de APIs"""
        api_config = await secrets_manager.get_api_config()
        
        # APIs obrigatórias
        required_apis = ['openai_api_key', 'meta_access_token']
        missing_apis = [api for api in required_apis if api not in api_config]
        
        if missing_apis:
            logger.warning(f"⚠️ APIs faltando: {missing_apis}")
        
        self.config['apis'] = api_config
        
        # Configurações específicas
        self.config['openai_api_key'] = api_config.get('openai_api_key')
        self.config['meta_access_token'] = api_config.get('meta_access_token')
        self.config['webhook_verify_token'] = api_config.get('webhook_verify_token')
        
        logger.info(f"✅ {len(api_config)} APIs configuradas")
    
    async def _load_app_config(self):
        """Carregar configuração geral da aplicação"""
        # Configurações da aplicação
        self.config['app'] = {
            'name': await secrets_manager.get_secret('app_name', 'WhatsApp Agent'),
            'version': await secrets_manager.get_secret('app_version', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'host': await secrets_manager.get_secret('app_host', '0.0.0.0'),
            'port': int(await secrets_manager.get_secret('app_port', '8000')),
        }
        
        # Logs
        self.config['logging'] = {
            'level': await secrets_manager.get_secret('log_level', 'INFO'),
            'format': await secrets_manager.get_secret('log_format', 'json'),
            'file_path': await secrets_manager.get_secret('log_file', '/app/logs/app.log')
        }
        
        logger.info("✅ Configuração da aplicação carregada")
    
    async def _load_security_config(self):
        """Carregar configuração de segurança"""
        self.config['security'] = {
            'secret_key': await secrets_manager.get_secret('secret_key'),
            'jwt_secret': await secrets_manager.get_secret('jwt_secret'),
            'encryption_key': await secrets_manager.get_secret('encryption_key'),
            'rate_limit': {
                'requests_per_minute': int(await secrets_manager.get_secret('rate_limit_rpm', '60')),
                'burst_size': int(await secrets_manager.get_secret('rate_limit_burst', '10'))
            }
        }
        
        # Gerar secrets se não existirem
        if not self.config['security']['secret_key']:
            import secrets
            secret_key = secrets.token_urlsafe(32)
            self.config['security']['secret_key'] = secret_key
            logger.warning("⚠️ Secret key gerada automaticamente")
        
        logger.info("✅ Configuração de segurança carregada")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Buscar valor na configuração"""
        return self.config.get(key, default)
    
    def get_nested(self, path: str, default: Any = None) -> Any:
        """Buscar valor aninhado usando path (ex: 'database.host')"""
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def is_loaded(self) -> bool:
        """Verificar se configuração foi carregada"""
        return self._loaded
    
    def get_status(self) -> Dict[str, Any]:
        """Status da configuração"""
        return {
            'loaded': self._loaded,
            'sections': list(self.config.keys()),
            'secrets_manager': secrets_manager.get_provider_status()
        }
    
    async def reload(self) -> bool:
        """Recarregar configuração"""
        logger.info("🔄 Recarregando configuração...")
        self.config.clear()
        self._loaded = False
        return await self.load_configuration()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check da configuração"""
        health = {
            'status': 'healthy',
            'configuration': {
                'loaded': self._loaded,
                'sections': len(self.config)
            },
            'issues': []
        }
        
        # Verificar secrets manager
        secrets_health = await secrets_manager.health_check()
        health['secrets_manager'] = secrets_health
        
        if secrets_health['status'] != 'healthy':
            health['status'] = 'degraded'
            health['issues'].extend(secrets_health['issues'])
        
        # Verificar configurações críticas
        critical_configs = ['database_url', 'openai_api_key']
        missing_configs = [config for config in critical_configs if not self.get(config)]
        
        if missing_configs:
            health['status'] = 'unhealthy'
            health['issues'].extend([f"Configuração crítica faltando: {config}" for config in missing_configs])
        
        return health


# Instância global
config_manager = SecretsConfigManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle da aplicação FastAPI com secrets management"""
    # Startup
    logger.info("🚀 Iniciando WhatsApp Agent...")
    
    try:
        # Carregar configuração
        if not await config_manager.load_configuration():
            logger.error("❌ Falha crítica ao carregar configuração")
            raise RuntimeError("Configuração não pôde ser carregada")
        
        # Configurar logging baseado na configuração
        log_level = config_manager.get_nested('logging.level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        # Adicionar configuração ao app
        app.state.config = config_manager
        app.state.secrets = secrets_manager
        
        logger.info("✅ WhatsApp Agent iniciado com sucesso")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Erro crítico no startup: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("⏹️ Encerrando WhatsApp Agent...")
        
        try:
            await secrets_manager.close()
            logger.info("✅ Secrets Manager fechado")
        except Exception as e:
            logger.error(f"❌ Erro no shutdown: {e}")


def create_secure_app() -> FastAPI:
    """Criar aplicação FastAPI com secrets management"""
    app = FastAPI(
        title="WhatsApp Agent",
        description="Bot inteligente com secrets management avançado",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Middleware de saúde para secrets
    @app.middleware("http")
    async def secrets_health_middleware(request, call_next):
        # Verificar se secrets manager está saudável
        if not secrets_manager._initialized:
            logger.error("❌ Secrets Manager não inicializado")
        
        response = await call_next(request)
        return response
    
    # Endpoint de health check
    @app.get("/health/secrets")
    async def secrets_health():
        """Health check do sistema de secrets"""
        return await config_manager.health_check()
    
    @app.get("/health/config")
    async def config_health():
        """Status da configuração"""
        return config_manager.get_status()
    
    return app


# Helper para acessar configuração
def get_config() -> SecretsConfigManager:
    """Acessar gerenciador de configuração"""
    return config_manager
