from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema de Monitoramento de Custos OpenAI
Rastreia uso e custos da API OpenAI em tempo real
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class OpenAICostTracker:
    """Rastreia custos da API OpenAI com persistência e relatórios"""
    
    # Preços atualizados da OpenAI (por 1K tokens)
    PRICES = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "whisper": 0.006,  # por minuto
        "tts": 0.015,      # por 1K caracteres
        "dall-e-3": 0.04,  # por imagem (1024x1024)
        "dall-e-2": 0.02   # por imagem (1024x1024)
    }
    
    def __init__(self, storage_path: str = "logs/cost_tracking.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Dados de uso atual em memória
        self.daily_usage = {}
        self.monthly_usage = {}
        self.session_usage = {
            "gpt-4": {"input": 0, "output": 0, "calls": 0},
            "gpt-4o": {"input": 0, "output": 0, "calls": 0},
            "gpt-4o-mini": {"input": 0, "output": 0, "calls": 0},
            "gpt-3.5-turbo": {"input": 0, "output": 0, "calls": 0},
            "whisper": {"minutes": 0, "calls": 0},
            "tts": {"characters": 0, "calls": 0},
            "dall-e-3": {"images": 0, "calls": 0},
            "dall-e-2": {"images": 0, "calls": 0}
        }
        
        # Configurações de limites
        self.daily_limit_usd = 10.0
        self.monthly_limit_usd = 100.0
        self.alert_threshold = 0.8  # 80% do limite
        
        # Exchange rate para BRL
        self.exchange_rate = 5.0
        
        # Inicializar dados
        self._load_usage_data()
    
    def _load_usage_data(self):
        """Carrega dados de uso do arquivo"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.daily_usage = data.get("daily_usage", {})
                    self.monthly_usage = data.get("monthly_usage", {})
                    self.daily_limit_usd = data.get("daily_limit_usd", 10.0)
                    self.monthly_limit_usd = data.get("monthly_limit_usd", 100.0)
                    self.exchange_rate = data.get("exchange_rate", 5.0)
                    logger.info("✅ Dados de custo carregados com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados de custo: {e}")
    
    def _save_usage_data(self):
        """Salva dados de uso no arquivo"""
        try:
            data = {
                "daily_usage": self.daily_usage,
                "monthly_usage": self.monthly_usage,
                "daily_limit_usd": self.daily_limit_usd,
                "monthly_limit_usd": self.monthly_limit_usd,
                "exchange_rate": self.exchange_rate,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados de custo: {e}")
    
    def track_usage(self, model: str, input_tokens: int = 0, output_tokens: int = 0, 
                   minutes: float = 0, characters: int = 0, images: int = 0):
        """Registra uso de API"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            month = datetime.now().strftime("%Y-%m")
            
            # Inicializar estruturas se necessário
            if today not in self.daily_usage:
                self.daily_usage[today] = {}
            if month not in self.monthly_usage:
                self.monthly_usage[month] = {}
            if model not in self.daily_usage[today]:
                self.daily_usage[today][model] = {"input": 0, "output": 0, "calls": 0, "minutes": 0, "characters": 0, "images": 0}
            if model not in self.monthly_usage[month]:
                self.monthly_usage[month][model] = {"input": 0, "output": 0, "calls": 0, "minutes": 0, "characters": 0, "images": 0}
            
            # Atualizar contadores
            if model in ["gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]:
                # Modelos de texto
                self.session_usage[model]["input"] += input_tokens
                self.session_usage[model]["output"] += output_tokens
                self.session_usage[model]["calls"] += 1
                
                self.daily_usage[today][model]["input"] += input_tokens
                self.daily_usage[today][model]["output"] += output_tokens
                self.daily_usage[today][model]["calls"] += 1
                
                self.monthly_usage[month][model]["input"] += input_tokens
                self.monthly_usage[month][model]["output"] += output_tokens
                self.monthly_usage[month][model]["calls"] += 1
                
            elif model == "whisper":
                # Whisper (áudio)
                self.session_usage[model]["minutes"] += minutes
                self.session_usage[model]["calls"] += 1
                
                self.daily_usage[today][model]["minutes"] += minutes
                self.daily_usage[today][model]["calls"] += 1
                
                self.monthly_usage[month][model]["minutes"] += minutes
                self.monthly_usage[month][model]["calls"] += 1
                
            elif model == "tts":
                # Text-to-Speech
                self.session_usage[model]["characters"] += characters
                self.session_usage[model]["calls"] += 1
                
                self.daily_usage[today][model]["characters"] += characters
                self.daily_usage[today][model]["calls"] += 1
                
                self.monthly_usage[month][model]["characters"] += characters
                self.monthly_usage[month][model]["calls"] += 1
                
            elif model in ["dall-e-3", "dall-e-2"]:
                # DALL-E (imagens)
                self.session_usage[model]["images"] += images
                self.session_usage[model]["calls"] += 1
                
                self.daily_usage[today][model]["images"] += images
                self.daily_usage[today][model]["calls"] += 1
                
                self.monthly_usage[month][model]["images"] += images
                self.monthly_usage[month][model]["calls"] += 1
            
            # Salvar dados
            self._save_usage_data()
            
            # Verificar limites
            self._check_usage_limits()
            
            logger.info(f"📊 Uso registrado: {model} - Tokens: {input_tokens + output_tokens}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar uso: {e}")
    
    def get_session_cost(self) -> float:
        """Calcula custo da sessão atual em USD"""
        total = 0.0
        
        for model, data in self.session_usage.items():
            if model == "whisper":
                total += data["minutes"] * self.PRICES["whisper"] / 60
            elif model == "tts":
                total += (data["characters"] / 1000) * self.PRICES["tts"]
            elif model in ["dall-e-3", "dall-e-2"]:
                total += data["images"] * self.PRICES[model]
            elif model in self.PRICES:
                price = self.PRICES[model]
                total += (data["input"] / 1000) * price["input"]
                total += (data["output"] / 1000) * price["output"]
        
        return total
    
    def get_daily_cost(self, date: str = None) -> float:
        """Calcula custo diário em USD"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if date not in self.daily_usage:
            return 0.0
        
        total = 0.0
        for model, data in self.daily_usage[date].items():
            if model == "whisper":
                total += data["minutes"] * self.PRICES["whisper"] / 60
            elif model == "tts":
                total += (data["characters"] / 1000) * self.PRICES["tts"]
            elif model in ["dall-e-3", "dall-e-2"]:
                total += data["images"] * self.PRICES[model]
            elif model in self.PRICES:
                price = self.PRICES[model]
                total += (data["input"] / 1000) * price["input"]
                total += (data["output"] / 1000) * price["output"]
        
        return total
    
    def get_monthly_cost(self, month: str = None) -> float:
        """Calcula custo mensal em USD"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        
        if month not in self.monthly_usage:
            return 0.0
        
        total = 0.0
        for model, data in self.monthly_usage[month].items():
            if model == "whisper":
                total += data["minutes"] * self.PRICES["whisper"] / 60
            elif model == "tts":
                total += (data["characters"] / 1000) * self.PRICES["tts"]
            elif model in ["dall-e-3", "dall-e-2"]:
                total += data["images"] * self.PRICES[model]
            elif model in self.PRICES:
                price = self.PRICES[model]
                total += (data["input"] / 1000) * price["input"]
                total += (data["output"] / 1000) * price["output"]
        
        return total
    
    def get_cost_in_brl(self, usd_amount: float = None) -> float:
        """Converte custo para reais"""
        if usd_amount is None:
            usd_amount = self.get_session_cost()
        return usd_amount * self.exchange_rate
    
    def _check_usage_limits(self):
        """Verifica se os limites foram atingidos"""
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        
        # Alertas diários
        if daily_cost >= self.daily_limit_usd:
            logger.warning(f"🚨 LIMITE DIÁRIO ATINGIDO: ${daily_cost:.4f} / ${self.daily_limit_usd}")
        elif daily_cost >= self.daily_limit_usd * self.alert_threshold:
            logger.warning(f"⚠️ Alerta diário: ${daily_cost:.4f} / ${self.daily_limit_usd} ({daily_cost/self.daily_limit_usd*100:.1f}%)")
        
        # Alertas mensais
        if monthly_cost >= self.monthly_limit_usd:
            logger.warning(f"🚨 LIMITE MENSAL ATINGIDO: ${monthly_cost:.4f} / ${self.monthly_limit_usd}")
        elif monthly_cost >= self.monthly_limit_usd * self.alert_threshold:
            logger.warning(f"⚠️ Alerta mensal: ${monthly_cost:.4f} / ${self.monthly_limit_usd} ({monthly_cost/self.monthly_limit_usd*100:.1f}%)")
    
    def get_detailed_report(self) -> Dict:
        """Gera relatório detalhado de custos"""
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m")
        
        session_cost = self.get_session_cost()
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        
        return {
            "session": {
                "cost_usd": session_cost,
                "cost_brl": self.get_cost_in_brl(session_cost),
                "usage": self.session_usage
            },
            "daily": {
                "date": today,
                "cost_usd": daily_cost,
                "cost_brl": self.get_cost_in_brl(daily_cost),
                "limit_usd": self.daily_limit_usd,
                "limit_brl": self.daily_limit_usd * self.exchange_rate,
                "usage_percentage": (daily_cost / self.daily_limit_usd * 100) if self.daily_limit_usd > 0 else 0,
                "usage": self.daily_usage.get(today, {})
            },
            "monthly": {
                "month": month,
                "cost_usd": monthly_cost,
                "cost_brl": self.get_cost_in_brl(monthly_cost),
                "limit_usd": self.monthly_limit_usd,
                "limit_brl": self.monthly_limit_usd * self.exchange_rate,
                "usage_percentage": (monthly_cost / self.monthly_limit_usd * 100) if self.monthly_limit_usd > 0 else 0,
                "usage": self.monthly_usage.get(month, {})
            },
            "settings": {
                "exchange_rate": self.exchange_rate,
                "daily_limit_usd": self.daily_limit_usd,
                "monthly_limit_usd": self.monthly_limit_usd,
                "alert_threshold": self.alert_threshold
            }
        }
    
    def update_settings(self, daily_limit_usd: float = None, monthly_limit_usd: float = None, 
                       exchange_rate: float = None, alert_threshold: float = None):
        """Atualiza configurações de limites"""
        if daily_limit_usd is not None:
            self.daily_limit_usd = daily_limit_usd
        if monthly_limit_usd is not None:
            self.monthly_limit_usd = monthly_limit_usd
        if exchange_rate is not None:
            self.exchange_rate = exchange_rate
        if alert_threshold is not None:
            self.alert_threshold = alert_threshold
        
        # Salvar configurações
        self._save_usage_data()
        logger.info("✅ Configurações de custo atualizadas")
    
    def reset_session_usage(self):
        """Reseta contadores da sessão"""
        for model in self.session_usage:
            if isinstance(self.session_usage[model], dict):
                for key in self.session_usage[model]:
                    self.session_usage[model][key] = 0
        logger.info("🔄 Contadores de sessão resetados")
    
    def get_cost_projection(self, days_ahead: int = 30) -> Dict:
        """Projeta custos futuros baseado no uso atual"""
        try:
            # Calcular média dos últimos 7 dias
            daily_costs = []
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_costs.append(self.get_daily_cost(date))
            
            avg_daily_cost = sum(daily_costs) / len(daily_costs) if daily_costs else 0
            
            projected_monthly = avg_daily_cost * 30
            projected_custom = avg_daily_cost * days_ahead
            
            return {
                "average_daily_cost_usd": avg_daily_cost,
                "average_daily_cost_brl": avg_daily_cost * self.exchange_rate,
                "projected_monthly_usd": projected_monthly,
                "projected_monthly_brl": projected_monthly * self.exchange_rate,
                f"projected_{days_ahead}days_usd": projected_custom,
                f"projected_{days_ahead}days_brl": projected_custom * self.exchange_rate,
                "within_monthly_limit": projected_monthly <= self.monthly_limit_usd,
                "risk_level": "high" if projected_monthly > self.monthly_limit_usd else "medium" if projected_monthly > self.monthly_limit_usd * 0.8 else "low"
            }
        except Exception as e:
            logger.error(f"❌ Erro ao calcular projeção: {e}")
            return {}

# Instância global do tracker
cost_tracker = OpenAICostTracker()
