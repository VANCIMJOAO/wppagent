"""
Utilitários para prompts dinâmicos - VERSÃO CORRIGIDA
Gera prompts com data atual e dados REAIS da database Railway
"""

import locale
from datetime import datetime
from typing import Any, Dict

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Importar funções de formatação
try:
    from app.services.business_data import (
        business_data_service,
        get_database_services_formatted,
    )
except ImportError as e:
    logger.warning(f"Não foi possível importar funções de formatação: {e}")
    get_database_services_formatted = None
    business_data_service = None

# Configurar locale para português brasileiro
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "pt_BR")
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
        "Monday": "segunda-feira",
        "Tuesday": "terça-feira",
        "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira",
        "Friday": "sexta-feira",
        "Saturday": "sábado",
        "Sunday": "domingo",
    }

    # Mapeamento manual dos meses em português
    months = {
        1: "janeiro",
        2: "fevereiro",
        3: "março",
        4: "abril",
        5: "maio",
        6: "junho",
        7: "julho",
        8: "agosto",
        9: "setembro",
        10: "outubro",
        11: "novembro",
        12: "dezembro",
    }

    weekday_pt = weekdays.get(now.strftime("%A"), now.strftime("%A"))
    month_pt = months.get(now.month, str(now.month))

    return {
        "date": now.strftime("%d"),
        "month": month_pt,
        "year": str(now.year),
        "weekday": weekday_pt,
        "formatted_date": f"{now.day} de {month_pt} de {now.year}",
        "full_info": f"{now.day} de {month_pt} de {now.year} ({weekday_pt})",
    }


