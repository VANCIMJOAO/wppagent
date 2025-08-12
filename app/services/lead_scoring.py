from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema Avançado de Lead Scoring para WhatsApp Agent
Identifica e prioriza oportunidades de negócio em tempo real
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from dataclasses import dataclass, field
import re

logger = logging.getLogger(__name__)


class LeadCategory(Enum):
    """Categorias de leads baseadas no score"""
    COLD = "cold"           # 0-30: Baixo interesse
    WARM = "warm"           # 31-60: Interesse moderado
    HOT = "hot"             # 61-80: Alto interesse
    QUALIFIED = "qualified" # 81-95: Lead qualificado
    OPPORTUNITY = "opportunity" # 96-100: Oportunidade imediata


class InteractionType(Enum):
    """Tipos de interação do cliente"""
    FIRST_CONTACT = "first_contact"
    PRICE_INQUIRY = "price_inquiry"
    SERVICE_INQUIRY = "service_inquiry"
    APPOINTMENT_REQUEST = "appointment_request"
    COMPLAINT = "complaint"
    FOLLOW_UP_RESPONSE = "follow_up_response"
    REFERRAL = "referral"


@dataclass
class LeadScore:
    """Representa o score de um lead"""
    total_score: float
    category: LeadCategory
    factors: Dict[str, float]
    recommendations: List[str]
    priority_level: int  # 1-5 (5 = máxima prioridade)
    confidence: float
    next_actions: List[str]
    estimated_value: float
    conversion_probability: float


@dataclass
class CustomerProfile:
    """Perfil completo do cliente para scoring"""
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None  # Adicionado campo email
    total_interactions: int = 0
    last_interaction: Optional[datetime] = None
    avg_response_time: float = 0.0  # em minutos
    services_purchased: List[str] = field(default_factory=list)
    total_spent: float = 0.0
    referrals_made: int = 0
    complaints: int = 0
    no_shows: int = 0
    cancellations: int = 0
    preferred_time: Optional[str] = None
    communication_style: str = "neutral"  # formal, casual, neutral
    geographic_location: Optional[str] = None
    interaction_history: List[InteractionType] = field(default_factory=list)
    # Novos campos para compatibilidade
    interactions: List[str] = field(default_factory=list)
    preferred_services: List[str] = field(default_factory=list)
    total_appointments: int = 0


