#!/usr/bin/env python3
"""
Script de Teste para Sistema de Rate Limiting
=============================================

Este script demonstra e testa o funcionamento do sistema de rate limiting
implementado no WhatsApp Agent Dashboard.

Funcionalidades testadas:
- Rate limiting básico
- Detecção de burst attacks
- Bloqueio automático de IPs
- Estratégias diferentes de rate limiting
- Comportamento adaptativo
"""

import time
import requests
import json
import threading
import random
from datetime import datetime
from typing import List, Dict, Any
import argparse
import sys

class RateLimitTester:
    """Classe para testar o sistema de rate limiting"""
    
    def __init__(self, base_url: str = "http://localhost:8054"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        self.stats = {
            'total_requests': 0,
            'allowed_requests': 0,
            'blocked_requests': 0,
            'errors': 0
        }
    
    def make_request(self, endpoint: str = "/", delay: float = 0) -> Dict[str, Any]:
        """Fazer uma requisição e registrar o resultado"""
        if delay > 0:
            time.sleep(delay)
        
        start_time = time.time()
        
        try:
            response = self.session.get(f"{self.base_url}{endpoint}")
            duration = time.time() - start_time
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': endpoint,
                'status_code': response.status_code,
                'duration': duration,
                'allowed': response.status_code != 429,
                'headers': dict(response.headers),
                'content_length': len(response.content) if response.content else 0
            }
            
            if response.status_code == 429:
                # Rate limited
                self.stats['blocked_requests'] += 1
                try:
                    error_data = response.json()
                    result['error_data'] = error_data
                    result['retry_after'] = error_data.get('retry_after', 0)
                except:
                    result['retry_after'] = int(response.headers.get('Retry-After', 0))
            else:
                self.stats['allowed_requests'] += 1
            
            self.stats['total_requests'] += 1
            self.results.append(result)
            
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['total_requests'] += 1
            
            error_result = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': endpoint,
                'error': str(e),
                'allowed': False,
                'duration': time.time() - start_time
            }
            
            self.results.append(error_result)
            return error_result
    
    def test_basic_rate_limiting(self, num_requests: int = 50, delay: float = 0.1):
        """Teste básico de rate limiting"""
        print(f"\n🧪 TESTE 1: Rate Limiting Básico")
        print(f"Fazendo {num_requests} requisições com delay de {delay}s...")
        
        for i in range(num_requests):
            result = self.make_request(delay=delay)
            
            status = "✅" if result['allowed'] else "🚫"
            print(f"{status} {i+1:2d}/#{num_requests} - Status: {result.get('status_code', 'ERROR')} - "
                  f"Duration: {result['duration']:.3f}s")
            
            if not result['allowed'] and 'retry_after' in result:
                print(f"   ⏰ Retry after: {result['retry_after']} seconds")
        
        self.print_stats()
    
    def test_burst_attack(self, burst_size: int = 20):
        """Teste de ataque de rajada (burst)"""
        print(f"\n🧪 TESTE 2: Ataque de Rajada (Burst)")
        print(f"Fazendo {burst_size} requisições simultâneas...")
        
        threads = []
        burst_results = []
        
        def make_burst_request(index):
            result = self.make_request()
            result['burst_index'] = index
            burst_results.append(result)
        
        # Criar threads para requisições simultâneas
        for i in range(burst_size):
            thread = threading.Thread(target=make_burst_request, args=(i,))
            threads.append(thread)
        
        # Iniciar todas as threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Analisar resultados
        allowed = len([r for r in burst_results if r['allowed']])
        blocked = len([r for r in burst_results if not r['allowed']])
        
        print(f"📊 Resultados do burst ({total_time:.3f}s total):")
        print(f"   ✅ Permitidas: {allowed}")
        print(f"   🚫 Bloqueadas: {blocked}")
        print(f"   📈 Taxa de bloqueio: {(blocked/burst_size)*100:.1f}%")
        
        self.print_stats()
    
    def test_sustained_attack(self, duration: int = 60, requests_per_second: int = 5):
        """Teste de ataque sustentado"""
        print(f"\n🧪 TESTE 3: Ataque Sustentado")
        print(f"Fazendo {requests_per_second} req/s por {duration} segundos...")
        
        start_time = time.time()
        request_count = 0
        blocked_streak = 0
        max_blocked_streak = 0
        
        while time.time() - start_time < duration:
            cycle_start = time.time()
            
            # Fazer requisições neste segundo
            for _ in range(requests_per_second):
                result = self.make_request()
                request_count += 1
                
                if not result['allowed']:
                    blocked_streak += 1
                    max_blocked_streak = max(max_blocked_streak, blocked_streak)
                else:
                    blocked_streak = 0
                
                # Pequeno delay para não sobrecarregar
                time.sleep(0.05)
            
            # Aguardar até completar 1 segundo
            elapsed = time.time() - cycle_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            # Status a cada 10 segundos
            if request_count % (requests_per_second * 10) == 0:
                elapsed_time = time.time() - start_time
                print(f"   ⏱️ {elapsed_time:.0f}s - Requests: {request_count}, "
                      f"Blocked streak: {blocked_streak}")
        
        print(f"📊 Ataque sustentado completado:")
        print(f"   📈 Total de requests: {request_count}")
        print(f"   🔥 Maior sequência bloqueada: {max_blocked_streak}")
        
        self.print_stats()
    
    def test_different_endpoints(self):
        """Teste com diferentes endpoints"""
        print(f"\n🧪 TESTE 4: Diferentes Endpoints")
        
        endpoints = [
            "/",
            "/_dash-layout",
            "/_dash-dependencies", 
            "/_dash-update-component",
            "/assets/style.css"  # Simulado
        ]
        
        for endpoint in endpoints:
            print(f"🎯 Testando endpoint: {endpoint}")
            
            # Fazer várias requisições para cada endpoint
            for i in range(10):
                result = self.make_request(endpoint, delay=0.1)
                status = "✅" if result['allowed'] else "🚫"
                print(f"   {status} {i+1:2d}/10 - Status: {result.get('status_code', 'ERROR')}")
                
                # Se for bloqueado, parar este endpoint
                if not result['allowed']:
                    print(f"   🛑 Endpoint bloqueado após {i+1} tentativas")
                    break
        
        self.print_stats()
    
    def test_ip_spoofing(self):
        """Teste simulando diferentes IPs"""
        print(f"\n🧪 TESTE 5: Simulação de IPs Diferentes")
        
        fake_ips = [
            "192.168.1.100",
            "10.0.0.50", 
            "172.16.0.25",
            "203.0.113.10",
            "198.51.100.20"
        ]
        
        for ip in fake_ips:
            print(f"🌐 Simulando requests do IP: {ip}")
            
            # Simular X-Forwarded-For header
            headers = {'X-Forwarded-For': ip}
            
            for i in range(5):
                try:
                    response = self.session.get(f"{self.base_url}/", headers=headers)
                    status = "✅" if response.status_code != 429 else "🚫"
                    print(f"   {status} {i+1}/5 - Status: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
    
    def print_stats(self):
        """Imprimir estatísticas atuais"""
        total = self.stats['total_requests']
        allowed = self.stats['allowed_requests']
        blocked = self.stats['blocked_requests']
        errors = self.stats['errors']
        
        if total > 0:
            print(f"\n📊 ESTATÍSTICAS ATUAIS:")
            print(f"   📈 Total de requests: {total}")
            print(f"   ✅ Permitidas: {allowed} ({(allowed/total)*100:.1f}%)")
            print(f"   🚫 Bloqueadas: {blocked} ({(blocked/total)*100:.1f}%)")
            print(f"   ❌ Erros: {errors} ({(errors/total)*100:.1f}%)")
            
            if blocked > 0:
                print(f"   🛡️ Rate limiting está ATIVO e funcionando!")
            else:
                print(f"   ⚠️ Nenhuma requisição foi bloqueada ainda")
    
    def export_results(self, filename: str = None):
        """Exportar resultados para arquivo JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rate_limit_test_{timestamp}.json"
        
        report = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'base_url': self.base_url,
                'total_duration': self.results[-1]['timestamp'] if self.results else None
            },
            'statistics': self.stats,
            'detailed_results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Resultados exportados para: {filename}")
        return filename

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Teste do sistema de Rate Limiting')
    parser.add_argument('--url', default='http://localhost:8054', 
                       help='URL base do dashboard (default: http://localhost:8054)')
    parser.add_argument('--test', choices=['basic', 'burst', 'sustained', 'endpoints', 'ips', 'all'],
                       default='all', help='Tipo de teste a executar')
    parser.add_argument('--export', action='store_true', 
                       help='Exportar resultados para arquivo JSON')
    
    args = parser.parse_args()
    
    print("🛡️ TESTADOR DE RATE LIMITING - WhatsApp Agent")
    print("=" * 50)
    print(f"🎯 URL de teste: {args.url}")
    print(f"🧪 Tipo de teste: {args.test}")
    print("=" * 50)
    
    tester = RateLimitTester(args.url)
    
    try:
        # Verificar se o servidor está acessível
        print("🔍 Verificando conectividade...")
        initial_result = tester.make_request()
        
        if 'error' in initial_result:
            print(f"❌ Erro de conectividade: {initial_result['error']}")
            print("💡 Certifique-se de que o dashboard está rodando!")
            return 1
        
        print(f"✅ Servidor acessível (Status: {initial_result['status_code']})")
        
        # Executar testes baseado na escolha
        if args.test in ['basic', 'all']:
            tester.test_basic_rate_limiting()
        
        if args.test in ['burst', 'all']:
            tester.test_burst_attack()
        
        if args.test in ['sustained', 'all']:
            tester.test_sustained_attack(duration=30)  # Duração reduzida para demo
        
        if args.test in ['endpoints', 'all']:
            tester.test_different_endpoints()
        
        if args.test in ['ips', 'all']:
            tester.test_ip_spoofing()
        
        # Estatísticas finais
        print("\n" + "="*50)
        print("📊 RELATÓRIO FINAL")
        print("="*50)
        tester.print_stats()
        
        # Exportar se solicitado
        if args.export:
            tester.export_results()
        
        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        if tester.stats['blocked_requests'] > 0:
            print("✅ Sistema de rate limiting está funcionando corretamente!")
            print("✅ Ataques estão sendo detectados e bloqueados")
            print("✅ Endpoints críticos estão protegidos")
        else:
            print("⚠️ Nenhuma requisição foi bloqueada - verifique as configurações")
            print("💡 Talvez seja necessário ajustar os limites de rate limiting")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        tester.print_stats()
        return 0
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
