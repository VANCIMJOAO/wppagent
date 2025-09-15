#!/usr/bin/env python3
"""
TRILHA 2 FASE 3 - Performance Profiling (Simplified)
Sistema de profiling automático de performance com detecção de bottlenecks
"""

import asyncio
import functools
import gc
import json
import os
import statistics
import sys
import threading
import time
import tracemalloc
from collections import defaultdict, deque
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil


class ProfileType(Enum):
    """Tipos de profiling"""

    CPU = "cpu"
    MEMORY = "memory"
    IO = "io"
    DATABASE = "database"
    FUNCTION = "function"


class BottleneckType(Enum):
    """Tipos de bottleneck"""

    SLOW_FUNCTION = "slow_function"
    MEMORY_LEAK = "memory_leak"
    SLOW_QUERY = "slow_query"
    HIGH_CPU = "high_cpu"
    FREQUENT_CALLS = "frequent_calls"


@dataclass
class ProfileResult:
    """Resultado de profiling"""

    profile_type: ProfileType
    function_name: str
    start_time: float
    end_time: float
    duration: float
    memory_before: Optional[float] = None
    memory_after: Optional[float] = None
    cpu_usage: Optional[float] = None
    call_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return self.duration * 1000


@dataclass
class BottleneckDetection:
    """Detecção de bottleneck"""

    bottleneck_type: BottleneckType
    severity: int  # 1-10
    function_name: str
    description: str
    impact: str
    recommendations: List[str]
    evidence: Dict[str, Any]
    confidence: float
    timestamp: float = field(default_factory=time.time)


