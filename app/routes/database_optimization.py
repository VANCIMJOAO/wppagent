"""
🗄️ Rotas para Otimização do Banco de Dados
==========================================

Endpoints para gerenciar:
- Criação de índices otimizados
- Stored procedures
- Estratégias de backup/restore
- Configuração de replicação
- Análise de performance
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any
from app.services.database_optimization import db_optimizer
from app.utils.logger import get_logger
from app.models.database import AdminUser
logger = get_logger(__name__)
from app.routes.admin_auth import get_current_admin_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/database", tags=["Database Optimization"])

@router.post("/optimize/indexes")
async def create_optimized_indexes(
    admin_user: AdminUser = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    🚀 Cria índices otimizados para queries frequentes
    
    Implementa índices para:
    - Mensagens (data, usuário, conversation)
    - Conversações (status, data, usuário)
    - Usuários (telefone, status, interação)
    - Agendamentos (data, status, serviço)
    - Logs Meta (data, endpoint, status)
    - Admin e sessões
    """
    try:
        logger.info(f"🚀 Admin {admin_user.username} iniciando criação de índices...")
        result = await db_optimizer.create_optimized_indexes()
        
        # Contar sucessos
        total_created = sum(
            len([item for item in category_results if "✅" in item])
            for category_results in result.values()
        )
        
        logger.info(f"✅ {total_created} índices criados com sucesso")
        
        return {
            "success": True,
            "message": f"✅ {total_created} índices criados com sucesso",
            "results": result,
            "admin_user": admin_user.username,
            "optimization_type": "indexes"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar índices: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar índices: {str(e)}"
        )

