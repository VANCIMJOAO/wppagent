"""
Sistema Integrado de Validação de Serviços
Verifica existência, cria automaticamente e sugere serviços similares
"""
import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.models.database import Service, Business
from app.utils.logger import get_logger
# REMOVIDO: from app.prompts import SERVICES (agora usa dados da database)
logger = get_logger(__name__)

logger = logging.getLogger(__name__)

@dataclass
class ServiceMatch:
    """Representa uma correspondência de serviço"""
    service: Service
    confidence: float
    exact_match: bool

@dataclass
class ServiceValidationResult:
    """Resultado da validação de serviço"""
    found: bool
    service: Optional[Service]
    matches: List[ServiceMatch]
    suggestions: List[str]
    auto_created: bool
    confidence: float

@dataclass
class ServiceSuggestion:
    """Sugestão de serviço com detalhes"""
    name: str
    description: str
    duration: int
    price: str
    category: str


class ServiceValidationService:
    """Serviço para validação e gerenciamento de serviços"""
    
    def __init__(self):
        self.service_categories = {
            'cabelo': ['corte', 'cabelo', 'hair', 'cut'],
            'barba': ['barba', 'beard', 'bigode'],
            'manicure': ['manicure', 'mao', 'nail', 'unha'],
            'pedicure': ['pedicure', 'pe', 'foot'],
            'sobrancelha': ['sobrancelha', 'eyebrow', 'ceja'],
            'estetica': ['limpeza', 'tratamento', 'facial'],
            'massagem': ['massagem', 'massage', 'relaxante']
        }
        
        self.similarity_threshold = 0.6
    
    async def validate_and_get_service(
        self,
        db: AsyncSession,
        service_input: str,
        auto_create: bool = True,
        business_id: Optional[int] = None
    ) -> ServiceValidationResult:
        """
        Valida entrada de serviço e retorna serviço correspondente
        
        Args:
            db: Sessão do banco
            service_input: Nome/descrição do serviço inserido pelo usuário
            auto_create: Se deve criar serviço automaticamente se não encontrar
            business_id: ID do negócio (opcional)
            
        Returns:
            Resultado da validação com serviço encontrado/criado
        """
        try:
            logger.info(f"Validando serviço: '{service_input}'")
            
            if not service_input or len(service_input.strip()) < 2:
                return ServiceValidationResult(
                    found=False,
                    service=None,
                    matches=[],
                    suggestions=await self._get_popular_services(db),
                    auto_created=False,
                    confidence=0.0
                )
            
            # 1. Busca exata
            exact_match = await self._find_exact_match(db, service_input)
            if exact_match:
                return ServiceValidationResult(
                    found=True,
                    service=exact_match,
                    matches=[ServiceMatch(exact_match, 1.0, True)],
                    suggestions=[],
                    auto_created=False,
                    confidence=1.0
                )
            
            # 2. Busca por similaridade
            similar_matches = await self._find_similar_services(db, service_input)
            
            if similar_matches and similar_matches[0].confidence >= self.similarity_threshold:
                best_match = similar_matches[0]
                return ServiceValidationResult(
                    found=True,
                    service=best_match.service,
                    matches=similar_matches,
                    suggestions=[],
                    auto_created=False,
                    confidence=best_match.confidence
                )
            
            # 3. Criar automaticamente se habilitado
            if auto_create:
                created_service = await self._auto_create_service(
                    db, service_input, business_id
                )
                
                if created_service:
                    return ServiceValidationResult(
                        found=True,
                        service=created_service,
                        matches=[ServiceMatch(created_service, 0.8, False)],
                        suggestions=[],
                        auto_created=True,
                        confidence=0.8
                    )
            
            # 4. Retornar sugestões
            suggestions = await self._generate_suggestions(service_input)
            
            return ServiceValidationResult(
                found=False,
                service=None,
                matches=similar_matches,
                suggestions=suggestions,
                auto_created=False,
                confidence=0.0
            )
            
        except Exception as e:
            logger.error(f"Erro na validação de serviço: {e}")
            raise
    
    async def get_service_recommendations(
        self,
        db: AsyncSession,
        user_history: List[str] = None,
        category: str = None,
        max_recommendations: int = 5
    ) -> List[ServiceSuggestion]:
        """
        Obtém recomendações de serviços baseado em histórico e categoria
        
        Args:
            db: Sessão do banco
            user_history: Histórico de serviços do usuário
            category: Categoria preferida
            max_recommendations: Máximo de recomendações
            
        Returns:
            Lista de recomendações de serviços
        """
        try:
            recommendations = []
            
            # Buscar serviços populares
            popular_services = await self._get_popular_services_detailed(db)
            
            # Se tem histórico, recomendar serviços relacionados
            if user_history:
                related_services = await self._get_related_services(db, user_history)
                recommendations.extend(related_services)
            
            # Adicionar serviços populares
            for service in popular_services:
                if len(recommendations) >= max_recommendations:
                    break
                    
                # Evitar duplicatas
                if not any(r.name == service['name'] for r in recommendations):
                    recommendations.append(ServiceSuggestion(
                        name=service['name'],
                        description=service.get('description', ''),
                        duration=service.get('duration_minutes', 60),
                        price=service.get('price', 'Consultar'),
                        category=self._classify_service(service['name'])
                    ))
            
            return recommendations[:max_recommendations]
            
        except Exception as e:
            logger.error(f"Erro ao obter recomendações: {e}")
            return []
    
    async def verify_service_capacity(
        self,
        db: AsyncSession,
        service_id: int,
        date_range: Tuple[str, str]
    ) -> Dict:
        """
        Verifica capacidade e demanda de um serviço
        
        Args:
            db: Sessão do banco
            service_id: ID do serviço
            date_range: Tupla com data inicial e final (YYYY-MM-DD)
            
        Returns:
            Análise de capacidade do serviço
        """
        try:
            from datetime import datetime
            from app.models.database import Appointment
            
            start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
            end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
            
            # Buscar serviço
            service_result = await db.execute(select(Service).where(Service.id == service_id))
            service = service_result.scalar_one_or_none()
            
            if not service:
                return {'error': 'Serviço não encontrado'}
            
            # Contar agendamentos no período
            appointments_query = await db.execute(
                select(func.count(Appointment.id), func.avg(Appointment.price_at_booking)).where(
                    and_(
                        Appointment.service_id == service_id,
                        Appointment.date_time >= start_date,
                        Appointment.date_time <= end_date,
                        Appointment.status.in_(['pendente', 'confirmado', 'concluido'])
                    )
                )
            )
            
            appointment_count, avg_price = appointments_query.first()
            appointment_count = appointment_count or 0
            avg_price = float(avg_price) if avg_price else 0.0
            
            # Calcular estatísticas
            days_in_period = (end_date - start_date).days + 1
            appointments_per_day = appointment_count / days_in_period if days_in_period > 0 else 0
            
            # Estimar capacidade máxima (assumindo 8 horas úteis por dia)
            daily_capacity = (8 * 60) // service.duration_minutes if service.duration_minutes else 8
            total_capacity = daily_capacity * days_in_period
            utilization_rate = (appointment_count / total_capacity * 100) if total_capacity > 0 else 0
            
            return {
                'service_name': service.name,
                'period_days': days_in_period,
                'total_appointments': appointment_count,
                'appointments_per_day': round(appointments_per_day, 2),
                'average_price': round(avg_price, 2),
                'estimated_daily_capacity': daily_capacity,
                'utilization_rate': round(utilization_rate, 2),
                'capacity_status': self._get_capacity_status(utilization_rate),
                'revenue_period': round(appointment_count * avg_price, 2)
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar capacidade do serviço: {e}")
            return {'error': str(e)}
    
    async def _find_exact_match(self, db: AsyncSession, service_input: str) -> Optional[Service]:
        """Busca correspondência exata (case insensitive)"""
        try:
            result = await db.execute(
                select(Service).where(
                    func.lower(Service.name) == func.lower(service_input.strip())
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Erro na busca exata: {e}")
            return None
    
    async def _find_similar_services(
        self, 
        db: AsyncSession, 
        service_input: str
    ) -> List[ServiceMatch]:
        """Busca serviços similares usando algoritmo de similaridade"""
        try:
            # Buscar todos os serviços
            result = await db.execute(select(Service))
            all_services = result.scalars().all()
            
            matches = []
            input_lower = service_input.lower().strip()
            
            for service in all_services:
                # Calcular similaridade usando diferentes métodos
                name_similarity = SequenceMatcher(None, input_lower, service.name.lower()).ratio()
                
                # Verificar se contém palavras-chave
                keyword_bonus = 0.0
                input_words = set(input_lower.split())
                service_words = set(service.name.lower().split())
                common_words = input_words & service_words
                
                if common_words:
                    keyword_bonus = len(common_words) / max(len(input_words), len(service_words)) * 0.3
                
                # Verificar categoria
                category_bonus = 0.0
                service_category = self._classify_service(service.name)
                if self._matches_category(input_lower, service_category):
                    category_bonus = 0.2
                
                # Pontuação final
                final_confidence = min(1.0, name_similarity + keyword_bonus + category_bonus)
                
                if final_confidence > 0.3:  # Threshold mínimo
                    matches.append(ServiceMatch(
                        service=service,
                        confidence=final_confidence,
                        exact_match=False
                    ))
            
            # Ordenar por confiança
            matches.sort(key=lambda x: x.confidence, reverse=True)
            return matches[:5]  # Top 5 matches
            
        except Exception as e:
            logger.error(f"Erro na busca por similaridade: {e}")
            return []
    
    async def _auto_create_service(
        self,
        db: AsyncSession,
        service_name: str,
        business_id: Optional[int] = None
    ) -> Optional[Service]:
        """Cria serviço automaticamente com configurações inteligentes"""
        try:
            # Obter ou criar business padrão
            if not business_id:
                business_result = await db.execute(select(Business).limit(1))
                business = business_result.scalar_one_or_none()
                
                if not business:
                    business = Business(
                        name="Negócio Principal",
                        created_at=func.now()
                    )
                    db.add(business)
                    await db.flush()
                
                business_id = business.id
            
            # Determinar configurações baseadas no tipo de serviço
            service_config = self._get_service_config(service_name)
            
            # Criar serviço
            new_service = Service(
                business_id=business_id,
                name=service_name.title(),
                description=service_config['description'],
                price=service_config['price'],
                duration_minutes=service_config['duration'],
                is_active=True,
                created_at=func.now()
            )
            
            db.add(new_service)
            await db.commit()
            await db.refresh(new_service)
            
            logger.info(f"Serviço criado automaticamente: {new_service.name} (ID: {new_service.id})")
            return new_service
            
        except Exception as e:
            logger.error(f"Erro ao criar serviço automaticamente: {e}")
            await db.rollback()
            return None
    
    async def _get_popular_services(self, db: AsyncSession) -> List[str]:
        """Obtém lista de serviços mais populares"""
        try:
            from app.models.database import Appointment
            
            # Buscar serviços mais agendados
            popular_query = await db.execute(
                select(Service.name, func.count(Appointment.id).label('count'))
                .join(Appointment, Service.id == Appointment.service_id)
                .group_by(Service.name)
                .order_by(func.count(Appointment.id).desc())
                .limit(10)
            )
            
            popular_services = [row[0] for row in popular_query.all()]
            
            # Se não há agendamentos, buscar serviços da database
            if not popular_services:
                from app.services.business_data import business_data_service
                try:
                    services = await business_data_service.get_active_services()
                    popular_services = [s['name'] for s in services[:10]]
                except Exception as e:
                    logger.error(f"Erro ao buscar serviços da database: {e}")
                    popular_services = ["Corte Masculino", "Corte Feminino", "Barba", "Manicure"]
            
            return popular_services
            
        except Exception as e:
            logger.error(f"Erro ao buscar serviços populares: {e}")
            # Fallback para dados da database
            from app.services.business_data import business_data_service
            try:
                services = await business_data_service.get_active_services()
                return [s['name'] for s in services[:10]]
            except:
                return ["Corte Masculino", "Corte Feminino", "Barba", "Manicure"]
    
    async def _get_popular_services_detailed(self, db: AsyncSession) -> List[Dict]:
        """Obtém detalhes dos serviços populares"""
        try:
            result = await db.execute(
                select(Service).where(Service.is_active == True).limit(10)
            )
            
            services = []
            for service in result.scalars().all():
                services.append({
                    'id': service.id,
                    'name': service.name,
                    'description': service.description,
                    'price': service.price,
                    'duration_minutes': service.duration_minutes
                })
            
            return services
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes dos serviços: {e}")
            return []
    
    async def _get_related_services(
        self, 
        db: AsyncSession, 
        user_history: List[str]
    ) -> List[ServiceSuggestion]:
        """Obtém serviços relacionados baseado no histórico"""
        try:
            related = []
            
            for service_name in user_history:
                category = self._classify_service(service_name)
                
                # Buscar outros serviços da mesma categoria
                category_services = await db.execute(
                    select(Service).where(
                        and_(
                            Service.is_active == True,
                            Service.name != service_name
                        )
                    )
                )
                
                for service in category_services.scalars().all():
                    if self._classify_service(service.name) == category:
                        related.append(ServiceSuggestion(
                            name=service.name,
                            description=service.description or '',
                            duration=service.duration_minutes or 60,
                            price=service.price or 'Consultar',
                            category=category
                        ))
            
            return related[:3]  # Máximo 3 relacionados
            
        except Exception as e:
            logger.error(f"Erro ao buscar serviços relacionados: {e}")
            return []
    
    def _classify_service(self, service_name: str) -> str:
        """Classifica serviço por categoria"""
        service_lower = service_name.lower()
        
        for category, keywords in self.service_categories.items():
            if any(keyword in service_lower for keyword in keywords):
                return category
        
        return 'outros'
    
    def _matches_category(self, input_text: str, category: str) -> bool:
        """Verifica se entrada corresponde a uma categoria"""
        if category in self.service_categories:
            keywords = self.service_categories[category]
            return any(keyword in input_text for keyword in keywords)
        return False
    
    def _get_service_config(self, service_name: str) -> Dict:
        """Obtém configuração padrão baseada no tipo de serviço"""
        service_lower = service_name.lower()
        
        # Configurações por categoria
        configs = {
            'cabelo': {
                'description': 'Corte e finalização profissional',
                'duration': 45,
                'price': 'R$ 35,00'
            },
            'barba': {
                'description': 'Aparação e modelagem de barba',
                'duration': 30,
                'price': 'R$ 25,00'
            },
            'manicure': {
                'description': 'Cuidados completos para as mãos',
                'duration': 60,
                'price': 'R$ 30,00'
            },
            'pedicure': {
                'description': 'Cuidados completos para os pés',
                'duration': 60,
                'price': 'R$ 35,00'
            },
            'sobrancelha': {
                'description': 'Design e modelagem de sobrancelhas',
                'duration': 20,
                'price': 'R$ 20,00'
            }
        }
        
        # Determinar categoria e retornar config
        category = self._classify_service(service_name)
        
        if category in configs:
            return configs[category]
        
        # Configuração padrão
        return {
            'description': f'Serviço profissional de {service_name.lower()}',
            'duration': 60,
            'price': 'R$ 50,00'
        }
    
    async def _generate_suggestions(self, service_input: str) -> List[str]:
        """Gera sugestões baseadas na entrada"""
        input_lower = service_input.lower()
        suggestions = []
        
        # Sugestões baseadas em palavras-chave
        keyword_suggestions = {
            'corte': ['Corte Masculino', 'Corte Feminino', 'Corte Infantil'],
            'cabelo': ['Corte de Cabelo', 'Escova', 'Penteado'],
            'barba': ['Barba Completa', 'Aparar Barba', 'Bigode'],
            'unha': ['Manicure', 'Pedicure', 'Esmaltação'],
            'sobrancelha': ['Design de Sobrancelhas', 'Depilação'],
            'massagem': ['Massagem Relaxante', 'Massagem Terapêutica']
        }
        
        for keyword, service_list in keyword_suggestions.items():
            if keyword in input_lower:
                suggestions.extend(service_list)
        
        # Se não encontrou sugestões específicas, usar populares da database
        if not suggestions:
            try:
                from app.services.business_data import business_data_service
                import asyncio
                services = asyncio.run(business_data_service.get_active_services())
                suggestions = [s['name'] for s in services[:5]]
            except:
                suggestions = ["Corte Masculino", "Corte Feminino", "Barba", "Manicure", "Sobrancelha"]
        
        return suggestions[:5]
    
    def _get_capacity_status(self, utilization_rate: float) -> str:
        """Determina status da capacidade baseado na taxa de utilização"""
        if utilization_rate >= 90:
            return "Muito Alto"
        elif utilization_rate >= 70:
            return "Alto"
        elif utilization_rate >= 50:
            return "Médio"
        elif utilization_rate >= 30:
            return "Baixo"
        else:
            return "Muito Baixo"


# Instância global do serviço
service_validator = ServiceValidationService()