class SimpleProfiler:
    """Profiler simplificado e funcional"""

    def __init__(self):
        self.results: List[ProfileResult] = []
        self.function_stats: Dict[str, List[float]] = defaultdict(list)
        self.memory_tracking = False
        self.memory_snapshots: List[Tuple[float, int]] = []
        self.bottlenecks: List[BottleneckDetection] = []

    def start_memory_tracking(self):
        """Inicia tracking de memória"""
        if not self.memory_tracking:
            tracemalloc.start()
            self.memory_tracking = True

    def stop_memory_tracking(self):
        """Para tracking de memória"""
        if self.memory_tracking:
            tracemalloc.stop()
            self.memory_tracking = False

    def get_memory_usage(self) -> int:
        """Obtém uso de memória atual"""
        if self.memory_tracking:
            current, peak = tracemalloc.get_traced_memory()
            return current
        else:
            process = psutil.Process()
            return process.memory_info().rss

    def profile_function(self, profile_type: ProfileType = ProfileType.FUNCTION):
        """Decorator para profiling de função"""

        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                function_name = (
                    f"{func.__module__}.{func.__name__}"
                    if hasattr(func, "__module__")
                    else func.__name__
                )

                # Medições iniciais
                start_time = time.time()
                memory_before = self.get_memory_usage()
                cpu_before = psutil.cpu_percent()

                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    # Medições finais
                    end_time = time.time()
                    memory_after = self.get_memory_usage()
                    cpu_after = psutil.cpu_percent()

                    duration = end_time - start_time

                    # Criar resultado
                    profile_result = ProfileResult(
                        profile_type=profile_type,
                        function_name=function_name,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        memory_before=memory_before,
                        memory_after=memory_after,
                        cpu_usage=(cpu_before + cpu_after) / 2,
                        metadata={"args_count": len(args), "kwargs_count": len(kwargs)},
                    )

                    self.results.append(profile_result)
                    self.function_stats[function_name].append(duration)

                    # Detectar problemas em tempo real
                    if duration > 0.1:  # > 100ms
                        print(
                            f"⚠️  Slow function detected: {function_name} took {duration*1000:.1f}ms"
                        )

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                function_name = (
                    f"{func.__module__}.{func.__name__}"
                    if hasattr(func, "__module__")
                    else func.__name__
                )

                # Medições iniciais
                start_time = time.time()
                memory_before = self.get_memory_usage()
                cpu_before = psutil.cpu_percent()

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    # Medições finais
                    end_time = time.time()
                    memory_after = self.get_memory_usage()
                    cpu_after = psutil.cpu_percent()

                    duration = end_time - start_time

                    # Criar resultado
                    profile_result = ProfileResult(
                        profile_type=profile_type,
                        function_name=function_name,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration,
                        memory_before=memory_before,
                        memory_after=memory_after,
                        cpu_usage=(cpu_before + cpu_after) / 2,
                        metadata={"args_count": len(args), "kwargs_count": len(kwargs)},
                    )

                    self.results.append(profile_result)
                    self.function_stats[function_name].append(duration)

                    # Detectar problemas em tempo real
                    if duration > 0.1:  # > 100ms
                        print(
                            f"⚠️  Slow function detected: {function_name} took {duration*1000:.1f}ms"
                        )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def take_memory_snapshot(self):
        """Tira snapshot de memória"""
        timestamp = time.time()
        memory_usage = self.get_memory_usage()
        self.memory_snapshots.append((timestamp, memory_usage))

        # Manter apenas últimos 100 snapshots
        if len(self.memory_snapshots) > 100:
            self.memory_snapshots = self.memory_snapshots[-100:]

    def detect_bottlenecks(self) -> List[BottleneckDetection]:
        """Detecta bottlenecks baseado nos dados coletados"""
        bottlenecks = []

        # 1. Detectar funções lentas
        for function_name, durations in self.function_stats.items():
            if len(durations) >= 3:  # Pelo menos 3 execuções
                avg_duration = statistics.mean(durations)
                max_duration = max(durations)

                if avg_duration > 0.05:  # > 50ms em média
                    severity = min(10, int(avg_duration * 20))
                    bottlenecks.append(
                        BottleneckDetection(
                            bottleneck_type=BottleneckType.SLOW_FUNCTION,
                            severity=severity,
                            function_name=function_name,
                            description=f"Function averages {avg_duration*1000:.1f}ms per call",
                            impact=f"Performance impact: {len(durations)} calls, max {max_duration*1000:.1f}ms",
                            recommendations=[
                                "Profile function internally for bottlenecks",
                                "Consider algorithm optimization",
                                "Check for blocking I/O operations",
                                "Consider caching if appropriate",
                            ],
                            evidence={
                                "avg_duration_ms": avg_duration * 1000,
                                "max_duration_ms": max_duration * 1000,
                                "call_count": len(durations),
                                "total_time_ms": sum(durations) * 1000,
                            },
                            confidence=0.8,
                        )
                    )

        # 2. Detectar vazamentos de memória
        if len(self.memory_snapshots) >= 5:
            recent_snapshots = self.memory_snapshots[-10:]
            memory_values = [snapshot[1] for snapshot in recent_snapshots]

            # Calcular tendência de crescimento
            if len(memory_values) >= 3:
                n = len(memory_values)
                x = list(range(n))

                sum_x = sum(x)
                sum_y = sum(memory_values)
                sum_xy = sum(x[i] * memory_values[i] for i in range(n))
                sum_x2 = sum(xi * xi for xi in x)

                if n * sum_x2 - sum_x * sum_x != 0:
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

                    # Se slope > 1MB por snapshot
                    if slope > 1024 * 1024:
                        bottlenecks.append(
                            BottleneckDetection(
                                bottleneck_type=BottleneckType.MEMORY_LEAK,
                                severity=min(10, int(slope / (1024 * 1024))),
                                function_name="memory_system",
                                description=f"Memory growing at {slope / 1024 / 1024:.2f} MB per measurement",
                                impact="Continuous memory growth detected",
                                recommendations=[
                                    "Review object lifecycle management",
                                    "Check for unclosed resources",
                                    "Analyze reference cycles",
                                    "Consider memory profiling tools",
                                ],
                                evidence={
                                    "growth_rate_mb": slope / 1024 / 1024,
                                    "measurements": n,
                                    "current_memory_mb": memory_values[-1]
                                    / 1024
                                    / 1024,
                                },
                                confidence=0.7,
                            )
                        )

        # 3. Detectar funções com muitas chamadas
        for function_name, durations in self.function_stats.items():
            if len(durations) > 100:  # Muitas chamadas
                total_time = sum(durations)
                avg_duration = total_time / len(durations)

                if total_time > 1.0:  # Mais de 1 segundo total
                    bottlenecks.append(
                        BottleneckDetection(
                            bottleneck_type=BottleneckType.FREQUENT_CALLS,
                            severity=min(10, int(total_time)),
                            function_name=function_name,
                            description=f"Function called {len(durations)} times, consuming {total_time:.2f}s total",
                            impact=f"High frequency impact: {avg_duration*1000:.1f}ms average per call",
                            recommendations=[
                                "Consider result caching",
                                "Batch multiple calls if possible",
                                "Optimize function for frequent usage",
                                "Review call patterns for optimization",
                            ],
                            evidence={
                                "call_count": len(durations),
                                "total_time_s": total_time,
                                "avg_duration_ms": avg_duration * 1000,
                                "calls_per_second": len(durations) / max(1, total_time),
                            },
                            confidence=0.9,
                        )
                    )

        self.bottlenecks.extend(bottlenecks)
        return bottlenecks

    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtém resumo de performance"""
        if not self.results:
            return {"error": "No profiling data available"}

        # Estatísticas gerais
        total_functions = len(set(r.function_name for r in self.results))
        total_calls = len(self.results)

        durations = [r.duration for r in self.results]
        avg_duration = statistics.mean(durations)
        max_duration = max(durations)

        # Top funções mais lentas
        function_totals = defaultdict(float)
        function_counts = defaultdict(int)

        for result in self.results:
            function_totals[result.function_name] += result.duration
            function_counts[result.function_name] += 1

        top_functions = sorted(
            [
                (func, total_time, function_counts[func])
                for func, total_time in function_totals.items()
            ],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        # Memória
        memory_info = {}
        if self.memory_snapshots:
            latest_memory = self.memory_snapshots[-1][1]
            first_memory = self.memory_snapshots[0][1]
            memory_info = {
                "current_mb": latest_memory / 1024 / 1024,
                "growth_mb": (latest_memory - first_memory) / 1024 / 1024,
                "snapshots": len(self.memory_snapshots),
            }

        return {
            "summary": {
                "total_functions": total_functions,
                "total_calls": total_calls,
                "avg_duration_ms": avg_duration * 1000,
                "max_duration_ms": max_duration * 1000,
                "total_time_s": sum(durations),
            },
            "top_functions": [
                {
                    "name": func,
                    "total_time_ms": total_time * 1000,
                    "calls": calls,
                    "avg_time_ms": (total_time / calls) * 1000,
                }
                for func, total_time, calls in top_functions
            ],
            "memory": memory_info,
            "bottlenecks": len(self.bottlenecks),
        }

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização"""
        recommendations = []
        bottlenecks = self.detect_bottlenecks()

        # Agrupar por tipo de bottleneck
        bottleneck_groups = defaultdict(list)
        for bottleneck in bottlenecks:
            bottleneck_groups[bottleneck.bottleneck_type].append(bottleneck)

        for bottleneck_type, group in bottleneck_groups.items():
            if len(group) >= 1:  # Pelo menos 1 ocorrência
                avg_severity = statistics.mean([b.severity for b in group])
                total_functions = len(set(b.function_name for b in group))

                recommendations.append(
                    {
                        "type": bottleneck_type.value,
                        "priority": (
                            "high"
                            if avg_severity >= 7
                            else "medium"
                            if avg_severity >= 4
                            else "low"
                        ),
                        "title": f"{bottleneck_type.value.replace('_', ' ').title()} Issues",
                        "description": f"Detected {len(group)} {bottleneck_type.value} issues affecting {total_functions} functions",
                        "impact": f"Average severity: {avg_severity:.1f}/10",
                        "recommendations": list(
                            set().union(*[b.recommendations for b in group])
                        ),
                        "affected_functions": [b.function_name for b in group],
                    }
                )

        return sorted(
            recommendations,
            key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]],
            reverse=True,
        )


