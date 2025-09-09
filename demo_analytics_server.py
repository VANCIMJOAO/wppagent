"""
Analytics Endpoints com Mock Data
Sistema simplificado para demonstrar o sistema de analytics sem depender de banco PostgreSQL
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional
import json
import uuid
import random

# App FastAPI simplificada
app = FastAPI(
    title="WhatsApp Agent Analytics API",
    description="API de Analytics em Modo Demo",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.railway.app",
        "*"  # Para desenvolvimento
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulação de dados
def generate_dashboard_summary(days: int = 30):
    """Gera dados simulados para dashboard summary"""
    base_date = datetime.now()
    
    # Métricas principais
    total_customers = random.randint(800, 1200)
    total_conversations = random.randint(1500, 2500)
    total_messages = random.randint(5000, 8000)
    total_appointments = random.randint(300, 600)
    
    return {
        "key_metrics": {
            "total_customers": total_customers,
            "total_messages": total_messages,
            "total_conversations": total_conversations,
            "total_appointments": total_appointments,
            "overall_conversion_rate": round(random.uniform(15.5, 25.8), 1),
            "avg_response_time_minutes": round(random.uniform(2.5, 8.2), 1),
            "satisfaction_score": round(random.uniform(4.2, 4.8), 1),
        },
        "funnel": {
            "stages": [
                {
                    "stage": "Visitantes",
                    "count": total_customers * 3,
                    "conversionRate": 100.0,
                    "previousStage": 0
                },
                {
                    "stage": "Contatos Iniciados",
                    "count": total_customers,
                    "conversionRate": 33.3,
                    "previousStage": total_customers * 3
                },
                {
                    "stage": "Conversas Ativas",
                    "count": total_conversations,
                    "conversionRate": 66.7,
                    "previousStage": total_customers
                },
                {
                    "stage": "Agendamentos",
                    "count": total_appointments,
                    "conversionRate": 25.0,
                    "previousStage": total_conversations
                }
            ],
            "overall_conversion": round((total_appointments / (total_customers * 3)) * 100, 1),
            "total_visitors": total_customers * 3,
            "total_conversions": total_appointments
        },
        "channel_performance": [
            {
                "channel": "WhatsApp Web",
                "conversations": random.randint(800, 1200),
                "messages": random.randint(2500, 3500),
                "avgResponseTime": round(random.uniform(2.1, 4.5), 1),
                "satisfaction": round(random.uniform(4.3, 4.7), 1)
            },
            {
                "channel": "WhatsApp Mobile",
                "conversations": random.randint(600, 900),
                "messages": random.randint(1800, 2800),
                "avgResponseTime": round(random.uniform(3.2, 6.1), 1),
                "satisfaction": round(random.uniform(4.1, 4.6), 1)
            },
            {
                "channel": "API Integration",
                "conversations": random.randint(200, 400),
                "messages": random.randint(600, 1200),
                "avgResponseTime": round(random.uniform(1.5, 3.2), 1),
                "satisfaction": round(random.uniform(4.4, 4.9), 1)
            }
        ],
        "satisfaction_breakdown": [
            {"rating": 5, "count": random.randint(300, 500), "percentage": 65.2, "trend": 2.1},
            {"rating": 4, "count": random.randint(150, 250), "percentage": 23.8, "trend": 1.5},
            {"rating": 3, "count": random.randint(50, 100), "percentage": 8.3, "trend": -0.8},
            {"rating": 2, "count": random.randint(10, 30), "percentage": 2.1, "trend": -1.2},
            {"rating": 1, "count": random.randint(5, 15), "percentage": 0.6, "trend": -0.3}
        ],
        "trends": {
            "conversations": round(random.uniform(-5.2, 15.8), 1),
            "responseTime": round(random.uniform(-12.3, 8.1), 1),
            "satisfaction": round(random.uniform(-2.1, 5.4), 1)
        },
        "time_series": [
            {
                "date": (base_date - timedelta(days=i)).strftime("%Y-%m-%d"),
                "conversations": random.randint(50, 120),
                "messages": random.randint(150, 400),
                "responses": random.randint(140, 380),
                "responseRate": round(random.uniform(85.5, 96.2), 1)
            }
            for i in range(days)
        ],
        "period": {
            "start_date": (base_date - timedelta(days=days)).strftime("%Y-%m-%d"),
            "end_date": base_date.strftime("%Y-%m-%d"),
            "days": days
        }
    }

def generate_conversion_funnel(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Gera dados simulados do funil de conversão"""
    visitors = random.randint(2500, 4000)
    leads = int(visitors * random.uniform(0.25, 0.40))
    qualified = int(leads * random.uniform(0.65, 0.85))
    appointments = int(qualified * random.uniform(0.35, 0.55))
    
    return {
        "stages": [
            {
                "stage": "Visitantes do Site",
                "count": visitors,
                "conversionRate": 100.0,
                "previousStage": 0
            },
            {
                "stage": "Leads Capturados",
                "count": leads,
                "conversionRate": round((leads / visitors) * 100, 1),
                "previousStage": visitors
            },
            {
                "stage": "Leads Qualificados",
                "count": qualified,
                "conversionRate": round((qualified / leads) * 100, 1),
                "previousStage": leads
            },
            {
                "stage": "Agendamentos Realizados",
                "count": appointments,
                "conversionRate": round((appointments / qualified) * 100, 1),
                "previousStage": qualified
            }
        ],
        "overall_conversion": round((appointments / visitors) * 100, 1),
        "total_visitors": visitors,
        "total_conversions": appointments
    }

