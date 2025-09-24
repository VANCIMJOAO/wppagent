#!/usr/bin/env python3
"""
Script para limpeza automática de sessões expiradas
Executa limpeza de login_sessions e refresh_tokens expirados
"""

import os
import sys
import psycopg2
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/vancim/whats_agent/logs/session_cleanup.log'),
        logging.StreamHandler()
    ]
)

def get_database_connection():
    """Conectar ao banco de dados"""
    try:
        # Usar variável de ambiente ou fallback
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway')
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco: {e}")
        return None

def cleanup_expired_sessions():
    """Limpar sessões expiradas"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Limpar login_sessions expiradas (mais de 24 horas)
        logging.info("🧹 Limpando login_sessions expiradas...")
        cur.execute("""
            DELETE FROM login_sessions 
            WHERE created_at < NOW() - INTERVAL '24 hours'
        """)
        login_sessions_deleted = cur.rowcount
        logging.info(f"✅ {login_sessions_deleted} login_sessions expiradas removidas")
        
        # Limpar refresh_tokens expirados (mais de 30 dias)
        logging.info("🧹 Limpando refresh_tokens expirados...")
        cur.execute("""
            DELETE FROM refresh_tokens 
            WHERE created_at < NOW() - INTERVAL '30 days'
        """)
        refresh_tokens_deleted = cur.rowcount
        logging.info(f"✅ {refresh_tokens_deleted} refresh_tokens expirados removidos")
        
        # Limpar user_sessions expiradas (mais de 7 dias)
        logging.info("🧹 Limpando user_sessions expiradas...")
        cur.execute("""
            DELETE FROM user_sessions 
            WHERE created_at < NOW() - INTERVAL '7 days'
        """)
        user_sessions_deleted = cur.rowcount
        logging.info(f"✅ {user_sessions_deleted} user_sessions expiradas removidas")
        
        conn.commit()
        
        total_deleted = login_sessions_deleted + refresh_tokens_deleted + user_sessions_deleted
        logging.info(f"🎉 Limpeza concluída! Total de registros removidos: {total_deleted}")
        
        return True
        
    except Exception as e:
        logging.error(f"Erro durante limpeza: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def cleanup_old_logs():
    """Limpar logs antigos"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        
        # Limpar meta_logs antigos (mais de 30 dias)
        logging.info("🧹 Limpando meta_logs antigos...")
        cur.execute("""
            DELETE FROM meta_logs 
            WHERE created_at < NOW() - INTERVAL '30 days'
        """)
        logs_deleted = cur.rowcount
        logging.info(f"✅ {logs_deleted} meta_logs antigos removidos")
        
        conn.commit()
        return True
        
    except Exception as e:
        logging.error(f"Erro durante limpeza de logs: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_session_stats():
    """Obter estatísticas de sessões"""
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # Estatísticas de login_sessions
        cur.execute("SELECT COUNT(*) FROM login_sessions")
        total_login_sessions = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM login_sessions WHERE created_at > NOW() - INTERVAL '24 hours'")
        active_login_sessions = cur.fetchone()[0]
        
        # Estatísticas de refresh_tokens
        cur.execute("SELECT COUNT(*) FROM refresh_tokens")
        total_refresh_tokens = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM refresh_tokens WHERE created_at > NOW() - INTERVAL '30 days'")
        active_refresh_tokens = cur.fetchone()[0]
        
        # Estatísticas de meta_logs
        cur.execute("SELECT COUNT(*) FROM meta_logs")
        total_meta_logs = cur.fetchone()[0]
        
        logging.info("📊 ESTATÍSTICAS DE SESSÕES:")
        logging.info(f"   Login Sessions: {active_login_sessions}/{total_login_sessions} ativas")
        logging.info(f"   Refresh Tokens: {active_refresh_tokens}/{total_refresh_tokens} ativos")
        logging.info(f"   Meta Logs: {total_meta_logs} registros")
        
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas: {e}")
    finally:
        cur.close()
        conn.close()

def main():
    """Função principal"""
    logging.info("🚀 Iniciando limpeza automática de sessões...")
    
    # Obter estatísticas antes da limpeza
    get_session_stats()
    
    # Executar limpeza
    success = cleanup_expired_sessions()
    if success:
        cleanup_old_logs()
    
    # Obter estatísticas após a limpeza
    logging.info("📊 Estatísticas após limpeza:")
    get_session_stats()
    
    if success:
        logging.info("✅ Limpeza concluída com sucesso!")
        sys.exit(0)
    else:
        logging.error("❌ Erro durante a limpeza!")
        sys.exit(1)

if __name__ == "__main__":
    main()
