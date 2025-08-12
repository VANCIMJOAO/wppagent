#!/usr/bin/env python3
"""
Health Check Script para WhatsApp Agent
Verificações abrangentes de saúde do sistema
"""

import asyncio
import sys
import json
import time
import httpx
import psutil
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import text
from app.database import get_async_engine
from app.config import settings

class HealthChecker:
    def __init__(self):
        self.checks = []
        self.start_time = time.time()
    
    async def check_database(self) -> Dict[str, Any]:
        """Verificar conectividade e performance do banco"""
        try:
            engine = get_async_engine()
            start = time.time()
            
            async with engine.begin() as conn:
                # Teste básico de conectividade
                await conn.execute(text("SELECT 1"))
                
                # Verificar tabelas principais
                tables_check = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('users', 'messages', 'conversations')
                """))
                tables = [row[0] for row in tables_check]
                
                # Verificar contadores básicos
                stats = {}
                for table in ['users', 'messages', 'conversations']:
                    if table in tables:
                        count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        stats[f"{table}_count"] = count_result.scalar()
                
                # Verificar conexões ativas
                connections_result = await conn.execute(text("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active' AND datname = current_database()
                """))
                active_connections = connections_result.scalar()
                
            response_time = time.time() - start
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "tables_found": tables,
                "stats": stats,
                "active_connections": active_connections,
                "details": "Database connection successful"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "Database connection failed"
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Verificar Redis/Cache"""
        try:
            import redis.asyncio as redis
            
            redis_client = redis.from_url(settings.redis_url if hasattr(settings, 'redis_url') else "redis://localhost:6379")
            start = time.time()
            
            # Test ping
            await redis_client.ping()
            
            # Test set/get
            test_key = "health_check_test"
            await redis_client.set(test_key, "test_value", ex=30)
            value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            
            # Get info
            info = await redis_client.info()
            
            response_time = time.time() - start
            
            await redis_client.aclose()
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "details": "Redis connection successful"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "Redis connection failed"
            }
    
    async def check_api_endpoints(self) -> Dict[str, Any]:
        """Verificar endpoints críticos da API"""
        try:
            base_url = f"http://localhost:{settings.app_port}"
            endpoints = [
                "/",
                "/health",
                "/docs"
            ]
            
            results = {}
            async with httpx.AsyncClient(timeout=10.0) as client:
                for endpoint in endpoints:
                    try:
                        start = time.time()
                        response = await client.get(f"{base_url}{endpoint}")
                        response_time = time.time() - start
                        
                        results[endpoint] = {
                            "status": "healthy" if response.status_code < 400 else "unhealthy",
                            "status_code": response.status_code,
                            "response_time_ms": round(response_time * 1000, 2)
                        }
                    except Exception as e:
                        results[endpoint] = {
                            "status": "unhealthy",
                            "error": str(e)
                        }
            
            all_healthy = all(r.get("status") == "healthy" for r in results.values())
            
            return {
                "status": "healthy" if all_healthy else "unhealthy",
                "endpoints": results,
                "details": "API endpoints check completed"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "API endpoints check failed"
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Verificar recursos do sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memória
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('/')
            
            # Load average (apenas Unix)
            try:
                load_avg = psutil.getloadavg()
            except:
                load_avg = [0, 0, 0]
            
            # Determinar status baseado em thresholds
            warnings = []
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 85:
                warnings.append(f"High memory usage: {memory.percent}%")
            if disk.percent > 90:
                warnings.append(f"High disk usage: {disk.percent}%")
            
            status = "unhealthy" if warnings else "healthy"
            
            return {
                "status": status,
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": load_avg
                },
                "memory": {
                    "percent": memory.percent,
                    "total_gb": round(memory.total / 1024**3, 2),
                    "available_gb": round(memory.available / 1024**3, 2),
                    "used_gb": round(memory.used / 1024**3, 2)
                },
                "disk": {
                    "percent": disk.percent,
                    "total_gb": round(disk.total / 1024**3, 2),
                    "free_gb": round(disk.free / 1024**3, 2),
                    "used_gb": round(disk.used / 1024**3, 2)
                },
                "warnings": warnings,
                "details": "System resources check completed"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "System resources check failed"
            }
    
    async def check_whatsapp_api(self) -> Dict[str, Any]:
        """Verificar conectividade com WhatsApp API"""
        try:
            if not hasattr(settings, 'meta_access_token') or not settings.meta_access_token:
                return {
                    "status": "warning",
                    "details": "WhatsApp API token not configured"
                }
            
            # Test Meta API connectivity
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.time()
                response = await client.get(
                    f"https://graph.facebook.com/v18.0/{settings.phone_number_id}",
                    headers={"Authorization": f"Bearer {settings.meta_access_token}"}
                )
                response_time = time.time() - start
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "response_time_ms": round(response_time * 1000, 2),
                        "phone_number_id": settings.phone_number_id,
                        "details": "WhatsApp API connection successful"
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "details": "WhatsApp API connection failed"
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "details": "WhatsApp API check failed"
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Executar todas as verificações"""
        checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "api_endpoints": await self.check_api_endpoints(),
            "system_resources": self.check_system_resources(),
            "whatsapp_api": await self.check_whatsapp_api()
        }
        
        # Determinar status geral
        statuses = [check.get("status", "unknown") for check in checks.values()]
        
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        # Contar checks
        healthy_count = statuses.count("healthy")
        warning_count = statuses.count("warning")
        unhealthy_count = statuses.count("unhealthy")
        
        total_time = time.time() - self.start_time
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(checks),
            "healthy": healthy_count,
            "warnings": warning_count,
            "unhealthy": unhealthy_count,
            "total_time_ms": round(total_time * 1000, 2),
            "checks": checks,
            "version": getattr(settings, 'version', '1.0.0'),
            "environment": getattr(settings, 'environment', 'unknown')
        }

async def main():
    """Função principal do health check"""
    checker = HealthChecker()
    
    try:
        result = await checker.run_all_checks()
        
        # Output JSON
        print(json.dumps(result, indent=2))
        
        # Exit code baseado no status
        if result["status"] == "healthy":
            sys.exit(0)
        elif result["status"] == "warning":
            sys.exit(1)  # Warning ainda é considerado ok para health check
        else:
            sys.exit(2)  # Unhealthy
            
    except Exception as e:
        error_result = {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "details": "Health check script failed"
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
