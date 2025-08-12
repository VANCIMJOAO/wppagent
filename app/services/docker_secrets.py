from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Docker Secrets Integration para WhatsApp Agent
Suporte nativo a Docker Swarm Secrets
"""
import os
import logging
from typing import Dict, Optional, Any
from pathlib import Path
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DockerSecretsConfig:
    """Configuração do Docker Secrets"""
    secrets_path: str = "/run/secrets"
    prefix: str = "whatsapp_agent_"
    fallback_to_env: bool = True


class DockerSecretsManager:
    """Gerenciador de secrets usando Docker Secrets"""
    
    def __init__(self, config: DockerSecretsConfig = None):
        self.config = config or DockerSecretsConfig()
        self.secrets_cache: Dict[str, str] = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Inicializar Docker Secrets Manager"""
        try:
            secrets_dir = Path(self.config.secrets_path)
            
            if secrets_dir.exists() and secrets_dir.is_dir():
                logger.info(f"✅ Docker Secrets disponível em: {self.config.secrets_path}")
                await self._load_all_secrets()
                self._initialized = True
                return True
            else:
                logger.warning(f"⚠️ Docker Secrets não disponível em: {self.config.secrets_path}")
                if self.config.fallback_to_env:
                    logger.info("🔄 Usando fallback para variáveis de ambiente")
                    self._initialized = True
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Docker Secrets: {e}")
            return False
    
    async def _load_all_secrets(self):
        """Carregar todos os secrets disponíveis"""
        try:
            secrets_dir = Path(self.config.secrets_path)
            
            for secret_file in secrets_dir.iterdir():
                if secret_file.is_file():
                    secret_name = secret_file.name
                    
                    # Filtrar apenas secrets do WhatsApp Agent
                    if secret_name.startswith(self.config.prefix):
                        try:
                            secret_value = secret_file.read_text().strip()
                            self.secrets_cache[secret_name] = secret_value
                            logger.debug(f"🔑 Secret carregado: {secret_name}")
                        except Exception as e:
                            logger.error(f"❌ Erro ao ler secret {secret_name}: {e}")
            
            logger.info(f"✅ {len(self.secrets_cache)} secrets carregados do Docker")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar secrets: {e}")
    
    def get_secret(self, key: str) -> Optional[str]:
        """Buscar secret por chave"""
        if not self._initialized:
            logger.error("❌ Docker Secrets Manager não inicializado")
            return None
        
        # Tentar buscar com prefixo
        prefixed_key = f"{self.config.prefix}{key}"
        
        # 1. Buscar no cache de Docker Secrets
        if prefixed_key in self.secrets_cache:
            logger.debug(f"✅ Secret encontrado no Docker: {key}")
            return self.secrets_cache[prefixed_key]
        
        # 2. Tentar buscar arquivo individual
        secret_file = Path(self.config.secrets_path) / prefixed_key
        if secret_file.exists():
            try:
                value = secret_file.read_text().strip()
                self.secrets_cache[prefixed_key] = value
                logger.debug(f"✅ Secret carregado do arquivo: {key}")
                return value
            except Exception as e:
                logger.error(f"❌ Erro ao ler secret file {prefixed_key}: {e}")
        
        # 3. Fallback para variável de ambiente
        if self.config.fallback_to_env:
            env_value = os.getenv(key.upper())
            if env_value:
                logger.debug(f"✅ Secret encontrado no ENV: {key}")
                return env_value
        
        logger.warning(f"⚠️ Secret não encontrado: {key}")
        return None
    
    def get_json_secret(self, key: str) -> Optional[Dict[str, Any]]:
        """Buscar secret no formato JSON"""
        secret_value = self.get_secret(key)
        if secret_value:
            try:
                return json.loads(secret_value)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Erro ao parsear JSON secret {key}: {e}")
        return None
    
    def get_database_credentials(self) -> Optional[Dict[str, str]]:
        """Buscar credenciais do banco de dados"""
        # Tentar buscar como JSON primeiro
        db_creds = self.get_json_secret("database_credentials")
        if db_creds:
            return db_creds
        
        # Buscar individualmente
        return {
            "host": self.get_secret("db_host") or "localhost",
            "port": self.get_secret("db_port") or "5432",
            "name": self.get_secret("db_name") or "whats_agent",
            "user": self.get_secret("db_user"),
            "password": self.get_secret("db_password")
        }
    
    def get_api_keys(self) -> Optional[Dict[str, str]]:
        """Buscar chaves de API"""
        # Tentar buscar como JSON primeiro
        api_keys = self.get_json_secret("api_keys")
        if api_keys:
            return api_keys
        
        # Buscar individualmente
        return {
            "openai": self.get_secret("openai_api_key"),
            "meta_access_token": self.get_secret("meta_access_token"),
            "webhook_verify_token": self.get_secret("webhook_verify_token")
        }
    
    def get_whatsapp_config(self) -> Optional[Dict[str, str]]:
        """Buscar configurações do WhatsApp"""
        whatsapp_config = self.get_json_secret("whatsapp_config")
        if whatsapp_config:
            return whatsapp_config
        
        return {
            "phone_number_id": self.get_secret("phone_number_id"),
            "webhook_secret": self.get_secret("whatsapp_webhook_secret"),
            "access_token": self.get_secret("whatsapp_access_token")
        }
    
    def list_available_secrets(self) -> list:
        """Listar secrets disponíveis (sem mostrar valores)"""
        secrets = list(self.secrets_cache.keys())
        
        # Adicionar secrets de arquivo que não estão no cache
        secrets_dir = Path(self.config.secrets_path)
        if secrets_dir.exists():
            for secret_file in secrets_dir.iterdir():
                if (secret_file.is_file() and 
                    secret_file.name.startswith(self.config.prefix) and
                    secret_file.name not in secrets):
                    secrets.append(secret_file.name)
        
        return sorted(secrets)
    
    def get_secret_info(self) -> Dict[str, Any]:
        """Informações sobre o estado dos secrets"""
        return {
            "initialized": self._initialized,
            "secrets_path": self.config.secrets_path,
            "secrets_available": len(self.secrets_cache),
            "fallback_enabled": self.config.fallback_to_env,
            "docker_secrets_available": Path(self.config.secrets_path).exists()
        }


# Instância global
docker_secrets_manager = DockerSecretsManager()
