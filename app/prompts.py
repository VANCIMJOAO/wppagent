"""
Prompts personalizáveis para o sistema
Edite este arquivo para modificar o comportamento do bot
"""

from app.utils.dynamic_prompts import get_dynamic_system_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)
# Função para obter prompt principal do sistema com dados da database
async def get_system_prompt_with_database() -> str:
    """
    Retorna o prompt do sistema com dados reais da database
    """
    from app.utils.dynamic_prompts import get_dynamic_system_prompt_with_database
    return await get_dynamic_system_prompt_with_database()

def get_system_prompt() -> str:
    """
    Retorna o prompt do sistema com data atual dinâmica (LEGACY)
    RECOMENDADO: Use get_system_prompt_with_database() para dados reais
    """
    return get_dynamic_system_prompt()

# Prompt estático (mantido para compatibilidade, mas recomenda-se usar get_system_prompt())
SYSTEM_PROMPT = get_dynamic_system_prompt()

# Mensagens de saudação
GREETING_MESSAGES = [
    "Olá! 👋 Bem-vindo(a)! Como posso ajudar você hoje?",
    "Oi! 😊 Em que posso ser útil?",
    "Olá! Sou seu assistente virtual. Como posso ajudar?",
]

# Mensagens de agendamento confirmado
APPOINTMENT_CONFIRMED_MESSAGES = [
    "✅ Perfeito! Seu agendamento foi confirmado com sucesso!",
    "🎉 Agendamento confirmado! Estamos te esperando!",
    "✅ Tudo certo! Agendamento realizado com sucesso!",
]

# Mensagens de cancelamento
APPOINTMENT_CANCELLED_MESSAGES = [
    "❌ Agendamento cancelado com sucesso. Esperamos você em uma próxima oportunidade!",
    "✅ Cancelamento realizado. Obrigado por avisar!",
    "❌ Agendamento cancelado. Até uma próxima vez!",
]

# Mensagens de handoff para humano
HANDOFF_MESSAGES = [
    "👤 Entendi! Você será atendido por um de nossos especialistas em breve. Aguarde que alguém entrará em contato!",
    "👨‍💼 Perfeito! Vou transferir você para nossa equipe. Alguém entrará em contato em instantes!",
    "👩‍💼 Sem problemas! Um atendente humano cuidará do seu caso. Aguarde só um momento!",
]

# Mensagens de erro
ERROR_MESSAGES = [
    "Ops! Algo deu errado. Pode tentar novamente, por favor?",
    "Desculpe, ocorreu um erro. Tente novamente em alguns instantes.",
    "Hmm, parece que houve um probleminha. Que tal tentar de novo?",
]

# Mensagens quando não entende
CONFUSION_MESSAGES = [
    "Desculpe, não entendi muito bem. Pode reformular sua pergunta?",
    "Hmm, não consegui compreender. Pode explicar de outra forma?",
    "Não entendi direito. Pode ser mais específico?",
]

# Botões padrão para diferentes situações
DEFAULT_BUTTONS = {
    "main_menu": [
        {"id": "new_schedule", "title": "📅 Novo agendamento"},
        {"id": "check_schedule", "title": "📋 Meus agendamentos"},
        {"id": "human_support", "title": "👤 Falar com humano"}
    ],
    
    "schedule_confirmation": [
        {"id": "confirm_schedule", "title": "✅ Confirmar"},
        {"id": "change_schedule", "title": "📅 Alterar horário"},
        {"id": "cancel_action", "title": "❌ Cancelar"}
    ],
    
    "schedule_actions": [
        {"id": "reschedule", "title": "📅 Reagendar"},
        {"id": "cancel_appointment", "title": "❌ Cancelar"},
        {"id": "confirm_appointment", "title": "✅ Confirmar"}
    ]
}

# Horários disponíveis para agendamento
AVAILABLE_TIMES = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
    "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"
]

# COMPATIBILIDADE: Mantido para código legado que ainda importa SERVICES
# IMPORTANTE: Para obter serviços reais da database, use:
# from app.services.business_data import get_database_services
# services = await get_database_services()

# Função para obter SERVICES da database (compatibilidade)
def get_services_from_database():
    """Retorna serviços da database no formato legado"""
    try:
        import asyncio
        from app.services.business_data import business_data_service
        
        services = asyncio.run(business_data_service.get_services_dict())
        return services
    except Exception as e:
        # Fallback se não conseguir acessar database
        return {
            "corte masculino": 30,
            "corte feminino": 45,
            "barba": 20,
            "manicure": 60
        }

# SERVICES para compatibilidade (será carregado da database quando possível)
try:
    SERVICES = get_services_from_database()
except:
    # Fallback se database não estiver disponível durante import
    SERVICES = {
        "corte masculino": 30,
        "corte feminino": 45,
        "barba": 20,
        "manicure": 60,
        "pedicure": 45,
        "sobrancelha": 15,
        "escova": 30,
        "penteado": 60,
        "tratamento capilar": 90
    }

# Mensagens de confirmação por serviço
SERVICE_CONFIRMATIONS = {
    "corte masculino": "✂️ Corte masculino agendado!",
    "corte feminino": "✂️ Corte feminino agendado!", 
    "barba": "🧔 Serviço de barba agendado!",
    "manicure": "💅 Manicure agendada!",
    "pedicure": "🦶 Pedicure agendado!",
    "sobrancelha": "👁️ Design de sobrancelha agendado!",
    "escova": "💨 Escova agendada!",
    "penteado": "👸 Penteado agendado!",
    "tratamento capilar": "💆‍♀️ Tratamento capilar agendado!"
}

# Perguntas para coletar informações faltantes
INFORMATION_REQUESTS = {
    "service": "Que tipo de serviço você gostaria de agendar? 🤔",
    "date": "Para que dia você gostaria de agendar? 📅",
    "time": "Que horário seria melhor para você? 🕐",
    "confirmation": "Posso confirmar os detalhes do seu agendamento? ✅"
}
