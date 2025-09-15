"""
API Router para LGPD Compliance
Endpoints obrigatórios para conformidade com LGPD
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..services.lgpd_compliance import (
    LGPDComplianceManager,
    LGPDRequest,
    LGPDRequestStatus,
    LGPDRequestType,
    get_lgpd_manager,
)

# from ..auth.dependencies import get_current_user  # Comentado para desenvolvimento
from ..services.structured_apm import get_structured_logger

logger = get_structured_logger(__name__)


# Mock para desenvolvimento - remover em produção
async def get_current_user():
    """Mock de usuário para desenvolvimento"""

    class MockUser:
        id = "user_mock"
        phone = "+5511999999999"
        email = "user@example.com"
        name = "Usuário Teste"

    return MockUser()


# Pydantic Models
class DataPortabilityRequest(BaseModel):
    """Request para portabilidade de dados"""

    user_identifier: str = Field(..., description="Telefone, email ou ID do usuário")
    format: str = Field("json", description="Formato de exportação (json, zip)")
    include_metadata: bool = Field(True, description="Incluir metadados da exportação")


class DataPortabilityResponse(BaseModel):
    """Response da portabilidade de dados"""

    request_id: str
    user_identifier: str
    status: str
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    file_size_mb: Optional[float] = None


class AccountDeletionRequest(BaseModel):
    """Request para eliminação de conta"""

    user_identifier: str = Field(..., description="Telefone, email ou ID do usuário")
    confirmation: bool = Field(
        ..., description="Confirmação da operação (deve ser True)"
    )
    reason: Optional[str] = Field("user_request", description="Motivo da eliminação")


class AccountDeletionResponse(BaseModel):
    """Response da eliminação de conta"""

    request_id: str
    user_identifier: str
    deleted_at: datetime
    summary: Dict[str, Any]


class RetentionPolicyResponse(BaseModel):
    """Response das políticas de retenção"""

    executed_at: datetime
    policies_applied: Dict[str, Any]
    total_records_processed: int
    total_records_deleted: int
    total_records_anonymized: int


class DataProcessingReport(BaseModel):
    """Relatório de tratamento de dados"""

    generated_at: datetime
    data_categories: Dict[str, Any]
    total_records: int
    retention_policies: Dict[str, Any]
    processing_purposes: Dict[str, Any]
    user_rights_summary: Dict[str, bool]


# Router
router = APIRouter(prefix="/api/lgpd")


@router.get("/my-data", response_model=Dict[str, Any])
async def get_my_data(
    current_user=Depends(get_current_user),
    lgpd_manager: LGPDComplianceManager = Depends(get_lgpd_manager),
):
    """
    Endpoint para acesso aos dados pessoais (Art. 18, II LGPD)
    Permite ao usuário visualizar seus dados pessoais
    """
    try:
        logger.info(f"📋 Solicitação de acesso aos dados: {current_user.phone}")

        # Coletar dados do usuário
        user_data = await lgpd_manager.get_user_data_for_portability(current_user.phone)

        # Estruturar resposta
        response_data = {
            "user_identifier": current_user.phone,
            "data_access_date": datetime.utcnow().isoformat(),
            "legal_basis": "LGPD Art. 18, II - Confirmação da existência de tratamento",
            "data": {
                "personal_data": user_data.user_data,
                "conversations_count": len(user_data.conversations),
                "appointments_count": len(user_data.appointments),
                "data_categories": ["personal_basic", "conversation", "appointment"],
            },
            "retention_info": {
                "personal_data": "5 anos",
                "conversations": "2 anos",
                "appointments": "5 anos",
            },
            "user_rights": {
                "can_export": True,
                "can_delete": True,
                "can_correct": False,  # Não implementado
                "can_object": True,
            },
        }

        logger.info(f"✅ Dados fornecidos para: {current_user.phone}")
        return response_data

    except Exception as e:
        logger.error(f"❌ Erro ao fornecer dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/data-portability", response_model=DataPortabilityResponse)
async def request_data_portability(
    request: DataPortabilityRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    lgpd_manager: LGPDComplianceManager = Depends(get_lgpd_manager),
):
    """
    Endpoint para portabilidade de dados (Art. 18, V LGPD)
    Permite ao usuário exportar seus dados em formato estruturado
    """
    try:
        logger.info(f"📦 Solicitação de portabilidade: {request.user_identifier}")

        # Verificar se o usuário pode acessar esses dados
        if (
            current_user.phone != request.user_identifier
            and current_user.email != request.user_identifier
        ):
            raise HTTPException(
                status_code=403, detail="Acesso negado aos dados solicitados"
            )

        # Gerar ID da solicitação
        request_id = f"port_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{current_user.phone[-4:]}"

        # Iniciar exportação em background
        background_tasks.add_task(
            _export_user_data_background,
            lgpd_manager,
            request.user_identifier,
            request_id,
        )

        # Resposta imediata
        response = DataPortabilityResponse(
            request_id=request_id,
            user_identifier=request.user_identifier,
            status="processing",
            expires_at=datetime.utcnow().replace(
                hour=23, minute=59, second=59
            ),  # Expira no final do dia
        )

        logger.info(f"✅ Portabilidade iniciada: {request_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na portabilidade: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


async def _export_user_data_background(
    lgpd_manager: LGPDComplianceManager, user_identifier: str, request_id: str
):
    """Executa exportação em background"""
    try:
        logger.info(f"🔄 Iniciando exportação background: {request_id}")

        # Exportar dados
        zip_path = await lgpd_manager.export_user_data(user_identifier)

        # Calcular tamanho do arquivo
        file_size = Path(zip_path).stat().st_size / (1024 * 1024)  # MB

        logger.info(f"✅ Exportação concluída: {zip_path} ({file_size:.2f}MB)")

        # Aqui você pode salvar o status em banco de dados ou cache
        # Para simplificar, só logamos

    except Exception as e:
        logger.error(f"❌ Erro na exportação background: {e}")


@router.get("/data-portability/{request_id}/download")
async def download_data_export(
    request_id: str,
    current_user=Depends(get_current_user),
    lgpd_manager: LGPDComplianceManager = Depends(get_lgpd_manager),
):
    """
    Download do arquivo de portabilidade de dados
    """
    try:
        # Verificar se o arquivo existe
        export_pattern = f"dados_pessoais_*{request_id[-8:]}.zip"
        export_dir = Path("exports/lgpd")

        matching_files = list(export_dir.glob("dados_pessoais_*.zip"))

        if not matching_files:
            raise HTTPException(
                status_code=404, detail="Arquivo de exportação não encontrado"
            )

        # Pegar o arquivo mais recente
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)

        if not latest_file.exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        logger.info(f"📥 Download de portabilidade: {latest_file}")

        return FileResponse(
            path=str(latest_file),
            filename=f"meus_dados_pessoais_{datetime.now().strftime('%Y%m%d')}.zip",
            media_type="application/zip",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no download: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/delete-account", response_model=AccountDeletionResponse)
async def delete_user_account(
    request: AccountDeletionRequest,
    current_user=Depends(get_current_user),
    lgpd_manager: LGPDComplianceManager = Depends(get_lgpd_manager),
):
    """
    Endpoint para direito ao esquecimento (Art. 18, VI LGPD)
    Elimina completamente os dados pessoais do usuário
    """
    try:
        logger.info(f"🗑️ Solicitação de eliminação: {request.user_identifier}")

        # Verificar confirmação
        if not request.confirmation:
            raise HTTPException(
                status_code=400, detail="Confirmação obrigatória não fornecida"
            )

        # Verificar se o usuário pode deletar esses dados
        if (
            current_user.phone != request.user_identifier
            and current_user.email != request.user_identifier
        ):
            raise HTTPException(
                status_code=403, detail="Acesso negado para eliminação desses dados"
            )

        # Executar eliminação
        deletion_summary = await lgpd_manager.delete_user_account(
            user_identifier=request.user_identifier, reason=request.reason
        )

        # Gerar ID da solicitação
        request_id = f"del_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{current_user.phone[-4:]}"

        response = AccountDeletionResponse(
            request_id=request_id,
            user_identifier=request.user_identifier,
            deleted_at=datetime.utcnow(),
            summary=deletion_summary,
        )

        logger.info(f"✅ Conta eliminada com sucesso: {request_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na eliminação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/data-processing-report", response_model=DataProcessingReport)
async def get_data_processing_report(
    # current_admin = Depends(get_current_admin_user),  # Apenas admins
    lgpd_manager: LGPDComplianceManager = Depends(get_lgpd_manager),
):
    """
    Relatório de tratamento de dados pessoais (Art. 37 LGPD)
    Endpoint administrativo para auditoria
    """
    try:
        logger.info("📊 Solicitação de relatório de tratamento de dados")

        # Gerar relatório
        report_data = await lgpd_manager.get_data_processing_report()

        response = DataProcessingReport(
            generated_at=datetime.fromisoformat(report_data["generated_at"]),
            data_categories=report_data["data_categories"],
            total_records=report_data["total_records"],
            retention_policies=report_data["retention_policies"],
            processing_purposes=report_data["processing_purposes"],
            user_rights_summary=report_data["user_rights_summary"],
        )

        logger.info("✅ Relatório de tratamento gerado")
        return response

    except Exception as e:
        logger.error(f"❌ Erro no relatório: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/apply-retention-policies", response_model=RetentionPolicyResponse)
async def apply_retention_policies(
    # current_admin = Depends(get_current_admin_user),  # Apenas admins
    lgpd_manager: LGPDComplianceManager = Depends(get_lgpd_manager),
):
    """
    Aplica políticas de retenção automática
    Endpoint administrativo para limpeza periódica
    """
    try:
        logger.info("🔄 Aplicação de políticas de retenção iniciada")

        # Aplicar políticas
        retention_result = await lgpd_manager.apply_retention_policies()

        response = RetentionPolicyResponse(
            executed_at=datetime.fromisoformat(retention_result["executed_at"]),
            policies_applied=retention_result["policies_applied"],
            total_records_processed=retention_result["total_records_processed"],
            total_records_deleted=retention_result["total_records_deleted"],
            total_records_anonymized=retention_result["total_records_anonymized"],
        )

        logger.info(
            f"✅ Políticas aplicadas: {response.total_records_processed} registros processados"
        )
        return response

    except Exception as e:
        logger.error(f"❌ Erro na aplicação de políticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/privacy-policy")
async def get_privacy_policy():
    """
    Política de privacidade e termos LGPD
    """
    privacy_policy = {
        "last_updated": "2025-09-09",
        "version": "1.0",
        "controller": {
            "name": "WhatsApp Agent",
            "contact": "dpo@whatsappagent.com",
            "address": "Brasil",
        },
        "data_categories": [
            {
                "category": "Dados Pessoais Básicos",
                "data_types": ["nome", "telefone", "email"],
                "purpose": "Atendimento ao cliente e execução de serviços",
                "legal_basis": "Consentimento (Art. 7º, I LGPD)",
                "retention": "5 anos",
            },
            {
                "category": "Conversas e Mensagens",
                "data_types": ["histórico de conversas", "mensagens"],
                "purpose": "Execução de serviços e suporte",
                "legal_basis": "Execução de contrato (Art. 7º, V LGPD)",
                "retention": "2 anos",
            },
            {
                "category": "Agendamentos",
                "data_types": ["dados de agendamento", "preferências"],
                "purpose": "Cumprimento de obrigação legal e execução de serviços",
                "legal_basis": "Obrigação legal (Art. 7º, II LGPD)",
                "retention": "5 anos",
            },
        ],
        "user_rights": [
            "Confirmação da existência de tratamento",
            "Acesso aos dados",
            "Correção de dados incompletos",
            "Anonimização ou eliminação",
            "Portabilidade dos dados",
            "Informação sobre compartilhamento",
            "Revogação do consentimento",
        ],
        "contact_dpo": {"email": "dpo@whatsappagent.com", "phone": "+55 11 99999-9999"},
    }

    return privacy_policy


@router.get("/user-rights")
async def get_user_rights():
    """
    Informações sobre direitos do titular (Art. 18 LGPD)
    """
    user_rights = {
        "lgpd_rights": {
            "art_18_i": {
                "right": "Confirmação da existência de tratamento",
                "endpoint": "GET /api/lgpd/my-data",
                "description": "Verificar se seus dados estão sendo tratados",
            },
            "art_18_ii": {
                "right": "Acesso aos dados",
                "endpoint": "GET /api/lgpd/my-data",
                "description": "Visualizar todos os seus dados pessoais",
            },
            "art_18_iii": {
                "right": "Correção de dados",
                "endpoint": "Não implementado",
                "description": "Corrigir dados incompletos ou inexatos",
            },
            "art_18_iv": {
                "right": "Anonimização",
                "endpoint": "POST /api/lgpd/delete-account",
                "description": "Anonimizar dados quando possível",
            },
            "art_18_v": {
                "right": "Portabilidade",
                "endpoint": "POST /api/lgpd/data-portability",
                "description": "Obter dados em formato estruturado",
            },
            "art_18_vi": {
                "right": "Eliminação",
                "endpoint": "POST /api/lgpd/delete-account",
                "description": "Eliminação completa dos dados",
            },
        },
        "how_to_exercise": {
            "online": "Use os endpoints da API disponíveis",
            "email": "dpo@whatsappagent.com",
            "response_time": "15 dias úteis conforme LGPD",
        },
    }

    return user_rights


@router.get("/health")
async def lgpd_health_check():
    """Health check do sistema LGPD"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints_available": [
            "/my-data",
            "/data-portability",
            "/delete-account",
            "/data-processing-report",
            "/apply-retention-policies",
        ],
        "lgpd_compliance": "active",
    }
