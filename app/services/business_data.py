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
        Busca um serviço específico pelo nome
        
        Args:
            service_name: Nome do serviço para buscar
            
        Returns:
            Objeto ServiceData ou None se não encontrado
        """
        services = await self.get_active_services()
        
        service_name_lower = service_name.lower()
        
        # Busca exata primeiro
        for service in services:
            if service.name.lower() == service_name_lower:
                return service
        
        # Busca parcial
        for service in services:
            if service_name_lower in service.name.lower():
                return service
        
        # Busca por palavras-chave
        keywords_map = {
            'corte masculino': ['corte', 'masculino', 'homem', 'cabelo masculino'],
            'corte feminino': ['corte', 'feminino', 'mulher', 'cabelo feminino'],
            'barba': ['barba', 'fazer barba', 'aparar barba'],
            'manicure': ['manicure', 'unha', 'fazer unha']
        }
        
        for service in services:
            service_keywords = keywords_map.get(service.name.lower(), [])
            if any(keyword in service_name_lower for keyword in service_keywords):
                return service
        
        return None
    
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
business_data_service = BusinessDataService(business_id=3)


async def get_database_services() -> List[ServiceData]:
    """Função de conveniência para buscar serviços da database"""
    return await business_data_service.get_active_services()


async def get_database_services_formatted(user_message: str = "") -> str:
    """Função de conveniência para buscar serviços formatados da database"""
    return await business_data_service.get_services_formatted_text(user_message)


async def find_database_service(service_name: str) -> Optional[ServiceData]:
    """Função de conveniência para buscar um serviço específico da database"""
    return await business_data_service.find_service_by_name(service_name)
