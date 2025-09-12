#!/usr/bin/env python3
"""
🔒 HF001 - Test Script: Validação de Webhook Signature
=====================================================

Testa a implementação do HF001 que remove o bypass de validação e torna
a verificação HMAC obrigatória para todos os webhooks.

Teste Negativo: Webhook com signature inválida deve retornar HTTP 403
Teste Positivo: Webhook com signature válida deve retornar HTTP 200
"""

import asyncio
import hmac
import hashlib
import json
import aiohttp
import os
from datetime import datetime
from typing import Dict, Any, Optional

class HF001TestSuite:
    def __init__(self):
        self.webhook_url = "https://wppagent-production.up.railway.app/webhook"
        self.webhook_secret = os.getenv('WHATSAPP_WEBHOOK_SECRET')
        self.test_payload = {"entry": []}
        
    def generate_valid_signature(self, payload: str) -> str:
        """Gerar assinatura HMAC SHA256 válida"""
        if not self.webhook_secret:
            raise ValueError("WHATSAPP_WEBHOOK_SECRET não configurado")
            
        signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def test_invalid_signature(self) -> Dict[str, Any]:
        """Teste negativo: webhook com signature inválida"""
        payload = json.dumps(self.test_payload)
        headers = {
            'Content-Type': 'application/json',
            'X-Hub-Signature-256': 'sha256=invalid_signature_should_be_rejected'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.webhook_url,
                    data=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return {
                        'test': 'invalid_signature',
                        'expected_status': 403,
                        'actual_status': response.status,
                        'success': response.status == 403,
                        'response_text': await response.text(),
                        'headers': dict(response.headers)
                    }
            except Exception as e:
                return {
                    'test': 'invalid_signature',
                    'error': str(e),
                    'success': False
                }
    
    async def test_missing_signature(self) -> Dict[str, Any]:
        """Teste negativo: webhook sem header de signature"""
        payload = json.dumps(self.test_payload)
        headers = {
            'Content-Type': 'application/json'
            # Sem X-Hub-Signature-256
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.webhook_url,
                    data=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return {
                        'test': 'missing_signature',
                        'expected_status': 403,
                        'actual_status': response.status,
                        'success': response.status == 403,
                        'response_text': await response.text(),
                        'headers': dict(response.headers)
                    }
            except Exception as e:
                return {
                    'test': 'missing_signature',
                    'error': str(e),
                    'success': False
                }
    
    async def test_valid_signature(self) -> Dict[str, Any]:
        """Teste positivo: webhook com signature válida"""
        if not self.webhook_secret:
            return {
                'test': 'valid_signature',
                'error': 'WHATSAPP_WEBHOOK_SECRET não configurado',
                'success': False,
                'skipped': True
            }
        
        payload = json.dumps(self.test_payload)
        valid_signature = self.generate_valid_signature(payload)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Hub-Signature-256': valid_signature
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.webhook_url,
                    data=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return {
                        'test': 'valid_signature',
                        'expected_status': 200,
                        'actual_status': response.status,
                        'success': response.status == 200,
                        'response_text': await response.text(),
                        'headers': dict(response.headers),
                        'signature_used': valid_signature[:20] + '...'
                    }
            except Exception as e:
                return {
                    'test': 'valid_signature',
                    'error': str(e),
                    'success': False
                }
    
    async def test_malformed_signature(self) -> Dict[str, Any]:
        """Teste negativo: signature malformada (sem prefixo sha256=)"""
        payload = json.dumps(self.test_payload)
        headers = {
            'Content-Type': 'application/json',
            'X-Hub-Signature-256': 'malformed_signature_without_prefix'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.webhook_url,
                    data=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return {
                        'test': 'malformed_signature',
                        'expected_status': 403,
                        'actual_status': response.status,
                        'success': response.status == 403,
                        'response_text': await response.text(),
                        'headers': dict(response.headers)
                    }
            except Exception as e:
                return {
                    'test': 'malformed_signature',
                    'error': str(e),
                    'success': False
                }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Executar toda a suite de testes HF001"""
        print("🔒 HF001 Test Suite - Webhook Signature Validation")
        print("=" * 55)
        print(f"Target URL: {self.webhook_url}")
        print(f"Webhook Secret Configured: {bool(self.webhook_secret)}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print()
        
        tests = [
            self.test_invalid_signature,
            self.test_missing_signature,
            self.test_malformed_signature,
            self.test_valid_signature
        ]
        
        results = []
        passed = 0
        failed = 0
        skipped = 0
        
        for test_func in tests:
            print(f"Running {test_func.__name__}...")
            result = await test_func()
            results.append(result)
            
            if result.get('skipped'):
                print(f"  ⏭️  SKIPPED: {result.get('error', 'No reason provided')}")
                skipped += 1
            elif result.get('success'):
                print(f"  ✅ PASSED: Status {result.get('actual_status')} (expected {result.get('expected_status')})")
                passed += 1
            else:
                print(f"  ❌ FAILED: Status {result.get('actual_status')} (expected {result.get('expected_status')})")
                if 'error' in result:
                    print(f"     Error: {result['error']}")
                failed += 1
            print()
        
        print("📊 Test Summary:")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⏭️  Skipped: {skipped}")
        print(f"  📈 Success Rate: {(passed/(passed+failed)*100) if (passed+failed) > 0 else 0:.1f}%")
        print()
        
        # Análise de conformidade HF001
        compliance_analysis = self.analyze_hf001_compliance(results)
        print("🔍 HF001 Compliance Analysis:")
        for key, value in compliance_analysis.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'webhook_url': self.webhook_url,
            'webhook_secret_configured': bool(self.webhook_secret),
            'total_tests': len(tests),
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'success_rate': (passed/(passed+failed)*100) if (passed+failed) > 0 else 0,
            'results': results,
            'hf001_compliance': compliance_analysis,
            'overall_hf001_success': all(compliance_analysis.values())
        }
    
    def analyze_hf001_compliance(self, results: list) -> Dict[str, bool]:
        """Analisar conformidade com requisitos HF001"""
        compliance = {}
        
        # Encontrar resultados específicos
        invalid_sig_result = next((r for r in results if r.get('test') == 'invalid_signature'), None)
        missing_sig_result = next((r for r in results if r.get('test') == 'missing_signature'), None)
        malformed_sig_result = next((r for r in results if r.get('test') == 'malformed_signature'), None)
        valid_sig_result = next((r for r in results if r.get('test') == 'valid_signature'), None)
        
        # Verificar rejeição de signatures inválidas
        compliance['Rejects invalid signatures (HTTP 403)'] = (
            invalid_sig_result and invalid_sig_result.get('success', False)
        )
        
        # Verificar rejeição de requests sem signature
        compliance['Rejects missing signatures (HTTP 403)'] = (
            missing_sig_result and missing_sig_result.get('success', False)
        )
        
        # Verificar rejeição de signatures malformadas
        compliance['Rejects malformed signatures (HTTP 403)'] = (
            malformed_sig_result and malformed_sig_result.get('success', False)
        )
        
        # Verificar aceitação de signatures válidas
        if valid_sig_result and not valid_sig_result.get('skipped'):
            compliance['Accepts valid signatures (HTTP 200)'] = (
                valid_sig_result.get('success', False)
            )
        else:
            compliance['Accepts valid signatures (HTTP 200)'] = False
        
        # Verificar mensagens de erro HF001
        has_hf001_messages = any(
            'HF001' in result.get('response_text', '') 
            for result in results 
            if not result.get('success', True)
        )
        compliance['Returns HF001 error messages'] = has_hf001_messages
        
        return compliance

async def main():
    """Executar testes HF001"""
    test_suite = HF001TestSuite()
    results = await test_suite.run_all_tests()
    
    # Salvar resultados
    output_file = 'hf001_test_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Results saved to: {output_file}")
    
    # Exit code baseado no sucesso
    if results['overall_hf001_success']:
        print("🎉 HF001 implementation is COMPLIANT!")
        exit(0)
    else:
        print("🚨 HF001 implementation has ISSUES!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
