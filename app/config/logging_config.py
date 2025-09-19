"""
Configuração otimizada de logging para Railway
Reduz logs excessivos e evita rate limit
"""

import logging
import os
from typing import Dict, Any

class RailwayLoggingConfig:
    """Configuração de logging otimizada para Railway"""
    
    @staticmethod
    def setup_optimized_logging():
        """Configurar logging otimizado para evitar rate limit"""
        
        # Configurações baseadas no ambiente
        is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
        is_production = os.getenv("ENVIRONMENT") == "production"
        
        # Configurar root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remover handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Handler console otimizado
        console_handler = logging.StreamHandler()
        
        if is_railway or is_production:
            # Formato JSON compacto para Railway/Produção
            formatter = logging.Formatter(
                '{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","logger":"%(name)s"}'
            )
        else:
            # Formato simples para desenvolvimento
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Configurar loggers específicos para reduzir spam
        RailwayLoggingConfig._configure_third_party_loggers()
        RailwayLoggingConfig._configure_application_loggers()
        
        # Log de inicialização
        logger = logging.getLogger(__name__)
        logger.info("Logging otimizado configurado para Railway")
    
    @staticmethod
    def _configure_third_party_loggers():
        """Configurar loggers de bibliotecas externas"""
        
        # Loggers que geram muito spam
        noisy_loggers = {
            "uvicorn.access": logging.WARNING,
            "uvicorn.error": logging.WARNING,
            "sqlalchemy.engine": logging.WARNING,
            "sqlalchemy.pool": logging.WARNING,
            "httpx": logging.WARNING,
            "httpcore": logging.WARNING,
            "asyncio": logging.WARNING,
            "urllib3": logging.WARNING,
            "requests": logging.WARNING,
            "aiohttp": logging.WARNING,
            "redis": logging.WARNING,
            "aioredis": logging.WARNING,
        }
        
        for logger_name, level in noisy_loggers.items():
            logging.getLogger(logger_name).setLevel(level)
    
    @staticmethod
    def _configure_application_loggers():
        """Configurar loggers da aplicação"""
        
        # Loggers de debug que devem ser reduzidos em produção
        debug_loggers = {
            "app.auth.middleware": logging.WARNING,  # Reduzir logs de debug do AuthMiddleware
            "app.security.https_middleware": logging.WARNING,  # Reduzir logs de debug do HTTPS
            "app.middleware.user_rate_limit": logging.WARNING,  # Reduzir logs de rate limiting
            "app.services.structured_apm": logging.INFO,  # Manter APM mas reduzir verbosidade
        }
        
        for logger_name, level in debug_loggers.items():
            logging.getLogger(logger_name).setLevel(level)

class DebugLogFilter:
    """Filtro para reduzir logs de debug em produção"""
    
    def __init__(self, max_debug_per_minute: int = 10):
        self.max_debug_per_minute = max_debug_per_minute
        self.debug_count = 0
        self.last_reset = 0
    
    def filter(self, record):
        """Filtrar logs de debug excessivos"""
        import time
        
        current_time = time.time()
        
        # Reset contador a cada minuto
        if current_time - self.last_reset > 60:
            self.debug_count = 0
            self.last_reset = current_time
        
        # Se é log de debug e já passou do limite
        if record.levelno == logging.DEBUG:
            if self.debug_count >= self.max_debug_per_minute:
                return False
            self.debug_count += 1
        
        return True

def setup_railway_logging():
    """Setup principal de logging para Railway"""
    RailwayLoggingConfig.setup_optimized_logging()
    
    # Adicionar filtro de debug se necessário
    debug_filter = DebugLogFilter(max_debug_per_minute=5)
    
    # Aplicar filtro aos loggers principais
    main_loggers = [
        "app.auth.middleware",
        "app.security.https_middleware", 
        "app.middleware.user_rate_limit"
    ]
    
    for logger_name in main_loggers:
        logger = logging.getLogger(logger_name)
        logger.addFilter(debug_filter)
