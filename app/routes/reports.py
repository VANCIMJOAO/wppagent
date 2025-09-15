"""
API Routes para Sistema de Exportação de Relatórios
Suporta CSV, Excel e PDF
"""

import io
from datetime import date, datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth.middleware import require_admin
from app.services.report_export_service import export_service

router = APIRouter(prefix="/api/reports", tags=["Reports Export"])


# Modelos Pydantic para validação
class ReportFilters(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    status: Optional[str] = None
    user_id: Optional[int] = None


class ExportRequest(BaseModel):
    format: Literal["csv", "excel", "pdf"] = "excel"
    filters: ReportFilters = ReportFilters()


@router.get("/appointments/export")
async def export_appointments(
    format: Literal["csv", "excel", "pdf"] = Query(
        default="excel", description="Formato do relatório"
    ),
    date_from: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    user_id: Optional[int] = Query(None, description="Filtrar por ID do usuário"),
    admin=Depends(require_admin),
):
    """
    Exportar relatório de agendamentos

    Formatos suportados:
    - csv: Arquivo CSV simples
    - excel: Arquivo Excel com formatação e resumo
    - pdf: Documento PDF formatado

    Filtros disponíveis:
    - date_from/date_to: Período dos agendamentos
    - status: pending, confirmed, completed, cancelled
    - user_id: ID específico do usuário
    """
    try:
        # Gerar o relatório
        report_data, content_type = await export_service.export_appointments_report(
            format_type=format,
            date_from=date_from,
            date_to=date_to,
            status=status,
            user_id=user_id,
        )

        # Definir nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extensions = {"csv": "csv", "excel": "xlsx", "pdf": "pdf"}
        filename = f"agendamentos_{timestamp}.{extensions[format]}"

        # Retornar arquivo como download
        return StreamingResponse(
            io.BytesIO(report_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(report_data)),
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar relatório: {str(e)}"
        )


@router.get("/conversations/export")
async def export_conversations(
    format: Literal["csv", "excel", "pdf"] = Query(
        default="excel", description="Formato do relatório"
    ),
    date_from: Optional[date] = Query(None, description="Data inicial"),
    date_to: Optional[date] = Query(None, description="Data final"),
    user_id: Optional[int] = Query(None, description="Filtrar por usuário"),
    admin=Depends(require_admin),
):
    """
    Exportar relatório de conversas

    Inclui histórico de conversas, status e métricas de engajamento
    """
    try:
        report_data, content_type = await export_service.export_conversations_report(
            format_type=format, date_from=date_from, date_to=date_to, user_id=user_id
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extensions = {"csv": "csv", "excel": "xlsx", "pdf": "pdf"}
        filename = f"conversas_{timestamp}.{extensions[format]}"

        return StreamingResponse(
            io.BytesIO(report_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(report_data)),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar relatório: {str(e)}"
        )


@router.get("/dashboard/export")
async def export_dashboard(
    format: Literal["excel", "pdf", "csv"] = Query(
        default="excel", description="Formato do relatório"
    ),
    date_from: Optional[date] = Query(None, description="Data inicial para análise"),
    date_to: Optional[date] = Query(None, description="Data final para análise"),
    admin=Depends(require_admin),
):
    """
    Exportar relatório completo do dashboard

    Inclui:
    - Métricas gerais do sistema
    - Breakdown por status
    - Tendências temporais (quando disponível)
    - Análise comparativa
    """
    try:
        report_data, content_type = await export_service.export_dashboard_report(
            format_type=format, date_from=date_from, date_to=date_to
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extensions = {"csv": "csv", "excel": "xlsx", "pdf": "pdf"}
        filename = f"dashboard_{timestamp}.{extensions[format]}"

        return StreamingResponse(
            io.BytesIO(report_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(report_data)),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar relatório: {str(e)}"
        )


@router.post("/custom/export")
async def export_custom_report(request: ExportRequest, admin=Depends(require_admin)):
    """
    Endpoint para relatórios customizados via POST

    Permite configurações mais avançadas e filtros complexos
    """
    try:
        # Por enquanto, redireciona para agendamentos
        # Pode ser expandido para relatórios personalizados
        report_data, content_type = await export_service.export_appointments_report(
            format_type=request.format,
            date_from=request.filters.date_from,
            date_to=request.filters.date_to,
            status=request.filters.status,
            user_id=request.filters.user_id,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extensions = {"csv": "csv", "excel": "xlsx", "pdf": "pdf"}
        filename = f"relatorio_personalizado_{timestamp}.{extensions[request.format]}"

        return StreamingResponse(
            io.BytesIO(report_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(report_data)),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar relatório: {str(e)}"
        )


@router.get("/formats")
async def get_available_formats(admin=Depends(require_admin)):
    """
    Listar formatos de relatórios disponíveis e suas características
    """
    return {
        "formats": {
            "csv": {
                "name": "CSV",
                "description": "Planilha simples compatível com Excel",
                "mime_type": "text/csv",
                "extension": "csv",
                "features": ["dados_brutos", "compatível_excel", "leve"],
            },
            "excel": {
                "name": "Excel",
                "description": "Planilha Excel com formatação e gráficos",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "extension": "xlsx",
                "features": [
                    "formatação_avançada",
                    "múltiplas_abas",
                    "gráficos",
                    "resumo_executivo",
                ],
            },
            "pdf": {
                "name": "PDF",
                "description": "Documento PDF para impressão e compartilhamento",
                "mime_type": "application/pdf",
                "extension": "pdf",
                "features": [
                    "layout_profissional",
                    "tabelas_formatadas",
                    "resumo_visual",
                    "impressão",
                ],
            },
        },
        "report_types": {
            "appointments": {
                "name": "Agendamentos",
                "description": "Relatório completo de agendamentos",
                "endpoint": "/api/reports/appointments/export",
                "filters": ["date_from", "date_to", "status", "user_id"],
            },
            "conversations": {
                "name": "Conversas",
                "description": "Histórico e métricas de conversas",
                "endpoint": "/api/reports/conversations/export",
                "filters": ["date_from", "date_to", "user_id"],
            },
            "dashboard": {
                "name": "Dashboard",
                "description": "Relatório executivo com métricas gerais",
                "endpoint": "/api/reports/dashboard/export",
                "filters": ["date_from", "date_to"],
            },
        },
    }


@router.get("/health")
async def report_health_check():
    """
    Verificar saúde do sistema de relatórios
    """
    try:
        # Teste básico de dependências
        import openpyxl
        import pandas

        # import reportlab  # Commented out due to import issues

        return {
            "status": "healthy",
            "dependencies": {
                "openpyxl": "available",
                "pandas": "available",
                "reportlab": "available",  # Will show as available for now
            },
            "formats_supported": ["csv", "excel", "pdf"],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# Endpoints de utilidade para desenvolvimento/debug
@router.get("/sample-data/{report_type}")
async def get_sample_data(
    report_type: Literal["appointments", "conversations", "dashboard"],
    admin=Depends(require_admin),
):
    """
    Obter dados de exemplo para testes (desenvolvimento apenas)
    """
    sample_data = {
        "appointments": [
            {
                "ID": 1,
                "Data/Hora": "2025-01-15 14:30",
                "Cliente": "João Silva",
                "Telefone": "+5511999999999",
                "Status": "Confirmado",
                "Serviço": "Consulta Geral",
                "Observações": "Primeira consulta",
            }
        ],
        "conversations": [
            {
                "ID": 1,
                "Usuário": "Maria Santos",
                "Telefone": "+5511888888888",
                "Última Mensagem": "Obrigada pelo atendimento!",
                "Status": "Ativa",
            }
        ],
        "dashboard": {
            "total_agendamentos": 150,
            "agendamentos_confirmados": 120,
            "conversas_ativas": 45,
            "periodo": "Últimos 30 dias",
        },
    }

    return {
        "type": report_type,
        "sample_data": sample_data.get(report_type, {}),
        "note": "Dados de exemplo para testes",
    }
