"""
Serviço de Backup Automatizado para WppAgent
Gerencia backup de PostgreSQL, Redis e upload para cloud storage
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from app.config import get_settings
from app.services.alert_system import alert_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)
config = get_settings()


class BackupService:
    """
    Serviço principal para gerenciar backups automatizados

    Funcionalidades:
    - Backup PostgreSQL via pg_dump
    - Backup Redis via redis-cli
    - Compressão automática
    - Upload para cloud storage
    - Verificação de integridade
    - Limpeza de backups antigos
    - Alertas em caso de falha
    """

    def __init__(self):
        # Usar diretório relativo em desenvolvimento, absoluto em produção
        if os.getenv("RAILWAY_ENVIRONMENT_NAME"):
            self.backup_dir = Path("/app/backups")
        else:
            # Ambiente de desenvolvimento
            self.backup_dir = Path("./backups")

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Configurações
        self.retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
        self.max_backup_size = (
            int(os.getenv("MAX_BACKUP_SIZE_MB", "1000")) * 1024 * 1024
        )  # MB to bytes

        # Cloud storage (será implementado baseado no ambiente)
        self.cloud_enabled = (
            os.getenv("BACKUP_CLOUD_ENABLED", "false").lower() == "true"
        )
        self.storage_provider = os.getenv(
            "BACKUP_STORAGE_PROVIDER", "railway"
        )  # railway, s3, gcp

        logger.info(
            f"BackupService initialized - Retention: {self.retention_days} days, Cloud: {self.cloud_enabled}"
        )

    async def get_database_url(self) -> str:
        """Obter URL do banco de dados"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not configured")
        return database_url

    async def create_database_backup(self) -> Dict[str, str]:
        """
        Criar backup do PostgreSQL

        Returns:
            Dict com informações do backup criado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"postgres_backup_{timestamp}.sql"
        backup_file = self.backup_dir / backup_filename
        compressed_file = self.backup_dir / f"{backup_filename}.gz"

        try:
            logger.info("Starting PostgreSQL backup...")

            database_url = await self.get_database_url()

            # Executar pg_dump
            process = await asyncio.create_subprocess_exec(
                "pg_dump",
                database_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown pg_dump error"
                raise Exception(
                    f"pg_dump failed with code {process.returncode}: {error_msg}"
                )

            # Salvar arquivo SQL
            backup_file.write_bytes(stdout)

            # Verificar se o backup não está vazio
            if backup_file.stat().st_size < 1024:  # Menos de 1KB é suspeito
                raise Exception("Backup file is too small, likely empty or corrupted")

            # Compactar
            await self._compress_file(backup_file, compressed_file)
            backup_file.unlink()  # Remover arquivo não compactado

            # Calcular hash para verificação de integridade
            file_hash = await self._calculate_file_hash(compressed_file)

            backup_info = {
                "type": "postgresql",
                "filename": compressed_file.name,
                "filepath": str(compressed_file),
                "size_bytes": compressed_file.stat().st_size,
                "size_mb": round(compressed_file.stat().st_size / (1024 * 1024), 2),
                "hash": file_hash,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
            }

            logger.info(
                f"PostgreSQL backup created successfully: {backup_info['filename']} ({backup_info['size_mb']} MB)"
            )
            return backup_info

        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}")

            # Limpar arquivos parciais
            if backup_file.exists():
                backup_file.unlink()
            if compressed_file.exists():
                compressed_file.unlink()

            raise

    async def create_redis_backup(self) -> Optional[Dict[str, str]]:
        """
        Criar backup do Redis (se disponível)

        Returns:
            Dict com informações do backup criado ou None se Redis não disponível
        """
        try:
            # Verificar se Redis está disponível
            test_process = await asyncio.create_subprocess_exec(
                "redis-cli",
                "ping",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await test_process.communicate()

            if test_process.returncode != 0 or b"PONG" not in stdout:
                logger.warning("Redis not available, skipping Redis backup")
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"redis_backup_{timestamp}.rdb"
            backup_file = self.backup_dir / backup_filename
            compressed_file = self.backup_dir / f"{backup_filename}.gz"

            logger.info("Starting Redis backup...")

            # Executar BGSAVE para criar snapshot
            save_process = await asyncio.create_subprocess_exec(
                "redis-cli",
                "BGSAVE",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await save_process.communicate()

            # Aguardar conclusão do BGSAVE
            await asyncio.sleep(2)

            # Copiar arquivo RDB
            copy_process = await asyncio.create_subprocess_exec(
                "redis-cli",
                "--rdb",
                str(backup_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await copy_process.communicate()

            if copy_process.returncode != 0 or not backup_file.exists():
                logger.warning("Redis backup failed or file not created")
                return None

            # Compactar
            await self._compress_file(backup_file, compressed_file)
            backup_file.unlink()

            # Calcular hash
            file_hash = await self._calculate_file_hash(compressed_file)

            backup_info = {
                "type": "redis",
                "filename": compressed_file.name,
                "filepath": str(compressed_file),
                "size_bytes": compressed_file.stat().st_size,
                "size_mb": round(compressed_file.stat().st_size / (1024 * 1024), 2),
                "hash": file_hash,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
            }

            logger.info(
                f"Redis backup created successfully: {backup_info['filename']} ({backup_info['size_mb']} MB)"
            )
            return backup_info

        except Exception as e:
            logger.warning(f"Redis backup failed: {e}")
            return None

    async def create_files_backup(self) -> Dict[str, str]:
        """
        Criar backup de arquivos importantes (logs, configurações, uploads)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"files_backup_{timestamp}.tar.gz"
        backup_file = self.backup_dir / backup_filename

        try:
            logger.info("Starting files backup...")

            # Diretórios para backup
            backup_paths = [
                "/app/logs",
                "/app/config",
                "/app/static/uploads",
                "/app/secrets",
            ]

            # Filtrar apenas diretórios que existem
            existing_paths = [path for path in backup_paths if Path(path).exists()]

            if not existing_paths:
                logger.warning("No files to backup")
                return None

            # Criar tar.gz
            cmd = ["tar", "-czf", str(backup_file)] + existing_paths

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown tar error"
                raise Exception(f"tar command failed: {error_msg}")

            # Calcular hash
            file_hash = await self._calculate_file_hash(backup_file)

            backup_info = {
                "type": "files",
                "filename": backup_file.name,
                "filepath": str(backup_file),
                "size_bytes": backup_file.stat().st_size,
                "size_mb": round(backup_file.stat().st_size / (1024 * 1024), 2),
                "hash": file_hash,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "paths_included": existing_paths,
            }

            logger.info(
                f"Files backup created successfully: {backup_info['filename']} ({backup_info['size_mb']} MB)"
            )
            return backup_info

        except Exception as e:
            logger.error(f"Files backup failed: {e}")

            if backup_file.exists():
                backup_file.unlink()

            raise

    async def upload_to_cloud(self, backup_info: Dict[str, str]) -> Optional[str]:
        """
        Upload backup para cloud storage

        Args:
            backup_info: Informações do backup

        Returns:
            URL ou path do arquivo no cloud storage
        """
        if not self.cloud_enabled:
            logger.info("Cloud storage disabled, skipping upload")
            return None

        try:
            filepath = backup_info["filepath"]

            if self.storage_provider == "railway":
                return await self._upload_to_railway_volumes(filepath, backup_info)
            elif self.storage_provider == "s3":
                return await self._upload_to_s3(filepath, backup_info)
            elif self.storage_provider == "gcp":
                return await self._upload_to_gcp(filepath, backup_info)
            else:
                logger.warning(f"Unsupported storage provider: {self.storage_provider}")
                return None

        except Exception as e:
            logger.error(f"Cloud upload failed: {e}")
            raise

    async def _upload_to_railway_volumes(self, filepath: str, backup_info: Dict) -> str:
        """Upload para Railway Volumes"""
        cloud_dir = Path("/app/backup_storage")
        cloud_dir.mkdir(parents=True, exist_ok=True)

        cloud_file = cloud_dir / Path(filepath).name
        shutil.copy2(filepath, cloud_file)

        logger.info(f"Backup uploaded to Railway volume: {cloud_file}")
        return str(cloud_file)

    async def _upload_to_s3(self, filepath: str, backup_info: Dict) -> str:
        """Upload para Amazon S3 (placeholder)"""
        # Implementar quando necessário
        logger.info("S3 upload not implemented yet")
        return None

    async def _upload_to_gcp(self, filepath: str, backup_info: Dict) -> str:
        """Upload para Google Cloud Storage (placeholder)"""
        # Implementar quando necessário
        logger.info("GCP upload not implemented yet")
        return None

    async def verify_backup_integrity(self, backup_info: Dict[str, str]) -> bool:
        """
        Verificar integridade do backup

        Args:
            backup_info: Informações do backup

        Returns:
            True se backup está íntegro
        """
        try:
            filepath = backup_info["filepath"]
            expected_hash = backup_info["hash"]

            if not Path(filepath).exists():
                logger.error(f"Backup file does not exist: {filepath}")
                return False

            # Recalcular hash
            actual_hash = await self._calculate_file_hash(Path(filepath))

            if actual_hash != expected_hash:
                logger.error(f"Backup integrity check failed: {filepath}")
                logger.error(f"Expected: {expected_hash}, Got: {actual_hash}")
                return False

            logger.info(f"Backup integrity verified: {Path(filepath).name}")
            return True

        except Exception as e:
            logger.error(f"Backup integrity verification failed: {e}")
            return False

    async def cleanup_old_backups(self) -> Dict[str, int]:
        """
        Remover backups antigos baseado na política de retenção

        Returns:
            Dict com estatísticas da limpeza
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        stats = {"files_checked": 0, "files_deleted": 0, "bytes_freed": 0}

        try:
            logger.info(
                f"Starting cleanup of backups older than {self.retention_days} days"
            )

            for file in self.backup_dir.glob("*.gz"):
                stats["files_checked"] += 1

                file_mtime = datetime.fromtimestamp(file.stat().st_mtime)

                if file_mtime < cutoff_date:
                    file_size = file.stat().st_size
                    file.unlink()

                    stats["files_deleted"] += 1
                    stats["bytes_freed"] += file_size

                    logger.info(f"Deleted old backup: {file.name}")

            # Também limpar cloud storage se habilitado
            if self.cloud_enabled:
                await self._cleanup_cloud_backups(cutoff_date)

            stats["mb_freed"] = round(stats["bytes_freed"] / (1024 * 1024), 2)

            logger.info(
                f"Cleanup completed - Deleted: {stats['files_deleted']} files, Freed: {stats['mb_freed']} MB"
            )
            return stats

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            raise

    async def _cleanup_cloud_backups(self, cutoff_date: datetime):
        """Limpar backups antigos no cloud storage"""
        if self.storage_provider == "railway":
            cloud_dir = Path("/app/backup_storage")
            if cloud_dir.exists():
                for file in cloud_dir.glob("*.gz"):
                    file_mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file.unlink()
                        logger.info(f"Deleted old cloud backup: {file.name}")

    async def get_backup_status(self) -> Dict:
        """
        Obter status atual dos backups

        Returns:
            Dict com estatísticas e status
        """
        try:
            backups = []
            total_size = 0

            for file in sorted(
                self.backup_dir.glob("*.gz"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            ):
                stat = file.stat()
                backups.append(
                    {
                        "filename": file.name,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "age_days": (
                            datetime.now() - datetime.fromtimestamp(stat.st_mtime)
                        ).days,
                    }
                )
                total_size += stat.st_size

            # Verificar último backup
            last_backup = backups[0] if backups else None
            last_backup_age = None

            if last_backup:
                last_backup_time = datetime.fromisoformat(last_backup["created_at"])
                last_backup_age = (
                    datetime.now() - last_backup_time
                ).total_seconds() / 3600  # horas

            status = {
                "total_backups": len(backups),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "last_backup_age_hours": (
                    round(last_backup_age, 2) if last_backup_age else None
                ),
                "retention_days": self.retention_days,
                "cloud_enabled": self.cloud_enabled,
                "storage_provider": self.storage_provider,
                "backups": backups[:10],  # Últimos 10
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return {"error": str(e)}

    async def full_backup_routine(self) -> Dict[str, any]:
        """
        Executar rotina completa de backup

        Returns:
            Dict com resultado da operação
        """
        start_time = datetime.now()
        results = {
            "started_at": start_time.isoformat(),
            "success": False,
            "backups_created": [],
            "cloud_uploads": [],
            "errors": [],
            "cleanup_stats": None,
        }

        try:
            logger.info("Starting full backup routine...")

            # 1. Backup PostgreSQL
            try:
                db_backup = await self.create_database_backup()
                results["backups_created"].append(db_backup)

                # Verificar integridade
                if not await self.verify_backup_integrity(db_backup):
                    raise Exception("PostgreSQL backup integrity check failed")

                # Upload para cloud
                if self.cloud_enabled:
                    cloud_path = await self.upload_to_cloud(db_backup)
                    if cloud_path:
                        results["cloud_uploads"].append(
                            {
                                "type": "postgresql",
                                "local_file": db_backup["filename"],
                                "cloud_path": cloud_path,
                            }
                        )

            except Exception as e:
                error_msg = f"PostgreSQL backup failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

            # 2. Backup Redis
            try:
                redis_backup = await self.create_redis_backup()
                if redis_backup:
                    results["backups_created"].append(redis_backup)

                    if not await self.verify_backup_integrity(redis_backup):
                        raise Exception("Redis backup integrity check failed")

                    if self.cloud_enabled:
                        cloud_path = await self.upload_to_cloud(redis_backup)
                        if cloud_path:
                            results["cloud_uploads"].append(
                                {
                                    "type": "redis",
                                    "local_file": redis_backup["filename"],
                                    "cloud_path": cloud_path,
                                }
                            )

            except Exception as e:
                error_msg = f"Redis backup failed: {e}"
                logger.warning(error_msg)
                results["errors"].append(error_msg)

            # 3. Backup Files
            try:
                files_backup = await self.create_files_backup()
                if files_backup:
                    results["backups_created"].append(files_backup)

                    if not await self.verify_backup_integrity(files_backup):
                        raise Exception("Files backup integrity check failed")

                    if self.cloud_enabled:
                        cloud_path = await self.upload_to_cloud(files_backup)
                        if cloud_path:
                            results["cloud_uploads"].append(
                                {
                                    "type": "files",
                                    "local_file": files_backup["filename"],
                                    "cloud_path": cloud_path,
                                }
                            )

            except Exception as e:
                error_msg = f"Files backup failed: {e}"
                logger.warning(error_msg)
                results["errors"].append(error_msg)

            # 4. Cleanup backups antigos
            try:
                cleanup_stats = await self.cleanup_old_backups()
                results["cleanup_stats"] = cleanup_stats
            except Exception as e:
                error_msg = f"Backup cleanup failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

            # 5. Determinar sucesso geral
            results["success"] = len(results["backups_created"]) > 0
            results["duration_minutes"] = round(
                (datetime.now() - start_time).total_seconds() / 60, 2
            )
            results["completed_at"] = datetime.now().isoformat()

            if results["success"]:
                logger.info(
                    f"Full backup routine completed successfully in {results['duration_minutes']} minutes"
                )
                logger.info(
                    f"Created {len(results['backups_created'])} backups, {len(results['cloud_uploads'])} cloud uploads"
                )
            else:
                logger.error("Full backup routine failed - no backups created")

            return results

        except Exception as e:
            error_msg = f"Full backup routine failed: {e}"
            logger.error(error_msg)

            results["errors"].append(error_msg)
            results["completed_at"] = datetime.now().isoformat()
            results["duration_minutes"] = round(
                (datetime.now() - start_time).total_seconds() / 60, 2
            )

            # Enviar alerta crítico
            try:
                await alert_manager.create_alert(
                    alert_id="backup_routine_failed",
                    alert_type="SYSTEM_ERROR",
                    severity="CRITICAL",
                    title="Rotina de Backup Falhou",
                    message=f"A rotina de backup automatizada falhou: {error_msg}",
                    data=results,
                )
            except Exception as alert_error:
                logger.error(f"Failed to send backup failure alert: {alert_error}")

            return results

    # Métodos auxiliares
    async def _compress_file(self, source_file: Path, target_file: Path):
        """Compactar arquivo usando gzip"""
        with open(source_file, "rb") as f_in:
            with gzip.open(target_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcular hash SHA-256 do arquivo"""
        hash_sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()