class LeadScoringEngine:
    """Engine principal de Lead Scoring"""
    
    def __init__(self):
        self.scoring_weights = {
            # Fatores comportamentais (40% do score)
            "urgency_indicators": 15,      # "urgente", "hoje", "agora"
            "price_sensitivity": 10,       # perguntas sobre preço
            "service_specificity": 10,     # menciona serviços específicos
            "decision_authority": 5,       # "eu decido", "minha empresa"
            
            # Histórico do cliente (30% do score)
            "previous_purchases": 12,      # compras anteriores
            "interaction_frequency": 8,    # frequência de contato
            "response_speed": 5,           # velocidade de resposta
            "loyalty_indicators": 5,       # indicadores de fidelidade
            
            # Características demográficas (20% do score)
            "geographic_value": 8,         # localização valiosa
            "time_preference": 6,          # horários premium
            "communication_quality": 6,    # qualidade da comunicação
            
            # Indicadores de intenção (10% do score)
            "buying_signals": 5,           # sinais de compra
            "timeline_urgency": 3,         # urgência temporal
            "budget_indicators": 2,        # indicadores de orçamento
        }
        
        # Palavras-chave para detecção de intenção
        self.urgency_keywords = [
            "urgente", "hoje", "agora", "imediato", "rápido", "emergência",
            "preciso", "necessário", "importante", "amanhã", "esta semana"
        ]
        
        self.price_keywords = [
            "preço", "valor", "quanto custa", "orçamento", "investimento",
            "promoção", "desconto", "condições", "parcelamento", "taxa"
        ]
        
        self.buying_signals = [
            "quero", "preciso", "vou", "pretendo", "estou interessado",
            "gostaria", "como faço para", "onde", "quando posso"
        ]
        
        self.decision_authority = [
            "eu decido", "sou o responsável", "minha empresa", "nossa equipe",
            "posso autorizar", "tenho autonomia", "sou o dono"
        ]

    def calculate_lead_score(
        self, 
        message: str, 
        customer_profile: CustomerProfile,
        context: Dict[str, Any] = None
    ) -> LeadScore:
        """Calcula o score completo do lead"""
        
        factors = {}
        total_score = 0.0
        
        # 1. Análise comportamental da mensagem
        behavioral_score = self._analyze_message_behavior(message)
        factors.update(behavioral_score)
        
        # 2. Análise do histórico do cliente
        history_score = self._analyze_customer_history(customer_profile)
        factors.update(history_score)
        
        # 3. Análise demográfica/contextual
        demographic_score = self._analyze_demographics(customer_profile, context)
        factors.update(demographic_score)
        
        # 4. Análise de intenção de compra
        intention_score = self._analyze_buying_intention(message, customer_profile)
        factors.update(intention_score)
        
        # Calcular score total ponderado
        for factor, score in factors.items():
            weight = self.scoring_weights.get(factor, 1)
            total_score += score * (weight / 100)
        
        # Limitar score entre 0-100
        total_score = max(0, min(100, total_score))
        
        # Determinar categoria e recomendações
        category = self._determine_category(total_score)
        recommendations = self._generate_recommendations(total_score, factors, customer_profile)
        priority_level = self._calculate_priority(total_score, factors)
        confidence = self._calculate_confidence(factors)
        next_actions = self._suggest_next_actions(category, factors, customer_profile)
        estimated_value = self._estimate_value(customer_profile, factors)
        conversion_probability = self._calculate_conversion_probability(total_score, factors)
        
        return LeadScore(
            total_score=round(total_score, 2),
            category=category,
            factors=factors,
            recommendations=recommendations,
            priority_level=priority_level,
            confidence=round(confidence, 2),
            next_actions=next_actions,
            estimated_value=round(estimated_value, 2),
            conversion_probability=round(conversion_probability, 2)
        )

    def _analyze_message_behavior(self, message: str) -> Dict[str, float]:
        """Analisa comportamento na mensagem atual"""
        message_lower = message.lower()
        factors = {}
        
        # Indicadores de urgência
        urgency_count = sum(1 for keyword in self.urgency_keywords if keyword in message_lower)
        factors["urgency_indicators"] = min(10, urgency_count * 3)
        
        # Sensibilidade a preço
        price_count = sum(1 for keyword in self.price_keywords if keyword in message_lower)
        factors["price_sensitivity"] = min(8, price_count * 2.5)
        
        # Especificidade do serviço
        service_specificity = 0
        if any(word in message_lower for word in ["corte", "barba", "sobrancelha", "massagem"]):
            service_specificity += 3
        if len(message.split()) > 10:  # mensagem detalhada
            service_specificity += 2
        factors["service_specificity"] = min(7, service_specificity)
        
        # Autoridade de decisão
        authority_count = sum(1 for phrase in self.decision_authority if phrase in message_lower)
        factors["decision_authority"] = min(5, authority_count * 2)
        
        return factors

    def _analyze_customer_history(self, profile: CustomerProfile) -> Dict[str, float]:
        """Analisa histórico do cliente"""
        factors = {}
        
        # Compras anteriores
        purchase_score = 0
        if profile.total_spent > 0:
            if profile.total_spent > 500:
                purchase_score = 10
            elif profile.total_spent > 200:
                purchase_score = 7
            elif profile.total_spent > 50:
                purchase_score = 4
            else:
                purchase_score = 2
        factors["previous_purchases"] = purchase_score
        
        # Frequência de interação
        interaction_score = 0
        if profile.total_interactions > 0:
            if profile.total_interactions >= 10:
                interaction_score = 8
            elif profile.total_interactions >= 5:
                interaction_score = 6
            elif profile.total_interactions >= 2:
                interaction_score = 4
            else:
                interaction_score = 2
        factors["interaction_frequency"] = interaction_score
        
        # Velocidade de resposta
        response_score = 0
        if profile.avg_response_time > 0:
            if profile.avg_response_time <= 5:  # responde em 5 min
                response_score = 5
            elif profile.avg_response_time <= 30:  # responde em 30 min
                response_score = 3
            elif profile.avg_response_time <= 120:  # responde em 2h
                response_score = 1
        factors["response_speed"] = response_score
        
        # Indicadores de fidelidade
        loyalty_score = 0
        loyalty_score += min(3, profile.referrals_made)
        loyalty_score -= min(2, profile.complaints)
        loyalty_score -= min(2, profile.no_shows)
        factors["loyalty_indicators"] = max(0, loyalty_score)
        
        return factors

    def _analyze_demographics(self, profile: CustomerProfile, context: Dict[str, Any]) -> Dict[str, float]:
        """Analisa características demográficas"""
        factors = {}
        
        # Valor geográfico
        geographic_score = 0
        if profile.geographic_location:
            high_value_areas = ["centro", "zona sul", "bairro nobre"]
            if any(area in profile.geographic_location.lower() for area in high_value_areas):
                geographic_score = 6
            else:
                geographic_score = 3
        factors["geographic_value"] = geographic_score
        
        # Preferência de horário
        time_score = 0
        if profile.preferred_time:
            premium_times = ["manhã", "tarde", "horário comercial"]
            if any(time in profile.preferred_time.lower() for time in premium_times):
                time_score = 4
            else:
                time_score = 2
        factors["time_preference"] = time_score
        
        # Qualidade da comunicação
        communication_score = 0
        if profile.communication_style == "formal":
            communication_score = 5
        elif profile.communication_style == "casual":
            communication_score = 3
        else:
            communication_score = 2
        factors["communication_quality"] = communication_score
        
        return factors

    def _analyze_buying_intention(self, message: str, profile: CustomerProfile) -> Dict[str, float]:
        """Analisa intenção de compra"""
        message_lower = message.lower()
        factors = {}
        
        # Sinais de compra
        buying_count = sum(1 for signal in self.buying_signals if signal in message_lower)
        factors["buying_signals"] = min(4, buying_count * 1.5)
        
        # Urgência temporal
        timeline_score = 0
        if any(word in message_lower for word in ["hoje", "amanhã", "esta semana"]):
            timeline_score = 3
        elif any(word in message_lower for word in ["próxima semana", "mês que vem"]):
            timeline_score = 1
        factors["timeline_urgency"] = timeline_score
        
        # Indicadores de orçamento
        budget_score = 0
        if "orçamento" in message_lower or "quanto" in message_lower:
            budget_score = 2
        factors["budget_indicators"] = budget_score
        
        return factors

    def _determine_category(self, score: float) -> LeadCategory:
        """Determina categoria do lead baseada no score"""
        if score >= 96:
            return LeadCategory.OPPORTUNITY
        elif score >= 81:
            return LeadCategory.QUALIFIED
        elif score >= 61:
            return LeadCategory.HOT
        elif score >= 31:
            return LeadCategory.WARM
        else:
            return LeadCategory.COLD

    def _generate_recommendations(
        self, 
        score: float, 
        factors: Dict[str, float], 
        profile: CustomerProfile
    ) -> List[str]:
        """Gera recomendações baseadas no score"""
        recommendations = []
        
        if score >= 90:
            recommendations.append("🔥 PRIORIDADE MÁXIMA: Contato imediato")
            recommendations.append("💰 Preparar proposta personalizada")
            recommendations.append("📞 Agendar ligação de fechamento")
        elif score >= 70:
            recommendations.append("⚡ Alta prioridade: Resposta rápida")
            recommendations.append("🎯 Enviar informações detalhadas")
            recommendations.append("📅 Oferecer agendamento prioritário")
        elif score >= 50:
            recommendations.append("📧 Nutrir lead com conteúdo relevante")
            recommendations.append("⏰ Follow-up em 24-48h")
            recommendations.append("🎁 Considerar oferta especial")
        else:
            recommendations.append("📚 Educar sobre benefícios")
            recommendations.append("🔄 Follow-up semanal")
            recommendations.append("👥 Adicionar à campanha de nurturing")
        
        # Recomendações específicas baseadas em fatores
        if factors.get("urgency_indicators", 0) > 5:
            recommendations.append("⚡ Cliente com urgência - priorizar atendimento")
        
        if factors.get("price_sensitivity", 0) > 5:
            recommendations.append("💳 Preparar opções de pagamento flexíveis")
        
        if profile.total_spent > 200:
            recommendations.append("⭐ Cliente VIP - atendimento diferenciado")
        
        return recommendations

    def _calculate_priority(self, score: float, factors: Dict[str, float]) -> int:
        """Calcula nível de prioridade (1-5)"""
        if score >= 90:
            return 5
        elif score >= 75:
            return 4
        elif score >= 60:
            return 3
        elif score >= 40:
            return 2
        else:
            return 1

    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """Calcula confiança na predição"""
        # Mais fatores com valores altos = maior confiança
        non_zero_factors = [f for f in factors.values() if f > 0]
        if not non_zero_factors:
            return 0.3
        
        confidence = min(0.95, 0.4 + (len(non_zero_factors) * 0.08))
        return confidence

    def _suggest_next_actions(
        self, 
        category: LeadCategory, 
        factors: Dict[str, float], 
        profile: CustomerProfile
    ) -> List[str]:
        """Sugere próximas ações"""
        actions = []
        
        if category == LeadCategory.OPPORTUNITY:
            actions = [
                "Ligar imediatamente",
                "Preparar proposta detalhada",
                "Agendar demonstração/consulta",
                "Enviar contrato"
            ]
        elif category == LeadCategory.QUALIFIED:
            actions = [
                "Responder em até 30 minutos",
                "Enviar informações completas",
                "Agendar ligação de qualificação",
                "Preparar orçamento personalizado"
            ]
        elif category == LeadCategory.HOT:
            actions = [
                "Responder em até 2 horas",
                "Enviar materiais informativos",
                "Oferecer consulta gratuita",
                "Agendar follow-up em 24h"
            ]
        elif category == LeadCategory.WARM:
            actions = [
                "Responder em até 4 horas",
                "Nutrir com conteúdo educativo",
                "Agendar follow-up em 48h",
                "Adicionar à sequência de e-mails"
            ]
        else:  # COLD
            actions = [
                "Responder em até 24 horas",
                "Enviar conteúdo introdutório",
                "Adicionar à campanha de nurturing",
                "Follow-up semanal"
            ]
        
        return actions

    def _estimate_value(self, profile: CustomerProfile, factors: Dict[str, float]) -> float:
        """Estima valor potencial do lead"""
        base_value = 50.0  # valor base
        
        # Ajustar baseado no histórico
        if profile.total_spent > 0:
            base_value = profile.total_spent * 1.2  # 20% de crescimento
        
        # Multiplicadores baseados em fatores
        multiplier = 1.0
        
        if factors.get("urgency_indicators", 0) > 5:
            multiplier += 0.3
        
        if factors.get("service_specificity", 0) > 5:
            multiplier += 0.2
        
        if factors.get("decision_authority", 0) > 3:
            multiplier += 0.25
        
        if factors.get("buying_signals", 0) > 3:
            multiplier += 0.15
        
        return base_value * multiplier

    def _calculate_conversion_probability(self, score: float, factors: Dict[str, float]) -> float:
        """Calcula probabilidade de conversão"""
        # Conversão base baseada no score
        base_probability = score / 100
        
        # Ajustes baseados em fatores específicos
        if factors.get("urgency_indicators", 0) > 7:
            base_probability += 0.15
        
        if factors.get("buying_signals", 0) > 3:
            base_probability += 0.1
        
        if factors.get("previous_purchases", 0) > 7:
            base_probability += 0.2
        
        return min(0.98, base_probability)


