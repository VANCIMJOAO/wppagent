"""
🌐 Rotas WebSocket Unificadas - Sistema Consolidado
==================================================

Sistema único e consolidado de WebSocket que elimina conflitos entre múltiplos gerenciadores.
Usa APENAS o realtime_websocket_manager.py como fonte única da verdade.

CORREÇÃO CRÍTICA: Elimina PROBLEMA #1 - Múltiplos Gerenciadores Conflitantes
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.routes.admin_auth import get_current_admin_user
from app.auth.rbac_decorators import get_current_user
from app.services.realtime_websocket_manager import (
    RealtimeEventType,
    get_realtime_manager,
    RealtimeWebSocketManager,
)
from app.schemas.websocket_events import validate_event_data, get_event_schema, EVENT_SCHEMA_MAP

logger = logging.getLogger(__name__)

# Router unificado para WebSocket
router = APIRouter(prefix="/api/websocket", tags=["WebSocket - Unificado"])

# Instância única do gerenciador
realtime_manager: RealtimeWebSocketManager = get_realtime_manager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    🔌 Endpoint WebSocket Principal - Sistema Unificado
    
    Endpoint único e consolidado que elimina conflitos entre múltiplos gerenciadores.
    Usa apenas o realtime_websocket_manager como fonte única da verdade.
    """
    connection_id = None
    user_id = None
    
    try:
        # Aceita conexão
        await websocket.accept()
        
        # Aguarda mensagem inicial com credenciais
        initial_message = await websocket.receive_text()
        data = json.loads(initial_message)
        
        user_id = data.get("user_id")
        subscriptions = data.get("subscriptions", ["global"])
        
        if not user_id:
            await websocket.close(code=1008, reason="user_id required")
            return
        
        # Conecta usando o gerenciador unificado
        connection_id = await realtime_manager.connect(
            websocket=websocket,
            user_id=user_id,
            subscriptions=subscriptions
        )
        
        if not connection_id:
            await websocket.close(code=1008, reason="connection failed")
            return
        
        logger.info(f"✅ WebSocket conectado: {connection_id} (user: {user_id})")
        
        # Loop principal de mensagens
        while True:
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # Processa mensagem usando gerenciador unificado
                await realtime_manager.handle_message(
                    connection_id=connection_id,
                    message=data
                )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Erro ao processar mensagem: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado: {connection_id}")
    except Exception as e:
        logger.error(f"Erro no WebSocket: {e}")
    finally:
        # Desconecta usando gerenciador unificado
        if connection_id:
            await realtime_manager.disconnect(connection_id)
            logger.info(f"✅ WebSocket desconectado: {connection_id}")