class PerformanceDemo:
    """Demonstração do sistema de profiling"""

    def __init__(self):
        self.profiler = SimpleProfiler()
        self.profiler.start_memory_tracking()

    async def run_demo(self):
        """Executa demonstração completa"""
        print("🔍 TRILHA 2 FASE 3 - Performance Profiling Demo")
        print("⚡ Sistema de Profiling Automático de Performance")
        print("=" * 70)

        await self._demo_function_profiling()
        await self._demo_memory_tracking()
        await self._demo_performance_analysis()

        self._show_dashboard()
        self._show_recommendations()

        print(f"\n🔍 Performance Profiling Demo Completed!")
        return True

    async def _demo_function_profiling(self):
        """Demonstra profiling de funções"""
        print(f"\n⚡ Scenario 1: Function Performance Profiling")
        print("=" * 50)

        @self.profiler.profile_function(ProfileType.CPU)
        def cpu_intensive_task(n: int = 100000):
            """Tarefa intensiva de CPU"""
            total = 0
            for i in range(n):
                total += i * i
            return total

        @self.profiler.profile_function(ProfileType.FUNCTION)
        async def async_task():
            """Tarefa assíncrona"""
            await asyncio.sleep(0.1)
            return sum(i**2 for i in range(50000))

        @self.profiler.profile_function(ProfileType.FUNCTION)
        def slow_function():
            """Função deliberadamente lenta"""
            time.sleep(0.15)  # 150ms
            return "slow_result"

        @self.profiler.profile_function(ProfileType.FUNCTION)
        def memory_intensive():
            """Função que usa muita memória"""
            big_list = [f"item_{i}_{'x'*100}" for i in range(10000)]
            big_dict = {i: f"value_{i}" for i in range(5000)}
            return len(big_list) + len(big_dict)

        print("🚀 Running profiled functions...")

        # Executar várias vezes para coletar estatísticas
        for i in range(5):
            cpu_intensive_task(50000 + i * 10000)
            await async_task()
            slow_function()
            memory_intensive()

            # Tomar snapshot de memória
            self.profiler.take_memory_snapshot()

            print(f"   Iteration {i+1}/5 completed")

        print(f"✅ Function profiling completed")
        print(f"📊 Collected {len(self.profiler.results)} function profiles")

    async def _demo_memory_tracking(self):
        """Demonstra tracking de memória"""
        print(f"\n💾 Scenario 2: Memory Growth Tracking")
        print("=" * 50)

        @self.profiler.profile_function(ProfileType.MEMORY)
        def create_large_objects():
            """Cria objetos grandes"""
            data = []
            for i in range(5000):
                data.append(
                    {
                        "id": i,
                        "data": f"large_string_{'x' * 200}",
                        "metadata": {"timestamp": time.time(), "index": i},
                    }
                )
            return len(data)

        # Simular crescimento de memória
        persistent_data = []

        print("🧠 Tracking memory growth...")
        for i in range(8):
            create_large_objects()

            # Adicionar dados persistentes (simular vazamento)
            persistent_data.extend([f"persistent_{j}" for j in range(1000)])

            self.profiler.take_memory_snapshot()
            print(f"   Memory snapshot {i+1}/8 taken")
            await asyncio.sleep(0.2)

        print(f"✅ Memory tracking completed")
        print(f"📈 Collected {len(self.profiler.memory_snapshots)} memory snapshots")

    async def _demo_performance_analysis(self):
        """Demonstra análise de performance"""
        print(f"\n📊 Scenario 3: Performance Analysis & Bottleneck Detection")
        print("=" * 50)

        @self.profiler.profile_function(ProfileType.FUNCTION)
        def frequent_function():
            """Função chamada frequentemente"""
            return sum(i for i in range(1000))

        @self.profiler.profile_function(ProfileType.FUNCTION)
        def variable_performance():
            """Função com performance variável"""
            import random

            sleep_time = random.uniform(0.01, 0.05)
            time.sleep(sleep_time)
            return sleep_time

        print("🔍 Running performance analysis...")

        # Executar função frequente muitas vezes
        for i in range(50):
            frequent_function()

        # Executar função com performance variável
        for i in range(10):
            variable_performance()

        print(f"✅ Performance analysis data collected")

        # Detectar bottlenecks
        bottlenecks = self.profiler.detect_bottlenecks()
        print(f"�� Detected {len(bottlenecks)} potential bottlenecks")

    def _show_dashboard(self):
        """Mostra dashboard de performance"""
        print(f"\n📊 PERFORMANCE DASHBOARD")
        print("=" * 50)

        summary = self.profiler.get_performance_summary()

        # Resumo geral
        if "summary" in summary:
            s = summary["summary"]
            print(f"📈 OVERVIEW:")
            print(f"   Functions Profiled: {s['total_functions']}")
            print(f"   Total Function Calls: {s['total_calls']}")
            print(f"   Average Duration: {s['avg_duration_ms']:.1f}ms")
            print(f"   Max Duration: {s['max_duration_ms']:.1f}ms")
            print(f"   Total Execution Time: {s['total_time_s']:.2f}s")

        # Top funções
        if "top_functions" in summary and summary["top_functions"]:
            print(f"\n⚡ TOP FUNCTIONS BY TOTAL TIME:")
            for i, func in enumerate(summary["top_functions"][:5], 1):
                print(f"   {i}. {func['name']}")
                print(
                    f"      Total: {func['total_time_ms']:.1f}ms ({func['calls']} calls)"
                )
                print(f"      Average: {func['avg_time_ms']:.1f}ms per call")

        # Memória
        if "memory" in summary and summary["memory"]:
            mem = summary["memory"]
            print(f"\n💾 MEMORY STATUS:")
            print(f"   Current Usage: {mem['current_mb']:.1f} MB")
            print(f"   Memory Growth: {mem['growth_mb']:.1f} MB")
            print(f"   Snapshots Taken: {mem['snapshots']}")

        # Bottlenecks
        print(f"\n🚨 BOTTLENECKS: {summary.get('bottlenecks', 0)} detected")

    def _show_recommendations(self):
        """Mostra recomendações"""
        print(f"\n💡 PERFORMANCE RECOMMENDATIONS")
        print("=" * 50)

        recommendations = self.profiler.generate_recommendations()

        if not recommendations:
            print("✅ No critical performance issues detected!")
            return

        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            print(
                f"{i}. {priority_emoji[rec['priority']]} {rec['title']} ({rec['priority'].upper()})"
            )
            print(f"   📝 {rec['description']}")
            print(f"   💥 {rec['impact']}")
            print(f"   🔧 Recommendations:")
            for j, recommendation in enumerate(rec["recommendations"][:3], 1):
                print(f"      {j}. {recommendation}")
            print(f"   🎯 Affected: {', '.join(rec['affected_functions'][:3])}")
            print()


async def main():
    """Função principal"""
    demo = PerformanceDemo()
    success = await demo.run_demo()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
