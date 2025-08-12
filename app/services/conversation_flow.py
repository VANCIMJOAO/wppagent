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
    """Memória da conversa para contexto"""
    topic_history: deque = field(default_factory=lambda: deque(maxlen=10))
    active_topics: Dict[str, ConversationTopic] = field(default_factory=dict)
    current_state: ConversationState = ConversationState.GREETING
    previous_state: Optional[ConversationState] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    pending_questions: List[str] = field(default_factory=list)
    context_switches: int = 0
    conversation_start: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


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
    """Engine de fluxo conversacional não-linear"""
    
    def __init__(self):
        self.topic_definitions = self._initialize_topics()
        self.state_transitions = self._initialize_transitions()
        self.context_patterns = self._initialize_context_patterns()
        
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


class ConversationFlowService:
    """Serviço de gerenciamento de fluxo conversacional"""
    
    def __init__(self):
        self.engine = ConversationFlowEngine()
        self.conversation_memories: Dict[str, ConversationMemory] = {}
    
    def process_message_flow(
        self,
        message: str,
        user_phone: str,
        context: Dict[str, Any] = None
    ) -> FlowDecision:
        """Processa mensagem e retorna decisão de fluxo"""
        
        # Obter ou criar memória da conversa
        if user_phone not in self.conversation_memories:
            self.conversation_memories[user_phone] = ConversationMemory()
        
        memory = self.conversation_memories[user_phone]
        
        # Analisar fluxo
        decision = self.engine.analyze_conversation_flow(
            message, user_phone, memory, context
        )
        
        # Atualizar estado atual na memória
        memory.previous_state = memory.current_state
        memory.current_state = decision.next_state
        
        # Incrementar switches se mudou de estado
        if decision.transition_type != FlowTransition.NATURAL_PROGRESSION:
            memory.context_switches += 1
        
        logger.info(f"Flow decision for {user_phone}: {decision.transition_type.value} → {decision.next_state.value}")
        
        return decision
    
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
