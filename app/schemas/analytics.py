"""
📊 SCHEMAS PARA ANALYTICS AVANÇADAS
Pydantic models para validação e documentação das APIs de Business Intelligence
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# =================================================================================
#                           ENUMS E TIPOS BASE
# =================================================================================


class RiskLevel(str, Enum):
    """Níveis de risco para churn prediction"""

    low = "low"
    medium = "medium"
    high = "high"


class SegmentType(str, Enum):
    """Tipos de segmentos RFM"""

    vip_champions = "VIP Champions"
    loyal_customers = "Loyal Customers"
    potential_loyalists = "Potential Loyalists"
    new_customers = "New Customers"
    at_risk = "At Risk"
    cannot_lose_them = "Cannot Lose Them"
    lost_customers = "Lost Customers"


class ChannelType(str, Enum):
    """Canais de aquisição"""

    organic = "organic"
    whatsapp = "whatsapp"
    google_ads = "google_ads"
    facebook = "facebook"
    instagram = "instagram"
    referral = "referral"
    other = "other"


# =================================================================================
#                         SCHEMAS DE FUNIL DE CONVERSÃO
# =================================================================================


class ConversionFunnelStageSchema(BaseModel):
    """Schema para estágio individual do funil"""

    stage_name: str = Field(..., description="Nome do estágio")
    stage_order: int = Field(..., description="Ordem do estágio no funil")
    total_users: int = Field(..., description="Total de usuários no estágio")
    conversion_rate: float = Field(
        ..., description="Taxa de conversão para próximo estágio"
    )
    drop_off_count: int = Field(..., description="Usuários que saíram neste estágio")
    avg_time_to_next: Optional[float] = Field(
        None, description="Tempo médio para próximo estágio (horas)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stage_name": "first_contact",
                "stage_order": 1,
                "total_users": 1000,
                "conversion_rate": 85.5,
                "drop_off_count": 145,
                "avg_time_to_next": 2.5,
            }
        }


class ConversionFunnelResponse(BaseModel):
    """Response completa para análise de funil"""

    success: bool = Field(..., description="Status da operação")
    data: Dict[str, Any] = Field(..., description="Dados do funil de conversão")
    message: str = Field(..., description="Mensagem descritiva")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "stages": [
                        {
                            "stage_name": "first_contact",
                            "total_users": 1000,
                            "conversion_rate": 85.5,
                        }
                    ],
                    "overall_conversion": 15.2,
                    "bottlenecks": ["appointment_confirmed"],
                    "analysis_period": "2024-01-01 to 2024-01-31",
                },
                "message": "Análise de funil de conversão concluída com sucesso",
            }
        }


# =================================================================================
#                      SCHEMAS DE SEGMENTAÇÃO DE CLIENTES
# =================================================================================


class CustomerSegmentSchema(BaseModel):
    """Schema para segmento individual de cliente"""

    user_id: int = Field(..., description="ID do usuário")
    nome: str = Field(..., description="Nome do cliente")
    wa_id: str = Field(..., description="WhatsApp ID")
    segment_type: str = Field(..., description="Tipo do segmento RFM")
    rfm_score: str = Field(..., description="Score RFM (ex: 555)")
    recency_score: int = Field(..., description="Score de recência (1-5)")
    frequency_score: int = Field(..., description="Score de frequência (1-5)")
    monetary_score: int = Field(..., description="Score monetário (1-5)")
    total_spent: float = Field(..., description="Valor total gasto")
    total_orders: int = Field(..., description="Total de pedidos")
    avg_order_value: float = Field(..., description="Valor médio do pedido")
    days_since_last_order: int = Field(..., description="Dias desde último pedido")
    customer_lifetime_days: int = Field(..., description="Tempo como cliente (dias)")
    characteristics: List[str] = Field(..., description="Características do segmento")
    recommended_actions: List[str] = Field(..., description="Ações recomendadas")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "nome": "João Silva",
                "wa_id": "5511999999999",
                "segment_type": "VIP Champions",
                "rfm_score": "555",
                "recency_score": 5,
                "frequency_score": 5,
                "monetary_score": 5,
                "total_spent": 2500.50,
                "total_orders": 15,
                "avg_order_value": 166.70,
                "days_since_last_order": 5,
                "customer_lifetime_days": 180,
                "characteristics": ["Clientes mais valiosos do negócio"],
                "recommended_actions": ["Programa VIP exclusivo"],
            }
        }


class CustomerSegmentationResponse(BaseModel):
    """Response para segmentação de clientes"""

    success: bool = Field(..., description="Status da operação")
    data: Dict[str, Any] = Field(..., description="Dados da segmentação")
    message: str = Field(..., description="Mensagem descritiva")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "segments": [],
                    "summary": {"total_segments": 150, "methodology": "RFM Analysis"},
                    "segment_statistics": {
                        "VIP Champions": {"count": 10, "total_value": 25000.0}
                    },
                },
                "message": "Segmentação RFM concluída: 150 clientes analisados",
            }
        }


# =================================================================================
#                        SCHEMAS DE PREDIÇÃO DE CHURN
# =================================================================================


class ChurnPredictionSchema(BaseModel):
    """Schema para predição individual de churn"""

    user_id: int = Field(..., description="ID do usuário")
    nome: str = Field(..., description="Nome do cliente")
    wa_id: str = Field(..., description="WhatsApp ID")
    churn_score: float = Field(..., description="Score de churn (0-100)")
    churn_risk: str = Field(..., description="Nível de risco (low/medium/high)")
    churn_probability: float = Field(..., description="Probabilidade de churn (0-1)")
    key_factors: List[str] = Field(..., description="Principais fatores de risco")
    recommended_actions: List[str] = Field(..., description="Ações recomendadas")
    days_since_last_contact: int = Field(..., description="Dias desde último contato")
    engagement_level: str = Field(..., description="Nível de engajamento")
    monetary_value: float = Field(..., description="Valor monetário do cliente")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "nome": "Maria Santos",
                "wa_id": "5511888888888",
                "churn_score": 75.5,
                "churn_risk": "high",
                "churn_probability": 0.8,
                "key_factors": [
                    "Sem contato há 45 dias",
                    "Baixa frequência de interação",
                ],
                "recommended_actions": [
                    "Contato personalizado do gerente",
                    "Oferta especial exclusiva",
                ],
                "days_since_last_contact": 45,
                "engagement_level": "low",
                "monetary_value": 450.0,
            }
        }


class ChurnPredictionResponse(BaseModel):
    """Response para predição de churn"""

    success: bool = Field(..., description="Status da operação")
    data: Dict[str, Any] = Field(..., description="Dados da predição de churn")
    message: str = Field(..., description="Mensagem descritiva")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "predictions": [],
                    "summary": {
                        "total_customers_analyzed": 200,
                        "high_risk_count": 15,
                        "medium_risk_count": 35,
                        "revenue_at_risk": 12500.50,
                    },
                    "methodology": {"weights": {"recency": 0.4, "frequency": 0.25}},
                },
                "message": "Predição de churn concluída: 15 clientes em alto risco",
            }
        }


# =================================================================================
#                           SCHEMAS DE ROI METRICS
# =================================================================================


class ROIMetricsSchema(BaseModel):
    """Schema para métricas de ROI por canal"""

    canal: str = Field(..., description="Canal de aquisição")
    receita_total: float = Field(..., description="Receita total do canal")
    receita_periodo: float = Field(..., description="Receita no período analisado")
    custo_aquisicao_estimado: float = Field(
        ..., description="Custo estimado de aquisição"
    )
    roi_percentual: float = Field(..., description="ROI em percentual")
    clientes_adquiridos: int = Field(..., description="Clientes adquiridos")
    clientes_pagantes: int = Field(..., description="Clientes que fizeram compras")
    taxa_conversao: float = Field(..., description="Taxa de conversão (%)")
    valor_medio_pedido: float = Field(..., description="Valor médio do pedido")
    clv_estimado: float = Field(..., description="Customer Lifetime Value estimado")
    payback_period_dias: Optional[int] = Field(
        None, description="Período de payback em dias"
    )
    lifetime_dias: int = Field(..., description="Lifetime médio do cliente em dias")

    class Config:
        json_schema_extra = {
            "example": {
                "canal": "google_ads",
                "receita_total": 15000.0,
                "receita_periodo": 5000.0,
                "custo_aquisicao_estimado": 2250.0,
                "roi_percentual": 566.67,
                "clientes_adquiridos": 50,
                "clientes_pagantes": 35,
                "taxa_conversao": 70.0,
                "valor_medio_pedido": 300.0,
                "clv_estimado": 428.57,
                "payback_period_dias": 30,
                "lifetime_dias": 120,
            }
        }


class ROIMetricsResponse(BaseModel):
    """Response para métricas de ROI"""

    success: bool = Field(..., description="Status da operação")
    data: Dict[str, Any] = Field(..., description="Dados das métricas de ROI")
    message: str = Field(..., description="Mensagem descritiva")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "channel_metrics": [],
                    "consolidated_metrics": {
                        "total_revenue": 50000.0,
                        "consolidated_roi": 250.5,
                        "total_customers": 300,
                    },
                    "performance_insights": [
                        "ROI excelente de 250.5% - Estratégia eficaz"
                    ],
                    "methodology": {
                        "roi_formula": "(Revenue - Investment) / Investment * 100"
                    },
                },
                "message": "Análise de ROI concluída - ROI consolidado: 250.5%",
            }
        }


# =================================================================================
#                         SCHEMAS AUXILIARES
# =================================================================================


class AnalyticsPeriod(BaseModel):
    """Schema para período de análise"""

    start_date: str = Field(..., description="Data de início (ISO format)")
    end_date: str = Field(..., description="Data de fim (ISO format)")
    days: int = Field(..., description="Número de dias no período")


class AnalyticsAlert(BaseModel):
    """Schema para alertas do sistema"""

    type: str = Field(..., description="Tipo do alerta (warning/error/info)")
    message: str = Field(..., description="Mensagem do alerta")
    priority: str = Field(..., description="Prioridade (low/medium/high)")
    action_required: bool = Field(..., description="Se requer ação imediata")


class AnalyticsInsight(BaseModel):
    """Schema para insights gerados"""

    category: str = Field(..., description="Categoria do insight")
    description: str = Field(..., description="Descrição do insight")
    impact: str = Field(..., description="Impacto estimado")
    confidence: float = Field(..., description="Confiança no insight (0-1)")


# =================================================================================
#                      SCHEMAS DE DASHBOARD SUMMARY
# =================================================================================


class DashboardKeyMetrics(BaseModel):
    """Métricas-chave do dashboard"""

    consolidated_roi: float = Field(..., description="ROI consolidado (%)")
    total_revenue: float = Field(..., description="Receita total do período")
    high_risk_customers: int = Field(..., description="Clientes em alto risco de churn")
    total_customers: int = Field(..., description="Total de clientes analisados")
    active_segments: int = Field(..., description="Segmentos ativos")


class DashboardSummaryResponse(BaseModel):
    """Response do dashboard summary"""

    success: bool = Field(..., description="Status da operação")
    data: Dict[str, Any] = Field(..., description="Dados do dashboard")
    message: str = Field(..., description="Mensagem descritiva")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "period": {
                        "days": 30,
                        "start_date": "2024-01-01T00:00:00",
                        "end_date": "2024-01-31T23:59:59",
                    },
                    "key_metrics": {
                        "consolidated_roi": 250.5,
                        "total_revenue": 15000.0,
                        "high_risk_customers": 5,
                        "total_customers": 150,
                        "active_segments": 25,
                    },
                    "alerts": ["⚠️ 5 clientes em alto risco de churn"],
                    "insights": ["✅ ROI excelente de 250.5% - Estratégia eficaz"],
                    "quick_actions": [
                        "Ver análise detalhada de churn",
                        "Analisar funil de conversão",
                    ],
                },
                "message": "Dashboard executivo atualizado com sucesso",
            }
        }


# =================================================================================
#                          SCHEMAS DE REQUEST/QUERY
# =================================================================================


class ConversionFunnelRequest(BaseModel):
    """Request parameters para funil de conversão"""

    start_date: Optional[str] = Field(None, description="Data início (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Data fim (YYYY-MM-DD)")
    custom_stages: Optional[List[str]] = Field(
        None, description="Estágios customizados"
    )
    include_cohort: bool = Field(True, description="Incluir análise de coorte")
    segment_by: Optional[str] = Field(
        None, description="Segmentar por (channel/month/week)"
    )


class CustomerSegmentationRequest(BaseModel):
    """Request parameters para segmentação"""

    analysis_date: Optional[str] = Field(None, description="Data da análise")
    include_actions: bool = Field(True, description="Incluir ações recomendadas")
    min_transactions: int = Field(1, description="Mínimo de transações")
    segment_details: bool = Field(True, description="Incluir detalhes dos segmentos")


class ChurnPredictionRequest(BaseModel):
    """Request parameters para predição de churn"""

    analysis_date: Optional[str] = Field(None, description="Data da análise")
    include_low_risk: bool = Field(False, description="Incluir baixo risco")
    risk_threshold: str = Field("medium", description="Filtro mínimo de risco")


class ROIMetricsRequest(BaseModel):
    """Request parameters para métricas de ROI"""

    start_date: Optional[str] = Field(None, description="Data início")
    end_date: Optional[str] = Field(None, description="Data fim")
    include_projections: bool = Field(True, description="Incluir projeções")
    channel_filter: Optional[List[str]] = Field(None, description="Filtros de canal")


# =================================================================================
#                          RESPONSE GENÉRICA
# =================================================================================


class AnalyticsBaseResponse(BaseModel):
    """Response base para todas as APIs de analytics"""

    success: bool = Field(..., description="Status da operação")
    data: Union[Dict[str, Any], List[Any]] = Field(..., description="Dados retornados")
    message: str = Field(..., description="Mensagem descritiva")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp da resposta",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"key": "value"},
                "message": "Operação concluída com sucesso",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
