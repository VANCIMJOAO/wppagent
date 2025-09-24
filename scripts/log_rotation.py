#!/usr/bin/env python3
"""
Sistema de rotação automática de logs
Remove logs antigos e mantém apenas os mais recentes
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta
import logging
import gzip
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/vancim/whats_agent/logs/log_rotation.log'),
        logging.StreamHandler()
    ]
)

def get_database_connection():
    """Conectar ao banco de dados"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway')
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco: {e}")
        return None

def rotate_database_logs():
    """Rotacionar logs do banco de dados"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Rotacionar meta_logs (manter apenas 30 dias)
        logging.info("🔄 Rotacionando meta_logs...")
        cur.execute("""
            DELETE FROM meta_logs 
            WHERE created_at < NOW() - INTERVAL '30 days'
        """)
        meta_logs_deleted = cur.rowcount
        logging.info(f"✅ {meta_logs_deleted} meta_logs antigos removidos")
        
        # Rotacionar logs de sistema (se existir tabela)
        try:
            cur.execute("""
                DELETE FROM system_logs 
                WHERE created_at < NOW() - INTERVAL '7 days'
            """)
            system_logs_deleted = cur.rowcount
            logging.info(f"✅ {system_logs_deleted} system_logs antigos removidos")
        except:
            logging.info("ℹ️ Tabela system_logs não encontrada, pulando...")
        
        # Rotacionar logs de erro (se existir tabela)
        try:
            cur.execute("""
                DELETE FROM error_logs 
                WHERE created_at < NOW() - INTERVAL '14 days'
            """)
            error_logs_deleted = cur.rowcount
            logging.info(f"✅ {error_logs_deleted} error_logs antigos removidos")
        except:
            logging.info("ℹ️ Tabela error_logs não encontrada, pulando...")
        
        conn.commit()
        return True
        
    except Exception as e:
        logging.error(f"Erro durante rotação de logs do banco: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def rotate_file_logs():
    """Rotacionar logs de arquivos"""
    log_dir = '/home/vancim/whats_agent/logs'
    
    if not os.path.exists(log_dir):
        logging.info(f"Diretório de logs não encontrado: {log_dir}")
        return True
    
    try:
        # Listar arquivos de log
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        
        for log_file in log_files:
            file_path = os.path.join(log_dir, log_file)
            
            # Verificar tamanho do arquivo (se > 10MB, rotacionar)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                logging.info(f"🔄 Rotacionando arquivo grande: {log_file} ({file_size/1024/1024:.1f}MB)")
                
                # Criar backup comprimido
                backup_name = f"{log_file}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.gz"
                backup_path = os.path.join(log_dir, backup_name)
                
                with open(file_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Limpar arquivo original
                with open(file_path, 'w') as f:
                    f.write('')
                
                logging.info(f"✅ Arquivo rotacionado: {backup_name}")
        
        # Remover backups antigos (> 30 dias)
        backup_files = [f for f in os.listdir(log_dir) if f.endswith('.gz')]
        for backup_file in backup_files:
            backup_path = os.path.join(log_dir, backup_file)
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(backup_path))
            
            if file_age > timedelta(days=30):
                os.remove(backup_path)
                logging.info(f"🗑️ Backup antigo removido: {backup_file}")
        
        return True
        
    except Exception as e:
        logging.error(f"Erro durante rotação de arquivos de log: {e}")
        return False

def get_log_stats():
    """Obter estatísticas de logs"""
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Estatísticas de meta_logs
        cur.execute("SELECT COUNT(*) FROM meta_logs")
        total_meta_logs = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM meta_logs WHERE created_at >= NOW() - INTERVAL '7 days'")
        recent_meta_logs = cur.fetchone()[0]
        
        # Estatísticas de arquivos de log
        log_dir = '/home/vancim/whats_agent/logs'
        total_log_files = 0
        total_log_size = 0
        
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith('.log'):
                    file_path = os.path.join(log_dir, file)
                    total_log_files += 1
                    total_log_size += os.path.getsize(file_path)
        
        logging.info("📊 ESTATÍSTICAS DE LOGS:")
        logging.info(f"   Meta Logs: {recent_meta_logs}/{total_meta_logs} (últimos 7 dias/total)")
        logging.info(f"   Arquivos de Log: {total_log_files} arquivos")
        logging.info(f"   Tamanho Total: {total_log_size/1024/1024:.1f} MB")
        
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas de logs: {e}")
    finally:
        cur.close()
        conn.close()

def main():
    """Função principal"""
    logging.info("🔄 Iniciando rotação automática de logs...")
    
    # Obter estatísticas antes da rotação
    get_log_stats()
    
    # Executar rotação
    db_success = rotate_database_logs()
    file_success = rotate_file_logs()
    
    # Obter estatísticas após a rotação
    logging.info("📊 Estatísticas após rotação:")
    get_log_stats()
    
    if db_success and file_success:
        logging.info("✅ Rotação de logs concluída com sucesso!")
        sys.exit(0)
    else:
        logging.error("❌ Erro durante a rotação de logs!")
        sys.exit(1)

if __name__ == "__main__":
    main()