def generate_template_performance(days: int = 30):
    """Gera dados simulados de performance de templates"""
    templates = [
        "Boas-vindas Inicial",
        "Agendamento de Consulta",
        "Confirmação de Horário",
        "Lembrete de Consulta",
        "Feedback Pós-Atendimento",
        "Promoção Mensal",
        "FAQ Automatizada",
        "Encerramento de Conversa"
    ]
    
    return {
        "templates": [
            {
                "template_name": template,
                "usage_count": random.randint(150, 800),
                "unique_users": random.randint(100, 600),
                "response_rate": round(random.uniform(72.5, 95.8), 1),
                "conversion_rate": round(random.uniform(12.3, 45.7), 1),
                "avg_response_time": round(random.uniform(1.5, 8.2), 1),
                "effectiveness_score": round(random.uniform(3.8, 4.9), 1)
            }
            for template in templates
        ],
        "period": {
            "start_date": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d")
        },
        "total_templates_analyzed": len(templates)
    }

def generate_time_series(days: int = 30, granularity: str = "daily", metrics: str = "conversations,messages"):
    """Gera dados simulados de série temporal"""
    base_date = datetime.now()
    metric_list = metrics.split(",")
    
    data_points = []
    for i in range(days):
        current_date = base_date - timedelta(days=i)
        point = {
            "period": granularity,
            "date": current_date.strftime("%Y-%m-%d")
        }
        
        if "conversations" in metric_list:
            point["conversations"] = random.randint(45, 150)
        if "messages" in metric_list:
            point["messages"] = random.randint(200, 600)
        if "appointments" in metric_list:
            point["appointments"] = random.randint(15, 80)
            
        data_points.append(point)
    
    return {
        "data": sorted(data_points, key=lambda x: x["date"]),
        "metadata": {
            "period": {
                "start": (base_date - timedelta(days=days)).strftime("%Y-%m-%d"),
                "end": base_date.strftime("%Y-%m-%d")
            },
            "granularity": granularity,
            "metrics": metric_list,
            "total_data_points": len(data_points)
        }
    }

# Endpoints
@app.get("/api/analytics/dashboard-summary")
async def dashboard_summary(days: int = Query(30, ge=1, le=365)):
    """Endpoint principal do dashboard - resumo completo"""
    try:
        data = generate_dashboard_summary(days)
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "message": f"Dashboard summary for {days} days generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard summary: {str(e)}")

@app.get("/api/analytics/conversion-funnel")
async def conversion_funnel(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Endpoint do funil de conversão"""
    try:
        data = generate_conversion_funnel(start_date, end_date)
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "message": "Conversion funnel data generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating conversion funnel: {str(e)}")

@app.get("/api/analytics/template-performance")
async def template_performance(days: int = Query(30, ge=1, le=365)):
    """Endpoint de performance de templates"""
    try:
        data = generate_template_performance(days)
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "message": f"Template performance for {days} days generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating template performance: {str(e)}")

@app.get("/api/analytics/time-series")
async def time_series(
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("daily"),
    metrics: str = Query("conversations,messages")
):
    """Endpoint de dados de série temporal"""
    try:
        data = generate_time_series(days, granularity, metrics)
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "message": f"Time series data for {days} days generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating time series: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "whatsapp-agent-analytics",
        "version": "1.0.0-demo",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/analytics/dashboard-summary",
            "/api/analytics/conversion-funnel", 
            "/api/analytics/template-performance",
            "/api/analytics/time-series"
        ]
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "WhatsApp Agent Analytics API - Demo Version",
        "status": "running",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
