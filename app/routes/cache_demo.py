"""
PD003 - Cache Demo Routes

Rotas de demonstração para mostrar performance antes/depois do cache em listas e dashboards.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
import asyncio
import time
from datetime import datetime, timedelta
import random
import json

from app.services.cache_dashboard import dashboard_cache
from app.services.cache_invalidation_policy import invalidation_policy, trigger_cache_invalidation

router = APIRouter()


# Simulação de dados para demonstração
def generate_mock_conversations(count: int = 20) -> List[Dict[str, Any]]:
    """Gerar conversas mock para demonstração"""
    conversations = []
    for i in range(count):
        conversations.append({
            'id': i + 1,
            'customer_name': f'Cliente {i + 1}',
            'last_message': f'Mensagem do cliente {i + 1}',
            'status': random.choice(['active', 'pending', 'closed']),
            'created_at': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
            'message_count': random.randint(1, 50),
            'priority': random.choice(['low', 'medium', 'high'])
        })
    return conversations


def generate_mock_appointments(count: int = 15) -> List[Dict[str, Any]]:
    """Gerar appointments mock para demonstração"""
    appointments = []
    for i in range(count):
        appointments.append({
            'id': i + 1,
            'customer_name': f'Cliente {i + 1}',
            'service': random.choice(['Consulta', 'Atendimento', 'Suporte', 'Venda']),
            'datetime': (datetime.now() + timedelta(hours=random.randint(1, 168))).isoformat(),
            'status': random.choice(['scheduled', 'confirmed', 'completed', 'cancelled']),
            'duration_minutes': random.choice([30, 60, 90, 120]),
            'price': random.randint(50, 500)
        })
    return appointments


def generate_mock_dashboard_stats(business_id: int) -> Dict[str, Any]:
    """Gerar estatísticas mock do dashboard"""
    return {
        'business_id': business_id,
        'total_conversations': random.randint(100, 1000),
        'active_conversations': random.randint(10, 100),
        'pending_conversations': random.randint(5, 50),
        'total_appointments': random.randint(50, 500),
        'upcoming_appointments': random.randint(5, 30),
        'completed_appointments': random.randint(40, 200),
        'total_revenue': random.randint(5000, 50000),
        'monthly_revenue': random.randint(1000, 10000),
        'customer_satisfaction': round(random.uniform(4.0, 5.0), 2),
        'response_time_avg': round(random.uniform(5.0, 60.0), 2),
        'last_updated': datetime.now().isoformat()
    }


async def simulate_database_query_delay():
    """Simular delay de query no banco de dados"""
    await asyncio.sleep(random.uniform(0.1, 0.5))  # 100-500ms delay


@router.get("/cache-demo/conversations/without-cache")
async def get_conversations_without_cache(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """Demonstração: Lista de conversas SEM cache"""
    start_time = time.time()
    
    # Simular delay de banco de dados
    await simulate_database_query_delay()
    
    # Simular filtros
    filters = {}
    if status:
        filters['status'] = status
    if priority:
        filters['priority'] = priority
    
    # Gerar dados mock
    conversations = generate_mock_conversations(limit)
    
    # Aplicar filtros se necessário
    if status:
        conversations = [c for c in conversations if c['status'] == status]
    if priority:
        conversations = [c for c in conversations if c['priority'] == priority]
    
    end_time = time.time()
    query_time = round((end_time - start_time) * 1000, 2)
    
    return {
        'success': True,
        'data': {
            'conversations': conversations[:limit],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': len(conversations)
            },
            'filters': filters,
            'performance': {
                'cache_used': False,
                'query_time_ms': query_time,
                'data_source': 'database_simulation'
            }
        }
    }


@router.get("/cache-demo/conversations/with-cache")
async def get_conversations_with_cache(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    """Demonstração: Lista de conversas COM cache"""
    start_time = time.time()
    
    # Preparar filtros
    filters = {}
    if status:
        filters['status'] = status
    if priority:
        filters['priority'] = priority
    
    # Tentar buscar do cache primeiro
    cached_data = await dashboard_cache.get_conversation_list(filters, page, limit)
    
    if cached_data:
        # Cache HIT
        end_time = time.time()
        query_time = round((end_time - start_time) * 1000, 2)
        
        return {
            'success': True,
            'data': {
                **cached_data,
                'performance': {
                    'cache_used': True,
                    'cache_hit': True,
                    'query_time_ms': query_time,
                    'data_source': 'redis_cache'
                }
            }
        }
    else:
        # Cache MISS - buscar do "banco"
        await simulate_database_query_delay()
        
        conversations = generate_mock_conversations(limit)
        
        # Aplicar filtros
        if status:
            conversations = [c for c in conversations if c['status'] == status]
        if priority:
            conversations = [c for c in conversations if c['priority'] == priority]
        
        # Preparar resposta
        response_data = {
            'conversations': conversations[:limit],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': len(conversations)
            },
            'filters': filters
        }
        
        # Cachear para próximas requisições
        await dashboard_cache.set_conversation_list(filters, page, limit, response_data)
        
        end_time = time.time()
        query_time = round((end_time - start_time) * 1000, 2)
        
        return {
            'success': True,
            'data': {
                **response_data,
                'performance': {
                    'cache_used': True,
                    'cache_hit': False,
                    'query_time_ms': query_time,
                    'data_source': 'database_simulation',
                    'cached_for_next_request': True
                }
            }
        }


@router.get("/cache-demo/appointments/with-cache")
async def get_appointments_with_cache(
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    """Demonstração: Lista de appointments COM cache"""
    start_time = time.time()
    
    filters = {}
    if status:
        filters['status'] = status
    
    # Buscar do cache
    cached_data = await dashboard_cache.get_appointment_list(filters, page, limit)
    
    if cached_data:
        end_time = time.time()
        query_time = round((end_time - start_time) * 1000, 2)
        
        return {
            'success': True,
            'data': {
                **cached_data,
                'performance': {
                    'cache_hit': True,
                    'query_time_ms': query_time,
                    'data_source': 'redis_cache'
                }
            }
        }
    else:
        # Cache miss
        await simulate_database_query_delay()
        
        appointments = generate_mock_appointments(limit)
        
        if status:
            appointments = [a for a in appointments if a['status'] == status]
        
        response_data = {
            'appointments': appointments[:limit],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': len(appointments)
            },
            'filters': filters
        }
        
        # Cachear
        await dashboard_cache.set_appointment_list(filters, page, limit, response_data)
        
        end_time = time.time()
        query_time = round((end_time - start_time) * 1000, 2)
        
        return {
            'success': True,
            'data': {
                **response_data,
                'performance': {
                    'cache_hit': False,
                    'query_time_ms': query_time,
                    'data_source': 'database_simulation'
                }
            }
        }


@router.get("/cache-demo/dashboard/stats/{business_id}")
async def get_dashboard_stats_cached(business_id: int):
    """Demonstração: Dashboard stats COM cache"""
    start_time = time.time()
    
    # Buscar do cache
    cached_stats = await dashboard_cache.get_dashboard_stats(business_id)
    
    if cached_stats:
        end_time = time.time()
        query_time = round((end_time - start_time) * 1000, 2)
        
        return {
            'success': True,
            'data': {
                **cached_stats,
                'performance': {
                    'cache_hit': True,
                    'query_time_ms': query_time,
                    'data_source': 'redis_cache'
                }
            }
        }
    else:
        # Simular múltiplas queries para dashboard
        await asyncio.sleep(0.3)  # Simular queries mais pesadas
        
        stats = generate_mock_dashboard_stats(business_id)
        
        # Cachear
        await dashboard_cache.set_dashboard_stats(business_id, stats)
        
        end_time = time.time()
        query_time = round((end_time - start_time) * 1000, 2)
        
        return {
            'success': True,
            'data': {
                **stats,
                'performance': {
                    'cache_hit': False,
                    'query_time_ms': query_time,
                    'data_source': 'database_simulation',
                    'heavy_queries_executed': 5
                }
            }
        }


@router.get("/cache-demo/quick-stats/{business_id}")
async def get_quick_stats_cached(business_id: int):
    """Demonstração: Quick stats (TTL 1 minuto)"""
    start_time = time.time()
    
    cached_stats = await dashboard_cache.get_quick_stats(business_id)
    
    if cached_stats:
        end_time = time.time()
        query_time = round((end_time - start_time) * 1000, 2)
        
        return {
            'success': True,
            'data': {
                **cached_stats,
                'performance': {
                    'cache_hit': True,
                    'query_time_ms': query_time,
                    'ttl_seconds': 60
                }
            }
        }
    else:
        await simulate_database_query_delay()
        
        quick_stats = {
            'active_conversations': random.randint(5, 50),
            'pending_appointments': random.randint(2, 20),
            'online_agents': random.randint(1, 10),
            'avg_response_time': round(random.uniform(30, 180), 1),
            'generated_at': datetime.now().isoformat()
        }
        
        await dashboard_cache.set_quick_stats(business_id, quick_stats)
        
        end_time = time.time()
        query_time = round((end_time - start_time) * 1000, 2)
        
        return {
            'success': True,
            'data': {
                **quick_stats,
                'performance': {
                    'cache_hit': False,
                    'query_time_ms': query_time,
                    'ttl_seconds': 60
                }
            }
        }


@router.post("/cache-demo/invalidate/trigger")
async def trigger_cache_invalidation_demo(
    event_type: str,
    business_id: Optional[int] = None,
    user_id: Optional[int] = None
):
    """Demonstração: Trigger de invalidação de cache"""
    start_time = time.time()
    
    # Preparar dados do evento
    event_data = {}
    if business_id:
        event_data['business_id'] = business_id
    if user_id:
        event_data['user_id'] = user_id
    
    # Trigger invalidação
    await trigger_cache_invalidation(event_type, **event_data)
    
    end_time = time.time()
    invalidation_time = round((end_time - start_time) * 1000, 2)
    
    return {
        'success': True,
        'data': {
            'event_type': event_type,
            'event_data': event_data,
            'invalidation_time_ms': invalidation_time,
            'cache_types_invalidated': invalidation_policy.INVALIDATION_RULES.get(event_type, []),
            'message': f'Cache invalidado para evento: {event_type}'
        }
    }


@router.get("/cache-demo/performance/benchmark")
async def cache_performance_benchmark():
    """Benchmark de performance: com cache vs sem cache"""
    results = {
        'test_scenarios': [],
        'summary': {}
    }
    
    # Teste 1: Dashboard stats
    business_id = 1
    
    # Sem cache (primeira chamada)
    start = time.time()
    await get_dashboard_stats_cached(business_id)
    no_cache_time = (time.time() - start) * 1000
    
    # Com cache (segunda chamada)
    start = time.time()
    await get_dashboard_stats_cached(business_id)
    with_cache_time = (time.time() - start) * 1000
    
    results['test_scenarios'].append({
        'name': 'Dashboard Stats',
        'no_cache_ms': round(no_cache_time, 2),
        'with_cache_ms': round(with_cache_time, 2),
        'speedup': round(no_cache_time / with_cache_time, 2) if with_cache_time > 0 else 0
    })
    
    # Teste 2: Conversation list
    filters = {'status': 'active'}
    
    # Sem cache
    start = time.time()
    await get_conversations_without_cache()
    no_cache_conv_time = (time.time() - start) * 1000
    
    # Com cache (primeira chamada para cachear)
    await get_conversations_with_cache(status='active')
    
    # Com cache (segunda chamada)
    start = time.time()
    await get_conversations_with_cache(status='active')
    with_cache_conv_time = (time.time() - start) * 1000
    
    results['test_scenarios'].append({
        'name': 'Conversation List',
        'no_cache_ms': round(no_cache_conv_time, 2),
        'with_cache_ms': round(with_cache_conv_time, 2),
        'speedup': round(no_cache_conv_time / with_cache_conv_time, 2) if with_cache_conv_time > 0 else 0
    })
    
    # Calcular resumo
    total_speedup = sum(scenario['speedup'] for scenario in results['test_scenarios'])
    avg_speedup = total_speedup / len(results['test_scenarios'])
    
    results['summary'] = {
        'total_tests': len(results['test_scenarios']),
        'average_speedup': round(avg_speedup, 2),
        'cache_stats': dashboard_cache.get_cache_stats(),
        'recommendation': 'Cache ativado' if avg_speedup > 2 else 'Cache opcional'
    }
    
    return {
        'success': True,
        'data': results
    }


@router.get("/cache-demo/stats")
async def get_cache_demo_stats():
    """Estatísticas completas do sistema de cache"""
    return {
        'success': True,
        'data': {
            'dashboard_cache_stats': dashboard_cache.get_cache_stats(),
            'invalidation_policy_stats': invalidation_policy.get_invalidation_stats(),
            'cache_ttl_config': dashboard_cache.CACHE_TTL,
            'invalidation_rules': len(invalidation_policy.INVALIDATION_RULES),
            'system_info': {
                'cache_service_active': True,
                'redis_connected': True,  # Assumindo que está conectado
                'cache_types_available': list(dashboard_cache.CACHE_TTL.keys())
            }
        }
    }


@router.delete("/cache-demo/clear")
async def clear_demo_cache():
    """Limpar cache de demonstração"""
    start_time = time.time()
    
    # Reset das estatísticas
    dashboard_cache.reset_stats()
    invalidation_policy.reset_stats()
    
    # Trigger invalidação geral
    await trigger_cache_invalidation('cache_cleanup_triggered')
    
    end_time = time.time()
    clear_time = round((end_time - start_time) * 1000, 2)
    
    return {
        'success': True,
        'data': {
            'message': 'Cache de demonstração limpo com sucesso',
            'clear_time_ms': clear_time,
            'stats_reset': True
        }
    }
