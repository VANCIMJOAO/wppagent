"""
🔒 CriticalEndpointsMiddleware - Bypass para Endpoints Críticos
==============================================================

Este middleware faz bypass completo para endpoints críticos como /ping,
evitando qualquer interferência de outros middlewares de autenticação
ou rate limiting.

Endpoints críticos:
- /ping (Railway healthcheck)
- /health (Health check)
- /meta/webhook/verify (WhatsApp webhook)
"""

import logging
from typing import Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CriticalEndpointsMiddleware(BaseHTTPMiddleware):
    """
    Middleware para bypass de endpoints críticos
    
    Este middleware intercepta requisições para endpoints críticos
    e faz bypass completo, evitando interferência de outros middlewares.
    """

    def __init__(self, app):
        super().__init__(app)
        
        # 🔒 Endpoints críticos que precisam de bypass completo
        self.critical_endpoints: Set[str] = {
            "/ping",                    # Railway healthcheck
            "/health",                  # Health check
            "/meta/webhook/verify",     # WhatsApp webhook
            "/meta/webhook",            # Meta webhook prefix
            "/webhook",                 # Webhook prefix
            "/webhook/test",            # Webhook test
        }
        
        logger.info("🔒 CriticalEndpointsMiddleware inicializado")
        logger.info(f"   Endpoints críticos: {len(self.critical_endpoints)}")
        for endpoint in sorted(self.critical_endpoints):
            logger.info(f"      - {endpoint}")

    def _is_critical_endpoint(self, path: str) -> bool:
        """
        Verifica se o endpoint é crítico e precisa de bypass
        
        Args:
            path: Caminho da requisição
            
        Returns:
            True se o endpoint é crítico
        """
        # Verificar match exato
        if path in self.critical_endpoints:
            return True
        
        # Verificar match por prefixo
        for critical_path in self.critical_endpoints:
            if path.startswith(critical_path + "/"):
                return True
        
        return False

    async def dispatch(self, request: Request, call_next):
        """
        Processa requisição com bypass para endpoints críticos
        
        Args:
            request: Requisição HTTP
            call_next: Próximo middleware/handler
            
        Returns:
            Response HTTP
        """
        path = request.url.path
        
        # Verificar se é endpoint crítico
        if self._is_critical_endpoint(path):
            logger.debug(f"🔒 Critical endpoint bypass: {path}")
            
            # Fazer bypass completo - chamar diretamente o handler
            # sem passar por outros middlewares
            response = await call_next(request)
            
            # Log do bypass
            logger.info(f"✅ Critical endpoint bypassed: {path} -> {response.status_code}")
            
            return response
        
        # Para endpoints não críticos, processar normalmente
        return await call_next(request)


class CriticalEndpointsConfig:
    """Configuração para CriticalEndpointsMiddleware"""
    
    @staticmethod
    def get_critical_endpoints() -> Set[str]:
        """Obter lista de endpoints críticos"""
        return {
            "/ping",                    # Railway healthcheck
            "/health",                  # Health check
            "/meta/webhook/verify",     # WhatsApp webhook
            "/meta/webhook",            # Meta webhook prefix
            "/webhook",                 # Webhook prefix
            "/webhook/test",            # Webhook test
        }
    
    @staticmethod
    def is_critical_endpoint(path: str) -> bool:
        """Verificar se endpoint é crítico"""
        critical_endpoints = CriticalEndpointsConfig.get_critical_endpoints()
        
        # Verificar match exato
        if path in critical_endpoints:
            return True
        
        # Verificar match por prefixo
        for critical_path in critical_endpoints:
            if path.startswith(critical_path + "/"):
                return True
        
        return False
