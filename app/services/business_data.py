"""
Serviço de Dados de Negócio - Interface com Database
Busca informações reais da database usando asyncpg diretamente
"""

import asyncpg
from typing import List, Dict, Optional
from app.utils.logger import get_logger
import logging

logger = get_logger(__name__)


class ServiceData:
    """Classe simples para representar dados de serviço"""
    def __init__(self, id: int, name: str, price: str, duration: int, description: str = ""):
        self.id = id
        self.name = name
        self.price = price  # Agora é string (ex: "R$ 50,00")
        self.duration = duration
        self.description = description
    
    def __repr__(self):
        return f"ServiceData(name='{self.name}', price='{self.price}', duration={self.duration})"


class BusinessDataService:
    """Serviço para buscar dados reais do negócio da database usando asyncpg"""
    
    def __init__(self, business_id: int = 3):  # Usar business_id = 3 igual ao dynamic_prompts
        self.business_id = business_id
        # URL IDÊNTICA ao comprehensive_bot_test.py
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        self._services_cache = None
        self._company_info_cache = None
        self._business_hours_cache = None
        self._payment_methods_cache = None
        self._policies_cache = None
    
    async def _get_connection(self):
        """Conecta usando asyncpg diretamente - IGUAL AO COMPREHENSIVE_BOT_TEST"""
        try:
            conn = await asyncpg.connect(self.DATABASE_URL)
            return conn
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            raise e
    
    async def get_active_services(self, refresh_cache: bool = False) -> List[ServiceData]:
        """
        Busca serviços ativos da database usando asyncpg
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Lista de objetos ServiceData com nome, preço e duração
        """
        if self._services_cache is None or refresh_cache:
            conn = None
            try:
                conn = await self._get_connection()
                
                # Buscar serviços IGUAL ao dynamic_prompts.py
                services = await conn.fetch("""
                    SELECT * FROM services 
                    WHERE business_id = $1 AND is_active = true 
                    ORDER BY name
                """, self.business_id)
                
                self._services_cache = [
                    ServiceData(
                        id=service['id'],
                        name=service['name'],
                        price=service['price'],
                        duration=service['duration_minutes'],
                        description=service['description'] or ""
                    )
                    for service in services
                ]
                
                logger.info(f"✅ Carregados {len(self._services_cache)} serviços da database")
                
            except Exception as e:
                logger.error(f"❌ Erro ao buscar serviços: {e}")
                self._services_cache = []
            finally:
                if conn:
                    await conn.close()
        
        return self._services_cache or []
    
    async def get_company_info(self, refresh_cache: bool = False) -> Optional[Dict]:
        """
        Busca informações da empresa da database usando asyncpg
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Dicionário com informações da empresa
        """
        if self._company_info_cache is None or refresh_cache:
            conn = None
            try:
                conn = await self._get_connection()
                
                # Buscar informações da empresa IGUAL ao dynamic_prompts.py
                company_info = await conn.fetchrow("""
                    SELECT * FROM company_info WHERE business_id = $1
                """, self.business_id)
                
                if company_info:
                    self._company_info_cache = {
                        "company_name": company_info['company_name'],
                        "slogan": company_info.get('slogan', ''),
                        "about_us": company_info.get('about_us', ''),
                        "street_address": company_info.get('street_address', ''),
                        "city": company_info.get('city', ''),
                        "state": company_info.get('state', ''),
                        "phone": company_info.get('phone', ''),
                        "email": company_info.get('email', ''),
                        "website": company_info.get('website', '')
                    }
                    logger.info("✅ Informações da empresa carregadas")
                else:
                    logger.warning("⚠️ Informações da empresa não encontradas")
                    self._company_info_cache = {}
                    
            except Exception as e:
                logger.error(f"❌ Erro ao buscar informações da empresa: {e}")
                self._company_info_cache = {}
            finally:
                if conn:
                    await conn.close()
        
        return self._company_info_cache
    
    async def get_services_formatted_text(self, user_message: str = "") -> str:
        """
        Retorna texto formatado com serviços e preços da database
        CORREÇÃO: Divisão automática por limite WhatsApp + detecção de "mais serviços"
        
        Args:
            user_message: Mensagem do usuário para detectar se quer parte 2
            
        Returns:
            String formatada com lista de serviços (primeira ou segunda parte)
        """
        services = await self.get_active_services()
        
        if not services:
            return "🔍 No momento não temos serviços cadastrados.\n📞 Entre em contato conosco!"
        
        # 🔥 DETECÇÃO INTELIGENTE: Se usuário pediu "mais serviços", mostrar parte 2
        if "mais serviços" in user_message.lower() or "restante" in user_message.lower():
            return await self.get_services_formatted_text_part2()
        
        # Dividir serviços em duas partes para respeitar limite de 4096 chars
        total_services = len(services)
        mid_point = total_services // 2
        
        text = f"📋 *Nossos Serviços e Preços (Parte 1/2):*\n\n"
        
        for i, service in enumerate(services[:mid_point], 1):
            text += f"{i}. *{service.name}*\n"
            text += f"   💰 {service.price}"
            if service.duration:
                text += f" • ⏰ {service.duration}min"
            text += "\n"
            if service.description:
                text += f"   ℹ️ _{service.description}_\n"
            text += "\n"
        
        text += "\n💬 *Digite mais serviços para ver o restante*"
        
        return text
    
    async def get_services_formatted_text_part2(self) -> str:
        """
        Retorna segunda parte dos serviços formatados
        
        Returns:
            String formatada com lista de serviços (segunda parte)
        """
        services = await self.get_active_services()
        
        if not services:
            return "🔍 Não há mais serviços para mostrar."
        
        total_services = len(services)
        mid_point = total_services // 2
        
        text = f"📋 *Nossos Serviços e Preços (Parte 2/2):*\n\n"
        
        for i, service in enumerate(services[mid_point:], mid_point + 1):
            text += f"{i}. *{service.name}*\n"
            text += f"   💰 {service.price}"
            if service.duration:
                text += f" • ⏰ {service.duration}min"
            text += "\n"
            if service.description:
                text += f"   ℹ️ _{service.description}_\n"
            text += "\n"
        
        text += "\n✅ *Estes são todos os nossos serviços!*\n"
        text += "📞 *Para agendar, me informe:*\n"
        text += "• Qual serviço deseja\n"
        text += "• Data e horário preferido\n"
        text += "• Seu nome completo"
        
        return text
    
    async def get_company_info_formatted_text(self) -> str:
        """
        Retorna informações da empresa formatadas para WhatsApp
        
        Returns:
            String formatada com informações da empresa
        """
        company_info = await self.get_company_info()
        
        if not company_info:
            return "🏢 *Studio Beleza & Bem-Estar*\n📍 Endereço: _Rua das Flores, 123 - Centro, São Paulo, SP_\n📞 Contato: (11) 98765-4321\n📧 Email: _contato@studiobeleza.com_"
        
        text = f"🏢 *{company_info.get('name', 'Studio Beleza & Bem-Estar')}*\n"
        
        if company_info.get('address'):
            text += f"📍 Endereço: _{company_info['address']}_\n"
        
        if company_info.get('phone'):
            text += f"📞 Contato: {company_info['phone']}\n"
        
        if company_info.get('email'):
            text += f"📧 Email: _{company_info['email']}_\n"
        
        if company_info.get('website'):
            text += f"🌐 Site: _{company_info['website']}_\n"
        
        return text.strip()
    
    async def find_service_by_name(self, service_name: str) -> Optional[ServiceData]:
        """
        Busca INTELIGENTE de serviços com sinônimos e palavras-chave flexíveis
        CORREÇÃO CRÍTICA: Resolve problemas de "limpeza de pele", "massagem", "radiofrequência"
        
        Args:
            service_name: Nome ou termo de busca do serviço
            
        Returns:
            Objeto ServiceData ou None se não encontrado
        """
        services = await self.get_active_services()
        
        if not services:
            logger.warning("❌ Nenhum serviço disponível para busca")
            return None
            
        service_name_clean = service_name.lower().strip()
        
        # 🔍 FASE 1: Busca exata primeiro
        for service in services:
            if service.name.lower() == service_name_clean:
                logger.info(f"✅ Encontrado por busca exata: {service.name}")
                return service
        
        # 🔍 FASE 2: Busca parcial (palavra contida no nome)
        for service in services:
            if service_name_clean in service.name.lower():
                logger.info(f"✅ Encontrado por busca parcial: {service.name}")
                return service
        
        # 🔍 FASE 3: Busca por palavras individuais
        search_words = service_name_clean.split()
        for service in services:
            service_words = service.name.lower().split()
            # Se pelo menos uma palavra da busca está no nome do serviço
            if any(word in service.name.lower() for word in search_words):
                logger.info(f"✅ Encontrado por palavra-chave: {service.name} (busca: {search_words})")
                return service
        
        # 🔍 FASE 4: Mapeamento INTELIGENTE de sinônimos e variações
        # ⚠️ CORREÇÃO CRÍTICA: Mapear todos os termos problemáticos identificados
        keywords_map = {
            # PROBLEMAS CRÍTICOS IDENTIFICADOS:
            'limpeza de pele profunda': [
                'limpeza', 'limpeza de pele', 'facial', 'limpeza facial', 
                'limpeza profunda', 'pele', 'tratamento facial'
            ],
            'massagem relaxante': [
                'massagem', 'massagem relaxante', 'relaxante', 'relax', 
                'massoterapia', 'terapia', 'descontração'
            ],
            'massagem modeladora': [
                'massagem modeladora', 'modeladora', 'modelar', 'redutora',
                'massagem redutora', 'corporal'
            ],
            'radiofrequência': [
                'radiofrequência', 'radiofrequencia', 'radio', 'rf', 
                'radio frequência', 'radio-frequência'
            ],
            'hidrofacial diamante': [
                'hidrofacial', 'hidro', 'facial diamante', 'diamante',
                'microdermoabrasão', 'peeling', 'hidratação facial'
            ],
            'criolipólise': [
                'criolipólise', 'criolipolise', 'cryo', 'congelamento', 
                'gordura localizada', 'redução de medidas'
            ],
            'drenagem linfática': [
                'drenagem', 'linfática', 'drenagem linfática', 'drenar',
                'inchaço', 'retenção', 'detox'
            ],
            'corte feminino': [
                'corte', 'corte feminino', 'cabelo', 'cortar cabelo',
                'corte de cabelo', 'feminino', 'mulher'
            ],
            'escova progressiva': [
                'escova', 'progressiva', 'alisamento', 'alisar',
                'cabelo liso', 'tratamento capilar'
            ],
            'manicure completa': [
                'manicure', 'manicure completa', 'unha', 'unhas',
                'fazer unha', 'cuidar das unhas'
            ],
            'pedicure spa': [
                'pedicure', 'pedi', 'spa', 'pés', 'unha do pé',
                'cuidar dos pés', 'pedicure spa'
            ],
            'peeling químico': [
                'peeling', 'químico', 'peeling químico', 'ácido',
                'renovação', 'esfoliação'
            ],
            'depilação pernas completas': [
                'depilação', 'pernas', 'perna', 'depilar',
                'pelos', 'cera', 'laser'
            ],
            'depilação virilha completa': [
                'virilha', 'íntima', 'bikini', 'região íntima',
                'depilação íntima', 'brazilian'
            ],
            'pacote noiva': [
                'noiva', 'casamento', 'pacote', 'dia especial',
                'combo noiva', 'preparação'
            ],
            'day spa relax': [
                'day spa', 'spa', 'relax', 'relaxamento',
                'dia de spa', 'bem-estar', 'autocuidado'
            ]
        }
        
        # Buscar por sinônimos para cada serviço disponível
        for service in services:
            service_key = service.name.lower()
            
            # Verificar se existe mapeamento para este serviço
            service_keywords = keywords_map.get(service_key, [])
            
            # Também adicionar palavras do próprio nome como keywords
            service_name_words = service.name.lower().split()
            all_keywords = service_keywords + service_name_words
            
            # Verificar se qualquer palavra da busca corresponde às keywords
            if any(keyword in service_name_clean for keyword in all_keywords):
                logger.info(f"✅ Encontrado por sinônimo: {service.name} (termo: '{service_name_clean}')")
                return service
            
            # Verificar também se qualquer keyword corresponde a palavras da busca
            search_words = service_name_clean.split()
            if any(search_word in keyword for keyword in all_keywords for search_word in search_words):
                logger.info(f"✅ Encontrado por keyword reversa: {service.name} (busca: {search_words})")
                return service
        
        # 🔍 FASE 5: Busca SUPER flexível - qualquer palavra em comum
        for service in services:
            service_words = set(service.name.lower().replace('-', ' ').replace('_', ' ').split())
            search_words = set(service_name_clean.replace('-', ' ').replace('_', ' ').split())
            
            # Se há interseção entre as palavras
            common_words = service_words.intersection(search_words)
            if common_words:
                logger.info(f"✅ Encontrado por interseção: {service.name} (palavras comuns: {common_words})")
                return service
        
        logger.warning(f"❌ Serviço não encontrado: '{service_name}' (testados {len(services)} serviços)")
        return None
    
    async def find_services_by_keyword(self, keyword: str, limit: int = 5) -> List[ServiceData]:
        """
        Busca MÚLTIPLOS serviços por palavra-chave (para sugestões)
        
        Args:
            keyword: Palavra-chave para buscar
            limit: Número máximo de resultados
            
        Returns:
            Lista de ServiceData encontrados
        """
        services = await self.get_active_services()
        found_services = []
        
        if not services:
            return found_services
        
        keyword_clean = keyword.lower().strip()
        
        # Buscar serviços que contenham a palavra-chave
        for service in services:
            if keyword_clean in service.name.lower():
                found_services.append(service)
                if len(found_services) >= limit:
                    break
        
        # Se não encontrou nada, buscar por palavras individuais
        if not found_services:
            keyword_words = keyword_clean.split()
            for service in services:
                if any(word in service.name.lower() for word in keyword_words):
                    found_services.append(service)
                    if len(found_services) >= limit:
                        break
        
        logger.info(f"✅ Encontrados {len(found_services)} serviços para '{keyword}'")
        return found_services
    
    async def get_service_info_formatted(self, service_name: str) -> str:
        """
        Busca um serviço e retorna informações formatadas
        CORREÇÃO CRÍTICA: Para resolver problemas de "não oferecemos"
        
        Args:
            service_name: Nome ou termo de busca do serviço
            
        Returns:
            String formatada com informações do serviço ou mensagem de erro
        """
        service = await self.find_service_by_name(service_name)
        
        if service:
            text = f"✅ *{service.name}*\n"
            text += f"💰 Preço: {service.price}\n"
            
            if service.duration:
                text += f"⏰ Duração: {service.duration} minutos\n"
            
            if service.description:
                text += f"ℹ️ _Sobre: {service.description}_\n"
            
            text += "\n📞 *Para agendar, me informe:*\n"
            text += "• Data e horário preferido\n"
            text += "• Seu nome completo\n"
            
            return text
        
        else:
            # Buscar serviços similares como sugestão
            similar_services = await self.find_services_by_keyword(service_name, 3)
            
            if similar_services:
                text = f"🔍 Não encontrei exatamente '{service_name}', mas temos estes serviços similares:\n\n"
                
                for i, similar in enumerate(similar_services, 1):
                    text += f"{i}. *{similar.name}* - {similar.price}\n"
                
                text += "\n💬 Qual destes serviços te interessa?"
                return text
            
            else:
                return f"😔 Desculpe, não oferecemos '{service_name}' no momento.\n\n💬 Digite *serviços* para ver nossa lista completa!"
    
    async def get_business_hours(self, refresh_cache: bool = False) -> Optional[Dict]:
        """
        Busca horários de funcionamento da database usando asyncpg
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Dicionário com horários por dia da semana
        """
        if self._business_hours_cache is None or refresh_cache:
            conn = None
            try:
                conn = await self._get_connection()
                
                # Buscar horários IGUAL ao dynamic_prompts.py
                business_hours = await conn.fetch("""
                    SELECT * FROM business_hours WHERE business_id = $1
                """, self.business_id)
                
                if business_hours:
                    days_map = {
                        0: 'Domingo', 1: 'Segunda', 2: 'Terça', 
                        3: 'Quarta', 4: 'Quinta', 5: 'Sexta', 6: 'Sábado'
                    }
                    
                    hours_dict = {}
                    
                    for hour in business_hours:
                        day_val = hour['day_of_week']
                        day_name = days_map.get(day_val, f"Dia {day_val}")
                        
                        if hour.get('is_open', True):
                            open_time = hour['open_time'].strftime('%H:%M') if hour['open_time'] else '09:00'
                            close_time = hour['close_time'].strftime('%H:%M') if hour['close_time'] else '18:00'
                            hours_dict[day_name] = {
                                "open_time": open_time,
                                "close_time": close_time,
                                "is_open": True
                            }
                        else:
                            hours_dict[day_name] = {"is_open": False}
                    
                    self._business_hours_cache = hours_dict
                    logger.info("✅ Horários de funcionamento carregados")
                else:
                    # Fallback default
                    self._business_hours_cache = {
                        "Segunda": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                        "Terça": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                        "Quarta": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                        "Quinta": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                        "Sexta": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                        "Sábado": {"open_time": "09:00", "close_time": "16:00", "is_open": True},
                        "Domingo": {"is_open": False}
                    }
                    
            except Exception as e:
                logger.error(f"❌ Erro ao buscar horários: {e}")
                # Fallback padrão
                self._business_hours_cache = {
                    "Segunda": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                    "Terça": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                    "Quarta": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                    "Quinta": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                    "Sexta": {"open_time": "09:00", "close_time": "18:00", "is_open": True},
                    "Sábado": {"open_time": "09:00", "close_time": "16:00", "is_open": True},
                    "Domingo": {"is_open": False}
                }
            finally:
                if conn:
                    await conn.close()
        
        return self._business_hours_cache
    
    def _get_default_business_hours(self) -> Dict:
        """Retorna horários padrão quando a tabela não existe"""
        return {
            "hours_by_day": {
                "Segunda": {"open": "09:00:00", "close": "18:00:00", "is_open": True},
                "Terça": {"open": "09:00:00", "close": "18:00:00", "is_open": True},
                "Quarta": {"open": "09:00:00", "close": "18:00:00", "is_open": True},
                "Quinta": {"open": "09:00:00", "close": "18:00:00", "is_open": True},
                "Sexta": {"open": "09:00:00", "close": "18:00:00", "is_open": True},
                "Sábado": {"is_open": False},
                "Domingo": {"is_open": False}
            },
            "formatted_text": "Segunda a Sexta: 09:00 às 18:00\nSábado: Fechado\nDomingo: Fechado",
            "summary": "Segunda a Sexta: 9h às 18h, Fins de semana: Fechado"
        }
    
    async def get_business_hours_formatted_text(self) -> str:
        """
        Retorna horários de funcionamento formatados para WhatsApp
        
        Returns:
            String formatada com horários de funcionamento
        """
        hours_data = await self.get_business_hours()
        
        # Buscar nome da empresa para incluir no template
        company_info = await self.get_company_info()
        company_name = "Studio Beleza & Bem-Estar"  # Default
        if company_info and company_info.get('name'):
            company_name = company_info['name']
        
        if not hours_data:
            return f"🏢 *{company_name}*\n� *Horário de Funcionamento:*\n- _Segunda a Sexta_: 9h às 18h\n- _Sábado_: 9h às 16h\n- _Domingo_: 🚫 Fechado"
        
        # Usar o texto formatado do cache se disponível
        if "formatted_text" in hours_data and hours_data["formatted_text"]:
            text = f"🏢 *{company_name}*\n� *Horário de Funcionamento:*\n"
            
            # Quebrar por linhas e reformatar com itálicos
            lines = hours_data["formatted_text"].split('\n')
            for line in lines:
                if "Fechado" in line:
                    # Extrair o dia da semana e colocar em itálico
                    day_part = line.split(':')[0].strip()
                    text += f"- _{day_part}_: 🚫 Fechado\n"
                else:
                    # Extrair o dia da semana e horário, colocar dia em itálico
                    if ':' in line:
                        day_part = line.split(':')[0].strip()
                        time_part = ':'.join(line.split(':')[1:]).strip()
                        text += f"- _{day_part}_: {time_part}\n"
                    else:
                        text += f"🕘 {line}\n"
            
            return text.strip()
        
        # Fallback para formato padrão com nova formatação
        return f"🏢 *{company_name}*\n� *Horário de Funcionamento:*\n- _Segunda a Sexta_: 9h às 18h\n- _Sábado_: 9h às 16h\n- _Domingo_: 🚫 Fechado"
        
        return self._business_hours_cache
    
    async def get_payment_methods(self, refresh_cache: bool = False) -> Optional[List[Dict]]:
        """
        Busca formas de pagamento da database usando asyncpg
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Lista com formas de pagamento
        """
        if self._payment_methods_cache is None or refresh_cache:
            conn = None
            try:
                conn = await self._get_connection()
                
                # Buscar formas de pagamento IGUAL ao dynamic_prompts.py
                payment_methods = await conn.fetch("""
                    SELECT * FROM payment_methods WHERE business_id = $1
                """, self.business_id)
                
                if payment_methods:
                    self._payment_methods_cache = [
                        {
                            "name": payment['name'],
                            "description": payment.get('description', ''),
                            "additional_info": payment.get('additional_info', '')
                        }
                        for payment in payment_methods
                    ]
                    logger.info(f"✅ Carregadas {len(self._payment_methods_cache)} formas de pagamento")
                else:
                    # Fallback padrão
                    self._payment_methods_cache = [
                        {"name": "Dinheiro", "description": "Pagamento à vista"},
                        {"name": "PIX", "description": "Transferência instantânea"},
                        {"name": "Cartão de Débito", "description": "Pagamento no débito"},
                        {"name": "Cartão de Crédito", "description": "Pagamento no crédito"}
                    ]
                    
            except Exception as e:
                logger.error(f"❌ Erro ao buscar formas de pagamento: {e}")
                # Fallback padrão
                self._payment_methods_cache = [
                    {"name": "Dinheiro", "description": "Pagamento à vista"},
                    {"name": "PIX", "description": "Transferência instantânea"},
                    {"name": "Cartão de Débito", "description": "Pagamento no débito"},
                    {"name": "Cartão de Crédito", "description": "Pagamento no crédito"}
                ]
            finally:
                if conn:
                    await conn.close()
        
        return self._payment_methods_cache
    
    async def get_business_policies(self, refresh_cache: bool = False) -> Optional[List[Dict]]:
        """
        Busca políticas do negócio da database usando asyncpg
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Lista com políticas do negócio
        """
        if self._policies_cache is None or refresh_cache:
            conn = None
            try:
                conn = await self._get_connection()
                
                # Buscar políticas IGUAL ao dynamic_prompts.py
                policies = await conn.fetch("""
                    SELECT * FROM business_policies WHERE business_id = $1
                """, self.business_id)
                
                if policies:
                    self._policies_cache = [
                        {
                            "policy_type": policy['policy_type'],
                            "title": policy.get('title', ''),
                            "description": policy.get('description', ''),
                            "rules": policy.get('rules', '')
                        }
                        for policy in policies
                    ]
                    logger.info(f"✅ Carregadas {len(self._policies_cache)} políticas")
                else:
                    self._policies_cache = []
                    
            except Exception as e:
                logger.error(f"❌ Erro ao buscar políticas: {e}")
                self._policies_cache = []
            finally:
                if conn:
                    await conn.close()
        
        return self._policies_cache
    
    def _get_default_payment_methods(self) -> List[Dict]:
        """Retorna formas de pagamento padrão quando a tabela não existe"""
        return [
            {"name": "Dinheiro", "description": "Pagamento em espécie", "additional_info": None},
            {"name": "PIX", "description": "Transferência instantânea", "additional_info": "Chave PIX disponível"},
            {"name": "Cartão de Débito", "description": "Cartão de débito", "additional_info": None},
            {"name": "Cartão de Crédito", "description": "Cartão de crédito", "additional_info": "Parcelamento disponível"}
        ]
    
    def _get_default_business_policies(self) -> List[Dict]:
        """Retorna políticas padrão quando a tabela não existe"""
        return [
            {
                "type": "cancellation",
                "title": "Política de Cancelamento", 
                "description": "Cancelamentos devem ser feitos com pelo menos 24 horas de antecedência.",
                "rules": {"min_hours": 24, "refund": False}
            },
            {
                "type": "rescheduling",
                "title": "Política de Reagendamento",
                "description": "Reagendamentos podem ser feitos até 2 horas antes do horário marcado.",
                "rules": {"min_hours": 2, "max_reschedules": 2}
            },
            {
                "type": "no_show", 
                "title": "Política de Falta",
                "description": "Faltas sem aviso prévio resultam em cobrança de taxa.",
                "rules": {"fee_percentage": 50, "grace_period": 15}
            }
        ]

    async def get_complete_business_info(self) -> Dict:
        """
        Busca informações completas do negócio incluindo novos dados
        
        Returns:
            Dicionário com todas as informações do negócio
        """
        try:
            # Buscar todos os dados em paralelo
            services = await self.get_active_services()
            company_info = await self.get_company_info()
            business_hours = await self.get_business_hours()
            payment_methods = await self.get_payment_methods()
            policies = await self.get_business_policies()
            
            return {
                "services": services,
                "company_info": company_info,
                "business_hours": business_hours,
                "payment_methods": payment_methods,
                "policies": policies,
                "completeness": {
                    "services": len(services) > 0,
                    "company_info": company_info is not None,
                    "business_hours": business_hours is not None,
                    "payment_methods": len(payment_methods or []) > 0,
                    "policies": len(policies or []) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar informações completas: {e}")
            return {}
    
    async def get_services_dict(self) -> Dict[str, int]:
        """
        Retorna dicionário de serviços no formato compatível com o sistema legado
        
        Returns:
            Dict com nome do serviço como chave e duração como valor
        """
        services = await self.get_active_services()
        
        return {
            service.name.lower(): service.duration
            for service in services
        }
    
    async def clear_cache(self):
        """Limpa o cache forçando nova busca na database"""
        self._services_cache = None
        self._company_info_cache = None
        logger.info("🔄 Cache de dados do negócio limpo")


# Instância global do serviço
business_data_service = BusinessDataService()

async def get_database_services_formatted(user_message: str = "") -> str:
    """
    Função helper para obter serviços formatados da database
    CORREÇÃO: Adiciona função de busca inteligente
    
    Args:
        user_message: Mensagem do usuário para contexto
        
    Returns:
        String formatada com serviços
    """
    return await business_data_service.get_services_formatted_text(user_message)


async def find_service_smart(service_name: str) -> Optional[ServiceData]:
    """
    Função helper para busca inteligente de serviços
    NOVA: Para resolver problemas de "não oferecemos"
    
    Args:
        service_name: Nome ou termo de busca
        
    Returns:
        ServiceData encontrado ou None
    """
    return await business_data_service.find_service_by_name(service_name)


async def get_service_info_smart(service_name: str) -> str:
    """
    Função helper para obter informações formatadas de um serviço
    NOVA: Para substituir respostas de "não oferecemos"
    
    Args:
        service_name: Nome ou termo de busca
        
    Returns:
        String formatada com info do serviço
    """
    return await business_data_service.get_service_info_formatted(service_name)


async def get_database_services() -> List[ServiceData]:
    """Função de conveniência para buscar serviços da database"""
    return await business_data_service.get_active_services()


async def get_database_services_formatted(user_message: str = "") -> str:
    """Função de conveniência para buscar serviços formatados da database"""
    return await business_data_service.get_services_formatted_text(user_message)


async def find_database_service(service_name: str) -> Optional[ServiceData]:
    """Função de conveniência para buscar um serviço específico da database"""
    return await business_data_service.find_service_by_name(service_name)
