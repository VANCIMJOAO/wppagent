#!/usr/bin/env python3
"""
💥 Teste de Stress e Volume Extremo - WhatsApp Agent
Simula condições extremas de uso para validar limites e estabilidade
"""

import requests
import json
import time
import threading
import concurrent.futures
import statistics
from datetime import datetime, timedelta
import sys
import os
import psutil
import random

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

class TestesStressVolume:
    def __init__(self):
        self.base_url = BASE_URL
        self.resultados = []
        self.metricas_sistema = []
        
    def log_resultado(self, teste, sucesso, detalhes="", metricas=None):
        """Registra resultado com métricas de sistema"""
        resultado = {
            "teste": teste,
            "sucesso": sucesso,
            "detalhes": detalhes,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "metricas": metricas or {},
            "memoria_local": psutil.virtual_memory().percent,
            "cpu_local": psutil.cpu_percent()
        }
        self.resultados.append(resultado)
        
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        print(f"{status} - {teste}")
        if detalhes:
            print(f"    Detalhes: {detalhes}")
        if metricas:
            for key, value in metricas.items():
                print(f"    {key}: {value}")
    
    def monitorar_metricas_sistema(self, duracao_segundos):
        """Monitora métricas do sistema local durante os testes"""
        start_time = time.time()
        
        while time.time() - start_time < duracao_segundos:
            self.metricas_sistema.append({
                "timestamp": time.time(),
                "cpu": psutil.cpu_percent(),
                "memoria": psutil.virtual_memory().percent,
                "conexoes": len(psutil.net_connections())
            })
            time.sleep(1)
    
    def teste_volume_massivo(self):
        """Teste de volume massivo - simula pico de tráfego"""
        print("\n🔥 TESTE DE VOLUME MASSIVO")
        print("-" * 50)
        
        # Configurações do teste
        num_threads = 20
        requests_por_thread = 25
        total_requests = num_threads * requests_por_thread
        
        print(f"    Configuração: {num_threads} threads × {requests_por_thread} requests = {total_requests} total")
        
        def worker_thread(thread_id, resultados_compartilhados):
            """Worker para cada thread"""
            tempos = []
            sucessos = 0
            erros = []
            
            for i in range(requests_por_thread):
                start_time = time.time()
                try:
                    response = requests.get(
                        f"{self.base_url}/health",
                        timeout=10
                    )
                    end_time = time.time()
                    tempo = end_time - start_time
                    tempos.append(tempo)
                    
                    if response.status_code == 200:
                        sucessos += 1
                    else:
                        erros.append(response.status_code)
                        
                except requests.exceptions.Timeout:
                    erros.append("TIMEOUT")
                except Exception as e:
                    erros.append(str(e)[:50])
                
                # Delay mínimo para não sobrecarregar
                time.sleep(0.02)
            
            resultados_compartilhados.append({
                "thread_id": thread_id,
                "sucessos": sucessos,
                "total": requests_por_thread,
                "tempos": tempos,
                "erros": erros
            })
        
        # Iniciar monitoramento de sistema
        monitor_thread = threading.Thread(
            target=self.monitorar_metricas_sistema, 
            args=(60,)  # 60 segundos de monitoramento
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Executar teste de volume
        start_time = time.time()
        resultados_compartilhados = []
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(worker_thread, i, resultados_compartilhados)
                    for i in range(num_threads)
                ]
                
                # Aguardar conclusão com timeout
                concurrent.futures.wait(futures, timeout=120)
            
            end_time = time.time()
            tempo_total = end_time - start_time
            
            # Análise dos resultados
            total_sucessos = sum(r["sucessos"] for r in resultados_compartilhados)
            todos_tempos = []
            todos_erros = []
            
            for r in resultados_compartilhados:
                todos_tempos.extend(r["tempos"])
                todos_erros.extend(r["erros"])
            
            if todos_tempos:
                tempo_medio = statistics.mean(todos_tempos)
                tempo_mediano = statistics.median(todos_tempos)
                tempo_max = max(todos_tempos)
                tempo_min = min(todos_tempos)
                desvio_padrao = statistics.stdev(todos_tempos) if len(todos_tempos) > 1 else 0
                
                taxa_sucesso = (total_sucessos / total_requests) * 100
                throughput = total_requests / tempo_total
                
                # Critérios de sucesso para teste de stress
                sucesso = (
                    taxa_sucesso >= 70 and  # Pelo menos 70% de sucesso
                    tempo_medio < 2.0 and   # Tempo médio aceitável
                    tempo_max < 10.0        # Sem timeouts extremos
                )
                
                metricas = {
                    "Total Requests": total_requests,
                    "Taxa Sucesso": f"{taxa_sucesso:.1f}%",
                    "Throughput": f"{throughput:.2f} req/s",
                    "Tempo Médio": f"{tempo_medio:.3f}s",
                    "Tempo Mediano": f"{tempo_mediano:.3f}s",
                    "Tempo Min/Max": f"{tempo_min:.3f}s / {tempo_max:.3f}s",
                    "Desvio Padrão": f"{desvio_padrao:.3f}s",
                    "Tipos de Erro": len(set(todos_erros)),
                    "Duração Total": f"{tempo_total:.2f}s"
                }
                
                detalhes = f"Stress test com {num_threads} threads simultâneas"
                
                self.log_resultado(
                    "Volume massivo",
                    sucesso,
                    detalhes,
                    metricas
                )
                
                return sucesso
            else:
                self.log_resultado("Volume massivo", False, "Nenhuma resposta obtida")
                return False
                
        except Exception as e:
            self.log_resultado("Volume massivo", False, f"Erro crítico: {e}")
            return False
    
    def teste_carga_sustentada(self):
        """Teste de carga sustentada por período prolongado"""
        print("\n⏰ TESTE DE CARGA SUSTENTADA")
        print("-" * 50)
        
        duracao_minutos = 3  # 3 minutos de teste sustentado
        intervalo_requests = 0.5  # Request a cada 0.5s
        duracao_segundos = duracao_minutos * 60
        
        print(f"    Duração: {duracao_minutos} minutos")
        print(f"    Intervalo: {intervalo_requests}s entre requests")
        
        start_time = time.time()
        tempos = []
        sucessos = 0
        erros = []
        
        request_count = 0
        
        try:
            while time.time() - start_time < duracao_segundos:
                req_start = time.time()
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=5)
                    req_end = time.time()
                    
                    tempo = req_end - req_start
                    tempos.append(tempo)
                    request_count += 1
                    
                    if response.status_code == 200:
                        sucessos += 1
                    else:
                        erros.append(response.status_code)
                    
                    # Log progresso a cada 30 requests
                    if request_count % 30 == 0:
                        elapsed = time.time() - start_time
                        print(f"    Progress: {elapsed:.0f}s - {request_count} requests")
                        
                except Exception as e:
                    erros.append(str(e)[:30])
                
                time.sleep(intervalo_requests)
            
            tempo_total = time.time() - start_time
            
            if tempos:
                tempo_medio = statistics.mean(tempos)
                throughput = request_count / tempo_total
                taxa_sucesso = (sucessos / request_count) * 100
                
                # Análise de estabilidade ao longo do tempo
                # Dividir em quartis para ver degradação
                quartil_size = len(tempos) // 4
                if quartil_size > 0:
                    q1_tempos = tempos[:quartil_size]
                    q4_tempos = tempos[-quartil_size:]
                    
                    tempo_inicial = statistics.mean(q1_tempos)
                    tempo_final = statistics.mean(q4_tempos)
                    degradacao = ((tempo_final - tempo_inicial) / tempo_inicial) * 100
                else:
                    degradacao = 0
                
                sucesso = (
                    taxa_sucesso >= 90 and     # Alta taxa de sucesso
                    tempo_medio < 1.0 and      # Performance consistente
                    degradacao < 50            # Degradação aceitável
                )
                
                metricas = {
                    "Duração Real": f"{tempo_total:.1f}s",
                    "Total Requests": request_count,
                    "Taxa Sucesso": f"{taxa_sucesso:.1f}%",
                    "Throughput Médio": f"{throughput:.2f} req/s",
                    "Tempo Médio": f"{tempo_medio:.3f}s",
                    "Degradação Performance": f"{degradacao:.1f}%",
                    "Erros Únicos": len(set(erros))
                }
                
                self.log_resultado(
                    "Carga sustentada",
                    sucesso,
                    f"{duracao_minutos} minutos de carga contínua",
                    metricas
                )
                
                return sucesso
            else:
                self.log_resultado("Carga sustentada", False, "Nenhuma resposta válida")
                return False
                
        except Exception as e:
            self.log_resultado("Carga sustentada", False, f"Erro: {e}")
            return False
    
    def teste_picos_instantaneos(self):
        """Teste de picos instantâneos de tráfego"""
        print("\n⚡ TESTE DE PICOS INSTANTÂNEOS")
        print("-" * 50)
        
        # Simula picos repentinos como em promoções ou notícias virais
        num_picos = 3
        requests_por_pico = 30
        threads_por_pico = 15
        
        print(f"    {num_picos} picos de {requests_por_pico} requests cada")
        
        resultados_picos = []
        
        for pico in range(num_picos):
            print(f"    Executando pico {pico + 1}/{num_picos}...")
            
            def fazer_request_rapido():
                try:
                    start = time.time()
                    response = requests.get(f"{self.base_url}/health", timeout=3)
                    end = time.time()
                    return {
                        "sucesso": response.status_code == 200,
                        "tempo": end - start,
                        "status": response.status_code
                    }
                except Exception as e:
                    return {
                        "sucesso": False,
                        "tempo": 3.0,  # Timeout
                        "status": "ERROR",
                        "erro": str(e)[:30]
                    }
            
            # Execução do pico
            start_pico = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads_por_pico) as executor:
                futures = [
                    executor.submit(fazer_request_rapido)
                    for _ in range(requests_por_pico)
                ]
                
                resultados = [
                    future.result() for future in concurrent.futures.as_completed(futures, timeout=10)
                ]
            
            end_pico = time.time()
            duracao_pico = end_pico - start_pico
            
            # Análise do pico
            sucessos_pico = sum(1 for r in resultados if r["sucesso"])
            tempos_pico = [r["tempo"] for r in resultados if "tempo" in r]
            
            if tempos_pico:
                tempo_medio_pico = statistics.mean(tempos_pico)
                throughput_pico = len(resultados) / duracao_pico
                
                resultados_picos.append({
                    "pico": pico + 1,
                    "sucessos": sucessos_pico,
                    "total": len(resultados),
                    "tempo_medio": tempo_medio_pico,
                    "throughput": throughput_pico,
                    "duracao": duracao_pico
                })
            
            # Pausa entre picos
            if pico < num_picos - 1:
                time.sleep(2)
        
        # Análise geral dos picos
        if resultados_picos:
            total_sucessos = sum(p["sucessos"] for p in resultados_picos)
            total_requests = sum(p["total"] for p in resultados_picos)
            taxa_sucesso_geral = (total_sucessos / total_requests) * 100
            
            tempo_medio_geral = statistics.mean([p["tempo_medio"] for p in resultados_picos])
            throughput_maximo = max([p["throughput"] for p in resultados_picos])
            
            sucesso = taxa_sucesso_geral >= 75 and tempo_medio_geral < 1.5
            
            metricas = {
                "Número de Picos": num_picos,
                "Requests por Pico": requests_por_pico,
                "Taxa Sucesso Geral": f"{taxa_sucesso_geral:.1f}%",
                "Tempo Médio Geral": f"{tempo_medio_geral:.3f}s",
                "Throughput Máximo": f"{throughput_maximo:.2f} req/s",
                "Total Requests": total_requests
            }
            
            self.log_resultado(
                "Picos instantâneos",
                sucesso,
                "Simulação de picos de tráfego viral",
                metricas
            )
            
            return sucesso
        else:
            self.log_resultado("Picos instantâneos", False, "Falha na execução dos picos")
            return False
    
    def teste_memoria_conexoes(self):
        """Teste de gestão de memória e conexões"""
        print("\n🧠 TESTE DE GESTÃO DE MEMÓRIA E CONEXÕES")
        print("-" * 50)
        
        num_sessoes = 50  # Simular múltiplas sessões de cliente
        requests_por_sessao = 10
        
        print(f"    {num_sessoes} sessões × {requests_por_sessao} requests")
        
        memoria_inicial = psutil.virtual_memory().percent
        conexoes_iniciais = len(psutil.net_connections())
        
        sessoes_ativas = []
        
        try:
            # Criar múltiplas sessões
            for i in range(num_sessoes):
                session = requests.Session()
                session.timeout = 5
                
                # Fazer requests com cada sessão
                for j in range(requests_por_sessao):
                    try:
                        response = session.get(f"{self.base_url}/health")
                        # Manter conexão viva
                        sessoes_ativas.append(session)
                    except:
                        pass
                
                # Verificar uso de recursos a cada 10 sessões
                if (i + 1) % 10 == 0:
                    memoria_atual = psutil.virtual_memory().percent
                    conexoes_atuais = len(psutil.net_connections())
                    print(f"    Sessões {i+1}: Mem {memoria_atual:.1f}%, Conn {conexoes_atuais}")
            
            # Medição final
            memoria_final = psutil.virtual_memory().percent
            conexoes_finais = len(psutil.net_connections())
            
            # Limpar sessões
            for session in sessoes_ativas:
                try:
                    session.close()
                except:
                    pass
            
            time.sleep(2)  # Aguardar limpeza
            
            memoria_pos_limpeza = psutil.virtual_memory().percent
            conexoes_pos_limpeza = len(psutil.net_connections())
            
            # Análise de vazamentos
            incremento_memoria = memoria_final - memoria_inicial
            incremento_conexoes = conexoes_finais - conexoes_iniciais
            limpeza_memoria = memoria_final - memoria_pos_limpeza
            limpeza_conexoes = conexoes_finais - conexoes_pos_limpeza
            
            # Critérios de aprovação
            sucesso = (
                incremento_memoria < 10 and     # Memória não cresceu muito
                limpeza_conexoes > 0 and        # Conexões foram limpas
                incremento_conexoes < 100       # Não muitas conexões ativas
            )
            
            metricas = {
                "Memória Inicial": f"{memoria_inicial:.1f}%",
                "Memória Final": f"{memoria_final:.1f}%",
                "Incremento Memória": f"{incremento_memoria:.1f}%",
                "Conexões Inicial": conexoes_iniciais,
                "Conexões Final": conexoes_finais,
                "Incremento Conexões": incremento_conexoes,
                "Limpeza Conexões": limpeza_conexoes,
                "Total Requests": num_sessoes * requests_por_sessao
            }
            
            self.log_resultado(
                "Gestão memória/conexões",
                sucesso,
                "Teste de vazamentos e limpeza",
                metricas
            )
            
            return sucesso
            
        except Exception as e:
            self.log_resultado("Gestão memória/conexões", False, f"Erro: {e}")
            return False
    
    def executar_testes_stress(self):
        """Executa todos os testes de stress"""
        print("💥 INICIANDO TESTES DE STRESS E VOLUME EXTREMO")
        print(f"🎯 API: {self.base_url}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"💻 Sistema: CPU {psutil.cpu_percent()}%, RAM {psutil.virtual_memory().percent}%")
        print("=" * 70)
        
        testes = [
            ("Volume Massivo", self.teste_volume_massivo),
            ("Carga Sustentada", self.teste_carga_sustentada),
            ("Picos Instantâneos", self.teste_picos_instantaneos),
            ("Memória/Conexões", self.teste_memoria_conexoes),
        ]
        
        for nome, teste_func in testes:
            try:
                print(f"\n🔄 Executando: {nome}")
                resultado = teste_func()
                time.sleep(3)  # Pausa para recuperação
            except Exception as e:
                print(f"❌ ERRO CRÍTICO em {nome}: {e}")
        
        self.gerar_relatorio_stress()
    
    def gerar_relatorio_stress(self):
        """Gera relatório dos testes de stress"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO DOS TESTES DE STRESS E VOLUME")
        print("=" * 70)
        
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        print(f"📈 Resultados: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print()
        
        print("📋 Análise de Stress:")
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            print(f"{i:2d}. {status} {resultado['teste']}")
            print(f"      {resultado['detalhes']}")
            if resultado.get("metricas"):
                for key, value in resultado["metricas"].items():
                    print(f"      {key}: {value}")
            print(f"      Sistema Local: CPU {resultado.get('cpu_local', 0):.1f}%, RAM {resultado.get('memoria_local', 0):.1f}%")
            print()
        
        # Análise de métricas de sistema
        if self.metricas_sistema:
            cpu_medio = statistics.mean([m["cpu"] for m in self.metricas_sistema])
            memoria_media = statistics.mean([m["memoria"] for m in self.metricas_sistema])
            print(f"📊 Impacto no Sistema Local:")
            print(f"    CPU Médio: {cpu_medio:.1f}%")
            print(f"    RAM Média: {memoria_media:.1f}%")
            print()
        
        # Avaliação final
        if percentual >= 80:
            print("💪 EXCELENTE! A API suporta condições extremas de stress!")
            print("🚀 Pronta para picos de tráfego e alta demanda.")
            return 0
        elif percentual >= 60:
            print("💪 MUITO BOM! A API tem boa resistência a stress.")
            print("⚠️ Pode precisar de otimizações para picos extremos.")
            return 0
        else:
            print("⚠️ ATENÇÃO! A API tem limitações em condições de stress.")
            print("🔧 Recomenda-se otimizações antes de tráfego intenso.")
            return 1

def main():
    """Função principal"""
    tester = TestesStressVolume()
    exit_code = tester.executar_testes_stress()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()