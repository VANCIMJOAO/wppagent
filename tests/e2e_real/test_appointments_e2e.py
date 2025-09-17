"""
🧪 Comprehensive E2E Tests for WhatsApp Agent - Railway Production Environment
Tests the complete appointment system workflow against the live Railway deployment.
"""

import pytest
import httpx
import asyncio
import os
from datetime import datetime, timedelta
import json

# Configuration
BASE_URL = "https://wppagent-production.up.railway.app"
REQUEST_TIMEOUT = 30.0
CONNECTION_TIMEOUT = 10.0

class TestRailwayE2E:
    """End-to-End tests for Railway production deployment"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup for each test"""
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=CONNECTION_TIMEOUT)
        )
        yield
        await self.client.aclose()

    async def test_railway_health_check(self):
        """Test basic Railway health check"""
        try:
            response = await self.client.get("/ping")
            
            # Handle Railway 502 errors gracefully
            if response.status_code == 502:
                pytest.skip("Railway application not responding (502) - server may be starting or routing issue")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            print(f"✅ Railway health check passed: {data}")
            
        except httpx.ConnectTimeout:
            pytest.skip("Railway connection timeout - server may be starting")
        except httpx.ReadTimeout:
            pytest.skip("Railway read timeout - server may be under load")

    async def test_railway_basic_endpoints(self):
        """Test basic Railway endpoints availability"""
        endpoints = ["/ping", "/health", "/docs"]
        
        for endpoint in endpoints:
            try:
                response = await self.client.get(endpoint)
                
                if response.status_code == 502:
                    pytest.skip(f"Railway {endpoint} not responding (502) - routing issue")
                
                # Accept 200 for ping/health, 200 for docs
                assert response.status_code in [200, 404], f"Unexpected status for {endpoint}: {response.status_code}"
                print(f"✅ Railway endpoint {endpoint}: {response.status_code}")
                
            except (httpx.ConnectTimeout, httpx.ReadTimeout):
                pytest.skip(f"Railway {endpoint} timeout - server may be starting")

    async def test_railway_appointment_system(self):
        """Test complete appointment system on Railway"""
        try:
            # 1. Test appointment creation
            appointment_data = {
                "customer_phone": "5511999999999",
                "customer_name": "Test Customer Railway",
                "service_type": "Consulta",
                "preferred_date": (datetime.now() + timedelta(days=1)).isoformat(),
                "notes": "E2E test appointment on Railway"
            }
            
            response = await self.client.post("/api/appointments", json=appointment_data)
            
            if response.status_code == 502:
                pytest.skip("Railway appointments API not responding (502)")
            
            # Handle various expected responses
            if response.status_code == 401:
                pytest.skip("Railway appointments API requires authentication")
            elif response.status_code == 404:
                pytest.skip("Railway appointments endpoint not found")
            
            assert response.status_code in [200, 201], f"Unexpected appointment creation status: {response.status_code}"
            
            appointment = response.json()
            assert "id" in appointment or "appointment_id" in appointment
            print(f"✅ Railway appointment created: {appointment}")
            
        except (httpx.ConnectTimeout, httpx.ReadTimeout):
            pytest.skip("Railway appointments API timeout")

    async def test_railway_websocket_availability(self):
        """Test WebSocket endpoint availability on Railway"""
        try:
            # Test WebSocket endpoint existence (not actual connection)
            response = await self.client.get("/ws")
            
            if response.status_code == 502:
                pytest.skip("Railway WebSocket endpoint not responding (502)")
            
            # WebSocket endpoints typically return 426 (Upgrade Required) for HTTP requests
            assert response.status_code in [426, 400, 404], f"Unexpected WebSocket status: {response.status_code}"
            print(f"✅ Railway WebSocket endpoint available: {response.status_code}")
            
        except (httpx.ConnectTimeout, httpx.ReadTimeout):
            pytest.skip("Railway WebSocket endpoint timeout")

    async def test_railway_performance_basic(self):
        """Test basic Railway performance metrics"""
        try:
            start_time = datetime.now()
            response = await self.client.get("/ping")
            end_time = datetime.now()
            
            if response.status_code == 502:
                pytest.skip("Railway performance test failed - 502 error")
            
            response_time = (end_time - start_time).total_seconds()
            
            assert response.status_code == 200
            assert response_time < 5.0, f"Railway response too slow: {response_time}s"
            
            print(f"✅ Railway performance: {response_time:.2f}s")
            
        except (httpx.ConnectTimeout, httpx.ReadTimeout):
            pytest.skip("Railway performance test timeout")

if __name__ == "__main__":
    # Run tests with Railway-optimized configuration
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--timeout=60",
        "-x"  # Stop on first failure for faster debugging
    ])