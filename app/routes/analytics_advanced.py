"""
🚀 ANALYTICS AVANÇADAS - BUSINESS INTELLIGENCE
Endpoints para analytics avançadas incluindo:
- Conversion Funnel Analysis
- Customer Segmentation (RFM)
- Churn Prediction
- ROI Metrics & Performance
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.middleware import require_admin
from ..database import get_db
from ..services.analytics_engine_advanced import AdvancedAnalyticsEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics/advanced", tags=["Analytics Avançadas"])


@router.get("/conversion-funnel")
async def get_conversion_funnel_analysis(
    db: AsyncSession = Depends(get_db),
    start_date: Optional[str] = Query(None, description="Data início (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data fim (YYYY-MM-DD)"),
    custom_stages: Optional[List[str]] = Query(
        None, description="Estágios customizados do funil"
    ),
    include_cohort: bool = Query(True, description="Incluir análise de coorte"),
    segment_by: Optional[str] = Query(None, enum=["channel", "month", "week"]),
    current_admin: dict = Depends(require_admin),
):
    """
    🔍 **ANÁLISE DETALHADA DO FUNIL DE CONVERSÃO**

    Retorna análise completa do funil de conversão com:
    - Taxa de conversão entre estágios
    - Identificação de gargalos
    - Análise temporal de coortes
    - Segmentação por canal ou período
    - Métricas de performance detalhadas

    **Casos de uso:**
    - Identificar onde clientes abandonam o processo
    - Otimizar taxa de conversão
    - Comparar performance entre canais
    - Análise de tendências temporais
    """
    try:
        logger.info(
            f"🔍 Admin {current_admin.get('username', 'unknown')} solicitou análise do funil"
        )

        analytics_engine = AdvancedAnalyticsEngine(db)

        # Parse dates se fornecidas
        parsed_start = datetime.fromisoformat(start_date) if start_date else None
        parsed_end = datetime.fromisoformat(end_date) if end_date else None

        result = await analytics_engine.calculate_detailed_conversion_funnel(
            start_date=parsed_start,
            end_date=parsed_end,
            custom_stages=custom_stages,
            include_cohort_analysis=include_cohort,
            segment_by=segment_by,
        )

        logger.info(
            f"✅ Funil de conversão calculado: {len(result.get('stages', []))} estágios"
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "message": "Análise de funil de conversão concluída com sucesso",
            },
        )

    except Exception as e:
        logger.error(f"❌ Erro na análise do funil de conversão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/customer-segmentation")
async def get_customer_segmentation(
    db: AsyncSession = Depends(get_db),
    analysis_date: Optional[str] = Query(
        None, description="Data da análise (YYYY-MM-DD)"
    ),
    include_actions: bool = Query(True, description="Incluir ações recomendadas"),
    min_transactions: int = Query(1, description="Mínimo de transações para análise"),
    segment_details: bool = Query(True, description="Incluir detalhes dos segmentos"),
    current_admin: dict = Depends(require_admin),
):
    """
    👥 **SEGMENTAÇÃO AVANÇADA DE CLIENTES (RFM)**

    Análise RFM completa com:
    - Segmentação em 8 categorias estratégicas
    - Scoring de Recency, Frequency, Monetary
    - Ações recomendadas por segmento
    - Características detalhadas de cada grupo
    - Insights para estratégias de marketing

    **Segmentos identificados:**
    - VIP Champions: Clientes mais valiosos
    - Loyal Customers: Base leal e consistente
    - Potential Loyalists: Alta oportunidade
    - New Customers: Recém-chegados
    - At Risk: Precisam de atenção
    - Cannot Lose Them: Retenção crítica
    - Lost Customers: Reativação necessária
    """
    try:
        logger.info(
            f"👥 Admin {current_admin.get('username', 'unknown')} solicitou segmentação RFM"
        )

        analytics_engine = AdvancedAnalyticsEngine(db)

        # Parse date se fornecida
        parsed_date = datetime.fromisoformat(analysis_date) if analysis_date else None

        result = await analytics_engine.calculate_rfm_segmentation(
            analysis_date=parsed_date,
            include_recommendations=include_actions,
            min_transactions=min_transactions,
        )

        segments_count = len(result) if isinstance(result, list) else 0
        logger.info(f"✅ Segmentação RFM calculada: {segments_count} segmentos")

        # Preparar resposta estruturada
        response_data = {
            "segments": result,
            "summary": {
                "total_segments": segments_count,
                "analysis_date": (parsed_date or datetime.utcnow()).isoformat(),
                "methodology": "RFM (Recency, Frequency, Monetary) Analysis",
            },
        }

        if segment_details:
            # Adicionar estatísticas por tipo de segmento
            segment_stats = {}
            for segment in result:
                seg_type = segment.segment_type
                if seg_type not in segment_stats:
                    segment_stats[seg_type] = {"count": 0, "total_value": 0.0}
                segment_stats[seg_type]["count"] += 1
                segment_stats[seg_type]["total_value"] += segment.total_spent

            response_data["segment_statistics"] = segment_stats

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": response_data,
                "message": f"Segmentação RFM concluída: {segments_count} clientes analisados",
            },
        )

    except Exception as e:
        logger.error(f"❌ Erro na segmentação de clientes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/churn-prediction")
async def get_churn_prediction(
    db: AsyncSession = Depends(get_db),
    analysis_date: Optional[str] = Query(
        None, description="Data da análise (YYYY-MM-DD)"
    ),
    include_low_risk: bool = Query(
        False, description="Incluir clientes de baixo risco"
    ),
    risk_threshold: str = Query(
        "medium", enum=["low", "medium", "high"], description="Filtro mínimo de risco"
    ),
    current_admin: dict = Depends(require_admin),
):
    """
    🔮 **PREDIÇÃO DE CHURN INTELIGENTE**

    Sistema avançado de predição de churn com:
    - Score de risco 0-100 usando múltiplos fatores
    - Probabilidade de churn calculada
    - Identificação de fatores-chave de risco
    - Ações específicas de prevenção
    - Análise de revenue em risco

    **Algoritmo considera:**
    - Recency: Tempo desde último contato (peso 40%)
    - Frequency: Frequência de interações (peso 25%)
    - Monetary: Valor monetário (peso 15%)
    - Engagement: Padrões comportamentais (peso 20%)

    **Níveis de risco:**
    - Alto (70-100): Ação imediata necessária
    - Médio (40-69): Monitoramento próximo
    - Baixo (0-39): Acompanhamento preventivo
    """
    try:
        logger.info(
            f"🔮 Admin {current_admin.get('username', 'unknown')} solicitou predição de churn"
        )

        analytics_engine = AdvancedAnalyticsEngine(db)

        # Parse date se fornecida
        parsed_date = datetime.fromisoformat(analysis_date) if analysis_date else None

        result = await analytics_engine.calculate_churn_prediction(
            analysis_date=parsed_date,
            include_predictions=include_low_risk or risk_threshold == "low",
        )

        # Filtrar por threshold se necessário
        if not include_low_risk and risk_threshold != "low":
            filtered_predictions = []
            for pred in result.get("predictions", []):
                if risk_threshold == "high" and pred.churn_risk == "high":
                    filtered_predictions.append(pred)
                elif risk_threshold == "medium" and pred.churn_risk in [
                    "high",
                    "medium",
                ]:
                    filtered_predictions.append(pred)
                else:
                    filtered_predictions.append(pred)

            result["predictions"] = filtered_predictions
            result["filtered_by"] = risk_threshold

        prediction_count = len(result.get("predictions", []))
        high_risk_count = result.get("summary", {}).get("high_risk_count", 0)

        logger.info(
            f"✅ Predição de churn calculada: {prediction_count} clientes, {high_risk_count} alto risco"
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "message": f"Predição de churn concluída: {high_risk_count} clientes em alto risco",
            },
        )

    except Exception as e:
        logger.error(f"❌ Erro na predição de churn: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/roi-metrics")
async def get_roi_metrics(
    db: AsyncSession = Depends(get_db),
    start_date: Optional[str] = Query(None, description="Data início (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data fim (YYYY-MM-DD)"),
    include_projections: bool = Query(True, description="Incluir projeções futuras"),
    channel_filter: Optional[List[str]] = Query(
        None, description="Filtrar canais específicos"
    ),
    current_admin: dict = Depends(require_admin),
):
    """
    � **MÉTRICAS AVANÇADAS DE ROI & PERFORMANCE**

    Dashboard completo de ROI com:
    - ROI por canal de aquisição
    - Customer Lifetime Value (CLV)
    - Customer Acquisition Cost (CAC)
    - Payback Period por canal
    - Análise de tendências de crescimento
    - Revenue metrics detalhadas

    **Métricas calculadas:**
    - ROI = (Revenue - Investment) / Investment × 100
    - CLV baseado em histórico transacional
    - CAC estimado por canal de marketing
    - Taxa de conversão por funil
    - Growth rate período a período

    **Insights inclusos:**
    - Canais mais lucrativos
    - Tendências de performance
    - Oportunidades de otimização
    - Alertas de performance
    """
    try:
        logger.info(
            f"💰 Admin {current_admin.get('username', 'unknown')} solicitou métricas ROI"
        )

        analytics_engine = AdvancedAnalyticsEngine(db)

        # Parse dates se fornecidas
        parsed_start = datetime.fromisoformat(start_date) if start_date else None
        parsed_end = datetime.fromisoformat(end_date) if end_date else None

        result = await analytics_engine.calculate_roi_metrics(
            start_date=parsed_start, end_date=parsed_end
        )

        # Filtrar canais se especificado
        if channel_filter:
            filtered_channels = [
                channel
                for channel in result.get("channel_metrics", [])
                if channel.canal in channel_filter
            ]
            result["channel_metrics"] = filtered_channels
            result["filtered_channels"] = channel_filter

        # Adicionar projeções se solicitado
        if include_projections and result.get("consolidated_metrics"):
            consolidated = result["consolidated_metrics"]
            growth_rate = consolidated.get("growth_rate", 0)

            # Projeção simples baseada no growth rate
            current_revenue = consolidated.get("total_revenue", 0)
            projected_30d = (
                current_revenue * (1 + growth_rate / 100) * (30 / 30)
            )  # Próximo mês
            projected_90d = (
                current_revenue * (1 + growth_rate / 100) * (90 / 30)
            )  # Próximos 3 meses

            result["projections"] = {
                "next_30_days_revenue": projected_30d,
                "next_90_days_revenue": projected_90d,
                "growth_rate_used": growth_rate,
                "confidence": "medium" if abs(growth_rate) < 50 else "low",
            }

        total_roi = result.get("consolidated_metrics", {}).get("consolidated_roi", 0)

        logger.info(f"✅ ROI metrics calculadas: ROI consolidado {total_roi:.1f}%")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "message": f"Análise de ROI concluída - ROI consolidado: {total_roi:.1f}%",
            },
        )

    except Exception as e:
        logger.error(f"❌ Erro nas métricas de ROI: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/dashboard-summary")
async def get_analytics_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    period_days: int = Query(30, description="Período em dias para análise"),
    current_admin: dict = Depends(require_admin),
):
    """
    📊 **DASHBOARD EXECUTIVO - RESUMO ANALYTICS**

    Visão consolidada das principais métricas:
    - KPIs principais
    - Alertas críticos
    - Tendências período
    - Top insights
    - Ações recomendadas
    """
    try:
        logger.info(
            f"� Admin {current_admin.get('username', 'unknown')} solicitou dashboard summary"
        )

        analytics_engine = AdvancedAnalyticsEngine(db)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # Executar análises em paralelo (simplificado)
        try:
            # ROI metrics (principais)
            roi_data = await analytics_engine.calculate_roi_metrics(
                start_date, end_date
            )

            # Churn prediction (apenas alto risco)
            churn_data = await analytics_engine.calculate_churn_prediction(
                analysis_date=end_date, include_predictions=False  # Apenas summary
            )

            # Segmentação (contagem básica)
            segments_data = await analytics_engine.calculate_rfm_segmentation(
                analysis_date=end_date, include_recommendations=False
            )

        except Exception as inner_e:
            logger.warning(f"⚠️ Erro parcial nas análises: {inner_e}")
            # Fallback com dados básicos
            roi_data = {
                "consolidated_metrics": {"consolidated_roi": 0, "total_revenue": 0}
            }
            churn_data = {
                "summary": {"high_risk_count": 0, "total_customers_analyzed": 0}
            }
            segments_data = []

        # Compilar dashboard
        consolidated_roi = roi_data.get("consolidated_metrics", {}).get(
            "consolidated_roi", 0
        )
        total_revenue = roi_data.get("consolidated_metrics", {}).get("total_revenue", 0)
        high_risk_customers = churn_data.get("summary", {}).get("high_risk_count", 0)
        total_customers = churn_data.get("summary", {}).get(
            "total_customers_analyzed", 0
        )
        total_segments = len(segments_data) if isinstance(segments_data, list) else 0

        # Alertas automáticos
        alerts = []
        if consolidated_roi < 0:
            alerts.append("🚨 ROI NEGATIVO - Revisar estratégia de marketing urgente")
        if high_risk_customers > 0:
            alerts.append(f"⚠️ {high_risk_customers} clientes em alto risco de churn")
        if total_revenue == 0:
            alerts.append("📉 Sem receita no período analisado")

        # Top insights
        insights = []
        if consolidated_roi > 100:
            insights.append(
                f"✅ ROI excelente de {consolidated_roi:.1f}% - Estratégia eficaz"
            )
        if high_risk_customers == 0:
            insights.append(
                "🎯 Nenhum cliente em alto risco de churn - Retenção saudável"
            )
        if total_segments > 20:
            insights.append(
                f"📊 Base diversificada com {total_segments} segmentos ativos"
            )

        dashboard_data = {
            "period": {
                "days": period_days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "key_metrics": {
                "consolidated_roi": consolidated_roi,
                "total_revenue": total_revenue,
                "high_risk_customers": high_risk_customers,
                "total_customers": total_customers,
                "active_segments": total_segments,
            },
            "alerts": alerts,
            "insights": insights,
            "quick_actions": [
                "Ver análise detalhada de churn" if high_risk_customers > 0 else None,
                "Analisar funil de conversão" if total_revenue > 0 else None,
                "Revisar segmentação RFM" if total_segments > 0 else None,
            ],
            "last_updated": datetime.utcnow().isoformat(),
        }

        # Remover ações None
        dashboard_data["quick_actions"] = [
            action for action in dashboard_data["quick_actions"] if action
        ]

        logger.info(
            f"✅ Dashboard summary gerado: {len(alerts)} alertas, {len(insights)} insights"
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": dashboard_data,
                "message": "Dashboard executivo atualizado com sucesso",
            },
        )

    except Exception as e:
        logger.error(f"❌ Erro no dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
