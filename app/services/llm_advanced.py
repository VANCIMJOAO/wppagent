"""
Sistema de LLM Estruturado e Avançado
Implementa patterns de design para conversas contextuais e inteligentes
"""
import json
import openai
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging

from app.config import settings
from app.utils.logger import get_logger
from app.models.database import User, Conversation, Message, Appointment
logger = get_logger(__name__)
from app.utils.dynamic_prompts import get_dynamic_llm_system_prompt, get_dynamic_data_extraction_prompt
from .retry_handler import retry_handler
from .alert_manager import alert_llm_service_error
from .cost_tracker import cost_tracker

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Estados possíveis da conversa"""
    INITIAL = "initial"
    COLLECTING_INFO = "collecting_info"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"
    HANDOFF = "handoff"


class IntentType(Enum):
    """Tipos de intenção detectadas"""
    GREETING = "greeting"
    SCHEDULE_CREATE = "schedule_create"
    SCHEDULE_CANCEL = "schedule_cancel"
    SCHEDULE_RESCHEDULE = "schedule_reschedule"
    CHECK_APPOINTMENTS = "check_appointments"
    GENERAL_INFO = "general_info"
    HUMAN_HANDOFF = "human_handoff"
    COMPLAINT = "complaint"
    SMALL_TALK = "small_talk"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Representa uma intenção detectada"""
    type: IntentType
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    requires_data: List[str] = field(default_factory=list)
    next_questions: List[str] = field(default_factory=list)


@dataclass
class ConversationContext:
    """Contexto completo da conversa"""
    user_id: str
    conversation_id: str
    state: ConversationState
    current_intent: Optional[Intent] = None
    collected_data: Dict[str, Any] = field(default_factory=dict)
    message_history: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LLMResponse:
    """Resposta estruturada do LLM"""
    text: str
    intent: Optional[Intent] = None
    suggested_actions: List[Dict] = field(default_factory=list)
    interactive_buttons: List[Dict] = field(default_factory=list)
    requires_function_call: bool = False
    function_call: Optional[Dict] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromptTemplate:
    """Sistema de templates de prompts estruturados com data dinâmica"""
    
    @staticmethod
    async def get_system_base_with_database(**kwargs) -> str:
        """Retorna prompt base do sistema com dados reais da database"""
        from app.services.business_data import business_data_service
        from app.utils.dynamic_prompts import get_dynamic_system_prompt_with_database
        
        try:
            # Usar prompt com dados da database
            base_prompt = await get_dynamic_system_prompt_with_database()
        except Exception as e:
            logger.error(f"Erro ao carregar prompt com database: {e}")
            # Fallback para prompt padrão
            base_prompt = get_dynamic_llm_system_prompt()
        
        # Adiciona informações específicas do contexto
        context_info = f"""

CONTEXTO ATUAL:
Estado da conversa: {kwargs.get('state', 'unknown')}
Intenção detectada: {kwargs.get('intent', 'unknown')}
Dados coletados: {kwargs.get('collected_data', {})}
"""
        return base_prompt + context_info
    
    @staticmethod
    def get_system_base(**kwargs) -> str:
        """Retorna prompt base do sistema com data dinâmica (LEGACY)"""
        base_prompt = get_dynamic_llm_system_prompt()
        
        # Adiciona informações específicas do contexto
        context_info = f"""

CONTEXTO ATUAL:
Estado da conversa: {kwargs.get('state', 'unknown')}
Intenção detectada: {kwargs.get('intent', 'unknown')}
Dados coletados: {kwargs.get('collected_data', {})}
"""
        return base_prompt + context_info
    
    @staticmethod
    def get_data_extraction() -> str:
        """Retorna prompt de extração de dados com data dinâmica"""
        return get_dynamic_data_extraction_prompt()

    # Manter compatibilidade com código existente
    SYSTEM_BASE = get_dynamic_llm_system_prompt()
    DATA_EXTRACTION = get_dynamic_data_extraction_prompt()

    INTENT_DETECTION = """
Analise a mensagem do usuário e determine a intenção principal.

INTENÇÕES POSSÍVEIS:
- greeting: Saudações e cumprimentos
- schedule_create: Criar novo agendamento
- schedule_cancel: Cancelar agendamento
- schedule_reschedule: Reagendar compromisso
- check_appointments: Consultar agendamentos
- general_info: Informações gerais
- human_handoff: Transferir para humano
- complaint: Reclamações
- small_talk: Conversa casual
- unknown: Não conseguiu determinar

Retorne um JSON com:
{
    "intent": "tipo_da_intenção",
    "confidence": 0.95,
    "entities": {
        "service": "corte de cabelo",
        "date": "2025-07-25",
        "time": "14:00"
    },
    "reasoning": "explicação da análise"
}
"""

    RESPONSE_GENERATION = """
Gere uma resposta natural e contextual baseada no estado atual da conversa.

CONTEXTO:
Estado: {state}
Intenção: {intent}
Dados coletados: {collected_data}
Dados faltantes: {missing_data}

DIRETRIZES:
- Se dados estão faltando, faça perguntas específicas
- Se pronto para executar, confirme os detalhes
- Use linguagem natural e amigável
- Ofereça alternativas quando apropriado

Responda de forma conversacional e útil.
"""


