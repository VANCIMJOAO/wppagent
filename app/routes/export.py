"""
Export Routes - Endpoints para exportação de relatórios
Fornece download de CSV, Excel e PDF com autenticação admin
"""

import io
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import require_admin
from app.database import get_db
from app.services.analytics_engine import AdvancedAnalyticsEngine
from app.services.report_export_service import ReportExportService
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/export", tags=["Data Export"])


@router.get("/appointments/csv")
async def export_appointments_csv(
    start_date: datetime = Query(
        default_factory=lambda: datetime.now() - timedelta(days=30),
        description="Data inicial para filtrar agendamentos",
    ),
    end_date: datetime = Query(
        default_factory=datetime.now, description="Data final para filtrar agendamentos"
    ),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """
    📊 Exportar agendamentos para CSV

    Features:
    • Dados completos dos agendamentos
    • Filtros por período
    • Formato CSV compatível com Excel
    • Download automático
    """
    logger.info(f"🔄 Admin {current_admin.get('user_id')} exportando CSV agendamentos")

    try:
        # Validar datas
        if start_date >= end_date:
            raise HTTPException(
                status_code=400, detail="Data inicial deve ser anterior à data final"
            )

        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=400, detail="Período máximo permitido: 365 dias"
            )

        # Criar serviços
        analytics = AdvancedAnalyticsEngine(session)
        export_service = ReportExportService(analytics)

        # Gerar CSV
        csv_data, content_type = await export_service.export_appointments_report(
            format_type="csv",
            date_from=start_date.date(),
            date_to=end_date.date()
        )

        # Nome do arquivo com timestamp
        filename = f"agendamentos_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"

        logger.info(
            f"✅ CSV {filename} gerado para admin {current_admin.get('user_id')}"
        )

        return StreamingResponse(
            io.BytesIO(csv_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": content_type,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na exportação CSV: {e}")
        raise HTTPException(status_code=500, detail="Erro interno na exportação CSV")


@router.get("/analytics/excel")
async def export_analytics_excel(
    period_days: int = Query(
        30, ge=1, le=365, description="Número de dias para análise (máximo 365)"
    ),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """
    📈 Exportar analytics completas para Excel

    Features:
    • Múltiplas abas com diferentes análises
    • Gráficos e formatação profissional
    • Dados de funil, clientes VIP e temporal
    • Download automático
    """
    logger.info(
        f"🔄 Admin {current_admin.get('user_id')} exportando Excel analytics ({period_days} dias)"
    )

    try:
        # Criar serviços
        analytics = AdvancedAnalyticsEngine(session)
        export_service = ReportExportService(analytics)

        # Gerar Excel
        excel_data, content_type = await export_service.export_dashboard_report(
            format_type="excel",
            date_from=(datetime.now() - timedelta(days=period_days)).date(),
            date_to=datetime.now().date()
        )

        # Nome do arquivo com timestamp
        filename = f"analytics_{period_days}dias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        logger.info(
            f"✅ Excel {filename} gerado para admin {current_admin.get('user_id')}"
        )

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": content_type,
            },
        )

    except Exception as e:
        logger.error(f"❌ Erro na exportação Excel: {e}")
        raise HTTPException(status_code=500, detail="Erro interno na exportação Excel")


@router.get("/executive/pdf")
async def export_executive_pdf(
    period_days: int = Query(
        30, ge=1, le=365, description="Número de dias para análise (máximo 365)"
    ),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """
    📑 Exportar relatório executivo em PDF

    Features:
    • Layout profissional formatado
    • Métricas principais do negócio
    • Análise detalhada do funil
    • Pronto para apresentações
    """
    logger.info(
        f"🔄 Admin {current_admin.get('user_id')} exportando PDF executivo ({period_days} dias)"
    )

    try:
        # Criar serviços
        analytics = AdvancedAnalyticsEngine(session)
        export_service = ReportExportService(analytics)

        # Gerar PDF
        pdf_data, content_type = await export_service.export_dashboard_report(
            format_type="pdf",
            date_from=(datetime.now() - timedelta(days=period_days)).date(),
            date_to=datetime.now().date()
        )

        # Nome do arquivo com timestamp
        filename = f"relatorio_executivo_{period_days}dias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        logger.info(
            f"✅ PDF {filename} gerado para admin {current_admin.get('user_id')}"
        )

        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": content_type,
            },
        )

    except Exception as e:
        logger.error(f"❌ Erro na exportação PDF: {e}")
        raise HTTPException(status_code=500, detail="Erro interno na exportação PDF")


@router.get("/health")
async def export_health_check(current_admin: Dict = Depends(require_admin)):
    """
    🏥 Health check do sistema de exportação
    """
    try:
        return {
            "status": "healthy",
            "service": "export-service",
            "features": ["csv_appointments", "excel_analytics", "pdf_executive"],
            "formats_supported": ["CSV", "XLSX", "PDF"],
            "max_period_days": 365,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"❌ Export health check failed: {e}")
        return {"status": "unhealthy", "service": "export-service", "error": str(e)}
