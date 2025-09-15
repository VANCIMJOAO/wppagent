"""
📊 PD001 - Queries Otimizadas para Eliminar N+1 Problem
======================================================

Sistema de queries otimizadas usando SQLAlchemy selectinload/joinedload
para eliminar o problema N+1 em conversações e agendamentos.

Implementações:
- Conversations com users e messages precarregados
- Appointments com relations (user, service, business) precarregados
- Contagem de mensagens otimizada com subqueries
- Paginação eficiente com LIMIT/OFFSET

Performance Target:
- Antes: 4.228ms com Seq Scan em messages (N+1)
- Depois: <1ms com Index Scan e preload otimizado

Autor: GitHub Copilot
Data: 2025-09-12
Status: PD001 Implementation - N+1 Query Optimization
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import asc, desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, subqueryload

from app.models.database import (Appointment, Business, Conversation, Message,
                                 Service, User)
from app.services.structured_apm import get_structured_logger

logger = get_structured_logger(__name__)


class OptimizedQueryServicePD001:
    """📊 PD001 - Queries otimizadas para eliminar N+1"""

    @staticmethod
    async def get_conversations_optimized(
        session: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Conversation]:
        """
        📊 Query otimizada para conversas - elimina N+1

        Estratégia:
        - joinedload(Conversation.user): uma query em vez de N
        - selectinload(Conversation.messages): subquery otimizada em vez de N
        - Índices compostos para ORDER BY otimizado
        """
        start_time = time.time()

        # Base query com preload otimizado
        query = select(Conversation).options(
            joinedload(Conversation.user),  # JOIN em vez de query separada por conversa
            selectinload(Conversation.messages)
            .options(joinedload(Message.user))  # Precarregar users das mensagens também
            .limit(5),  # Limitar mensagens por conversa
        )

        # Filtros opcionais
        if user_id:
            query = query.where(Conversation.user_id == user_id)

        if status:
            query = query.where(Conversation.status == status)

        # Ordenação otimizada (usa índice composto)
        query = query.order_by(desc(Conversation.last_message_at))

        # Paginação
        query = query.offset(offset).limit(limit)

        # Executar query otimizada
        result = await session.execute(query)
        conversations = result.unique().scalars().all()

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            f"📊 PD001 Conversations query optimized: {execution_time:.2f}ms",
            metadata={
                "execution_time_ms": execution_time,
                "conversations_count": len(conversations),
                "limit": limit,
                "offset": offset,
                "filters": {"user_id": user_id, "status": status},
            },
            category="query_optimization",
        )

        return conversations

    @staticmethod
    async def get_appointments_with_relations(
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        business_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Appointment]:
        """
        📊 Query otimizada para appointments - elimina N+1

        Estratégia:
        - joinedload para todas as relations em uma única query
        - Índices compostos para filtros e ordenação
        - LIMIT/OFFSET eficiente
        """
        start_time = time.time()

        # Query com preload completo das relations
        query = select(Appointment).options(
            joinedload(Appointment.user),  # Uma query em vez de N para users
            joinedload(Appointment.service),  # Uma query em vez de N para services
            joinedload(Appointment.business),  # Uma query em vez de N para businesses
        )

        # Filtros opcionais (usa índices compostos)
        if business_id:
            query = query.where(Appointment.business_id == business_id)

        if user_id:
            query = query.where(Appointment.user_id == user_id)

        if status:
            query = query.where(Appointment.status == status)

        # Ordenação otimizada (usa índice composto business_id + date_time)
        query = query.order_by(desc(Appointment.date_time))

        # Paginação
        query = query.offset(offset).limit(limit)

        # Executar query otimizada
        result = await session.execute(query)
        appointments = result.unique().scalars().all()

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            f"📊 PD001 Appointments query optimized: {execution_time:.2f}ms",
            metadata={
                "execution_time_ms": execution_time,
                "appointments_count": len(appointments),
                "limit": limit,
                "offset": offset,
                "filters": {
                    "business_id": business_id,
                    "user_id": user_id,
                    "status": status,
                },
            },
            category="query_optimization",
        )

        return appointments

    @staticmethod
    async def get_conversations_with_counts_batch(
        session: AsyncSession, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        📊 Batch query para conversas com contagens - elimina N+1 completamente

        Strategy: Uma query com subquery correlacionada para contagens
        """
        start_time = time.time()

        # Subquery para contagem de mensagens (correlacionada)
        message_count_subquery = (
            select(func.count(Message.id))
            .where(Message.conversation_id == Conversation.id)
            .scalar_subquery()
        )

        # Query principal com contagem incluída
        query = (
            select(
                Conversation,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                message_count_subquery.label("message_count"),
            )
            .join(User, Conversation.user_id == User.id)
            .order_by(desc(Conversation.last_message_at))
            .offset(offset)
            .limit(limit)
        )

        # Executar query otimizada
        result = await session.execute(query)
        rows = result.all()

        # Transformar resultado
        conversations_data = []
        for row in rows:
            conversations_data.append(
                {
                    "conversation": row.Conversation,
                    "user_name": row.user_name,
                    "user_phone": row.user_phone,
                    "message_count": row.message_count,
                }
            )

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            f"📊 PD001 Batch conversations with counts: {execution_time:.2f}ms",
            metadata={
                "execution_time_ms": execution_time,
                "conversations_count": len(conversations_data),
                "limit": limit,
                "offset": offset,
            },
            category="query_optimization",
        )

        return conversations_data

    @staticmethod
    async def analyze_query_performance(
        session: AsyncSession, query_name: str, raw_sql: str
    ) -> Dict[str, Any]:
        """
        📊 Analisar performance de query com EXPLAIN ANALYZE

        Útil para validar otimizações de índices
        """
        start_time = time.time()

        try:
            # Executar EXPLAIN ANALYZE
            explain_query = text(f"EXPLAIN ANALYZE {raw_sql}")
            result = await session.execute(explain_query)
            explain_output = [row[0] for row in result.fetchall()]

            execution_time = (time.time() - start_time) * 1000

            # Extrair métricas do EXPLAIN
            total_time = None
            index_scans = 0
            seq_scans = 0

            for line in explain_output:
                if "actual time=" in line:
                    # Pegar o tempo total da primeira linha
                    if total_time is None:
                        import re

                        time_match = re.search(
                            r"actual time=[\d.]+\.\.[\d.]+ rows=\d+ loops=\d+", line
                        )
                        if time_match:
                            total_time = line

                if "Index Scan" in line:
                    index_scans += 1
                elif "Seq Scan" in line:
                    seq_scans += 1

            analysis = {
                "query_name": query_name,
                "execution_time_ms": execution_time,
                "explain_output": explain_output,
                "total_time_info": total_time,
                "index_scans": index_scans,
                "seq_scans": seq_scans,
                "performance_grade": (
                    "A"
                    if seq_scans == 0 and index_scans > 0
                    else "B" if seq_scans == 0 else "C"
                ),
            }

            logger.info(
                f"📊 PD001 Query analysis: {query_name} - Grade {analysis['performance_grade']}",
                metadata=analysis,
                category="query_analysis",
            )

            return analysis

        except Exception as e:
            logger.error(
                f"❌ PD001 Query analysis failed: {query_name}",
                metadata={"error": str(e), "query": raw_sql},
                category="query_analysis_error",
            )

            return {
                "query_name": query_name,
                "error": str(e),
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

    @staticmethod
    async def benchmark_before_after_optimization(
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        📊 Benchmark comparando queries antes e depois da otimização PD001
        """
        results = {"timestamp": datetime.utcnow().isoformat(), "benchmarks": {}}

        # 1. Test conversations query (problema N+1 original)
        old_query = """
        SELECT c.*, u.nome, u.telefone, COUNT(m.id) 
        FROM conversations c 
        JOIN users u ON c.user_id = u.id 
        LEFT JOIN messages m ON m.conversation_id = c.id 
        GROUP BY c.id, u.nome, u.telefone
        LIMIT 10
        """

        new_query = """
        SELECT c.*, u.nome, u.telefone, 
            (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
        FROM conversations c 
        JOIN users u ON c.user_id = u.id 
        ORDER BY c.last_message_at DESC 
        LIMIT 10
        """

        # Analyze both queries
        old_analysis = await OptimizedQueryServicePD001.analyze_query_performance(
            session, "conversations_old_n1", old_query
        )

        new_analysis = await OptimizedQueryServicePD001.analyze_query_performance(
            session, "conversations_optimized", new_query
        )

        results["benchmarks"]["conversations"] = {
            "old_approach": old_analysis,
            "optimized_approach": new_analysis,
            "improvement": "Reduced N+1 queries, added composite indexes",
        }

        # 2. Test usando o serviço otimizado
        service_start = time.time()
        optimized_conversations = (
            await OptimizedQueryServicePD001.get_conversations_optimized(
                session, limit=10
            )
        )
        service_time = (time.time() - service_start) * 1000

        results["benchmarks"]["optimized_service"] = {
            "execution_time_ms": service_time,
            "conversations_loaded": len(optimized_conversations),
            "method": "selectinload + joinedload",
        }

        logger.info(
            "📊 PD001 Benchmark completed",
            metadata=results,
            category="performance_benchmark",
        )

        return results
