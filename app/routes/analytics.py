"""
Analytics Routes - Endpoints para dashboard de business intelligence
Fornece APIs REST para análises avançadas do WhatsApp Agent
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.middleware import get_current_user  # 🔧 Usar middleware unificado
from app.services.analytics_engine import AdvancedAnalyticsEngine
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["Advanced Analytics"])

@router.get("/funnel")
async def get_conversion_funnel_analysis(
    start_date: Optional[datetime] = Query(
        default=None,
        description="Data início (ISO format). Default: 30 dias atrás"
    ),
    end_date: Optional[datetime] = Query(
        default=None,
        description="Data fim (ISO format). Default: hoje"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 🔧 Usar middleware
):
    """
    📊 Análise completa do funil de conversão
    
    Retorna:
    - Número de usuários em cada etapa do funil
    - Taxas de conversão entre etapas
    - Análise de drop-off
    - Recomendações de otimização
    """
    logger.info(f"🔍 User {current_user['user_id']} solicitou análise do funil")
    
    try:
        # Define período padrão se não fornecido
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Validar período
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="Data início deve ser anterior à data fim")
        
        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="Período máximo: 365 dias")
        
        analytics = AdvancedAnalyticsEngine(session)
        result = await analytics.get_conversion_funnel(start_date, end_date)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        logger.info(f"✅ Funil analisado: {result['conversion_rates']['overall_conversion']:.1f}% conversão")
        return {
            "status": "success",
            "data": result,
            "message": f"Funil analisado para período de {(end_date - start_date).days} dias"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na análise do funil: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/time-analysis")
async def get_time_based_analytics(
    days: int = Query(
        30, 
        le=365, 
        ge=1,
        description="Período em dias (1-365)"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 🔧 Usar middleware
):
    """
    🕐 Análise temporal detalhada de atividade
    
    Retorna:
    - Padrões por hora do dia
    - Atividade por dia da semana  
    - Tendências diárias
    - Insights e recomendações
    """
    logger.info(f"🕐 User {current_user['user_id']} solicitou análise temporal - {days} dias")
    
    try:
        analytics = AdvancedAnalyticsEngine(session)
        result = await analytics.get_time_based_analytics(days)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Estatísticas do resultado
        total_messages = sum(h.get("messages", 0) for h in result.get("hourly_patterns", []))
        peak_hour = max(result.get("hourly_patterns", []), key=lambda x: x.get("messages", 0), default={})
        
        logger.info(f"✅ Análise temporal concluída: {total_messages} mensagens, pico às {peak_hour.get('hour', 'N/A')}h")
        return {
            "status": "success",
            "data": result,
            "summary": {
                "total_messages_analyzed": total_messages,
                "peak_hour": peak_hour.get("hour", None),
                "analysis_period_days": days
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na análise temporal: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/customer-insights")
async def get_customer_insights_analysis(
    days: int = Query(
        30, 
        le=365, 
        ge=1,
        description="Período em dias para análise"
    ),
    include_detailed: bool = Query(
        False,
        description="Incluir detalhes completos dos clientes"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 🔧 Usar middleware
):
    """
    👥 Insights detalhados sobre base de clientes
    
    Retorna:
    - Clientes VIP (alto valor)
    - Clientes em churn (inativos)
    - Prospects de alto valor
    - Métricas de segmentação
    """
    logger.info(f"👥 User {current_user['user_id']} solicitou insights de clientes - {days} dias")
    
    try:
        analytics = AdvancedAnalyticsEngine(session)
        result = await analytics.get_customer_insights(days)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Remover dados sensíveis se não solicitado detalhamento
        if not include_detailed:
            for customer_list in ["vip_customers", "churned_customers", "high_value_prospects"]:
                for customer in result.get(customer_list, []):
                    if "phone" in customer:
                        # Mascarar telefone
                        phone = customer["phone"]
                        customer["phone"] = phone[:2] + "*" * (len(phone) - 4) + phone[-2:] if phone and len(phone) > 4 else "***"
        
        summary = result.get("customer_summary", {})
        logger.info(f"✅ Insights calculados: {summary.get('total_vip', 0)} VIPs, {summary.get('total_prospects', 0)} prospects")
        
        return {
            "status": "success",
            "data": result,
            "summary": {
                "total_segments_analyzed": 3,
                "total_customers": summary.get("total_vip", 0) + summary.get("total_churned", 0),
                "analysis_period_days": days,
                "data_privacy": "enabled" if not include_detailed else "disabled"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro nos insights de clientes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/business-metrics")
async def get_business_metrics_analysis(
    days: int = Query(
        30,
        le=365,
        ge=1, 
        description="Período em dias para análise"
    ),
    include_financial: bool = Query(
        True,
        description="Incluir métricas financeiras detalhadas"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 🔧 Usar middleware
):
    """
    💰 Métricas de negócio essenciais
    
    Retorna:
    - Revenue metrics (receita, AOV, etc.)
    - Customer metrics (CAC, LTV, etc.) 
    - Growth metrics (crescimento, tendências)
    - Efficiency metrics (ROI, conversão)
    """
    logger.info(f"💰 User {current_user['user_id']} solicitou métricas de negócio - {days} dias")
    
    try:
        analytics = AdvancedAnalyticsEngine(session)
        result = await analytics.get_business_metrics(days)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Filtrar métricas financeiras se solicitado
        if not include_financial:
            result["revenue_metrics"] = {
                k: v for k, v in result.get("revenue_metrics", {}).items() 
                if k not in ["total_revenue", "revenue_per_customer"]
            }
            result["customer_metrics"]["estimated_marketing_spend"] = "***"
        
        revenue = result.get("revenue_metrics", {}).get("total_revenue", 0)
        roi = result.get("efficiency_metrics", {}).get("roi_percentage", 0)
        
        logger.info(f"✅ Métricas calculadas: R$ {revenue:.2f} receita, {roi:.1f}% ROI")
        
        return {
            "status": "success", 
            "data": result,
            "summary": {
                "analysis_period_days": days,
                "revenue_analyzed": revenue if include_financial else "***",
                "roi_percentage": roi,
                "financial_details_included": include_financial
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro nas métricas de negócio: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    days: int = Query(
        7,
        le=30,
        ge=1,
        description="Período em dias (máx 30 para performance)"
    ),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 🔧 Usar middleware
):
    """
    🎯 Resumo executivo para dashboard principal
    
    Combina métricas essenciais de todas as análises em um endpoint otimizado
    """
    logger.info(f"🎯 User {current_user['user_id']} solicitou resumo do dashboard - {days} dias")
    
    try:
        analytics = AdvancedAnalyticsEngine(session)
        
        # Executar análises em paralelo (versões simplificadas)
        funnel_data = await analytics.get_conversion_funnel(
            datetime.now() - timedelta(days=days),
            datetime.now()
        )
        
        customer_data = await analytics.get_customer_insights(days)
        business_data = await analytics.get_business_metrics(days)
        
        # Compilar resumo executivo
        summary = {
            "period": {
                "days": days,
                "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
                "end_date": datetime.now().isoformat()
            },
            "key_metrics": {
                "overall_conversion_rate": funnel_data.get("conversion_rates", {}).get("overall_conversion", 0),
                "total_customers": customer_data.get("customer_summary", {}).get("total_vip", 0),
                "total_revenue": business_data.get("revenue_metrics", {}).get("total_revenue", 0),
                "roi_percentage": business_data.get("efficiency_metrics", {}).get("roi_percentage", 0)
            },
            "alerts": [],
            "quick_insights": [
                f"Taxa de conversão: {funnel_data.get('conversion_rates', {}).get('overall_conversion', 0):.1f}%",
                f"Clientes VIP: {customer_data.get('customer_summary', {}).get('total_vip', 0)}",
                f"ROI: {business_data.get('efficiency_metrics', {}).get('roi_percentage', 0):.1f}%"
            ]
        }
        
        # Adicionar alertas baseados em métricas
        conversion_rate = funnel_data.get("conversion_rates", {}).get("overall_conversion", 0)
        if conversion_rate < 5:
            summary["alerts"].append("⚠️ Taxa de conversão baixa - revisar estratégia")
        
        churn_rate = customer_data.get("customer_summary", {}).get("churn_rate", 0)
        if churn_rate > 20:
            summary["alerts"].append("⚠️ Taxa de churn elevada - focar retenção")
        
        logger.info(f"✅ Resumo gerado: {conversion_rate:.1f}% conversão, {len(summary['alerts'])} alertas")
        
        return {
            "status": "success",
            "data": summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no resumo do dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/export/{analysis_type}")
async def export_analytics_data(
    analysis_type: str,
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(30, le=365, ge=1),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # 🔧 Usar middleware
):
    """
    📥 Exportar dados de analytics em diferentes formatos
    
    Tipos disponíveis: funnel, time-analysis, customer-insights, business-metrics
    Formatos: json, csv
    """
    logger.info(f"📥 User {current_user['user_id']} exportando {analysis_type} - {format}")
    
    try:
        analytics = AdvancedAnalyticsEngine(session)
        
        # Executar análise baseada no tipo solicitado
        if analysis_type == "funnel":
            data = await analytics.get_conversion_funnel(
                datetime.now() - timedelta(days=days),
                datetime.now()
            )
        elif analysis_type == "time-analysis":
            data = await analytics.get_time_based_analytics(days)
        elif analysis_type == "customer-insights":
            data = await analytics.get_customer_insights(days)
        elif analysis_type == "business-metrics":
            data = await analytics.get_business_metrics(days)
        else:
            raise HTTPException(status_code=400, detail="Tipo de análise inválido")
        
        if "error" in data:
            raise HTTPException(status_code=500, detail=data["error"])
        
        # Para CSV, converter dados complexos em formato tabular
        if format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            
            if analysis_type == "funnel":
                writer = csv.writer(output)
                writer.writerow(["Etapa", "Quantidade", "Taxa_Conversao"])
                stages = data.get("funnel_stages", {})
                rates = data.get("conversion_rates", {})
                
                writer.writerow(["Primeiro Contato", stages.get("first_contact", 0), "100%"])
                writer.writerow(["Bot Response", stages.get("bot_response", 0), f"{rates.get('contact_to_response', 0):.1f}%"])
                writer.writerow(["Agendado", stages.get("scheduled", 0), f"{rates.get('contact_to_schedule', 0):.1f}%"])
                writer.writerow(["Confirmado", stages.get("confirmed", 0), f"{rates.get('schedule_to_confirm', 0):.1f}%"])
                writer.writerow(["Realizado", stages.get("completed", 0), f"{rates.get('confirm_to_complete', 0):.1f}%"])
            
            csv_content = output.getvalue()
            output.close()
            
            from fastapi.responses import Response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={analysis_type}_{days}days.csv"}
            )
        
        # Formato JSON (padrão)
        return {
            "status": "success",
            "analysis_type": analysis_type,
            "format": format,
            "period_days": days,
            "exported_at": datetime.now().isoformat(),
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na exportação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Health check específico para analytics
@router.get("/health")
async def analytics_health_check(
    session: AsyncSession = Depends(get_db)
):
    """🏥 Health check do sistema de analytics"""
    try:
        # Teste básico de conexão com banco
        from sqlalchemy import select, func
        result = await session.execute(select(func.now()))
        db_time = result.scalar()
        
        return {
            "status": "healthy",
            "service": "analytics-engine",
            "database": "connected",
            "server_time": datetime.now().isoformat(),
            "database_time": db_time.isoformat() if db_time else None,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"❌ Analytics health check failed: {e}")
        return {
            "status": "unhealthy", 
            "service": "analytics-engine",
            "error": str(e)
        }
                
