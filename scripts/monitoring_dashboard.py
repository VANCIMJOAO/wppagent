#!/usr/bin/env python3
"""
📊 DASHBOARD DE MONITORAMENTO WEB
================================

Dashboard web para visualização do sistema de monitoramento
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import asyncio
import psutil
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any
import uvicorn

sys.path.append('/home/vancim/whats_agent')

app = FastAPI(title="WhatsApp Agent - Dashboard de Monitoramento")

# Configurar templates
templates_dir = Path("/home/vancim/whats_agent/templates")
templates_dir.mkdir(exist_ok=True)

# Criar template HTML se não existir
dashboard_template = """
<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp Agent - Dashboard de Monitoramento</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { 
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            text-align: center;
        }
        .header h1 { color: #2c3e50; margin-bottom: 10px; }
        .status-indicator { 
            display: inline-block;
            width: 12px; height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online { background: #27ae60; }
        .status-warning { background: #f39c12; }
        .status-critical { background: #e74c3c; }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); }
        .card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        .card-icon {
            font-size: 1.5em;
            margin-right: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #ecf0f1;
        }
        .metric:last-child { border-bottom: none; }
        .metric-value {
            font-weight: bold;
            color: #2980b9;
        }
        .metric-critical { color: #e74c3c; }
        .metric-warning { color: #f39c12; }
        .metric-good { color: #27ae60; }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #ecf0f1;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #27ae60, #f39c12, #e74c3c);
            transition: width 0.3s ease;
        }
        
        .alert-item {
            background: #fff;
            border-left: 4px solid #e74c3c;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .alert-warning { border-left-color: #f39c12; }
        .alert-info { border-left-color: #3498db; }
        
        .log-container {
            background: #2c3e50;
            color: #ecf0f1;
            border-radius: 10px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            max-height: 300px;
            overflow-y: auto;
            font-size: 12px;
        }
        
        .auto-refresh {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(52, 152, 219, 0.9);
            color: white;
            padding: 10px 15px;
            border-radius: 25px;
            border: none;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .auto-refresh:hover {
            background: rgba(52, 152, 219, 1);
            transform: scale(1.05);
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .updating { animation: pulse 1s infinite; }
    </style>
</head>
<body>
    <button class="auto-refresh" onclick="toggleAutoRefresh()">🔄 Auto Refresh: ON</button>
    
    <div class="container">
        <div class="header">
            <h1>🔍 WhatsApp Agent - Dashboard de Monitoramento</h1>
            <p>
                <span class="status-indicator status-online"></span>
                Sistema Online - Última atualização: <span id="lastUpdate">Carregando...</span>
            </p>
        </div>
        
        <div class="dashboard-grid">
            <!-- Sistema -->
            <div class="card">
                <h3><span class="card-icon">🖥️</span>Sistema</h3>
                <div class="metric">
                    <span>CPU</span>
                    <span class="metric-value" id="cpu-usage">-%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpu-progress" style="width: 0%"></div>
                </div>
                
                <div class="metric">
                    <span>Memória</span>
                    <span class="metric-value" id="memory-usage">-%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memory-progress" style="width: 0%"></div>
                </div>
                
                <div class="metric">
                    <span>Disco</span>
                    <span class="metric-value" id="disk-usage">-%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="disk-progress" style="width: 0%"></div>
                </div>
            </div>
            
            <!-- Serviços -->
            <div class="card">
                <h3><span class="card-icon">⚙️</span>Serviços</h3>
                <div class="metric">
                    <span>WhatsApp Agent API</span>
                    <span class="metric-value" id="api-status">Verificando...</span>
                </div>
                <div class="metric">
                    <span>PostgreSQL</span>
                    <span class="metric-value" id="postgres-status">Verificando...</span>
                </div>
                <div class="metric">
                    <span>Redis</span>
                    <span class="metric-value" id="redis-status">Verificando...</span>
                </div>
                <div class="metric">
                    <span>Sistema de Monitoramento</span>
                    <span class="metric-value metric-good">Online</span>
                </div>
            </div>
            
            <!-- Segurança -->
            <div class="card">
                <h3><span class="card-icon">🔒</span>Segurança</h3>
                <div class="metric">
                    <span>Certificados SSL</span>
                    <span class="metric-value" id="ssl-status">Verificando...</span>
                </div>
                <div class="metric">
                    <span>Firewall</span>
                    <span class="metric-value" id="firewall-status">Verificando...</span>
                </div>
                <div class="metric">
                    <span>Últimas tentativas de login</span>
                    <span class="metric-value" id="login-attempts">0</span>
                </div>
                <div class="metric">
                    <span>Vulnerabilidades</span>
                    <span class="metric-value" id="vulnerabilities">Escaneando...</span>
                </div>
            </div>
            
            <!-- Alertas Ativos -->
            <div class="card">
                <h3><span class="card-icon">🚨</span>Alertas Ativos</h3>
                <div id="active-alerts">
                    <div class="alert-item alert-info">
                        Sistema de monitoramento iniciado com sucesso
                    </div>
                </div>
            </div>
            
            <!-- Métricas de Negócio -->
            <div class="card">
                <h3><span class="card-icon">📊</span>Métricas de Negócio</h3>
                <div class="metric">
                    <span>Conversas Hoje</span>
                    <span class="metric-value" id="conversations-today">0</span>
                </div>
                <div class="metric">
                    <span>Mensagens Processadas</span>
                    <span class="metric-value" id="messages-today">0</span>
                </div>
                <div class="metric">
                    <span>Agendamentos</span>
                    <span class="metric-value" id="appointments-today">0</span>
                </div>
                <div class="metric">
                    <span>Tempo Médio Resposta</span>
                    <span class="metric-value" id="avg-response-time">0ms</span>
                </div>
            </div>
            
            <!-- Logs Recentes -->
            <div class="card">
                <h3><span class="card-icon">📝</span>Logs Recentes</h3>
                <div class="log-container" id="recent-logs">
                    Carregando logs recentes...
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let autoRefresh = true;
        let refreshInterval;
        
        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            const button = document.querySelector('.auto-refresh');
            button.textContent = `🔄 Auto Refresh: ${autoRefresh ? 'ON' : 'OFF'}`;
            
            if (autoRefresh) {
                startAutoRefresh();
            } else {
                clearInterval(refreshInterval);
            }
        }
        
        function startAutoRefresh() {
            refreshInterval = setInterval(updateDashboard, 5000); // 5 segundos
        }
        
        async function updateDashboard() {
            const container = document.querySelector('.container');
            container.classList.add('updating');
            
            try {
                const response = await fetch('/api/dashboard-data');
                const data = await response.json();
                
                updateSystemMetrics(data.system);
                updateServices(data.services);
                updateSecurity(data.security);
                updateAlerts(data.alerts);
                updateBusinessMetrics(data.business);
                updateLogs(data.logs);
                
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                
            } catch (error) {
                console.error('Erro ao atualizar dashboard:', error);
            }
            
            container.classList.remove('updating');
        }
        
        function updateSystemMetrics(system) {
            // CPU
            const cpuUsage = system.cpu_percent || 0;
            document.getElementById('cpu-usage').textContent = `${cpuUsage.toFixed(1)}%`;
            document.getElementById('cpu-progress').style.width = `${cpuUsage}%`;
            document.getElementById('cpu-usage').className = `metric-value ${getStatusClass(cpuUsage, 85, 95)}`;
            
            // Memória
            const memoryUsage = system.memory_percent || 0;
            document.getElementById('memory-usage').textContent = `${memoryUsage.toFixed(1)}%`;
            document.getElementById('memory-progress').style.width = `${memoryUsage}%`;
            document.getElementById('memory-usage').className = `metric-value ${getStatusClass(memoryUsage, 85, 95)}`;
            
            // Disco
            const diskUsage = system.disk_percent || 0;
            document.getElementById('disk-usage').textContent = `${diskUsage.toFixed(1)}%`;
            document.getElementById('disk-progress').style.width = `${diskUsage}%`;
            document.getElementById('disk-usage').className = `metric-value ${getStatusClass(diskUsage, 85, 95)}`;
        }
        
        function updateServices(services) {
            document.getElementById('api-status').textContent = services.api || 'Offline';
            document.getElementById('api-status').className = `metric-value ${services.api === 'Online' ? 'metric-good' : 'metric-critical'}`;
            
            document.getElementById('postgres-status').textContent = services.postgres || 'Offline';
            document.getElementById('postgres-status').className = `metric-value ${services.postgres === 'Online' ? 'metric-good' : 'metric-critical'}`;
            
            document.getElementById('redis-status').textContent = services.redis || 'Offline';
            document.getElementById('redis-status').className = `metric-value ${services.redis === 'Online' ? 'metric-good' : 'metric-critical'}`;
        }
        
        function updateSecurity(security) {
            document.getElementById('ssl-status').textContent = security.ssl || 'Desconhecido';
            document.getElementById('firewall-status').textContent = security.firewall || 'Desconhecido';
            document.getElementById('login-attempts').textContent = security.login_attempts || 0;
            document.getElementById('vulnerabilities').textContent = security.vulnerabilities || 0;
        }
        
        function updateAlerts(alerts) {
            const container = document.getElementById('active-alerts');
            if (alerts.length === 0) {
                container.innerHTML = '<div class="alert-item alert-info">Nenhum alerta ativo</div>';
            } else {
                container.innerHTML = alerts.map(alert => 
                    `<div class="alert-item alert-${alert.severity.toLowerCase()}">
                        <strong>${alert.severity}:</strong> ${alert.message}
                        <br><small>${new Date(alert.timestamp).toLocaleString()}</small>
                    </div>`
                ).join('');
            }
        }
        
        function updateBusinessMetrics(business) {
            document.getElementById('conversations-today').textContent = business.conversations || 0;
            document.getElementById('messages-today').textContent = business.messages || 0;
            document.getElementById('appointments-today').textContent = business.appointments || 0;
            document.getElementById('avg-response-time').textContent = `${business.avg_response_time || 0}ms`;
        }
        
        function updateLogs(logs) {
            const container = document.getElementById('recent-logs');
            container.innerHTML = logs.join('\\n');
            container.scrollTop = container.scrollHeight;
        }
        
        function getStatusClass(value, warning, critical) {
            if (value >= critical) return 'metric-critical';
            if (value >= warning) return 'metric-warning';
            return 'metric-good';
        }
        
        // Inicializar
        updateDashboard();
        startAutoRefresh();
    </script>
</body>
</html>
"""

# Salvar template
with open(templates_dir / "dashboard.html", "w", encoding="utf-8") as f:
    f.write(dashboard_template)

templates = Jinja2Templates(directory=str(templates_dir))

class DashboardData:
    """Classe para coletar dados do dashboard"""
    
    @staticmethod
    async def get_system_metrics():
        """Obter métricas do sistema"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": (disk.used / disk.total) * 100,
            "disk_free_gb": disk.free / (1024**3)
        }
    
    @staticmethod
    async def check_services():
        """Verificar status dos serviços"""
        import socket
        import httpx
        
        services = {
            "api": "Offline",
            "postgres": "Offline", 
            "redis": "Offline"
        }
        
        # Verificar API
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get("http://localhost:8000/health")
                services["api"] = "Online" if response.status_code == 200 else "Offline"
        except:
            services["api"] = "Offline"
        
        # Verificar PostgreSQL
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 5432))
            services["postgres"] = "Online" if result == 0 else "Offline"
            sock.close()
        except:
            services["postgres"] = "Offline"
        
        # Verificar Redis
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 6379))
            services["redis"] = "Online" if result == 0 else "Offline"
            sock.close()
        except:
            services["redis"] = "Offline"
        
        return services
    
    @staticmethod
    async def get_security_status():
        """Obter status de segurança"""
        # Verificar certificados SSL
        ssl_status = "Válido"
        try:
            import subprocess
            result = subprocess.run([
                "openssl", "x509", "-in", "/home/vancim/whats_agent/config/postgres/ssl/server.crt",
                "-noout", "-enddate"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                ssl_status = "Não encontrado"
        except:
            ssl_status = "Erro na verificação"
        
        # Verificar firewall
        firewall_status = "Desconhecido"
        try:
            result = subprocess.run(["sudo", "ufw", "status"], capture_output=True, text=True)
            if "active" in result.stdout.lower():
                firewall_status = "Ativo"
            elif "inactive" in result.stdout.lower():
                firewall_status = "Inativo"
        except:
            pass
        
        # Contar tentativas de login recentes
        login_attempts = 0
        try:
            access_log = Path("/home/vancim/whats_agent/logs/audit/access_audit.log")
            if access_log.exists():
                with open(access_log, 'r') as f:
                    lines = f.readlines()[-100:]  # Últimas 100 linhas
                login_attempts = sum(1 for line in lines if '"status": 401' in line)
        except:
            pass
        
        # Contar vulnerabilidades
        vulnerabilities = 0
        try:
            vuln_dir = Path("/home/vancim/whats_agent/logs/vulnerabilities")
            if vuln_dir.exists():
                vuln_files = list(vuln_dir.glob("vulnerability_scan_*.json"))
                if vuln_files:
                    latest_scan = max(vuln_files, key=lambda f: f.stat().st_mtime)
                    with open(latest_scan, 'r') as f:
                        scan_data = json.load(f)
                        vulnerabilities = scan_data.get("summary", {}).get("total", 0)
        except:
            pass
        
        return {
            "ssl": ssl_status,
            "firewall": firewall_status,
            "login_attempts": login_attempts,
            "vulnerabilities": vulnerabilities
        }
    
    @staticmethod
    async def get_active_alerts():
        """Obter alertas ativos"""
        alerts = []
        
        try:
            alerts_file = Path("/home/vancim/whats_agent/logs/alerts/active_alerts.json")
            if alerts_file.exists():
                with open(alerts_file, 'r') as f:
                    alerts_data = json.load(f)
                    alerts = alerts_data.get("alerts", [])
        except:
            pass
        
        return alerts
    
    @staticmethod
    async def get_business_metrics():
        """Obter métricas de negócio simuladas"""
        # Em produção, isso viria do banco de dados
        return {
            "conversations": 42,
            "messages": 187,
            "appointments": 12,
            "avg_response_time": 245
        }
    
    @staticmethod
    async def get_recent_logs():
        """Obter logs recentes"""
        logs = []
        
        try:
            log_file = Path("/home/vancim/whats_agent/logs/monitoring_audit.log")
            if log_file.exists():
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-20:]  # Últimas 20 linhas
                    logs = [line.strip() for line in lines if line.strip()]
        except:
            logs = ["Erro ao carregar logs"]
        
        if not logs:
            logs = ["Nenhum log disponível"]
        
        return logs

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Página principal do dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/dashboard-data")
async def get_dashboard_data():
    """API para obter dados do dashboard"""
    try:
        data = {
            "system": await DashboardData.get_system_metrics(),
            "services": await DashboardData.check_services(),
            "security": await DashboardData.get_security_status(),
            "alerts": await DashboardData.get_active_alerts(),
            "business": await DashboardData.get_business_metrics(),
            "logs": await DashboardData.get_recent_logs(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return data
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Erro ao obter dados: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    """Health check do dashboard"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

def main():
    """Função principal"""
    print("📊 DASHBOARD DE MONITORAMENTO WEB")
    print("=" * 50)
    print("🌐 Iniciando servidor web...")
    print("📱 Dashboard disponível em: http://localhost:8001")
    print("🔄 Atualização automática a cada 5 segundos")
    print("🛑 Pressione Ctrl+C para parar")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info",
            access_log=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Dashboard parado pelo usuário")

if __name__ == "__main__":
    main()
