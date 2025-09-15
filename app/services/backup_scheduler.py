"""
Agendador de Backups Automatizados
Gerencia execução periódica de backups usando APScheduler
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.services.alert_system import alert_manager
from app.services.backup_service import BackupService
from app.utils.logger import get_logger

logger = get_logger(__name__)
config = get_settings()


class BackupScheduler:
    """
    Agendador para execução automática de backups

    Funcionalidades:
    - Agendamento baseado em cron
    - Monitoramento de execuções
    - Alertas em caso de falha
    - Relatórios de status
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            timezone="America/Sao_Paulo",
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,  # 5 minutos
            },
        )

        self.backup_service = BackupService()
        self.is_running = False

        # Configurações de agendamento
        self.backup_schedule = os.getenv(
            "BACKUP_SCHEDULE", "0 2 * * *"
        )  # 2h da manhã diariamente
        self.health_check_interval = int(
            os.getenv("BACKUP_HEALTH_CHECK_INTERVAL", "6")
        )  # 6 horas

        # Histórico de execuções
        self.execution_history = []
        self.max_history_size = 50

        logger.info(f"BackupScheduler initialized - Schedule: {self.backup_schedule}")

    async def start(self):
        """Iniciar agendador"""
        if self.is_running:
            logger.warning("BackupScheduler is already running")
            return

        try:
            # Adicionar listeners
            self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)

            # Agendar backup principal
            self.scheduler.add_job(
                self._execute_backup_routine,
                CronTrigger.from_crontab(self.backup_schedule),
                id="main_backup",
                name="Main Backup Routine",
                replace_existing=True,
            )

            # Agendar verificação de saúde
            self.scheduler.add_job(
                self._health_check_routine,
                IntervalTrigger(hours=self.health_check_interval),
                id="backup_health_check",
                name="Backup Health Check",
                replace_existing=True,
            )

            # Agendar limpeza de logs
            self.scheduler.add_job(
                self._cleanup_logs,
                CronTrigger(hour=3, minute=30),  # 3:30 da manhã diariamente
                id="log_cleanup",
                name="Log Cleanup",
                replace_existing=True,
            )

            # Iniciar scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("BackupScheduler started successfully")

            # Executar health check inicial
            await asyncio.create_task(self._health_check_routine())

        except Exception as e:
            logger.error(f"Failed to start BackupScheduler: {e}")
            raise

    async def stop(self):
        """Parar agendador"""
        if not self.is_running:
            return

        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("BackupScheduler stopped")

        except Exception as e:
            logger.error(f"Error stopping BackupScheduler: {e}")

    async def _execute_backup_routine(self):
        """Executar rotina de backup"""
        execution_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        start_time = datetime.now()
        logger.info(f"Starting scheduled backup routine: {execution_id}")

        try:
            # Executar backup completo
            result = await self.backup_service.full_backup_routine()

            # Registrar execução
            execution_record = {
                "id": execution_id,
                "started_at": start_time.isoformat(),
                "completed_at": datetime.now().isoformat(),
                "success": result["success"],
                "backups_created": len(result.get("backups_created", [])),
                "cloud_uploads": len(result.get("cloud_uploads", [])),
                "errors": result.get("errors", []),
                "duration_minutes": result.get("duration_minutes", 0),
            }

            self._add_to_history(execution_record)

            if result["success"]:
                logger.info(f"Scheduled backup completed successfully: {execution_id}")

                # Alerta de sucesso apenas se houve problemas recentes
                if self._has_recent_failures():
                    await alert_manager.create_alert(
                        alert_id=f"backup_recovered_{execution_id}",
                        alert_type="SYSTEM_INFO",
                        severity="LOW",
                        title="Backup Sistema Recuperado",
                        message="Sistema de backup voltou a funcionar normalmente após falhas anteriores",
                        data=execution_record,
                    )
            else:
                logger.error(f"Scheduled backup failed: {execution_id}")

                # Alerta crítico de falha
                await alert_manager.create_alert(
                    alert_id=f"backup_failed_{execution_id}",
                    alert_type="SYSTEM_ERROR",
                    severity="HIGH",
                    title="Backup Automático Falhou",
                    message=f"Falha na execução do backup agendado: {', '.join(result.get('errors', ['Unknown error']))}",
                    data=execution_record,
                )

        except Exception as e:
            error_msg = f"Backup routine execution failed: {e}"
            logger.error(error_msg)

            # Registrar falha
            execution_record = {
                "id": execution_id,
                "started_at": start_time.isoformat(),
                "completed_at": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "duration_minutes": (datetime.now() - start_time).total_seconds() / 60,
            }

            self._add_to_history(execution_record)

            # Alerta crítico
            await alert_manager.create_alert(
                alert_id=f"backup_exception_{execution_id}",
                alert_type="SYSTEM_ERROR",
                severity="CRITICAL",
                title="Erro Crítico no Sistema de Backup",
                message=f"Exceção durante execução do backup: {error_msg}",
                data=execution_record,
            )

    async def _health_check_routine(self):
        """Verificação de saúde dos backups"""
        logger.info("Starting backup health check...")

        try:
            status = await self.backup_service.get_backup_status()

            # Verificar se há backups recentes
            last_backup_age = status.get("last_backup_age_hours")

            if last_backup_age is None:
                # Nenhum backup encontrado
                await alert_manager.create_alert(
                    alert_id="backup_health_no_backups",
                    alert_type="SYSTEM_ERROR",
                    severity="HIGH",
                    title="Nenhum Backup Encontrado",
                    message="Sistema não possui nenhum backup disponível",
                    data=status,
                )

            elif last_backup_age > 36:  # Mais de 36 horas
                # Backup muito antigo
                await alert_manager.create_alert(
                    alert_id="backup_health_old_backup",
                    alert_type="SYSTEM_WARNING",
                    severity="MEDIUM",
                    title="Backup Desatualizado",
                    message=f"Último backup tem {last_backup_age:.1f} horas (recomendado: máximo 24h)",
                    data=status,
                )

            # Verificar espaço em disco
            backup_dir = Path("/app/backups")
            if backup_dir.exists():
                # Calcular uso de disco
                total_size = sum(f.stat().st_size for f in backup_dir.glob("*.gz"))
                total_size_gb = total_size / (1024**3)

                if total_size_gb > 10:  # Mais de 10GB
                    await alert_manager.create_alert(
                        alert_id="backup_health_disk_usage",
                        alert_type="SYSTEM_WARNING",
                        severity="LOW",
                        title="Alto Uso de Disco para Backups",
                        message=f"Backups estão usando {total_size_gb:.2f}GB de espaço",
                        data={
                            "disk_usage_gb": total_size_gb,
                            "total_backups": status.get("total_backups"),
                        },
                    )

            logger.info("Backup health check completed")

        except Exception as e:
            logger.error(f"Backup health check failed: {e}")

    async def _cleanup_logs(self):
        """Limpeza de logs antigos"""
        try:
            logger.info("Starting log cleanup...")

            logs_dir = Path("/app/logs")
            if not logs_dir.exists():
                return

            # Limpar logs de backup mais antigos que 7 dias
            cutoff_date = datetime.now() - timedelta(days=7)

            for log_file in logs_dir.glob("backup*.log*"):
                if log_file.is_file():
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file.name}")

            # Limpar histórico de execuções antigo
            if len(self.execution_history) > self.max_history_size:
                removed = len(self.execution_history) - self.max_history_size
                self.execution_history = self.execution_history[
                    -self.max_history_size :
                ]
                logger.info(f"Cleaned {removed} old execution records")

            logger.info("Log cleanup completed")

        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")

    def _add_to_history(self, execution_record: Dict):
        """Adicionar registro ao histórico"""
        self.execution_history.append(execution_record)

        # Manter apenas os últimos registros
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size :]

    def _has_recent_failures(self) -> bool:
        """Verificar se houve falhas recentes"""
        if len(self.execution_history) < 2:
            return False

        # Verificar últimas 3 execuções
        recent_executions = self.execution_history[-3:]
        failures = [
            exec for exec in recent_executions if not exec.get("success", False)
        ]

        return len(failures) > 0

    def _job_executed(self, event):
        """Callback para job executado com sucesso"""
        logger.debug(f"Job executed: {event.job_id}")

    def _job_error(self, event):
        """Callback para erro em job"""
        logger.error(f"Job failed: {event.job_id} - {event.exception}")

    async def get_status(self) -> Dict:
        """Obter status do agendador"""
        try:
            jobs_info = []

            for job in self.scheduler.get_jobs():
                next_run = job.next_run_time
                jobs_info.append(
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run": next_run.isoformat() if next_run else None,
                        "trigger": str(job.trigger),
                    }
                )

            return {
                "is_running": self.is_running,
                "backup_schedule": self.backup_schedule,
                "health_check_interval_hours": self.health_check_interval,
                "jobs": jobs_info,
                "execution_history_size": len(self.execution_history),
                "recent_executions": (
                    self.execution_history[-5:] if self.execution_history else []
                ),
                "last_execution": (
                    self.execution_history[-1] if self.execution_history else None
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get scheduler status: {e}")
            return {"error": str(e)}

    async def execute_backup_now(self) -> Dict:
        """Executar backup manualmente"""
        try:
            logger.info("Manual backup execution requested")

            # Executar em background para não bloquear
            task = asyncio.create_task(self._execute_backup_routine())

            return {
                "success": True,
                "message": "Backup started in background",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Manual backup execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Instância global do agendador
backup_scheduler = BackupScheduler()
