"""
Advanced Analytics Engine - Sistema completo de business intelligence
Fornece insights profundos sobre conversão, comportamento temporal e clientes
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text, case
from sqlalchemy.orm import selectinload
import json
import logging
from app.models.database import Appointment, Conversation, Message, User
from app.utils.logger import get_logger

logger = logging.getLogger(__name__)

class AdvancedAnalyticsEngine:
    """Engine avançado para análises de negócio"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        logger.info("🚀 AdvancedAnalyticsEngine inicializado")
    
    async def get_conversion_funnel(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Análise completa do funil de conversão com taxas por etapa
        
        Etapas:
        1. Primeiro Contato (usuários que enviaram primeira mensagem)
        2. Bot Response (usuários que receberam resposta)  
        3. Scheduled (usuários que agendaram)
        4. Confirmed (agendamentos confirmados)
        5. Completed (agendamentos realizados)
        """
        logger.info(f"🔍 Analisando funil de conversão: {start_date} a {end_date}")
        
        try:
            # Etapa 1: Usuários que enviaram primeira mensagem
            first_contact_query = select(func.count(func.distinct(User.id))).select_from(
                User.join(Message)
            ).where(
                and_(
                    Message.direction == 'in',
                    Message.created_at.between(start_date, end_date)
                )
            )
            first_contacts = (await self.session.execute(first_contact_query)).scalar() or 0
            
            # Etapa 2: Usuários que receberam resposta do bot
            bot_responses_query = select(func.count(func.distinct(User.id))).select_from(
                User.join(Message)
            ).where(
                and_(
                    Message.direction == 'out',
                    Message.created_at.between(start_date, end_date)
                )
            )
            bot_responses = (await self.session.execute(bot_responses_query)).scalar() or 0
            
            # Etapa 3: Usuários que agendaram
            scheduled_query = select(func.count(func.distinct(User.id))).select_from(
                User.join(Appointment)
            ).where(
                Appointment.created_at.between(start_date, end_date)
            )
            scheduled = (await self.session.execute(scheduled_query)).scalar() or 0
            
            # Etapa 4: Agendamentos confirmados
            confirmed_query = select(func.count(Appointment.id)).where(
                and_(
                    Appointment.status == 'confirmado',
                    Appointment.created_at.between(start_date, end_date)
                )
            )
            confirmed = (await self.session.execute(confirmed_query)).scalar() or 0
            
            # Etapa 5: Agendamentos realizados
            completed_query = select(func.count(Appointment.id)).where(
                and_(
                    Appointment.status == 'realizado',
                    Appointment.created_at.between(start_date, end_date)
                )
            )
            completed = (await self.session.execute(completed_query)).scalar() or 0
            
            # Cálculo das taxas de conversão
            conversion_rates = {
                "contact_to_response": (bot_responses / first_contacts * 100) if first_contacts > 0 else 0,
                "response_to_schedule": (scheduled / bot_responses * 100) if bot_responses > 0 else 0,
                "contact_to_schedule": (scheduled / first_contacts * 100) if first_contacts > 0 else 0,
                "schedule_to_confirm": (confirmed / scheduled * 100) if scheduled > 0 else 0,
                "confirm_to_complete": (completed / confirmed * 100) if confirmed > 0 else 0,
                "overall_conversion": (completed / first_contacts * 100) if first_contacts > 0 else 0
            }
            
            # Análise de drop-off por etapa
            dropoff_analysis = {
                "contact_to_response_lost": first_contacts - bot_responses,
                "response_to_schedule_lost": bot_responses - scheduled,
                "schedule_to_confirm_lost": scheduled - confirmed,
                "confirm_to_complete_lost": confirmed - completed
            }
            
            result = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "funnel_stages": {
                    "first_contact": first_contacts,
                    "bot_response": bot_responses,
                    "scheduled": scheduled,
                    "confirmed": confirmed,
                    "completed": completed
                },
                "conversion_rates": conversion_rates,
                "dropoff_analysis": dropoff_analysis,
                "funnel_health_score": min(100, conversion_rates["overall_conversion"] * 10),
                "recommendations": self._generate_funnel_recommendations(conversion_rates)
            }
            
            logger.info(f"✅ Funil analisado - Conversão geral: {conversion_rates['overall_conversion']:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na análise do funil: {e}")
            return {"error": str(e), "funnel_stages": {}, "conversion_rates": {}}
    
    async def get_time_based_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Análise temporal detalhada - padrões por hora, dia e semana
        """
        logger.info(f"🕐 Analisando padrões temporais - {days} dias")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Análise por hora do dia (0-23)
            hourly_query = select(
                func.extract('hour', Message.created_at).label('hour'),
                func.count(Message.id).label('message_count'),
                func.count(func.distinct(Message.user_id)).label('unique_users'),
                func.avg(
                    case(
                        (Message.direction == 'out', 1),
                        else_=0
                    )
                ).label('response_rate')
            ).where(
                Message.created_at.between(start_date, end_date)
            ).group_by(func.extract('hour', Message.created_at)).order_by('hour')
            
            hourly_data = []
            result = await self.session.execute(hourly_query)
            for row in result:
                hourly_data.append({
                    "hour": int(row.hour),
                    "hour_formatted": f"{int(row.hour):02d}:00",
                    "messages": int(row.message_count),
                    "unique_users": int(row.unique_users),
                    "response_rate": float(row.response_rate) * 100 if row.response_rate else 0,
                    "efficiency_score": int(row.message_count) / max(1, int(row.unique_users))
                })
            
            # Análise por dia da semana (0=Domingo, 6=Sábado)
            weekly_query = select(
                func.extract('dow', Message.created_at).label('day_of_week'),
                func.count(Message.id).label('message_count'),
                func.count(func.distinct(Message.user_id)).label('unique_users'),
                func.count(func.distinct(
                    case(
                        (Message.direction == 'in', Message.user_id),
                        else_=None
                    )
                )).label('incoming_users')
            ).where(
                Message.created_at.between(start_date, end_date)
            ).group_by(func.extract('dow', Message.created_at)).order_by('day_of_week')
            
            weekly_data = []
            day_names = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
            result = await self.session.execute(weekly_query)
            for row in result:
                day_idx = int(row.day_of_week)
                weekly_data.append({
                    "day_of_week": day_idx,
                    "day_name": day_names[day_idx],
                    "day_abbr": day_names[day_idx][:3],
                    "messages": int(row.message_count),
                    "unique_users": int(row.unique_users),
                    "incoming_users": int(row.incoming_users),
                    "engagement_ratio": int(row.message_count) / max(1, int(row.unique_users))
                })
            
            # Tendências diárias com moving average
            daily_query = select(
                func.date(Message.created_at).label('date'),
                func.count(Message.id).label('message_count'),
                func.count(func.distinct(Message.user_id)).label('unique_users'),
                func.count(case(
                    (Message.direction == 'in', 1),
                    else_=None
                )).label('incoming_messages'),
                func.count(case(
                    (Message.direction == 'out', 1), 
                    else_=None
                )).label('outgoing_messages')
            ).where(
                Message.created_at.between(start_date, end_date)
            ).group_by(func.date(Message.created_at)).order_by(func.date(Message.created_at))
            
            daily_data = []
            result = await self.session.execute(daily_query)
            for row in result:
                daily_data.append({
                    "date": row.date.isoformat(),
                    "date_formatted": row.date.strftime('%d/%m'),
                    "messages": int(row.message_count),
                    "unique_users": int(row.unique_users),
                    "incoming_messages": int(row.incoming_messages),
                    "outgoing_messages": int(row.outgoing_messages),
                    "response_ratio": int(row.outgoing_messages) / max(1, int(row.incoming_messages))
                })
            
            # Cálculo de moving averages
            for i, day in enumerate(daily_data):
                window_start = max(0, i - 6)  # 7-day moving average
                window_data = daily_data[window_start:i+1]
                day["messages_ma7"] = sum(d["messages"] for d in window_data) / len(window_data)
                day["users_ma7"] = sum(d["unique_users"] for d in window_data) / len(window_data)
            
            # Identificar padrões e insights
            peak_hours = sorted(hourly_data, key=lambda x: x['messages'], reverse=True)[:3]
            busiest_days = sorted(weekly_data, key=lambda x: x['messages'], reverse=True)[:3]
            
            # Análise de sazonalidade
            weekend_msgs = sum(d["messages"] for d in weekly_data if d["day_of_week"] in [0, 6])
            weekday_msgs = sum(d["messages"] for d in weekly_data if d["day_of_week"] not in [0, 6])
            
            result = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "hourly_patterns": hourly_data,
                "weekly_patterns": weekly_data,
                "daily_trends": daily_data,
                "insights": {
                    "peak_hours": peak_hours,
                    "busiest_days": busiest_days,
                    "weekend_vs_weekday": {
                        "weekend_messages": weekend_msgs,
                        "weekday_messages": weekday_msgs,
                        "weekend_ratio": weekend_msgs / max(1, weekday_msgs)
                    },
                    "activity_score": sum(h["messages"] for h in hourly_data) / len(hourly_data),
                    "consistency_score": self._calculate_consistency_score(daily_data)
                },
                "recommendations": self._generate_time_recommendations(hourly_data, weekly_data)
            }
            
            logger.info(f"✅ Análise temporal concluída - {len(daily_data)} dias analisados")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na análise temporal: {e}")
            return {"error": str(e), "hourly_patterns": [], "daily_trends": []}
    
    async def get_customer_insights(self, days: int = 30) -> Dict[str, Any]:
        """
        Insights detalhados sobre clientes - segmentação e valor
        """
        logger.info(f"👥 Analisando insights de clientes - {days} dias")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Clientes VIP (múltiplos agendamentos e alto valor)
            vip_query = select(
                User.id,
                User.nome,
                User.telefone,
                func.count(Appointment.id).label('total_appointments'),
                func.sum(
                    case(
                        (Appointment.price.is_not(None), Appointment.price),
                        else_=0
                    )
                ).label('total_spent'),
                func.max(Appointment.created_at).label('last_appointment'),
                func.min(Appointment.created_at).label('first_appointment'),
                func.count(func.distinct(func.date(Appointment.created_at))).label('visit_days')
            ).select_from(
                User.join(Appointment)
            ).where(
                Appointment.created_at >= start_date - timedelta(days=90)  # Expanded window for VIPs
            ).group_by(User.id, User.nome, User.telefone).having(
                func.count(Appointment.id) >= 2  # At least 2 appointments
            ).order_by(desc('total_spent')).limit(20)
            
            vip_customers = []
            result = await self.session.execute(vip_query)
            for row in result:
                days_active = (row.last_appointment - row.first_appointment).days if row.first_appointment and row.last_appointment else 0
                vip_customers.append({
                    "user_id": row.id,
                    "name": row.nome or "N/A",
                    "phone": row.telefone,
                    "appointments": int(row.total_appointments),
                    "total_spent": float(row.total_spent) if row.total_spent else 0,
                    "last_appointment": row.last_appointment.isoformat() if row.last_appointment else None,
                    "first_appointment": row.first_appointment.isoformat() if row.first_appointment else None,
                    "days_active": days_active,
                    "visit_frequency": int(row.visit_days),
                    "avg_order_value": float(row.total_spent) / int(row.total_appointments) if row.total_spent and row.total_appointments else 0,
                    "loyalty_score": min(100, int(row.total_appointments) * 20 + (days_active / 30) * 10)
                })
            
            # Análise de churn (clientes inativos há mais de 60 dias)
            churn_threshold = datetime.now() - timedelta(days=60)
            churn_query = select(
                User.id,
                User.nome,
                User.telefone,
                func.max(Message.created_at).label('last_activity'),
                func.count(Appointment.id).label('total_appointments'),
                func.sum(
                    case(
                        (Appointment.price.is_not(None), Appointment.price),
                        else_=0
                    )
                ).label('lifetime_value')
            ).select_from(
                User.outerjoin(Message).outerjoin(Appointment)
            ).group_by(User.id, User.nome, User.telefone).having(
                and_(
                    func.max(Message.created_at) < churn_threshold,
                    func.count(Appointment.id) > 0  # Had at least one appointment
                )
            ).order_by(desc('lifetime_value')).limit(15)
            
            churned_customers = []
            result = await self.session.execute(churn_query)
            for row in result:
                if row.last_activity:
                    days_inactive = (datetime.now() - row.last_activity).days
                    churned_customers.append({
                        "user_id": row.id,
                        "name": row.nome or "N/A",
                        "phone": row.telefone,
                        "last_activity": row.last_activity.isoformat(),
                        "days_inactive": days_inactive,
                        "total_appointments": int(row.total_appointments),
                        "lifetime_value": float(row.lifetime_value) if row.lifetime_value else 0,
                        "risk_score": min(100, days_inactive * 1.5),
                        "reactivation_priority": "High" if row.lifetime_value and row.lifetime_value > 200 else "Medium"
                    })
            
            # Prospects de alto valor (engajamento sem conversão)
            prospects_query = select(
                User.id,
                User.nome,
                User.telefone,
                func.count(Message.id).label('message_count'),
                func.count(case(
                    (Message.direction == 'in', 1),
                    else_=None
                )).label('incoming_messages'),
                func.max(Message.created_at).label('last_message'),
                func.count(Appointment.id).label('appointments')
            ).select_from(
                User.join(Message).outerjoin(Appointment)
            ).where(
                Message.created_at.between(start_date, end_date)
            ).group_by(User.id, User.nome, User.telefone).having(
                and_(
                    func.count(Message.id) >= 5,  # High engagement
                    func.count(Appointment.id) == 0  # No appointments
                )
            ).order_by(desc('message_count')).limit(15)
            
            high_value_prospects = []
            result = await self.session.execute(prospects_query)
            for row in result:
                engagement_score = min(100, int(row.message_count) * 8)
                high_value_prospects.append({
                    "user_id": row.id,
                    "name": row.nome or "N/A", 
                    "phone": row.telefone,
                    "message_count": int(row.message_count),
                    "incoming_messages": int(row.incoming_messages),
                    "last_message": row.last_message.isoformat() if row.last_message else None,
                    "engagement_score": engagement_score,
                    "conversion_potential": "High" if engagement_score > 60 else "Medium",
                    "days_since_contact": (datetime.now() - row.last_message).days if row.last_message else 0
                })
            
            # Métricas de resumo
            total_customers = len(vip_customers) + len(churned_customers)
            avg_customer_value = sum(c["total_spent"] for c in vip_customers) / len(vip_customers) if vip_customers else 0
            total_ltv = sum(c["total_spent"] for c in vip_customers) + sum(c["lifetime_value"] for c in churned_customers)
            
            result = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "vip_customers": vip_customers[:10],
                "churned_customers": churned_customers[:10], 
                "high_value_prospects": high_value_prospects[:10],
                "customer_summary": {
                    "total_vip": len(vip_customers),
                    "total_churned": len(churned_customers),
                    "total_prospects": len(high_value_prospects),
                    "avg_customer_value": avg_customer_value,
                    "total_lifetime_value": total_ltv,
                    "churn_rate": len(churned_customers) / max(1, total_customers) * 100,
                    "prospect_conversion_opportunity": len(high_value_prospects) * avg_customer_value
                },
                "segmentation": {
                    "high_value": len([c for c in vip_customers if c["total_spent"] > avg_customer_value]),
                    "medium_value": len([c for c in vip_customers if 0 < c["total_spent"] <= avg_customer_value]),
                    "at_risk": len([c for c in churned_customers if c["days_inactive"] < 90]),
                    "lost": len([c for c in churned_customers if c["days_inactive"] >= 90])
                },
                "recommendations": self._generate_customer_recommendations(vip_customers, churned_customers, high_value_prospects)
            }
            
            logger.info(f"✅ Insights de clientes concluídos - {len(vip_customers)} VIPs, {len(high_value_prospects)} prospects")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de clientes: {e}")
            return {"error": str(e), "vip_customers": [], "churned_customers": [], "high_value_prospects": []}
    
    async def get_business_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Métricas de negócio essenciais - ROI, LTV, CAC, etc.
        """
        logger.info(f"📊 Calculando métricas de negócio - {days} dias")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # Revenue metrics
            revenue_query = select(
                func.sum(Appointment.price).label('total_revenue'),
                func.count(Appointment.id).label('total_appointments'),
                func.avg(Appointment.price).label('avg_order_value'),
                func.count(func.distinct(Appointment.user_id)).label('unique_customers')
            ).where(
                and_(
                    Appointment.status.in_(['confirmado', 'realizado']),
                    Appointment.created_at.between(start_date, end_date),
                    Appointment.price.is_not(None)
                )
            )
            
            result = await self.session.execute(revenue_query)
            revenue_data = result.first()
            
            # Customer Acquisition Cost (simplified - messages sent as proxy for marketing spend)
            message_cost_query = select(
                func.count(Message.id).label('total_messages')
            ).where(
                and_(
                    Message.direction == 'out',
                    Message.created_at.between(start_date, end_date)
                )
            )
            
            result = await self.session.execute(message_cost_query)
            total_messages = result.scalar() or 0
            
            # Assume R$0.10 per message sent (WhatsApp Business cost estimate)
            estimated_marketing_spend = total_messages * 0.10
            cac = estimated_marketing_spend / max(1, revenue_data.unique_customers) if revenue_data.unique_customers else 0
            
            # Customer Lifetime Value (30-day window)
            ltv_query = select(
                func.avg(
                    func.sum(Appointment.price)
                ).label('avg_ltv')
            ).select_from(
                Appointment.join(User)
            ).where(
                and_(
                    Appointment.price.is_not(None),
                    Appointment.created_at >= start_date - timedelta(days=90)  # Expanded window
                )
            ).group_by(User.id)
            
            result = await self.session.execute(ltv_query)
            avg_ltv = result.scalar() or 0
            
            # Growth metrics
            previous_period_start = start_date - timedelta(days=days)
            previous_period_end = start_date
            
            prev_revenue_query = select(
                func.sum(Appointment.price).label('prev_revenue'),
                func.count(func.distinct(Appointment.user_id)).label('prev_customers')
            ).where(
                and_(
                    Appointment.status.in_(['confirmado', 'realizado']),
                    Appointment.created_at.between(previous_period_start, previous_period_end),
                    Appointment.price.is_not(None)
                )
            )
            
            result = await self.session.execute(prev_revenue_query)
            prev_data = result.first()
            
            # Calculate growth rates
            revenue_growth = 0
            customer_growth = 0
            
            if prev_data and prev_data.prev_revenue:
                current_revenue = float(revenue_data.total_revenue) if revenue_data.total_revenue else 0
                prev_revenue = float(prev_data.prev_revenue)
                revenue_growth = ((current_revenue - prev_revenue) / prev_revenue) * 100 if prev_revenue > 0 else 0
            
            if prev_data and prev_data.prev_customers:
                current_customers = revenue_data.unique_customers or 0
                prev_customers = prev_data.prev_customers or 0
                customer_growth = ((current_customers - prev_customers) / prev_customers) * 100 if prev_customers > 0 else 0
            
            result = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "revenue_metrics": {
                    "total_revenue": float(revenue_data.total_revenue) if revenue_data.total_revenue else 0,
                    "total_appointments": int(revenue_data.total_appointments) if revenue_data.total_appointments else 0,
                    "avg_order_value": float(revenue_data.avg_order_value) if revenue_data.avg_order_value else 0,
                    "unique_customers": int(revenue_data.unique_customers) if revenue_data.unique_customers else 0,
                    "revenue_per_customer": (float(revenue_data.total_revenue) / revenue_data.unique_customers) if revenue_data.total_revenue and revenue_data.unique_customers else 0
                },
                "customer_metrics": {
                    "customer_acquisition_cost": cac,
                    "customer_lifetime_value": float(avg_ltv),
                    "ltv_to_cac_ratio": float(avg_ltv) / cac if cac > 0 else 0,
                    "estimated_marketing_spend": estimated_marketing_spend
                },
                "growth_metrics": {
                    "revenue_growth_percent": revenue_growth,
                    "customer_growth_percent": customer_growth,
                    "growth_trend": "Positive" if revenue_growth > 0 else "Negative" if revenue_growth < 0 else "Stable"
                },
                "efficiency_metrics": {
                    "messages_per_conversion": total_messages / max(1, revenue_data.unique_customers) if revenue_data.unique_customers else 0,
                    "cost_per_appointment": estimated_marketing_spend / max(1, revenue_data.total_appointments) if revenue_data.total_appointments else 0,
                    "roi_percentage": ((float(revenue_data.total_revenue) - estimated_marketing_spend) / estimated_marketing_spend * 100) if estimated_marketing_spend > 0 and revenue_data.total_revenue else 0
                }
            }
            
            logger.info(f"✅ Métricas de negócio calculadas - ROI: {result['efficiency_metrics']['roi_percentage']:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de métricas: {e}")
            return {"error": str(e), "revenue_metrics": {}, "customer_metrics": {}}
    
    def _generate_funnel_recommendations(self, conversion_rates: Dict) -> List[str]:
        """Gera recomendações baseadas no funil de conversão"""
        recommendations = []
        
        if conversion_rates["contact_to_schedule"] < 20:
            recommendations.append("📞 Taxa de agendamento baixa - revisar scripts do bot e ofertas")
        
        if conversion_rates["schedule_to_confirm"] < 70:
            recommendations.append("✅ Muitos agendamentos não confirmados - implementar lembretes automáticos")
        
        if conversion_rates["confirm_to_complete"] < 80:
            recommendations.append("🎯 Alto no-show - melhorar confirmações e follow-up")
        
        if conversion_rates["overall_conversion"] > 15:
            recommendations.append("🚀 Performance excelente - considerar escalar operação")
        
        return recommendations
    
    def _generate_time_recommendations(self, hourly_data: List, weekly_data: List) -> List[str]:
        """Gera recomendações baseadas em padrões temporais"""
        recommendations = []
        
        peak_hour = max(hourly_data, key=lambda x: x['messages'])['hour']
        if peak_hour < 12:
            recommendations.append("🌅 Pico pela manhã - focar atendimento 8h-12h")
        elif peak_hour > 18:
            recommendations.append("🌙 Pico à noite - considerar atendimento estendido")
        
        weekend_activity = sum(d["messages"] for d in weekly_data if d["day_of_week"] in [0, 6])
        weekday_activity = sum(d["messages"] for d in weekly_data if d["day_of_week"] not in [0, 6])
        
        if weekend_activity > weekday_activity * 0.3:
            recommendations.append("📅 Boa atividade nos finais de semana - manter atendimento")
        
        return recommendations
    
    def _generate_customer_recommendations(self, vips: List, churned: List, prospects: List) -> List[str]:
        """Gera recomendações baseadas em insights de clientes"""
        recommendations = []
        
        if len(vips) > 0:
            recommendations.append(f"👑 {len(vips)} clientes VIP identificados - criar programa de fidelidade")
        
        if len(churned) > 0:
            recommendations.append(f"📧 {len(churned)} clientes inativos - campanha de reativação")
        
        if len(prospects) > 0:
            recommendations.append(f"🎯 {len(prospects)} prospects engajados - ofertas personalizadas")
        
        return recommendations
    
    def _calculate_consistency_score(self, daily_data: List) -> float:
        """Calcula score de consistência da atividade diária"""
        if len(daily_data) < 7:
            return 0
        
        messages = [d["messages"] for d in daily_data]
        avg = sum(messages) / len(messages)
        variance = sum((x - avg) ** 2 for x in messages) / len(messages)
        
        # Normalize variance to 0-100 scale (lower variance = higher consistency)
        consistency = max(0, 100 - (variance / avg * 50)) if avg > 0 else 0
        return round(consistency, 1)
