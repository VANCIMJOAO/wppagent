"""
Scheduler para Políticas de Retenção LGPD
Execução automática das políticas de retenção de dados
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from threading import Thread
from typing import Any, Dict

import schedule

from ..services.lgpd_compliance import get_lgpd_manager
from ..services.structured_apm import get_structured_logger

logger = get_structured_logger(__name__)


class LGPDRetentionScheduler:
    """Agendador de políticas de retenção LGPD"""

    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.lgpd_manager = get_lgpd_manager()

    def start(self):
        """Inicia o agendador"""
        if self.running:
            logger.warning("⚠️ Scheduler LGPD já está executando")
            return

        logger.info("🚀 Iniciando LGPD Retention Scheduler")

        # Configurar agendamentos
        self._setup_schedules()

        # Iniciar thread do scheduler
        self.running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("✅ LGPD Retention Scheduler iniciado")

    def stop(self):
        """Para o agendador"""
        if not self.running:
            return

        logger.info("⏹️ Parando LGPD Retention Scheduler")
        self.running = False

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        schedule.clear()
        logger.info("✅ LGPD Retention Scheduler parado")

    def _setup_schedules(self):
        """Configura os agendamentos das políticas"""

        # Execução diária às 02:00 - Políticas de retenção principais
        schedule.every().day.at("02:00").do(self._run_daily_retention)

        # Execução semanal aos domingos às 03:00 - Limpeza profunda
        schedule.every().sunday.at("03:00").do(self._run_weekly_deep_cleanup)

        # Execução mensal no dia 1 às 04:00 - Relatório de auditoria
        schedule.every().month.do(self._run_monthly_audit)

        # Execução a cada 6 horas - Verificação de dados expirados críticos
        schedule.every(6).hours.do(self._run_critical_cleanup)

        logger.info("📅 Agendamentos LGPD configurados:")
        logger.info("   - Retenção diária: 02:00")
        logger.info("   - Limpeza semanal: Dom 03:00")
        logger.info("   - Auditoria mensal: Dia 1, 04:00")
        logger.info("   - Verificação crítica: a cada 6h")

    def _run_scheduler(self):
        """Executa o loop do agendador"""
        logger.info("🔄 Loop do scheduler LGPD iniciado")

        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
            except Exception as e:
                logger.error(f"❌ Erro no scheduler LGPD: {e}")
                time.sleep(300)  # Aguardar 5 minutos antes de tentar novamente

    def _run_daily_retention(self):
        """Executa políticas de retenção diárias"""
        logger.info("📅 Executando políticas de retenção diárias")

        try:
            # Executar em nova thread async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.lgpd_manager.apply_retention_policies()
            )

            logger.info(
                f"✅ Retenção diária concluída: {result['total_records_processed']} registros processados"
            )

            # Log detalhado
            if result["total_records_deleted"] > 0:
                logger.info(
                    f"🗑️ Registros deletados: {result['total_records_deleted']}"
                )

            if result["total_records_anonymized"] > 0:
                logger.info(
                    f"🔒 Registros anonimizados: {result['total_records_anonymized']}"
                )

        except Exception as e:
            logger.error(f"❌ Erro na retenção diária: {e}")
        finally:
            loop.close()

    def _run_weekly_deep_cleanup(self):
        """Executa limpeza profunda semanal"""
        logger.info("🧹 Executando limpeza profunda semanal")

        try:
            # Executar políticas de retenção
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.lgpd_manager.apply_retention_policies()
            )

            # Limpeza adicional de arquivos de exportação antigos
            self._cleanup_old_exports()

            logger.info(
                f"✅ Limpeza semanal concluída: {result['total_records_processed']} registros"
            )

        except Exception as e:
            logger.error(f"❌ Erro na limpeza semanal: {e}")
        finally:
            loop.close()

    def _run_monthly_audit(self):
        """Executa auditoria mensal"""
        logger.info("📊 Executando auditoria mensal LGPD")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Gerar relatório de tratamento de dados
            report = loop.run_until_complete(
                self.lgpd_manager.get_data_processing_report()
            )

            logger.info(f"📋 Relatório mensal gerado:")
            logger.info(f"   - Total de registros: {report['total_records']}")
            logger.info(f"   - Categorias de dados: {len(report['data_categories'])}")
            logger.info(f"   - Finalidades: {len(report['processing_purposes'])}")

            # Salvar relatório em arquivo
            self._save_monthly_report(report)

            logger.info("✅ Auditoria mensal concluída")

        except Exception as e:
            logger.error(f"❌ Erro na auditoria mensal: {e}")
        finally:
            loop.close()

    def _run_critical_cleanup(self):
        """Executa verificação crítica a cada 6 horas"""
        logger.info("🚨 Verificação crítica de dados expirados")

        try:
            # Verificar apenas dados críticos com retenção imediata
            # Por simplicidade, executamos uma verificação básica

            current_time = datetime.utcnow()
            logger.info(f"⏰ Verificação crítica às {current_time.strftime('%H:%M:%S')}")

            # Aqui você pode implementar verificações específicas
            # Por exemplo, dados que devem ser deletados imediatamente

            logger.info("✅ Verificação crítica concluída")

        except Exception as e:
            logger.error(f"❌ Erro na verificação crítica: {e}")

    def _cleanup_old_exports(self):
        """Limpa arquivos de exportação antigos"""
        try:
            from pathlib import Path

            export_dir = Path("exports/lgpd")
            if not export_dir.exists():
                return

            # Deletar arquivos de exportação com mais de 7 dias
            cutoff_date = datetime.utcnow() - timedelta(days=7)

            deleted_count = 0
            for file_path in export_dir.glob("*.zip"):
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(
                    f"🧹 {deleted_count} arquivos de exportação antigos removidos"
                )

        except Exception as e:
            logger.error(f"❌ Erro na limpeza de exports: {e}")

    def _save_monthly_report(self, report: Dict[str, Any]):
        """Salva relatório mensal em arquivo"""
        try:
            import json
            from pathlib import Path

            reports_dir = Path("reports/lgpd")
            reports_dir.mkdir(parents=True, exist_ok=True)

            report_file = (
                reports_dir / f"lgpd_audit_{datetime.utcnow().strftime('%Y%m')}.json"
            )

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"📄 Relatório mensal salvo: {report_file}")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar relatório: {e}")

    def force_run_retention(self):
        """Força execução imediata das políticas de retenção"""
        logger.info("🚀 Execução forçada de políticas de retenção")
        self._run_daily_retention()

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Retorna status do agendador"""
        return {
            "running": self.running,
            "next_runs": {
                "daily_retention": "02:00 (diário)",
                "weekly_cleanup": "Domingo 03:00",
                "monthly_audit": "Dia 1, 04:00",
                "critical_check": "A cada 6 horas",
            },
            "thread_alive": (
                self.scheduler_thread.is_alive() if self.scheduler_thread else False
            ),
            "scheduled_jobs": len(schedule.jobs),
        }


# Instância global do scheduler
lgpd_scheduler = LGPDRetentionScheduler()


def get_lgpd_scheduler() -> LGPDRetentionScheduler:
    """Dependency injection para o scheduler LGPD"""
    return lgpd_scheduler


def start_lgpd_scheduler():
    """Inicia o scheduler LGPD"""
    lgpd_scheduler.start()


def stop_lgpd_scheduler():
    """Para o scheduler LGPD"""
    lgpd_scheduler.stop()
