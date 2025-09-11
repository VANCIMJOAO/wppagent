"""
🏥 Schemas para Health Check e Monitoramento
==========================================

Modelos Pydantic para endpoints de saúde e monitoramento do sistema.
Garante tipagem consistente entre backend e frontend.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Resposta básica do health check"""
    status: str = Field(
        description="Status da aplicação",
        example="healthy"
    )
    timestamp: str = Field(
        description="Timestamp da verificação",
        example="2025-09-11T16:45:00.123456"
    )
    service: str = Field(
        description="Nome do serviço",
        example="WhatsApp Agent API"
    )
    version: Optional[str] = Field(
        default="1.0.0",
        description="Versão da aplicação"
    )


class SystemHealth(BaseModel):
    """Status detalhado de um componente do sistema"""
    healthy: bool = Field(description="Se o componente está saudável")
    status: str = Field(description="Status detalhado")
    response_time_ms: Optional[float] = Field(
        default=None,
        description="Tempo de resposta em milissegundos"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detalhes adicionais do componente"
    )


class DetailedHealthResponse(BaseModel):
    """Resposta detalhada do health check"""
    status: str = Field(description="Status geral do sistema")
    timestamp: str = Field(description="Timestamp da verificação")
    service: str = Field(description="Nome do serviço")
    version: str = Field(description="Versão da aplicação")
    
    # Componentes do sistema
    database: SystemHealth = Field(description="Status do banco de dados")
    redis: SystemHealth = Field(description="Status do Redis")
    cache_service: SystemHealth = Field(description="Status do serviço de cache")
    
    # Métricas gerais
    uptime_seconds: float = Field(description="Tempo de atividade em segundos")
    memory_usage_mb: float = Field(description="Uso de memória em MB")
    cpu_usage_percent: float = Field(description="Uso de CPU em porcentagem")
    
    # Status agregado
    overall_healthy: bool = Field(
        description="Se todos os componentes estão saudáveis"
    )


class SystemMetrics(BaseModel):
    """Métricas detalhadas do sistema"""
    database: Optional[SystemHealth] = Field(
        default=None,
        description="Métricas do banco de dados"
    )
    redis: Optional[SystemHealth] = Field(
        default=None,
        description="Métricas do Redis"
    )
    cache_service: Optional[SystemHealth] = Field(
        default=None,
        description="Métricas do serviço de cache"
    )
    memory: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métricas de memória"
    )
    cpu: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métricas de CPU"
    )
    disk: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métricas de disco"
    )
    network: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Métricas de rede"
    )


class AppInfo(BaseModel):
    """Informações básicas da aplicação"""
    message: str = Field(
        description="Mensagem da aplicação",
        example="WhatsApp Agent API"
    )
    version: str = Field(
        description="Versão da aplicação",
        example="1.0.0"
    )
    status: str = Field(
        description="Status da aplicação",
        example="running"
    )
    environment: Optional[str] = Field(
        default=None,
        description="Ambiente de execução"
    )
    docs_url: Optional[str] = Field(
        default="/docs",
        description="URL da documentação"
    )
