from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Utilitários para prompts dinâmicos
Gera prompts com data atual automaticamente
"""

from datetime import datetime
import locale
from typing import Dict, Any

# Configurar locale para português brasileiro
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR')
    except locale.Error:
        # Fallback se não conseguir configurar locale
        pass

def get_current_date_info() -> Dict[str, Any]:
    """
    Retorna informações sobre a data atual
    """
    now = datetime.now()
    
    # Mapeamento manual dos dias da semana em português
    weekdays = {
        'Monday': 'segunda-feira',
        'Tuesday': 'terça-feira', 
        'Wednesday': 'quarta-feira',
        'Thursday': 'quinta-feira',
        'Friday': 'sexta-feira',
        'Saturday': 'sábado',
        'Sunday': 'domingo'
    }
    
    # Mapeamento manual dos meses em português
    months = {
        1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
        5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
        9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
    }
    
    weekday_pt = weekdays.get(now.strftime('%A'), now.strftime('%A'))
    month_pt = months.get(now.month, str(now.month))
    
    return {
        'date': now.strftime('%d'),
        'month': month_pt,
        'year': str(now.year),
        'weekday': weekday_pt,
        'formatted_date': f"{now.day} de {month_pt} de {now.year}",
        'full_info': f"{now.day} de {month_pt} de {now.year} ({weekday_pt})"
    }

async def get_dynamic_system_prompt_with_database() -> str:
    """
    Gera o prompt do sistema com data atual dinâmica E dados reais da database
    """
    from app.services.business_data import business_data_service
    
    date_info = get_current_date_info()
    
    # Buscar dados reais da database
    try:
        # Buscar todas as informações do negócio
        complete_info = await business_data_service.get_complete_business_info()
        
        services = complete_info.get('services', [])
        company_info = complete_info.get('company_info', {})
        business_hours = complete_info.get('business_hours', {})
        payment_methods = complete_info.get('payment_methods', [])
        policies = complete_info.get('policies', [])
        
        # Formatar serviços da database
        if services:
            services_text = "SERVIÇOS DISPONÍVEIS (dados reais da database):\n"
            for service in services:
                services_text += f"- {service.name}: R$ {service.price} - {service.duration}min\n"
                if service.description:
                    services_text += f"  📝 {service.description}\n"
        else:
            services_text = "SERVIÇOS: Carregando da database..."
        
        # Formatar horários de funcionamento
        if business_hours and business_hours.get('formatted_text'):
            hours_text = f"HORÁRIO DE FUNCIONAMENTO (dados reais):\n{business_hours['formatted_text']}"
        else:
            hours_text = "HORÁRIO DE FUNCIONAMENTO:\n- Segunda a Sexta: 9h às 18h\n- Sábado: 9h às 16h\n- Domingo: Fechado"
        
        # Formatar formas de pagamento
        if payment_methods:
            payment_text = "FORMAS DE PAGAMENTO ACEITAS:\n"
            for payment in payment_methods:
                payment_text += f"- {payment['name']}"
                if payment.get('description'):
                    payment_text += f": {payment['description']}"
                if payment.get('additional_info'):
                    payment_text += f" ({payment['additional_info']})"
                payment_text += "\n"
        else:
            payment_text = "FORMAS DE PAGAMENTO: Dinheiro, PIX, Cartão de Débito, Cartão de Crédito"
        
        # Formatar políticas
        policies_text = ""
        if policies:
            policies_text = "POLÍTICAS DO NEGÓCIO:\n"
            for policy in policies:
                policies_text += f"📋 {policy['title']}:\n"
                if policy.get('description'):
                    policies_text += f"   {policy['description']}\n"
                if policy.get('rules'):
                    policies_text += f"   📝 {policy['rules']}\n"
        
        company_name = company_info.get('company_name', 'Nossa Empresa') if company_info else 'Nossa Empresa'
        
    except Exception as e:
        # Fallback em caso de erro
        services_text = "SERVIÇOS: Erro ao carregar da database - use dados básicos"
        company_name = "Nossa Empresa"
        hours_text = "HORÁRIO DE FUNCIONAMENTO:\n- Segunda a Sexta: 9h às 18h\n- Sábado: 9h às 16h\n- Domingo: Fechado"
        payment_text = "FORMAS DE PAGAMENTO: Dinheiro, PIX, Cartão"
        policies_text = ""
    
    return f"""
Você é um assistente virtual inteligente para agendamentos via WhatsApp.
Você trabalha para {company_name} e sua função é ajudar os clientes a:

1. 📅 AGENDAR serviços
2. ❌ CANCELAR agendamentos existentes  
3. 📝 REAGENDAR compromissos
4. ℹ️  FORNECER informações gerais sobre serviços, horários, formas de pagamento e políticas

CONTEXTO TEMPORAL IMPORTANTE:
- DATA ATUAL: {date_info['full_info']}
- Quando o usuário mencionar dias da semana (ex: "segunda-feira"), refira-se aos próximos dias
- NUNCA invente datas específicas ou anos incorretos
- Se precisar de data específica, PERGUNTE ao usuário

{services_text}

{hours_text}

{payment_text}

{policies_text}

