from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Unified Secrets Manager para WhatsApp Agent
Gerenciamento centralizado e hierárquico de secrets
"""
import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Union

from .docker_secrets import DockerSecretsManager, docker_secrets_manager
from .vault_secrets import VaultSecretsManager, vault_manager

logger = logging.getLogger(__name__)


class SecretProvider(Enum):
    """Provedores de secrets disponíveis"""

    VAULT = "vault"
    DOCKER = "docker"
    ENVIRONMENT = "environment"
    FILE = "file"


@dataclass
class SecretsConfig:
    """Configuração do sistema de secrets"""

    # Ordem de prioridade dos provedores
    provider_priority: list = None

    # Configurações específicas
    vault_enabled: bool = False
    docker_enabled: bool = True
    env_fallback: bool = True

    # Cache
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutos

    def __post_init__(self):
        if self.provider_priority is None:
            self.provider_priority = [
                SecretProvider.VAULT,
                SecretProvider.DOCKER,
                SecretProvider.ENVIRONMENT,
            ]


class UnifiedSecretsManager:
    """Gerenciador unificado de secrets com múltiplos provedores"""

    def __init__(self, config: SecretsConfig = None):
        self.config = config or SecretsConfig()
        self.providers: Dict[SecretProvider, Any] = {}
        self.cache: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self) -> bool:
        """Inicializar todos os provedores de secrets"""
        try:
            logger.info("🔐 Inicializando Unified Secrets Manager...")

            # Inicializar provedores baseado na configuração
            for provider in self.config.provider_priority:
                await self._initialize_provider(provider)

            self._initialized = True

            # Log do status
            active_providers = [p.value for p in self.providers.keys()]
            logger.info(
                f"✅ Secrets Manager inicializado com provedores: {active_providers}"
            )

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Secrets Manager: {e}")
            return False

    async def _initialize_provider(self, provider: SecretProvider):
        """Inicializar provedor específico"""
        try:
            if provider == SecretProvider.VAULT and self.config.vault_enabled:
                if await vault_manager.initialize():
                    self.providers[provider] = vault_manager
                    logger.info("✅ HashiCorp Vault inicializado")

            elif provider == SecretProvider.DOCKER and self.config.docker_enabled:
                if await docker_secrets_manager.initialize():
                    self.providers[provider] = docker_secrets_manager
                    logger.info("✅ Docker Secrets inicializado")

            elif provider == SecretProvider.ENVIRONMENT:
                # Environment sempre disponível
                self.providers[provider] = "env"
                logger.info("✅ Environment Variables disponível")

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar {provider.value}: {e}")

    async def get_secret(self, key: str, default: Any = None) -> Optional[Any]:
        """Buscar secret usando hierarquia de provedores"""
        if not self._initialized:
            logger.error("❌ Secrets Manager não inicializado")
            return default

        # Verificar cache primeiro
        if self.config.cache_enabled and key in self.cache:
            logger.debug(f"✅ Secret encontrado no cache: {key}")
            return self.cache[key]

        # Buscar nos provedores por ordem de prioridade
        for provider in self.config.provider_priority:
            if provider not in self.providers:
                continue

            try:
                value = await self._get_from_provider(provider, key)
                if value is not None:
                    # Cachear resultado
                    if self.config.cache_enabled:
                        self.cache[key] = value

                    logger.debug(f"✅ Secret encontrado em {provider.value}: {key}")
                    return value

            except Exception as e:
                logger.warning(f"⚠️ Erro em {provider.value} para {key}: {e}")
                continue

        logger.warning(f"⚠️ Secret não encontrado: {key}")
        return default

    async def _get_from_provider(
        self, provider: SecretProvider, key: str
    ) -> Optional[Any]:
        """Buscar secret em provedor específico"""
        if provider == SecretProvider.VAULT:
            vault = self.providers[provider]
            # Mapear chaves para paths do Vault
            vault_paths = {
                "database_password": "database/credentials",
                "openai_api_key": "apis/keys",
                "meta_access_token": "whatsapp/config",
            }

            if key in vault_paths:
                secret_data = await vault.get_secret(vault_paths[key])
                if secret_data and key in secret_data:
                    return secret_data[key]

            # Buscar direto por chave
            secret_data = await vault.get_secret(f"general/{key}")
            if secret_data and "value" in secret_data:
                return secret_data["value"]

        elif provider == SecretProvider.DOCKER:
            docker = self.providers[provider]
            return docker.get_secret(key)

        elif provider == SecretProvider.ENVIRONMENT:
            return os.getenv(key.upper()) or os.getenv(key)

        return None

    async def get_database_config(self) -> Dict[str, str]:
        """Buscar configuração completa do banco de dados"""
        config = {}

        # Buscar cada campo necessário
        fields = {
            "host": ["db_host", "database_host"],
            "port": ["db_port", "database_port"],
            "name": ["db_name", "database_name"],
            "user": ["db_user", "database_user"],
            "password": ["db_password", "database_password"],
        }

        for field, possible_keys in fields.items():
            for key in possible_keys:
                value = await self.get_secret(key)
                if value:
                    config[field] = value
                    break

            # Valores padrão
            if field not in config:
                defaults = {"host": "localhost", "port": "5432", "name": "whats_agent"}
                if field in defaults:
                    config[field] = defaults[field]

        return config

    async def get_api_config(self) -> Dict[str, str]:
        """Buscar configuração de APIs"""
        config = {}

        api_keys = [
            "openai_api_key",
            "meta_access_token",
            "webhook_verify_token",
            "whatsapp_webhook_secret",
        ]

        for key in api_keys:
            value = await self.get_secret(key)
            if value:
                config[key] = value

        return config

    async def set_secret(
        self, key: str, value: Any, provider: SecretProvider = None
    ) -> bool:
        """Armazenar secret (apenas em provedores que suportam escrita)"""
        if not self._initialized:
            logger.error("❌ Secrets Manager não inicializado")
            return False

        # Se não especificado, usar o primeiro provedor que suporta escrita
        if provider is None:
            if SecretProvider.VAULT in self.providers:
                provider = SecretProvider.VAULT
            else:
                logger.error("❌ Nenhum provedor suporta escrita de secrets")
                return False

        try:
            if provider == SecretProvider.VAULT:
                vault = self.providers[provider]
                success = await vault.set_secret(f"general/{key}", {"value": value})
                if success and self.config.cache_enabled:
                    self.cache[key] = value
                return success

            else:
                logger.error(f"❌ Provedor {provider.value} não suporta escrita")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao armazenar secret {key}: {e}")
            return False

    async def rotate_secret(self, key: str, new_value: Any) -> bool:
        """Rotacionar secret em todos os provedores possíveis"""
        success = False

        for provider in self.providers:
            if provider == SecretProvider.VAULT:
                vault = self.providers[provider]
                if await vault.rotate_secret(f"general/{key}", {"value": new_value}):
                    success = True
                    logger.info(f"🔄 Secret rotacionado no Vault: {key}")

        if success and self.config.cache_enabled:
            # Limpar do cache para forçar reload
            self.cache.pop(key, None)

        return success

    def clear_cache(self):
        """Limpar cache de secrets"""
        self.cache.clear()
        logger.info("🧹 Cache de secrets limpo")

    def get_provider_status(self) -> Dict[str, Any]:
        """Status dos provedores"""
        status = {
            "initialized": self._initialized,
            "providers": {},
            "cache_size": len(self.cache) if self.config.cache_enabled else 0,
        }

        for provider in SecretProvider:
            if provider in self.providers:
                if provider == SecretProvider.VAULT:
                    status["providers"][provider.value] = {
                        "active": True,
                        "authenticated": vault_manager._authenticated,
                    }
                elif provider == SecretProvider.DOCKER:
                    status["providers"][provider.value] = {
                        "active": True,
                        "info": docker_secrets_manager.get_secret_info(),
                    }
                else:
                    status["providers"][provider.value] = {"active": True}
            else:
                status["providers"][provider.value] = {"active": False}

        return status

    async def health_check(self) -> Dict[str, Any]:
        """Health check do sistema de secrets"""
        health = {"status": "healthy", "providers": {}, "issues": []}

        for provider in self.providers:
            try:
                if provider == SecretProvider.VAULT:
                    vault = self.providers[provider]
                    if vault._authenticated:
                        health["providers"][provider.value] = "healthy"
                    else:
                        health["providers"][provider.value] = "unhealthy"
                        health["issues"].append(f"Vault não autenticado")

                elif provider == SecretProvider.DOCKER:
                    docker = self.providers[provider]
                    if docker._initialized:
                        health["providers"][provider.value] = "healthy"
                    else:
                        health["providers"][provider.value] = "unhealthy"
                        health["issues"].append(f"Docker Secrets não inicializado")

                else:
                    health["providers"][provider.value] = "healthy"

            except Exception as e:
                health["providers"][provider.value] = "error"
                health["issues"].append(f"{provider.value}: {str(e)}")

        if health["issues"]:
            health["status"] = (
                "degraded"
                if len(health["issues"]) < len(self.providers)
                else "unhealthy"
            )

        return health

    async def close(self):
        """Fechar conexões com provedores"""
        for provider, manager in self.providers.items():
            try:
                if hasattr(manager, "close"):
                    await manager.close()
                logger.info(f"🔒 {provider.value} desconectado")
            except Exception as e:
                logger.error(f"❌ Erro ao fechar {provider.value}: {e}")

        self.providers.clear()
        self.cache.clear()
        self._initialized = False


# Instância global
secrets_manager = UnifiedSecretsManager()
