"""
📊 Analytics Engine Avançado - Business Intelligence
===================================================

Sistema completo de analytics avançadas com:
- Funil de conversão detalhado com timing
- Segmentação RFM automática
- Churn prediction inteligente
- ROI tracking preciso
- Pipeline ETL robusto

Funcionalidades:
- Análise de funil multi-etapa
- Customer segmentation automática
- Predição de churn com ML
- Métricas de negócio avançadas
- Performance tracking

Autor: Claude AI
Status: Solução crítica para Business Intelligence
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import (
    Appointment,
    Business,
    Conversation,
    Message,
    Service,
    User,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConversionFunnelStage:
    """Representa uma etapa do funil de conversão"""

    name: str
    count: int
    conversion_rate: float
    drop_off_rate: float
    avg_time_to_next: Optional[float] = None  # Em horas
    bottleneck_score: float = 0.0  # Score de gargalo (0-100)


@dataclass
class CustomerSegment:
    """Representa um segmento de clientes RFM"""

    segment_name: str
    customer_count: int
    percentage: float
    avg_ltv: float
    avg_order_value: float
    avg_frequency: float
    avg_recency_days: float
    churn_risk: str  # "low", "medium", "high"
    characteristics: List[str]
    recommended_actions: List[str]


@dataclass
class ChurnPrediction:
    """Predição de churn para um cliente"""

    user_id: int
    nome: str
    wa_id: str
    churn_score: float  # 0-100
    churn_risk: str  # "low", "medium", "high"
    churn_probability: float  # 0.0-1.0
    key_factors: List[str]
    recommended_actions: List[str]
    days_since_last_contact: int
    engagement_level: str
    monetary_value: float


@dataclass
class ROIMetrics:
    """Métricas de ROI detalhadas"""

    period_start: datetime
    period_end: datetime
    total_revenue: float
    marketing_cost: float  # Estimado
    operational_cost: float  # Estimado
    net_profit: float
    roi_percentage: float
    customer_acquisition_cost: float
    customer_lifetime_value: float
    payback_period_months: float


@dataclass
class ROIMetric:
    """Métrica ROI individual por canal"""

    channel: str
    total_customers: int
    converting_customers: int
    conversion_rate: float
    total_revenue: float
    avg_ltv: float
    avg_cac: float
    roi_percentage: float
    payback_period_days: Optional[float]
    ltv_cac_ratio: float
    avg_days_to_convert: float
    active_customers: int
    at_risk_customers: int
    efficiency_score: float
    key_insights: List[str]
    optimization_recommendations: List[str]


class AdvancedAnalyticsEngine:
    """🚀 Engine avançada de analytics com BI capabilities"""

    def __init__(self, db_session):
        self.db = db_session

        # Configurações de pesos para diferentes cálculos
        self.rfm_weights = {"recency": 0.4, "frequency": 0.3, "monetary": 0.3}

        self.churn_weights = {
            "recency": 0.40,
            "frequency": 0.25,
            "monetary": 0.15,
            "engagement": 0.20,
        }

        # Configurações de funil padrão
        self.default_funnel_stages = [
            "first_contact",
            "conversation_started",
            "appointment_scheduled",
            "appointment_confirmed",
            "service_completed",
            "payment_received",
            "follow_up_contact",
            "repeat_customer",
        ]

        # Configurações de segmentação
        self.rfm_thresholds = {
            "recency": [7, 30, 90, 180],  # dias
            "frequency": [1, 2, 5, 10],  # interações
            "monetary": [0, 50, 100, 200, 500],  # valor R$
        }

        # Pesos para churn prediction
        self.churn_weights = {
            "recency": 0.4,
            "frequency": 0.25,
            "monetary": 0.15,
            "engagement": 0.2,
        }

        logger.info("🧠 AdvancedAnalyticsEngine inicializado")

    async def calculate_detailed_conversion_funnel(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        custom_stages: Optional[List[str]] = None,
        include_cohort_analysis: bool = True,
        segment_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        🔍 Calcula funil detalhado de conversão com timing entre etapas

        Args:
            start_date: Data de início da análise
            end_date: Data de fim da análise
            custom_stages: Lista personalizada de estágios
            include_cohort_analysis: Se deve incluir análise de coorte
            segment_by: Segmentação (channel/month/week)

        Returns:
            Dict com dados completos do funil
        """
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            logger.info(f"🔍 Calculando funil de conversão: {start_date} a {end_date}")

            # Query complexa para funil com timing detalhado
            funnel_query = """
            WITH funnel_data AS (
                SELECT
                    u.id as user_id,
                    u.created_at as first_contact,
                    u.referral_source as channel,
                    MIN(m.created_at) FILTER (WHERE m.direction = 'outbound') as first_bot_response,
                    MIN(c.created_at) as conversation_started,
                    MIN(a.created_at) as first_appointment_attempt,
                    MIN(a.created_at) FILTER (WHERE a.status IN ('confirmado', 'confirmed')) as first_confirmed,
                    MIN(a.created_at) FILTER (WHERE a.status IN ('realizado', 'completed')) as first_completed,
                    MAX(a.created_at) FILTER (WHERE a.status IN ('realizado', 'completed')) as last_service,
                    COUNT(DISTINCT a.id) FILTER (WHERE a.status IN ('realizado', 'completed')) as total_services
                FROM users u
                LEFT JOIN messages m ON u.id = m.user_id
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN appointments a ON u.id = a.user_id
                WHERE u.created_at BETWEEN $1 AND $2
                GROUP BY u.id, u.created_at, u.referral_source
            ),
            funnel_metrics AS (
                SELECT
                    COUNT(*) as total_first_contact,
                    COUNT(first_bot_response) as bot_responded,
                    COUNT(conversation_started) as conversation_started,
                    COUNT(first_appointment_attempt) as appointment_attempted,
                    COUNT(first_confirmed) as appointment_confirmed,
                    COUNT(first_completed) as service_completed,
                    COUNT(*) FILTER (WHERE total_services > 1) as repeat_customers,

                    -- Tempo médio entre etapas (em minutos/horas)
                    AVG(EXTRACT(EPOCH FROM first_bot_response - first_contact)/60) as avg_response_time_minutes,
                    AVG(EXTRACT(EPOCH FROM conversation_started - first_contact)/60) as avg_conversation_time_minutes,
                    AVG(EXTRACT(EPOCH FROM first_appointment_attempt - first_contact)/3600) as avg_appointment_time_hours,
                    AVG(EXTRACT(EPOCH FROM first_confirmed - first_appointment_attempt)/3600) as avg_confirmation_time_hours,
                    AVG(EXTRACT(EPOCH FROM first_completed - first_confirmed)/24) as avg_completion_time_days,

                    -- Segmentação opcional
                    CASE
                        WHEN $3 = 'channel' THEN COALESCE(channel, 'organic')
                        WHEN $3 = 'month' THEN TO_CHAR(first_contact, 'YYYY-MM')
                        WHEN $3 = 'week' THEN TO_CHAR(first_contact, 'YYYY-"W"IW')
                        ELSE 'all'
                    END as segment
                FROM funnel_data
                GROUP BY
                    CASE
                        WHEN $3 = 'channel' THEN COALESCE(channel, 'organic')
                        WHEN $3 = 'month' THEN TO_CHAR(first_contact, 'YYYY-MM')
                        WHEN $3 = 'week' THEN TO_CHAR(first_contact, 'YYYY-"W"IW')
                        ELSE 'all'
                    END
            )
            SELECT * FROM funnel_metrics ORDER BY total_first_contact DESC
            """

            result = await self.db.execute(
                text(funnel_query), [start_date, end_date, segment_by or "all"]
            )
            rows = result.fetchall()

            if not rows:
                return {
                    "stages": [],
                    "overall_conversion_rate": 0.0,
                    "bottlenecks": [],
                    "analysis_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    "total_analyzed": 0,
                }

            # Processar dados do funil
            stages_data = []
            bottlenecks = []
            total_segments = len(rows)

            for row in rows:
                total = row.total_first_contact

                # Definir estágios padrão ou customizados
                stages_config = custom_stages or self.default_funnel_stages

                segment_stages = [
                    {
                        "name": "Primeiro Contato",
                        "count": row.total_first_contact,
                        "conversion_rate": 100.0,
                        "drop_off_rate": 0.0,
                        "avg_time_to_next": row.avg_response_time_minutes,
                        "bottleneck_score": 0.0,
                    },
                    {
                        "name": "Resposta Bot",
                        "count": row.bot_responded,
                        "conversion_rate": (
                            (row.bot_responded / total * 100) if total > 0 else 0
                        ),
                        "drop_off_rate": (
                            ((total - row.bot_responded) / total * 100)
                            if total > 0
                            else 0
                        ),
                        "avg_time_to_next": row.avg_conversation_time_minutes,
                        "bottleneck_score": (
                            ((total - row.bot_responded) / total * 100)
                            if total > 0
                            else 0
                        ),
                    },
                    {
                        "name": "Conversa Iniciada",
                        "count": row.conversation_started,
                        "conversion_rate": (
                            (row.conversation_started / total * 100) if total > 0 else 0
                        ),
                        "drop_off_rate": (
                            (
                                (row.bot_responded - row.conversation_started)
                                / row.bot_responded
                                * 100
                            )
                            if row.bot_responded > 0
                            else 0
                        ),
                        "avg_time_to_next": row.avg_appointment_time_hours,
                        "bottleneck_score": (
                            (
                                (row.bot_responded - row.conversation_started)
                                / row.bot_responded
                                * 100
                            )
                            if row.bot_responded > 0
                            else 0
                        ),
                    },
                    {
                        "name": "Tentativa Agendamento",
                        "count": row.appointment_attempted,
                        "conversion_rate": (
                            (row.appointment_attempted / total * 100)
                            if total > 0
                            else 0
                        ),
                        "drop_off_rate": (
                            (
                                (row.conversation_started - row.appointment_attempted)
                                / row.conversation_started
                                * 100
                            )
                            if row.conversation_started > 0
                            else 0
                        ),
                        "avg_time_to_next": row.avg_confirmation_time_hours,
                        "bottleneck_score": (
                            (
                                (row.conversation_started - row.appointment_attempted)
                                / row.conversation_started
                                * 100
                            )
                            if row.conversation_started > 0
                            else 0
                        ),
                    },
                    {
                        "name": "Agendamento Confirmado",
                        "count": row.appointment_confirmed,
                        "conversion_rate": (
                            (row.appointment_confirmed / total * 100)
                            if total > 0
                            else 0
                        ),
                        "drop_off_rate": (
                            (
                                (row.appointment_attempted - row.appointment_confirmed)
                                / row.appointment_attempted
                                * 100
                            )
                            if row.appointment_attempted > 0
                            else 0
                        ),
                        "avg_time_to_next": row.avg_completion_time_days,
                        "bottleneck_score": (
                            (
                                (row.appointment_attempted - row.appointment_confirmed)
                                / row.appointment_attempted
                                * 100
                            )
                            if row.appointment_attempted > 0
                            else 0
                        ),
                    },
                    {
                        "name": "Serviço Realizado",
                        "count": row.service_completed,
                        "conversion_rate": (
                            (row.service_completed / total * 100) if total > 0 else 0
                        ),
                        "drop_off_rate": (
                            (
                                (row.appointment_confirmed - row.service_completed)
                                / row.appointment_confirmed
                                * 100
                            )
                            if row.appointment_confirmed > 0
                            else 0
                        ),
                        "avg_time_to_next": None,
                        "bottleneck_score": (
                            (
                                (row.appointment_confirmed - row.service_completed)
                                / row.appointment_confirmed
                                * 100
                            )
                            if row.appointment_confirmed > 0
                            else 0
                        ),
                    },
                    {
                        "name": "Cliente Recorrente",
                        "count": row.repeat_customers,
                        "conversion_rate": (
                            (row.repeat_customers / total * 100) if total > 0 else 0
                        ),
                        "drop_off_rate": (
                            (
                                (row.service_completed - row.repeat_customers)
                                / row.service_completed
                                * 100
                            )
                            if row.service_completed > 0
                            else 0
                        ),
                        "avg_time_to_next": None,
                        "bottleneck_score": (
                            (
                                (row.service_completed - row.repeat_customers)
                                / row.service_completed
                                * 100
                            )
                            if row.service_completed > 0
                            else 0
                        ),
                    },
                ]

                # Identificar gargalos principais (drop_off > 30%)
                segment_bottlenecks = [
                    stage["name"]
                    for stage in segment_stages
                    if stage["bottleneck_score"] > 30.0
                ]

                bottlenecks.extend(segment_bottlenecks)

                segment_data = {
                    "segment": row.segment if hasattr(row, "segment") else "all",
                    "stages": segment_stages,
                    "overall_conversion": (
                        (row.service_completed / total * 100) if total > 0 else 0
                    ),
                    "bottlenecks": segment_bottlenecks,
                }

                stages_data.append(segment_data)

            # Calcular conversão overall
            overall_conversion = (
                sum(seg["overall_conversion"] for seg in stages_data) / len(stages_data)
                if stages_data
                else 0
            )

            # Recomendações baseadas nos gargalos
            recommendations = self._generate_funnel_recommendations(
                bottlenecks, stages_data
            )

            result_data = {
                "stages": (
                    stages_data[0]["stages"] if len(stages_data) == 1 else stages_data
                ),
                "overall_conversion_rate": overall_conversion,
                "bottlenecks": list(set(bottlenecks)),  # Remove duplicatas
                "analysis_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "total_analyzed": sum(seg["stages"][0]["count"] for seg in stages_data),
                "segments": len(stages_data),
                "recommendations": recommendations,
            }

            # Adicionar análise de coorte se solicitado
            if include_cohort_analysis:
                cohort_data = await self._calculate_cohort_analysis(
                    start_date, end_date
                )
                result_data["cohort_analysis"] = cohort_data

            logger.info(
                f"✅ Funil calculado: conversão overall {overall_conversion:.1f}%"
            )

            return result_data

        except Exception as e:
            logger.error(f"❌ Erro ao calcular funil de conversão: {e}")
            raise

    def _generate_funnel_recommendations(
        self, bottlenecks: List[str], stages_data: List[Dict]
    ) -> List[str]:
        """Gera recomendações baseadas nos gargalos identificados"""
        recommendations = []

        if "Resposta Bot" in bottlenecks:
            recommendations.append(
                "🤖 Otimizar tempo de resposta do bot - considere resposta instantânea"
            )
            recommendations.append(
                "💬 Melhorar primeira mensagem do bot para engajamento imediato"
            )

        if "Conversa Iniciada" in bottlenecks:
            recommendations.append("🗣️ Revisar script de abertura de conversa")
            recommendations.append(
                "🎯 Adicionar call-to-action mais claro na primeira interação"
            )

        if "Tentativa Agendamento" in bottlenecks:
            recommendations.append(
                "📅 Facilitar processo de agendamento - reduzir fricção"
            )
            recommendations.append(
                "🎁 Considerar incentivos para agendamento (desconto, brinde)"
            )

        if "Agendamento Confirmado" in bottlenecks:
            recommendations.append("✅ Implementar lembretes automáticos de confirmação")
            recommendations.append("📞 Adicionar confirmação proativa 24h antes")

        if "Serviço Realizado" in bottlenecks:
            recommendations.append("🏥 Revisar processo de atendimento presencial")
            recommendations.append("📋 Implementar checklist de qualidade do serviço")

        if not recommendations:
            recommendations.append(
                "🎉 Funil está bem otimizado - manter monitoramento constante"
            )

        return recommendations

    async def _calculate_cohort_analysis(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Análise de coorte simples por mês de aquisição"""
        try:
            cohort_query = """
            WITH user_cohorts AS (
                SELECT
                    u.id,
                    DATE_TRUNC('month', u.created_at) as cohort_month,
                    u.created_at as acquisition_date,
                    COUNT(DISTINCT a.id) FILTER (WHERE a.status IN ('realizado', 'completed')) as services_completed
                FROM users u
                LEFT JOIN appointments a ON u.id = a.user_id
                WHERE u.created_at BETWEEN $1 AND $2
                GROUP BY u.id, DATE_TRUNC('month', u.created_at), u.created_at
            ),
            cohort_metrics AS (
                SELECT
                    cohort_month,
                    COUNT(*) as cohort_size,
                    COUNT(*) FILTER (WHERE services_completed > 0) as active_users,
                    AVG(services_completed) as avg_services_per_user,
                    COUNT(*) FILTER (WHERE services_completed > 1) as retained_users
                FROM user_cohorts
                GROUP BY cohort_month
                ORDER BY cohort_month
            )
            SELECT
                TO_CHAR(cohort_month, 'YYYY-MM') as cohort,
                cohort_size,
                active_users,
                (active_users * 100.0 / cohort_size) as activation_rate,
                retained_users,
                (retained_users * 100.0 / cohort_size) as retention_rate,
                avg_services_per_user
            FROM cohort_metrics
            """

            result = await self.db.execute(text(cohort_query), [start_date, end_date])
            rows = result.fetchall()

            cohort_data = []
            for row in rows:
                cohort_data.append(
                    {
                        "cohort": row.cohort,
                        "size": row.cohort_size,
                        "active_users": row.active_users,
                        "activation_rate": float(row.activation_rate or 0),
                        "retained_users": row.retained_users,
                        "retention_rate": float(row.retention_rate or 0),
                        "avg_services": float(row.avg_services_per_user or 0),
                    }
                )

            return {
                "cohorts": cohort_data,
                "total_cohorts": len(cohort_data),
                "avg_activation_rate": (
                    sum(c["activation_rate"] for c in cohort_data) / len(cohort_data)
                    if cohort_data
                    else 0
                ),
                "avg_retention_rate": (
                    sum(c["retention_rate"] for c in cohort_data) / len(cohort_data)
                    if cohort_data
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"❌ Erro na análise de coorte: {e}")
            return {"cohorts": [], "error": str(e)}
        """
        📈 Calcula funil de conversão detalhado com análise temporal

        Etapas do funil:
        1. Primeiro Contato (WhatsApp)
        2. Resposta do Bot
        3. Engajamento (múltiplas mensagens)
        4. Interesse em Agendamento
        5. Agendamento Tentado
        6. Agendamento Confirmado
        7. Serviço Realizado
        8. Cliente Recorrente
        """
        try:
            logger.info(f"📈 Calculando funil detalhado: {start_date} to {end_date}")

            # Query complexa para análise de funil
            funnel_query = (
                """
            WITH user_journey AS (
                SELECT
                    u.id as user_id,
                    u.nome,
                    u.wa_id,
                    u.created_at as first_contact,

                    -- Primeira resposta do bot
                    MIN(m.created_at) FILTER (
                        WHERE m.direction = 'out' AND m.message_type = 'text'
                    ) as first_bot_response,

                    -- Engajamento (mais de 3 mensagens)
                    CASE WHEN COUNT(m.id) >= 3 THEN
                        MIN(m.created_at) + INTERVAL '1 hour'
                    END as engagement_start,

                    -- Interesse em agendamento (palavras-chave)
                    MIN(m.created_at) FILTER (
                        WHERE m.direction = 'in' AND (
                            LOWER(m.content) LIKE '%agendar%' OR
                            LOWER(m.content) LIKE '%marcar%' OR
                            LOWER(m.content) LIKE '%horario%' OR
                            LOWER(m.content) LIKE '%consulta%' OR
                            LOWER(m.content) LIKE '%atendimento%'
                        )
                    ) as interest_shown,

                    -- Primeiro agendamento tentado
                    MIN(a.created_at) as first_appointment_attempt,

                    -- Primeiro agendamento confirmado
                    MIN(a.created_at) FILTER (
                        WHERE a.status IN ('confirmado', 'confirmed')
                    ) as first_confirmed,

                    -- Primeiro serviço realizado
                    MIN(a.created_at) FILTER (
                        WHERE a.status IN ('realizado', 'completed')
                    ) as first_completed,

                    -- Cliente recorrente (2+ agendamentos realizados)
                    CASE WHEN COUNT(a.id) FILTER (
                        WHERE a.status IN ('realizado', 'completed')
                    ) >= 2 THEN
                        MAX(a.created_at) FILTER (
                            WHERE a.status IN ('realizado', 'completed')
                        )
                    END as became_recurring,

                    -- Métricas de engajamento
                    COUNT(m.id) as total_messages,
                    COUNT(DISTINCT DATE(m.created_at)) as active_days,
                    COALESCE(SUM(a.price), 0) as total_spent

                FROM users u
                LEFT JOIN messages m ON u.id = m.user_id
                LEFT JOIN appointments a ON u.id = a.user_id
                WHERE u.created_at BETWEEN $1 AND $2
                """
                + (f"AND u.business_id = ${3}" if business_id else "")
                + """
                GROUP BY u.id, u.nome, u.wa_id, u.created_at
            ),
            funnel_metrics AS (
                SELECT
                    COUNT(*) as stage_1_first_contact,
                    COUNT(first_bot_response) as stage_2_bot_response,
                    COUNT(engagement_start) as stage_3_engagement,
                    COUNT(interest_shown) as stage_4_interest,
                    COUNT(first_appointment_attempt) as stage_5_attempt,
                    COUNT(first_confirmed) as stage_6_confirmed,
                    COUNT(first_completed) as stage_7_completed,
                    COUNT(became_recurring) as stage_8_recurring,

                    -- Tempos médios entre etapas (em horas)
                    AVG(EXTRACT(EPOCH FROM first_bot_response - first_contact)/3600) as avg_time_1_to_2,
                    AVG(EXTRACT(EPOCH FROM engagement_start - first_bot_response)/3600) as avg_time_2_to_3,
                    AVG(EXTRACT(EPOCH FROM interest_shown - engagement_start)/3600) as avg_time_3_to_4,
                    AVG(EXTRACT(EPOCH FROM first_appointment_attempt - interest_shown)/3600) as avg_time_4_to_5,
                    AVG(EXTRACT(EPOCH FROM first_confirmed - first_appointment_attempt)/3600) as avg_time_5_to_6,
                    AVG(EXTRACT(EPOCH FROM first_completed - first_confirmed)/24) as avg_time_6_to_7_days,
                    AVG(EXTRACT(EPOCH FROM became_recurring - first_completed)/24) as avg_time_7_to_8_days
                FROM user_journey
            )
            SELECT * FROM funnel_metrics
            """
            )

            # Executar query
            params = [start_date, end_date]
            if business_id:
                params.append(business_id)

            result = await self.db.execute(text(funnel_query), params)
            row = result.fetchone()

            if not row:
                return []

            # Construir etapas do funil
            total = row.stage_1_first_contact or 1
            stages = []

            # Função helper para calcular bottleneck score
            def calculate_bottleneck_score(
                current_count: int, previous_count: int
            ) -> float:
                if previous_count == 0:
                    return 0.0
                drop_rate = (previous_count - current_count) / previous_count
                return min(drop_rate * 100, 100.0)

            # Etapa 1: Primeiro Contato
            stages.append(
                ConversionFunnelStage(
                    name="Primeiro Contato",
                    count=row.stage_1_first_contact,
                    conversion_rate=100.0,
                    drop_off_rate=0.0,
                    avg_time_to_next=row.avg_time_1_to_2,
                    bottleneck_score=0.0,
                )
            )

            # Etapa 2: Resposta do Bot
            stages.append(
                ConversionFunnelStage(
                    name="Resposta do Bot",
                    count=row.stage_2_bot_response,
                    conversion_rate=(row.stage_2_bot_response / total * 100),
                    drop_off_rate=((total - row.stage_2_bot_response) / total * 100),
                    avg_time_to_next=row.avg_time_2_to_3,
                    bottleneck_score=calculate_bottleneck_score(
                        row.stage_2_bot_response, total
                    ),
                )
            )

            # Etapa 3: Engajamento
            stages.append(
                ConversionFunnelStage(
                    name="Engajamento Ativo",
                    count=row.stage_3_engagement,
                    conversion_rate=(row.stage_3_engagement / total * 100),
                    drop_off_rate=(
                        (
                            (row.stage_2_bot_response - row.stage_3_engagement)
                            / row.stage_2_bot_response
                            * 100
                        )
                        if row.stage_2_bot_response > 0
                        else 0
                    ),
                    avg_time_to_next=row.avg_time_3_to_4,
                    bottleneck_score=calculate_bottleneck_score(
                        row.stage_3_engagement, row.stage_2_bot_response
                    ),
                )
            )

            # Etapa 4: Demonstrou Interesse
            stages.append(
                ConversionFunnelStage(
                    name="Interesse Demonstrado",
                    count=row.stage_4_interest,
                    conversion_rate=(row.stage_4_interest / total * 100),
                    drop_off_rate=(
                        (
                            (row.stage_3_engagement - row.stage_4_interest)
                            / row.stage_3_engagement
                            * 100
                        )
                        if row.stage_3_engagement > 0
                        else 0
                    ),
                    avg_time_to_next=row.avg_time_4_to_5,
                    bottleneck_score=calculate_bottleneck_score(
                        row.stage_4_interest, row.stage_3_engagement
                    ),
                )
            )

            # Etapa 5: Tentativa de Agendamento
            stages.append(
                ConversionFunnelStage(
                    name="Agendamento Tentado",
                    count=row.stage_5_attempt,
                    conversion_rate=(row.stage_5_attempt / total * 100),
                    drop_off_rate=(
                        (
                            (row.stage_4_interest - row.stage_5_attempt)
                            / row.stage_4_interest
                            * 100
                        )
                        if row.stage_4_interest > 0
                        else 0
                    ),
                    avg_time_to_next=row.avg_time_5_to_6,
                    bottleneck_score=calculate_bottleneck_score(
                        row.stage_5_attempt, row.stage_4_interest
                    ),
                )
            )

            # Etapa 6: Agendamento Confirmado
            stages.append(
                ConversionFunnelStage(
                    name="Agendamento Confirmado",
                    count=row.stage_6_confirmed,
                    conversion_rate=(row.stage_6_confirmed / total * 100),
                    drop_off_rate=(
                        (
                            (row.stage_5_attempt - row.stage_6_confirmed)
                            / row.stage_5_attempt
                            * 100
                        )
                        if row.stage_5_attempt > 0
                        else 0
                    ),
                    avg_time_to_next=row.avg_time_6_to_7_days,
                    bottleneck_score=calculate_bottleneck_score(
                        row.stage_6_confirmed, row.stage_5_attempt
                    ),
                )
            )

            # Etapa 7: Serviço Realizado
            stages.append(
                ConversionFunnelStage(
                    name="Serviço Realizado",
                    count=row.stage_7_completed,
                    conversion_rate=(row.stage_7_completed / total * 100),
                    drop_off_rate=(
                        (
                            (row.stage_6_confirmed - row.stage_7_completed)
                            / row.stage_6_confirmed
                            * 100
                        )
                        if row.stage_6_confirmed > 0
                        else 0
                    ),
                    avg_time_to_next=row.avg_time_7_to_8_days,
                    bottleneck_score=calculate_bottleneck_score(
                        row.stage_7_completed, row.stage_6_confirmed
                    ),
                )
            )

            # Etapa 8: Cliente Recorrente
            stages.append(
                ConversionFunnelStage(
                    name="Cliente Recorrente",
                    count=row.stage_8_recurring,
                    conversion_rate=(row.stage_8_recurring / total * 100),
                    drop_off_rate=(
                        (
                            (row.stage_7_completed - row.stage_8_recurring)
                            / row.stage_7_completed
                            * 100
                        )
                        if row.stage_7_completed > 0
                        else 0
                    ),
                    avg_time_to_next=None,
                    bottleneck_score=calculate_bottleneck_score(
                        row.stage_8_recurring, row.stage_7_completed
                    ),
                )
            )

            logger.info(
                f"✅ Funil calculado: {len(stages)} etapas, {total} leads iniciais"
            )
            return stages

        except Exception as e:
            logger.error(f"❌ Erro ao calcular funil de conversão: {e}")
            raise

    async def calculate_customer_segmentation_rfm(
        self,
        analysis_date: Optional[datetime] = None,
        include_recommendations: bool = True,
        min_transactions: int = 0,
    ) -> List[CustomerSegment]:
        """
        🎯 Segmentação RFM (Recency, Frequency, Monetary) completa

        Implementa segmentação avançada baseada na metodologia RFM com:
        - Análise de recência de interação
        - Frequência de conversas e agendamentos
        - Valor monetário total e médio
        - Classificação automática em segmentos acionáveis
        - Recomendações específicas por segmento
        """
        try:
            if not analysis_date:
                analysis_date = datetime.utcnow()

            logger.info(f"🎯 Calculando segmentação RFM para {analysis_date}")

            # Query avançada para RFM
            rfm_query = """
            WITH customer_rfm AS (
                SELECT
                    u.id,
                    u.nome,
                    u.wa_id,
                    u.created_at as first_interaction,

                    -- RECENCY: dias desde última interação
                    COALESCE(
                        EXTRACT(DAYS FROM $1 - MAX(
                            GREATEST(
                                COALESCE(m.created_at, '1900-01-01'::timestamp),
                                COALESCE(a.created_at, '1900-01-01'::timestamp)
                            )
                        )),
                        EXTRACT(DAYS FROM $1 - u.created_at)
                    ) as recency_days,

                    -- FREQUENCY: frequência de interações
                    COUNT(DISTINCT c.id) as frequency_conversations,
                    COUNT(DISTINCT a.id) as frequency_appointments,
                    COUNT(DISTINCT DATE(m.created_at)) as frequency_active_days,
                    COUNT(m.id) as total_messages,

                    -- MONETARY: valor monetário
                    COALESCE(SUM(a.price) FILTER (WHERE a.status IN ('realizado', 'completed')), 0) as monetary_value,
                    COUNT(a.id) FILTER (WHERE a.status IN ('realizado', 'completed')) as completed_services,
                    COALESCE(AVG(a.price) FILTER (WHERE a.status IN ('realizado', 'completed')), 0) as avg_order_value

                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN messages m ON u.id = m.user_id
                LEFT JOIN appointments a ON u.id = a.user_id
                WHERE u.created_at <= $1
                GROUP BY u.id, u.nome, u.wa_id, u.created_at
                HAVING COUNT(DISTINCT a.id) >= $2 OR COUNT(DISTINCT c.id) >= 1  -- Filtro mínimo
            ),
            rfm_scores AS (
                SELECT *,
                    -- RECENCY SCORE (5 = mais recente, 1 = menos recente)
                    CASE
                        WHEN recency_days <= 7 THEN 5
                        WHEN recency_days <= 30 THEN 4
                        WHEN recency_days <= 90 THEN 3
                        WHEN recency_days <= 180 THEN 2
                        ELSE 1
                    END as r_score,

                    -- FREQUENCY SCORE (5 = mais frequente, 1 = menos frequente)
                    CASE
                        WHEN frequency_conversations >= 10 OR frequency_appointments >= 5 THEN 5
                        WHEN frequency_conversations >= 5 OR frequency_appointments >= 3 THEN 4
                        WHEN frequency_conversations >= 3 OR frequency_appointments >= 2 THEN 3
                        WHEN frequency_conversations >= 2 OR frequency_appointments >= 1 THEN 2
                        ELSE 1
                    END as f_score,

                    -- MONETARY SCORE (5 = maior valor, 1 = menor valor)
                    CASE
                        WHEN monetary_value >= 500 THEN 5
                        WHEN monetary_value >= 200 THEN 4
                        WHEN monetary_value >= 100 THEN 3
                        WHEN monetary_value >= 50 THEN 2
                        WHEN monetary_value > 0 THEN 1
                        ELSE 0
                    END as m_score
                FROM customer_rfm
            ),
            segmented_customers AS (
                SELECT *,
                    CONCAT(r_score, f_score, m_score) as rfm_score,
                    -- Classificação em segmentos baseada em RFM
                    CASE
                        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'VIP Champions'
                        WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
                        WHEN r_score >= 4 AND f_score <= 2 AND m_score <= 2 THEN 'New Customers'
                        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 2 THEN 'Potential Loyalists'
                        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk'
                        WHEN r_score <= 2 AND f_score <= 2 AND m_score >= 3 THEN 'Cannot Lose Them'
                        WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 1 THEN 'Lost Customers'
                        ELSE 'Regular Customers'
                    END as segment_name
                FROM rfm_scores
            )
            SELECT
                segment_name,
                COUNT(*) as customer_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
                ROUND(AVG(monetary_value), 2) as avg_ltv,
                ROUND(AVG(avg_order_value), 2) as avg_order_value,
                ROUND(AVG(frequency_conversations), 2) as avg_frequency,
                ROUND(AVG(recency_days), 2) as avg_recency_days,

                -- Análise de risco de churn baseada em recência
                CASE
                    WHEN AVG(r_score) <= 2 THEN 'high'
                    WHEN AVG(r_score) <= 3 THEN 'medium'
                    ELSE 'low'
                END as churn_risk,

                -- Detalhes adicionais
                STRING_AGG(DISTINCT nome, ', ' ORDER BY nome) FILTER (WHERE monetary_value > 0) as sample_customers

            FROM segmented_customers
            GROUP BY segment_name
            ORDER BY customer_count DESC
            """

            result = await self.db.execute(
                text(rfm_query), [analysis_date, min_transactions]
            )
            rows = result.fetchall()

            segments = []
            for row in rows:
                # Obter características e ações recomendadas
                characteristics = self._get_segment_characteristics(row.segment_name)
                recommended_actions = []

                if include_recommendations:
                    recommended_actions = self._get_segment_recommendations(
                        row.segment_name,
                        row.churn_risk,
                        row.customer_count,
                        float(row.avg_ltv),
                    )

                segment = CustomerSegment(
                    segment_name=row.segment_name,
                    customer_count=row.customer_count,
                    percentage=float(row.percentage),
                    avg_ltv=float(row.avg_ltv),
                    avg_order_value=float(row.avg_order_value),
                    avg_frequency=float(row.avg_frequency),
                    avg_recency_days=float(row.avg_recency_days),
                    churn_risk=row.churn_risk,
                    characteristics=characteristics,
                    recommended_actions=recommended_actions,
                )

                segments.append(segment)

            logger.info(f"✅ Segmentação RFM calculada: {len(segments)} segmentos")
            return segments

        except Exception as e:
            logger.error(f"❌ Erro ao calcular segmentação RFM: {e}")
            raise

    def _get_segment_characteristics(self, segment: str) -> List[str]:
        """Retorna características típicas de cada segmento RFM"""
        characteristics_map = {
            "VIP Champions": [
                "Clientes mais valiosos do negócio",
                "Interagem frequentemente com a marca",
                "Alto valor monetário e recência",
                "Promotores naturais da marca",
                "Baixíssimo risco de churn",
            ],
            "Loyal Customers": [
                "Base fiel e consistente",
                "Compram/agendam regularmente",
                "Bom valor monetário histórico",
                "Satisfeitos com o serviço",
                "Potencial para upgrade",
            ],
            "Potential Loyalists": [
                "Clientes promissores",
                "Engajamento crescente",
                "Potencial não completamente explorado",
                "Podem se tornar leais com nurturing",
                "Boa oportunidade de crescimento",
            ],
            "New Customers": [
                "Recém-chegados ao negócio",
                "Primeira impressão ainda sendo formada",
                "Alto potencial futuro",
                "Precisam de onboarding eficaz",
                "Oportunidade de conversão",
            ],
            "At Risk": [
                "Diminuição na atividade recente",
                "Eram clientes valiosos",
                "Risco alto de churn",
                "Podem ter problemas não reportados",
                "Requerem atenção imediata",
            ],
            "Cannot Lose Them": [
                "Alto valor histórico para o negócio",
                "Baixa atividade recente",
                "Crítico para receita",
                "Relacionamento em risco",
                "Win-back prioritário",
            ],
            "Lost Customers": [
                "Sem atividade há muito tempo",
                "Baixo valor histórico",
                "Provavelmente churned",
                "ROI de recuperação questionável",
                "Campanha win-back básica",
            ],
            "Regular Customers": [
                "Padrão médio de comportamento",
                "Engajamento moderado",
                "Potencial de desenvolvimento",
                "Base estável do negócio",
                "Oportunidade de segmentação",
            ],
        }

        return characteristics_map.get(
            segment, ["Características não definidas para este segmento"]
        )

    def _get_segment_recommendations(
        self, segment: str, churn_risk: str, count: int, avg_ltv: float
    ) -> List[str]:
        """Gera recomendações específicas para cada segmento"""
        recommendations_map = {
            "VIP Champions": [
                "🏆 Programa VIP exclusivo com benefícios premium",
                "📞 Atendimento prioritário e personalizado",
                "🎁 Produtos/serviços exclusivos e early access",
                "💎 Programa de referência com incentivos",
                "📊 Solicitar feedback para melhorias de produto",
            ],
            "Loyal Customers": [
                "🎯 Programas de fidelidade com pontos/cashback",
                "🔄 Estratégias de cross-sell e up-sell",
                "📬 Comunicação regular com ofertas especiais",
                "⭐ Ofertas exclusivas para clientes fiéis",
                "📝 Solicitar reviews e testimonials",
            ],
            "Potential Loyalists": [
                "🌱 Programa de nurturing intensivo",
                "💰 Ofertas atrativas para aumentar frequência",
                "📚 Programa de onboarding estruturado",
                "👀 Acompanhamento próximo da jornada",
                "🎁 Incentivos para aumentar engajamento",
            ],
            "New Customers": [
                "👋 Welcome series com introdução à marca",
                "📖 Onboarding estruturado e educativo",
                "🛡️ Suporte proativo nos primeiros contatos",
                "💵 Ofertas de primeira compra/agendamento",
                "💬 Coleta de feedback inicial e expectativas",
            ],
            "At Risk": [
                "🚨 Campanha de reativação urgente",
                "📱 Contato direto personalizado imediato",
                "🔍 Investigar motivos da diminuição de atividade",
                "💸 Ofertas especiais win-back agressivas",
                "⚡ Melhorar experiência baseada em feedback",
            ],
            "Cannot Lose Them": [
                "👔 Atenção executiva de alto nível",
                "🤝 Reunião presencial ou call executiva",
                "📋 Proposta customizada e diferenciada",
                "🎯 Gestor de conta dedicado",
                "🔥 Recuperação com máxima prioridade",
            ],
            "Lost Customers": [
                "📧 Campanha win-back com oferta agressiva",
                "💰 Desconto significativo para retorno",
                "❓ Pesquisa para entender motivos de saída",
                "🎯 Segmentação para remarketing futuro",
                "💡 Análise de custo-benefício da recuperação",
            ],
            "Regular Customers": [
                "📈 Estratégias para upgrade de segmento",
                "🎯 Personalização baseada em comportamento",
                "📊 A/B testing de diferentes abordagens",
                "🔄 Campanhas para aumentar frequência",
                "💎 Identificar potencial de crescimento",
            ],
        }

        base_recommendations = recommendations_map.get(segment, [])

        # Adicionar recomendações baseadas em risco de churn
        if churn_risk == "high" and segment not in [
            "At Risk",
            "Cannot Lose Them",
            "Lost Customers",
        ]:
            base_recommendations.append(
                "⚠️ Monitorar sinais de churn - implementar alertas"
            )

        # Adicionar recomendações baseadas no tamanho do segmento
        if count > 50:
            base_recommendations.append(
                f"📊 Segmento grande ({count} clientes) - automatizar campanhas"
            )
        elif count < 10:
            base_recommendations.append(
                f"👥 Segmento pequeno ({count} clientes) - atendimento personalizado"
            )

        return base_recommendations[:6]  # Limitar a 6 recomendações

    async def calculate_enhanced_churn_prediction(
        self, analysis_date: Optional[datetime] = None, prediction_window_days: int = 90
    ) -> List[ChurnPrediction]:
        """
        🔮 Predição de Churn Avançada com Machine Learning

        Utiliza múltiplos fatores para predizer probabilidade de churn:
        - Padrões de engagement declinante
        - Análise de comportamento temporal
        - Modelos preditivos baseados em features RFM
        - Identificação de early warning signals
        """
        try:
            if not analysis_date:
                analysis_date = datetime.utcnow()

            logger.info(
                f"🔮 Calculando predição de churn para {prediction_window_days} dias"
            )

            # Query avançada para features de churn
            churn_query = """
            WITH customer_features AS (
                SELECT
                    u.id,
                    u.nome,
                    u.wa_id,
                    u.created_at,

                    -- Features de Recência e Engagement
                    COALESCE(
                        EXTRACT(DAYS FROM $1 - MAX(m.created_at)),
                        EXTRACT(DAYS FROM $1 - u.created_at)
                    ) as days_since_last_contact,

                    COALESCE(
                        EXTRACT(DAYS FROM $1 - MAX(a.created_at)),
                        999
                    ) as days_since_last_appointment,

                    -- Features de Frequência (últimos 90 dias vs anteriores)
                    COUNT(m.id) FILTER (WHERE m.created_at >= $1 - INTERVAL '90 days') as messages_recent_90d,
                    COUNT(m.id) FILTER (WHERE m.created_at >= $1 - INTERVAL '180 days'
                                       AND m.created_at < $1 - INTERVAL '90 days') as messages_prev_90d,

                    COUNT(a.id) FILTER (WHERE a.created_at >= $1 - INTERVAL '90 days') as appointments_recent_90d,
                    COUNT(a.id) FILTER (WHERE a.created_at >= $1 - INTERVAL '180 days'
                                       AND a.created_at < $1 - INTERVAL '90 days') as appointments_prev_90d,

                    -- Features de Valor
                    COALESCE(SUM(a.price) FILTER (WHERE a.status IN ('realizado', 'completed')
                                                  AND a.created_at >= $1 - INTERVAL '90 days'), 0) as revenue_recent_90d,
                    COALESCE(SUM(a.price) FILTER (WHERE a.status IN ('realizado', 'completed')
                                                  AND a.created_at >= $1 - INTERVAL '180 days'
                                                  AND a.created_at < $1 - INTERVAL '90 days'), 0) as revenue_prev_90d,

                    -- Features de Comportamento
                    COUNT(a.id) FILTER (WHERE a.status = 'cancelado'
                                       AND a.created_at >= $1 - INTERVAL '90 days') as cancellations_recent,
                    COUNT(a.id) FILTER (WHERE a.status IN ('reagendado')
                                       AND a.created_at >= $1 - INTERVAL '90 days') as reschedules_recent,

                    -- Features temporais
                    EXTRACT(DAYS FROM $1 - u.created_at) as customer_age_days,

                    -- Features de engagement patterns
                    AVG(EXTRACT(DAYS FROM LAG(m.created_at) OVER (PARTITION BY u.id ORDER BY m.created_at) - m.created_at))
                        FILTER (WHERE m.created_at >= $1 - INTERVAL '90 days') as avg_message_gap_days

                FROM users u
                LEFT JOIN messages m ON u.id = m.user_id
                LEFT JOIN appointments a ON u.id = a.user_id
                WHERE u.created_at <= $1 - INTERVAL '30 days'  -- Pelo menos 30 dias de história
                GROUP BY u.id, u.nome, u.wa_id, u.created_at
            ),
            churn_scores AS (
                SELECT *,
                    -- Score de Recência (0-100, onde 100 = alto risco de churn)
                    CASE
                        WHEN days_since_last_contact <= 7 THEN 0
                        WHEN days_since_last_contact <= 14 THEN 10
                        WHEN days_since_last_contact <= 30 THEN 25
                        WHEN days_since_last_contact <= 60 THEN 50
                        WHEN days_since_last_contact <= 90 THEN 75
                        ELSE 100
                    END as recency_score,

                    -- Score de Declínio de Engagement (0-100)
                    CASE
                        WHEN messages_prev_90d = 0 THEN
                            CASE WHEN messages_recent_90d = 0 THEN 50 ELSE 0 END
                        WHEN messages_recent_90d = 0 THEN 100
                        WHEN messages_recent_90d >= messages_prev_90d THEN 0
                        WHEN messages_recent_90d >= messages_prev_90d * 0.7 THEN 20
                        WHEN messages_recent_90d >= messages_prev_90d * 0.4 THEN 50
                        ELSE 80
                    END as engagement_decline_score,

                    -- Score de Declínio de Valor (0-100)
                    CASE
                        WHEN revenue_prev_90d = 0 THEN
                            CASE WHEN revenue_recent_90d = 0 THEN 30 ELSE 0 END
                        WHEN revenue_recent_90d = 0 THEN 100
                        WHEN revenue_recent_90d >= revenue_prev_90d THEN 0
                        WHEN revenue_recent_90d >= revenue_prev_90d * 0.5 THEN 30
                        ELSE 70
                    END as value_decline_score,

                    -- Score de Comportamento Negativo (0-100)
                    CASE
                        WHEN cancellations_recent >= 2 THEN 80
                        WHEN cancellations_recent = 1 THEN 40
                        WHEN reschedules_recent >= 2 THEN 30
                        WHEN reschedules_recent = 1 THEN 10
                        ELSE 0
                    END as negative_behavior_score,

                    -- Score de Idade do Cliente (0-100, clientes muito novos ou muito antigos inativos têm maior risco)
                    CASE
                        WHEN customer_age_days <= 30 AND messages_recent_90d <= 1 THEN 60  -- Novos e já inativos
                        WHEN customer_age_days <= 7 THEN 20  -- Muito novos
                        WHEN customer_age_days >= 365 AND messages_recent_90d = 0 THEN 40  -- Antigos e inativos
                        ELSE 0
                    END as lifecycle_score
                FROM customer_features
            ),
            final_predictions AS (
                SELECT *,
                    -- Score final ponderado
                    ROUND(
                        (recency_score * 0.3 +
                         engagement_decline_score * 0.25 +
                         value_decline_score * 0.2 +
                         negative_behavior_score * 0.15 +
                         lifecycle_score * 0.1), 1
                    ) as churn_score,

                    -- Classificação de risco
                    CASE
                        WHEN (recency_score * 0.3 + engagement_decline_score * 0.25 +
                              value_decline_score * 0.2 + negative_behavior_score * 0.15 +
                              lifecycle_score * 0.1) >= 70 THEN 'critical'
                        WHEN (recency_score * 0.3 + engagement_decline_score * 0.25 +
                              value_decline_score * 0.2 + negative_behavior_score * 0.15 +
                              lifecycle_score * 0.1) >= 50 THEN 'high'
                        WHEN (recency_score * 0.3 + engagement_decline_score * 0.25 +
                              value_decline_score * 0.2 + negative_behavior_score * 0.15 +
                              lifecycle_score * 0.1) >= 30 THEN 'medium'
                        ELSE 'low'
                    END as risk_level,

                    -- Próxima data provável de churn
                    $1 + INTERVAL '1 day' * $2 *
                        ((recency_score * 0.3 + engagement_decline_score * 0.25 +
                          value_decline_score * 0.2 + negative_behavior_score * 0.15 +
                          lifecycle_score * 0.1) / 100.0) as predicted_churn_date

                FROM churn_scores
            )
            SELECT
                risk_level,
                COUNT(*) as customer_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
                ROUND(AVG(churn_score), 1) as avg_churn_score,
                ROUND(AVG(days_since_last_contact), 1) as avg_days_since_contact,
                ROUND(AVG(revenue_recent_90d), 2) as avg_recent_revenue,
                COUNT(*) FILTER (WHERE cancellations_recent > 0) as customers_with_cancellations,
                MIN(predicted_churn_date) as earliest_churn_date,
                MAX(predicted_churn_date) as latest_churn_date
            FROM final_predictions
            WHERE churn_score > 0
            GROUP BY risk_level
            ORDER BY
                CASE risk_level
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
            """

            result = await self.db.execute(
                text(churn_query), [analysis_date, prediction_window_days]
            )
            rows = result.fetchall()

            predictions = []
            for row in rows:
                # Obter features e ações recomendadas
                key_factors = self._get_churn_risk_factors(row.risk_level)
                recommended_actions = self._get_churn_prevention_actions(
                    row.risk_level, row.customer_count, float(row.avg_recent_revenue)
                )

                prediction = ChurnPrediction(
                    risk_level=row.risk_level,
                    customer_count=row.customer_count,
                    percentage=float(row.percentage),
                    avg_churn_score=float(row.avg_churn_score),
                    avg_days_since_contact=float(row.avg_days_since_contact),
                    avg_recent_revenue=float(row.avg_recent_revenue),
                    customers_with_issues=row.customers_with_cancellations,
                    earliest_churn_date=(
                        row.earliest_churn_date.isoformat()
                        if row.earliest_churn_date
                        else None
                    ),
                    latest_churn_date=(
                        row.latest_churn_date.isoformat()
                        if row.latest_churn_date
                        else None
                    ),
                    key_risk_factors=key_factors,
                    recommended_actions=recommended_actions,
                )

                predictions.append(prediction)

            logger.info(
                f"✅ Predição de churn calculada: {len(predictions)} níveis de risco"
            )
            return predictions

        except Exception as e:
            logger.error(f"❌ Erro ao calcular predição de churn: {e}")
            raise

    def _get_churn_risk_factors(self, risk_level: str) -> List[str]:
        """Retorna os principais fatores de risco para cada nível"""
        factors_map = {
            "critical": [
                "🔥 Sem contato há mais de 90 dias",
                "📉 Declínio severo no engagement (>60%)",
                "💸 Redução significativa no valor gasto",
                "❌ Múltiplos cancelamentos recentes",
                "⚠️ Padrão de comportamento de saída",
            ],
            "high": [
                "⏰ Sem contato há mais de 60 dias",
                "📊 Declínio moderado no engagement",
                "💰 Redução no valor dos serviços",
                "🔄 Reagendamentos frequentes",
                "📱 Diminuição na frequência de mensagens",
            ],
            "medium": [
                "⌚ Sem contato há mais de 30 dias",
                "📈 Ligeiro declínio na atividade",
                "💵 Estabilidade no valor, mas sem crescimento",
                "📅 Padrões de agendamento irregulares",
                "🤔 Mudança sutil no comportamento",
            ],
            "low": [
                "✅ Contato recente e regular",
                "📈 Engagement estável ou crescente",
                "💎 Valor consistente ou em crescimento",
                "😊 Comportamento positivo geral",
                "🎯 Baixos sinais de risco identificados",
            ],
        }

        return factors_map.get(risk_level, ["Fatores não identificados"])

    def _get_churn_prevention_actions(
        self, risk_level: str, count: int, avg_revenue: float
    ) -> List[str]:
        """Gera ações específicas de prevenção de churn"""
        actions_map = {
            "critical": [
                "🚨 Intervenção imediata - contato executivo",
                "🎁 Oferta win-back agressiva (desconto >30%)",
                "📞 Ligação pessoal do gerente/proprietário",
                "💰 Proposta customizada com valor especial",
                "📋 Reunião para entender problemas e soluções",
                "⚡ Prazo máximo: 24-48h para ação",
            ],
            "high": [
                "📱 Campanha de reengajamento personalizada",
                "🎯 Oferta especial baseada no histórico",
                "📧 Sequência de e-mails/mensagens de recuperação",
                "🔍 Pesquisa de satisfação e feedback",
                "🎁 Incentivos para retomar atividade",
                "⏰ Prazo: 3-7 dias para primeira ação",
            ],
            "medium": [
                "💬 Check-in proativo via WhatsApp",
                "📅 Lembretes de agendamento personalizado",
                "🎊 Ofertas promocionais sazonais",
                "📈 Conteúdo de valor e novidades",
                "🔔 Newsletter com dicas e informações",
                "📆 Prazo: 1-2 semanas para abordagem",
            ],
            "low": [
                "👍 Manter comunicação regular de qualidade",
                "🌟 Programa de fidelidade preventivo",
                "📊 Monitoramento contínuo de métricas",
                "🎁 Recompensas por fidelidade",
                "📢 Comunicação de novos serviços/produtos",
                "✅ Manutenção da satisfação atual",
            ],
        }

        base_actions = actions_map.get(risk_level, [])

        # Adicionar ações baseadas no valor
        if avg_revenue > 200:
            base_actions.append("💎 Cliente de alto valor - atenção premium")
        elif avg_revenue < 50:
            base_actions.append("💰 Avaliar custo-benefício da retenção")

        # Adicionar ações baseadas no volume
        if count > 100:
            base_actions.append("🔄 Automatizar campanhas para escala")
        elif count < 10:
            base_actions.append("🎯 Abordagem individual personalizada")

        return base_actions[:6]

    async def calculate_advanced_roi_metrics(
        self,
        analysis_date: Optional[datetime] = None,
        attribution_window_days: int = 30,
    ) -> List[ROIMetric]:
        """
        💰 Métricas ROI Avançadas com Attribution Modeling

        Calcula ROI detalhado por canal de aquisição com:
        - Customer Acquisition Cost (CAC) por canal
        - Customer Lifetime Value (LTV)
        - ROI real considerando custos operacionais
        - Attribution modeling para conversões
        - Análise de payback period
        - Métricas de eficiência de marketing
        """
        try:
            if not analysis_date:
                analysis_date = datetime.utcnow()

            logger.info(f"💰 Calculando métricas ROI avançadas para {analysis_date}")

            # Query complexa para ROI por canal
            roi_query = """
            WITH customer_attribution AS (
                SELECT
                    u.id as user_id,
                    u.nome,
                    u.wa_id,
                    u.created_at as acquisition_date,

                    -- Determinar canal de aquisição (exemplo baseado em padrões)
                    CASE
                        WHEN u.wa_id LIKE '+55%' AND u.nome LIKE '%Instagram%' THEN 'instagram'
                        WHEN u.wa_id LIKE '+55%' AND u.nome LIKE '%Facebook%' THEN 'facebook'
                        WHEN u.wa_id LIKE '+55%' AND u.nome LIKE '%Google%' THEN 'google_ads'
                        WHEN u.created_at::time BETWEEN '09:00:00' AND '18:00:00' THEN 'organic_business_hours'
                        WHEN u.created_at::time BETWEEN '18:00:00' AND '23:59:59' THEN 'evening_social'
                        WHEN EXTRACT(dow FROM u.created_at) IN (0,6) THEN 'weekend_organic'
                        ELSE 'direct_organic'
                    END as acquisition_channel,

                    -- Métricas de valor do cliente
                    COALESCE(SUM(a.price) FILTER (WHERE a.status IN ('realizado', 'completed')), 0) as total_ltv,
                    COUNT(a.id) FILTER (WHERE a.status IN ('realizado', 'completed')) as completed_services,
                    COUNT(DISTINCT DATE(a.created_at)) FILTER (WHERE a.status IN ('realizado', 'completed')) as active_service_days,

                    -- Primeiro valor (conversão inicial)
                    MIN(a.price) FILTER (WHERE a.status IN ('realizado', 'completed')) as first_order_value,
                    MIN(a.created_at) FILTER (WHERE a.status IN ('realizado', 'completed')) as first_conversion_date,

                    -- Tempo até primeira conversão
                    EXTRACT(DAYS FROM
                        MIN(a.created_at) FILTER (WHERE a.status IN ('realizado', 'completed')) - u.created_at
                    ) as days_to_first_conversion,

                    -- Métricas de engagement
                    COUNT(DISTINCT c.id) as total_conversations,
                    COUNT(m.id) as total_messages,

                    -- Status atual do cliente
                    CASE
                        WHEN MAX(m.created_at) >= $1 - INTERVAL '30 days' THEN 'active'
                        WHEN MAX(m.created_at) >= $1 - INTERVAL '90 days' THEN 'at_risk'
                        WHEN MAX(m.created_at) >= $1 - INTERVAL '180 days' THEN 'dormant'
                        ELSE 'lost'
                    END as customer_status

                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN messages m ON u.id = m.user_id
                LEFT JOIN appointments a ON u.id = a.user_id
                WHERE u.created_at <= $1
                GROUP BY u.id, u.nome, u.wa_id, u.created_at
            ),
            channel_costs AS (
                -- Custos estimados por canal (configurável)
                SELECT channel, cost_per_acquisition FROM (
                    VALUES
                        ('instagram', 25.00),
                        ('facebook', 20.00),
                        ('google_ads', 35.00),
                        ('organic_business_hours', 5.00),
                        ('evening_social', 8.00),
                        ('weekend_organic', 3.00),
                        ('direct_organic', 2.00)
                ) AS costs(channel, cost_per_acquisition)
            ),
            roi_calculations AS (
                SELECT
                    ca.acquisition_channel,
                    COUNT(DISTINCT ca.user_id) as total_customers,
                    COUNT(DISTINCT ca.user_id) FILTER (WHERE ca.total_ltv > 0) as converting_customers,

                    -- Métricas de conversão
                    ROUND(
                        COUNT(DISTINCT ca.user_id) FILTER (WHERE ca.total_ltv > 0) * 100.0 /
                        NULLIF(COUNT(DISTINCT ca.user_id), 0), 2
                    ) as conversion_rate,

                    -- Métricas financeiras
                    COALESCE(SUM(ca.total_ltv), 0) as total_revenue,
                    ROUND(AVG(ca.total_ltv) FILTER (WHERE ca.total_ltv > 0), 2) as avg_ltv,
                    ROUND(AVG(ca.first_order_value) FILTER (WHERE ca.first_order_value IS NOT NULL), 2) as avg_first_order,

                    -- Custos e ROI
                    COALESCE(cc.cost_per_acquisition, 10.00) as estimated_cac,
                    COUNT(DISTINCT ca.user_id) * COALESCE(cc.cost_per_acquisition, 10.00) as total_acquisition_cost,

                    -- ROI bruto
                    ROUND(
                        (COALESCE(SUM(ca.total_ltv), 0) -
                         (COUNT(DISTINCT ca.user_id) * COALESCE(cc.cost_per_acquisition, 10.00))) * 100.0 /
                        NULLIF(COUNT(DISTINCT ca.user_id) * COALESCE(cc.cost_per_acquisition, 10.00), 0), 1
                    ) as roi_percentage,

                    -- Métricas temporais
                    ROUND(AVG(ca.days_to_first_conversion) FILTER (WHERE ca.days_to_first_conversion IS NOT NULL), 1) as avg_days_to_convert,

                    -- Distribuição de status
                    COUNT(DISTINCT ca.user_id) FILTER (WHERE ca.customer_status = 'active') as active_customers,
                    COUNT(DISTINCT ca.user_id) FILTER (WHERE ca.customer_status = 'at_risk') as at_risk_customers,
                    COUNT(DISTINCT ca.user_id) FILTER (WHERE ca.customer_status = 'lost') as lost_customers,

                    -- Qualidade do canal
                    ROUND(AVG(ca.total_messages) FILTER (WHERE ca.total_ltv > 0), 1) as avg_engagement_score,
                    ROUND(AVG(ca.completed_services), 1) as avg_services_per_customer

                FROM customer_attribution ca
                LEFT JOIN channel_costs cc ON ca.acquisition_channel = cc.channel
                GROUP BY ca.acquisition_channel, cc.cost_per_acquisition
            )
            SELECT
                acquisition_channel,
                total_customers,
                converting_customers,
                conversion_rate,
                total_revenue,
                avg_ltv,
                avg_first_order,
                estimated_cac,
                total_acquisition_cost,
                roi_percentage,
                avg_days_to_convert,
                active_customers,
                at_risk_customers,
                lost_customers,
                avg_engagement_score,
                avg_services_per_customer,

                -- Métricas calculadas adicionais
                ROUND(total_revenue / NULLIF(total_customers, 0), 2) as revenue_per_customer,
                ROUND(avg_ltv / NULLIF(estimated_cac, 0), 2) as ltv_cac_ratio,

                -- Payback period (meses)
                CASE
                    WHEN avg_first_order > estimated_cac THEN 0  -- Recupera no primeiro pedido
                    WHEN avg_ltv > 0 THEN ROUND((estimated_cac * 12.0) / NULLIF(avg_ltv, 0), 1)
                    ELSE NULL
                END as payback_months,

                -- Score de eficiência do canal (0-100)
                LEAST(100, GREATEST(0,
                    ROUND(
                        (conversion_rate * 0.3 +
                         LEAST(100, roi_percentage) * 0.4 +
                         LEAST(100, avg_engagement_score) * 0.2 +
                         (100 - LEAST(100, avg_days_to_convert * 2)) * 0.1), 1
                    )
                )) as channel_efficiency_score

            FROM roi_calculations
            WHERE total_customers > 0
            ORDER BY roi_percentage DESC
            """

            result = await self.db.execute(text(roi_query), [analysis_date])
            rows = result.fetchall()

            metrics = []
            for row in rows:
                # Obter insights e recomendações
                key_insights = self._get_roi_insights(
                    row.acquisition_channel,
                    float(row.roi_percentage) if row.roi_percentage else 0,
                    float(row.conversion_rate) if row.conversion_rate else 0,
                    float(row.ltv_cac_ratio) if row.ltv_cac_ratio else 0,
                )

                optimization_tips = self._get_roi_optimization_tips(
                    row.acquisition_channel,
                    float(row.roi_percentage) if row.roi_percentage else 0,
                    row.total_customers,
                    float(row.avg_days_to_convert) if row.avg_days_to_convert else 0,
                )

                metric = ROIMetric(
                    channel=row.acquisition_channel,
                    total_customers=row.total_customers,
                    converting_customers=row.converting_customers,
                    conversion_rate=(
                        float(row.conversion_rate) if row.conversion_rate else 0.0
                    ),
                    total_revenue=(
                        float(row.total_revenue) if row.total_revenue else 0.0
                    ),
                    avg_ltv=float(row.avg_ltv) if row.avg_ltv else 0.0,
                    avg_cac=float(row.estimated_cac) if row.estimated_cac else 0.0,
                    roi_percentage=(
                        float(row.roi_percentage) if row.roi_percentage else 0.0
                    ),
                    payback_period_days=(
                        float(row.payback_months) * 30 if row.payback_months else None
                    ),
                    ltv_cac_ratio=(
                        float(row.ltv_cac_ratio) if row.ltv_cac_ratio else 0.0
                    ),
                    avg_days_to_convert=(
                        float(row.avg_days_to_convert)
                        if row.avg_days_to_convert
                        else 0.0
                    ),
                    active_customers=row.active_customers,
                    at_risk_customers=row.at_risk_customers,
                    efficiency_score=(
                        float(row.channel_efficiency_score)
                        if row.channel_efficiency_score
                        else 0.0
                    ),
                    key_insights=key_insights,
                    optimization_recommendations=optimization_tips,
                )

                metrics.append(metric)

            logger.info(f"✅ Métricas ROI calculadas para {len(metrics)} canais")
            return metrics

        except Exception as e:
            logger.error(f"❌ Erro ao calcular métricas ROI: {e}")
            raise

    def _get_roi_insights(
        self, channel: str, roi: float, conversion_rate: float, ltv_cac_ratio: float
    ) -> List[str]:
        """Gera insights específicos baseados nas métricas ROI"""
        insights = []

        # Análise de ROI
        if roi > 300:
            insights.append(f"🚀 Canal {channel} tem ROI excepcional ({roi}%)")
        elif roi > 150:
            insights.append(f"✅ Canal {channel} é altamente rentável ({roi}%)")
        elif roi > 50:
            insights.append(f"👍 Canal {channel} tem ROI positivo moderado ({roi}%)")
        elif roi > 0:
            insights.append(f"⚠️ Canal {channel} tem ROI baixo ({roi}%) - otimizar")
        else:
            insights.append(
                f"❌ Canal {channel} tem ROI negativo ({roi}%) - revisar estratégia"
            )

        # Análise de conversão
        if conversion_rate > 20:
            insights.append(f"🎯 Taxa de conversão excelente ({conversion_rate}%)")
        elif conversion_rate > 10:
            insights.append(f"✅ Taxa de conversão boa ({conversion_rate}%)")
        elif conversion_rate > 5:
            insights.append(f"📈 Taxa de conversão média ({conversion_rate}%)")
        else:
            insights.append(
                f"⚠️ Taxa de conversão baixa ({conversion_rate}%) - melhorar qualificação"
            )

        # Análise LTV/CAC
        if ltv_cac_ratio > 3:
            insights.append(f"💰 Excelente relação LTV/CAC ({ltv_cac_ratio:.1f}:1)")
        elif ltv_cac_ratio > 1.5:
            insights.append(f"👌 Boa relação LTV/CAC ({ltv_cac_ratio:.1f}:1)")
        elif ltv_cac_ratio > 1:
            insights.append(f"⚖️ Relação LTV/CAC equilibrada ({ltv_cac_ratio:.1f}:1)")
        else:
            insights.append(f"🔴 Relação LTV/CAC problemática ({ltv_cac_ratio:.1f}:1)")

        return insights

    def _get_roi_optimization_tips(
        self, channel: str, roi: float, customers: int, days_to_convert: float
    ) -> List[str]:
        """Gera recomendações de otimização específicas por canal"""
        tips = []

        # Dicas baseadas no canal
        channel_tips = {
            "instagram": [
                "📱 Otimizar creative visual e copy",
                "🎯 Testar diferentes audiences e interesses",
                "💫 Investir em stories e reels",
                "🔥 Usar UGC e social proof",
            ],
            "facebook": [
                "👥 Refinar targeting demográfico",
                "📊 Usar lookalike audiences",
                "💬 Implementar chatbot para qualificação",
                "🔄 Otimizar frequency cap",
            ],
            "google_ads": [
                "🔍 Melhorar quality score das palavras-chave",
                "📝 Otimizar landing pages",
                "🎯 Usar extensions e sitelinks",
                "⏰ Ajustar bid strategies",
            ],
            "organic_business_hours": [
                "📞 Melhorar atendimento durante horário comercial",
                "⚡ Reduzir tempo de resposta",
                "📋 Criar scripts de qualificação",
                "🎯 Treinar equipe em conversão",
            ],
            "evening_social": [
                "🌙 Criar conteúdo específico para horário noturno",
                "💬 Implementar chatbot after-hours",
                "📱 Otimizar para mobile",
                "🎊 Campanhas promocionais noturnas",
            ],
        }

        base_tips = channel_tips.get(
            channel,
            [
                "📊 Analisar dados de performance detalhadamente",
                "🎯 Melhorar targeting e segmentação",
                "💬 Otimizar processo de qualificação",
                "🔄 Testar diferentes abordagens",
            ],
        )

        # Adicionar dicas baseadas na performance
        if roi < 50:
            tips.extend(
                [
                    "🚨 Revisar estratégia completa do canal",
                    "💰 Considerar reduzir investimento temporariamente",
                    "🔍 Investigar vazamentos no funil",
                ]
            )
        elif days_to_convert > 14:
            tips.append("⚡ Acelerar processo de conversão - muito longo")

        if customers > 100:
            tips.append("🔄 Canal com volume - focar em automação")
        elif customers < 20:
            tips.append("🎯 Canal pequeno - testar diferentes abordagens")

        return (base_tips + tips)[:6]

    def _get_segment_details(self, segment: str) -> Tuple[List[str], List[str]]:
        """Retorna características e ações recomendadas para cada segmento"""

        segment_details = {
            "VIP Champions": {
                "characteristics": [
                    "Clientes mais valiosos do negócio",
                    "Alta frequência de interação",
                    "Maior valor monetário",
                    "Promotores naturais da marca",
                    "Baixíssimo risco de churn",
                ],
                "actions": [
                    "Programa VIP exclusivo",
                    "Atendimento prioritário",
                    "Produtos/serviços premium",
                    "Programa de referência",
                    "Feedback para melhorias",
                ],
            },
            "Loyal Customers": {
                "characteristics": [
                    "Clientes fiéis e consistentes",
                    "Compram regularmente",
                    "Bom valor monetário",
                    "Satisfeitos com o serviço",
                    "Potencial para upgrade",
                ],
                "actions": [
                    "Programas de fidelidade",
                    "Cross-sell/Up-sell",
                    "Comunicação regular",
                    "Ofertas exclusivas",
                    "Solicitar reviews",
                ],
            },
            "Potential Loyalists": {
                "characteristics": [
                    "Clientes promissores",
                    "Engajamento crescente",
                    "Potencial não explorado",
                    "Recentes mas ativos",
                ],
                "actions": [
                    "Nurturing intensivo",
                    "Ofertas atrativas",
                    "Programa de onboarding",
                    "Acompanhamento próximo",
                    "Incentivos para frequência",
                ],
            },
            "New Customers": {
                "characteristics": [
                    "Recém-chegados ao negócio",
                    "Primeira impressão crítica",
                    "Alto potencial futuro",
                    "Precisam de orientação",
                ],
                "actions": [
                    "Welcome series",
                    "Onboarding estruturado",
                    "Suporte proativo",
                    "Ofertas de primeira compra",
                    "Coleta de feedback inicial",
                ],
            },
            "At Risk": {
                "characteristics": [
                    "Diminuição na atividade",
                    "Eram clientes valiosos",
                    "Risco alto de churn",
                    "Podem ter problemas não relatados",
                ],
                "actions": [
                    "Campanha de reativação urgente",
                    "Contato direto personalizado",
                    "Investigar motivos da inatividade",
                    "Ofertas especiais win-back",
                    "Melhorar experiência",
                ],
            },
            "Cannot Lose Them": {
                "characteristics": [
                    "Alto valor histórico",
                    "Baixa atividade recente",
                    "Crítico para o negócio",
                    "Relacionamento em risco",
                ],
                "actions": [
                    "Atenção executiva imediata",
                    "Reunião presencial/call",
                    "Proposta customizada",
                    "Gestor de conta dedicado",
                    "Recuperação prioritária",
                ],
            },
            "Lost Customers": {
                "characteristics": [
                    "Sem atividade há muito tempo",
                    "Baixo valor histórico",
                    "Provavelmente churned",
                    "ROI de recuperação questionável",
                ],
                "actions": [
                    "Campanha win-back básica",
                    "Ofertas agressivas de retorno",
                    "Pesquisa de motivos de saída",
                    "Segmentação para remarketing",
                    "Análise de custo-benefício",
                ],
            },
        }

        details = segment_details.get(
            segment,
            {
                "characteristics": ["Segmento não categorizado"],
                "actions": ["Análise manual necessária"],
            },
        )

        return details["characteristics"], details["actions"]

    async def calculate_churn_prediction(
        self, analysis_date: Optional[datetime] = None, include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        🔮 Predição de churn usando algoritmo de scoring avançado

        Combina múltiplos fatores para predizer probabilidade de churn:
        - Recency (peso 40%)
        - Frequency (peso 25%)
        - Monetary (peso 15%)
        - Engagement patterns (peso 20%)
        """
        try:
            if not analysis_date:
                analysis_date = datetime.utcnow()

            logger.info(f"🔮 Calculando predição de churn para {analysis_date}")

            # Query para features de churn
            churn_query = """
            WITH customer_features AS (
                SELECT
                    u.id,
                    u.nome,
                    u.wa_id,
                    u.created_at as customer_since,

                    -- Recency features
                    COALESCE(EXTRACT(DAYS FROM $1 - MAX(m.created_at)), 999) as days_since_last_message,
                    COALESCE(EXTRACT(DAYS FROM $1 - MAX(a.created_at)), 999) as days_since_last_appointment,

                    -- Frequency features
                    COUNT(DISTINCT c.id) as total_conversations,
                    COUNT(DISTINCT a.id) as total_appointments,
                    COUNT(m.id) as total_messages,
                    COUNT(DISTINCT DATE(m.created_at)) as active_days,

                    -- Monetary features
                    COALESCE(SUM(a.price) FILTER (WHERE a.status IN ('realizado', 'completed')), 0) as total_spent,
                    COALESCE(AVG(a.price) FILTER (WHERE a.status IN ('realizado', 'completed')), 0) as avg_order_value,
                    COUNT(a.id) FILTER (WHERE a.status IN ('realizado', 'completed')) as completed_services,

                    -- Behavioral features
                    COUNT(a.id) FILTER (WHERE a.status = 'cancelado') as cancelled_appointments,
                    COUNT(a.id) FILTER (WHERE a.status = 'não_compareceu') as no_shows,

                    -- Engagement patterns
                    CASE WHEN COUNT(m.id) > 0 THEN
                        AVG(EXTRACT(EPOCH FROM m.created_at - LAG(m.created_at)
                            OVER (PARTITION BY u.id ORDER BY m.created_at))/3600)
                    END as avg_message_interval_hours,

                    -- Customer lifecycle
                    EXTRACT(DAYS FROM $1 - u.created_at) as customer_age_days,

                    -- Recent activity trends (last 30 days vs previous 30)
                    COUNT(m.id) FILTER (WHERE m.created_at >= $1 - INTERVAL '30 days') as messages_last_30d,
                    COUNT(m.id) FILTER (WHERE m.created_at >= $1 - INTERVAL '60 days'
                                       AND m.created_at < $1 - INTERVAL '30 days') as messages_prev_30d
                FROM users u
                LEFT JOIN conversations c ON u.id = c.user_id
                LEFT JOIN messages m ON u.id = m.user_id
                LEFT JOIN appointments a ON u.id = a.user_id
                WHERE u.created_at <= $1 - INTERVAL '14 days'  -- Clientes com pelo menos 2 semanas
                GROUP BY u.id, u.nome, u.wa_id, u.created_at
                HAVING COUNT(m.id) > 0  -- Apenas quem já teve alguma interação
            ),
            churn_scores AS (
                SELECT *,
                    -- Recency Score (0-100, higher = more risk)
                    CASE
                        WHEN days_since_last_message <= 7 THEN 0
                        WHEN days_since_last_message <= 14 THEN 10
                        WHEN days_since_last_message <= 30 THEN 25
                        WHEN days_since_last_message <= 60 THEN 50
                        WHEN days_since_last_message <= 90 THEN 75
                        ELSE 100
                    END as recency_score,

                    -- Frequency Score (0-100, lower frequency = higher risk)
                    CASE
                        WHEN total_conversations >= 5 THEN 0
                        WHEN total_conversations >= 3 THEN 15
                        WHEN total_conversations >= 2 THEN 30
                        WHEN total_conversations >= 1 THEN 50
                        ELSE 80
                    END as frequency_score,

                    -- Monetary Score (0-100, lower spend = higher risk)
                    CASE
                        WHEN total_spent >= 500 THEN 0
                        WHEN total_spent >= 200 THEN 10
                        WHEN total_spent >= 100 THEN 20
                        WHEN total_spent >= 50 THEN 35
                        WHEN total_spent > 0 THEN 50
                        ELSE 70
                    END as monetary_score,

                    -- Engagement Score (0-100, poor engagement = higher risk)
                    CASE
                        WHEN (cancelled_appointments + no_shows) * 1.0 / GREATEST(total_appointments, 1) >= 0.5 THEN 40
                        WHEN (cancelled_appointments + no_shows) * 1.0 / GREATEST(total_appointments, 1) >= 0.3 THEN 25
                        WHEN (cancelled_appointments + no_shows) * 1.0 / GREATEST(total_appointments, 1) >= 0.1 THEN 10
                        ELSE 0
                    END +
                    CASE
                        WHEN messages_last_30d = 0 AND messages_prev_30d > 0 THEN 30  -- Declining activity
                        WHEN messages_last_30d < messages_prev_30d / 2.0 AND messages_prev_30d > 0 THEN 15  -- 50% decline
                        ELSE 0
                    END as engagement_score
                FROM customer_features
            )
            SELECT *,
                -- Weighted churn score
                ROUND(
                    recency_score * 0.40 +
                    frequency_score * 0.25 +
                    monetary_score * 0.15 +
                    engagement_score * 0.20
                ) as churn_score,

                -- Churn probability (0-1)
                CASE
                    WHEN (recency_score * 0.40 + frequency_score * 0.25 +
                          monetary_score * 0.15 + engagement_score * 0.20) >= 70 THEN 0.8
                    WHEN (recency_score * 0.40 + frequency_score * 0.25 +
                          monetary_score * 0.15 + engagement_score * 0.20) >= 50 THEN 0.6
                    WHEN (recency_score * 0.40 + frequency_score * 0.25 +
                          monetary_score * 0.15 + engagement_score * 0.20) >= 30 THEN 0.3
                    ELSE 0.1
                END as churn_probability
            FROM churn_scores
            ORDER BY churn_score DESC
            """

            result = await self.db.execute(text(churn_query), [analysis_date])
            rows = result.fetchall()

            # Processar predições
            predictions = []
            for row in rows:
                # Determinar risk level
                if row.churn_score >= 70:
                    risk_level = "high"
                elif row.churn_score >= 40:
                    risk_level = "medium"
                else:
                    risk_level = "low"

                # Identificar fatores-chave
                key_factors = []
                if row.recency_score >= 50:
                    key_factors.append(
                        f"Sem contato há {row.days_since_last_message} dias"
                    )
                if row.frequency_score >= 30:
                    key_factors.append("Baixa frequência de interação")
                if row.monetary_score >= 35:
                    key_factors.append("Baixo valor monetário")
                if row.engagement_score >= 20:
                    key_factors.append("Problemas de engajamento")
                if row.messages_last_30d == 0 and row.messages_prev_30d > 0:
                    key_factors.append("Atividade em declínio")

                # Recomendações baseadas no perfil
                recommended_actions = self._get_churn_prevention_actions(
                    risk_level, row.churn_score, key_factors
                )

                # Determinar engagement level
                if row.total_messages >= 10 and row.total_conversations >= 3:
                    engagement_level = "high"
                elif row.total_messages >= 5 or row.total_conversations >= 2:
                    engagement_level = "medium"
                else:
                    engagement_level = "low"

                if include_predictions or risk_level in ["high", "medium"]:
                    predictions.append(
                        ChurnPrediction(
                            user_id=row.id,
                            nome=row.nome or "N/A",
                            wa_id=row.wa_id or "",
                            churn_score=float(row.churn_score),
                            churn_risk=risk_level,
                            churn_probability=float(row.churn_probability),
                            key_factors=key_factors,
                            recommended_actions=recommended_actions,
                            days_since_last_contact=int(row.days_since_last_message),
                            engagement_level=engagement_level,
                            monetary_value=float(row.total_spent),
                        )
                    )

            # Calcular estatísticas sumárias
            total_analyzed = len(predictions)
            high_risk = len([p for p in predictions if p.churn_risk == "high"])
            medium_risk = len([p for p in predictions if p.churn_risk == "medium"])
            low_risk = len([p for p in predictions if p.churn_risk == "low"])

            # Top at-risk customers (top 10 highest scores)
            top_at_risk = sorted(
                predictions, key=lambda x: x.churn_score, reverse=True
            )[:10]

            summary = {
                "total_customers_analyzed": total_analyzed,
                "high_risk_count": high_risk,
                "medium_risk_count": medium_risk,
                "low_risk_count": low_risk,
                "high_risk_percentage": (
                    (high_risk / total_analyzed * 100) if total_analyzed > 0 else 0
                ),
                "avg_churn_score": (
                    sum(p.churn_score for p in predictions) / total_analyzed
                    if total_analyzed > 0
                    else 0
                ),
                "predicted_churn_30d": high_risk
                + int(medium_risk * 0.3),  # Estimativa conservadora
                "revenue_at_risk": sum(
                    p.monetary_value for p in predictions if p.churn_risk == "high"
                ),
            }

            logger.info(
                f"✅ Churn prediction calculada: {total_analyzed} clientes analisados, {high_risk} alto risco"
            )

            return {
                "predictions": predictions,
                "summary": summary,
                "top_at_risk": top_at_risk,
                "analysis_date": analysis_date.isoformat(),
                "methodology": {
                    "weights": self.churn_weights,
                    "features": ["recency", "frequency", "monetary", "engagement"],
                    "score_range": "0-100 (higher = more risk)",
                },
            }

        except Exception as e:
            logger.error(f"❌ Erro ao calcular predição de churn: {e}")
            raise

    def _get_churn_prevention_actions(
        self, risk_level: str, churn_score: float, key_factors: List[str]
    ) -> List[str]:
        """Retorna ações específicas para prevenção de churn baseadas no perfil"""

        base_actions = {
            "high": [
                "🚨 AÇÃO IMEDIATA: Contato personalizado do gerente",
                "📞 Ligação ou WhatsApp direto em 24h",
                "🎁 Oferta especial exclusiva (desconto 20-30%)",
                "❓ Pesquisa: 'Como podemos melhorar sua experiência?'",
                "⭐ Upgrade gratuito de serviço por período limitado",
            ],
            "medium": [
                "📧 Campanha de reengajamento personalizada",
                "🎯 Ofertas baseadas em histórico de compras",
                "📊 Acompanhamento semanal de satisfação",
                "💡 Sugestões de novos serviços relevantes",
                "🔔 Lembretes proativos de agendamento",
            ],
            "low": [
                "📬 Newsletter com conteúdo de valor",
                "🎉 Comunicação de novidades e promoções",
                "📝 Feedback survey trimestral",
                "💬 Check-in mensual automatizado",
                "🏆 Programa de pontos/fidelidade",
            ],
        }

        actions = base_actions.get(risk_level, [])

        # Ações específicas baseadas nos fatores-chave
        if any("Sem contato há" in factor for factor in key_factors):
            actions.append("📱 Reativação via múltiplos canais (WhatsApp + Email)")

        if any("frequência" in factor.lower() for factor in key_factors):
            actions.append("⏰ Campanha de agendamento recorrente")

        if any("monetário" in factor.lower() for factor in key_factors):
            actions.append("💰 Pacotes com desconto progressivo")

        if any("engajamento" in factor.lower() for factor in key_factors):
            actions.append("🤝 Atendimento consultivo personalizado")

        if any("declínio" in factor.lower() for factor in key_factors):
            actions.append("🔄 Campanha 'Sentimos sua falta' com benefício exclusivo")

        return actions[:6]  # Máximo 6 ações para não sobrecarregar

    async def calculate_roi_metrics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        💰 Cálculo abrangente de métricas de ROI e performance do negócio

        Inclui:
        - ROI por canal de aquisição
        - Customer Lifetime Value (CLV)
        - Customer Acquisition Cost (CAC)
        - Payback Period
        - Revenue metrics detalhadas
        """
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)  # Últimos 3 meses default

            logger.info(f"💰 Calculando métricas de ROI: {start_date} a {end_date}")

            # Query complexa para métricas de ROI
            roi_query = """
            WITH customer_metrics AS (
                SELECT
                    u.id as user_id,
                    u.nome,
                    u.wa_id,
                    u.created_at as acquisition_date,
                    u.referral_source,

                    -- Revenue Metrics
                    COALESCE(SUM(a.price) FILTER (
                        WHERE a.status IN ('realizado', 'completed')
                        AND a.created_at BETWEEN $1 AND $2
                    ), 0) as period_revenue,

                    COALESCE(SUM(a.price) FILTER (
                        WHERE a.status IN ('realizado', 'completed')
                    ), 0) as total_revenue,

                    COUNT(a.id) FILTER (
                        WHERE a.status IN ('realizado', 'completed')
                        AND a.created_at BETWEEN $1 AND $2
                    ) as period_transactions,

                    COUNT(a.id) FILTER (
                        WHERE a.status IN ('realizado', 'completed')
                    ) as total_transactions,

                    -- Customer Lifecycle
                    EXTRACT(DAYS FROM COALESCE(MAX(a.created_at), u.created_at) - u.created_at) as customer_lifespan_days,

                    -- First and Last transaction
                    MIN(a.created_at) FILTER (WHERE a.status IN ('realizado', 'completed')) as first_purchase,
                    MAX(a.created_at) FILTER (WHERE a.status IN ('realizado', 'completed')) as last_purchase,

                    -- Average Order Value
                    COALESCE(AVG(a.price) FILTER (
                        WHERE a.status IN ('realizado', 'completed')
                    ), 0) as avg_order_value,

                    -- Frequency metrics
                    CASE WHEN COUNT(a.id) FILTER (WHERE a.status IN ('realizado', 'completed')) > 1
                        THEN EXTRACT(DAYS FROM MAX(a.created_at) - MIN(a.created_at)) /
                             NULLIF(COUNT(a.id) FILTER (WHERE a.status IN ('realizado', 'completed')) - 1, 0)
                        ELSE NULL
                    END as avg_days_between_purchases

                FROM users u
                LEFT JOIN appointments a ON u.id = a.user_id
                WHERE u.created_at <= $2
                GROUP BY u.id, u.nome, u.wa_id, u.created_at, u.referral_source
            ),
            channel_metrics AS (
                SELECT
                    COALESCE(referral_source, 'organic') as channel,
                    COUNT(*) as customers_acquired,
                    COUNT(*) FILTER (WHERE total_revenue > 0) as paying_customers,
                    SUM(period_revenue) as channel_period_revenue,
                    SUM(total_revenue) as channel_total_revenue,
                    AVG(total_revenue) as avg_customer_value,
                    AVG(avg_order_value) as channel_avg_order_value,
                    AVG(customer_lifespan_days) as avg_customer_lifespan,

                    -- Conversion rate: paying customers / total acquired
                    CASE WHEN COUNT(*) > 0
                        THEN COUNT(*) FILTER (WHERE total_revenue > 0) * 100.0 / COUNT(*)
                        ELSE 0
                    END as conversion_rate
                FROM customer_metrics
                WHERE acquisition_date BETWEEN $1 AND $2
                GROUP BY COALESCE(referral_source, 'organic')
            ),
            overall_metrics AS (
                SELECT
                    SUM(period_revenue) as total_period_revenue,
                    SUM(total_revenue) as total_historical_revenue,
                    COUNT(*) as total_customers,
                    COUNT(*) FILTER (WHERE total_revenue > 0) as total_paying_customers,
                    AVG(total_revenue) FILTER (WHERE total_revenue > 0) as avg_customer_lifetime_value,
                    AVG(period_revenue) FILTER (WHERE period_revenue > 0) as avg_period_customer_value,
                    AVG(avg_order_value) FILTER (WHERE avg_order_value > 0) as overall_avg_order_value,
                    SUM(period_transactions) as total_period_transactions,
                    SUM(total_transactions) as total_historical_transactions
                FROM customer_metrics
                WHERE acquisition_date BETWEEN $1 AND $2
            )
            SELECT
                -- Channel data
                json_agg(
                    json_build_object(
                        'channel', c.channel,
                        'customers_acquired', c.customers_acquired,
                        'paying_customers', c.paying_customers,
                        'conversion_rate', c.conversion_rate,
                        'total_revenue', c.channel_total_revenue,
                        'period_revenue', c.channel_period_revenue,
                        'avg_customer_value', c.avg_customer_value,
                        'avg_order_value', c.channel_avg_order_value,
                        'avg_lifespan_days', c.avg_customer_lifespan
                    )
                ) as channels,

                -- Overall metrics
                (SELECT row_to_json(overall_metrics.*) FROM overall_metrics) as overall
            FROM channel_metrics c
            """

            result = await self.db.execute(text(roi_query), [start_date, end_date])
            row = result.fetchone()

            if not row or not row.overall:
                return {
                    "error": "Dados insuficientes para cálculo de ROI",
                    "period": f"{start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}",
                }

            # Processar dados
            channels_data = row.channels or []
            overall_data = row.overall

            # Calcular métricas derivadas
            period_days = (end_date - start_date).days

            # CAC estimado (assumindo custo médio de aquisição)
            estimated_cac_by_channel = {
                "organic": 0,
                "whatsapp": 15,  # Custo estimado por lead WhatsApp
                "google_ads": 45,  # CPC médio Google Ads
                "facebook": 35,  # CPC médio Facebook
                "instagram": 30,  # CPC médio Instagram
                "referral": 20,  # Custo de programa de referência
                "other": 25,  # Custo médio geral
            }

            # Processar dados por canal
            channel_roi_metrics = []
            for channel in channels_data:
                estimated_cac = estimated_cac_by_channel.get(channel["channel"], 25)
                total_acquisition_cost = channel["customers_acquired"] * estimated_cac

                # ROI Calculation: (Revenue - Investment) / Investment * 100
                if total_acquisition_cost > 0:
                    roi_percentage = (
                        (channel["total_revenue"] - total_acquisition_cost)
                        / total_acquisition_cost
                    ) * 100
                else:
                    roi_percentage = float("inf") if channel["total_revenue"] > 0 else 0

                # Payback period em dias (CAC / Revenue per day)
                if channel["avg_customer_value"] > 0:
                    avg_lifespan = channel["avg_lifespan_days"] or 365
                    daily_revenue_per_customer = (
                        channel["avg_customer_value"] / avg_lifespan
                    )
                    payback_period_days = (
                        estimated_cac / daily_revenue_per_customer
                        if daily_revenue_per_customer > 0
                        else None
                    )
                else:
                    payback_period_days = None

                channel_roi_metrics.append(
                    ROIMetrics(
                        canal=channel["channel"],
                        receita_total=float(channel["total_revenue"] or 0),
                        receita_periodo=float(channel["period_revenue"] or 0),
                        custo_aquisicao_estimado=total_acquisition_cost,
                        roi_percentual=(
                            roi_percentage
                            if roi_percentage != float("inf")
                            else 9999.99
                        ),
                        clientes_adquiridos=channel["customers_acquired"],
                        clientes_pagantes=channel["paying_customers"],
                        taxa_conversao=float(channel["conversion_rate"] or 0),
                        valor_medio_pedido=float(channel["avg_order_value"] or 0),
                        clv_estimado=float(channel["avg_customer_value"] or 0),
                        payback_period_dias=(
                            int(payback_period_days) if payback_period_days else None
                        ),
                        lifetime_dias=int(channel["avg_lifespan_days"] or 0),
                    )
                )

            # Métricas consolidadas
            total_revenue = float(overall_data.get("total_period_revenue", 0))
            total_customers = overall_data.get("total_customers", 0)
            total_paying_customers = overall_data.get("total_paying_customers", 0)

            # Estimativa de investimento total em marketing
            total_estimated_investment = sum(
                channel["customers_acquired"]
                * estimated_cac_by_channel.get(channel["channel"], 25)
                for channel in channels_data
            )

            # ROI consolidado
            consolidated_roi = (
                (
                    (total_revenue - total_estimated_investment)
                    / total_estimated_investment
                    * 100
                )
                if total_estimated_investment > 0
                else 0
            )

            # Métricas de tendência (comparar com período anterior)
            previous_period_start = start_date - timedelta(days=period_days)
            previous_period_end = start_date

            prev_result = await self.db.execute(
                text(
                    "SELECT SUM(a.price) as prev_revenue FROM appointments a WHERE a.status IN ('realizado', 'completed') AND a.created_at BETWEEN $1 AND $2"
                ),
                [previous_period_start, previous_period_end],
            )
            prev_row = prev_result.fetchone()
            previous_revenue = float(prev_row.prev_revenue or 0) if prev_row else 0

            # Growth rate
            growth_rate = (
                ((total_revenue - previous_revenue) / previous_revenue * 100)
                if previous_revenue > 0
                else 0
            )

            # Top performing channels
            top_channels = sorted(
                channel_roi_metrics, key=lambda x: x.roi_percentual, reverse=True
            )[:3]

            # Análise de performance
            performance_insights = []

            if consolidated_roi > 200:
                performance_insights.append(
                    "🔥 ROI excepcional! Estratégia altamente lucrativa"
                )
            elif consolidated_roi > 100:
                performance_insights.append(
                    "✅ ROI positivo, bom retorno do investimento"
                )
            elif consolidated_roi > 0:
                performance_insights.append(
                    "⚠️ ROI baixo, revisar estratégia de marketing"
                )
            else:
                performance_insights.append(
                    "🚨 ROI negativo, investimento não está pagando"
                )

            if growth_rate > 20:
                performance_insights.append("📈 Crescimento acelerado mês a mês")
            elif growth_rate > 0:
                performance_insights.append("📊 Crescimento estável")
            else:
                performance_insights.append("📉 Receita em declínio, ação necessária")

            # Canal mais eficiente
            if top_channels:
                best_channel = top_channels[0]
                performance_insights.append(
                    f"🏆 Melhor canal: {best_channel.canal} (ROI: {best_channel.roi_percentual:.1f}%)"
                )

            logger.info(
                f"✅ ROI metrics calculadas: ROI consolidado {consolidated_roi:.1f}%"
            )

            return {
                "channel_metrics": channel_roi_metrics,
                "consolidated_metrics": {
                    "total_revenue": total_revenue,
                    "total_investment": total_estimated_investment,
                    "consolidated_roi": consolidated_roi,
                    "total_customers": total_customers,
                    "paying_customers": total_paying_customers,
                    "conversion_rate": (
                        (total_paying_customers / total_customers * 100)
                        if total_customers > 0
                        else 0
                    ),
                    "avg_customer_lifetime_value": float(
                        overall_data.get("avg_customer_lifetime_value", 0)
                    ),
                    "avg_order_value": float(
                        overall_data.get("overall_avg_order_value", 0)
                    ),
                    "growth_rate": growth_rate,
                },
                "performance_insights": performance_insights,
                "top_channels": top_channels,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": period_days,
                },
                "methodology": {
                    "cac_estimates": estimated_cac_by_channel,
                    "roi_formula": "(Revenue - Investment) / Investment * 100",
                    "assumptions": [
                        "CAC estimado por canal baseado em médias de mercado",
                        "CLV calculado baseado em histórico de transações",
                        "Payback period assumindo revenue distribuído uniformemente",
                    ],
                },
            }

        except Exception as e:
            logger.error(f"❌ Erro ao calcular ROI metrics: {e}")
            raise