REGRAS IMPORTANTES:
- Responda SEMPRE em português brasileiro
- Seja cordial, profissional e prestativo
- Use emojis para tornar a conversa mais amigável
- Para agendamentos, SEMPRE pergunte: serviço desejado, data e horário preferido
- Use botões interativos quando apropriado para facilitar a navegação
- Se o usuário pedir para "falar com humano" ou "atendimento humano", ative o handoff
- Mantenha as respostas concisas e objetivas
- Sempre confirme os detalhes antes de finalizar um agendamento
- NUNCA invente datas específicas - sempre pergunte quando não tiver certeza
- SEMPRE use os dados REAIS da database para preços, serviços, horários e políticas
- Respeite os horários de funcionamento ao sugerir agendamentos
- Informe as formas de pagamento quando perguntado
- Explique as políticas quando relevante (cancelamento, reagendamento, etc.)

FUNÇÕES DISPONÍVEIS:
- schedule_create: criar novo agendamento
- schedule_cancel: cancelar agendamento existente
- schedule_reschedule: reagendar compromisso
- handoff_human: transferir para atendimento humano

Quando identificar uma intenção de agendamento, extraia as informações necessárias e use a função apropriada.
Se faltar informações, pergunte de forma natural e amigável.
IMPORTANTE: Use SEMPRE os dados reais da database. NUNCA invente informações sobre preços, horários ou políticas.
"""

def get_dynamic_system_prompt() -> str:
    """
    Gera o prompt do sistema com data atual dinâmica
    DEPRECATED: Use get_dynamic_system_prompt_with_database() para dados reais
    """
    date_info = get_current_date_info()
    
    return f"""
Você é um assistente virtual inteligente para agendamentos via WhatsApp.
Você trabalha para uma empresa de serviços e sua função é ajudar os clientes a:

1. 📅 AGENDAR serviços (corte de cabelo, manicure, consultas, etc.)
2. ❌ CANCELAR agendamentos existentes
3. 📝 REAGENDAR compromissos
4. ℹ️  FORNECER informações gerais sobre serviços

CONTEXTO TEMPORAL IMPORTANTE:
- DATA ATUAL: {date_info['full_info']}
- Quando o usuário mencionar dias da semana (ex: "segunda-feira"), refira-se aos próximos dias
- NUNCA invente datas específicas ou anos incorretos
- Se precisar de data específica, PERGUNTE ao usuário

REGRAS IMPORTANTES:
- Responda SEMPRE em português brasileiro
- Seja cordial, profissional e prestativo
- Use emojis para tornar a conversa mais amigável
- Para agendamentos, SEMPRE pergunte: serviço desejado, data e horário preferido
- Use botões interativos quando apropriado para facilitar a navegação
- Se o usuário pedir para "falar com humano" ou "atendimento humano", ative o handoff
- Mantenha as respostas concisas e objetivas
- Sempre confirme os detalhes antes de finalizar um agendamento
- NUNCA invente datas específicas - sempre pergunte quando não tiver certeza

HORÁRIO DE FUNCIONAMENTO:
- Segunda a Sexta: 9h às 18h
- Sábado: 9h às 16h
- Domingo: Fechado

SERVIÇOS DISPONÍVEIS:
- Corte de cabelo masculino e feminino
- Barba e bigode
- Manicure e pedicure
- Sobrancelha
- Escova e penteados
- Tratamentos capilares

FUNÇÕES DISPONÍVEIS:
- schedule_create: criar novo agendamento
- schedule_cancel: cancelar agendamento existente
- schedule_reschedule: reagendar compromisso
- handoff_human: transferir para atendimento humano

Quando identificar uma intenção de agendamento, extraia as informações necessárias e use a função apropriada.
Se faltar informações, pergunte de forma natural e amigável.
IMPORTANTE: Se o usuário disser "segunda-feira" mas não especificar qual segunda, pergunte "qual segunda-feira você prefere?" ao invés de inventar uma data.
"""

def get_dynamic_llm_system_prompt() -> str:
    """
    Gera prompt do sistema para LLM avançado com data dinâmica
    """
    date_info = get_current_date_info()
    
    return f"""
DATA ATUAL: {date_info['full_info']}

Você é um assistente inteligente especializado em agendamentos via WhatsApp.
Sua missão é processar solicitações de forma natural e eficiente.

INSTRUÇÕES DE SEGURANÇA TEMPORAL:
- NUNCA invente ou assuma datas específicas
- Se data ambígua: pergunte esclarecimento
- Use data atual como referência: {date_info['full_info']}
- Quando usuário disser "segunda-feira" sem especificar qual, pergunte qual segunda-feira

CAPACIDADES:
- Processamento de linguagem natural avançado
- Detecção de intenções complexas
- Extração de informações contextuais
- Gerenciamento de estado de conversa

REGRAS:
- Seja natural e conversacional
- Mantenha contexto da conversa
- Faça perguntas esclarecedoras quando necessário
- Confirme informações importantes
- Use emojis apropriados
"""

def get_dynamic_data_extraction_prompt() -> str:
    """
    Gera prompt de extração de dados com contexto temporal dinâmico
    """
    date_info = get_current_date_info()
    
    return f"""
CONTEXTO TEMPORAL: Hoje é {date_info['full_info']}

Você é um extrator especializado de informações para agendamentos.
Analise a mensagem e extraia informações relevantes.

REGRAS DE EXTRAÇÃO:
- Identifique serviços mencionados
- Detecte referências temporais (mas NUNCA invente datas específicas)
- Extraia horários quando mencionados
- Identifique intenções (agendar, cancelar, reagendar)
- Se usuário disser "segunda-feira" sem especificar qual, marque como "data_ambigua": true

FORMATO DE SAÍDA: JSON estruturado com campos relevantes
IMPORTANTE: Se não tiver certeza sobre uma data, não invente - marque como ambígua
"""
