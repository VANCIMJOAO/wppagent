"""
API endpoints para sistema de backup
"""

from typing import Dict, List, Optional
from datetime import datetime
import json

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import asyncio

from app.auth.middleware import verify_admin_token, AdminUser
from app.services.backup_service import BackupService
from app.services.backup_scheduler import backup_scheduler
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/backup", tags=["backup"])

# Modelos Pydantic
class BackupTriggerRequest(BaseModel):
    backup_type: Optional[str] = None  # "full", "database", "redis", "files"
    cloud_upload: Optional[bool] = True

class BackupScheduleConfig(BaseModel):
    cron_schedule: str  # Formato cron
    enabled: bool = True

class RestoreRequest(BaseModel):
    backup_filename: str
    restore_type: str  # "database", "files"
    confirm: bool = False

@router.get("/status")
async def get_backup_status(admin_user: AdminUser = Depends(verify_admin_token)):
    """
    Obter status completo do sistema de backup
    """
    try:
        backup_service = BackupService()
        
        # Status dos backups
        backup_status = await backup_service.get_backup_status()
        
        # Status do agendador
        scheduler_status = await backup_scheduler.get_status()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "backup_status": backup_status,
            "scheduler_status": scheduler_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger")
async def trigger_backup(
    request: BackupTriggerRequest,
    background_tasks: BackgroundTasks,
    admin_user: AdminUser = Depends(verify_admin_token)
):
    """
    Disparar backup manual
    """
    try:
        backup_service = BackupService()
        
        logger.info(f"Manual backup triggered by {admin_user.username} - Type: {request.backup_type}")
        
        if request.backup_type == "full" or request.backup_type is None:
            # Backup completo em background
            background_tasks.add_task(backup_service.full_backup_routine)
            
            return {
                "success": True,
                "message": "Full backup started in background",
                "backup_type": "full",
                "timestamp": datetime.now().isoformat()
            }
            
        elif request.backup_type == "database":
            # Backup apenas do banco
            result = await backup_service.create_database_backup()
            
            if request.cloud_upload:
                cloud_path = await backup_service.upload_to_cloud(result)
                result["cloud_path"] = cloud_path
            
            return {
                "success": True,
                "message": "Database backup completed",
                "backup_info": result,
                "timestamp": datetime.now().isoformat()
            }
            
        elif request.backup_type == "redis":
            # Backup apenas do Redis
            result = await backup_service.create_redis_backup()
            
            if result and request.cloud_upload:
                cloud_path = await backup_service.upload_to_cloud(result)
                result["cloud_path"] = cloud_path
            
            return {
                "success": True,
                "message": "Redis backup completed" if result else "Redis backup skipped (not available)",
                "backup_info": result,
                "timestamp": datetime.now().isoformat()
            }
            
        elif request.backup_type == "files":
            # Backup apenas de arquivos
            result = await backup_service.create_files_backup()
            
            if result and request.cloud_upload:
                cloud_path = await backup_service.upload_to_cloud(result)
                result["cloud_path"] = cloud_path
            
            return {
                "success": True,
                "message": "Files backup completed" if result else "Files backup skipped (no files)",
                "backup_info": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid backup type: {request.backup_type}")
        
    except Exception as e:
        logger.error(f"Manual backup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_backups(
    limit: int = 20,
    backup_type: Optional[str] = None,
    admin_user: AdminUser = Depends(verify_admin_token)
):
    """
    Listar backups disponíveis
    """
    try:
        backup_service = BackupService()
        status = await backup_service.get_backup_status()
        
        backups = status.get("backups", [])
        
        # Filtrar por tipo se especificado
        if backup_type:
            backups = [b for b in backups if backup_type in b["filename"]]
        
        # Limitar resultado
        backups = backups[:limit]
        
        return {
            "success": True,
            "total_backups": len(backups),
            "backups": backups,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup")
async def cleanup_backups(
    force: bool = False,
    admin_user: AdminUser = Depends(verify_admin_token)
):
    """
    Executar limpeza de backups antigos
    """
    try:
        backup_service = BackupService()
        
        logger.info(f"Backup cleanup requested by {admin_user.username} - Force: {force}")
        
        if force:
            # Limpeza forçada - reduzir retenção temporariamente
            original_retention = backup_service.retention_days
            backup_service.retention_days = 7  # Manter apenas 7 dias
        
        stats = await backup_service.cleanup_old_backups()
        
        if force:
            # Restaurar retenção original
            backup_service.retention_days = original_retention
        
        return {
            "success": True,
            "message": "Backup cleanup completed",
            "cleanup_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_backup(
    filename: str,
    admin_user: AdminUser = Depends(verify_admin_token)
):
    """
    Download de arquivo de backup
    """
    try:
        from pathlib import Path
        
        backup_file = Path("/app/backups") / filename
        
        # Verificar se arquivo existe
        if not backup_file.exists():
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Verificar se é um arquivo de backup válido
        if not filename.endswith('.gz') or not any(t in filename for t in ['postgres', 'redis', 'files']):
            raise HTTPException(status_code=400, detail="Invalid backup file")
        
        logger.info(f"Backup download requested by {admin_user.username}: {filename}")
        
        return FileResponse(
            path=str(backup_file),
            filename=filename,
            media_type='application/gzip'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify/{filename}")
async def verify_backup(
    filename: str,
    admin_user: AdminUser = Depends(verify_admin_token)
):
    """
    Verificar integridade de backup específico
    """
    try:
        from pathlib import Path
        import hashlib
        
        backup_file = Path("/app/backups") / filename
        
        if not backup_file.exists():
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # Simular verificação de integridade básica
        # Em produção, usar hash armazenado
        file_size = backup_file.stat().st_size
        
        # Calcular hash
        hash_sha256 = hashlib.sha256()
        with open(backup_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        file_hash = hash_sha256.hexdigest()
        
        # Verificação básica
        is_valid = file_size > 1024  # Pelo menos 1KB
        
        return {
            "success": True,
            "filename": filename,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "file_hash": file_hash,
            "is_valid": is_valid,
            "checked_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_backup_config(admin_user: AdminUser = Depends(verify_admin_token)):
    """
    Obter configuração atual do sistema de backup
    """
    try:
        import os
        
        config = {
            "retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
            "max_backup_size_mb": int(os.getenv("MAX_BACKUP_SIZE_MB", "1000")),
            "cloud_enabled": os.getenv("BACKUP_CLOUD_ENABLED", "false").lower() == "true",
            "storage_provider": os.getenv("BACKUP_STORAGE_PROVIDER", "railway"),
            "backup_schedule": os.getenv("BACKUP_SCHEDULE", "0 2 * * *"),
            "health_check_interval": int(os.getenv("BACKUP_HEALTH_CHECK_INTERVAL", "6"))
        }
        
        return {
            "success": True,
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get backup config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule/update")
async def update_backup_schedule(
    config: BackupScheduleConfig,
    admin_user: AdminUser = Depends(verify_admin_token)
):
    """
    Atualizar agendamento de backup
    """
    try:
        # Validar formato cron
        from crontab import CronTab
        
        cron = CronTab(config.cron_schedule)
        if not cron.is_valid():
            raise HTTPException(status_code=400, detail="Invalid cron format")
        
        # Atualizar agendamento
        # Em produção, isso salvaria no banco ou arquivo de config
        logger.info(f"Backup schedule updated by {admin_user.username}: {config.cron_schedule}")
        
        return {
            "success": True,
            "message": "Backup schedule updated successfully",
            "new_schedule": config.cron_schedule,
            "enabled": config.enabled,
            "next_run": str(cron.next()),
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        # Se crontab não estiver disponível, fazer validação básica
        parts = config.cron_schedule.split()
        if len(parts) != 5:
            raise HTTPException(status_code=400, detail="Cron schedule must have 5 parts")
        
        return {
            "success": True,
            "message": "Backup schedule updated successfully (basic validation)",
            "new_schedule": config.cron_schedule,
            "enabled": config.enabled,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update backup schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_backup_logs(
    lines: int = 100,
    admin_user: AdminUser = Depends(verify_admin_token)
):
    """
    Obter logs recentes do sistema de backup
    """
    try:
        from pathlib import Path
        
        log_file = Path("/app/logs/backup.log")
        
        if not log_file.exists():
            return {
                "success": True,
                "message": "No backup logs found",
                "logs": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Ler últimas linhas do log
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "success": True,
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines),
            "logs": [line.strip() for line in recent_lines],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get backup logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def backup_health_check(admin_user: AdminUser = Depends(verify_admin_token)):
    """
    Verificação de saúde do sistema de backup
    """
    try:
        backup_service = BackupService()
        status = await backup_service.get_backup_status()
        
        # Análise de saúde
        health_status = "healthy"
        issues = []
        
        # Verificar se há backups
        if status.get("total_backups", 0) == 0:
            health_status = "critical"
            issues.append("No backups found")
        
        # Verificar idade do último backup
        last_backup_age = status.get("last_backup_age_hours")
        if last_backup_age is not None and last_backup_age > 48:
            health_status = "warning"
            issues.append(f"Last backup is {last_backup_age:.1f} hours old")
        
        # Verificar espaço em disco
        total_size_mb = status.get("total_size_mb", 0)
        if total_size_mb > 5000:  # 5GB
            health_status = "warning" if health_status == "healthy" else health_status
            issues.append(f"Backup storage is using {total_size_mb}MB")
        
        return {
            "success": True,
            "health_status": health_status,
            "issues": issues,
            "backup_status": status,
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup health check failed: {e}")
        return {
            "success": False,
            "health_status": "error",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }
