from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema de Fluxo Conversacional Não-Linear
Permite conversas naturais e flexíveis com mudança de contexto dinâmica
"""
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from dataclasses import dataclass, field
import re
from collections import deque

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Estados possíveis da conversa"""
    GREETING = "greeting"
    INFORMATION_GATHERING = "information_gathering"
    SERVICE_DISCUSSION = "service_discussion"
    SCHEDULING = "scheduling"
    PRICING = "pricing"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    SUPPORT = "support"
    FOLLOW_UP = "follow_up"
    IDLE = "idle"
    MULTI_INTENT = "multi_intent"  # Cliente quer falar de várias coisas


class FlowTransition(Enum):
    """Tipos de transições entre estados"""
    NATURAL_PROGRESSION = "natural_progression"    # Fluxo natural
    TOPIC_CHANGE = "topic_change"                 # Mudança de assunto
    BACK_REFERENCE = "back_reference"             # Voltar a tópico anterior
    INTERRUPT = "interrupt"                       # Interrupção para novo tópico
    CLARIFICATION = "clarification"               # Pedido de esclarecimento
    MULTI_TOPIC = "multi_topic"                   # Múltiplos tópicos em uma mensagem


@dataclass
class ConversationTopic:
    """Representa um tópico de conversa"""
    topic_id: str
    name: str
    keywords: List[str]
    priority: int  # 1-10, sendo 10 mais prioritário
    state: ConversationState
    context_data: Dict[str, Any] = field(default_factory=dict)
    mentions: int = 0
    last_mentioned: Optional[datetime] = None
    resolved: bool = False
    confidence: float = 0.0


@dataclass
class ConversationMemory:
    """Memória de conversa com controle de resposta única"""
    conversation_start: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    current_state: 'ConversationState' = None
    previous_state: 'ConversationState' = None
    active_topics: Dict[str, 'TopicMemory'] = field(default_factory=dict)
    topic_history: List[str] = field(default_factory=list)
    context_switches: int = 0
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    pending_questions: List[str] = field(default_factory=list)
    
    # 🆕 NOVOS CAMPOS PARA CONTROLE DE RESPOSTA ÚNICA
    last_response_sent: Optional[str] = None
    response_timestamp: Optional[datetime] = None
    is_processing: bool = False
    response_lock: Optional[asyncio.Lock] = None
    
    def __post_init__(self):
        if self.response_lock is None:
            self.response_lock = asyncio.Lock()


@dataclass
class FlowDecision:
    """Decisão sobre o próximo passo no fluxo"""
    next_state: ConversationState
    transition_type: FlowTransition
    confidence: float
    reasoning: str
    suggested_response: str
    context_to_maintain: List[str]
    topics_to_activate: List[str]
    agent_instructions: Dict[str, Any] = field(default_factory=dict)


class ConversationFlowEngine:
    """Motor de fluxo conversacional com controle de resposta única"""
    
    def __init__(self):
        self.processing_locks: Dict[str, asyncio.Lock] = {}
        self.response_control: Dict[str, Dict[str, Any]] = {}
        self.topic_definitions = self._initialize_topics()
        self.state_transitions = self._initialize_transitions()
        self.context_patterns = self._initialize_context_patterns()
        
    async def ensure_single_response(self, user_id: str, message: str) -> bool:
        """
        Garante que apenas uma resposta seja processada por mensagem
        
        Args:
            user_id: ID do usuário
            message: Mensagem recebida
            
        Returns:
            True se deve processar, False se deve ignorar
        """
        if user_id not in self.processing_locks:
            self.processing_locks[user_id] = asyncio.Lock()
        
        async with self.processing_locks[user_id]:
            # Verificar se já processamos uma mensagem similar recentemente
            if user_id in self.response_control:
                last_response = self.response_control[user_id]
                time_diff = time.time() - last_response.get('timestamp', 0)
                
                # Se a última resposta foi há menos de 5 segundos
                if time_diff < 5:
                    # Verificar se a mensagem é similar
                    if self._is_similar_message(message, last_response.get('message', '')):
                        logger.info(f"🔄 Ignorando mensagem similar para {user_id}: {message[:50]}...")
                        return False
            
            # Marcar como processando
            self.response_control[user_id] = {
                'message': message,
                'timestamp': time.time(),
                'processing': True
            }
            
            return True
    
    def _is_similar_message(self, msg1: str, msg2: str, threshold: float = 0.8) -> bool:
        """Verifica se duas mensagens são similares"""
        if not msg1 or not msg2:
            return False
        
        # Normalizar mensagens
        msg1_norm = re.sub(r'[^\w\s]', '', msg1.lower())
        msg2_norm = re.sub(r'[^\w\s]', '', msg2.lower())
        
        # Calcular similaridade
        similarity = SequenceMatcher(None, msg1_norm, msg2_norm).ratio()
        return similarity >= threshold
    
    async def mark_response_sent(self, user_id: str, message: str, response: str):
        """Marca que uma resposta foi enviada"""
        if user_id in self.response_control:
            self.response_control[user_id].update({
                'response': response,
                'processing': False,
                'response_timestamp': time.time()
            })

    def _initialize_topics(self) -> Dict[str, ConversationTopic]:
        """Inicializa definições de tópicos"""
        topics = {
            "greeting": ConversationTopic(
                topic_id="greeting",
                name="Cumprimentos",
                keywords=["oi", "olá", "bom dia", "boa tarde", "boa noite", "tudo bem"],
                priority=3,
                state=ConversationState.GREETING
            ),
            
            "services": ConversationTopic(
                topic_id="services", 
                name="Serviços",
                keywords=["serviço", "corte", "barba", "sobrancelha", "massagem", "tratamento", "procedimento"],
                priority=8,
                state=ConversationState.SERVICE_DISCUSSION
            ),
            
            "pricing": ConversationTopic(
                topic_id="pricing",
                name="Preços",
                keywords=["preço", "valor", "quanto custa", "orçamento", "investimento", "taxa", "promoção"],
                priority=9,
                state=ConversationState.PRICING
            ),
            
            "scheduling": ConversationTopic(
                topic_id="scheduling",
                name="Agendamento",
                keywords=["agendar", "marcar", "horário", "data", "disponibilidade", "quando", "agenda"],
                priority=10,
                state=ConversationState.SCHEDULING
            ),
            
            "location": ConversationTopic(
                topic_id="location",
                name="Localização",
                keywords=["onde", "endereço", "localização", "como chegar", "estacionamento", "perto"],
                priority=6,
                state=ConversationState.INFORMATION_GATHERING
            ),
            
            "support": ConversationTopic(
                topic_id="support",
                name="Suporte",
                keywords=["problema", "ajuda", "dúvida", "não funcionou", "erro", "reclamação"],
                priority=9,
                state=ConversationState.SUPPORT
            ),
            
            "cancellation": ConversationTopic(
                topic_id="cancellation", 
                name="Cancelamento",
                keywords=["cancelar", "desmarcar", "não posso", "remover", "reagendar"],
                priority=8,
                state=ConversationState.SUPPORT
            ),
            
            "testimonials": ConversationTopic(
                topic_id="testimonials",
                name="Depoimentos",
                keywords=["opinião", "avaliação", "experiência", "recomendação", "qualidade"],
                priority=5,
                state=ConversationState.INFORMATION_GATHERING
            ),
            
            "payment": ConversationTopic(
                topic_id="payment",
                name="Pagamento", 
                keywords=["pagamento", "cartão", "dinheiro", "pix", "parcelamento", "desconto"],
                priority=7,
                state=ConversationState.PRICING
            ),
            
            "followup": ConversationTopic(
                topic_id="followup",
                name="Acompanhamento",
                keywords=["como foi", "resultado", "satisfeito", "voltarei", "próxima vez"],
                priority=4,
                state=ConversationState.FOLLOW_UP
            )
        }
        
        return topics
    
    def _initialize_transitions(self) -> Dict[str, List[ConversationState]]:
        """Inicializa transições possíveis entre estados"""
        return {
            ConversationState.GREETING.value: [
                ConversationState.SERVICE_DISCUSSION,
                ConversationState.SCHEDULING,
                ConversationState.INFORMATION_GATHERING,
                ConversationState.PRICING
            ],
            
            ConversationState.INFORMATION_GATHERING.value: [
                ConversationState.SERVICE_DISCUSSION,
                ConversationState.SCHEDULING,
                ConversationState.PRICING,
                ConversationState.SUPPORT
            ],
            
            ConversationState.SERVICE_DISCUSSION.value: [
                ConversationState.PRICING,
                ConversationState.SCHEDULING,
                ConversationState.OBJECTION_HANDLING,
                ConversationState.INFORMATION_GATHERING
            ],
            
            ConversationState.PRICING.value: [
                ConversationState.SCHEDULING,
                ConversationState.OBJECTION_HANDLING,
                ConversationState.SERVICE_DISCUSSION,
                ConversationState.CLOSING
            ],
            
            ConversationState.SCHEDULING.value: [
                ConversationState.CLOSING,
                ConversationState.SERVICE_DISCUSSION,
                ConversationState.PRICING,
                ConversationState.SUPPORT
            ],
            
            ConversationState.OBJECTION_HANDLING.value: [
                ConversationState.PRICING,
                ConversationState.SERVICE_DISCUSSION,
                ConversationState.SCHEDULING,
                ConversationState.CLOSING
            ],
            
            ConversationState.SUPPORT.value: [
                ConversationState.SERVICE_DISCUSSION,
                ConversationState.SCHEDULING,
                ConversationState.FOLLOW_UP,
                ConversationState.CLOSING
            ],
            
            ConversationState.CLOSING.value: [
                ConversationState.FOLLOW_UP,
                ConversationState.SCHEDULING,
                ConversationState.SUPPORT
            ],
            
            ConversationState.FOLLOW_UP.value: [
                ConversationState.SCHEDULING,
                ConversationState.SERVICE_DISCUSSION,
                ConversationState.SUPPORT,
                ConversationState.IDLE
            ]
        }
    
    def _initialize_context_patterns(self) -> Dict[str, List[str]]:
        """Inicializa padrões de contexto para detecção"""
        return {
            "back_reference": [
                "voltando ao que", "como falamos", "sobre aquilo", "lembra que",
                "retomando", "continuando", "ainda sobre", "voltando"
            ],
            
            "topic_change": [
                "mas agora", "mudando de assunto", "aliás", "por falar nisso",
                "ah, e também", "outra coisa", "já que estamos falando"
            ],
            
            "interrupt": [
                "espera", "antes disso", "na verdade", "peraí", "calma",
                "primeiro", "só uma coisa", "rapidinho"
            ],
            
            "clarification": [
                "não entendi", "pode explicar", "como assim", "o que você quer dizer",
                "pode repetir", "não ficou claro", "explica melhor"
            ],
            
            "multi_topic": [
                "e também", "além disso", "outra coisa", "mais uma pergunta",
                "ah, e", "já aproveitando", "e sobre"
            ]
        }
    
    def analyze_conversation_flow(
        self, 
        message: str, 
        user_phone: str,
        memory: ConversationMemory,
        context: Dict[str, Any] = None
    ) -> FlowDecision:
        """Analisa fluxo da conversa e decide próximo passo"""
        
        # 1. Detectar tópicos na mensagem
        detected_topics = self._detect_topics(message)
        
        # 2. Analisar tipo de transição
        transition_type = self._analyze_transition_type(message, memory)
        
        # 3. Atualizar memória com novos tópicos
        self._update_conversation_memory(memory, detected_topics, message)
        
        # 4. Decidir próximo estado
        next_state = self._decide_next_state(detected_topics, memory, transition_type)
        
        # 5. Gerar instruções para agente
        agent_instructions = self._generate_agent_instructions(
            next_state, detected_topics, memory, transition_type
        )
        
        # 6. Calcular confiança da decisão
        confidence = self._calculate_decision_confidence(detected_topics, memory, transition_type)
        
        # 7. Gerar reasoning
        reasoning = self._generate_reasoning(detected_topics, memory, transition_type, next_state)
        
        # 8. Sugerir resposta contextual
        suggested_response = self._generate_contextual_response(
            next_state, detected_topics, memory, transition_type
        )
        
        return FlowDecision(
            next_state=next_state,
            transition_type=transition_type,
            confidence=confidence,
            reasoning=reasoning,
            suggested_response=suggested_response,
            context_to_maintain=self._identify_context_to_maintain(memory, detected_topics),
            topics_to_activate=[topic.topic_id for topic in detected_topics],
            agent_instructions=agent_instructions
        )
    
    def _detect_topics(self, message: str) -> List[ConversationTopic]:
        """Detecta tópicos mencionados na mensagem"""
        message_lower = message.lower()
        detected_topics = []
        
        for topic_id, topic in self.topic_definitions.items():
            confidence = 0.0
            matches = 0
            
            # Contar matches de palavras-chave
            for keyword in topic.keywords:
                if keyword in message_lower:
                    matches += 1
                    confidence += 0.1
            
            # Ajustar confiança baseada no número de matches
            if matches > 0:
                confidence = min(1.0, confidence + (matches * 0.15))
                
                # Criar cópia do tópico com confiança
                topic_copy = ConversationTopic(
                    topic_id=topic.topic_id,
                    name=topic.name,
                    keywords=topic.keywords,
                    priority=topic.priority,
                    state=topic.state,
                    confidence=confidence,
                    mentions=1,
                    last_mentioned=datetime.now()
                )
                
                detected_topics.append(topic_copy)
        
        # Ordenar por prioridade e confiança
        detected_topics.sort(key=lambda t: (t.priority, t.confidence), reverse=True)
        
        return detected_topics
    
    def _analyze_transition_type(self, message: str, memory: ConversationMemory) -> FlowTransition:
        """Analisa tipo de transição baseado na mensagem"""
        message_lower = message.lower()
        
        # Verificar padrões de contexto
        for pattern_type, patterns in self.context_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    if pattern_type == "back_reference":
                        return FlowTransition.BACK_REFERENCE
                    elif pattern_type == "topic_change":
                        return FlowTransition.TOPIC_CHANGE
                    elif pattern_type == "interrupt":
                        return FlowTransition.INTERRUPT
                    elif pattern_type == "clarification":
                        return FlowTransition.CLARIFICATION
                    elif pattern_type == "multi_topic":
                        return FlowTransition.MULTI_TOPIC
        
        # Se não detectou padrão específico, verificar se é progressão natural
        if len(memory.topic_history) > 0:
            last_state = memory.current_state
            # Lógica para determinar se é progressão natural baseada no estado atual
            return FlowTransition.NATURAL_PROGRESSION
        
        return FlowTransition.NATURAL_PROGRESSION
    
    def _update_conversation_memory(
        self, 
        memory: ConversationMemory, 
        detected_topics: List[ConversationTopic],
        message: str
    ):
        """Atualiza memória da conversa"""
        memory.last_activity = datetime.now()
        
        # Adicionar tópicos detectados à memória
        for topic in detected_topics:
            if topic.topic_id in memory.active_topics:
                # Atualizar tópico existente
                memory.active_topics[topic.topic_id].mentions += 1
                memory.active_topics[topic.topic_id].last_mentioned = datetime.now()
                memory.active_topics[topic.topic_id].confidence = max(
                    memory.active_topics[topic.topic_id].confidence,
                    topic.confidence
                )
            else:
                # Adicionar novo tópico
                memory.active_topics[topic.topic_id] = topic
        
        # Adicionar ao histórico
        if detected_topics:
            primary_topic = detected_topics[0]
            memory.topic_history.append({
                "topic_id": primary_topic.topic_id,
                "state": primary_topic.state,
                "timestamp": datetime.now(),
                "message_preview": message[:50] + "..." if len(message) > 50 else message
            })
    
    def _decide_next_state(
        self, 
        detected_topics: List[ConversationTopic],
        memory: ConversationMemory,
        transition_type: FlowTransition
    ) -> ConversationState:
        """Decide próximo estado da conversa"""
        
        if not detected_topics:
            # Se não detectou tópicos, manter estado atual ou ir para idle
            if memory.current_state == ConversationState.IDLE:
                return ConversationState.GREETING
            return memory.current_state
        
        primary_topic = detected_topics[0]
        
        # Se é múltiplos tópicos, priorizar o mais importante
        if transition_type == FlowTransition.MULTI_TOPIC and len(detected_topics) > 1:
            return ConversationState.MULTI_INTENT
        
        # Se é back reference, verificar tópico no histórico
        if transition_type == FlowTransition.BACK_REFERENCE:
            # Encontrar tópico mencionado anteriormente
            for hist_entry in reversed(memory.topic_history):
                if hist_entry["topic_id"] in [t.topic_id for t in detected_topics]:
                    return hist_entry["state"]
        
        # Verificar se transição é válida
        current_state_str = memory.current_state.value
        if current_state_str in self.state_transitions:
            valid_transitions = self.state_transitions[current_state_str]
            if primary_topic.state in valid_transitions:
                return primary_topic.state
        
        # Se não é válida, forçar baseado na prioridade do tópico
        if primary_topic.priority >= 8:  # Tópicos de alta prioridade
            return primary_topic.state
        
        # Manter estado atual
        return memory.current_state
    
    def _generate_agent_instructions(
        self,
        next_state: ConversationState,
        detected_topics: List[ConversationTopic], 
        memory: ConversationMemory,
        transition_type: FlowTransition
    ) -> Dict[str, Any]:
        """Gera instruções específicas para o agente"""
        
        instructions = {
            "primary_focus": detected_topics[0].name if detected_topics else "General",
            "conversation_state": next_state.value,
            "transition_type": transition_type.value,
            "context_awareness": [],
            "response_style": "natural",
            "priority_actions": [],
            "avoid_topics": [],
            "maintain_context": True
        }
        
        # Instruções baseadas no tipo de transição
        if transition_type == FlowTransition.BACK_REFERENCE:
            instructions["context_awareness"].append("Client is referring back to previous topic")
            instructions["response_style"] = "acknowledging_reference"
            instructions["priority_actions"].append("Connect current response to previous context")
        
        elif transition_type == FlowTransition.TOPIC_CHANGE:
            instructions["context_awareness"].append("Client is changing subject")
            instructions["response_style"] = "smooth_transition"
            instructions["priority_actions"].append("Acknowledge topic change gracefully")
        
        elif transition_type == FlowTransition.INTERRUPT:
            instructions["context_awareness"].append("Client is interrupting/interjecting")
            instructions["response_style"] = "accommodating"
            instructions["priority_actions"].append("Address immediate concern first")
        
        elif transition_type == FlowTransition.MULTI_TOPIC:
            instructions["context_awareness"].append("Client mentioned multiple topics")
            instructions["response_style"] = "organized_multi_response"
            instructions["priority_actions"].append("Address all topics in order of priority")
        
        # Instruções baseadas no estado
        state_instructions = {
            ConversationState.MULTI_INTENT: {
                "response_style": "structured_multi_topic",
                "priority_actions": ["List all topics mentioned", "Ask which to address first"],
                "context_awareness": ["Multiple intentions detected"]
            },
            
            ConversationState.SCHEDULING: {
                "response_style": "efficient_scheduling",
                "priority_actions": ["Check availability", "Confirm details"],
                "avoid_topics": ["lengthy_explanations"]
            },
            
            ConversationState.PRICING: {
                "response_style": "transparent_pricing",
                "priority_actions": ["Provide clear pricing", "Explain value"],
                "context_awareness": ["Price sensitivity"]
            },
            
            ConversationState.OBJECTION_HANDLING: {
                "response_style": "empathetic_resolution",
                "priority_actions": ["Understand concern", "Provide reassurance"],
                "context_awareness": ["Client has concerns"]
            }
        }
        
        if next_state in state_instructions:
            instructions.update(state_instructions[next_state])
        
        # Adicionar contexto dos tópicos ativos
        active_topics_context = []
        for topic_id, topic in memory.active_topics.items():
            if not topic.resolved and topic.mentions > 0:
                active_topics_context.append(f"{topic.name} (mentioned {topic.mentions}x)")
        
        instructions["active_topics"] = active_topics_context
        
        return instructions
    
    def _calculate_decision_confidence(
        self,
        detected_topics: List[ConversationTopic],
        memory: ConversationMemory, 
        transition_type: FlowTransition
    ) -> float:
        """Calcula confiança na decisão"""
        
        base_confidence = 0.5
        
        # Confiança baseada nos tópicos detectados
        if detected_topics:
            topic_confidence = sum(t.confidence for t in detected_topics) / len(detected_topics)
            base_confidence += topic_confidence * 0.3
        
        # Confiança baseada no tipo de transição
        transition_confidence = {
            FlowTransition.NATURAL_PROGRESSION: 0.2,
            FlowTransition.BACK_REFERENCE: 0.15,
            FlowTransition.TOPIC_CHANGE: 0.1,
            FlowTransition.INTERRUPT: 0.1,
            FlowTransition.CLARIFICATION: 0.15,
            FlowTransition.MULTI_TOPIC: 0.05
        }
        
        base_confidence += transition_confidence.get(transition_type, 0.1)
        
        # Confiança baseada no histórico
        if len(memory.topic_history) > 2:
            base_confidence += 0.1  # Mais contexto = mais confiança
        
        return min(0.95, base_confidence)
    
    def _generate_reasoning(
        self,
        detected_topics: List[ConversationTopic],
        memory: ConversationMemory,
        transition_type: FlowTransition,
        next_state: ConversationState
    ) -> str:
        """Gera reasoning para a decisão"""
        
        reasoning_parts = []
        
        # Reasoning sobre tópicos
        if detected_topics:
            primary_topic = detected_topics[0]
            reasoning_parts.append(f"Primary topic detected: {primary_topic.name} (confidence: {primary_topic.confidence:.2f})")
            
            if len(detected_topics) > 1:
                other_topics = [t.name for t in detected_topics[1:]]
                reasoning_parts.append(f"Additional topics: {', '.join(other_topics)}")
        
        # Reasoning sobre transição
        transition_reasons = {
            FlowTransition.NATURAL_PROGRESSION: "Following natural conversation flow",
            FlowTransition.BACK_REFERENCE: "Client referenced previous topic",
            FlowTransition.TOPIC_CHANGE: "Client initiated topic change",
            FlowTransition.INTERRUPT: "Client interrupted with new concern",
            FlowTransition.CLARIFICATION: "Client requested clarification",
            FlowTransition.MULTI_TOPIC: "Multiple topics mentioned simultaneously"
        }
        
        reasoning_parts.append(transition_reasons.get(transition_type, "Standard progression"))
        
        # Reasoning sobre estado atual
        reasoning_parts.append(f"Current state: {memory.current_state.value} → Next state: {next_state.value}")
        
        # Contexto adicional
        if memory.context_switches > 3:
            reasoning_parts.append("High context switching detected - maintaining flexibility")
        
        return ". ".join(reasoning_parts)
    
    def _generate_contextual_response(
        self,
        next_state: ConversationState,
        detected_topics: List[ConversationTopic],
        memory: ConversationMemory,
        transition_type: FlowTransition
    ) -> str:
        """Gera sugestão de resposta contextual"""
        
        # Templates baseados no tipo de transição
        transition_templates = {
            FlowTransition.BACK_REFERENCE: "Sim, voltando ao que falávamos sobre {topic}...",
            FlowTransition.TOPIC_CHANGE: "Entendi, agora sobre {topic}...",
            FlowTransition.INTERRUPT: "Claro, primeiro vamos resolver {topic}...",
            FlowTransition.CLARIFICATION: "Vou explicar melhor sobre {topic}...",
            FlowTransition.MULTI_TOPIC: "Vejo que você quer saber sobre {topics}. Vamos por partes...",
            FlowTransition.NATURAL_PROGRESSION: "Perfeito, sobre {topic}..."
        }
        
        # Estado específico
        state_responses = {
            ConversationState.MULTI_INTENT: "Entendi que você quer falar sobre várias coisas. Podemos abordar: {topics}. Por qual prefere começar?",
            ConversationState.SCHEDULING: "Vamos agendar então! Que dia e horário funcionam melhor para você?",
            ConversationState.PRICING: "Sobre os valores, posso te explicar nossas opções...",
            ConversationState.SUPPORT: "Estou aqui para te ajudar! Vamos resolver isso juntos.",
            ConversationState.OBJECTION_HANDLING: "Entendo sua preocupação. Deixe-me esclarecer isso para você..."
        }
        
        # Gerar resposta
        if next_state == ConversationState.MULTI_INTENT and len(detected_topics) > 1:
            topics_list = [t.name for t in detected_topics]
            return state_responses[next_state].format(topics=", ".join(topics_list))
        
        elif next_state in state_responses:
            return state_responses[next_state]
        
        elif transition_type in transition_templates and detected_topics:
            primary_topic = detected_topics[0].name
            if transition_type == FlowTransition.MULTI_TOPIC:
                topics_list = [t.name for t in detected_topics]
                return transition_templates[transition_type].format(topics=", ".join(topics_list))
            else:
                return transition_templates[transition_type].format(topic=primary_topic)
        
        return "Como posso te ajudar com isso?"
    
    def _identify_context_to_maintain(
        self, 
        memory: ConversationMemory, 
        detected_topics: List[ConversationTopic]
    ) -> List[str]:
        """Identifica contexto que deve ser mantido"""
        
        context_to_maintain = []
        
        # Tópicos ainda não resolvidos
        for topic_id, topic in memory.active_topics.items():
            if not topic.resolved and topic.mentions > 0:
                context_to_maintain.append(topic_id)
        
        # Tópicos recentes com alta prioridade
        for topic in detected_topics:
            if topic.priority >= 8:
                context_to_maintain.append(topic.topic_id)
        
        # Preferências do usuário estabelecidas
        for pref_key in memory.user_preferences:
            context_to_maintain.append(f"preference_{pref_key}")
        
        return list(set(context_to_maintain))  # Remove duplicatas


class ConversationMemoryManager:
    """Gerenciador centralizado de memória conversacional"""
    
    def __init__(self):
        self.conversation_contexts: Dict[str, Dict[str, Any]] = {}
        self.service_discussions: Dict[str, Dict[str, Any]] = {}
        self.scheduling_contexts: Dict[str, Dict[str, Any]] = {}
        
    async def get_or_create_context(self, user_id: str) -> Dict[str, Any]:
        """Obtém ou cria contexto de conversa para um usuário"""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = {
                'current_topic': None,
                'last_service_discussed': None,
                'last_scheduling_context': None,
                'conversation_history': [],
                'user_preferences': {},
                'created_at': datetime.now(),
                'last_updated': datetime.now()
            }
        return self.conversation_contexts[user_id]
    
    async def update_context(self, user_id: str, **updates):
        """Atualiza contexto de conversa"""
        context = await self.get_or_create_context(user_id)
        context.update(updates)
        context['last_updated'] = datetime.now()
    
    async def remember_service_discussion(self, user_id: str, service_name: str, details: Dict[str, Any]):
        """Lembra discussão sobre um serviço específico"""
        if user_id not in self.service_discussions:
            self.service_discussions[user_id] = {}
        
        self.service_discussions[user_id][service_name] = {
            'discussed_at': datetime.now(),
            'details': details,
            'mentions': self.service_discussions[user_id].get(service_name, {}).get('mentions', 0) + 1
        }
        
        # Atualizar contexto principal
        await self.update_context(user_id, last_service_discussed=service_name)
    
    async def remember_scheduling_context(self, user_id: str, service_name: str, scheduling_data: Dict[str, Any]):
        """Lembra contexto de agendamento"""
        if user_id not in self.scheduling_contexts:
            self.scheduling_contexts[user_id] = {}
        
        self.scheduling_contexts[user_id] = {
            'service_name': service_name,
            'scheduling_data': scheduling_data,
            'created_at': datetime.now(),
            'last_updated': datetime.now()
        }
        
        # Atualizar contexto principal
        await self.update_context(user_id, last_scheduling_context=service_name)
    
    async def get_relevant_context(self, user_id: str, current_message: str) -> Dict[str, Any]:
        """Obtém contexto relevante para a mensagem atual"""
        context = await self.get_or_create_context(user_id)
        relevant_info = {}
        
        # Verificar se há discussão recente sobre serviços
        if user_id in self.service_discussions:
            for service_name, discussion in self.service_discussions[user_id].items():
                if discussion['discussed_at'] > datetime.now() - timedelta(minutes=30):
                    relevant_info['recent_service_discussion'] = {
                        'service': service_name,
                        'details': discussion['details']
                    }
        
        # Verificar se há contexto de agendamento ativo
        if user_id in self.scheduling_contexts:
            scheduling_context = self.scheduling_contexts[user_id]
            if scheduling_context['last_updated'] > datetime.now() - timedelta(minutes=15):
                relevant_info['active_scheduling'] = scheduling_context
        
        # Verificar histórico de conversa recente
        recent_history = [msg for msg in context['conversation_history'] 
                         if msg['timestamp'] > datetime.now() - timedelta(minutes=10)]
        if recent_history:
            relevant_info['recent_conversation'] = recent_history[-3:]  # Últimas 3 mensagens
        
        return relevant_info
    
    async def _update_conversation_memory(self, user_id: str, message: str, response: str):
        """Atualiza memória da conversa"""
        context = await self.get_or_create_context(user_id)
        
        # Adicionar à história
        context['conversation_history'].append({
            'message': message,
            'response': response,
            'timestamp': datetime.now()
        })
        
        # Manter apenas últimas 20 mensagens
        if len(context['conversation_history']) > 20:
            context['conversation_history'] = context['conversation_history'][-20:]
        
        # Atualizar timestamp
        context['last_updated'] = datetime.now()
    
    async def clear_old_contexts(self, max_age_hours: int = 24):
        """Limpa contextos antigos"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Limpar contextos antigos
        old_users = [user_id for user_id, context in self.conversation_contexts.items()
                    if context['last_updated'] < cutoff_time]
        
        for user_id in old_users:
            del self.conversation_contexts[user_id]
            if user_id in self.service_discussions:
                del self.service_discussions[user_id]
            if user_id in self.scheduling_contexts:
                del self.scheduling_contexts[user_id]

class ResponseRouter:
    """Roteador inteligente para seleção de resposta única"""
    
    def __init__(self):
        self.routing_rules = self._initialize_routing_rules()
        self.response_templates = self._initialize_response_templates()
    
    def _initialize_routing_rules(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa regras de roteamento"""
        return {
            'greeting': {
                'patterns': ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite'],
                'priority': 1,
                'response_type': 'greeting'
            },
            'service_inquiry': {
                'patterns': ['serviços', 'o que vocês fazem', 'tratamentos'],
                'priority': 2,
                'response_type': 'services_list'
            },
            'price_inquiry': {
                'patterns': ['quanto custa', 'preço', 'valor', 'custa quanto'],
                'priority': 3,
                'response_type': 'price_info'
            },
            'booking_request': {
                'patterns': ['agendar', 'marcar', 'quero agendar', 'preciso agendar'],
                'priority': 4,
                'response_type': 'booking_request'
            },
            'company_info': {
                'patterns': ['horário', 'funcionamento', 'endereço', 'onde vocês ficam'],
                'priority': 5,
                'response_type': 'company_info'
            }
        }
    
    def _initialize_response_templates(self) -> Dict[str, str]:
        """Inicializa templates de resposta"""
        return {
            'greeting': 'Olá! Como posso ajudar você hoje no Studio Beleza Bem-Estar? 🌟',
            'services_list': '📋 Aqui estão nossos serviços disponíveis...',
            'price_info': '💰 Aqui está a informação sobre preços...',
            'booking_request': '📅 Vamos agendar seu serviço...',
            'company_info': '🏢 Aqui estão as informações da empresa...'
        }
    
    async def route_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Roteia mensagem e retorna resposta apropriada"""
        # Detectar intenção
        intent = self._detect_intent(message)
        
        # Calcular confiança
        confidence = self._calculate_confidence(message, intent)
        
        # Selecionar resposta única
        response = self._select_single_response(intent, context)
        
        # Aplicar contexto se disponível
        if context:
            response = self._apply_context(response, context)
        
        # Validar resposta
        validated_response = self._validate_response(response)
        
        return {
            'intent': intent,
            'confidence': confidence,
            'response': validated_response,
            'response_type': intent.get('response_type', 'general')
        }
    
    def _detect_intent(self, message: str) -> Dict[str, Any]:
        """Detecta intenção da mensagem"""
        message_lower = message.lower()
        
        for rule_name, rule in self.routing_rules.items():
            for pattern in rule['patterns']:
                if pattern in message_lower:
                    return {
                        'rule_name': rule_name,
                        'priority': rule['priority'],
                        'response_type': rule['response_type'],
                        'matched_pattern': pattern
                    }
        
        return {
            'rule_name': 'general',
            'priority': 0,
            'response_type': 'general',
            'matched_pattern': None
        }
    
    def _calculate_confidence(self, message: str, intent: Dict[str, Any]) -> float:
        """Calcula confiança da detecção de intenção"""
        if intent['rule_name'] == 'general':
            return 0.3
        
        # Verificar se há múltiplos padrões correspondentes
        message_lower = message.lower()
        matches = 0
        
        for rule_name, rule in self.routing_rules.items():
            for pattern in rule['patterns']:
                if pattern in message_lower:
                    matches += 1
        
        if matches == 1:
            return 0.9
        elif matches > 1:
            return 0.7
        else:
            return 0.5
    
    def _select_single_response(self, intent: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Seleciona uma única resposta apropriada"""
        response_type = intent.get('response_type', 'general')
        
        # Verificar se há contexto específico
        if context and 'active_scheduling' in context:
            if response_type == 'booking_request':
                return f"📅 Continuando seu agendamento para {context['active_scheduling']['service_name']}..."
        
        if context and 'recent_service_discussion' in context:
            if response_type == 'price_inquiry':
                service = context['recent_service_discussion']['service']
                return f"💰 Sobre {service}, aqui estão os preços..."
        
        # Retornar template padrão
        return self.response_templates.get(response_type, "Como posso ajudar você?")
    
    def _apply_context(self, response: str, context: Dict[str, Any]) -> str:
        """Aplica contexto à resposta"""
        # Implementar lógica de aplicação de contexto
        return response
    
    def _validate_response(self, response: str) -> str:
        """Valida resposta antes de retornar"""
        if not response or len(response.strip()) < 10:
            return "Desculpe, não consegui gerar uma resposta adequada. Pode reformular sua pergunta?"
        return response

class ResponseMonitor:
    """Monitor de respostas para detectar anomalias"""
    
    def __init__(self):
        self.response_logs: List[Dict[str, Any]] = []
        self.anomaly_detectors = {
            'multiple_responses': self._detect_multiple_responses,
            'context_loss': self._detect_context_loss,
            'inconsistent_responses': self._detect_inconsistent_responses,
            'spam_patterns': self._detect_spam_patterns
        }
        self.alert_thresholds = {
            'multiple_responses': 2,  # Máximo de respostas por mensagem
            'context_loss_threshold': 0.3,  # Similaridade mínima para manter contexto
            'response_similarity_threshold': 0.8  # Similaridade para detectar duplicatas
        }
    
    async def log_response(self, user_id: str, message: str, response: str, metadata: Dict[str, Any] = None):
        """Registra resposta para monitoramento"""
        log_entry = {
            'user_id': user_id,
            'message': message,
            'response': response,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        }
        
        self.response_logs.append(log_entry)
        
        # Verificar anomalias
        await self._check_anomalies(user_id, message, response)
        
        # Limpar logs antigos
        await self._cleanup_old_logs()
    
    async def _check_anomalies(self, user_id: str, message: str, response: str):
        """Verifica anomalias na resposta"""
        for anomaly_type, detector in self.anomaly_detectors.items():
            try:
                if await detector(user_id, message, response):
                    await self._handle_anomaly(anomaly_type, user_id, message, response)
            except Exception as e:
                logger.error(f"Erro ao verificar anomalia {anomaly_type}: {e}")
    
    async def _detect_multiple_responses(self, user_id: str, message: str, response: str) -> bool:
        """Detecta múltiplas respostas para uma mensagem"""
        recent_logs = [log for log in self.response_logs 
                      if log['user_id'] == user_id and 
                      log['timestamp'] > datetime.now() - timedelta(seconds=30)]
        
        if len(recent_logs) > self.alert_thresholds['multiple_responses']:
            logger.warning(f"🚨 Múltiplas respostas detectadas para {user_id}: {len(recent_logs)} respostas")
            return True
        
        return False
    
    async def _detect_context_loss(self, user_id: str, message: str, response: str) -> bool:
        """Detecta perda de contexto na conversa"""
        recent_logs = [log for log in self.response_logs 
                      if log['user_id'] == user_id and 
                      log['timestamp'] > datetime.now() - timedelta(minutes=5)]
        
        if len(recent_logs) >= 2:
            # Verificar se há mudança brusca de tópico
            last_message = recent_logs[-2]['message']
            current_message = message
            
            similarity = self._calculate_text_similarity(last_message, current_message)
            
            if similarity < self.alert_thresholds['context_loss_threshold']:
                logger.warning(f"🚨 Perda de contexto detectada para {user_id}: similaridade {similarity:.2f}")
                return True
        
        return False
    
    async def _detect_inconsistent_responses(self, user_id: str, message: str, response: str) -> bool:
        """Detecta respostas inconsistentes"""
        recent_logs = [log for log in self.response_logs 
                      if log['user_id'] == user_id and 
                      log['timestamp'] > datetime.now() - timedelta(minutes=10)]
        
        if len(recent_logs) >= 2:
            # Verificar se há contradições nas respostas
            for i in range(len(recent_logs) - 1):
                resp1 = recent_logs[i]['response']
                resp2 = recent_logs[i + 1]['response']
                
                # Verificar contradições básicas
                if self._has_contradictions(resp1, resp2):
                    logger.warning(f"🚨 Contradição detectada para {user_id}")
                    return True
        
        return False
    
    async def _detect_spam_patterns(self, user_id: str, message: str, response: str) -> bool:
        """Detecta padrões de spam"""
        recent_logs = [log for log in self.response_logs 
                      if log['user_id'] == user_id and 
                      log['timestamp'] > datetime.now() - timedelta(minutes=1)]
        
        if len(recent_logs) > 5:  # Mais de 5 mensagens por minuto
            logger.warning(f"🚨 Padrão de spam detectado para {user_id}: {len(recent_logs)} mensagens/min")
            return True
        
        return False
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre dois textos"""
        if not text1 or not text2:
            return 0.0
        
        # Normalizar textos
        text1_norm = re.sub(r'[^\w\s]', '', text1.lower())
        text2_norm = re.sub(r'[^\w\s]', '', text2.lower())
        
        # Calcular similaridade
        return SequenceMatcher(None, text1_norm, text2_norm).ratio()
    
    def _has_contradictions(self, resp1: str, resp2: str) -> bool:
        """Verifica se há contradições entre duas respostas"""
        # Implementar lógica de detecção de contradições
        # Por exemplo: "não oferecemos" vs "custa R$ X"
        contradictions = [
            ('não oferecemos', 'custa'),
            ('não disponível', 'r$'),
            ('não fazemos', 'preço')
        ]
        
        for neg, pos in contradictions:
            if neg in resp1.lower() and pos in resp2.lower():
                return True
            if neg in resp2.lower() and pos in resp1.lower():
                return True
        
        return False
    
    async def _handle_anomaly(self, anomaly_type: str, user_id: str, message: str, response: str):
        """Trata anomalia detectada"""
        logger.error(f"🚨 ANOMALIA DETECTADA: {anomaly_type}")
        logger.error(f"   Usuário: {user_id}")
        logger.error(f"   Mensagem: {message}")
        logger.error(f"   Resposta: {response}")
        
        # Aqui você pode implementar ações como:
        # - Enviar alerta para administradores
        # - Ativar modo de segurança
        # - Registrar métricas para análise
    
    async def _cleanup_old_logs(self, max_age_hours: int = 24):
        """Limpa logs antigos"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        self.response_logs = [log for log in self.response_logs 
                            if log['timestamp'] > cutoff_time]
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de monitoramento"""
        return {
            'total_responses_logged': len(self.response_logs),
            'anomalies_detected': len([log for log in self.response_logs if 'anomaly' in log.get('metadata', {})]),
            'active_users': len(set(log['user_id'] for log in self.response_logs[-100:])),  # Últimas 100 respostas
            'last_anomaly': max([log['timestamp'] for log in self.response_logs if 'anomaly' in log.get('metadata', {})], default=None)
        }


class ConversationFlowService:
    """Serviço de gerenciamento de fluxo conversacional COM CORREÇÕES IMPLEMENTADAS"""
    
    def __init__(self):
        self.flow_engine = ConversationFlowEngine()
        self.memory_manager = ConversationMemoryManager()
        self.response_router = ResponseRouter()
        self.response_monitor = ResponseMonitor()
        self.conversation_memories: Dict[str, ConversationMemory] = {}
    
    async def process_message(self, message: str, user_phone: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        Processa mensagem com controle de resposta única e roteamento inteligente
        
        Args:
            message: Mensagem do usuário
            user_phone: Telefone do usuário
            context: Contexto adicional
            
        Returns:
            Resposta única ou None se deve ignorar
        """
        try:
            # 1. CONTROLE DE RESPOSTA ÚNICA
            should_process = await self.flow_engine.ensure_single_response(user_phone, message)
            if not should_process:
                logger.info(f"🔄 Ignorando mensagem duplicada para {user_phone}")
                return None
            
            # 2. OBTER CONTEXTO RELEVANTE
            relevant_context = await self.memory_manager.get_relevant_context(user_phone, message)
            
            # 3. ROTEAR MENSAGEM
            routing_result = await self.response_router.route_message(message, relevant_context)
            
            # 4. ATUALIZAR MEMÓRIA DA CONVERSAÇÃO
            await self.memory_manager._update_conversation_memory(user_phone, message, routing_result['response'])
            
            # 5. MONITORAR RESPOSTA
            await self.response_monitor.log_response(
                user_phone, message, routing_result['response'],
                {'routing_intent': routing_result['intent'], 'confidence': routing_result['confidence']}
            )
            
            # 6. MARCAR RESPOSTA COMO ENVIADA
            await self.flow_engine.mark_response_sent(user_phone, message, routing_result['response'])
            
            logger.info(f"✅ Resposta única processada para {user_phone}: {routing_result['response_type']}")
            return routing_result['response']
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento da mensagem: {e}")
            return None
    
    # 🆕 MÉTODO COMPATIBILIDADE - CHAMA O NOVO SISTEMA
    def process_message_flow(
        self,
        message: str,
        user_phone: str,
        context: Dict[str, Any] = None
    ) -> 'FlowDecision':
        """
        MÉTODO DE COMPATIBILIDADE - Chama o novo sistema de correções
        
        Args:
            message: Mensagem do usuário
            user_phone: Telefone do usuário
            context: Contexto adicional
            
        Returns:
            FlowDecision para compatibilidade com código existente
        """
        try:
            # Importar aqui para evitar circular imports
            from app.services.conversation_flow import FlowDecision, FlowTransition, ConversationState
            import asyncio
            
            # Criar novo event loop se necessário
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Processar com o novo sistema de forma síncrona
            if loop.is_running():
                # Se já há um loop rodando, usar create_task
                task = loop.create_task(self.process_message(message, user_phone, context))
                # Aguardar resultado
                response = None
                try:
                    response = task.result()
                except Exception as e:
                    logger.error(f"Erro ao aguardar task: {e}")
            else:
                # Executar no loop
                response = loop.run_until_complete(self.process_message(message, user_phone, context))
            
            if response:
                # Retornar decisão de fluxo compatível
                return FlowDecision(
                    next_state=ConversationState.CONVERSATION,
                    transition_type=FlowTransition.NATURAL_PROGRESSION,
                    confidence=0.9,
                    reasoning="Processado pelo novo sistema de correções"
                )
            else:
                # Mensagem ignorada (duplicada/similar)
                return FlowDecision(
                    next_state=ConversationState.CONVERSATION,
                    transition_type=FlowTransition.NATURAL_PROGRESSION,
                    confidence=0.1,
                    reasoning="Mensagem ignorada pelo controle de resposta única"
                )
                
        except Exception as e:
            logger.error(f"❌ Erro no process_message_flow: {e}")
            
            # Fallback para decisão padrão
            from app.services.conversation_flow import FlowDecision, FlowTransition, ConversationState
            return FlowDecision(
                next_state=ConversationState.CONVERSATION,
                transition_type=FlowTransition.NATURAL_PROGRESSION,
                confidence=0.5,
                reasoning=f"Erro no processamento: {str(e)}"
            )
    
    def get_conversation_summary(self, user_phone: str) -> Dict[str, Any]:
        """Retorna resumo da conversa"""
        
        if user_phone not in self.conversation_memories:
            return {"status": "no_conversation"}
        
        memory = self.conversation_memories[user_phone]
        
        return {
            "current_state": memory.current_state.value,
            "previous_state": memory.previous_state.value if memory.previous_state else None,
            "active_topics": {
                topic_id: {
                    "name": topic.name,
                    "mentions": topic.mentions,
                    "resolved": topic.resolved,
                    "priority": topic.priority
                }
                for topic_id, topic in memory.active_topics.items()
            },
            "topic_history": list(memory.topic_history),
            "context_switches": memory.context_switches,
            "conversation_duration": str(memory.last_activity - memory.conversation_start),
            "user_preferences": memory.user_preferences,
            "pending_questions": memory.pending_questions
        }
    
    def reset_conversation(self, user_phone: str):
        """Reseta conversa para começar do zero"""
        if user_phone in self.conversation_memories:
            del self.conversation_memories[user_phone]
        logger.info(f"Conversation reset for {user_phone}")
    
    def mark_topic_resolved(self, user_phone: str, topic_id: str):
        """Marca tópico como resolvido"""
        if user_phone in self.conversation_memories:
            memory = self.conversation_memories[user_phone]
            if topic_id in memory.active_topics:
                memory.active_topics[topic_id].resolved = True
                logger.info(f"Topic {topic_id} marked as resolved for {user_phone}")


# Instância global do serviço
conversation_flow_service = ConversationFlowService()