@router.post("/broadcast")
async def broadcast_message(
    topic: str,
    event_type: str,
    data: dict,
    current_user=Depends(get_current_admin_user)
):
    """
    📢 Broadcast de Mensagem - Sistema Unificado
    
    Envia mensagem para todos os clientes conectados em um tópico específico.
    """
    try:
        # Converte string para enum
        try:
            event_enum = RealtimeEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de evento inválido: {event_type}"
            )
        
        # Broadcast usando gerenciador unificado
        sent_count = await realtime_manager.broadcast_to_topic(
            topic=topic,
            event_type=event_enum,
            data=data
        )
        
        return {
            "success": True,
            "message": f"Mensagem enviada para {sent_count} clientes",
            "topic": topic,
            "event_type": event_type,
            "sent_count": sent_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro no broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-to-user")
async def send_to_user(
    user_id: str,
    event_type: str,
    data: dict,
    current_user=Depends(get_current_admin_user)
):
    """
    👤 Enviar para Usuário Específico - Sistema Unificado
    
    Envia mensagem para um usuário específico.
    """
    try:
        # Converte string para enum
        try:
            event_enum = RealtimeEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de evento inválido: {event_type}"
            )
        
        # Envia usando gerenciador unificado
        sent_count = await realtime_manager.send_to_user(
            user_id=user_id,
            event_type=event_enum,
            data=data
        )
        
        return {
            "success": True,
            "message": f"Mensagem enviada para {sent_count} conexões do usuário {user_id}",
            "user_id": user_id,
            "event_type": event_type,
            "sent_count": sent_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro ao enviar para usuário: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_websocket_stats(current_user=Depends(get_current_admin_user)):
    """
    📊 Estatísticas do WebSocket - Sistema Unificado
    
    Retorna estatísticas completas do sistema WebSocket consolidado.
    """
    try:
        stats = await realtime_manager.get_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_connections(current_user=Depends(get_current_admin_user)):
    """
    🧹 Limpeza de Conexões - Sistema Unificado
    
    Remove conexões obsoletas e otimiza o sistema.
    """
    try:
        cleaned_count = await realtime_manager.cleanup_stale_connections()
        
        return {
            "success": True,
            "message": f"{cleaned_count} conexões obsoletas removidas",
            "cleaned_count": cleaned_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/force")
async def force_cleanup_all_connections(current_user=Depends(get_current_admin_user)):
    """
    🚨 Limpeza Forçada de Todas as Conexões - Sistema Unificado
    
    CORREÇÃO CRÍTICA: Força limpeza de todas as conexões para resolver vazamentos.
    Use apenas em emergências ou para resolver problemas de vazamento de memória.
    """
    try:
        cleaned_count = await realtime_manager.force_cleanup_all()
        
        return {
            "success": True,
            "message": f"Limpeza forçada concluída: {cleaned_count} conexões removidas",
            "cleaned_count": cleaned_count,
            "warning": "Todas as conexões foram desconectadas",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro na limpeza forçada: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/user/{user_id}")
async def cleanup_user_connections(
    user_id: str,
    current_user=Depends(get_current_admin_user)
):
    """
    👤 Limpeza de Conexões de Usuário Específico - Sistema Unificado
    
    CORREÇÃO CRÍTICA: Força limpeza de todas as conexões de um usuário específico.
    Útil para resolver problemas de reconexão ou logout forçado.
    """
    try:
        await realtime_manager.disconnect_user(user_id, "Admin cleanup")
        
        return {
            "success": True,
            "message": f"Todas as conexões do usuário {user_id} foram desconectadas",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro na limpeza do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cleanup/stats")
async def get_cleanup_stats(current_user=Depends(get_current_admin_user)):
    """
    📊 Estatísticas de Limpeza - Sistema Unificado
    
    CORREÇÃO CRÍTICA: Retorna estatísticas detalhadas sobre limpeza e vazamentos.
    Inclui detecção de possíveis vazamentos de memória.
    """
    try:
        stats = await realtime_manager.get_stats()
        connection_stats = stats.get("connection_cleanup", {})
        
        return {
            "success": True,
            "cleanup_stats": connection_stats,
            "recommendations": {
                "force_cleanup_needed": connection_stats.get("cleanup_recommended", False),
                "potential_leaks_detected": len(connection_stats.get("potential_leaks", [])) > 0,
                "memory_usage_high": connection_stats.get("memory_usage_estimate", 0) > 1024 * 1024,  # > 1MB
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de limpeza: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/heartbeat/config")
async def get_heartbeat_config(current_user=Depends(get_current_admin_user)):
    """
    ⏱️ Configuração de Heartbeat - Sistema Unificado
    
    CORREÇÃO CRÍTICA: Retorna configurações atuais de timeout de heartbeat.
    Inclui timeouts diferenciados para mobile e desktop.
    """
    try:
        return {
            "success": True,
            "heartbeat_config": {
                "desktop_timeout": realtime_manager.heartbeat_timeout_desktop,
                "mobile_timeout": realtime_manager.heartbeat_timeout_mobile,
                "heartbeat_interval": realtime_manager.heartbeat_interval,
                "description": {
                    "desktop_timeout": "Timeout para conexões desktop (30s)",
                    "mobile_timeout": "Timeout para conexões mobile (60s - mais tolerante)",
                    "heartbeat_interval": "Intervalo entre envios de heartbeat (30s)"
                }
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter configuração de heartbeat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/heartbeat/config")
async def update_heartbeat_config(
    desktop_timeout: int = None,
    mobile_timeout: int = None,
    heartbeat_interval: int = None,
    current_user=Depends(get_current_admin_user)
):
    """
    ⚙️ Atualizar Configuração de Heartbeat - Sistema Unificado
    
    CORREÇÃO CRÍTICA: Permite configurar timeouts de heartbeat dinamicamente.
    Útil para ajustar comportamento em diferentes ambientes.
    """
    try:
        # Validações
        if desktop_timeout is not None and (desktop_timeout < 10 or desktop_timeout > 300):
            raise HTTPException(
                status_code=400, 
                detail="Timeout desktop deve estar entre 10 e 300 segundos"
            )
        
        if mobile_timeout is not None and (mobile_timeout < 10 or mobile_timeout > 600):
            raise HTTPException(
                status_code=400, 
                detail="Timeout mobile deve estar entre 10 e 600 segundos"
            )
        
        if heartbeat_interval is not None and (heartbeat_interval < 5 or heartbeat_interval > 120):
            raise HTTPException(
                status_code=400, 
                detail="Intervalo de heartbeat deve estar entre 5 e 120 segundos"
            )
        
        # Atualiza configurações
        if desktop_timeout is not None:
            realtime_manager.heartbeat_timeout_desktop = desktop_timeout
        
        if mobile_timeout is not None:
            realtime_manager.heartbeat_timeout_mobile = mobile_timeout
        
        if heartbeat_interval is not None:
            realtime_manager.heartbeat_interval = heartbeat_interval
        
        return {
            "success": True,
            "message": "Configuração de heartbeat atualizada com sucesso",
            "new_config": {
                "desktop_timeout": realtime_manager.heartbeat_timeout_desktop,
                "mobile_timeout": realtime_manager.heartbeat_timeout_mobile,
                "heartbeat_interval": realtime_manager.heartbeat_interval,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração de heartbeat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def websocket_health():
    """
    ❤️ Health Check - Sistema Unificado
    
    Verifica a saúde do sistema WebSocket consolidado.
    """
    try:
        stats = await realtime_manager.get_stats()
        
        # Determina status de saúde
        health_status = "healthy"
        if stats["total_connections"] == 0:
            health_status = "no_connections"
        elif stats["stale_connections"] > stats["total_connections"] * 0.5:
            health_status = "degraded"
        
        return {
            "status": health_status,
            "total_connections": stats["total_connections"],
            "active_connections": stats["active_connections"],
            "stale_connections": stats["stale_connections"],
            "topics": list(stats["topics"].keys()),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/events/types")
async def get_event_types():
    """
    📋 Tipos de Eventos Disponíveis - Sistema Unificado
    
    Retorna lista de todos os tipos de eventos suportados.
    """
    try:
        event_types = [
            {
                "value": event_type.value,
                "name": event_type.name,
                "description": getattr(event_type, "description", ""),
            }
            for event_type in RealtimeEventType
        ]
        
        return {
            "success": True,
            "event_types": event_types,
            "count": len(event_types),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter tipos de eventos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/broadcast")
async def test_broadcast(
    message: str = "Teste de broadcast",
    topic: str = "test",
    current_user=Depends(get_current_admin_user)
):
    """
    🧪 Teste de Broadcast - Sistema Unificado
    
    Endpoint para testar o sistema de broadcast.
    """
    try:
        test_data = {
            "message": message,
            "test_id": f"test_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        sent_count = await realtime_manager.broadcast_to_topic(
            topic=topic,
            event_type=RealtimeEventType.TEST_EVENT,
            data=test_data
        )
        
        return {
            "success": True,
            "message": f"Teste enviado para {sent_count} clientes",
            "topic": topic,
            "sent_count": sent_count,
            "test_data": test_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro no teste de broadcast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE MIGRAÇÃO E COMPATIBILIDADE
# ============================================================================

@router.get("/migration/status")
async def migration_status(current_user=Depends(get_current_admin_user)):
    """
    🔄 Status da Migração - Sistema Unificado
    
    Retorna informações sobre a migração para o sistema unificado.
    """
    try:
        stats = await realtime_manager.get_stats()
        
        return {
            "success": True,
            "migration_status": "completed",
            "unified_system": True,
            "active_connections": stats["total_connections"],
            "supported_features": [
                "Unified WebSocket Management",
                "Real-time Broadcasting",
                "User-specific Messaging",
                "Topic-based Subscriptions",
                "Connection Health Monitoring",
                "Automatic Cleanup",
                "Event History",
                "Persistent Storage",
            ],
            "deprecated_systems": [
                "websocket_manager.py",
                "websocket_realtime.py",
                "websocket.py",
                "websocket_realtime_advanced.py",
                "websocket_realtime_new.py",
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter status de migração: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migration/cleanup-old")
async def cleanup_old_systems(current_user=Depends(get_current_admin_user)):
    """
    🗑️ Limpeza de Sistemas Antigos - Sistema Unificado
    
    Remove arquivos e dependências dos sistemas WebSocket antigos.
    ATENÇÃO: Use com cuidado - pode quebrar compatibilidade.
    """
    try:
        # Lista de arquivos que devem ser removidos/movidos
        deprecated_files = [
            "app/services/websocket_manager.py",
            "app/routes/websocket_realtime.py",
            "app/routes/websocket.py",
            "app/routes/websocket_realtime_advanced.py",
            "app/routes/websocket_realtime_new.py",
            "app/routes/websocket_test.py",
        ]
        
        # Por segurança, apenas retorna a lista sem deletar
        return {
            "success": True,
            "message": "Lista de arquivos obsoletos identificados",
            "deprecated_files": deprecated_files,
            "warning": "Arquivos NÃO foram removidos automaticamente por segurança",
            "recommendation": "Remova manualmente após verificar dependências",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Erro na limpeza de sistemas antigos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= ENDPOINTS DE VALIDAÇÃO DE SCHEMA =============

@router.get("/schemas")
async def list_event_schemas(current_user=Depends(get_current_admin_user)):
    """
    📋 Lista Schemas de Eventos - Sistema Unificado
    
    CORREÇÃO: Retorna todos os schemas Pydantic disponíveis para validação de eventos.
    Útil para documentação e debugging de validação.
    """
    try:
        realtime_manager = get_realtime_manager()
        schemas = realtime_manager.list_available_schemas()
        
        return {
            "success": True,
            "data": {
                "schemas": schemas,
                "total_schemas": len(schemas),
                "description": "Schemas Pydantic para validação de eventos WebSocket"
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar schemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schemas/{event_type}")
async def get_event_schema_info(event_type: str, current_user=Depends(get_current_admin_user)):
    """
    🔍 Informações de Schema de Evento - Sistema Unificado
    
    CORREÇÃO: Retorna informações detalhadas sobre o schema de um tipo de evento específico.
    """
    try:
        schema_class = get_event_schema(event_type)
        
        if not schema_class:
            raise HTTPException(
                status_code=404, 
                detail=f"Schema não encontrado para evento: {event_type}"
            )
        
        # Obter informações do schema
        schema_info = {
            "event_type": event_type,
            "schema_class": schema_class.__name__,
            "fields": {},
            "required_fields": [],
            "optional_fields": [],
        }
        
        # Analisar campos do schema
        if hasattr(schema_class, 'model_fields'):
            for field_name, field_info in schema_class.model_fields.items():
                field_data = {
                    "type": str(field_info.annotation),
                    "description": field_info.description or "",
                    "default": field_info.default if field_info.default is not None else "Nenhum",
                }
                schema_info["fields"][field_name] = field_data
                
                if field_info.is_required():
                    schema_info["required_fields"].append(field_name)
                else:
                    schema_info["optional_fields"].append(field_name)
        
        return {
            "success": True,
            "data": schema_info,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter schema do evento {event_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_event_data_endpoint(
    event_type: str,
    data: Dict[str, Any],
    current_user=Depends(get_current_admin_user)
):
    """
    ✅ Validar Dados de Evento - Sistema Unificado
    
    CORREÇÃO: Valida dados de evento usando schema Pydantic.
    Útil para testar dados antes de enviar via WebSocket.
    """
    try:
        # Validar dados
        validated_data = validate_event_data(event_type, data)
        
        return {
            "success": True,
            "data": {
                "event_type": event_type,
                "original_data": data,
                "validated_data": validated_data,
                "validation_passed": True,
            },
            "message": "Dados validados com sucesso",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except ValueError as e:
        return {
            "success": False,
            "data": {
                "event_type": event_type,
                "original_data": data,
                "validation_passed": False,
                "error": str(e),
            },
            "message": "Erro de validação",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao validar dados do evento {event_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-appointment-created")
async def test_appointment_created_event(current_user=Depends(get_current_admin_user)):
    """
    🧪 Teste de Evento Appointment Created - Sistema Unificado
    
    CORREÇÃO: Testa a validação do evento appointment_created com dados válidos e inválidos.
    """
    try:
        from app.schemas.websocket_events import AppointmentCreatedData, AppointmentData, AppointmentStatus
        
        # Dados válidos
        valid_data = {
            "appointment": {
                "id": 123,
                "client_name": "João Silva",
                "client_phone": "+5511999999999",
                "service_name": "Corte de Cabelo",
                "business_name": "Salão da Maria",
                "date_time": "2025-10-01T14:30:00Z",
                "status": "confirmed",
                "duration_minutes": 60,
                "price": 50.0,
                "notes": "Cliente preferencial",
                "created_by": "admin",
                "updated_by": "admin"
            },
            "message": "Novo agendamento criado com sucesso"
        }
        
        # Dados inválidos (para testar validação)
        invalid_data = {
            "appointment": {
                "id": "invalid_id",  # Deveria ser int
                "client_name": "",   # Deveria ter pelo menos 1 caractere
                "service_name": "Serviço",
                "business_name": "Negócio",
                "date_time": "invalid_date",  # Deveria ser datetime válido
                "status": "invalid_status",   # Deveria ser enum válido
            },
            "message": "Teste de validação"
        }
        
        # Testar dados válidos
        try:
            validated_valid = validate_event_data("appointment_created", valid_data)
            valid_test_passed = True
        except Exception as e:
            validated_valid = None
            valid_test_passed = False
            valid_error = str(e)
        
        # Testar dados inválidos
        try:
            validated_invalid = validate_event_data("appointment_created", invalid_data)
            invalid_test_passed = True
        except Exception as e:
            validated_invalid = None
            invalid_test_passed = False
            invalid_error = str(e)
        
        return {
            "success": True,
            "data": {
                "valid_data_test": {
                    "passed": valid_test_passed,
                    "validated_data": validated_valid,
                    "error": valid_error if not valid_test_passed else None,
                },
                "invalid_data_test": {
                    "passed": invalid_test_passed,
                    "expected_to_fail": True,
                    "error": invalid_error if not invalid_test_passed else None,
                },
                "test_summary": {
                    "valid_data_validation": "✅ PASSOU" if valid_test_passed else "❌ FALHOU",
                    "invalid_data_validation": "✅ PASSOU (rejeitou dados inválidos)" if not invalid_test_passed else "❌ FALHOU (aceitou dados inválidos)",
                }
            },
            "message": "Teste de validação de schema concluído",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro no teste de validação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE CONFIRMAÇÃO DE ENTREGA (ACK)
# ============================================================================

@router.get("/ack/stats")
async def get_ack_stats(current_user=Depends(get_current_admin_user)):
    """
    📊 Estatísticas de Confirmação de Entrega - Sistema Unificado
    
    CORREÇÃO: Retorna estatísticas detalhadas do sistema ACK.
    """
    try:
        realtime_manager = get_realtime_manager()
        ack_stats = realtime_manager.get_ack_stats()
        
        return {
            "success": True,
            "data": ack_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de ACK: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ack/reset-stats")
async def reset_ack_stats(current_user=Depends(get_current_admin_user)):
    """
    🔄 Resetar Estatísticas de ACK - Sistema Unificado
    
    CORREÇÃO: Reseta todas as estatísticas do sistema ACK.
    """
    try:
        realtime_manager = get_realtime_manager()
        realtime_manager.reset_ack_stats()
        
        return {
            "success": True,
            "data": {"message": "Estatísticas de ACK resetadas com sucesso"},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao resetar estatísticas de ACK: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ack/cleanup")
async def force_ack_cleanup(current_user=Depends(get_current_admin_user)):
    """
    🧹 Limpeza Forçada de ACKs - Sistema Unificado
    
    CORREÇÃO: Remove todas as mensagens pendentes de confirmação.
    """
    try:
        realtime_manager = get_realtime_manager()
        cleaned_count = await realtime_manager.force_ack_cleanup()
        
        return {
            "success": True,
            "data": {
                "cleaned_messages": cleaned_count,
                "message": f"{cleaned_count} mensagens pendentes removidas"
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza forçada de ACKs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ack/test")
async def test_ack_system(current_user=Depends(get_current_admin_user)):
    """
    🧪 Teste do Sistema ACK - Sistema Unificado
    
    CORREÇÃO: Testa o sistema de confirmação de entrega.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        # Obter uma conexão ativa para teste
        if not realtime_manager.connections:
            return {
                "success": False,
                "data": {"message": "Nenhuma conexão ativa para teste"},
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Usar a primeira conexão disponível
        connection_id = list(realtime_manager.connections.keys())[0]
        
        # Enviar mensagem de teste com ACK
        test_data = {
            "test_message": "Teste de confirmação de entrega",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        success = await realtime_manager.send_with_ack(
            connection_id=connection_id,
            event_type=RealtimeEventType.SYSTEM_NOTIFICATION,
            data=test_data,
            timeout=10.0  # 10 segundos para teste
        )
        
        return {
            "success": True,
            "data": {
                "test_connection": connection_id,
                "ack_received": success,
                "test_data": test_data,
                "message": "Teste de ACK executado com sucesso" if success else "Teste de ACK falhou"
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro no teste do sistema ACK: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE EVENTOS DE MENSAGEM
# ============================================================================

@router.post("/message/mark-delivered")
async def mark_message_delivered(
    message_id: str,
    conversation_id: str = None,
    user_id: str = None,
    current_user=Depends(get_current_admin_user)
):
    """
    📬 Marcar Mensagem como Entregue - Sistema Unificado
    
    CORREÇÃO: Marca uma mensagem como entregue e notifica via WebSocket.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        success = await realtime_manager.mark_message_as_delivered(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return {
            "success": success,
            "data": {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "status": "delivered",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "message": "Mensagem marcada como entregue" if success else "Falha ao marcar mensagem como entregue",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao marcar mensagem como entregue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/mark-read")
async def mark_message_read(
    message_id: str,
    conversation_id: str = None,
    user_id: str = None,
    current_user=Depends(get_current_admin_user)
):
    """
    👁️ Marcar Mensagem como Lida - Sistema Unificado
    
    CORREÇÃO: Marca uma mensagem como lida e notifica via WebSocket.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        success = await realtime_manager.mark_message_as_read(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return {
            "success": success,
            "data": {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "status": "read",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "message": "Mensagem marcada como lida" if success else "Falha ao marcar mensagem como lida",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao marcar mensagem como lida: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/mark-multiple-delivered")
async def mark_multiple_messages_delivered(
    message_ids: List[str],
    conversation_id: str = None,
    user_id: str = None,
    current_user=Depends(get_current_admin_user)
):
    """
    📬 Marcar Múltiplas Mensagens como Entregues - Sistema Unificado
    
    CORREÇÃO: Marca múltiplas mensagens como entregues em lote.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        success_count = await realtime_manager.mark_multiple_messages_as_delivered(
            message_ids=message_ids,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return {
            "success": success_count > 0,
            "data": {
                "message_ids": message_ids,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "success_count": success_count,
                "total_count": len(message_ids),
                "status": "delivered",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "message": f"{success_count}/{len(message_ids)} mensagens marcadas como entregues",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao marcar múltiplas mensagens como entregues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/mark-multiple-read")
async def mark_multiple_messages_read(
    message_ids: List[str],
    conversation_id: str = None,
    user_id: str = None,
    current_user=Depends(get_current_admin_user)
):
    """
    👁️ Marcar Múltiplas Mensagens como Lidas - Sistema Unificado
    
    CORREÇÃO: Marca múltiplas mensagens como lidas em lote.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        success_count = await realtime_manager.mark_multiple_messages_as_read(
            message_ids=message_ids,
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return {
            "success": success_count > 0,
            "data": {
                "message_ids": message_ids,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "success_count": success_count,
                "total_count": len(message_ids),
                "status": "read",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "message": f"{success_count}/{len(message_ids)} mensagens marcadas como lidas",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao marcar múltiplas mensagens como lidas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/test-events")
async def test_message_events(current_user=Depends(get_current_admin_user)):
    """
    🧪 Teste de Eventos de Mensagem - Sistema Unificado
    
    CORREÇÃO: Testa os eventos MESSAGE_DELIVERED e MESSAGE_READ.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        # Verificar se há conexões ativas
        if not realtime_manager.connections:
            return {
                "success": False,
                "data": {"message": "Nenhuma conexão ativa para teste"},
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Usar a primeira conexão disponível
        connection_id = list(realtime_manager.connections.keys())[0]
        
        # Teste de mensagem entregue
        test_message_id = f"test_delivered_{uuid.uuid4().hex[:8]}"
        delivered_success = await realtime_manager.mark_message_as_delivered(
            message_id=test_message_id,
            conversation_id="test_conversation",
            user_id="test_user"
        )
        
        # Teste de mensagem lida
        test_message_id_read = f"test_read_{uuid.uuid4().hex[:8]}"
        read_success = await realtime_manager.mark_message_as_read(
            message_id=test_message_id_read,
            conversation_id="test_conversation",
            user_id="test_user"
        )
        
        return {
            "success": delivered_success and read_success,
            "data": {
                "test_connection": connection_id,
                "delivered_test": {
                    "message_id": test_message_id,
                    "success": delivered_success,
                },
                "read_test": {
                    "message_id": test_message_id_read,
                    "success": read_success,
                },
                "message": "Teste de eventos de mensagem executado com sucesso" if (delivered_success and read_success) else "Teste de eventos de mensagem falhou"
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro no teste de eventos de mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE RECUPERAÇÃO DE MENSAGENS
# ============================================================================

@router.get("/recovery/last-message-id/{user_id}")
async def get_last_message_id(
    user_id: str,
    current_user=Depends(get_current_admin_user)
):
    """
    📝 Obter Last Message ID - Sistema Unificado
    
    CORREÇÃO: Retorna o ID da última mensagem recebida por um usuário.
    """
    try:
        realtime_manager = get_realtime_manager()
        last_message_id = await realtime_manager.get_last_message_id(user_id)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "last_message_id": last_message_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "message": "Last message ID obtido com sucesso" if last_message_id else "Nenhuma mensagem encontrada",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter last message ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/set-last-message-id")
async def set_last_message_id(
    user_id: str,
    message_id: str,
    current_user=Depends(get_current_admin_user)
):
    """
    📝 Definir Last Message ID - Sistema Unificado
    
    CORREÇÃO: Define o ID da última mensagem recebida por um usuário.
    """
    try:
        realtime_manager = get_realtime_manager()
        await realtime_manager.set_last_message_id(user_id, message_id)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "message": "Last message ID definido com sucesso",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao definir last message ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/simulate-reconnection")
async def simulate_reconnection(
    user_id: str,
    last_message_id: str = None,
    current_user=Depends(get_current_admin_user)
):
    """
    🔄 Simular Reconexão - Sistema Unificado
    
    CORREÇÃO: Simula uma reconexão e recupera mensagens perdidas.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        # Verificar se há conexões ativas para o usuário
        if user_id not in realtime_manager.user_connections:
            return {
                "success": False,
                "data": {"message": f"Nenhuma conexão ativa para usuário {user_id}"},
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Usar a primeira conexão do usuário
        connection_id = list(realtime_manager.user_connections[user_id])[0]
        
        # Simular recuperação de mensagens
        if last_message_id:
            recovered_count = await realtime_manager._recover_missed_messages(
                connection_id, user_id, last_message_id
            )
        else:
            # Se não fornecido, usar o last_message_id atual
            current_last_id = await realtime_manager.get_last_message_id(user_id)
            if current_last_id:
                recovered_count = await realtime_manager._recover_missed_messages(
                    connection_id, user_id, current_last_id
                )
            else:
                recovered_count = 0
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "connection_id": connection_id,
                "last_message_id": last_message_id or current_last_id,
                "recovered_messages": recovered_count,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "message": f"Reconexão simulada: {recovered_count} mensagens recuperadas",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro na simulação de reconexão: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recovery/history-stats")
async def get_recovery_history_stats(current_user=Depends(get_current_admin_user)):
    """
    📊 Estatísticas do Histórico de Recuperação - Sistema Unificado
    
    CORREÇÃO: Retorna estatísticas do sistema de recuperação de mensagens.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        # Estatísticas do histórico
        history_stats = {
            "total_messages_in_history": len(realtime_manager.message_history),
            "max_history_size": realtime_manager.max_history_size,
            "recovery_enabled": realtime_manager.reconnection_recovery_enabled,
            "users_with_last_message_id": len(realtime_manager.last_message_ids),
            "oldest_message_timestamp": None,
            "newest_message_timestamp": None,
        }
        
        # Timestamps das mensagens
        if realtime_manager.message_history:
            timestamps = [msg.get("timestamp") for msg in realtime_manager.message_history if msg.get("timestamp")]
            if timestamps:
                history_stats["oldest_message_timestamp"] = min(timestamps)
                history_stats["newest_message_timestamp"] = max(timestamps)
        
        return {
            "success": True,
            "data": history_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/clear-history")
async def clear_recovery_history(current_user=Depends(get_current_admin_user)):
    """
    🧹 Limpar Histórico de Recuperação - Sistema Unificado
    
    CORREÇÃO: Limpa o histórico de mensagens para recuperação.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        # Contar mensagens antes da limpeza
        messages_count = len(realtime_manager.message_history)
        
        # Limpar histórico
        realtime_manager.message_history.clear()
        realtime_manager.last_message_ids.clear()
        
        return {
            "success": True,
            "data": {
                "cleared_messages": messages_count,
                "message": f"{messages_count} mensagens removidas do histórico",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao limpar histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/test-recovery")
async def test_message_recovery(current_user=Depends(get_current_admin_user)):
    """
    🧪 Teste de Recuperação de Mensagens - Sistema Unificado
    
    CORREÇÃO: Testa o sistema de recuperação de mensagens.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        # Verificar se há conexões ativas
        if not realtime_manager.connections:
            return {
                "success": False,
                "data": {"message": "Nenhuma conexão ativa para teste"},
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Usar a primeira conexão disponível
        connection_id = list(realtime_manager.connections.keys())[0]
        connection = realtime_manager.connections[connection_id]
        user_id = connection.user_id
        
        # Adicionar algumas mensagens de teste ao histórico
        test_messages = []
        for i in range(5):
            test_msg = {
                "id": f"test_msg_{i}_{uuid.uuid4().hex[:8]}",
                "type": "test_message",
                "data": {"content": f"Mensagem de teste {i}", "test": True},
                "timestamp": datetime.utcnow().isoformat(),
                "priority": 1,
                "target_user": user_id,
                "source_user": "system"
            }
            realtime_manager.message_history.append(test_msg)
            test_messages.append(test_msg["id"])
        
        # Simular reconexão com last_message_id do meio
        middle_message_id = test_messages[2]  # Terceira mensagem
        recovered_count = await realtime_manager._recover_missed_messages(
            connection_id, user_id, middle_message_id
        )
        
        return {
            "success": True,
            "data": {
                "test_connection": connection_id,
                "test_user": user_id,
                "test_messages_created": len(test_messages),
                "last_message_id_used": middle_message_id,
                "recovered_messages": recovered_count,
                "expected_recovered": 2,  # Duas mensagens após a do meio
                "message": "Teste de recuperação executado com sucesso"
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro no teste de recuperação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE SAÚDE DAS CONEXÕES
# ============================================================================

@router.get("/health/connections")
async def get_connection_health_stats(current_user=Depends(get_current_admin_user)):
    """
    🏥 Estatísticas de Saúde das Conexões - Sistema Unificado
    
    CORREÇÃO: Retorna estatísticas de saúde das conexões WebSocket.
    """
    try:
        realtime_manager = get_realtime_manager()
        health_stats = await realtime_manager.get_connection_health_stats()
        
        return {
            "success": True,
            "data": health_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de saúde: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/cleanup-dead-connections")
async def cleanup_dead_connections(current_user=Depends(get_current_admin_user)):
    """
    🧹 Limpeza de Conexões Mortas - Sistema Unificado
    
    CORREÇÃO: Remove conexões WebSocket mortas/inativas.
    """
    try:
        realtime_manager = get_realtime_manager()
        removed_count = await realtime_manager.cleanup_dead_connections()
        
        return {
            "success": True,
            "data": {
                "removed_connections": removed_count,
                "message": f"{removed_count} conexões mortas removidas",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza de conexões mortas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/test-connection-state")
async def test_connection_state_validation(current_user=Depends(get_current_admin_user)):
    """
    🧪 Teste de Validação de Estado das Conexões - Sistema Unificado
    
    CORREÇÃO: Testa o sistema de validação de estado das conexões.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        # Verificar se há conexões ativas
        if not realtime_manager.connections:
            return {
                "success": False,
                "data": {"message": "Nenhuma conexão ativa para teste"},
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Testar validação de saúde das conexões
        health_stats = await realtime_manager.get_connection_health_stats()
        
        # Simular teste de envio para conexões saudáveis
        test_results = []
        for connection_id, connection in realtime_manager.connections.items():
            is_healthy = realtime_manager._is_connection_healthy(connection)
            test_results.append({
                "connection_id": connection_id,
                "user_id": connection.user_id,
                "is_healthy": is_healthy,
                "status": connection.status.value if hasattr(connection.status, 'value') else str(connection.status),
                "has_websocket": connection.websocket is not None,
                "websocket_state": getattr(connection.websocket, 'client_state', 'unknown') if connection.websocket else 'no_websocket'
            })
        
        return {
            "success": True,
            "data": {
                "health_stats": health_stats,
                "connection_tests": test_results,
                "total_tested": len(test_results),
                "healthy_count": sum(1 for r in test_results if r["is_healthy"]),
                "message": "Teste de validação de estado executado com sucesso"
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro no teste de validação de estado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/websocket-states")
async def get_websocket_states(current_user=Depends(get_current_admin_user)):
    """
    🔍 Estados dos WebSockets - Sistema Unificado
    
    CORREÇÃO: Retorna detalhes dos estados de todas as conexões WebSocket.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        connection_details = []
        for connection_id, connection in realtime_manager.connections.items():
            websocket_state = "unknown"
            if connection.websocket and hasattr(connection.websocket, 'client_state'):
                websocket_state = connection.websocket.client_state.name if hasattr(connection.websocket.client_state, 'name') else str(connection.websocket.client_state)
            
            connection_details.append({
                "connection_id": connection_id,
                "user_id": connection.user_id,
                "status": connection.status.value if hasattr(connection.status, 'value') else str(connection.status),
                "websocket_state": websocket_state,
                "is_healthy": realtime_manager._is_connection_healthy(connection),
                "last_activity": connection.last_activity.isoformat(),
                "connected_at": connection.connected_at.isoformat(),
                "room": connection.room,
                "subscriptions": list(connection.subscriptions)
            })
        
        return {
            "success": True,
            "data": {
                "total_connections": len(connection_details),
                "connections": connection_details,
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estados dos WebSockets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS DE RATE LIMITING
# ============================================================================

@router.get("/rate-limit/stats")
async def get_rate_limiter_stats(current_user=Depends(get_current_admin_user)):
    """
    📊 Estatísticas do Rate Limiter - Sistema Unificado
    
    CORREÇÃO: Retorna estatísticas do sistema de rate limiting.
    """
    try:
        realtime_manager = get_realtime_manager()
        stats = await realtime_manager.get_rate_limiter_stats()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do rate limiter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate-limit/configure")
async def configure_rate_limiting(
    max_messages: int = None,
    window_seconds: int = None,
    enabled: bool = None,
    current_user=Depends(get_current_admin_user)
):
    """
    ⚙️ Configurar Rate Limiting - Sistema Unificado
    
    CORREÇÃO: Configura parâmetros do sistema de rate limiting.
    """
    try:
        realtime_manager = get_realtime_manager()
        success = await realtime_manager.configure_rate_limiting(
            max_messages=max_messages,
            window_seconds=window_seconds,
            enabled=enabled
        )
        
        return {
            "success": success,
            "data": {
                "max_messages": max_messages,
                "window_seconds": window_seconds,
                "enabled": enabled,
                "message": "Rate limiting configurado com sucesso" if success else "Falha ao configurar rate limiting",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao configurar rate limiting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate-limit/unblock-connection")
async def unblock_connection(
    connection_id: str,
    current_user=Depends(get_current_admin_user)
):
    """
    🔓 Desbloquear Conexão - Sistema Unificado
    
    CORREÇÃO: Desbloqueia uma conexão específica do rate limiting.
    """
    try:
        realtime_manager = get_realtime_manager()
        success = await realtime_manager.unblock_connection(connection_id)
        
        return {
            "success": success,
            "data": {
                "connection_id": connection_id,
                "message": f"Conexão {connection_id} desbloqueada" if success else f"Falha ao desbloquear conexão {connection_id}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao desbloquear conexão: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate-limit/reset-stats")
async def reset_rate_limiter_stats(current_user=Depends(get_current_admin_user)):
    """
    🔄 Resetar Estatísticas do Rate Limiter - Sistema Unificado
    
    CORREÇÃO: Reseta as estatísticas do sistema de rate limiting.
    """
    try:
        realtime_manager = get_realtime_manager()
        success = await realtime_manager.reset_rate_limiter_stats()
        
        return {
            "success": success,
            "data": {
                "message": "Estatísticas do rate limiter resetadas" if success else "Falha ao resetar estatísticas",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao resetar estatísticas do rate limiter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rate-limit/test")
async def test_rate_limiting(current_user=Depends(get_current_admin_user)):
    """
    🧪 Teste de Rate Limiting - Sistema Unificado
    
    CORREÇÃO: Testa o sistema de rate limiting.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        # Verificar se há conexões ativas
        if not realtime_manager.connections:
            return {
                "success": False,
                "data": {"message": "Nenhuma conexão ativa para teste"},
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Usar a primeira conexão disponível
        connection_id = list(realtime_manager.connections.keys())[0]
        connection = realtime_manager.connections[connection_id]
        
        # Testar rate limiting
        test_results = []
        for i in range(5):  # Testar 5 mensagens
            is_allowed = realtime_manager.rate_limiter.is_allowed(connection_id)
            test_results.append({
                "message_number": i + 1,
                "is_allowed": is_allowed,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Obter estatísticas atuais
        stats = await realtime_manager.get_rate_limiter_stats()
        
        return {
            "success": True,
            "data": {
                "test_connection": connection_id,
                "test_user": connection.user_id,
                "test_results": test_results,
                "rate_limiter_stats": stats,
                "message": "Teste de rate limiting executado com sucesso"
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro no teste de rate limiting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limit/blocked-connections")
async def get_blocked_connections(current_user=Depends(get_current_admin_user)):
    """
    🚫 Conexões Bloqueadas - Sistema Unificado
    
    CORREÇÃO: Retorna lista de conexões bloqueadas pelo rate limiting.
    """
    try:
        realtime_manager = get_realtime_manager()
        
        blocked_connections = list(realtime_manager.rate_limiter.blocked_connections)
        
        # Obter detalhes das conexões bloqueadas
        blocked_details = []
        for conn_id in blocked_connections:
            if conn_id in realtime_manager.connections:
                connection = realtime_manager.connections[conn_id]
                blocked_details.append({
                    "connection_id": conn_id,
                    "user_id": connection.user_id,
                    "blocked_at": datetime.utcnow().isoformat(),
                    "status": connection.status.value if hasattr(connection.status, 'value') else str(connection.status)
                })
        
        return {
            "success": True,
            "data": {
                "blocked_connections": blocked_details,
                "total_blocked": len(blocked_connections),
                "timestamp": datetime.utcnow().isoformat(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter conexões bloqueadas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INICIALIZAÇÃO E CONFIGURAÇÃO
# ============================================================================

# Controle para evitar inicialização duplicada
_websocket_initialized = False

@router.on_event("startup")
async def startup_websocket_system():
    """
    🚀 Inicialização do Sistema WebSocket Unificado
    
    Configura e inicializa o sistema WebSocket consolidado.
    """
    global _websocket_initialized
    
    if _websocket_initialized:
        return  # Já foi inicializado
    
    try:
        logger.info("🚀 Iniciando sistema WebSocket unificado...")
        
        # O gerenciador já está inicializado automaticamente
        logger.info("✅ Sistema WebSocket unificado iniciado com sucesso")
        _websocket_initialized = True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar sistema WebSocket: {e}")
        raise


@router.on_event("shutdown")
async def shutdown_websocket_system():
    """
    🛑 Finalização do Sistema WebSocket Unificado
    
    Limpa recursos e finaliza o sistema WebSocket.
    """
    try:
        logger.info("🛑 Finalizando sistema WebSocket unificado...")
        
        # Finaliza o gerenciador
        await realtime_manager.shutdown()
        
        logger.info("✅ Sistema WebSocket unificado finalizado com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro ao finalizar sistema WebSocket: {e}")
