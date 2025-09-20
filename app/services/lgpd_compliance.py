"""
Sistema de LGPD Compliance Completo
Implementação completa para conformidade com LGPD (Lei Geral de Proteção de Dados)
"""

import asyncio
import hashlib
import json
import logging
import os
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, delete, or_, select, text, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..database import AsyncSessionLocal
from ..models.database import Appointment, Base, Conversation, Message, User
from ..services.structured_apm import get_structured_logger

logger = get_structured_logger(__name__)


class LGPDDataCategory(Enum):
    """Categorias de dados pessoais para LGPD"""

    PERSONAL_BASIC = "personal_basic"  # Nome, telefone, email
    PERSONAL_SENSITIVE = "personal_sensitive"  # Dados sensíveis (se houver)
    CONVERSATION = "conversation"  # Conversas e mensagens
    APPOINTMENT = "appointment"  # Agendamentos
    LOCATION = "location"  # Dados de localização
    BEHAVIORAL = "behavioral"  # Dados comportamentais
    TECHNICAL = "technical"  # IPs, logs técnicos
    FINANCIAL = "financial"  # Dados financeiros (se houver)


class LGPDRetentionPeriod(Enum):
    """Períodos de retenção conforme LGPD"""

    IMMEDIATE = 0  # Imediato
    DAYS_30 = 30  # 30 dias
    DAYS_90 = 90  # 90 dias
    DAYS_180 = 180  # 6 meses
    YEAR_1 = 365  # 1 ano
    YEARS_2 = 730  # 2 anos
    YEARS_5 = 1825  # 5 anos (máximo legal)
    INDEFINITE = -1  # Indefinido (com base legal)


class LGPDProcessingPurpose(Enum):
    """Finalidades de tratamento conforme LGPD"""

    CUSTOMER_SERVICE = "customer_service"  # Atendimento ao cliente
    SERVICE_EXECUTION = "service_execution"  # Execução de serviços
    LEGAL_COMPLIANCE = "legal_compliance"  # Cumprimento de obrigação legal
    LEGITIMATE_INTEREST = "legitimate_interest"  # Interesse legítimo
    CONSENT = "consent"  # Consentimento
    CONTRACT_EXECUTION = "contract_execution"  # Execução de contrato


class LGPDRequestType(Enum):
    """Tipos de solicitações LGPD"""

    ACCESS = "access"  # Acesso aos dados (Art. 18, II)
    CORRECTION = "correction"  # Correção (Art. 18, III)
    PORTABILITY = "portability"  # Portabilidade (Art. 18, V)
    DELETION = "deletion"  # Eliminação (Art. 18, VI)
    ANONYMIZATION = "anonymization"  # Anonimização (Art. 18, IV)
    REVOKE_CONSENT = "revoke_consent"  # Revogação do consentimento
    OBJECT_PROCESSING = "object_processing"  # Oposição ao tratamento


