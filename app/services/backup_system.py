"""
Sistema de Backup Automatizado do Banco de Dados
===============================================

Implementa backup automatizado com:
- Backup incremental e completo
- Rotação automática de backups
- Compressão e validação
- Restore automático
- Monitoramento do estado dos backups
"""

import os
import asyncio
import subprocess
import gzip
import shutil
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import schedule
import time
from concurrent.futures import ThreadPoolExecutor

from app.services.production_logger import business_logger
from app.utils.logger import get_logger
from app.services.automated_alerts import alert_manager, AlertSeverity, AlertCategory
logger = get_logger(__name__)
from app.config import settings


@dataclass
class BackupInfo:
    """Informações de um backup"""
    filename: str
    filepath: str
    backup_type: str  # 'full' ou 'incremental'
    timestamp: datetime
    size_bytes: int
    compressed: bool
    checksum: str
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'filename': self.filename,
            'filepath': self.filepath,
            'backup_type': self.backup_type,
            'timestamp': self.timestamp.isoformat(),
            'size_bytes': self.size_bytes,
            'size_mb': round(self.size_bytes / (1024**2), 2),
            'compressed': self.compressed,
            'checksum': self.checksum,
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'error_message': self.error_message
        }


class DatabaseBackupManager:
    """
    Gerenciador de backup automatizado do banco de dados
    """
    
    def __init__(self, 
                 backup_dir: str = "backups",
                 max_backups: int = 30,
                 compress_backups: bool = True):
        
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_backups = max_backups
        self.compress_backups = compress_backups
        
        # Configurações do banco
        self.db_config = {
            'host': getattr(settings, 'database_host', 'localhost'),
            'port': getattr(settings, 'database_port', 5432),
            'database': getattr(settings, 'database_name', 'whatsapp_agent'),
            'username': getattr(settings, 'database_user', 'postgres'),
            'password': getattr(settings, 'database_password', '')
        }
        
        # Histórico de backups
        self.backup_history: List[BackupInfo] = []
        self.load_backup_history()
        
        # Executor para operações bloqueantes
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Status do último backup
        self.last_backup_status = None
    
    def load_backup_history(self):
        """Carregar histórico de backups"""
        try:
            history_file = self.backup_dir / "backup_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for item in data:
                    backup_info = BackupInfo(
                        filename=item['filename'],
                        filepath=item['filepath'],
                        backup_type=item['backup_type'],
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        size_bytes=item['size_bytes'],
                        compressed=item['compressed'],
                        checksum=item['checksum'],
                        duration_seconds=item['duration_seconds'],
                        success=item['success'],
                        error_message=item.get('error_message')
                    )
                    self.backup_history.append(backup_info)
                    
        except Exception as e:
            business_logger.error(f"Error loading backup history: {e}", exc_info=True)
    
    def save_backup_history(self):
        """Salvar histórico de backups"""
        try:
            history_file = self.backup_dir / "backup_history.json"
            data = [backup.to_dict() for backup in self.backup_history]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            business_logger.error(f"Error saving backup history: {e}", exc_info=True)
    
    def _calculate_checksum(self, filepath: str) -> str:
        """Calcular checksum MD5 do arquivo"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _compress_file(self, input_path: str, output_path: str) -> bool:
        """Comprimir arquivo com gzip"""
        try:
            with open(input_path, 'rb') as f_in:
                with gzip.open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remover arquivo original
            os.remove(input_path)
            return True
            
        except Exception as e:
            business_logger.error(f"Error compressing backup: {e}", exc_info=True)
            return False
    
    async def create_full_backup(self) -> BackupInfo:
        """Criar backup completo do banco de dados"""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        filename = f"full_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.sql"
        filepath = self.backup_dir / filename
        
        try:
            business_logger.info("Starting full database backup")
            
            # Comando pg_dump
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['username'],
                '-d', self.db_config['database'],
                '--verbose',
                '--no-password',
                '-f', str(filepath)
            ]
            
            # Configurar variável de ambiente para senha
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # Executar backup
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                lambda: subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hora timeout
                )
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Backup bem-sucedido
                file_size = os.path.getsize(filepath)
                
                # Comprimir se configurado
                final_path = filepath
                if self.compress_backups:
                    compressed_path = str(filepath) + '.gz'
                    compress_success = await loop.run_in_executor(
                        self.executor,
                        self._compress_file,
                        str(filepath),
                        compressed_path
                    )
                    
                    if compress_success:
                        final_path = Path(compressed_path)
                        filename += '.gz'
                        file_size = os.path.getsize(final_path)
                
                # Calcular checksum
                checksum = await loop.run_in_executor(
                    self.executor,
                    self._calculate_checksum,
                    str(final_path)
                )
                
                backup_info = BackupInfo(
                    filename=filename,
                    filepath=str(final_path),
                    backup_type='full',
                    timestamp=timestamp,
                    size_bytes=file_size,
                    compressed=self.compress_backups,
                    checksum=checksum,
                    duration_seconds=duration,
                    success=True
                )
                
                business_logger.info(
                    "Full backup completed successfully",
                    extra_data={
                        'filename': filename,
                        'size_mb': round(file_size / (1024**2), 2),
                        'duration_seconds': round(duration, 2)
                    }
                )
                
            else:
                # Backup falhou
                error_message = result.stderr or "Unknown error"
                backup_info = BackupInfo(
                    filename=filename,
                    filepath=str(filepath),
                    backup_type='full',
                    timestamp=timestamp,
                    size_bytes=0,
                    compressed=False,
                    checksum='',
                    duration_seconds=duration,
                    success=False,
                    error_message=error_message
                )
                
                business_logger.error(
                    f"Full backup failed: {error_message}",
                    extra_data={'duration_seconds': round(duration, 2)}
                )
                
                # Criar alerta
                await alert_manager.create_alert(
                    alert_id="backup_failed",
                    title="Backup do banco de dados falhou",
                    message=f"Falha no backup completo: {error_message}",
                    severity=AlertSeverity.HIGH,
                    category=AlertCategory.SYSTEM,
                    metadata={'error': error_message, 'backup_type': 'full'}
                )
            
            # Adicionar ao histórico
            self.backup_history.append(backup_info)
            self.last_backup_status = backup_info
            self.save_backup_history()
            
            # Limpar backups antigos
            await self.cleanup_old_backups()
            
            return backup_info
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            backup_info = BackupInfo(
                filename=filename,
                filepath=str(filepath),
                backup_type='full',
                timestamp=timestamp,
                size_bytes=0,
                compressed=False,
                checksum='',
                duration_seconds=duration,
                success=False,
                error_message="Backup timeout"
            )
            
            business_logger.error("Full backup timed out")
            await alert_manager.create_alert(
                alert_id="backup_timeout",
                title="Backup do banco de dados expirou",
                message="Backup completo excedeu tempo limite de 1 hora",
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.SYSTEM,
                metadata={'backup_type': 'full', 'timeout_hours': 1}
            )
            
            return backup_info
            
        except Exception as e:
            duration = time.time() - start_time
            backup_info = BackupInfo(
                filename=filename,
                filepath=str(filepath),
                backup_type='full',
                timestamp=timestamp,
                size_bytes=0,
                compressed=False,
                checksum='',
                duration_seconds=duration,
                success=False,
                error_message=str(e)
            )
            
            business_logger.error(f"Error creating full backup: {e}", exc_info=True)
            await alert_manager.create_alert(
                alert_id="backup_error",
                title="Erro no backup do banco de dados",
                message=f"Erro durante backup completo: {str(e)}",
                severity=AlertSeverity.HIGH,
                category=AlertCategory.SYSTEM,
                metadata={'error': str(e), 'backup_type': 'full'}
            )
            
            return backup_info
    
    async def cleanup_old_backups(self):
        """Limpar backups antigos"""
        try:
            if len(self.backup_history) <= self.max_backups:
                return
            
            # Ordenar por timestamp
            sorted_backups = sorted(self.backup_history, key=lambda x: x.timestamp)
            
            # Remover backups antigos
            backups_to_remove = sorted_backups[:-self.max_backups]
            
            for backup in backups_to_remove:
                try:
                    if os.path.exists(backup.filepath):
                        os.remove(backup.filepath)
                        business_logger.info(f"Removed old backup: {backup.filename}")
                    
                    self.backup_history.remove(backup)
                    
                except Exception as e:
                    business_logger.error(f"Error removing backup {backup.filename}: {e}")
            
            self.save_backup_history()
            
        except Exception as e:
            business_logger.error(f"Error cleaning up old backups: {e}", exc_info=True)
    
    async def verify_backup(self, backup_info: BackupInfo) -> bool:
        """Verificar integridade de um backup"""
        try:
            if not os.path.exists(backup_info.filepath):
                return False
            
            # Verificar checksum
            current_checksum = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._calculate_checksum,
                backup_info.filepath
            )
            
            return current_checksum == backup_info.checksum
            
        except Exception as e:
            business_logger.error(f"Error verifying backup: {e}", exc_info=True)
            return False
    
    async def restore_backup(self, backup_info: BackupInfo) -> bool:
        """Restaurar um backup"""
        try:
            business_logger.warning(f"Starting database restore from {backup_info.filename}")
            
            # Verificar integridade primeiro
            if not await self.verify_backup(backup_info):
                business_logger.error("Backup verification failed, aborting restore")
                return False
            
            # Preparar arquivo para restore
            restore_file = backup_info.filepath
            temp_file = None
            
            # Descomprimir se necessário
            if backup_info.compressed:
                temp_file = str(self.backup_dir / f"temp_restore_{int(time.time())}.sql")
                
                with gzip.open(backup_info.filepath, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                restore_file = temp_file
            
            # Comando psql para restore
            cmd = [
                'psql',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['username'],
                '-d', self.db_config['database'],
                '-f', restore_file
            ]
            
            # Configurar variável de ambiente para senha
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # Executar restore
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=7200  # 2 horas timeout
                )
            )
            
            # Limpar arquivo temporário
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            if result.returncode == 0:
                business_logger.info(f"Database restore completed successfully from {backup_info.filename}")
                return True
            else:
                error_message = result.stderr or "Unknown error"
                business_logger.error(f"Database restore failed: {error_message}")
                return False
                
        except Exception as e:
            business_logger.error(f"Error restoring backup: {e}", exc_info=True)
            return False
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Obter estatísticas dos backups"""
        try:
            if not self.backup_history:
                return {}
            
            successful_backups = [b for b in self.backup_history if b.success]
            
            stats = {
                'total_backups': len(self.backup_history),
                'successful_backups': len(successful_backups),
                'failed_backups': len(self.backup_history) - len(successful_backups),
                'success_rate': len(successful_backups) / len(self.backup_history) * 100,
                'last_backup': self.last_backup_status.to_dict() if self.last_backup_status else None,
                'total_size_mb': sum(b.size_bytes for b in successful_backups) / (1024**2),
                'average_duration_minutes': sum(b.duration_seconds for b in successful_backups) / len(successful_backups) / 60 if successful_backups else 0,
                'oldest_backup': min(self.backup_history, key=lambda x: x.timestamp).timestamp.isoformat() if self.backup_history else None,
                'newest_backup': max(self.backup_history, key=lambda x: x.timestamp).timestamp.isoformat() if self.backup_history else None
            }
            
            return stats
            
        except Exception as e:
            business_logger.error(f"Error generating backup stats: {e}", exc_info=True)
            return {}
    
    def get_recent_backups(self, days: int = 7) -> List[BackupInfo]:
        """Obter backups recentes"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        return [b for b in self.backup_history if b.timestamp > cutoff_date]


class BackupScheduler:
    """
    Agendador de backups automáticos
    """
    
    def __init__(self, backup_manager: DatabaseBackupManager):
        self.backup_manager = backup_manager
        self.running = False
        self.scheduler_task = None
    
    def setup_schedule(self):
        """Configurar agendamento de backups"""
        # Backup completo diário às 2:00 AM
        schedule.every().day.at("02:00").do(
            lambda: asyncio.create_task(self.backup_manager.create_full_backup())
        )
        
        # Backup de verificação semanal (verificar integridade)
        schedule.every().sunday.at("03:00").do(
            lambda: asyncio.create_task(self._weekly_verification())
        )
    
    async def _weekly_verification(self):
        """Verificação semanal de integridade dos backups"""
        try:
            business_logger.info("Starting weekly backup verification")
            
            recent_backups = self.backup_manager.get_recent_backups(days=7)
            verified_count = 0
            failed_count = 0
            
            for backup in recent_backups:
                if backup.success:
                    is_valid = await self.backup_manager.verify_backup(backup)
                    if is_valid:
                        verified_count += 1
                    else:
                        failed_count += 1
                        business_logger.error(f"Backup verification failed: {backup.filename}")
            
            business_logger.info(
                f"Weekly verification completed: {verified_count} verified, {failed_count} failed"
            )
            
            # Alertar se muitos backups falharam na verificação
            if failed_count > 0:
                await alert_manager.create_alert(
                    alert_id="backup_verification_failed",
                    title="Falha na verificação de backups",
                    message=f"{failed_count} backups falharam na verificação de integridade",
                    severity=AlertSeverity.MEDIUM,
                    category=AlertCategory.SYSTEM,
                    metadata={'verified_count': verified_count, 'failed_count': failed_count}
                )
                
        except Exception as e:
            business_logger.error(f"Error in weekly verification: {e}", exc_info=True)
    
    async def start(self):
        """Iniciar agendador de backups"""
        if self.running:
            return
        
        self.running = True
        self.setup_schedule()
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        business_logger.info("Backup scheduler started")
    
    async def stop(self):
        """Parar agendador de backups"""
        if not self.running:
            return
        
        self.running = False
        schedule.clear()
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        business_logger.info("Backup scheduler stopped")
    
    async def _scheduler_loop(self):
        """Loop do agendador"""
        while self.running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Verificar a cada minuto
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                business_logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                await asyncio.sleep(60)


# Instâncias globais
backup_manager = DatabaseBackupManager()
backup_scheduler = BackupScheduler(backup_manager)


# Funções de conveniência
async def create_backup() -> BackupInfo:
    """Criar backup manual"""
    return await backup_manager.create_full_backup()

async def get_backup_status() -> Dict[str, Any]:
    """Obter status dos backups"""
    return backup_manager.get_backup_stats()

async def start_backup_scheduler():
    """Iniciar agendador de backups"""
    await backup_scheduler.start()

async def stop_backup_scheduler():
    """Parar agendador de backups"""
    await backup_scheduler.stop()
