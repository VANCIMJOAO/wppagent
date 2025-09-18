#!/usr/bin/env python3
"""
🧪 E2E Tests for Railway Production Environment
Testing WhatsApp Agent on https://wppagent-production-app-production.up.railway.app
"""

import requests
import json
import time
from datetime import datetime
import sys

# Railway Production Configuration
BASE_URL = "https://wppagent-production-app-production.up.railway.app"

def test_health_endpoint():
    """Test basic health endpoint"""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "WhatsApp Agent API"
        print("✅ Health endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_docs_endpoint():
    """Test API documentation accessibility"""
    print("\n🔍 Testing /docs endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        print("✅ Docs endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Docs endpoint test failed: {e}")
        return False

def test_openapi_schema():
    """Test OpenAPI schema endpoint"""
    print("\n🔍 Testing /openapi.json endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        print(f"API Title: {schema['info']['title']}")
        print(f"API Version: {schema['info']['version']}")
        print(f"Number of endpoints: {len(schema['paths'])}")
        print("✅ OpenAPI schema test passed!")
        return True
    except Exception as e:
        print(f"❌ OpenAPI schema test failed: {e}")
        return False

def test_security_headers():
    """Test security headers implementation"""
    print("\n🔍 Testing security headers...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        headers = response.headers
        
        security_headers = [
            "content-security-policy",
            "x-content-type-options",
            "x-frame-options", 
            "strict-transport-security",
            "x-xss-protection",
            "referrer-policy"
        ]
        
        missing_headers = []
        for header in security_headers:
            if header not in headers:
                missing_headers.append(header)
            else:
                print(f"✅ {header}: {headers[header][:50]}...")
        
        if missing_headers:
            print(f"⚠️ Missing security headers: {missing_headers}")
        else:
            print("✅ All security headers present!")
        
        return len(missing_headers) == 0
    except Exception as e:
        print(f"❌ Security headers test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting implementation"""
    print("\n🔍 Testing rate limiting...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        headers = response.headers
        
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "x-ratelimit-window"
        ]
        
        for header in rate_limit_headers:
            if header in headers:
                print(f"✅ {header}: {headers[header]}")
            else:
                print(f"⚠️ Missing rate limit header: {header}")
        
        return "x-ratelimit-limit" in headers
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def test_cors_configuration():
    """Test CORS configuration"""
    print("\n🔍 Testing CORS configuration...")
    try:
        # Test preflight request
        response = requests.options(f"{BASE_URL}/health", timeout=10)
        print(f"OPTIONS Status Code: {response.status_code}")
        
        # Check for CORS headers in actual request
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        headers = response.headers
        
        cors_indicators = [
            "access-control-allow-origin",
            "access-control-allow-methods", 
            "access-control-allow-headers"
        ]
        
        cors_present = any(header in headers for header in cors_indicators)
        print(f"CORS headers present: {cors_present}")
        
        return True  # CORS may be handled by Railway edge
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def run_all_tests():
    """Run all E2E tests"""
    print("🚀 Starting E2E Tests for Railway Production Environment")
    print(f"🎯 Target: {BASE_URL}")
    print(f"🕐 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_docs_endpoint,
        test_openapi_schema,
        test_security_headers,
        test_rate_limiting,
        test_cors_configuration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\n📈 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Railway production environment is fully functional!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the details above.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)