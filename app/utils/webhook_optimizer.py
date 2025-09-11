"""
⚡ OTIMIZAÇÕES DE PERFORMANCE PARA WEBHOOK
==========================================

Sistema de processamento em lote para reduzir latência e I/O blocante.
"""

import asyncio
import time
from typing import Dict, List, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from app.services.structured_apm import get_structured_logger, LogCategory
from app.routes.webhook import process_single_message

# Configurar logger
logger = get_structured_logger("webhook.optimizer")


class BatchProcessor:
    """Sistema de processamento em lote otimizado para webhooks"""
    
    def __init__(self, max_concurrent: int = 10, batch_timeout: float = 5.0):
        self.max_concurrent = max_concurrent
        self.batch_timeout = batch_timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_messages_optimized(
        self, 
        messages: List[Dict[str, Any]], 
        db: AsyncSession
    ) -> Tuple[int, int, Dict[str, Any]]:
        """
        Processa mensagens com otimizações de performance:
        - Processamento concurrent
        - Error isolation
        - Métricas detalhadas
        """
        if not messages:
            return 0, 0, {"processing_time": 0}
        
        batch_size = len(messages)
        start_time = time.time()
        
        logger.info(
            f"🚀 Starting optimized batch processing: {batch_size} messages",
            metadata={
                "batch_size": batch_size,
                "max_concurrent": self.max_concurrent,
                "batch_timeout": self.batch_timeout
            },
            category=LogCategory.PERFORMANCE
        )
        
        # Processar mensagens concorrentemente
        async def process_with_error_handling(message_data: Dict[str, Any]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    return await process_single_message(message_data, db)
                except Exception as e:
                    logger.error(
                        f"❌ Error processing individual message: {str(e)}",
                        metadata={
                            "message_type": message_data.get("type", "unknown"),
                            "error_type": e.__class__.__name__,
                            "wa_id": message_data.get("from", "unknown")
                        },
                        category=LogCategory.WEBHOOK
                    )
                    return {"processed": False, "reason": f"processing_error: {str(e)}"}
        
        # Executar processamento concurrent com timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    *[process_with_error_handling(msg) for msg in messages],
                    return_exceptions=True
                ),
                timeout=self.batch_timeout
            )
        except asyncio.TimeoutError:
            logger.error(
                f"⏱️ Batch processing timeout after {self.batch_timeout}s",
                metadata={"batch_size": batch_size},
                category=LogCategory.PERFORMANCE
            )
            return 0, batch_size, {"error": "timeout", "processing_time": self.batch_timeout}
        
        # Contar resultados
        total_processed = 0
        total_blocked = 0
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Exception in message {i}: {result}")
                errors.append(str(result))
                total_blocked += 1
            elif result and result.get("processed"):
                total_processed += 1
            else:
                total_blocked += 1
        
        processing_time = time.time() - start_time
        
        # Calcular métricas
        metrics = {
            "processing_time": round(processing_time, 3),
            "avg_time_per_message_ms": round((processing_time / batch_size) * 1000, 2),
            "messages_per_second": round(batch_size / processing_time, 2) if processing_time > 0 else 0,
            "success_rate": round((total_processed / batch_size) * 100, 2),
            "concurrent_processing": True,
            "errors_count": len(errors),
            "batch_efficiency": round((batch_size / self.max_concurrent), 2)
        }
        
        # Log performance results
        logger.info(
            f"✅ Batch processing completed: {total_processed} processed, {total_blocked} blocked",
            metadata={
                "batch_size": batch_size,
                "total_processed": total_processed, 
                "total_blocked": total_blocked,
                **metrics
            },
            category=LogCategory.PERFORMANCE
        )
        
        return total_processed, total_blocked, metrics


class BulkDatabaseOptimizer:
    """Otimizador de operações em lote no banco de dados"""
    
    @staticmethod
    async def bulk_user_lookup(
        db: AsyncSession, 
        wa_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Busca múltiplos usuários de uma vez para evitar N+1 queries
        """
        # TODO: Implementar bulk lookup quando necessário
        # Por enquanto, mantém comportamento individual
        return {}
    
    @staticmethod 
    async def bulk_conversation_lookup(
        db: AsyncSession,
        user_ids: List[int]
    ) -> Dict[int, Any]:
        """
        Busca múltiplas conversas de uma vez
        """
        # TODO: Implementar bulk lookup quando necessário
        return {}


# Instância global do processador otimizado
batch_processor = BatchProcessor(max_concurrent=10, batch_timeout=15.0)
bulk_optimizer = BulkDatabaseOptimizer()
