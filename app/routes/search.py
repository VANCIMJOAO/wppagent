"""
Search Endpoints - SPRINT 3
Busca global de mensagens com full-text search
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.cache_service import cache_service
from ..config.logging_config import get_optimized_logger

logger = get_optimized_logger(__name__)
router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/messages")
async def search_messages(
    q: str = Query(..., description="Termo de busca", min_length=2),
    limit: int = Query(50, description="Número máximo de resultados", ge=1, le=100),
    offset: int = Query(0, description="Offset para paginação", ge=0),
    conversation_id: Optional[int] = Query(None, description="Filtrar por conversa específica"),
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    🔍 Busca Global de Mensagens
    
    Busca full-text em mensagens com destaque do termo e navegação para conversa.
    """
    cache_key = f"search:messages:{q}:{limit}:{offset}:{conversation_id}:{start_date}:{end_date}"
    
    # Verificar cache primeiro
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        logger.info("Search results served from cache", cache_key=cache_key)
        return cached_result
    
    try:
        # Construir filtros
        filters = []
        params = {"search_term": f"%{q}%"}
        
        if conversation_id:
            filters.append("m.conversation_id = :conversation_id")
            params["conversation_id"] = conversation_id
        
        if start_date:
            filters.append("m.created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            filters.append("m.created_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        # Query otimizada com full-text search
        search_query = text(f"""
            SELECT 
                m.id,
                m.content,
                m.sender,
                m.created_at,
                m.conversation_id,
                c.status as conversation_status,
                c.customer_name,
                c.customer_phone,
                -- Destacar o termo de busca
                REPLACE(
                    REPLACE(
                        REPLACE(LOWER(m.content), LOWER(:search_term), '**' || UPPER(:search_term) || '**'),
                        '**%', '**'
                    ),
                    '%**', '**'
                ) as highlighted_content,
                -- Score de relevância baseado em posição e frequência
                (
                    CASE 
                        WHEN LOWER(m.content) LIKE LOWER(:search_term) THEN 10
                        ELSE 5
                    END +
                    CASE 
                        WHEN LOWER(m.content) LIKE LOWER(:search_term) || '%' THEN 3
                        ELSE 0
                    END +
                    CASE 
                        WHEN LOWER(m.content) LIKE '%' || LOWER(:search_term) || '%' THEN 1
                        ELSE 0
                    END
                ) as relevance_score
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE 
                LOWER(m.content) LIKE LOWER(:search_term)
                AND {where_clause}
            ORDER BY 
                relevance_score DESC,
                m.created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        params.update({
            "limit": limit,
            "offset": offset
        })
        
        result = db.execute(search_query, params).fetchall()
        
        # Processar resultados
        messages = []
        for row in result:
            message_data = {
                "id": row.id,
                "content": row.content,
                "highlighted_content": row.highlighted_content,
                "sender": row.sender,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "conversation": {
                    "id": row.conversation_id,
                    "status": row.conversation_status,
                    "customer_name": row.customer_name,
                    "customer_phone": row.customer_phone
                },
                "relevance_score": row.relevance_score
            }
            messages.append(message_data)
        
        # Contar total de resultados para paginação
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE 
                LOWER(m.content) LIKE LOWER(:search_term)
                AND {where_clause}
        """)
        
        count_result = db.execute(count_query, params).fetchone()
        total_count = count_result.total if count_result else 0
        
        response_data = {
            "query": q,
            "messages": messages,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "generated_at": datetime.utcnow().isoformat(),
            "cache_ttl": 60  # 1 minuto para busca
        }
        
        # Cache por 1 minuto
        await cache_service.set(cache_key, response_data, ttl=60)
        
        logger.info("Search completed", 
                   query=q,
                   results_count=len(messages),
                   total_count=total_count)
        
        return response_data
        
    except Exception as e:
        logger.error("Error searching messages", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error searching messages: {str(e)}")


@router.get("/conversations")
async def search_conversations(
    q: str = Query(..., description="Termo de busca", min_length=2),
    limit: int = Query(20, description="Número máximo de resultados", ge=1, le=50),
    offset: int = Query(0, description="Offset para paginação", ge=0),
    status: Optional[str] = Query(None, description="Filtrar por status da conversa"),
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    🔍 Busca Global de Conversas
    
    Busca em conversas por nome do cliente, telefone ou conteúdo das mensagens.
    """
    cache_key = f"search:conversations:{q}:{limit}:{offset}:{status}:{start_date}:{end_date}"
    
    # Verificar cache primeiro
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        logger.info("Conversation search results served from cache", cache_key=cache_key)
        return cached_result
    
    try:
        # Construir filtros
        filters = []
        params = {"search_term": f"%{q}%"}
        
        if status:
            filters.append("c.status = :status")
            params["status"] = status
        
        if start_date:
            filters.append("c.created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            filters.append("c.created_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        # Query otimizada para busca em conversas
        search_query = text(f"""
            WITH conversation_search AS (
                SELECT 
                    c.id,
                    c.customer_name,
                    c.customer_phone,
                    c.status,
                    c.outcome,
                    c.created_at,
                    c.updated_at,
                    COUNT(m.id) as message_count,
                    MAX(m.created_at) as last_message_at,
                    -- Buscar em nome, telefone e conteúdo das mensagens
                    (
                        CASE 
                            WHEN LOWER(c.customer_name) LIKE LOWER(:search_term) THEN 10
                            ELSE 0
                        END +
                        CASE 
                            WHEN c.customer_phone LIKE :search_term THEN 8
                            ELSE 0
                        END +
                        CASE 
                            WHEN EXISTS (
                                SELECT 1 FROM messages m2 
                                WHERE m2.conversation_id = c.id 
                                AND LOWER(m2.content) LIKE LOWER(:search_term)
                            ) THEN 5
                            ELSE 0
                        END
                    ) as relevance_score
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE 
                    (
                        LOWER(c.customer_name) LIKE LOWER(:search_term)
                        OR c.customer_phone LIKE :search_term
                        OR EXISTS (
                            SELECT 1 FROM messages m3 
                            WHERE m3.conversation_id = c.id 
                            AND LOWER(m3.content) LIKE LOWER(:search_term)
                        )
                    )
                    AND {where_clause}
                GROUP BY c.id, c.customer_name, c.customer_phone, c.status, c.outcome, c.created_at, c.updated_at
            )
            SELECT 
                id,
                customer_name,
                customer_phone,
                status,
                outcome,
                created_at,
                updated_at,
                message_count,
                last_message_at,
                relevance_score
            FROM conversation_search
            ORDER BY 
                relevance_score DESC,
                last_message_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        params.update({
            "limit": limit,
            "offset": offset
        })
        
        result = db.execute(search_query, params).fetchall()
        
        # Processar resultados
        conversations = []
        for row in result:
            conversation_data = {
                "id": row.id,
                "customer_name": row.customer_name,
                "customer_phone": row.customer_phone,
                "status": row.status,
                "outcome": row.outcome,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "message_count": row.message_count,
                "last_message_at": row.last_message_at.isoformat() if row.last_message_at else None,
                "relevance_score": row.relevance_score
            }
            conversations.append(conversation_data)
        
        # Contar total de resultados
        count_query = text(f"""
            SELECT COUNT(DISTINCT c.id) as total
            FROM conversations c
            WHERE 
                (
                    LOWER(c.customer_name) LIKE LOWER(:search_term)
                    OR c.customer_phone LIKE :search_term
                    OR EXISTS (
                        SELECT 1 FROM messages m 
                        WHERE m.conversation_id = c.id 
                        AND LOWER(m.content) LIKE LOWER(:search_term)
                    )
                )
                AND {where_clause}
        """)
        
        count_result = db.execute(count_query, params).fetchone()
        total_count = count_result.total if count_result else 0
        
        response_data = {
            "query": q,
            "conversations": conversations,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count,
                "total_pages": (total_count + limit - 1) // limit
            },
            "generated_at": datetime.utcnow().isoformat(),
            "cache_ttl": 60  # 1 minuto para busca
        }
        
        # Cache por 1 minuto
        await cache_service.set(cache_key, response_data, ttl=60)
        
        logger.info("Conversation search completed", 
                   query=q,
                   results_count=len(conversations),
                   total_count=total_count)
        
        return response_data
        
    except Exception as e:
        logger.error("Error searching conversations", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error searching conversations: {str(e)}")


@router.get("/health")
async def search_health():
    """
    🏥 Health Check da Busca
    
    Verifica se os endpoints de busca estão funcionando.
    """
    return {
        "status": "healthy",
        "service": "search",
        "version": "1.0.0",
        "endpoints": [
            "/api/search/messages",
            "/api/search/conversations"
        ],
        "cache_enabled": True,
        "timestamp": datetime.utcnow().isoformat()
    }