class LGPDRequestStatus(Enum):
    """Status das solicitações LGPD"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class LGPDDataMap:
    """Mapeamento de dados pessoais"""

    category: LGPDDataCategory
    table_name: str
    columns: List[str]
    retention_period: LGPDRetentionPeriod
    processing_purpose: LGPDProcessingPurpose
    legal_basis: str
    anonymizable: bool = True
    exportable: bool = True


@dataclass
class LGPDRequest:
    """Solicitação LGPD"""

    id: Optional[str] = None
    user_identifier: str = ""  # telefone, email, etc
    request_type: LGPDRequestType = LGPDRequestType.ACCESS
    status: LGPDRequestStatus = LGPDRequestStatus.PENDING
    requested_at: datetime = None
    completed_at: Optional[datetime] = None
    data_package_path: Optional[str] = None
    notes: Optional[str] = None
    expiry_at: Optional[datetime] = None


@dataclass
class LGPDDataPortability:
    """Dados para portabilidade"""

    user_data: Dict[str, Any]
    conversations: List[Dict[str, Any]]
    appointments: List[Dict[str, Any]]
    generated_at: datetime
    format_version: str = "1.0"


class LGPDComplianceManager:
    """Gerenciador de conformidade LGPD"""

    def __init__(self):
        self.data_maps = self._initialize_data_maps()
        self.export_base_path = Path("exports/lgpd")
        self.export_base_path.mkdir(parents=True, exist_ok=True)

    def _initialize_data_maps(self) -> Dict[str, LGPDDataMap]:
        """Inicializa mapeamento de dados pessoais"""
        return {
            "users": LGPDDataMap(
                category=LGPDDataCategory.PERSONAL_BASIC,
                table_name="users",
                columns=["id", "name", "email", "phone", "created_at", "updated_at"],
                retention_period=LGPDRetentionPeriod.YEARS_5,
                processing_purpose=LGPDProcessingPurpose.CUSTOMER_SERVICE,
                legal_basis="Art. 7º, I - consentimento",
            ),
            "conversations": LGPDDataMap(
                category=LGPDDataCategory.CONVERSATION,
                table_name="conversations",
                columns=[
                    "id",
                    "user_id",
                    "phone_number",
                    "context",
                    "created_at",
                    "updated_at",
                ],
                retention_period=LGPDRetentionPeriod.YEARS_2,
                processing_purpose=LGPDProcessingPurpose.SERVICE_EXECUTION,
                legal_basis="Art. 7º, V - execução de contrato",
            ),
            "messages": LGPDDataMap(
                category=LGPDDataCategory.CONVERSATION,
                table_name="messages",
                columns=[
                    "id",
                    "conversation_id",
                    "content",
                    "sender_type",
                    "created_at",
                ],
                retention_period=LGPDRetentionPeriod.YEARS_2,
                processing_purpose=LGPDProcessingPurpose.SERVICE_EXECUTION,
                legal_basis="Art. 7º, V - execução de contrato",
            ),
            "appointments": LGPDDataMap(
                category=LGPDDataCategory.APPOINTMENT,
                table_name="appointments",
                columns=[
                    "id",
                    "user_id",
                    "client_name",
                    "client_phone",
                    "service_type",
                    "scheduled_at",
                    "notes",
                ],
                retention_period=LGPDRetentionPeriod.YEARS_5,
                processing_purpose=LGPDProcessingPurpose.LEGAL_COMPLIANCE,
                legal_basis="Art. 7º, II - cumprimento de obrigação legal",
            ),
            # "clients": LGPDDataMap(
            #     category=LGPDDataCategory.PERSONAL_BASIC,
            #     table_name="clients",
            #     columns=["id", "name", "phone", "email", "notes", "created_at"],
            #     retention_period=LGPDRetentionPeriod.YEARS_5,
            #     processing_purpose=LGPDProcessingPurpose.CUSTOMER_SERVICE,
            #     legal_basis="Art. 7º, I - consentimento",
            # ),
        }

    async def get_user_data_for_portability(
        self, user_identifier: str
    ) -> LGPDDataPortability:
        """
        Coleta todos os dados de um usuário para portabilidade (Art. 18, V)

        Args:
            user_identifier: Telefone, email ou ID do usuário

        Returns:
            LGPDDataPortability: Dados estruturados para exportação
        """
        logger.info(f"🔍 Coletando dados para portabilidade: {user_identifier}")

        try:
            async with AsyncSessionLocal() as session:
                # Buscar usuário principal
                user_data = await self._get_user_basic_data(session, user_identifier)
                if not user_data:
                    raise ValueError(f"Usuário não encontrado: {user_identifier}")

                user_id = user_data.get("id")
                phone_number = user_data.get("phone") or user_identifier

                # Coletar conversas
                conversations = await self._get_user_conversations(
                    session, user_id, phone_number
                )

                # Coletar agendamentos
                appointments = await self._get_user_appointments(
                    session, user_id, phone_number
                )

                # Dados adicionais de clientes
                client_data = await self._get_user_client_data(session, phone_number)
                if client_data:
                    user_data.update({"client_profile": client_data})

                portability_data = LGPDDataPortability(
                    user_data=user_data,
                    conversations=conversations,
                    appointments=appointments,
                    generated_at=datetime.utcnow(),
                )

                logger.info(
                    f"✅ Dados coletados: {len(conversations)} conversas, {len(appointments)} agendamentos"
                )
                return portability_data

        except Exception as e:
            logger.error(f"❌ Erro ao coletar dados para portabilidade: {e}")
            raise

    async def _get_user_basic_data(
        self, session: Session, user_identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Coleta dados básicos do usuário"""
        try:
            # Tentar por telefone primeiro
            stmt = select(User).where(
                or_(
                    User.phone == user_identifier,
                    User.email == user_identifier,
                    User.id == user_identifier,
                )
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            return {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "data_category": "personal_basic",
                "retention_period": "5_years",
                "processing_purpose": "customer_service",
            }

        except Exception as e:
            logger.error(f"Erro ao buscar dados básicos: {e}")
            return None

    async def _get_user_conversations(
        self, session: Session, user_id: str, phone_number: str
    ) -> List[Dict[str, Any]]:
        """Coleta conversas do usuário"""
        try:
            stmt = (
                select(Conversation)
                .options(selectinload(Conversation.messages))
                .where(
                    or_(
                        Conversation.user_id == user_id,
                        Conversation.phone_number == phone_number,
                    )
                )
            )

            result = await session.execute(stmt)
            conversations = result.scalars().all()

            conversation_data = []
            for conv in conversations:
                conv_dict = {
                    "id": str(conv.id),
                    "phone_number": conv.phone_number,
                    "created_at": (
                        conv.created_at.isoformat() if conv.created_at else None
                    ),
                    "updated_at": (
                        conv.updated_at.isoformat() if conv.updated_at else None
                    ),
                    "context": conv.context,
                    "messages": [],
                }

                # Adicionar mensagens
                if hasattr(conv, "messages") and conv.messages:
                    for msg in conv.messages:
                        conv_dict["messages"].append(
                            {
                                "id": str(msg.id),
                                "content": msg.content,
                                "sender_type": msg.sender_type,
                                "created_at": (
                                    msg.created_at.isoformat()
                                    if msg.created_at
                                    else None
                                ),
                            }
                        )

                conversation_data.append(conv_dict)

            return conversation_data

        except Exception as e:
            logger.error(f"Erro ao buscar conversas: {e}")
            return []

    async def _get_user_appointments(
        self, session: Session, user_id: str, phone_number: str
    ) -> List[Dict[str, Any]]:
        """Coleta agendamentos do usuário"""
        try:
            stmt = select(Appointment).where(
                or_(
                    Appointment.user_id == user_id,
                    Appointment.client_phone == phone_number,
                )
            )

            result = await session.execute(stmt)
            appointments = result.scalars().all()

            appointment_data = []
            for apt in appointments:
                appointment_data.append(
                    {
                        "id": str(apt.id),
                        "client_name": apt.client_name,
                        "client_phone": apt.client_phone,
                        "service_type": apt.service_type,
                        "scheduled_at": (
                            apt.scheduled_at.isoformat() if apt.scheduled_at else None
                        ),
                        "status": apt.status,
                        "notes": apt.notes,
                        "created_at": (
                            apt.created_at.isoformat() if apt.created_at else None
                        ),
                    }
                )

            return appointment_data

        except Exception as e:
            logger.error(f"Erro ao buscar agendamentos: {e}")
            return []

    async def _get_user_client_data(
        self, session: Session, phone_number: str
    ) -> Optional[Dict[str, Any]]:
        """Coleta dados de cliente"""
        try:
            stmt = select(Client).where(Client.phone == phone_number)
            result = await session.execute(stmt)
            client = result.scalar_one_or_none()

            if not client:
                return None

            return {
                "id": str(client.id),
                "name": client.name,
                "phone": client.phone,
                "email": client.email,
                "notes": client.notes,
                "created_at": (
                    client.created_at.isoformat() if client.created_at else None
                ),
            }

        except Exception as e:
            logger.error(f"Erro ao buscar dados de cliente: {e}")
            return None

    async def export_user_data(self, user_identifier: str) -> str:
        """
        Exporta dados do usuário em formato ZIP para portabilidade

        Args:
            user_identifier: Identificador do usuário

        Returns:
            str: Caminho do arquivo ZIP gerado
        """
        logger.info(f"📦 Iniciando exportação de dados: {user_identifier}")

        try:
            # Coletar dados
            portability_data = await self.get_user_data_for_portability(user_identifier)

            # Criar diretório temporário
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            export_id = hashlib.md5(
                f"{user_identifier}_{timestamp}".encode()
            ).hexdigest()[:8]

            temp_dir = self.export_base_path / f"export_{export_id}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Gerar arquivos JSON
            files_created = []

            # 1. Dados básicos do usuário
            user_file = temp_dir / "dados_pessoais.json"
            with open(user_file, "w", encoding="utf-8") as f:
                json.dump(portability_data.user_data, f, ensure_ascii=False, indent=2)
            files_created.append(user_file)

            # 2. Conversas
            if portability_data.conversations:
                conversations_file = temp_dir / "conversas.json"
                with open(conversations_file, "w", encoding="utf-8") as f:
                    json.dump(
                        portability_data.conversations, f, ensure_ascii=False, indent=2
                    )
                files_created.append(conversations_file)

            # 3. Agendamentos
            if portability_data.appointments:
                appointments_file = temp_dir / "agendamentos.json"
                with open(appointments_file, "w", encoding="utf-8") as f:
                    json.dump(
                        portability_data.appointments, f, ensure_ascii=False, indent=2
                    )
                files_created.append(appointments_file)

            # 4. Metadados da exportação
            metadata = {
                "export_id": export_id,
                "user_identifier": user_identifier,
                "generated_at": portability_data.generated_at.isoformat(),
                "format_version": portability_data.format_version,
                "legal_basis": "LGPD Art. 18, V - Portabilidade dos dados",
                "retention_info": {
                    "dados_pessoais": "5 anos",
                    "conversas": "2 anos",
                    "agendamentos": "5 anos",
                },
                "files_included": [f.name for f in files_created],
            }

            metadata_file = temp_dir / "metadados.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            files_created.append(metadata_file)

            # 5. Criar arquivo ZIP
            zip_path = self.export_base_path / f"dados_pessoais_{export_id}.zip"

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_created:
                    zipf.write(file_path, file_path.name)

            # Limpar arquivos temporários
            for file_path in files_created:
                file_path.unlink()
            temp_dir.rmdir()

            logger.info(f"✅ Exportação concluída: {zip_path}")
            return str(zip_path)

        except Exception as e:
            logger.error(f"❌ Erro na exportação: {e}")
            raise

    async def delete_user_account(
        self, user_identifier: str, reason: str = "user_request"
    ) -> Dict[str, Any]:
        """
        Executa direito ao esquecimento - eliminação completa dos dados (Art. 18, VI)

        Args:
            user_identifier: Identificador do usuário
            reason: Motivo da eliminação

        Returns:
            Dict com resumo da operação
        """
        logger.info(f"🗑️ Iniciando eliminação de conta: {user_identifier}")

        try:
            async with AsyncSessionLocal() as session:
                deletion_summary = {
                    "user_identifier": user_identifier,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "reason": reason,
                    "deleted_records": {},
                    "anonymized_records": {},
                    "legal_basis": "LGPD Art. 18, VI - Direito ao esquecimento",
                }

                # 1. Buscar usuário
                user_data = await self._get_user_basic_data(session, user_identifier)
                if not user_data:
                    raise ValueError(f"Usuário não encontrado: {user_identifier}")

                user_id = user_data.get("id")
                phone_number = user_data.get("phone") or user_identifier

                # 2. Deletar conversas e mensagens
                conversations_deleted = await self._delete_user_conversations(
                    session, user_id, phone_number
                )
                deletion_summary["deleted_records"][
                    "conversations"
                ] = conversations_deleted

                # 3. Anonimizar agendamentos (manter por obrigação legal)
                appointments_anonymized = await self._anonymize_user_appointments(
                    session, user_id, phone_number
                )
                deletion_summary["anonymized_records"][
                    "appointments"
                ] = appointments_anonymized

                # 4. Deletar dados de cliente
                clients_deleted = await self._delete_user_clients(session, phone_number)
                deletion_summary["deleted_records"]["clients"] = clients_deleted

                # 5. Deletar usuário principal
                users_deleted = await self._delete_user_record(session, user_id)
                deletion_summary["deleted_records"]["users"] = users_deleted

                # 6. Commit das alterações
                await session.commit()

                logger.info(f"✅ Conta eliminada com sucesso: {deletion_summary}")
                return deletion_summary

        except Exception as e:
            logger.error(f"❌ Erro na eliminação de conta: {e}")
            raise

    async def _delete_user_conversations(
        self, session: Session, user_id: str, phone_number: str
    ) -> int:
        """Deleta conversas e mensagens do usuário"""
        try:
            # Buscar IDs das conversas
            conv_stmt = select(Conversation.id).where(
                or_(
                    Conversation.user_id == user_id,
                    Conversation.phone_number == phone_number,
                )
            )
            conv_result = await session.execute(conv_stmt)
            conversation_ids = [row[0] for row in conv_result.fetchall()]

            deleted_count = 0

            if conversation_ids:
                # Deletar mensagens
                msg_stmt = delete(Message).where(
                    Message.conversation_id.in_(conversation_ids)
                )
                await session.execute(msg_stmt)

                # Deletar conversas
                conv_delete_stmt = delete(Conversation).where(
                    Conversation.id.in_(conversation_ids)
                )
                result = await session.execute(conv_delete_stmt)
                deleted_count = result.rowcount

            return deleted_count

        except Exception as e:
            logger.error(f"Erro ao deletar conversas: {e}")
            return 0

    async def _anonymize_user_appointments(
        self, session: Session, user_id: str, phone_number: str
    ) -> int:
        """Anonimiza agendamentos (manter por obrigação legal)"""
        try:
            # Atualizar com dados anonimizados
            stmt = (
                update(Appointment)
                .where(
                    or_(
                        Appointment.user_id == user_id,
                        Appointment.client_phone == phone_number,
                    )
                )
                .values(
                    client_name="[DADOS ANONIMIZADOS]",
                    client_phone="[ANONIMIZADO]",
                    notes="[DADOS ANONIMIZADOS - LGPD]",
                    user_id=None,
                )
            )

            result = await session.execute(stmt)
            return result.rowcount

        except Exception as e:
            logger.error(f"Erro ao anonimizar agendamentos: {e}")
            return 0

    async def _delete_user_clients(self, session: Session, phone_number: str) -> int:
        """Deleta registros de cliente"""
        try:
            stmt = delete(Client).where(Client.phone == phone_number)
            result = await session.execute(stmt)
            return result.rowcount

        except Exception as e:
            logger.error(f"Erro ao deletar clientes: {e}")
            return 0

    async def _delete_user_record(self, session: Session, user_id: str) -> int:
        """Deleta registro principal do usuário"""
        try:
            stmt = delete(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.rowcount

        except Exception as e:
            logger.error(f"Erro ao deletar usuário: {e}")
            return 0

    async def apply_retention_policies(self) -> Dict[str, Any]:
        """
        Aplica políticas de retenção automática conforme LGPD

        Returns:
            Dict com resumo das operações de retenção
        """
        logger.info("🔄 Iniciando aplicação de políticas de retenção LGPD")

        try:
            retention_summary = {
                "executed_at": datetime.utcnow().isoformat(),
                "policies_applied": {},
                "total_records_processed": 0,
                "total_records_deleted": 0,
                "total_records_anonymized": 0,
            }

            async with AsyncSessionLocal() as session:
                # Processar cada mapeamento de dados
                for data_key, data_map in self.data_maps.items():
                    if data_map.retention_period == LGPDRetentionPeriod.INDEFINITE:
                        continue

                    records_processed = await self._apply_retention_policy(
                        session, data_map
                    )
                    retention_summary["policies_applied"][data_key] = records_processed
                    retention_summary[
                        "total_records_processed"
                    ] += records_processed.get("processed", 0)
                    retention_summary["total_records_deleted"] += records_processed.get(
                        "deleted", 0
                    )
                    retention_summary[
                        "total_records_anonymized"
                    ] += records_processed.get("anonymized", 0)

                await session.commit()

            logger.info(f"✅ Políticas de retenção aplicadas: {retention_summary}")
            return retention_summary

        except Exception as e:
            logger.error(f"❌ Erro na aplicação de políticas de retenção: {e}")
            raise

    async def _apply_retention_policy(
        self, session: Session, data_map: LGPDDataMap
    ) -> Dict[str, int]:
        """Aplica política de retenção para um mapeamento específico"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(
                days=data_map.retention_period.value
            )

            # Query para registros expirados
            query = text(
                f"""
                SELECT COUNT(*) FROM {data_map.table_name}
                WHERE created_at < :cutoff_date
            """
            )

            result = await session.execute(query, {"cutoff_date": cutoff_date})
            expired_count = result.scalar()

            if expired_count == 0:
                return {"processed": 0, "deleted": 0, "anonymized": 0}

            # Decidir entre deletar ou anonimizar
            if data_map.processing_purpose == LGPDProcessingPurpose.LEGAL_COMPLIANCE:
                # Anonimizar registros com base legal
                anonymize_query = text(
                    f"""
                    UPDATE {data_map.table_name}
                    SET notes = '[DADOS ANONIMIZADOS - RETENÇÃO LGPD]',
                        updated_at = :now
                    WHERE created_at < :cutoff_date
                """
                )

                await session.execute(
                    anonymize_query,
                    {"cutoff_date": cutoff_date, "now": datetime.utcnow()},
                )

                return {
                    "processed": expired_count,
                    "deleted": 0,
                    "anonymized": expired_count,
                }
            else:
                # Deletar registros sem base legal
                delete_query = text(
                    f"""
                    DELETE FROM {data_map.table_name}
                    WHERE created_at < :cutoff_date
                """
                )

                await session.execute(delete_query, {"cutoff_date": cutoff_date})

                return {
                    "processed": expired_count,
                    "deleted": expired_count,
                    "anonymized": 0,
                }

        except Exception as e:
            logger.error(
                f"Erro ao aplicar política de retenção para {data_map.table_name}: {e}"
            )
            return {"processed": 0, "deleted": 0, "anonymized": 0}

    async def get_data_processing_report(self) -> Dict[str, Any]:
        """
        Gera relatório de tratamento de dados pessoais (Art. 37)

        Returns:
            Dict com informações sobre tratamento de dados
        """
        logger.info("📊 Gerando relatório de tratamento de dados LGPD")

        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "report_version": "1.0",
                "legal_basis": "LGPD Art. 37 - Relatório de impacto",
                "data_categories": {},
                "total_records": 0,
                "retention_policies": {},
                "processing_purposes": {},
                "user_rights_summary": {
                    "portability_available": True,
                    "deletion_available": True,
                    "access_available": True,
                    "correction_available": False,  # Não implementado nesta versão
                },
            }

            async with AsyncSessionLocal() as session:
                # Analisar cada categoria de dados
                for data_key, data_map in self.data_maps.items():
                    count_query = text(f"SELECT COUNT(*) FROM {data_map.table_name}")
                    result = await session.execute(count_query)
                    record_count = result.scalar()

                    report["data_categories"][data_key] = {
                        "table": data_map.table_name,
                        "category": data_map.category.value,
                        "record_count": record_count,
                        "retention_period": data_map.retention_period.value,
                        "processing_purpose": data_map.processing_purpose.value,
                        "legal_basis": data_map.legal_basis,
                        "anonymizable": data_map.anonymizable,
                        "exportable": data_map.exportable,
                    }

                    report["total_records"] += record_count

                    # Agrupar por finalidades
                    purpose = data_map.processing_purpose.value
                    if purpose not in report["processing_purposes"]:
                        report["processing_purposes"][purpose] = []
                    report["processing_purposes"][purpose].append(data_key)

                    # Agrupar políticas de retenção
                    retention = data_map.retention_period.value
                    if retention not in report["retention_policies"]:
                        report["retention_policies"][retention] = []
                    report["retention_policies"][retention].append(data_key)

            logger.info(
                f"✅ Relatório gerado: {report['total_records']} registros analisados"
            )
            return report

        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            raise


# Instância global do gerenciador
lgpd_manager = LGPDComplianceManager()


def get_lgpd_manager() -> LGPDComplianceManager:
    """Dependency injection para o gerenciador LGPD"""
    return lgpd_manager
