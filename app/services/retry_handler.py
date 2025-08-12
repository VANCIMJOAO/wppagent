from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema de retry e circuit breaker para APIs externas
"""
import asyncio
import time
import logging
from typing import Callable, Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 120  # 2 minutos - valor padrão mais realista
    expected_exception: type = Exception


@dataclass
class CircuitBreaker:
    config: CircuitBreakerConfig
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    success_count: int = 0


class RetryHandler:
    """Handler para retry com backoff exponencial e circuit breaker"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, service_name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Obtém ou cria um circuit breaker para um serviço"""
        if service_name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuit_breakers[service_name] = CircuitBreaker(config=config)
        
        return self.circuit_breakers[service_name]
    
    async def execute_with_retry(
        self,
        func: Callable,
        service_name: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        circuit_breaker_config: CircuitBreakerConfig = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Executa função com retry e circuit breaker
        
        Args:
            func: Função a ser executada
            service_name: Nome do serviço (para circuit breaker)
            max_retries: Número máximo de tentativas
            base_delay: Delay base em segundos
            max_delay: Delay máximo em segundos
            exponential_base: Base para backoff exponencial
            circuit_breaker_config: Configuração do circuit breaker
        """
        circuit_breaker = self.get_circuit_breaker(service_name, circuit_breaker_config)
        
        # Verificar estado do circuit breaker
        if circuit_breaker.state == CircuitState.OPEN:
            if self._should_attempt_reset(circuit_breaker):
                circuit_breaker.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit breaker para {service_name} mudou para HALF_OPEN")
            else:
                raise Exception(f"Circuit breaker OPEN para {service_name}")
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                
                # Sucesso - reset circuit breaker se necessário
                if circuit_breaker.state == CircuitState.HALF_OPEN:
                    circuit_breaker.success_count += 1
                    if circuit_breaker.success_count >= 3:  # 3 sucessos consecutivos
                        self._reset_circuit_breaker(circuit_breaker, service_name)
                elif circuit_breaker.state == CircuitState.CLOSED and circuit_breaker.failure_count > 0:
                    # Reset contador de falhas em operação normal
                    circuit_breaker.failure_count = 0
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Tentativa {attempt + 1} falhou para {service_name}: {str(e)}")
                
                # Atualizar circuit breaker
                self._handle_failure(circuit_breaker, service_name, e)
                
                # Se circuit breaker está aberto, não tentar mais
                if circuit_breaker.state == CircuitState.OPEN:
                    break
                
                # Se não é a última tentativa, aguardar antes do retry
                if attempt < max_retries:
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    # Adicionar jitter para evitar thundering herd
                    jitter = delay * 0.1 * (0.5 - abs(hash(service_name) % 100) / 100)
                    total_delay = delay + jitter
                    
                    logger.info(f"Aguardando {total_delay:.2f}s antes da próxima tentativa para {service_name}")
                    await asyncio.sleep(total_delay)
        
        # Todas as tentativas falharam
        logger.error(f"Todas as {max_retries + 1} tentativas falharam para {service_name}")
        raise last_exception
    
    def _should_attempt_reset(self, circuit_breaker: CircuitBreaker) -> bool:
        """Verifica se deve tentar resetar o circuit breaker"""
        if circuit_breaker.last_failure_time is None:
            return True
        
        return datetime.now() - circuit_breaker.last_failure_time > timedelta(
            seconds=circuit_breaker.config.recovery_timeout
        )
    
    def _handle_failure(self, circuit_breaker: CircuitBreaker, service_name: str, exception: Exception):
        """Trata falhas no circuit breaker"""
        circuit_breaker.failure_count += 1
        circuit_breaker.last_failure_time = datetime.now()
        circuit_breaker.success_count = 0
        
        if (circuit_breaker.failure_count >= circuit_breaker.config.failure_threshold and
            circuit_breaker.state == CircuitState.CLOSED):
            circuit_breaker.state = CircuitState.OPEN
            logger.error(f"Circuit breaker ABERTO para {service_name} após {circuit_breaker.failure_count} falhas")
        
        elif circuit_breaker.state == CircuitState.HALF_OPEN:
            circuit_breaker.state = CircuitState.OPEN
            logger.error(f"Circuit breaker voltou para OPEN para {service_name}")
    
    def _reset_circuit_breaker(self, circuit_breaker: CircuitBreaker, service_name: str):
        """Reseta o circuit breaker para estado normal"""
        circuit_breaker.state = CircuitState.CLOSED
        circuit_breaker.failure_count = 0
        circuit_breaker.success_count = 0
        circuit_breaker.last_failure_time = None
        logger.info(f"Circuit breaker RESETADO para {service_name}")
    
    def get_circuit_breaker_status(self, service_name: str) -> Dict[str, Any]:
        """Obtém status do circuit breaker"""
        if service_name not in self.circuit_breakers:
            return {"state": "not_initialized"}
        
        cb = self.circuit_breakers[service_name]
        return {
            "state": cb.state.value,
            "failure_count": cb.failure_count,
            "success_count": cb.success_count,
            "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None
        }


# Instância global
retry_handler = RetryHandler()