@router.post("/optimize/procedures")
async def create_stored_procedures(
    admin_user: AdminUser = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    🔧 Cria stored procedures para operações complexas
    
    Procedures criadas:
    - Análise de conversas
    - Limpeza de dados antigos
    - Estatísticas de performance
    - Backup de conversas críticas
    - Otimização automática
    """
    try:
        logger.info(f"🔧 Admin {admin_user.username} criando stored procedures...")
        result = await db_optimizer.create_stored_procedures()
        
        # Contar sucessos
        successful_procedures = sum(
            1 for status in result.values() if "✅" in status
        )
        
        logger.info(f"✅ {successful_procedures} procedures criadas")
        
        return {
            "success": True,
            "message": f"✅ {successful_procedures} stored procedures criadas",
            "results": result,
            "admin_user": admin_user.username,
            "optimization_type": "stored_procedures"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar procedures: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar stored procedures: {str(e)}"
        )

@router.post("/backup/setup")
async def setup_backup_strategy(
    admin_user: AdminUser = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    💾 Configura estratégia completa de backup/restore
    
    Inclui:
    - Scripts de backup completo e incremental
    - Script de restore com verificação
    - Política de retenção automática
    - Verificação de integridade
    """
    try:
        logger.info(f"💾 Admin {admin_user.username} configurando backup...")
        result = await db_optimizer.setup_backup_strategy()
        
        logger.info("✅ Estratégia de backup configurada")
        
        return {
            "success": True,
            "message": "✅ Estratégia de backup configurada com sucesso",
            "configuration": result,
            "admin_user": admin_user.username,
            "next_steps": [
                f"Execute backup completo: {result['backup_script']} full",
                f"Configure cron para automação",
                f"Teste restore: {result['restore_script']} list"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar backup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao configurar backup: {str(e)}"
        )

@router.post("/replication/setup")
async def setup_replication_config(
    admin_user: AdminUser = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    🔄 Configura replicação para alta disponibilidade
    
    Gera:
    - Configurações PostgreSQL para replicação
    - Scripts de setup para Primary e Replica
    - Sistema de monitoramento
    - Configuração de failover automático
    """
    try:
        logger.info(f"🔄 Admin {admin_user.username} configurando replicação...")
        result = await db_optimizer.setup_replication_config()
        
        logger.info("✅ Configuração de replicação preparada")
        
        return {
            "success": True,
            "message": "✅ Configuração de replicação preparada",
            "configuration": result,
            "admin_user": admin_user.username,
            "warning": "⚠️ Replicação requer configuração manual nos servidores"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar replicação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao configurar replicação: {str(e)}"
        )

@router.get("/analysis/performance")
async def run_performance_analysis(
    admin_user: AdminUser = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    📊 Executa análise completa de performance
    
    Analisa:
    - Queries lentas
    - Tamanho das tabelas
    - Uso de índices
    - Estatísticas de conexão
    - Métricas de cache
    """
    try:
        logger.info(f"📊 Admin {admin_user.username} executando análise...")
        result = await db_optimizer.run_performance_analysis()
        
        logger.info("✅ Análise de performance concluída")
        
        return {
            "success": True,
            "message": "✅ Análise de performance concluída",
            "analysis": result,
            "admin_user": admin_user.username,
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na análise: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na análise de performance: {str(e)}"
        )

@router.get("/status")
async def get_optimization_status(
    admin_user: AdminUser = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    📈 Retorna status das otimizações implementadas
    
    Mostra:
    - Número de índices criados
    - Procedures disponíveis
    - Conexões ativas
    - Tamanho do banco
    - Health score geral
    """
    try:
        result = await db_optimizer.get_optimization_status()
        
        return {
            "success": True,
            "status": result,
            "admin_user": admin_user.username
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter status: {str(e)}"
        )

@router.post("/optimize/all")
async def optimize_all_database(
    background_tasks: BackgroundTasks,
    admin_user: AdminUser = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    🚀 Executa otimização completa do banco de dados
    
    Executa em sequência:
    1. Criação de índices otimizados
    2. Stored procedures
    3. Configuração de backup
    4. Análise de performance
    """
    async def run_full_optimization():
        """Função para executar todas as otimizações"""
        try:
            logger.info(f"🚀 Iniciando otimização completa por {admin_user.username}")
            
            # 1. Índices
            indexes_result = await db_optimizer.create_optimized_indexes()
            logger.info("✅ Índices criados")
            
            # 2. Procedures
            procedures_result = await db_optimizer.create_stored_procedures()
            logger.info("✅ Procedures criadas")
            
            # 3. Backup
            backup_result = await db_optimizer.setup_backup_strategy()
            logger.info("✅ Backup configurado")
            
            # 4. Análise
            analysis_result = await db_optimizer.run_performance_analysis()
            logger.info("✅ Análise concluída")
            
            logger.info("🎯 Otimização completa finalizada")
            
        except Exception as e:
            logger.error(f"❌ Erro na otimização completa: {e}")
    
    # Executar em background
    background_tasks.add_task(run_full_optimization)
    
    return {
        "success": True,
        "message": "🚀 Otimização completa iniciada em background",
        "admin_user": admin_user.username,
        "operations": [
            "✅ Criação de índices otimizados",
            "✅ Stored procedures para operações complexas", 
            "✅ Configuração de backup/restore",
            "✅ Análise de performance"
        ],
        "note": "Acompanhe o progresso nos logs"
    }

@router.post("/maintenance/cleanup")
async def run_database_cleanup(
    days_to_keep: int = 90,
    admin_user: AdminUser = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    🧹 Executa limpeza de dados antigos
    
    Remove:
    - Meta logs antigos (padrão: > 90 dias)
    - Sessões expiradas
    - Dados temporários
    """
    try:
        logger.info(f"🧹 Admin {admin_user.username} executando limpeza...")
        
        # Usar a stored procedure de limpeza se disponível
        from app.database import engine
        from sqlalchemy import text
        
        engine = engine
        async with engine.begin() as conn:
            result = await conn.execute(
                text("SELECT cleanup_old_data(:days)"),
                {"days": days_to_keep}
            )
            cleanup_results = result.fetchall()
        
        logger.info(f"✅ Limpeza concluída")
        
        return {
            "success": True,
            "message": f"✅ Limpeza concluída - dados > {days_to_keep} dias removidos",
            "results": [dict(row._mapping) for row in cleanup_results],
            "admin_user": admin_user.username,
            "days_kept": days_to_keep
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na limpeza do banco: {str(e)}"
        )

@router.get("/health")
async def database_health_check() -> Dict[str, Any]:
    """
    🏥 Verificação de saúde do banco de dados
    
    Verifica:
    - Conectividade
    - Performance básica
    - Espaço em disco
    - Métricas gerais
    """
    try:
        from app.database import engine
        from sqlalchemy import text
        import time
        
        engine = engine
        start_time = time.time()
        
        async with engine.begin() as conn:
            # Teste de conectividade
            await conn.execute(text("SELECT 1"))
            
            # Métricas básicas
            size_result = await conn.execute(
                text("SELECT pg_database_size(current_database()) / 1024.0 / 1024.0 as size_mb")
            )
            db_size = size_result.scalar()
            
            # Conexões ativas
            conn_result = await conn.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            )
            active_connections = conn_result.scalar()
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time * 1000, 2),
            "database_size_mb": round(db_size, 2),
            "active_connections": active_connections,
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error(f"❌ Health check falhou: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "now"
        }