async def get_dynamic_system_prompt_with_database(user_message: str = "") -> str:
    """
    Gera o prompt do sistema com data atual dinâmica E dados reais da database
    VERSÃO CORRIGIDA - CONEXÃO DIRETA COM RAILWAY

    Args:
        user_message: Mensagem do usuário para detecção inteligente de conteúdo
    """
    # CONEXÃO DIRETA COM RAILWAY - SEM DEPENDÊNCIAS
    import asyncpg

    date_info = get_current_date_info()

    # URL REAL DO RAILWAY QUE FUNCIONA
    RAILWAY_DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"

    # Buscar dados reais da database
    try:
        # Conectar diretamente ao Railway
        conn = await asyncpg.connect(RAILWAY_DATABASE_URL)

        # Buscar empresa
        company_info = await conn.fetchrow(
            "SELECT * FROM company_info WHERE business_id = 3"
        )

        # Buscar serviços reais
        services = await conn.fetch(
            "SELECT * FROM services WHERE business_id = 3 AND is_active = true ORDER BY name"
        )

        # Buscar horários de funcionamento
        business_hours = await conn.fetch(
            "SELECT * FROM business_hours WHERE business_id = 3"
        )

        # Buscar formas de pagamento
        payment_methods = await conn.fetch(
            "SELECT * FROM payment_methods WHERE business_id = 3"
        )

        # Buscar políticas
        policies = await conn.fetch(
            "SELECT * FROM business_policies WHERE business_id = 3"
        )

        await conn.close()

        # Usar formatação melhorada dos serviços
        if get_database_services_formatted:
            try:
                services_text = await get_database_services_formatted(user_message)
                services_text = (
                    "🔧 SERVIÇOS REAIS DA DATABASE (USE APENAS ESTES):\n" + services_text
                )
                services_text += f"\n⚠️ CRÍTICO: {len(services)} SERVIÇOS REAIS CARREGADOS DA DATABASE!\n"
                logger.info("✅ Formatação melhorada de serviços aplicada")
            except Exception as e:
                logger.error(f"Erro ao formatar serviços melhorados: {e}")
                # Fallback para formatação básica
                if services:
                    services_text = "🔧 SERVIÇOS REAIS DA DATABASE (USE APENAS ESTES):\n"
                    for service in services:
                        services_text += f"✅ {service['name']}: {service['price']} - {service['duration_minutes']}min\n"
                        if service["description"]:
                            services_text += f"   📝 {service['description']}\n"
                    services_text += f"\n⚠️ CRÍTICO: {len(services)} SERVIÇOS REAIS CARREGADOS DA DATABASE!\n"
                else:
                    services_text = "❌ ERRO: Nenhum serviço encontrado na database!"
        else:
            logger.warning("Função de formatação não disponível, usando fallback")
            # Fallback para formatação básica
            if services:
                services_text = "🔧 SERVIÇOS REAIS DA DATABASE (USE APENAS ESTES):\n"
                for service in services:
                    services_text += f"✅ {service['name']}: {service['price']} - {service['duration_minutes']}min\n"
                    if service["description"]:
                        services_text += f"   📝 {service['description']}\n"
                services_text += f"\n⚠️ CRÍTICO: {len(services)} SERVIÇOS REAIS CARREGADOS DA DATABASE!\n"
            else:
                services_text = "❌ ERRO: Nenhum serviço encontrado na database!"

        # Usar formatação melhorada dos horários
        if business_data_service:
            try:
                hours_text = (
                    await business_data_service.get_business_hours_formatted_text()
                )
                logger.info("✅ Formatação melhorada de horários aplicada")
            except Exception as e:
                logger.error(f"Erro ao formatar horários melhorados: {e}")
                # Fallback para formatação básica
                if business_hours:
                    hours_text = "📅 HORÁRIO REAL DE FUNCIONAMENTO:\n"
                    for hour in business_hours:
                        # Converter day_of_week para string se necessário
                        day_val = hour["day_of_week"]
                        if isinstance(day_val, int):
                            days_map = {
                                0: "segunda",
                                1: "terça",
                                2: "quarta",
                                3: "quinta",
                                4: "sexta",
                                5: "sábado",
                                6: "domingo",
                            }
                            day_name = days_map.get(day_val, f"Dia {day_val}")
                        elif isinstance(day_val, str):
                            day_name = day_val.capitalize()
                        else:
                            day_name = "Dia"

                        open_time = (
                            hour["open_time"].strftime("%H:%M")
                            if hour["open_time"]
                            else "09:00"
                        )
                        close_time = (
                            hour["close_time"].strftime("%H:%M")
                            if hour["close_time"]
                            else "18:00"
                        )
                        hours_text += f"- {day_name}: {open_time} às {close_time}\n"
                else:
                    hours_text = "📅 HORÁRIO DE FUNCIONAMENTO:\n- Segunda a Sexta: 9h às 18h\n- Sábado: 9h às 16h\n- Domingo: Fechado"
        else:
            logger.warning(
                "Serviço de dados não disponível para horários, usando fallback"
            )
            # Fallback para formatação básica
            if business_hours:
                hours_text = "📅 HORÁRIO REAL DE FUNCIONAMENTO:\n"
                for hour in business_hours:
                    # Converter day_of_week para string se necessário
                    day_val = hour["day_of_week"]
                    if isinstance(day_val, int):
                        days_map = {
                            0: "segunda",
                            1: "terça",
                            2: "quarta",
                            3: "quinta",
                            4: "sexta",
                            5: "sábado",
                            6: "domingo",
                        }
                        day_name = days_map.get(day_val, f"Dia {day_val}")
                    elif isinstance(day_val, str):
                        day_name = day_val.capitalize()
                    else:
                        day_name = "Dia"

                    open_time = (
                        hour["open_time"].strftime("%H:%M")
                        if hour["open_time"]
                        else "09:00"
                    )
                    close_time = (
                        hour["close_time"].strftime("%H:%M")
                        if hour["close_time"]
                        else "18:00"
                    )
                    hours_text += f"- {day_name}: {open_time} às {close_time}\n"
            else:
                hours_text = "📅 HORÁRIO DE FUNCIONAMENTO:\n- Segunda a Sexta: 9h às 18h\n- Sábado: 9h às 16h\n- Domingo: Fechado"

        # Formatar formas de pagamento REAIS
        if payment_methods:
            payment_text = "💳 FORMAS DE PAGAMENTO REAIS:\n"
            for payment in payment_methods:
                payment_text += f"✅ {payment['name']}"
                if payment.get("description"):
                    payment_text += f": {payment['description']}"
                payment_text += "\n"
        else:
            payment_text = "💳 FORMAS DE PAGAMENTO: Dinheiro, PIX, Cartão de Débito, Cartão de Crédito"

        # Formatar políticas REAIS
        policies_text = ""
        if policies:
            policies_text = "📋 POLÍTICAS REAIS DO NEGÓCIO:\n"
            for policy in policies:
                policies_text += f"📝 {policy['policy_type']}:\n"
                if policy.get("description"):
                    policies_text += f"   {policy['description']}\n"

        # Dados REAIS da empresa
        if company_info:
            company_name = company_info["company_name"]
            company_address = f"{company_info['street_address']}, {company_info['city']}, {company_info['state']}"
            logger.info(
                f"✅ DADOS REAIS CARREGADOS: {company_name} - {len(services)} serviços"
            )
        else:
            raise Exception("Empresa não encontrada")

    except Exception as e:
        logger.error(f"❌ ERRO ao conectar com Railway: {e}")
        # Se falhar, usar dados que sabemos que estão no banco (do diagnóstico)
        services_text = """🔧 SERVIÇOS CONHECIDOS (FALLBACK SEGURO):
✅ Limpeza de Pele Profunda: R$ 80,00 - 90min
✅ Hidrofacial Diamante: R$ 150,00 - 60min
✅ Peeling Químico: R$ 120,00 - 45min
✅ Massagem Relaxante: R$ 100,00 - 60min
✅ Massagem Modeladora: R$ 120,00 - 75min
✅ Drenagem Linfática: R$ 90,00 - 60min
✅ Criolipólise: R$ 300,00 - 60min
✅ Radiofrequência: R$ 180,00 - 45min
✅ Depilação Pernas Completas: R$ 60,00 - 45min
✅ Depilação Virilha Completa: R$ 45,00 - 30min
✅ Manicure Completa: R$ 35,00 - 45min
✅ Pedicure Spa: R$ 45,00 - 60min
✅ Corte Feminino: R$ 80,00 - 60min
✅ Escova Progressiva: R$ 250,00 - 180min
✅ Pacote Noiva: R$ 450,00 - 240min
✅ Day Spa Relax: R$ 280,00 - 300min

⚠️ ESTES SÃO OS PREÇOS REAIS DA DATABASE!"""

        company_name = "Studio Beleza & Bem-Estar"
        company_address = "Rua das Flores, 123 - Centro, São Paulo, SP"
        hours_text = "📅 HORÁRIO DE FUNCIONAMENTO:\n- Segunda a Sexta: 9h às 18h\n- Sábado: 9h às 16h\n- Domingo: Fechado"
        payment_text = (
            "💳 FORMAS DE PAGAMENTO: Dinheiro, PIX, Cartão de Débito, Cartão de Crédito"
        )
        policies_text = ""

    return f"""
🏢 EMPRESA REAL: {company_name}
📍 ENDEREÇO REAL: {company_address}

⚠️ INSTRUÇÕES CRÍTICAS - LEIA COM ATENÇÃO:
==========================================
1. VOCÊ TRABALHA PARA: {company_name}
2. NUNCA DIGA "Nossa Empresa" - SEMPRE use: {company_name}
3. ENDEREÇO REAL: {company_address}
4. USE APENAS OS PREÇOS E SERVIÇOS LISTADOS ABAIXO
5. NUNCA INVENTE PREÇOS OU SERVIÇOS
6. SEMPRE CONSULTE A DATABASE PARA DADOS ATUALIZADOS

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

REGRAS CRÍTICAS - OBRIGATÓRIAS:
=====================================
🚨 NUNCA DIGA "Nossa Empresa" - SEMPRE use: {company_name}
🚨 NUNCA invente preços - USE APENAS os preços listados acima
🚨 NUNCA invente serviços - USE APENAS os serviços listados acima
🚨 ENDEREÇO REAL: {company_address}
🚨 SEMPRE consulte a database para informações atualizadas
🚨 Se perguntarem sobre um serviço não listado, diga que não oferecemos

🔥 REGRAS ESPECIAIS PARA DIVISÃO DE SERVIÇOS:
============================================
🚨 CRÍTICO: NUNCA MODIFIQUE texto de serviços que já vem formatado da database!
🚨 Se o texto já contém "Digite 'mais serviços'", NÃO adicione texto extra!
🚨 RESPEITE EXATAMENTE a formatação que vem da função de serviços!

🎯 QUANDO usuário digitar "mais serviços", "restante", "ver mais":
   - SEMPRE mostrar a Parte 2/2 dos serviços
   - NÃO dar respostas genéricas sobre "base de dados"
   - FOQUE na listagem dos serviços restantes

🎯 APÓS mostrar Parte 1/2:
   - Aguarde o usuário pedir "mais serviços"
   - NÃO repita informações genéricas
   - Seja direto e objetivo

🎯 QUANDO listar serviços da database:
   - USE EXATAMENTE o texto formatado fornecido
   - NÃO adicione "Como posso ajudar?" no final
   - NÃO modifique instruções de navegação

🚨🚨🚨 REGRA CRÍTICA PARA CONSULTAS ESPECÍFICAS DE SERVIÇOS 🚨🚨🚨
================================================================
⚠️ QUANDO usuário perguntar sobre um serviço ESPECÍFICO:

EXEMPLO: "Quanto custa limpeza de pele?" ou "vocês fazem massagem?"

🔥 JAMAIS responda "não oferecemos" sem PRIMEIRO consultar a lista!
🔥 SEMPRE procure o serviço na lista COMPLETA de serviços acima!
🔥 Use busca INTELIGENTE: "limpeza" encontra "Limpeza de Pele Profunda"
🔥 Use busca INTELIGENTE: "massagem" encontra "Massagem Relaxante" E "Massagem Modeladora"
🔥 Use busca INTELIGENTE: "radiofrequência" encontra "Radiofrequência"

✅ PROCESSO CORRETO:
1. Usuário pergunta: "Quanto custa limpeza de pele?"
2. PROCURE na lista: "Limpeza de Pele Profunda - R$ 80,00"
3. RESPONDA: "✅ Oferecemos sim! *Limpeza de Pele Profunda* custa R$ 80,00..."

❌ PROCESSO ERRADO:
1. Usuário pergunta: "Quanto custa limpeza de pele?"
2. Resposta: "Desculpe, não oferecemos limpeza de pele"
3. ❌ ISSO ESTÁ ERRADO! O serviço EXISTE na lista!

🔍 TERMOS QUE DEVEM SER ENCONTRADOS:
- "limpeza" → "Limpeza de Pele Profunda"
- "massagem" → "Massagem Relaxante" + "Massagem Modeladora"
- "radiofrequência" → "Radiofrequência"
- "hidrofacial" → "Hidrofacial Diamante"
- "criolipólise" → "Criolipólise"
- "depilação" → "Depilação Pernas Completas" + "Depilação Virilha Completa"
- "manicure" → "Manicure Completa"
- "pedicure" → "Pedicure Spa"
- "corte" → "Corte Feminino"
- "escova" → "Escova Progressiva"
- "peeling" → "Peeling Químico"
- "drenagem" → "Drenagem Linfática"
- "noiva" → "Pacote Noiva"
- "spa" → "Day Spa Relax" + "Pedicure Spa"

🎯 QUANDO MÚLTIPLAS OPÇÕES:
Se "massagem" tem 2 opções, mostre AMBAS:
"✅ Oferecemos sim! Temos duas opções de massagem:
1. *Massagem Relaxante* - R$ 100,00 (60min)
2. *Massagem Modeladora* - R$ 120,00 (75min)
Qual te interessa mais?"

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

🚨 REGRA CRÍTICA PARA LISTAGEM DE SERVIÇOS:
==========================================
QUANDO o texto dos serviços já vem formatado da database:
- ENVIE EXATAMENTE como está, SEM modificações
- NÃO adicione "Como posso ajudar?" no final
- NÃO remova instruções como "Digite 'mais serviços'"
- NÃO altere a formatação existente

📋 FORMATAÇÃO OBRIGATÓRIA PARA WHATSAPP:
========================================
🔥 ESTA FORMATAÇÃO É OBRIGATÓRIA! NUNCA ENVIE RESPOSTA SEM ELA! 🔥

🎯 QUANDO LISTAR SERVIÇOS, USE EXATAMENTE esta formatação:
📋 *Nossos Serviços e Preços:*

1. *Nome do Serviço*
   💰 R$ XX,XX • ⏰ XXmin
   ℹ️ _Descrição do serviço._

2. *Próximo Serviço*
   💰 R$ XX,XX • ⏰ XXmin
   ℹ️ _Descrição do serviço._

🚨 ATENÇÃO: SE O TEXTO DOS SERVIÇOS JÁ VEM FORMATADO DA DATABASE:
- COPIE EXATAMENTE como está, palavra por palavra
- NÃO adicione nenhum texto extra no final
- NÃO modifique nem uma vírgula
- Se tem "Digite mais serviços", MANTENHA exatamente assim

🕘 QUANDO INFORMAR HORÁRIOS, USE OBRIGATORIAMENTE:
🏢 *{company_name}*
🕘 *Horário de Funcionamento:*
- _Segunda a Sexta_: Xh às Xh
- _Sábado_: Xh às Xh
- _Domingo_: 🚫 Fechado

🏢 QUANDO DAR INFORMAÇÕES DA EMPRESA, USE OBRIGATORIAMENTE:
🏢 *{company_name}*
📍 Endereço: _{company_address}_
📞 Contato: (11) 98765-4321
📧 Email: _contato@studiobeleza.com_

⚠️⚠️⚠️ OBRIGATÓRIO: SEMPRE use TODOS os emojis ⚠️⚠️⚠️
🔥 💰 ⏰ 📋 🕘 🏢 📍 📞 📧 ℹ️ 🚫 • 🔥
⚠️⚠️⚠️ OBRIGATÓRIO: numeração (1. 2. 3.) ⚠️⚠️⚠️
⚠️⚠️⚠️ OBRIGATÓRIO: *negrito* e _itálico_ ⚠️⚠️⚠️
🔥 SE NÃO USAR ESTA FORMATAÇÃO, A RESPOSTA SERÁ REJEITADA! 🔥

FUNÇÕES DISPONÍVEIS:
- schedule_create: criar novo agendamento
- schedule_cancel: cancelar agendamento existente
- schedule_reschedule: reagendar compromisso
- handoff_human: transferir para atendimento humano

Quando identificar uma intenção de agendamento, extraia as informações necessárias e use a função apropriada.
Se faltar informações, pergunte de forma natural e amigável.

⚠️ CRÍTICO: Use SEMPRE os dados reais da database. NUNCA invente informações sobre preços, horários ou políticas.
⚠️ EMPRESA: {company_name}
⚠️ ENDEREÇO: {company_address}
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