class LeadScoringService:
    """Serviço de Lead Scoring integrado ao WhatsApp Agent"""
    
    def __init__(self):
        self.engine = LeadScoringEngine()
        self.lead_database = {}  # Cache de leads em memória
        
    def score_lead(
        self, 
        message: str, 
        phone: str, 
        customer_data: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> LeadScore:
        """Interface principal para scoring de leads"""
        
        # Criar ou atualizar perfil do cliente
        profile = self._get_or_create_profile(phone, customer_data)
        
        # Atualizar perfil com nova interação
        self._update_profile_with_interaction(profile, message)
        
        # Calcular score
        lead_score = self.engine.calculate_lead_score(message, profile, context)
        
        # Salvar no cache
        self.lead_database[phone] = {
            "profile": profile,
            "last_score": lead_score,
            "last_updated": datetime.now()
        }
        
        # Log do resultado
        logger.info(f"Lead scored: {phone} - Score: {lead_score.total_score} - Category: {lead_score.category.value}")
        
        return lead_score
    
    def _get_or_create_profile(self, phone: str, customer_data: Dict[str, Any] = None) -> CustomerProfile:
        """Obtém ou cria perfil do cliente"""
        
        if phone in self.lead_database:
            return self.lead_database[phone]["profile"]
        
        # Criar novo perfil
        profile = CustomerProfile(phone=phone)
        
        if customer_data:
            profile.name = customer_data.get("name")
            profile.total_interactions = customer_data.get("total_interactions", 0)
            profile.total_spent = customer_data.get("total_spent", 0.0)
            profile.services_purchased = customer_data.get("services_purchased", [])
            profile.referrals_made = customer_data.get("referrals_made", 0)
            profile.complaints = customer_data.get("complaints", 0)
            profile.no_shows = customer_data.get("no_shows", 0)
            profile.cancellations = customer_data.get("cancellations", 0)
            profile.geographic_location = customer_data.get("location")
        
        return profile
    
    def _update_profile_with_interaction(self, profile: CustomerProfile, message: str):
        """Atualiza perfil com nova interação"""
        profile.total_interactions += 1
        profile.last_interaction = datetime.now()
        
        # Detectar tipo de interação
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["preço", "quanto", "valor"]):
            profile.interaction_history.append(InteractionType.PRICE_INQUIRY)
        elif any(word in message_lower for word in ["agendar", "marcar", "horário"]):
            profile.interaction_history.append(InteractionType.APPOINTMENT_REQUEST)
        elif any(word in message_lower for word in ["problema", "reclamação", "insatisfeito"]):
            profile.interaction_history.append(InteractionType.COMPLAINT)
        elif "olá" in message_lower or "oi" in message_lower:
            profile.interaction_history.append(InteractionType.FIRST_CONTACT)
        else:
            profile.interaction_history.append(InteractionType.SERVICE_INQUIRY)
        
        # Manter apenas últimas 10 interações
        profile.interaction_history = profile.interaction_history[-10:]
    
    def get_lead_analytics(self) -> Dict[str, Any]:
        """Retorna analytics dos leads"""
        if not self.lead_database:
            return {"total_leads": 0}
        
        scores = [data["last_score"].total_score for data in self.lead_database.values()]
        categories = [data["last_score"].category.value for data in self.lead_database.values()]
        
        category_counts = {}
        for category in LeadCategory:
            category_counts[category.value] = categories.count(category.value)
        
        return {
            "total_leads": len(self.lead_database),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "category_distribution": category_counts,
            "hot_leads": len([s for s in scores if s >= 61]),
            "qualified_leads": len([s for s in scores if s >= 81]),
            "opportunities": len([s for s in scores if s >= 96])
        }
    
    def get_top_leads(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna top leads por score"""
        leads = []
        
        for phone, data in self.lead_database.items():
            leads.append({
                "phone": phone,
                "score": data["last_score"].total_score,
                "category": data["last_score"].category.value,
                "priority": data["last_score"].priority_level,
                "estimated_value": data["last_score"].estimated_value,
                "conversion_probability": data["last_score"].conversion_probability,
                "last_updated": data["last_updated"].isoformat()
            })
        
        # Ordenar por score descendente
        leads.sort(key=lambda x: x["score"], reverse=True)
        
        return leads[:limit]


# Instância global do serviço
lead_scoring_service = LeadScoringService()