class IntentDetector:
    """Detector de intenções usando LLM"""
    
    def __init__(self, llm_client):
        self.client = llm_client
        
    async def detect_intent(self, message: str, context: ConversationContext) -> Intent:
        """Detecta a intenção da mensagem"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": PromptTemplate.INTENT_DETECTION
                },
                {
                    "role": "user", 
                    "content": f"Mensagem: {message}\nContexto: {context.state.value}"
                }
            ]
            
            response = await asyncio.wait_for(
                retry_handler.execute_with_retry(
                    self.client.chat.completions.create,
                    "openai_intent_detection",
                    model="gpt-4",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=300
                ),
                timeout=15.0  # 15 segundos máximo
            )
            
            # Track API usage
            if hasattr(response, 'usage'):
                cost_tracker.track_usage(
                    model="gpt-4",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens
                )
            
            result = json.loads(response.choices[0].message.content)
            
            return Intent(
                type=IntentType(result["intent"]),
                confidence=result["confidence"],
                entities=result.get("entities", {}),
                requires_data=self._get_required_data(IntentType(result["intent"]))
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout na detecção de intenção após 15 segundos")
            return Intent(type=IntentType.UNKNOWN, confidence=0.0)
        except Exception as e:
            logger.error(f"Erro na detecção de intenção: {e}")
            return Intent(type=IntentType.UNKNOWN, confidence=0.0)
    
    def _get_required_data(self, intent_type: IntentType) -> List[str]:
        """Define dados necessários para cada tipo de intenção"""
        requirements = {
            IntentType.SCHEDULE_CREATE: ["service", "date", "time"],
            IntentType.SCHEDULE_CANCEL: ["appointment_id"],
            IntentType.SCHEDULE_RESCHEDULE: ["appointment_id", "new_date", "new_time"],
            IntentType.CHECK_APPOINTMENTS: [],
            IntentType.HUMAN_HANDOFF: ["reason"],
        }
        return requirements.get(intent_type, [])


class ConversationStateManager:
    """Gerencia estados da conversa"""
    
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
    
    def get_context(self, user_id: str, conversation_id: str) -> ConversationContext:
        """Obtém ou cria contexto da conversa"""
        key = f"{user_id}_{conversation_id}"
        
        if key not in self.contexts:
            self.contexts[key] = ConversationContext(
                user_id=user_id,
                conversation_id=conversation_id,
                state=ConversationState.INITIAL
            )
        
        return self.contexts[key]
    
    def update_context(self, context: ConversationContext):
        """Atualiza contexto da conversa"""
        key = f"{context.user_id}_{context.conversation_id}"
        context.updated_at = datetime.now()
        self.contexts[key] = context
    
    def transition_state(self, context: ConversationContext, new_state: ConversationState):
        """Transição de estado com validação"""
        valid_transitions = {
            ConversationState.INITIAL: [ConversationState.COLLECTING_INFO, ConversationState.COMPLETED],
            ConversationState.COLLECTING_INFO: [ConversationState.CONFIRMING, ConversationState.ERROR],
            ConversationState.CONFIRMING: [ConversationState.EXECUTING, ConversationState.COLLECTING_INFO],
            ConversationState.EXECUTING: [ConversationState.COMPLETED, ConversationState.ERROR],
            ConversationState.ERROR: [ConversationState.COLLECTING_INFO, ConversationState.HANDOFF],
        }
        
        if new_state in valid_transitions.get(context.state, []):
            context.state = new_state
            self.update_context(context)
            logger.info(f"Estado alterado para {new_state.value} (user: {context.user_id})")
        else:
            logger.warning(f"Transição inválida: {context.state.value} -> {new_state.value}")


class DataCollector:
    """Coleta dados necessários para completar ações"""
    
    def __init__(self, llm_client):
        self.client = llm_client
    
    async def extract_data(self, message: str, required_fields: List[str], 
                          collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai dados específicos da mensagem"""
        try:
            prompt = PromptTemplate.get_data_extraction()
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ]
            
            response = await asyncio.wait_for(
                retry_handler.execute_with_retry(
                    self.client.chat.completions.create,
                    "openai_response_generation",
                    model="gpt-4",
                    messages=messages,
                    temperature=0.2,
                    max_tokens=200
                ),
                timeout=15.0  # 15 segundos máximo
            )
            
            # Track API usage
            if hasattr(response, 'usage'):
                cost_tracker.track_usage(
                    model="gpt-4",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens
                )
            
            extracted = json.loads(response.choices[0].message.content)
            
            # Validar e limpar dados extraídos
            return self._validate_extracted_data(extracted, required_fields)
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout na extração de dados após 15 segundos")
            return {}
        except Exception as e:
            logger.error(f"Erro na extração de dados: {e}")
            return {}
    
    def _validate_extracted_data(self, data: Dict[str, Any], 
                                required_fields: List[str]) -> Dict[str, Any]:
        """Valida dados extraídos"""
        validated = {}
        
        for field in required_fields:
            if field in data and data[field] is not None:
                # Validações específicas
                if field == "date":
                    validated[field] = self._validate_date(data[field])
                elif field == "time":
                    validated[field] = self._validate_time(data[field])
                else:
                    validated[field] = data[field]
        
        return validated
    
    def _validate_date(self, date_str: str) -> Optional[str]:
        """Valida formato de data"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except:
            return None
    
    def _validate_time(self, time_str: str) -> Optional[str]:
        """Valida formato de hora"""
        try:
            datetime.strptime(time_str, "%H:%M")
            return time_str
        except:
            return None


class ResponseGenerator:
    """Gera respostas contextuais inteligentes"""
    
    def __init__(self, llm_client):
        self.client = llm_client
    
    async def generate_response(self, context: ConversationContext, 
                              user_message: str) -> LLMResponse:
        """Gera resposta baseada no contexto com dados reais da database"""
        try:
            # Determinar dados faltantes
            required_data = context.current_intent.requires_data if context.current_intent else []
            missing_data = [field for field in required_data 
                          if field not in context.collected_data]
            
            # Gerar prompt contextual
            prompt = PromptTemplate.RESPONSE_GENERATION.format(
                state=context.state.value,
                intent=context.current_intent.type.value if context.current_intent else "none",
                collected_data=context.collected_data,
                missing_data=missing_data
            )
            
            # Construir histórico da conversa com DADOS DA DATABASE
            try:
                # Usar prompt com dados reais da database
                system_prompt = await PromptTemplate.get_system_base_with_database(
                    state=context.state.value,
                    intent=context.current_intent.type.value if context.current_intent else "none",
                    collected_data=context.collected_data
                )
            except Exception as e:
                logger.warning(f"Erro ao carregar dados da database, usando fallback: {e}")
                # Fallback para prompt sem database
                system_prompt = PromptTemplate.get_system_base(
                    state=context.state.value,
                    intent=context.current_intent.type.value if context.current_intent else "none",
                    collected_data=context.collected_data
                )
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Adicionar histórico recente
            for msg in context.message_history[-10:]:  # Últimas 10 mensagens
                messages.append({
                    "role": msg["role"], 
                    "content": msg["content"]
                })
            
            messages.append({"role": "user", "content": user_message})
            
            response = await asyncio.wait_for(
                retry_handler.execute_with_retry(
                    self.client.chat.completions.create,
                    "openai_function_call",
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                ),
                timeout=15.0  # 15 segundos máximo
            )
            
            # Track API usage
            if hasattr(response, 'usage'):
                cost_tracker.track_usage(
                    model="gpt-4",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens
                )
            
            response_text = response.choices[0].message.content
            
            # Gerar elementos interativos
            buttons = self._generate_interactive_buttons(context, user_message)
            actions = self._suggest_actions(context)
            
            return LLMResponse(
                text=response_text,
                intent=context.current_intent,
                suggested_actions=actions,
                interactive_buttons=buttons,
                confidence=0.8,  # Poderia ser calculado dinamicamente
                metadata={
                    "tokens_used": response.usage.total_tokens,
                    "model": "gpt-4",
                    "response_time": datetime.now().isoformat(),
                    "database_access": True  # Marcar que usou dados da database
                }
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout na geração de resposta após 15 segundos")
            await alert_llm_service_error({"error": "Timeout na OpenAI API", "context": context.user_id})
        except Exception as e:
            logger.error(f"Erro na geração de resposta: {e}")
            await alert_llm_service_error({"error": str(e), "context": context.user_id})
            
            return LLMResponse(
                text="Desculpe, tive um problema técnico. Pode repetir sua mensagem?",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def _generate_interactive_buttons(self, context: ConversationContext, 
                                    user_message: str) -> List[Dict]:
        """Gera botões interativos contextuais"""
        if not context.current_intent:
            return [
                {"id": "new_schedule", "title": "📅 Agendar"},
                {"id": "check_schedule", "title": "📋 Consultar"},
                {"id": "human_support", "title": "👤 Falar com atendente"}
            ]
        
        if context.current_intent.type == IntentType.SCHEDULE_CREATE:
            if context.state == ConversationState.CONFIRMING:
                return [
                    {"id": "confirm_schedule", "title": "✅ Confirmar"},
                    {"id": "change_schedule", "title": "📝 Alterar"},
                    {"id": "cancel_action", "title": "❌ Cancelar"}
                ]
        
        return []
    
    def _suggest_actions(self, context: ConversationContext) -> List[Dict]:
        """Sugere ações baseadas no contexto"""
        actions = []
        
        if context.current_intent and context.state == ConversationState.EXECUTING:
            if context.current_intent.type == IntentType.SCHEDULE_CREATE:
                actions.append({
                    "type": "create_appointment",
                    "data": context.collected_data,
                    "priority": "high"
                })
        
        return actions


class FunctionCallHandler:
    """Gerencia chamadas de funções estruturadas"""
    
    def __init__(self):
        self.functions = {
            "schedule_create": self._handle_schedule_create,
            "schedule_cancel": self._handle_schedule_cancel,
            "schedule_reschedule": self._handle_schedule_reschedule,
            "human_handoff": self._handle_human_handoff,
            "check_appointments": self._handle_check_appointments
        }
    
    async def execute_function(self, function_name: str, parameters: Dict[str, Any], 
                             context: ConversationContext) -> Dict[str, Any]:
        """Executa função especificada"""
        if function_name not in self.functions:
            return {"success": False, "error": f"Função {function_name} não encontrada"}
        
        try:
            return await self.functions[function_name](parameters, context)
        except Exception as e:
            logger.error(f"Erro ao executar função {function_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_schedule_create(self, params: Dict, context: ConversationContext) -> Dict:
        """Manipula criação de agendamento"""
        try:
            from app.services.data import AppointmentService
            from app.database import get_db
            from datetime import datetime
            
            # Obter sessão do banco
            async for db in get_db():
                # Extrair dados do agendamento
                service = params.get('service', 'Serviço não especificado')
                date_str = params.get('date', '')
                time_str = params.get('time', '')
                notes = params.get('notes', '')
                
                # Combinar data e hora
                if date_str and time_str:
                    try:
                        # Tentar diferentes formatos
                        datetime_str = f"{date_str} {time_str}"
                        appointment_datetime = None
                        
                        for fmt in ["%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                appointment_datetime = datetime.strptime(datetime_str, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if not appointment_datetime:
                            # Fallback para amanhã 15h se não conseguir parsear
                            from datetime import timedelta
                            appointment_datetime = datetime.now() + timedelta(days=1)
                            appointment_datetime = appointment_datetime.replace(hour=15, minute=0, second=0, microsecond=0)
                        
                        # Criar agendamento
                        appointment = await AppointmentService.create_appointment(
                            db=db,
                            user_id=context.user_id,
                            service=service,
                            date_time=appointment_datetime,
                            notes=f"Agendado via conversação LLM. {notes}",
                            status="pendente"
                        )
                        
                        return {
                            "success": True,
                            "appointment_id": appointment.id,
                            "message": f"✅ Agendamento criado com sucesso! ID: {appointment.id} - {service} para {appointment_datetime.strftime('%d/%m/%Y às %H:%M')}"
                        }
                        
                    except Exception as date_error:
                        return {
                            "success": False,
                            "error": f"Erro ao processar data/hora: {str(date_error)}",
                            "message": "❌ Não foi possível criar o agendamento. Verifique a data e horário informados."
                        }
                else:
                    return {
                        "success": False,
                        "error": "Data e/ou horário não fornecidos",
                        "message": "❌ Para criar o agendamento, preciso da data e horário. Pode me informar novamente?"
                    }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}",
                "message": "❌ Ocorreu um erro interno. Tente novamente ou entre em contato conosco."
            }
    
    async def _handle_schedule_cancel(self, params: Dict, context: ConversationContext) -> Dict:
        """Manipula cancelamento de agendamento"""
        return {
            "success": True,
            "message": f"Agendamento #{params['appointment_id']} cancelado"
        }
    
    async def _handle_schedule_reschedule(self, params: Dict, context: ConversationContext) -> Dict:
        """Manipula reagendamento"""
        return {
            "success": True,
            "message": f"Agendamento reagendado para {params['new_date']} às {params['new_time']}"
        }
    
    async def _handle_human_handoff(self, params: Dict, context: ConversationContext) -> Dict:
        """Manipula transferência para humano"""
        return {
            "success": True,
            "handoff": True,
            "message": "Transferindo para atendente humano..."
        }
    
    async def _handle_check_appointments(self, params: Dict, context: ConversationContext) -> Dict:
        """Manipula consulta de agendamentos"""
        # Aqui integraria com consulta real de agendamentos
        return {
            "success": True,
            "appointments": [
                {"id": 1, "service": "Corte", "date": "2025-07-25", "time": "14:00"},
                {"id": 2, "service": "Barba", "date": "2025-07-26", "time": "10:00"}
            ]
        }


class ConversationAnalyzer:
    """Analisa padrões e métricas das conversas"""
    
    def __init__(self):
        self.metrics = {
            "total_conversations": 0,
            "successful_completions": 0,
            "handoffs": 0,
            "errors": 0,
            "average_turns": 0,
            "intent_distribution": {},
            "state_transitions": {}
        }
    
    def analyze_conversation(self, context: ConversationContext) -> Dict[str, Any]:
        """Analisa uma conversa específica"""
        return {
            "conversation_id": context.conversation_id,
            "total_turns": len(context.message_history),
            "completion_time": (context.updated_at - context.created_at).total_seconds(),
            "final_state": context.state.value,
            "intents_detected": [msg.get("intent") for msg in context.message_history if msg.get("intent")],
            "data_collection_efficiency": len(context.collected_data) / len(context.current_intent.requires_data) if context.current_intent and context.current_intent.requires_data else 1.0
        }
    
    def update_metrics(self, context: ConversationContext):
        """Atualiza métricas globais"""
        self.metrics["total_conversations"] += 1
        
        if context.state == ConversationState.COMPLETED:
            self.metrics["successful_completions"] += 1
        elif context.state == ConversationState.HANDOFF:
            self.metrics["handoffs"] += 1
        elif context.state == ConversationState.ERROR:
            self.metrics["errors"] += 1
        
        # Atualizar distribuição de intenções
        if context.current_intent:
            intent_type = context.current_intent.type.value
            current_count = self.metrics["intent_distribution"].get(intent_type, 0)
            self.metrics["intent_distribution"][intent_type] = current_count + 1


class AdvancedLLMService:
    """Serviço LLM Avançado e Estruturado"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Componentes principais
        self.intent_detector = IntentDetector(self.client)
        # Usar ConversationStateManager local em vez do importado
        self.state_manager = ConversationStateManager()
        self.data_collector = DataCollector(self.client)
        self.response_generator = ResponseGenerator(self.client)
        self.function_handler = FunctionCallHandler()
        self.analyzer = ConversationAnalyzer()
        
        # Sistema de plugins (será importado dinamicamente para evitar dependência circular)
        self.plugin_manager = None
        self._init_plugins()
        
        # Cache para otimização
        self.response_cache: Dict[str, LLMResponse] = {}
        self.intent_cache: Dict[str, Intent] = {}
        
        # Flag para controle de cleanup automático
        self._cleanup_task = None
        self._start_cleanup_on_first_use = True
    
    def _init_plugins(self):
        """Inicializa sistema de plugins"""
        # Sistema de plugins removido por simplicidade
        logger.info("Sistema de plugins desabilitado")
        self.plugin_manager = None
    
    def _ensure_cleanup_started(self):
        """Inicia cleanup automático se ainda não foi iniciado"""
        if self._start_cleanup_on_first_use and self._cleanup_task is None:
            try:
                self._cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
                self._start_cleanup_on_first_use = False
                logger.info("Cleanup automático de contextos LLM iniciado")
            except RuntimeError:
                # Não há loop rodando, cleanup será manual
                logger.warning("Cleanup automático não pôde ser iniciado (sem loop assíncrono)")
                self._start_cleanup_on_first_use = False
    
    async def process_message(self, user_id: str, conversation_id: str, 
                            message: str, message_type: str = "text") -> LLMResponse:
        """
        Processa mensagem de forma estruturada e contextual
        
        Args:
            user_id: ID do usuário
            conversation_id: ID da conversa
            message: Conteúdo da mensagem
            message_type: Tipo (text, audio, image, etc.)
        
        Returns:
            Resposta estruturada com ações e contexto
        """
        try:
            # Iniciar cleanup automático na primeira execução
            self._ensure_cleanup_started()
            
            # Obter contexto da conversa
            context = self.state_manager.get_context(user_id, conversation_id)
            
            # PRÉ-PROCESSAMENTO COM PLUGINS
            processed_message = message
            if self.plugin_manager:
                preprocessor_results = await self.plugin_manager.execute_plugins(
                    self.PluginType.PREPROCESSOR, message, context
                )
                
                # Aplicar resultados do pré-processamento
                for result in preprocessor_results:
                    if result.success and result.data:
                        processed_message = result.data
            
            # Adicionar mensagem ao histórico
            context.message_history.append({
                "role": "user",
                "content": processed_message,
                "timestamp": datetime.now().isoformat(),
                "type": message_type,
                "original_content": message if processed_message != message else None
            })
            
            # ENRIQUECIMENTO DE CONTEXTO COM PLUGINS
            if self.plugin_manager:
                await self.plugin_manager.execute_plugins(
                    self.PluginType.CONTEXT_ENRICHER, processed_message, context
                )
            
            # Detectar intenção (se necessário)
            if context.state == ConversationState.INITIAL or not context.current_intent:
                context.current_intent = await self.intent_detector.detect_intent(processed_message, context)
                
                # MODIFICAÇÃO DE INTENÇÃO COM PLUGINS
                if self.plugin_manager:
                    intent_results = await self.plugin_manager.execute_plugins(
                        self.PluginType.INTENT_MODIFIER, context.current_intent, context
                    )
                    
                    # Aplicar modificações de intenção
                    for result in intent_results:
                        if result.success and result.data:
                            context.current_intent = result.data
                
                self.state_manager.transition_state(context, ConversationState.COLLECTING_INFO)
            
            # Coletar dados se necessário
            if context.state == ConversationState.COLLECTING_INFO:
                extracted_data = await self.data_collector.extract_data(
                    processed_message, 
                    context.current_intent.requires_data,
                    context.collected_data
                )
                
                # Atualizar dados coletados
                context.collected_data.update(extracted_data)
                
                # VALIDAÇÃO DE DADOS COM PLUGINS
                if self.plugin_manager:
                    validation_results = await self.plugin_manager.execute_plugins(
                        self.PluginType.VALIDATOR, context.collected_data, context
                    )
                    
                    # Verificar se validação passou
                    validation_passed = all(result.success for result in validation_results)
                    if not validation_passed:
                        # Coletar erros de validação
                        validation_errors = [
                            result.error for result in validation_results 
                            if not result.success and result.error
                        ]
                        
                        # Criar resposta com erros de validação
                        return LLMResponse(
                            text=f"Ops! {' '.join(validation_errors)}",
                            confidence=0.9,
                            metadata={"validation_errors": validation_errors}
                        )
                
                # Verificar se todos os dados foram coletados
                if self._all_data_collected(context):
                    self.state_manager.transition_state(context, ConversationState.CONFIRMING)
            
            # Confirmar ação se necessário
            if context.state == ConversationState.CONFIRMING:
                if self._is_confirmation(processed_message):
                    self.state_manager.transition_state(context, ConversationState.EXECUTING)
                elif self._is_modification_request(processed_message):
                    # Voltar para coleta de dados
                    self.state_manager.transition_state(context, ConversationState.COLLECTING_INFO)
            
            # Executar função se confirmado
            if context.state == ConversationState.EXECUTING:
                function_result = await self.function_handler.execute_function(
                    context.current_intent.type.value,
                    context.collected_data,
                    context
                )
                
                if function_result.get("success"):
                    self.state_manager.transition_state(context, ConversationState.COMPLETED)
                else:
                    self.state_manager.transition_state(context, ConversationState.ERROR)
                
                # Adicionar resultado ao contexto
                context.metadata["last_function_result"] = function_result
            
            # Gerar resposta contextual
            response = await self.response_generator.generate_response(context, processed_message)
            
            # PÓS-PROCESSAMENTO DA RESPOSTA COM PLUGINS
            if self.plugin_manager:
                postprocessor_results = await self.plugin_manager.execute_plugins(
                    self.PluginType.POSTPROCESSOR, response, context
                )
                
                # Aplicar melhorias na resposta
                for result in postprocessor_results:
                    if result.success and result.data:
                        response = result.data
                
                # ENRIQUECIMENTO DA RESPOSTA COM PLUGINS
                enhancer_results = await self.plugin_manager.execute_plugins(
                    self.PluginType.RESPONSE_ENHANCER, response, context
                )
                
                for result in enhancer_results:
                    if result.success and result.data:
                        response = result.data
            
            # Adicionar resposta ao histórico
            context.message_history.append({
                "role": "assistant",
                "content": response.text,
                "timestamp": datetime.now().isoformat(),
                "intent": context.current_intent.type.value if context.current_intent else None,
                "state": context.state.value,
                "plugins_executed": len([
                    p for p in (getattr(self, '_last_plugin_results', []))
                    if p.success
                ]) if hasattr(self, '_last_plugin_results') else 0
            })
            
            # COLETA DE ANALYTICS COM PLUGINS
            if self.plugin_manager:
                interaction_data = {
                    "user_message": processed_message,
                    "response": response.text,
                    "intent": context.current_intent.type.value if context.current_intent else None,
                    "state": context.state.value,
                    "response_time_ms": response.metadata.get("response_time", 0),
                    "error_occurred": context.state == ConversationState.ERROR
                }
                
                await self.plugin_manager.execute_plugins(
                    self.PluginType.ANALYTICS, interaction_data, context
                )
            
            # Atualizar contexto
            self.state_manager.update_context(context)
            
            # Atualizar métricas
            self.analyzer.update_metrics(context)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {e}")
            await alert_llm_service_error({
                "error": str(e),
                "user_id": user_id,
                "message": message[:100]  # Truncar mensagem
            })
            
            return LLMResponse(
                text="Desculpe, houve um erro técnico. Nossa equipe foi notificada. Pode tentar novamente?",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def _all_data_collected(self, context: ConversationContext) -> bool:
        """Verifica se todos os dados necessários foram coletados"""
        if not context.current_intent:
            return False
        
        required_data = context.current_intent.requires_data
        return all(field in context.collected_data for field in required_data)
    
    def _is_confirmation(self, message: str) -> bool:
        """Verifica se a mensagem é uma confirmação"""
        confirmations = ["sim", "confirmar", "ok", "certo", "perfeito", "✅", "confirmo"]
        return any(word in message.lower() for word in confirmations)
    
    def _is_modification_request(self, message: str) -> bool:
        """Verifica se o usuário quer modificar algo"""
        modifications = ["não", "alterar", "mudar", "outro", "diferente", "❌"]
        return any(word in message.lower() for word in modifications)
    
    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.ogg") -> Optional[str]:
        """Transcreve áudio usando Whisper"""
        try:
            # Salvar temporariamente o arquivo de áudio
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                # Transcrever usando Whisper
                with open(temp_path, 'rb') as audio_file:
                    response = await asyncio.wait_for(
                        retry_handler.execute_with_retry(
                            self.client.audio.transcriptions.create,
                            "openai_whisper",
                            model="whisper-1",
                            file=audio_file,
                            language="pt"
                        ),
                        timeout=30.0  # 30 segundos para áudio (mais tempo que texto)
                    )
                
                return response.text
                
            finally:
                # Limpar arquivo temporário
                os.unlink(temp_path)
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout na transcrição de áudio após 30 segundos")
            await alert_llm_service_error({"error": "Timeout na transcrição Whisper API", "operation": "transcription"})
            return ""
        except Exception as e:
            logger.error(f"Erro na transcrição de áudio: {e}")
            await alert_llm_service_error({"error": str(e), "operation": "transcription"})
            return None
    
    def get_conversation_analytics(self, user_id: str = None) -> Dict[str, Any]:
        """Obtém análises das conversas"""
        if user_id:
            # Análise específica do usuário
            user_contexts = [ctx for ctx in self.state_manager.contexts.values() 
                           if ctx.user_id == user_id]
            
            return {
                "user_id": user_id,
                "total_conversations": len(user_contexts),
                "average_completion_time": sum(
                    (ctx.updated_at - ctx.created_at).total_seconds() 
                    for ctx in user_contexts
                ) / len(user_contexts) if user_contexts else 0,
                "success_rate": len([ctx for ctx in user_contexts 
                                   if ctx.state == ConversationState.COMPLETED]) / len(user_contexts) if user_contexts else 0
            }
        
        # Análise global
        return self.analyzer.metrics
    
    def clear_conversation_context(self, user_id: str, conversation_id: str):
        """Limpa contexto de uma conversa específica"""
        key = f"{user_id}_{conversation_id}"
        if key in self.state_manager.contexts:
            del self.state_manager.contexts[key]
            logger.info(f"Contexto da conversa {conversation_id} limpo para usuário {user_id}")
    
    async def cleanup_old_contexts(self, max_age_hours: int = 24):
        """Remove contextos antigos para economizar memória"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Limpar contextos do state_manager (que usa contexts!)
        old_contexts = []
        if self.state_manager.contexts:
            old_contexts = [
                key for key, ctx in self.state_manager.contexts.items()
                if ctx.updated_at < cutoff_time
            ]
            
            for key in old_contexts:
                del self.state_manager.contexts[key]
        
        # Limpar cache local de respostas e intenções
        cache_cleaned = 0
        old_cache_keys = [
            key for key, value in self.response_cache.items()
            if isinstance(value, dict) and 'timestamp' in value and 
            datetime.fromisoformat(value['timestamp']) < cutoff_time
        ]
        
        for key in old_cache_keys:
            del self.response_cache[key]
            cache_cleaned += 1
        
        # Limpar cache de intenções
        old_intent_keys = [
            key for key, value in self.intent_cache.items()
            if isinstance(value, dict) and 'timestamp' in value and 
            datetime.fromisoformat(value['timestamp']) < cutoff_time
        ]
        
        for key in old_intent_keys:
            del self.intent_cache[key]
            cache_cleaned += 1
        
        total_cleaned = len(old_contexts) + cache_cleaned
        if total_cleaned > 0:
            logger.info(f"Limpeza de memória: {len(old_contexts)} contextos + {cache_cleaned} caches removidos")
    
    async def _auto_cleanup_loop(self):
        """Loop de limpeza automática de contextos"""
        while True:
            try:
                await asyncio.sleep(600)  # 10 minutos
                await self.cleanup_old_contexts(max_age_hours=2)
            except Exception as e:
                logger.error(f"Erro na limpeza automática de contextos LLM: {e}")
    
    # === MÉTODOS DE GERENCIAMENTO DE PLUGINS ===
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos plugins"""
        if not self.plugin_manager:
            return {"error": "Sistema de plugins não disponível"}
        
        return self.plugin_manager.get_plugin_stats()
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Ativa um plugin específico"""
        if not self.plugin_manager:
            return False
        
        self.plugin_manager.enable_plugin(plugin_name)
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Desativa um plugin específico"""
        if not self.plugin_manager:
            return False
        
        self.plugin_manager.disable_plugin(plugin_name)
        return True
    
    def get_analytics_report(self) -> Dict[str, Any]:
        """Obtém relatório completo de analytics"""
        report = {
            "conversation_analytics": self.get_conversation_analytics(),
            "system_metrics": {
                "cache_size": len(self.response_cache),
                "active_contexts": len(self.state_manager.contexts),
                "plugin_system": self.get_plugin_stats()
            }
        }
        
        # Adicionar analytics de plugins se disponível
        if self.plugin_manager:
            for plugin_name, plugin in self.plugin_manager.plugin_registry.items():
                if hasattr(plugin, 'get_analytics_report'):
                    report[f"plugin_{plugin_name}"] = plugin.get_analytics_report()
        
        return report
    
    async def optimize_performance(self):
        """Otimiza performance do sistema"""
        # Limpar cache antigo
        if len(self.response_cache) > 1000:
            # Manter apenas os 500 mais recentes
            sorted_cache = sorted(
                self.response_cache.items(), 
                key=lambda x: x[1].metadata.get('timestamp', ''),
                reverse=True
            )
            self.response_cache = dict(sorted_cache[:500])
            logger.info("Cache de respostas otimizado")
        
        # Limpar contextos antigos
        await self.cleanup_old_contexts(max_age_hours=12)
        
        # Otimizar plugins se disponível
        if self.plugin_manager:
            # Desabilitar plugins que não foram usados recentemente
            for plugin_name, plugin in self.plugin_manager.plugin_registry.items():
                if hasattr(plugin, 'last_used'):
                    if (datetime.now() - plugin.last_used).days > 7:
                        plugin.enabled = False
                        logger.info(f"Plugin {plugin_name} desabilitado por inatividade")


# Instância global do serviço (criada sob demanda)
advanced_llm_service = None

def get_advanced_llm_service() -> AdvancedLLMService:
    """Obtém instância global do serviço LLM"""
    global advanced_llm_service
    if advanced_llm_service is None:
        advanced_llm_service = AdvancedLLMService()
    return advanced_llm_service
