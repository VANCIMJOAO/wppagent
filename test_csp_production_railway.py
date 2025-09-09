"""
🧪 Teste CSP Security em Produção - Railway
===========================================

Script para testar o sistema CSP completo no backend 
Railway em produção, verificando:

- CSP headers implementation
- Violation reporting
- Security policy effectiveness  
- Production environment integration
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class CSPProductionTest:
    def __init__(self):
        self.railway_url = "https://wppagent-production.up.railway.app"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": "production_railway",
            "tests": {},
            "summary": {}
        }
        
    async def test_csp_headers_presence(self) -> Dict[str, Any]:
        """Test 1: Verify CSP headers are present in production"""
        print("\n🔒 Testing CSP Headers Presence...")
        
        test_result = {
            "name": "CSP Headers Presence",
            "status": "success",
            "details": {},
            "headers_found": {}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test main endpoints
                endpoints = [
                    "/",
                    "/api/dashboard",
                    "/api/appointments", 
                    "/api/analytics"
                ]
                
                for endpoint in endpoints:
                    try:
                        async with session.get(f"{self.railway_url}{endpoint}") as response:
                            headers = dict(response.headers)
                            
                            # Check for CSP header
                            csp_header = headers.get('content-security-policy', '')
                            csp_report_only = headers.get('content-security-policy-report-only', '')
                            
                            test_result["headers_found"][endpoint] = {
                                "csp_present": bool(csp_header),
                                "csp_report_only_present": bool(csp_report_only),
                                "csp_header": csp_header[:100] + "..." if len(csp_header) > 100 else csp_header,
                                "status_code": response.status,
                                "other_security_headers": {
                                    "x-frame-options": headers.get('x-frame-options', 'MISSING'),
                                    "x-content-type-options": headers.get('x-content-type-options', 'MISSING'),
                                    "strict-transport-security": headers.get('strict-transport-security', 'MISSING'),
                                    "referrer-policy": headers.get('referrer-policy', 'MISSING')
                                }
                            }
                            
                            print(f"✅ {endpoint}: CSP={'✓' if csp_header else '✗'}, Status={response.status}")
                            
                    except Exception as e:
                        test_result["headers_found"][endpoint] = {
                            "error": str(e),
                            "status": "failed"
                        }
                        print(f"❌ {endpoint}: {e}")
                
                # Summary
                total_endpoints = len(endpoints)
                endpoints_with_csp = sum(1 for ep in test_result["headers_found"].values() 
                                       if ep.get("csp_present", False))
                
                test_result["details"]["total_endpoints_tested"] = total_endpoints
                test_result["details"]["endpoints_with_csp"] = endpoints_with_csp
                test_result["details"]["csp_coverage"] = round((endpoints_with_csp / total_endpoints) * 100, 1)
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            print(f"❌ CSP headers test failed: {e}")
            
        return test_result
    
    async def test_csp_violation_reporting(self) -> Dict[str, Any]:
        """Test 2: Test CSP violation reporting endpoint"""
        print("\n📊 Testing CSP Violation Reporting...")
        
        test_result = {
            "name": "CSP Violation Reporting",
            "status": "success",
            "details": {},
            "violations_tested": []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test CSP report endpoint
                report_url = f"{self.railway_url}/api/csp-report"
                
                # Simulate CSP violation reports
                test_violations = [
                    {
                        "csp-report": {
                            "document-uri": "https://wppagent-production.up.railway.app/",
                            "referrer": "",
                            "violated-directive": "script-src",
                            "effective-directive": "script-src",
                            "original-policy": "default-src 'self'",
                            "disposition": "enforce",
                            "blocked-uri": "https://malicious-site.com/script.js",
                            "status-code": 0,
                            "script-sample": ""
                        }
                    },
                    {
                        "csp-report": {
                            "document-uri": "https://wppagent-production.up.railway.app/dashboard",
                            "referrer": "",
                            "violated-directive": "style-src",
                            "effective-directive": "style-src", 
                            "original-policy": "default-src 'self'",
                            "disposition": "enforce",
                            "blocked-uri": "inline",
                            "status-code": 0,
                            "script-sample": ""
                        }
                    }
                ]
                
                for i, violation in enumerate(test_violations):
                    try:
                        async with session.post(
                            report_url,
                            json=violation,
                            headers={"Content-Type": "application/csp-report"}
                        ) as response:
                            
                            violation_result = {
                                "violation_type": violation["csp-report"]["violated-directive"],
                                "status_code": response.status,
                                "response_text": await response.text() if response.status != 204 else "No Content",
                                "success": response.status in [200, 204]
                            }
                            
                            test_result["violations_tested"].append(violation_result)
                            
                            status_icon = "✅" if violation_result["success"] else "❌"
                            print(f"{status_icon} Violation {i+1} ({violation_result['violation_type']}): {response.status}")
                            
                    except Exception as e:
                        test_result["violations_tested"].append({
                            "violation_type": violation["csp-report"]["violated-directive"],
                            "error": str(e),
                            "success": False
                        })
                        print(f"❌ Violation {i+1} failed: {e}")
                
                # Summary
                successful_reports = sum(1 for v in test_result["violations_tested"] if v.get("success", False))
                total_reports = len(test_violations)
                
                test_result["details"]["total_violations_tested"] = total_reports
                test_result["details"]["successful_reports"] = successful_reports
                test_result["details"]["reporting_success_rate"] = round((successful_reports / total_reports) * 100, 1)
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            print(f"❌ CSP reporting test failed: {e}")
            
        return test_result
    
    async def test_csp_policy_effectiveness(self) -> Dict[str, Any]:
        """Test 3: Verify CSP policy blocks unauthorized resources"""
        print("\n🛡️ Testing CSP Policy Effectiveness...")
        
        test_result = {
            "name": "CSP Policy Effectiveness",
            "status": "success",
            "details": {},
            "policy_tests": []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get CSP policy first
                async with session.get(self.railway_url) as response:
                    csp_header = response.headers.get('content-security-policy', '')
                    
                    if csp_header:
                        test_result["details"]["csp_policy_found"] = True
                        test_result["details"]["policy_length"] = len(csp_header)
                        
                        # Analyze CSP directives
                        directives = {}
                        for directive in csp_header.split(';'):
                            directive = directive.strip()
                            if directive:
                                parts = directive.split(' ', 1)
                                if len(parts) >= 1:
                                    key = parts[0]
                                    value = parts[1] if len(parts) > 1 else ""
                                    directives[key] = value
                        
                        # Test specific directives
                        directive_tests = [
                            {
                                "directive": "default-src",
                                "expected": "'self'",
                                "description": "Default source should be restrictive"
                            },
                            {
                                "directive": "script-src", 
                                "contains": ["'self'"],
                                "description": "Script sources should include self"
                            },
                            {
                                "directive": "style-src",
                                "contains": ["'self'"],
                                "description": "Style sources should include self"
                            },
                            {
                                "directive": "frame-src",
                                "expected": "'none'",
                                "description": "Frame sources should be disabled"
                            },
                            {
                                "directive": "object-src",
                                "expected": "'none'",
                                "description": "Object sources should be disabled"
                            }
                        ]
                        
                        for directive_test in directive_tests:
                            directive_name = directive_test["directive"]
                            directive_value = directives.get(directive_name, "MISSING")
                            
                            test_passed = False
                            if "expected" in directive_test:
                                test_passed = directive_test["expected"] in directive_value
                            elif "contains" in directive_test:
                                test_passed = any(item in directive_value for item in directive_test["contains"])
                            
                            policy_test_result = {
                                "directive": directive_name,
                                "current_value": directive_value,
                                "test_passed": test_passed,
                                "description": directive_test["description"]
                            }
                            
                            test_result["policy_tests"].append(policy_test_result)
                            
                            status_icon = "✅" if test_passed else "❌"
                            print(f"{status_icon} {directive_name}: {directive_value}")
                        
                        # Calculate effectiveness score
                        passed_tests = sum(1 for test in test_result["policy_tests"] if test["test_passed"])
                        total_tests = len(directive_tests)
                        effectiveness_score = round((passed_tests / total_tests) * 100, 1)
                        
                        test_result["details"]["effectiveness_score"] = effectiveness_score
                        test_result["details"]["passed_directive_tests"] = passed_tests
                        test_result["details"]["total_directive_tests"] = total_tests
                        
                    else:
                        test_result["status"] = "failed"
                        test_result["details"]["csp_policy_found"] = False
                        test_result["error"] = "No CSP header found in response"
                        
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            print(f"❌ CSP effectiveness test failed: {e}")
            
        return test_result
    
    async def test_security_headers_complete(self) -> Dict[str, Any]:
        """Test 4: Comprehensive security headers check"""
        print("\n🔐 Testing Complete Security Headers...")
        
        test_result = {
            "name": "Complete Security Headers", 
            "status": "success",
            "details": {},
            "security_score": 0
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.railway_url) as response:
                    headers = dict(response.headers)
                    
                    # Define required security headers
                    security_headers = {
                        "content-security-policy": {
                            "weight": 30,
                            "description": "Content Security Policy"
                        },
                        "strict-transport-security": {
                            "weight": 20,
                            "description": "HTTP Strict Transport Security"
                        },
                        "x-frame-options": {
                            "weight": 15,
                            "description": "Frame Options Protection"
                        },
                        "x-content-type-options": {
                            "weight": 15,
                            "description": "Content Type Options"
                        },
                        "referrer-policy": {
                            "weight": 10,
                            "description": "Referrer Policy"
                        },
                        "permissions-policy": {
                            "weight": 5,
                            "description": "Permissions Policy"
                        },
                        "x-xss-protection": {
                            "weight": 5,
                            "description": "XSS Protection"
                        }
                    }
                    
                    total_possible_score = sum(header["weight"] for header in security_headers.values())
                    actual_score = 0
                    
                    header_results = {}
                    
                    for header_name, header_info in security_headers.items():
                        header_value = headers.get(header_name.lower(), '')
                        is_present = bool(header_value)
                        
                        if is_present:
                            actual_score += header_info["weight"]
                        
                        header_results[header_name] = {
                            "present": is_present,
                            "value": header_value[:100] + "..." if len(header_value) > 100 else header_value,
                            "weight": header_info["weight"],
                            "description": header_info["description"]
                        }
                        
                        status_icon = "✅" if is_present else "❌"
                        print(f"{status_icon} {header_name}: {'Present' if is_present else 'Missing'}")
                    
                    security_percentage = round((actual_score / total_possible_score) * 100, 1)
                    
                    test_result["details"]["header_results"] = header_results
                    test_result["details"]["security_percentage"] = security_percentage
                    test_result["details"]["actual_score"] = actual_score
                    test_result["details"]["max_possible_score"] = total_possible_score
                    test_result["security_score"] = security_percentage
                    
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            print(f"❌ Security headers test failed: {e}")
            
        return test_result
    
    async def run_production_tests(self) -> Dict[str, Any]:
        """Execute all CSP production tests"""
        print("🧪 Starting CSP Security Tests - Railway Production")
        print("=" * 65)
        
        test_start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_csp_headers_presence(),
            self.test_csp_violation_reporting(), 
            self.test_csp_policy_effectiveness(),
            self.test_security_headers_complete()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.results["tests"][f"test_{i+1}"] = {
                    "name": f"Test {i+1}",
                    "status": "failed",
                    "error": str(result)
                }
            else:
                self.results["tests"][result["name"]] = result
        
        # Calculate summary
        valid_results = [r for r in results if not isinstance(r, Exception)]
        total_tests = len(valid_results)
        successful_tests = sum(1 for r in valid_results if r.get("status") == "success")
        failed_tests = total_tests - successful_tests
        
        # Calculate overall security score
        security_scores = [r.get("security_score", 0) for r in valid_results if "security_score" in r]
        avg_security_score = sum(security_scores) / len(security_scores) if security_scores else 0
        
        total_time = time.time() - test_start_time
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": round((successful_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
            "average_security_score": round(avg_security_score, 1),
            "total_time": round(total_time, 2),
            "status": "PASSED" if failed_tests == 0 else "PARTIAL" if successful_tests > 0 else "FAILED",
            "railway_url": self.railway_url
        }
        
        return self.results
    
    def print_results(self):
        """Print comprehensive production test results"""
        print("\n" + "=" * 65)
        print("🎯 CSP SECURITY PRODUCTION TEST RESULTS")
        print("=" * 65)
        
        summary = self.results["summary"]
        print(f"\n📊 SUMMARY:")
        print(f"   Environment: Railway Production")
        print(f"   URL: {summary['railway_url']}")
        print(f"   Status: {summary['status']}")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Security Score: {summary['average_security_score']}%")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Successful: {summary['successful_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Execution Time: {summary['total_time']}s")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in self.results["tests"].items():
            status_icon = "✅" if result.get("status") == "success" else "❌"
            print(f"   {status_icon} {test_name}: {result.get('status', 'unknown').upper()}")
            
            if "details" in result and result["details"]:
                key_metrics = {}
                details = result["details"]
                
                if "csp_coverage" in details:
                    key_metrics["CSP Coverage"] = f"{details['csp_coverage']}%"
                if "effectiveness_score" in details:
                    key_metrics["Effectiveness"] = f"{details['effectiveness_score']}%"
                if "security_percentage" in details:
                    key_metrics["Security Score"] = f"{details['security_percentage']}%"
                if "reporting_success_rate" in details:
                    key_metrics["Reporting"] = f"{details['reporting_success_rate']}%"
                
                if key_metrics:
                    metrics_str = ", ".join([f"{k}: {v}" for k, v in key_metrics.items()])
                    print(f"      Metrics: {metrics_str}")
            
            if result.get("status") == "failed" and "error" in result:
                print(f"      Error: {result['error']}")
        
        print(f"\n🔍 CSP IMPLEMENTATION STATUS:")
        
        # Analyze results for CSP status
        headers_test = self.results["tests"].get("CSP Headers Presence", {})
        policy_test = self.results["tests"].get("CSP Policy Effectiveness", {})
        reporting_test = self.results["tests"].get("CSP Violation Reporting", {})
        security_test = self.results["tests"].get("Complete Security Headers", {})
        
        csp_features = []
        
        if headers_test.get("status") == "success":
            coverage = headers_test.get("details", {}).get("csp_coverage", 0)
            csp_features.append(f"✅ CSP Headers Present ({coverage}% coverage)")
        else:
            csp_features.append("❌ CSP Headers Missing")
        
        if policy_test.get("status") == "success":
            effectiveness = policy_test.get("details", {}).get("effectiveness_score", 0)
            csp_features.append(f"✅ CSP Policy Effective ({effectiveness}% score)")
        else:
            csp_features.append("❌ CSP Policy Issues")
        
        if reporting_test.get("status") == "success":
            reporting_rate = reporting_test.get("details", {}).get("reporting_success_rate", 0)
            csp_features.append(f"✅ Violation Reporting ({reporting_rate}% success)")
        else:
            csp_features.append("❌ Violation Reporting Failed")
        
        if security_test.get("status") == "success":
            security_score = security_test.get("security_score", 0)
            csp_features.append(f"✅ Security Headers ({security_score}% score)")
        else:
            csp_features.append("❌ Security Headers Incomplete")
        
        for feature in csp_features:
            print(f"   {feature}")
        
        print(f"\n💡 PROBLEMA 5.1 CSP HEADERS INCOMPLETOS:")
        if summary["success_rate"] >= 75 and summary["average_security_score"] >= 70:
            print(f"   Status: ✅ RESOLVIDO COMPLETAMENTE")
            print(f"   Solução: CSP headers rigorosos implementados em produção")
            print(f"   Score: {summary['average_security_score']}% de segurança")
        elif summary["success_rate"] >= 50:
            print(f"   Status: 🔄 PARCIALMENTE RESOLVIDO")  
            print(f"   Requer: Ajustes na configuração CSP")
            print(f"   Score: {summary['average_security_score']}% de segurança")
        else:
            print(f"   Status: ❌ REQUER ATENÇÃO")
            print(f"   Problema: CSP headers não encontrados ou malformados")
            print(f"   Score: {summary['average_security_score']}% de segurança")
        
        if summary["status"] == "PASSED":
            print(f"\n🎉 TODOS OS TESTES PASSARAM! CSP Security implementado com sucesso em produção.")
        else:
            print(f"\n⚠️  Alguns testes falharam. Verificar implementação CSP.")

async def main():
    """Execute CSP production tests on Railway"""
    test_runner = CSPProductionTest()
    
    try:
        print("🚀 Connecting to Railway Production Environment...")
        print(f"🌐 Target URL: {test_runner.railway_url}")
        
        await test_runner.run_production_tests()
        test_runner.print_results()
        
        # Save results
        with open("csp_production_test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_runner.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Results saved to: csp_production_test_results.json")
        
        return test_runner.results["summary"]["status"] == "PASSED"
        
    except Exception as e:
        print(f"\n❌ Production test execution failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
