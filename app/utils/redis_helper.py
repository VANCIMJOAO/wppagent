"""
Utilitário para obter URL Redis correta do Railway
Resolve problema temporário onde REDIS_URL não está configurada
"""

import os
from app.utils.logger import get_logger

logger = get_logger(__name__)

def get_railway_redis_url() -> str:
    """
    Retorna URL Redis do Railway
    Temporariamente hardcoded até REDIS_URL ser configurada no Railway
    """
    
    # Verificar se há REDIS_URL configurada
    redis_url = os.getenv("REDIS_URL")
    
    if redis_url and redis_url != "redis://localhost:6379/0":
        logger.info(f"🔗 Using REDIS_URL from environment")
        return redis_url
    
    # Fallback para Railway Redis hardcoded
    railway_url = "redis://default:SvSHiMNuuQEtmIUgGIEGqPpXsdZeInDG@yamanote.proxy.rlwy.net:14106"
    logger.info("🚀 Using hardcoded Railway Redis URL")
    return railway_url

def get_redis_config_for_service(service_name: str) -> str:
    """
    Retorna configuração Redis específica para um serviço
    """
    url = get_railway_redis_url()
    logger.info(f"🔧 Redis config for {service_name}: {url.split('@')[-1] if '@' in url else url}")
    return url
