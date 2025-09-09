"""
Sistema CrewAI Multi-Agentes para WhatsApp Agent (Versão com Lazy Loading)
Carregamento sob demanda para evitar problemas de permissão na inicialização
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from enum import Enum

from app.config import settings
from app.utils.logger import get_logger

logger = logging.getLogger(__name__)

# Variáveis globais para lazy loading
_crewai_loaded = False
_crewai_error = None
_Agent = None
_Task = None
_Crew = None
_Process = None

def _load_crewai():
    """Carrega CrewAI sob demanda com tratamento de erro"""
    global _crewai_loaded, _crewai_error, _Agent, _Task, _Crew, _Process
    
    if _crewai_loaded:
        return True
    
    if _crewai_error:
        raise _crewai_error
    
    try:
        print("🔧 Aplicando fix de permissões CrewAI...")
        from app.utils.crewai_fix import fix_crewai_permissions, alternative_crewai_init
        
        # Tentar fix principal, senão usar alternativo
        if not fix_crewai_permissions():
            print("🔄 Fix principal falhou, usando alternativo...")
            alternative_crewai_init()
        
        # Configurar a chave da API do OpenAI para o CrewAI
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
        
        # Importar CrewAI após as correções
        from crewai import Agent, Task, Crew, Process
        
        _Agent = Agent
        _Task = Task
        _Crew = Crew
        _Process = Process
        _crewai_loaded = True
        
        print("✅ CrewAI carregado com sucesso!")
        return True
        
    except Exception as e:
        _crewai_error = e
        logger.error(f"Erro ao carregar CrewAI: {str(e)}")
        print(f"❌ Falha ao carregar CrewAI: {str(e)}")
        return False


class AgentRole(Enum):
    """Roles dos agentes especializados"""
    RECEPTIONIST = "receptionist"
    SCHEDULER = "scheduler"
    SALES = "sales"
    SUPPORT = "support"
    SUPERVISOR = "supervisor"


class WhatsAppAgentCrew:
    """Sistema de múltiplos agentes especializados para WhatsApp"""
    
    def __init__(self):
        self.crew = None
        self.agents = {}
        self.performance_metrics = {
            "tasks_completed": 0,
            "response_time": [],
            "agent_usage": {role.value: 0 for role in AgentRole},
            "success_rate": 0.0
        }
        self._crewai_initialized = False
    
    def _ensure_crewai_loaded(self):
        """Garante que o CrewAI está carregado antes de usar"""
        if not self._crewai_initialized:
            if not _load_crewai():
                raise RuntimeError("CrewAI não pôde ser carregado. Verifique as permissões.")
            self._initialize_agents()
            self._initialize_crew()
            self._crewai_initialized = True
    
    def _initialize_agents(self):
        """Inicializa todos os agentes especializados"""
        
        # 1. Maria - Agente Recepcionista
        self.agents[AgentRole.RECEPTIONIST] = _Agent(
            role="Recepcionista Virtual",
            goal="Recepcionar clientes com cordialidade e direcionar para o agente correto",
            backstory="""Você é Maria, uma recepcionista virtual experiente e cordial. 
            Você é a primeira pessoa que os clientes encontram e é responsável por criar 
            uma primeira impressão positiva. Você identifica a necessidade do cliente 
            e direciona para o agente especializado apropriado.""",
            verbose=settings.debug,  # Condicional ao debug
            allow_delegation=True,
            llm_config={
                "model": "gpt-4o-mini",
                "temperature": 0.7
            }
        )
        
        # 2. Carlos - Agente Agendamento
        self.agents[AgentRole.SCHEDULER] = _Agent(
            role="Especialista em Agendamentos",
            goal="Gerenciar agendamentos de forma eficiente e organizada",
            backstory="""Você é Carlos, um especialista em agendamentos altamente organizado. 
            Você gerencia calendários, horários disponíveis e confirmações de agendamento. 
            Você é meticuloso com datas e horários e sempre confirma os detalhes com os clientes.""",
            verbose=settings.debug,  # Condicional ao debug
            allow_delegation=False,
            llm_config={
                "model": "gpt-4o-mini",
                "temperature": 0.3
            }
        )
        
        # 3. Ana - Agente Vendas
        self.agents[AgentRole.SALES] = _Agent(
            role="Consultora de Vendas",
            goal="Maximizar conversões através de consulta especializada",
            backstory="""Você é Ana, uma consultora de vendas experiente e persuasiva. 
            Você entende as necessidades dos clientes, qualifica leads e apresenta 
            soluções personalizadas. Você é focada em resultados mas sempre ética 
            e centrada no cliente.""",
            verbose=settings.debug,  # Condicional ao debug
            allow_delegation=False,
            llm_config={
                "model": "gpt-4o-mini",
                "temperature": 0.8
            }
        )
        
        # 4. Roberto - Agente Suporte
        self.agents[AgentRole.SUPPORT] = _Agent(
            role="Especialista em Suporte Técnico",
            goal="Resolver problemas técnicos e dúvidas dos clientes",
            backstory="""Você é Roberto, um especialista em suporte técnico paciente e conhecedor. 
            Você resolve problemas complexos, explica soluções de forma clara e sempre 
            acompanha para garantir que o problema foi resolvido completamente.""",
            verbose=settings.debug,  # Condicional ao debug
            allow_delegation=False,
            llm_config={
                "model": "gpt-4o-mini",  
                "temperature": 0.2
            }
        )
        
        # 5. Patricia - Agente Supervisora
        self.agents[AgentRole.SUPERVISOR] = _Agent(
            role="Supervisora de Qualidade",
            goal="Garantir qualidade e coordenar a equipe de agentes",
            backstory="""Você é Patricia, uma supervisora experiente que garante a 
            qualidade do atendimento. Você coordena os outros agentes, resolve 
            escalações e toma decisões estratégicas sobre o atendimento.""",
            verbose=settings.debug,  # Condicional ao debug
            allow_delegation=True,
            llm_config={
                "model": "gpt-4o-mini",
                "temperature": 0.5
            }
        )
    
    def _initialize_crew(self):
        """Inicializa o crew com todos os agentes"""
        self.crew = _Crew(
            agents=list(self.agents.values()),
            tasks=[],  # Tarefas serão criadas dinamicamente
            process=_Process.hierarchical,
            manager_llm="gpt-4o-mini",
            verbose=settings.debug  # Condicional ao debug
        )
    
    def _safe_get_lead_score_data(self, lead_score: Any) -> Dict[str, Any]:
        """Extrai dados do lead score de forma segura"""
        try:
            if hasattr(lead_score, 'total_score'):
                return {
                    "total_score": getattr(lead_score, 'total_score', 50.0),
                    "category": getattr(lead_score, 'category', None),
                    "priority_level": getattr(lead_score, 'priority_level', 2),
                    "estimated_value": getattr(lead_score, 'estimated_value', 0.0)
                }
            else:
                logging.warning(f"Lead score sem atributos esperados: {lead_score}")
                return {
                    "total_score": 50.0,
                    "category": "INDEFINIDA",
                    "priority_level": 2,
                    "estimated_value": 0.0
                }
        except Exception as e:
            logging.warning(f"Erro ao extrair dados do lead score: {e}")
            return {
                "total_score": 50.0,
                "category": "INDEFINIDA", 
                "priority_level": 2,
                "estimated_value": 0.0
            }
    
    def process_message(self, message: str, user_phone: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Processa mensagem usando fluxo não-linear e agente apropriado"""
        start_time = datetime.now()
        
        try:
            # Garantir que CrewAI está carregado
            self._ensure_crewai_loaded()
            
            # Imports tardios para evitar dependências circulares
            from app.services.lead_scoring import lead_scoring_service
            from app.services.conversation_flow import conversation_flow_service
            
            # 1. Analisar fluxo conversacional não-linear
            flow_decision = conversation_flow_service.process_message_flow(
                message, user_phone, context
            )
            
            # 2. Calcular lead score
            lead_score = lead_scoring_service.score_lead(
                message=message,
                phone=user_phone,
                customer_data=context.get("customer_data") if context else None,
                context=context
            )
            
            # 3. Análise de intenção considerando fluxo e lead score
            intent = self._analyze_intent_with_flow(message, context, lead_score, flow_decision)
            
            # 4. Seleção de agente baseada em fluxo e score
            selected_agent = self._select_agent_with_flow(intent, lead_score, flow_decision)
            
            # 5. Criação da tarefa com contexto completo
            task = self._create_task_with_flow(
                message, user_phone, selected_agent, intent, context, 
                lead_score, flow_decision
            )
            
            # 6. Execução da tarefa
            result = self._execute_task(task, selected_agent)
            
            # 7. Atualização de métricas
            end_time = datetime.now()
            self._update_metrics(selected_agent, start_time, end_time, True)
            
            # Extrair dados do lead score de forma segura
            lead_score_data = self._safe_get_lead_score_data(lead_score)
            
            return {
                "response": result,
                "agent_used": selected_agent.value,
                "intent": intent,
                "processing_time": (end_time - start_time).total_seconds(),
                "status": "success",
                "lead_score": lead_score_data,
                "flow_context": {
                    "conversation_state": flow_decision.next_state.value,
                    "transition_type": flow_decision.transition_type.value,
                    "confidence": flow_decision.confidence,
                    "topics_detected": flow_decision.topics_to_activate
                }
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento CrewAI: {str(e)}")
            end_time = datetime.now()
            self._update_metrics(AgentRole.RECEPTIONIST, start_time, end_time, False)
            
            return {
                "response": "Desculpe, houve um problema interno. Nossa equipe foi notificada.",
                "agent_used": "error_handler",
                "intent": "error",
                "processing_time": (end_time - start_time).total_seconds(),
                "status": "error",
                "error": str(e)
            }
    
    def _analyze_intent_with_flow(self, message: str, context: Dict[str, Any] = None, lead_score: Any = None, flow_decision: Any = None) -> str:
        """Analisa intenção considerando fluxo conversacional e lead score"""
        from app.services.conversation_flow import ConversationState, FlowTransition
        
        message_lower = message.lower()
        
        # 1. Priorizar baseado no estado da conversa
        if flow_decision:
            conversation_state = flow_decision.next_state
            transition_type = flow_decision.transition_type
            
            # Estados de alta prioridade
            if conversation_state == ConversationState.SCHEDULING:
                return "agendamento"
            elif conversation_state == ConversationState.PRICING:
                return "consulta_preco"
            elif conversation_state == ConversationState.SUPPORT:
                return "suporte"
            elif conversation_state == ConversationState.MULTI_INTENT:
                return "multiplos_topicos"
            
            # Tipos de transição especiais
            if transition_type == FlowTransition.INTERRUPT:
                return "interrupcao_urgente"
            elif transition_type == FlowTransition.CLARIFICATION:
                return "esclarecimento"
            elif transition_type == FlowTransition.BACK_REFERENCE:
                return "retorno_topico"
        
        # 2. Considerar lead score para priorização
        priority_level = getattr(lead_score, 'priority_level', 0) if lead_score else 0
        if lead_score and priority_level >= 4:
            # Leads de alta prioridade com urgência = escalação
            if any(word in message_lower for word in ["urgente", "agora", "hoje", "imediato"]):
                return "escalation"
            
            # Leads qualificados falando de serviços = vendas diretas
            if any(word in message_lower for word in ["quero", "preciso", "vou contratar"]):
                return "vendas_qualificada"
        
        # 3. Análise tradicional de intenção
        if any(word in message_lower for word in ["agendar", "marcar", "horário", "data", "disponibilidade"]):
            return "agendamento"
            
        if any(word in message_lower for word in ["preço", "valor", "quanto custa", "orçamento"]):
            return "consulta_preco"
            
        if any(word in message_lower for word in ["cancelar", "desmarcar", "problema", "reclamação"]):
            return "suporte"
            
        if any(word in message_lower for word in ["onde", "endereço", "localização", "como chegar"]):
            return "informacao"
            
        if any(word in message_lower for word in ["corte", "barba", "sobrancelha", "massagem", "serviço"]):
            return "consulta_servico"
            
        if any(word in message_lower for word in ["olá", "oi", "bom dia", "boa tarde", "boa noite"]):
            return "saudacao"
        
        return "geral"

    def _select_agent_with_flow(self, intent: str, lead_score: Any = None, flow_decision: Any = None) -> AgentRole:
        """Seleciona agente considerando fluxo e lead score"""
        from app.services.conversation_flow import ConversationState, FlowTransition
        
        # 1. Decisões baseadas no fluxo conversacional
        if flow_decision:
            # Estados que requerem agentes específicos
            if flow_decision.next_state == ConversationState.SCHEDULING:
                return AgentRole.SCHEDULER
            elif flow_decision.next_state == ConversationState.PRICING:
                return AgentRole.SALES
            elif flow_decision.next_state == ConversationState.SUPPORT:
                return AgentRole.SUPPORT
            elif flow_decision.next_state == ConversationState.MULTI_INTENT:
                # Para múltiplas intenções, usar supervisora
                return AgentRole.SUPERVISOR
            
            # Transições especiais
            if flow_decision.transition_type == FlowTransition.INTERRUPT:
                # Interrupções podem ser urgentes - usar supervisora
                return AgentRole.SUPERVISOR
        
        # 2. Decisões baseadas no lead score
        if lead_score:
            priority_level = getattr(lead_score, 'priority_level', 0)
            # Leads de máxima prioridade vão direto para supervisora
            if priority_level == 5:
                return AgentRole.SUPERVISOR
            
            # Leads qualificados para vendas vão para sales
            if priority_level >= 4 and intent in ["vendas_qualificada", "consulta_preco"]:
                return AgentRole.SALES
        
        # 3. Seleção tradicional baseada na intenção
        intent_to_agent = {
            "agendamento": AgentRole.SCHEDULER,
            "consulta_preco": AgentRole.SALES,
            "vendas_qualificada": AgentRole.SALES,
            "suporte": AgentRole.SUPPORT,
            "escalation": AgentRole.SUPERVISOR,
            "interrupcao_urgente": AgentRole.SUPERVISOR,
            "multiplos_topicos": AgentRole.SUPERVISOR,
            "esclarecimento": AgentRole.RECEPTIONIST,
            "retorno_topico": AgentRole.RECEPTIONIST,
            "consulta_servico": AgentRole.RECEPTIONIST,
            "informacao": AgentRole.RECEPTIONIST,
            "saudacao": AgentRole.RECEPTIONIST,
            "geral": AgentRole.RECEPTIONIST
        }
        
        return intent_to_agent.get(intent, AgentRole.RECEPTIONIST)

    def _create_task_with_flow(self, message: str, user_phone: str, agent_role: AgentRole, intent: str, 
                              context: Dict[str, Any] = None, lead_score: Any = None, flow_decision: Any = None) -> Any:
        """Cria tarefa considerando fluxo conversacional não-linear"""
        from app.services.conversation_flow import ConversationState, FlowTransition
        
        # Informações do lead score
        lead_info = ""
        if lead_score:
            # Extração segura dos dados
            total_score = getattr(lead_score, 'total_score', 50.0)
            category = getattr(lead_score, 'category', None)
            category_value = getattr(category, 'value', 'INDEFINIDA') if category else 'INDEFINIDA'
            priority_level = getattr(lead_score, 'priority_level', 2)
            estimated_value = getattr(lead_score, 'estimated_value', 0.0)
            conversion_probability = getattr(lead_score, 'conversion_probability', 0.5)
            recommendations = getattr(lead_score, 'recommendations', [])
            
            lead_info = f"""
        INFORMAÇÕES DO LEAD:
        - Score: {total_score}/100 ({category_value.upper()})
        - Prioridade: {priority_level}/5
        - Valor Estimado: R$ {estimated_value:.2f}
        - Probabilidade de Conversão: {conversion_probability*100:.1f}%
        - Recomendações: {', '.join(recommendations[:2]) if recommendations else 'Nenhuma'}
        """
        
        # Informações do fluxo conversacional
        flow_info = ""
        if flow_decision:
            flow_info = f"""
        CONTEXTO DA CONVERSA:
        - Estado da Conversa: {flow_decision.next_state.value.upper()}
        - Tipo de Transição: {flow_decision.transition_type.value}
        - Confiança: {flow_decision.confidence*100:.1f}%
        - Tópicos Ativos: {', '.join(flow_decision.topics_to_activate)}
        - Instruções Especiais: {flow_decision.reasoning}
        """
        
        base_context = f"""
        Mensagem do cliente: "{message}"
        Telefone: {user_phone}
        Intenção detectada: {intent}
        Contexto adicional: {context or {}}
        {lead_info}
        {flow_info}
        """
        
        # Instruções específicas baseadas no fluxo
        flow_instructions = self._get_flow_instructions(flow_decision)
        # Extrair o valor numérico do lead_score se for um objeto
        try:
            score_value = getattr(lead_score, 'total_score', lead_score)
            priority_instructions = self._get_priority_instructions(float(score_value))
        except (ValueError, TypeError):
            priority_instructions = self._get_priority_instructions(1.0)
        
        task_descriptions = {
            AgentRole.RECEPTIONIST: f"""
            {base_context}
            
            Como recepcionista inteligente, você deve:
            
            {flow_instructions}
            
            SUAS RESPONSABILIDADES:
            1. Manter continuidade da conversa considerando o contexto
            2. Ser natural na transição entre tópicos
            3. Reconhecer quando o cliente muda de assunto
            4. Fornecer informações relevantes ao momento da conversa
            5. Direcionar adequadamente quando necessário
            
            {priority_instructions}
            
            IMPORTANTE: Seja conversacional e adaptável. Se o cliente mudou de assunto,
            acompanhe naturalmente. Se está retomando algo anterior, demonstre que lembra.
            """,
            
            AgentRole.SCHEDULER: f"""
            {base_context}
            
            Como especialista em agendamentos com consciência conversacional:
            
            {flow_instructions}
            
            SUAS RESPONSABILIDADES:
            1. Considerar o contexto da conversa para agendamento
            2. Ser flexível se o cliente mudou de ideia sobre datas/serviços
            3. Reconhecer se está reagendando ou cancelando
            4. Manter eficiência mesmo com mudanças de tópico
            
            {priority_instructions}
            
            FOCO: Agendar de forma natural e contextual, adaptando-se ao fluxo da conversa.
            """,
            
            AgentRole.SALES: f"""
            {base_context}
            
            Como consultora de vendas conversacional:
            
            {flow_instructions}
            
            SUAS RESPONSABILIDADES:
            1. Adaptar abordagem de vendas ao contexto da conversa
            2. Ser natural se cliente voltou a falar de preços/serviços
            3. Reconhecer objeções e mudanças de interesse
            4. Manter foco comercial respeitando o fluxo natural
            
            {priority_instructions}
            
            ESTRATÉGIA: Vender de forma consultiva e adaptável, seguindo o ritmo do cliente.
            """,
            
            AgentRole.SUPPORT: f"""
            {base_context}
            
            Como especialista em suporte contextual:
            
            {flow_instructions}
            
            SUAS RESPONSABILIDADES:
            1. Entender o problema no contexto da conversa completa
            2. Reconhecer se é novo problema ou continuação
            3. Ser empático com mudanças de humor/contexto
            4. Resolver de forma natural e conversacional
            
            {priority_instructions}
            
            ABORDAGEM: Resolver problemas considerando todo o contexto conversacional.
            """,
            
            AgentRole.SUPERVISOR: f"""
            {base_context}
            
            Como supervisora estratégica com visão completa:
            
            {flow_instructions}
            
            SUAS RESPONSABILIDADES:
            1. Gerenciar múltiplas intenções e tópicos complexos
            2. Tomar decisões estratégicas baseadas no fluxo completo
            3. Coordenar soluções para conversas não-lineares
            4. Garantir satisfação em cenários complexos
            
            {priority_instructions}
            
            LIDERANÇA: Gerencie a conversa de forma estratégica e empática,
            considerando toda a jornada do cliente.
            """
        }
        
        return _Task(
            description=task_descriptions[agent_role],
            expected_output="Resposta natural, contextual e adaptada ao fluxo da conversa",
            agent=self.agents[agent_role]
        )
    
    def _get_flow_instructions(self, flow_decision: Any) -> str:
        """Retorna instruções específicas baseadas no fluxo"""
        if not flow_decision:
            return ""
        
        from app.services.conversation_flow import ConversationState, FlowTransition
        
        instructions = []
        
        # Instruções por estado
        state_instructions = {
            ConversationState.MULTI_INTENT: "🔄 MÚLTIPLOS TÓPICOS: Cliente quer falar de várias coisas. Organize e priorize.",
            ConversationState.SCHEDULING: "📅 FOCO AGENDAMENTO: Conversa direcionada para marcar horário.",
            ConversationState.PRICING: "💰 DISCUSSÃO DE PREÇOS: Cliente interessado em valores e investimento.",
            ConversationState.SUPPORT: "🔧 MODO SUPORTE: Cliente precisa de ajuda ou tem problema.",
            ConversationState.OBJECTION_HANDLING: "⚠️ OBJEÇÕES: Cliente tem resistências ou dúvidas.",
            ConversationState.CLOSING: "🎯 FECHAMENTO: Momento de conclusão/decisão."
        }
        
        if flow_decision.next_state in state_instructions:
            instructions.append(state_instructions[flow_decision.next_state])
        
        # Instruções por tipo de transição
        transition_instructions = {
            FlowTransition.BACK_REFERENCE: "↩️ RETOMADA: Cliente está voltando a um tópico anterior. Demonstre que você lembra.",
            FlowTransition.TOPIC_CHANGE: "🔄 MUDANÇA DE ASSUNTO: Cliente mudou de tópico. Acompanhe naturalmente.",
            FlowTransition.INTERRUPT: "⚡ INTERRUPÇÃO: Cliente interrompeu para algo urgente. Priorize isso.",
            FlowTransition.CLARIFICATION: "❓ ESCLARECIMENTO: Cliente não entendeu algo. Explique melhor.",
            FlowTransition.MULTI_TOPIC: "🗂️ MÚLTIPLOS TEMAS: Cliente mencionou vários assuntos juntos."
        }
        
        if flow_decision.transition_type in transition_instructions:
            instructions.append(transition_instructions[flow_decision.transition_type])
        
        # Sugestão contextual
        if flow_decision.suggested_response:
            instructions.append(f"💡 SUGESTÃO: {flow_decision.suggested_response}")
        
        return "\n".join(instructions) if instructions else ""
    
    def _get_priority_instructions(self, lead_score: float) -> str:
        """Gera instruções baseadas na pontuação do lead (0-100)"""
        if lead_score >= 70.0:
            return """
            🔥 LEAD QUENTE: Este cliente tem alta intenção de compra!
            - Priorize rapidez na resposta
            - Ofereça soluções imediatas
            - Facilite o processo de agendamento
            - Seja proativo em sugerir horários
            """
        elif lead_score >= 40.0:
            return """
            ⚡ LEAD MORNO: Cliente demonstra interesse moderado
            - Mantenha o engajamento
            - Forneça informações completas
            - Guie suavemente para agendamento
            - Destaque benefícios
            """
        else:
            return """
            💙 LEAD FRIO: Cultive o relacionamento
            - Seja educativo e informativo
            - Construa confiança gradualmente
            - Não pressione por vendas
            - Ofereça valor através de informações
            """

    def _execute_task(self, task: Any, agent_role: AgentRole) -> str:
        """Executa a tarefa usando o agente selecionado"""
        try:
            # Cria um crew temporário apenas com o agente necessário
            temp_crew = _Crew(
                agents=[self.agents[agent_role]],
                tasks=[task],
                process=_Process.sequential,
                verbose=False
            )
            
            result = temp_crew.kickoff()
            return str(result)
            
        except Exception as e:
            logger.error(f"Erro na execução da tarefa com {agent_role.value}: {str(e)}")
            return f"Desculpe, houve um problema com o agente {agent_role.value}. Tentarei te ajudar de outra forma."
    
    def _update_metrics(self, agent_role: AgentRole, start_time: datetime, end_time: datetime, success: bool):
        """Atualiza métricas de performance"""
        processing_time = (end_time - start_time).total_seconds()
        
        self.performance_metrics["tasks_completed"] += 1
        self.performance_metrics["response_time"].append(processing_time)
        self.performance_metrics["agent_usage"][agent_role.value] += 1
        
        # Calcula taxa de sucesso
        if success:
            current_success = self.performance_metrics.get("successful_tasks", 0)
            self.performance_metrics["successful_tasks"] = current_success + 1
        
        total_tasks = self.performance_metrics["tasks_completed"]
        successful_tasks = self.performance_metrics.get("successful_tasks", 0)
        self.performance_metrics["success_rate"] = (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance do sistema"""
        response_times = self.performance_metrics["response_time"]
        
        return {
            "total_tasks": self.performance_metrics["tasks_completed"],
            "success_rate": self.performance_metrics["success_rate"],
            "average_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "agent_usage": self.performance_metrics["agent_usage"],
            "last_updated": datetime.now().isoformat()
        }
    
    def get_agent_info(self) -> Dict[str, Dict[str, Any]]:
        """Retorna informações sobre todos os agentes"""
        return {
            role.value: {
                "name": agent.role,
                "goal": agent.goal,
                "backstory": agent.backstory[:100] + "..." if len(agent.backstory) > 100 else agent.backstory,
                "usage_count": self.performance_metrics["agent_usage"][role.value]
            }
            for role, agent in self.agents.items()
        }
    
    async def process_complex_request(self, user_message: str, agent_role: AgentRole, user_id: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Processa requisição complexa (compatibilidade com strategy_implementations)"""
        try:
            # Garantir que CrewAI está carregado
            self._ensure_crewai_loaded()
            
            # Converter para formato esperado pelo process_message
            result = self.process_message(
                message=user_message,
                user_phone=user_id,
                context=context_data
            )
            
            return {
                "response": result.get("response", ""),
                "intent": result.get("intent", "geral"),
                "confidence": 0.9,  # Valor padrão
                "interactive_buttons": None,
                "suggested_actions": []
            }
            
        except Exception as e:
            logger.error(f"Erro em process_complex_request: {str(e)}")
            return {
                "response": "Desculpe, houve um problema interno. Nossa equipe foi notificada.",
                "intent": "error",
                "confidence": 0.0,
                "interactive_buttons": None,
                "suggested_actions": []
            }
    
    def get_crew_analytics(self) -> Dict[str, Any]:
        """Retorna analytics do crew (compatibilidade com main.py)"""
        try:
            # Garantir que CrewAI está carregado
            self._ensure_crewai_loaded()
            
            # Combinar métricas de performance e informações dos agentes
            performance = self.get_performance_metrics()
            agents_info = self.get_agent_info()
            
            return {
                "status": "active",
                "performance": performance,
                "agents": agents_info,
                "crewai_loaded": self._crewai_initialized,
                "total_agents": len(self.agents)
            }
            
        except Exception as e:
            logger.error(f"Erro em get_crew_analytics: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "crewai_loaded": False,
                "performance": {},
                "agents": {},
                "total_agents": 0
            }


class WhatsAppCrewManager:
    """Manager para lazy loading do WhatsApp Crew"""
    
    def __init__(self):
        self._crew_instance = None
        self._crew_error = None
    
    def get_crew(self) -> Optional[WhatsAppAgentCrew]:
        """Retorna instância do crew com lazy loading"""
        if self._crew_error:
            return None
            
        if self._crew_instance is None:
            try:
                self._crew_instance = WhatsAppAgentCrew()
                print("✅ WhatsAppAgentCrew inicializado com sucesso!")
            except Exception as e:
                self._crew_error = e
                logger.error(f"Erro ao inicializar WhatsAppAgentCrew: {str(e)}")
                print(f"❌ Falha ao inicializar WhatsAppAgentCrew: {str(e)}")
                return None
        
        return self._crew_instance
    
    def is_available(self) -> bool:
        """Verifica se o crew está disponível"""
        return self._crew_error is None
    
    def get_error(self) -> Optional[Exception]:
        """Retorna o erro de inicialização, se houver"""
        return self._crew_error
    
    # Métodos de compatibilidade para usar como se fosse o crew diretamente
    def process_message(self, message: str, user_phone: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Compatibilidade: process_message"""
        crew = self.get_crew()
        if crew is None:
            return {
                "response": "Sistema de agentes temporariamente indisponível. Redirecionando para atendimento manual.",
                "agent_used": "fallback",
                "intent": "error",
                "processing_time": 0.0,
                "status": "fallback",
                "error": "CrewAI não disponível"
            }
        return crew.process_message(message, user_phone, context)
    
    async def process_complex_request(self, user_message: str, agent_role: AgentRole, user_id: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Compatibilidade: process_complex_request"""
        crew = self.get_crew()
        if crew is None:
            return {
                "response": "Sistema de agentes temporariamente indisponível. Redirecionando para atendimento manual.",
                "intent": "error",
                "confidence": 0.0,
                "interactive_buttons": None,
                "suggested_actions": []
            }
        return await crew.process_complex_request(user_message, agent_role, user_id, context_data)
    
    def get_crew_analytics(self) -> Dict[str, Any]:
        """Compatibilidade: get_crew_analytics"""
        crew = self.get_crew()
        if crew is None:
            return {
                "status": "unavailable",
                "error": str(self._crew_error) if self._crew_error else "CrewAI não inicializado",
                "crewai_loaded": False,
                "performance": {},
                "agents": {},
                "total_agents": 0
            }
        return crew.get_crew_analytics()


# Manager global para lazy loading
_crew_manager = WhatsAppCrewManager()

def get_whatsapp_crew() -> Optional[WhatsAppAgentCrew]:
    """Função para obter a instância do crew de forma segura"""
    return _crew_manager.get_crew()

def is_crewai_available() -> bool:
    """Verifica se o CrewAI está disponível"""
    return _crew_manager.is_available()

# Compatibilidade com código existente
whatsapp_crew = _crew_manager  # Agora é o manager, não a instância direta
