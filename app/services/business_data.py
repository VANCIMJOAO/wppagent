"""
Serviço de Dados de Negócio - Interface com Database
Busca informações reais da database ao invés de usar dados hardcoded
"""

from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from app.models.database import Service, Business, CompanyInfo
from app.utils.logger import get_logger
from app.database import AsyncSessionLocal
logger = get_logger(__name__)
import logging

logger = logging.getLogger(__name__)


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
    """Serviço para buscar dados reais do negócio da database"""
    
    def __init__(self, business_id: int = 1):
        self.business_id = business_id
        self._services_cache = None
        self._company_info_cache = None
        self._business_hours_cache = None
        self._payment_methods_cache = None
        self._policies_cache = None
    
    async def get_active_services(self, refresh_cache: bool = False) -> List[ServiceData]:
        """
        Busca serviços ativos da database
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Lista de objetos ServiceData com nome, preço e duração
        """
        if self._services_cache is None or refresh_cache:
            async with AsyncSessionLocal() as db:
                try:
                    result = await db.execute(
                        select(Service).where(
                            and_(
                                Service.business_id == self.business_id,
                                Service.is_active == True
                            )
                        ).order_by(Service.name)
                    )
                    services = result.scalars().all()
                    
                    self._services_cache = [
                        ServiceData(
                            id=service.id,
                            name=service.name,
                            price=service.price,
                            duration=service.duration_minutes,
                            description=service.description or ""
                        )
                        for service in services
                    ]
                    
                    logger.info(f"✅ Carregados {len(self._services_cache)} serviços da database")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar serviços: {e}")
                    self._services_cache = []
        
        return self._services_cache or []
    
    async def get_company_info(self, refresh_cache: bool = False) -> Optional[Dict]:
        """
        Busca informações da empresa da database
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Dicionário com informações da empresa
        """
        if self._company_info_cache is None or refresh_cache:
            async with AsyncSessionLocal() as db:
                try:
                    result = await db.execute(
                        select(CompanyInfo).where(
                            CompanyInfo.business_id == self.business_id
                        )
                    )
                    company_info = result.scalar_one_or_none()
                    
                    if company_info:
                        self._company_info_cache = {
                            "company_name": company_info.company_name,
                            "slogan": company_info.slogan,
                            "about_us": company_info.about_us,
                            "address": getattr(company_info, 'address', ''),
                            "phone": getattr(company_info, 'phone', ''),
                            "opening_hours": getattr(company_info, 'opening_hours', {})
                        }
                    else:
                        # Fallback se não houver dados
                        self._company_info_cache = {
                            "company_name": "Nossa Empresa",
                            "slogan": "Excelência em atendimento",
                            "about_us": "Oferecemos os melhores serviços para você!",
                            "address": "",
                            "phone": "",
                            "opening_hours": {}
                        }
                    
                    logger.info("✅ Informações da empresa carregadas da database")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar informações da empresa: {e}")
                    self._company_info_cache = None
        
        return self._company_info_cache
    
    async def get_services_formatted_text(self) -> str:
        """
        Retorna texto formatado com serviços e preços da database
        Formatação otimizada para WhatsApp com quebras de linha adequadas
        
        Returns:
            String formatada com lista de serviços
        """
        services = await self.get_active_services()
        
        if not services:
            return "🔍 No momento não temos serviços cadastrados.\n📞 Entre em contato conosco!"
        
        text = "📋 *Nossos Serviços e Preços:*\n\n"
        
        for i, service in enumerate(services, 1):
            # Formatação WhatsApp-friendly com numeração clara
            text += f"{i}. *{service.name}*\n"
            text += f"   💰 {service.price}"
            if service.duration:
                text += f" • ⏰ {service.duration}min"
            text += "\n"
            if service.description:
                text += f"   ℹ️ _{service.description}_\n"
            text += "\n"  # Linha extra entre serviços para melhor separação
        
        text += "📞 *Para agendar:*\n"
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
            return "🏢 *Studio Beleza & Bem-Estar*\n📍 Rua das Flores, 123 - Centro, São Paulo, SP\n📞 Entre em contato conosco!"
        
        text = f"🏢 *{company_info.get('name', 'Studio Beleza & Bem-Estar')}*\n\n"
        
        if company_info.get('address'):
            text += f"📍 *Endereço:*\n{company_info['address']}\n\n"
        
        if company_info.get('phone'):
            text += f"📞 *Telefone:* {company_info['phone']}\n"
        
        if company_info.get('email'):
            text += f"📧 *E-mail:* {company_info['email']}\n"
        
        if company_info.get('website'):
            text += f"🌐 *Site:* {company_info['website']}\n"
        
        # Adicionar horário de funcionamento
        text += "\n"
        hours_text = await self.get_business_hours_formatted_text()
        text += hours_text
        
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
        Busca horários de funcionamento da database
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Dicionário com horários por dia da semana
        """
        if self._business_hours_cache is None or refresh_cache:
            async with AsyncSessionLocal() as db:
                try:
                    result = await db.execute(
                        text("""
                        SELECT day_of_week, is_open, open_time, close_time, notes
                        FROM business_hours 
                        WHERE business_id = :business_id
                        ORDER BY day_of_week
                        """),
                        {"business_id": self.business_id}
                    )
                    hours_data = result.fetchall()
                    
                    if hours_data:
                        days_map = {
                            0: 'Domingo', 1: 'Segunda', 2: 'Terça', 
                            3: 'Quarta', 4: 'Quinta', 5: 'Sexta', 6: 'Sábado'
                        }
                        
                        hours_dict = {}
                        hours_text = []
                        
                        for row in hours_data:
                            day_name = days_map.get(row[0], f"Dia {row[0]}")
                            if row[1]:  # is_open
                                hours_dict[day_name] = {
                                    "open": str(row[2]),
                                    "close": str(row[3]),
                                    "is_open": True
                                }
                                hours_text.append(f"{day_name}: {row[2]} às {row[3]}")
                            else:
                                hours_dict[day_name] = {"is_open": False}
                                hours_text.append(f"{day_name}: Fechado")
                        
                        self._business_hours_cache = {
                            "hours_by_day": hours_dict,
                            "formatted_text": "\n".join(hours_text),
                            "summary": "Segunda a Sexta: 9h às 18h, Sábado: 9h às 16h, Domingo: Fechado"
                        }
                    else:
                        # Retornar dados padrão se não há registros
                        self._business_hours_cache = self._get_default_business_hours()
                    
                    logger.info("✅ Horários de funcionamento carregados da database")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar horários: {e}")
                    # Se a tabela não existe, retornar dados padrão
                    if "does not exist" in str(e):
                        logger.warning("⚠️  Tabela business_hours não existe, usando dados padrão")
                        self._business_hours_cache = self._get_default_business_hours()
                    else:
                        self._business_hours_cache = None

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
        
        if not hours_data:
            return "📅 *Horário de Funcionamento:*\n\n🕘 Segunda a Sexta: 9h às 18h\n🕘 Sábado: 9h às 16h\n🚫 Domingo: Fechado"
        
        # Usar o texto formatado do cache se disponível
        if "formatted_text" in hours_data and hours_data["formatted_text"]:
            text = "📅 *Horário de Funcionamento:*\n\n"
            
            # Quebrar por linhas e reformatar
            lines = hours_data["formatted_text"].split('\n')
            for line in lines:
                if "Fechado" in line:
                    text += f"🚫 {line}\n"
                else:
                    text += f"🕘 {line}\n"
            
            return text.strip()
        
        # Fallback para formato padrão
        return "📅 *Horário de Funcionamento:*\n\n🕘 Segunda a Sexta: 9h às 18h\n🕘 Sábado: 9h às 16h\n🚫 Domingo: Fechado"
        
        return self._business_hours_cache
    
    async def get_payment_methods(self, refresh_cache: bool = False) -> Optional[List[Dict]]:
        """
        Busca formas de pagamento da database
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Lista com formas de pagamento
        """
        if self._payment_methods_cache is None or refresh_cache:
            async with AsyncSessionLocal() as db:
                try:
                    result = await db.execute(
                        text("""
                        SELECT name, description, additional_info
                        FROM payment_methods 
                        WHERE business_id = :business_id AND is_active = true
                        ORDER BY display_order
                        """),
                        {"business_id": self.business_id}
                    )
                    payment_data = result.fetchall()
                    
                    if payment_data:
                        self._payment_methods_cache = [
                            {
                                "name": row[0],
                                "description": row[1],
                                "additional_info": row[2]
                            }
                            for row in payment_data
                        ]
                    else:
                        self._payment_methods_cache = []
                    
                    logger.info(f"✅ {len(self._payment_methods_cache)} formas de pagamento carregadas")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar formas de pagamento: {e}")
                    # Se a tabela não existe, usar dados padrão
                    if "does not exist" in str(e):
                        logger.warning("⚠️  Tabela payment_methods não existe, usando dados padrão")
                        self._payment_methods_cache = self._get_default_payment_methods()
                    else:
                        self._payment_methods_cache = []
        
        return self._payment_methods_cache
    
    async def get_business_policies(self, refresh_cache: bool = False) -> Optional[List[Dict]]:
        """
        Busca políticas do negócio da database
        
        Args:
            refresh_cache: Se deve atualizar o cache
            
        Returns:
            Lista com políticas do negócio
        """
        if self._policies_cache is None or refresh_cache:
            async with AsyncSessionLocal() as db:
                try:
                    result = await db.execute(
                        text("""
                        SELECT policy_type, title, description, rules
                        FROM business_policies 
                        WHERE business_id = :business_id AND is_active = true
                        ORDER BY policy_type
                        """),
                        {"business_id": self.business_id}
                    )
                    policy_data = result.fetchall()
                    
                    if policy_data:
                        self._policies_cache = [
                            {
                                "type": row[0],
                                "title": row[1],
                                "description": row[2],
                                "rules": row[3]
                            }
                            for row in policy_data
                        ]
                    else:
                        self._policies_cache = []
                    
                    logger.info(f"✅ {len(self._policies_cache)} políticas carregadas")
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao buscar políticas: {e}")
                    # Se a tabela não existe, usar dados padrão
                    if "does not exist" in str(e):
                        logger.warning("⚠️  Tabela business_policies não existe, usando dados padrão")
                        self._policies_cache = self._get_default_business_policies()
                    else:
                        self._policies_cache = []
        
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
business_data_service = BusinessDataService(business_id=1)


async def get_database_services() -> List[ServiceData]:
    """Função de conveniência para buscar serviços da database"""
    return await business_data_service.get_active_services()


async def get_database_services_formatted() -> str:
    """Função de conveniência para buscar serviços formatados da database"""
    return await business_data_service.get_services_formatted_text()


async def find_database_service(service_name: str) -> Optional[ServiceData]:
    """Função de conveniência para buscar um serviço específico da database"""
    return await business_data_service.find_service_by_name(service_name)
